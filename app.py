import streamlit as st
import os
import re
from bs4 import BeautifulSoup
import json
import hashlib
import hmac
import secrets
import uuid
import random
import time
from collections import Counter
from datetime import date, datetime, timezone
from filelock import FileLock
from urllib import error as urllib_error
from urllib import parse as urllib_parse
from urllib import request as urllib_request

st.set_page_config(
    page_title="Treinador IDECAN - Engenharia Elétrica",
    page_icon="⚡",
    layout="wide"
)

QUESTOES_DIR = "questoes"
DADOS_USUARIOS_DIR = "dados_usuarios"
USUARIOS_FILE = os.path.join(DADOS_USUARIOS_DIR, "usuarios.json")
PROGRESSO_LEGADO_FILE = "progresso_usuario.json"
MIGRACAO_GABARITOS_FILE = "migracao_gabaritos_v2.json"
REVISAO_QUESTOES = "v2"


def ler_secret(nome, padrao=""):
    """Lê um Secret do Streamlit e mantém compatibilidade com execução local."""
    try:
        valor = st.secrets.get(nome, os.environ.get(nome, padrao))
    except (FileNotFoundError, KeyError):
        valor = os.environ.get(nome, padrao)
    return str(valor).strip() if valor is not None else padrao


SUPABASE_URL = ler_secret("SUPABASE_URL").rstrip("/")
SUPABASE_SECRET_KEY = ler_secret("SUPABASE_SECRET_KEY") or ler_secret("SUPABASE_KEY")
SUPABASE_ATIVO = bool(SUPABASE_URL and SUPABASE_SECRET_KEY)
SUPABASE_ESTADO = {"online": False, "erro": None}
_REMOTO_AUSENTE = object()
_REMOTO_ERRO = object()

if not os.path.exists(QUESTOES_DIR):
    os.makedirs(QUESTOES_DIR)

os.makedirs(DADOS_USUARIOS_DIR, exist_ok=True)


def carregar_json(caminho, padrao):
    """Lê JSON com bloqueio para evitar leitura durante outra gravação."""
    with FileLock(f"{caminho}.lock"):
        if not os.path.exists(caminho):
            return padrao.copy() if isinstance(padrao, dict) else padrao
        try:
            with open(caminho, "r", encoding="utf-8") as arquivo:
                conteudo = json.load(arquivo)
                return conteudo if isinstance(conteudo, type(padrao)) else padrao
        except (OSError, json.JSONDecodeError):
            return padrao.copy() if isinstance(padrao, dict) else padrao


def salvar_json(caminho, conteudo):
    """Grava JSON de forma atômica e protegida contra concorrência."""
    os.makedirs(os.path.dirname(caminho) or ".", exist_ok=True)
    temporario = f"{caminho}.{uuid.uuid4().hex}.tmp"
    with FileLock(f"{caminho}.lock"):
        try:
            with open(temporario, "w", encoding="utf-8") as arquivo:
                json.dump(conteudo, arquivo, ensure_ascii=False, indent=2)
            os.replace(temporario, caminho)
        finally:
            if os.path.exists(temporario):
                os.remove(temporario)


def requisicao_supabase(metodo, caminho, conteudo=None, prefer=None):
    """Executa uma chamada REST ao Supabase sem expor a chave em mensagens."""
    if not SUPABASE_ATIVO:
        raise RuntimeError("Supabase não configurado.")

    dados = None
    if conteudo is not None:
        dados = json.dumps(conteudo, ensure_ascii=False).encode("utf-8")
    cabecalhos = {
        "apikey": SUPABASE_SECRET_KEY,
        "Authorization": f"Bearer {SUPABASE_SECRET_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if prefer:
        cabecalhos["Prefer"] = prefer

    requisicao = urllib_request.Request(
        f"{SUPABASE_URL}{caminho}",
        data=dados,
        headers=cabecalhos,
        method=metodo,
    )
    try:
        with urllib_request.urlopen(requisicao, timeout=12) as resposta:
            corpo = resposta.read().decode("utf-8")
            SUPABASE_ESTADO.update(online=True, erro=None)
            return json.loads(corpo) if corpo else None
    except urllib_error.HTTPError as erro:
        detalhe = erro.read().decode("utf-8", errors="replace")[:300]
        if erro.code in (401, 403):
            mensagem = "A chave configurada não possui acesso ao banco. Confira SUPABASE_SECRET_KEY."
        elif erro.code == 404 or "PGRST205" in detalhe or "42P01" in detalhe:
            mensagem = "Tabela app_state não encontrada. Execute o arquivo supabase_setup.sql no SQL Editor."
        else:
            mensagem = f"Supabase respondeu HTTP {erro.code}."
        SUPABASE_ESTADO.update(online=False, erro=mensagem)
        raise RuntimeError(mensagem) from erro
    except (urllib_error.URLError, TimeoutError, json.JSONDecodeError) as erro:
        mensagem = "Não foi possível acessar o Supabase neste momento."
        SUPABASE_ESTADO.update(online=False, erro=mensagem)
        raise RuntimeError(mensagem) from erro


def carregar_estado_remoto(namespace, chave):
    if not SUPABASE_ATIVO:
        return _REMOTO_AUSENTE
    consulta = (
        "/rest/v1/app_state?namespace=eq."
        f"{urllib_parse.quote(namespace, safe='')}&record_key=eq."
        f"{urllib_parse.quote(chave, safe='')}&select=payload"
    )
    try:
        registros = requisicao_supabase("GET", consulta) or []
        return registros[0].get("payload") if registros else _REMOTO_AUSENTE
    except RuntimeError:
        return _REMOTO_ERRO


def salvar_estado_remoto(namespace, chave, conteudo):
    if not SUPABASE_ATIVO:
        return False
    registro = {
        "namespace": namespace,
        "record_key": chave,
        "payload": conteudo,
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    try:
        requisicao_supabase(
            "POST",
            "/rest/v1/app_state?on_conflict=namespace,record_key",
            registro,
            prefer="resolution=merge-duplicates,return=minimal",
        )
        return True
    except RuntimeError:
        return False


def carregar_persistente(namespace, chave, caminho_local, padrao):
    """Prioriza o banco e migra automaticamente o JSON local na primeira leitura."""
    local = carregar_json(caminho_local, padrao)
    remoto = carregar_estado_remoto(namespace, chave)
    if remoto is _REMOTO_ERRO:
        return local
    if remoto is _REMOTO_AUSENTE:
        if SUPABASE_ATIVO and local != padrao:
            salvar_estado_remoto(namespace, chave, local)
        return local
    if isinstance(remoto, type(padrao)):
        salvar_json(caminho_local, remoto)
        return remoto
    return local


def salvar_persistente(namespace, chave, caminho_local, conteudo):
    """Mantém cópia local e sincroniza uma segunda cópia persistente no Supabase."""
    salvar_json(caminho_local, conteudo)
    salvar_estado_remoto(namespace, chave, conteudo)


def gerar_hash_pin(pin, salt_hex=None):
    salt = bytes.fromhex(salt_hex) if salt_hex else secrets.token_bytes(16)
    pin_hash = hashlib.pbkdf2_hmac("sha256", pin.encode("utf-8"), salt, 200_000)
    return salt.hex(), pin_hash.hex()


def validar_pin(usuario, pin):
    _, calculado = gerar_hash_pin(pin, usuario["pin_salt"])
    return hmac.compare_digest(calculado, usuario["pin_hash"])


def carregar_usuarios():
    return carregar_persistente("usuarios", "global", USUARIOS_FILE, {})


def criar_usuario(nome, pin):
    nome = " ".join(nome.strip().split())
    if len(nome) < 2 or len(nome) > 40:
        raise ValueError("O nome deve ter entre 2 e 40 caracteres.")
    if len(pin) < 4 or not pin.isdigit():
        raise ValueError("O PIN deve conter pelo menos 4 números.")

    with FileLock(f"{USUARIOS_FILE}.cadastro.lock"):
        usuarios = carregar_usuarios()
        if any(u["nome"].casefold() == nome.casefold() for u in usuarios.values()):
            raise ValueError("Já existe um perfil com esse nome.")

        usuario_id = uuid.uuid4().hex
        salt, pin_hash = gerar_hash_pin(pin)
        usuarios[usuario_id] = {
            "id": usuario_id,
            "nome": nome,
            "pin_salt": salt,
            "pin_hash": pin_hash,
            "criado_em": datetime.now().isoformat(timespec="seconds")
        }
        salvar_persistente("usuarios", "global", USUARIOS_FILE, usuarios)

        progresso_novo = os.path.join(DADOS_USUARIOS_DIR, f"{usuario_id}.json")
        if len(usuarios) == 1 and os.path.exists(PROGRESSO_LEGADO_FILE):
            progresso_inicial = carregar_json(PROGRESSO_LEGADO_FILE, {})
        else:
            progresso_inicial = {}
        salvar_persistente("progresso", usuario_id, progresso_novo, progresso_inicial)
        return usuarios[usuario_id]


def tela_de_perfil():
    if st.session_state.get("usuario_id"):
        return

    st.title("⚡ Treinador IDECAN")
    st.subheader("Escolha seu perfil de estudos")
    st.caption("Cada perfil possui histórico, estatísticas e arquivo de backup próprios.")

    usuarios = carregar_usuarios()
    aba_entrar, aba_criar = st.tabs(["Entrar", "Criar perfil"])

    with aba_entrar:
        if usuarios:
            por_nome = {u["nome"]: u for u in sorted(usuarios.values(), key=lambda x: x["nome"].casefold())}
            nome_selecionado = st.selectbox("Usuário", list(por_nome), key="login_usuario")
            pin = st.text_input("PIN", type="password", key="login_pin", max_chars=20)
            if st.button("Entrar", type="primary", use_container_width=True):
                usuario = por_nome[nome_selecionado]
                if validar_pin(usuario, pin):
                    st.session_state.usuario_id = usuario["id"]
                    st.session_state.usuario_nome = usuario["nome"]
                    st.session_state.pop("progresso", None)
                    st.rerun()
                else:
                    st.error("PIN incorreto.")
        else:
            st.info("Ainda não existe nenhum perfil. Crie o primeiro na aba ao lado.")

    with aba_criar:
        novo_nome = st.text_input("Nome do novo usuário", key="novo_usuario", max_chars=40)
        novo_pin = st.text_input("Crie um PIN numérico", type="password", key="novo_pin", max_chars=20)
        confirmar_pin = st.text_input("Confirme o PIN", type="password", key="confirmar_pin", max_chars=20)
        if st.button("Criar perfil", use_container_width=True):
            if novo_pin != confirmar_pin:
                st.error("Os PINs não coincidem.")
            else:
                try:
                    usuario = criar_usuario(novo_nome, novo_pin)
                    st.session_state.usuario_id = usuario["id"]
                    st.session_state.usuario_nome = usuario["nome"]
                    st.session_state.pop("progresso", None)
                    st.rerun()
                except ValueError as erro:
                    st.error(str(erro))

    if SUPABASE_ESTADO["online"]:
        st.success("☁️ Sincronização persistente com o Supabase ativa.")
    elif SUPABASE_ATIVO:
        st.error(SUPABASE_ESTADO["erro"] or "Não foi possível confirmar a conexão com o Supabase.")
        st.caption("O app continua em modo local e o backup JSON permanece disponível.")
    else:
        st.warning(
            "Supabase não configurado. No Streamlit Community Cloud, arquivos locais podem "
            "ser apagados em reinicializações."
        )
    st.stop()


tela_de_perfil()
PROGRESSO_FILE = os.path.join(DADOS_USUARIOS_DIR, f"{st.session_state.usuario_id}.json")
SIMULADOS_FILE = os.path.join(DADOS_USUARIOS_DIR, f"{st.session_state.usuario_id}_simulados.json")
TRILHA_FILE = os.path.join(DADOS_USUARIOS_DIR, f"{st.session_state.usuario_id}_trilha.json")

# --- Mapeamento do Edital: Assuntos, Blocos e Metas ---
MAPEAMENTO_ASSUNTOS = {
    # "esperadas" é uma distribuição estratégica para um simulado de 20 questões.
    # Não representa uma divisão oficial da IDECAN por assunto.
    "NBR 5410 & Instalações BT": {"bloco": "OURO", "meta": 50, "esperadas": 2, "keywords": ["5410", "BAIXA TENSÃO", "BAIXA TENSAO", "NOBREAK", "MOTOGERADOR"]},
    "NBR 14039 & Instalações MT": {"bloco": "OURO", "meta": 45, "esperadas": 1, "keywords": ["14039", "MEDIA TENSAO", "MÉDIA TENSÃO", "CABINE", "SUBESTACAO", "SUBESTAÇÃO"]},
    "Sistemas de Potência & Proteção": {"bloco": "OURO", "meta": 45, "esperadas": 1, "keywords": ["SISTEMAS DE POTENCIA", "SISTEMAS DE POTÊNCIA", "SEP", "TRANSMISSAO", "TRANSMISSÃO", "DISTRIBUICAO", "DISTRIBUIÇÃO", "RELE", "RELÉ"]},
    "Grandezas Elétricas & Circuitos": {"bloco": "OURO", "meta": 45, "esperadas": 1, "keywords": ["CIRCUITO", "GRANDEZA", "FATOR DE POTENCIA", "FATOR DE POTÊNCIA", "TRIFASICO", "TRIFÁSICO"]},
    "Aterramento e SPDA (NBR 5419)": {"bloco": "OURO", "meta": 45, "esperadas": 1, "keywords": ["5419", "SPDA", "ATERRAMENTO", "DESCARGA"]},
    "NR-10 & Segurança em Eletricidade": {"bloco": "OURO", "meta": 45, "esperadas": 1, "keywords": ["NR-10", "NR10", "SEGURANÇA EM ELETRICIDADE"]},
    "Lei nº 14.133/2021, Orçamentação & Planejamento": {"bloco": "OURO", "meta": 45, "esperadas": 1, "keywords": ["14.133", "14133", "LICITACAO", "LICITAÇÃO", "LICITACOES", "LICITAÇÕES", "BDI", "ORÇAMENTO", "ORCAMENTO", "CRONOGRAMA"]},

    "Luminotécnica & Iluminação Pública": {"bloco": "PRATA", "meta": 30, "esperadas": 1, "keywords": ["LUMINOTECNICA", "LUMINOTÉCNICA", "ILUMINACAO", "ILUMINAÇÃO"]},
    "Obras de Infraestrutura Elétrica & Projetos": {"bloco": "PRATA", "meta": 25, "esperadas": 1, "keywords": ["INFRAESTRUTURA", "IMPLANTACAO", "IMPLANTAÇÃO", "ESPECIFICACAO", "ESPECIFICAÇÃO"]},
    "Fiscalização de Obras, Vistorias & NBR 9050": {"bloco": "PRATA", "meta": 30, "esperadas": 1, "keywords": ["FISCALIZACAO", "FISCALIZAÇÃO", "9050", "ACESSIBILIDADE", "VISTORIA", "PARECER"]},
    "Legislação Profissional & CONFEA/ART": {"bloco": "PRATA", "meta": 25, "esperadas": 1, "keywords": ["5.194", "5194", "CONFEA", "CREA", "ART", "ETICA", "ÉTICA"]},
    "Manutenção & Gestão Predial": {"bloco": "PRATA", "meta": 20, "esperadas": 1, "keywords": ["MANUTENCAO", "MANUTENÇÃO", "PREDITIVA", "PREVENTIVA", "CORRETIVA"]},
    "Detecção e Alarme de Incêndio (SDAI)": {"bloco": "PRATA", "meta": 20, "esperadas": 1, "keywords": ["INCENDIO", "INCÊNDIO", "SDAI", "ALARME", "DETECTOR"]},
    "Eficiência Energética, Cogeração & Fontes Alternativas": {"bloco": "PRATA", "meta": 25, "esperadas": 1, "keywords": ["EFICIENCIA", "EFICIÊNCIA", "COGERACAO", "COGERAÇÃO", "SOLAR", "FOTOVOLTAICA", "EOLICA", "EÓLICA", "BIOMASSA"]},

    "Redes Estruturadas & Cabeamento": {"bloco": "BRONZE", "meta": 15, "esperadas": 1, "keywords": ["ESTRUTURADA", "CABEAMENTO", "TELEFONIA", "DADOS", "AUDIO", "ÁUDIO", "VIDEO", "VÍDEO"]},
    "Comandos Elétricos & Motores": {"bloco": "BRONZE", "meta": 15, "esperadas": 1, "keywords": ["COMANDOS_ELETRICOS_MOTORES", "COMANDOS ELÉTRICOS", "COMANDOS ELETRICOS", "CONTATOR", "PARTIDA DE MOTOR"]},
    "Desenho Técnico & Interpretação de Projetos": {"bloco": "BRONZE", "meta": 15, "esperadas": 1, "keywords": ["DESENHO", "PLANTA", "UNIFILAR", "MULTIFILAR", "SIMBOLOGIA", "INTERPRETACAO", "INTERPRETAÇÃO"]},
    "Legislação Urbanística & Parcelamento": {"bloco": "BRONZE", "meta": 15, "esperadas": 1, "keywords": ["6.766", "6766", "URBANO", "URBANISTICA", "URBANÍSTICA", "POSTURAS", "PLANO DIRETOR", "PARCELAMENTO"]},
    "Licenciamento Ambiental & Segurança em Obras": {"bloco": "BRONZE", "meta": 15, "esperadas": 1, "keywords": ["AMBIENTAL", "LICENCA", "LICENÇA", "EIA", "RIMA", "SEGURANÇA DO TRABALHO", "SEGURANCA DO TRABALHO"]}
}

ASSUNTO_POR_ARQUIVO = {
    "caderno_50_questoes_nbr5410_idecan.html": "NBR 5410 & Instalações BT",
    "caderno_45_questoes_nbr14039_idecan.html": "NBR 14039 & Instalações MT",
    "caderno_45_questoes_sep_protecao_idecan.html": "Sistemas de Potência & Proteção",
    "caderno_45_questoes_circuitos_idecan.html": "Grandezas Elétricas & Circuitos",
    "caderno_45_questoes_spda_idecan.html": "Aterramento e SPDA (NBR 5419)",
    "caderno_45_questoes_nr10_idecan.html": "NR-10 & Segurança em Eletricidade",
    "caderno_45_questoes_licitacoes_idecan.html": "Lei nº 14.133/2021, Orçamentação & Planejamento",
    "caderno_30_questoes_luminotecnica_idecan.html": "Luminotécnica & Iluminação Pública",
    "caderno_25_questoes_infraestrutura_projetos_idecan.html": "Obras de Infraestrutura Elétrica & Projetos",
    "caderno_30_questoes_fiscalizacao_vistorias_nbr9050_idecan.html": "Fiscalização de Obras, Vistorias & NBR 9050",
    "caderno_25_questoes_legislacao_profissional_confea_art_idecan.html": "Legislação Profissional & CONFEA/ART",
    "caderno_20_questoes_manutencao_gestao_predial_idecan.html": "Manutenção & Gestão Predial",
    "caderno_20_questoes_sdai_idecan.html": "Detecção e Alarme de Incêndio (SDAI)",
    "caderno_25_questoes_eficiencia_energetica_cogeracao_fontes_alternativas_idecan.html": "Eficiência Energética, Cogeração & Fontes Alternativas",
    "caderno_15_questoes_redes_estruturadas_cabeamento_idecan.html": "Redes Estruturadas & Cabeamento",
    "caderno_15_questoes_comandos_eletricos_motores_idecan.html": "Comandos Elétricos & Motores",
    "caderno_15_questoes_desenho_tecnico_interpretacao_projetos_idecan.html": "Desenho Técnico & Interpretação de Projetos",
    "caderno_15_questoes_legislacao_urbanistica_parcelamento_solo_idecan.html": "Legislação Urbanística & Parcelamento",
    "caderno_15_questoes_licenciamento_ambiental_obras_idecan.html": "Licenciamento Ambiental & Segurança em Obras",
}

META_POR_BLOCO = {
    bloco: sum(info["meta"] for info in MAPEAMENTO_ASSUNTOS.values() if info["bloco"] == bloco)
    for bloco in ("OURO", "PRATA", "BRONZE")
}
META_GLOBAL = sum(META_POR_BLOCO.values())
TOTAL_QUESTOES_SIMULADO = sum(info["esperadas"] for info in MAPEAMENTO_ASSUNTOS.values())

def identificar_assunto_e_bloco(nome_arquivo, tag_questao):
    assunto_exato = ASSUNTO_POR_ARQUIVO.get(nome_arquivo)
    if assunto_exato:
        info = MAPEAMENTO_ASSUNTOS[assunto_exato]
        return assunto_exato, info["bloco"], info["meta"]

    texto = (nome_arquivo + " " + tag_questao).upper()
    for assunto, info in MAPEAMENTO_ASSUNTOS.items():
        if any(k in nome_arquivo.upper() for k in info["keywords"]):
            return assunto, info["bloco"], info["meta"]
            
    for assunto, info in MAPEAMENTO_ASSUNTOS.items():
        if any(k in texto for k in info["keywords"]):
            return assunto, info["bloco"], info["meta"]
            
    return "Outros Assuntos", "BRONZE", 15

# --- Gerenciamento de Estado e Progresso ---
def carregar_progresso():
    return carregar_persistente(
        "progresso", st.session_state.usuario_id, PROGRESSO_FILE, {}
    )

def salvar_progresso(progresso):
    salvar_persistente(
        "progresso", st.session_state.usuario_id, PROGRESSO_FILE, progresso
    )


def carregar_trilha():
    return carregar_persistente(
        "trilha", st.session_state.usuario_id, TRILHA_FILE, {}
    )


def salvar_trilha(trilha):
    salvar_persistente(
        "trilha", st.session_state.usuario_id, TRILHA_FILE, trilha
    )

if "progresso" not in st.session_state:
    st.session_state.progresso = carregar_progresso()

if "trilha" not in st.session_state:
    st.session_state.trilha = carregar_trilha()

if "idx_individual" not in st.session_state:
    st.session_state.idx_individual = 0

if "pagina_lote" not in st.session_state:
    st.session_state.pagina_lote = 1

# --- Parser de Arquivos HTML ---
@st.cache_data
def carregar_todas_questoes():
    questoes = []
    if not os.path.exists(QUESTOES_DIR):
        return questoes

    arquivos = [f for f in os.listdir(QUESTOES_DIR) if f.endswith(".html")]
    
    for arq in arquivos:
        caminho = os.path.join(QUESTOES_DIR, arq)
        with open(caminho, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f.read(), "html.parser")
            
        cards = soup.find_all("div", class_="question-card")
        for idx, card in enumerate(cards):
            q_num_elem = card.find("td", class_="q-number")
            q_tag_elem = card.find("td", class_="q-tag")
            q_stmt_elem = card.find("div", class_="q-statement")
            sol_box = card.find("div", class_="solution-box")
            
            q_num = q_num_elem.get_text(strip=True) if q_num_elem else f"Questão {idx+1:02d}"
            subtema = q_tag_elem.get_text(strip=True) if q_tag_elem else "Geral"
            statement = q_stmt_elem.decode_contents().strip() if q_stmt_elem else ""
            
            alts = []
            alt_divs = card.find_all("div", class_="alt-item")
            for a_div in alt_divs:
                alts.append(a_div.decode_contents().strip())
                
            sol_text = ""
            gabarito = ""
            tip_text = ""
            
            if sol_box:
                header = sol_box.find("span", class_="sol-header")
                if header:
                    match = re.search(r"Alternativa\s+([A-E])", header.get_text(strip=True), re.IGNORECASE)
                    if match:
                        gabarito = match.group(1).upper()
                
                sol_div = sol_box.find("div", class_="sol-text")
                if sol_div:
                    sol_text = sol_div.decode_contents().strip()
                    
                tip_div = sol_box.find("div", class_="tip-box")
                if tip_div:
                    tip_text = tip_div.decode_contents().strip()
            
            assunto, bloco, meta = identificar_assunto_e_bloco(arq, subtema)
            assunto = card.get("data-assunto", assunto)
            if assunto in MAPEAMENTO_ASSUNTOS:
                bloco = card.get("data-bloco", MAPEAMENTO_ASSUNTOS[assunto]["bloco"])
                meta = MAPEAMENTO_ASSUNTOS[assunto]["meta"]
            fonte = card.get("data-origem", "Questões autorais")
            q_id = f"{arq}_{q_num}_{idx}"
            
            questoes.append({
                "id": q_id,
                "origem": arq,
                "fonte": fonte,
                "prova_fonte": card.get("data-prova", ""),
                "questao_original": card.get("data-questao-original", ""),
                "numero": q_num,
                "assunto": assunto,
                "subtema": subtema,
                "bloco": bloco,
                "meta": meta,
                "enunciado": statement,
                "alternativas": alts,
                "gabarito": gabarito,
                "resolucao": sol_text,
                "dica": tip_text
            })
            
    return questoes

todas_questoes = carregar_todas_questoes()

ESTADOS_TRILHA = [
    "Não iniciado", "Reconhecimento", "Em estudo", "Em revisão", "Consolidado"
]
PESO_ESTRATEGICO = {"OURO": 1.00, "PRATA": 0.70, "BRONZE": 0.45}


def converter_data(valor):
    """Converte datas antigas e ISO em date sem invalidar o progresso legado."""
    if not valor:
        return None
    try:
        return datetime.fromisoformat(str(valor).replace("Z", "+00:00")).date()
    except (TypeError, ValueError):
        return None


def estatisticas_trilha(assunto, info, questoes, progresso_atual, trilha_atual, hoje=None):
    hoje = hoje or date.today()
    questoes_tema = [q for q in questoes if q["assunto"] == assunto]
    ids_tema = {q["id"] for q in questoes_tema}
    registros = [v for qid, v in progresso_atual.items() if qid in ids_tema]
    respondidas = len(registros)

    tentativas = sum(max(1, int(r.get("tentativas", 1))) for r in registros)
    acertos = sum(
        int(r.get("acertos_total", 1 if r.get("acertou") else 0)) for r in registros
    )
    taxa_acerto = acertos / tentativas if tentativas else 0.0

    subtemas = sorted({q["subtema"] for q in questoes_tema})
    subtemas_cobertos = {
        q["subtema"] for q in questoes_tema if q["id"] in progresso_atual
    }
    subtemas_pendentes = [s for s in subtemas if s not in subtemas_cobertos]
    cobertura = len(subtemas_cobertos) / len(subtemas) if subtemas else 0.0
    meta_efetiva = max(1, min(info["meta"], len(questoes_tema) or info["meta"]))
    volume = min(respondidas / meta_efetiva, 1.0)

    datas = [converter_data(r.get("data")) for r in registros]
    dados_tema = trilha_atual.get(assunto, {})
    datas.append(converter_data(dados_tema.get("ultima_revisao")))
    datas = [d for d in datas if d]
    ultima_atividade = max(datas) if datas else None
    dias_sem_revisar = max(0, (hoje - ultima_atividade).days) if ultima_atividade else None

    # A taxa recebe confiança gradual: poucas respostas não geram domínio alto artificial.
    dominio = 100 * taxa_acerto * (0.45 + 0.35 * volume + 0.20 * cobertura)
    dominio = round(max(0.0, min(dominio, 100.0)), 1)

    if respondidas == 0:
        estado_automatico = "Não iniciado"
    elif volume < 0.15 or cobertura < 0.25:
        estado_automatico = "Reconhecimento"
    elif dominio < 70 or cobertura < 0.65:
        estado_automatico = "Em estudo"
    elif dominio >= 80 and volume >= 0.65 and cobertura >= 0.75 and (dias_sem_revisar or 0) < 10:
        estado_automatico = "Consolidado"
    else:
        estado_automatico = "Em revisão"

    estado_manual = dados_tema.get("estado")
    estado = estado_manual if estado_manual in ESTADOS_TRILHA else estado_automatico
    atraso = 0.35 if dias_sem_revisar is None else min(dias_sem_revisar / 14, 1.0)
    lacuna_dominio = 1 - dominio / 100
    lacuna_cobertura = 1 - cobertura
    peso = PESO_ESTRATEGICO.get(info["bloco"], 0.45)
    prioridade = round(100 * (
        0.35 * peso + 0.30 * lacuna_dominio + 0.20 * atraso + 0.15 * lacuna_cobertura
    ), 1)

    if respondidas == 0:
        acao = "Reconhecimento: resolva 5 questões variadas e leia as resoluções."
    elif subtemas_pendentes and cobertura < 0.65:
        acao = f"Cobertura: avance em “{subtemas_pendentes[0]}”."
    elif taxa_acerto < 0.70:
        acao = "Correção: refaça questões erradas e compare os distratores."
    elif dias_sem_revisar is not None and dias_sem_revisar >= 10:
        acao = "Revisão espaçada: faça de 5 a 10 questões sem consultar o resumo."
    else:
        acao = "Consolidação: faça 10 questões mistas e registre os pontos frágeis."

    return {
        "assunto": assunto, "bloco": info["bloco"], "meta": info["meta"],
        "disponiveis": len(questoes_tema), "respondidas": respondidas,
        "tentativas": tentativas, "acertos": acertos, "taxa_acerto": taxa_acerto,
        "subtemas_total": len(subtemas), "subtemas_pendentes": subtemas_pendentes,
        "cobertura": cobertura, "dias_sem_revisar": dias_sem_revisar,
        "dominio": dominio, "estado": estado, "estado_automatico": estado_automatico,
        "prioridade": prioridade, "acao": acao,
    }


def calcular_trilha(questoes, progresso_atual, trilha_atual, hoje=None):
    resultados = [
        estatisticas_trilha(assunto, info, questoes, progresso_atual, trilha_atual, hoje)
        for assunto, info in MAPEAMENTO_ASSUNTOS.items()
    ]
    return sorted(resultados, key=lambda item: (-item["prioridade"], item["assunto"]))


def registrar_tentativa(q, resposta, acertou, origem="estudo"):
    anterior = progresso.get(q["id"], {})
    tentativas_anteriores = int(anterior.get("tentativas", 1 if anterior.get("resposta") else 0))
    acertos_anteriores = int(anterior.get("acertos_total", 1 if anterior.get("acertou") else 0))
    progresso[q["id"]] = {
        "resposta": resposta, "acertou": acertou, "assunto": q["assunto"],
        "tema": q["subtema"], "bloco": q["bloco"], "origem_resposta": origem,
        "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "tentativas": tentativas_anteriores + 1,
        "acertos_total": acertos_anteriores + int(acertou),
    }

# Sincronização do progresso salvo
progresso = st.session_state.progresso
migracao_gabaritos = carregar_json(MIGRACAO_GABARITOS_FILE, {})
houve_ajuste = False
for q in todas_questoes:
    if q["id"] in progresso:
        registro = progresso[q["id"]]
        if registro.get("revisao_questoes") != REVISAO_QUESTOES:
            resposta_antiga = registro.get("resposta")
            conversao = migracao_gabaritos.get(q["id"], {})
            if resposta_antiga in conversao:
                registro["resposta"] = conversao[resposta_antiga]
            registro["revisao_questoes"] = REVISAO_QUESTOES
            houve_ajuste = True
        resposta_atual = registro.get("resposta")
        if isinstance(resposta_atual, str) and resposta_atual in "ABCDE" and q["gabarito"]:
            acertou_atual = resposta_atual == q["gabarito"]
            if registro.get("acertou") != acertou_atual:
                registro["acertou"] = acertou_atual
                houve_ajuste = True
        if progresso[q["id"]].get("bloco") != q["bloco"] or progresso[q["id"]].get("assunto") != q["assunto"]:
            progresso[q["id"]]["bloco"] = q["bloco"]
            progresso[q["id"]]["assunto"] = q["assunto"]
            progresso[q["id"]]["tema"] = q["subtema"]
            houve_ajuste = True

if houve_ajuste:
    salvar_progresso(progresso)

# --- Barra Lateral: Metas, Filtros e Modos de Visualização ---
st.sidebar.title("⚡ Painel de Metas • IDECAN")
st.sidebar.caption(f"Perfil ativo: **{st.session_state.usuario_nome}**")
if SUPABASE_ESTADO["online"]:
    st.sidebar.caption("☁️ Progresso sincronizado com o Supabase")
elif SUPABASE_ATIVO:
    st.sidebar.warning(SUPABASE_ESTADO["erro"] or "Sincronização online indisponível.")
else:
    st.sidebar.warning("Progresso salvo apenas neste servidor.")
if st.sidebar.button("Trocar usuário", use_container_width=True):
    for chave in list(st.session_state):
        if chave.startswith("sim_") or chave in ("usuario_id", "usuario_nome", "progresso", "trilha", "ultimo_upload_sig"):
            st.session_state.pop(chave, None)
    st.rerun()

if not todas_questoes:
    st.warning(f"Nenhum caderno `.html` encontrado na pasta `{QUESTOES_DIR}/`.")
    st.stop()

total_respondidas = len(progresso)
total_acertos = sum(1 for v in progresso.values() if v.get("acertou"))
taxa_acerto = (total_acertos / total_respondidas * 100) if total_respondidas > 0 else 0.0

st.sidebar.metric("Questões Feitas", f"{total_respondidas} / {META_GLOBAL}")
st.sidebar.metric("Aproveitamento Global", f"{taxa_acerto:.1f}%")

st.sidebar.divider()
modo_aplicacao = st.sidebar.radio(
    "Modo de uso:",
    ["Trilha do edital", "Estudo por cadernos", "Simulado específico"],
    key="modo_aplicacao_app",
    help="A trilha recomenda o estudo do dia; o simulado usa 20 questões e vale 40 pontos."
)

st.sidebar.divider()
st.sidebar.subheader("🎯 Progresso por Bloco")

qtd_ouro = sum(1 for q in todas_questoes if q["id"] in progresso and q["bloco"] == "OURO")
qtd_prata = sum(1 for q in todas_questoes if q["id"] in progresso and q["bloco"] == "PRATA")
qtd_bronze = sum(1 for q in todas_questoes if q["id"] in progresso and q["bloco"] == "BRONZE")

st.sidebar.write(f"🥇 **Bloco Ouro:** {qtd_ouro} / {META_POR_BLOCO['OURO']} questões")
st.sidebar.progress(min(qtd_ouro / META_POR_BLOCO["OURO"], 1.0))

st.sidebar.write(f"🥈 **Bloco Prata:** {qtd_prata} / {META_POR_BLOCO['PRATA']} questões")
st.sidebar.progress(min(qtd_prata / META_POR_BLOCO["PRATA"], 1.0))

st.sidebar.write(f"🥉 **Bloco Bronze:** {qtd_bronze} / {META_POR_BLOCO['BRONZE']} questões")
st.sidebar.progress(min(qtd_bronze / META_POR_BLOCO["BRONZE"], 1.0))

# --- Gerenciamento e Backup de Progresso (Streamlit Cloud & Local) ---
st.sidebar.divider()
st.sidebar.subheader("💾 Backup & Sincronização")

json_progresso = json.dumps(progresso, ensure_ascii=False, indent=2)
st.sidebar.download_button(
    label="📥 Baixar Progresso (.json)",
    data=json_progresso,
    file_name=f"progresso_{st.session_state.usuario_nome.replace(' ', '_').lower()}.json",
    mime="application/json",
    help="Baixe seu arquivo de progresso para guardar no PC/Celular ou subir no GitHub.",
    use_container_width=True
)

arquivo_upload = st.sidebar.file_uploader(
    "📤 Restaurar Progresso (.json):",
    type=["json"],
    help="Envie seu arquivo progresso_usuario.json para restaurar as questões já respondidas."
)

if arquivo_upload is not None:
    upload_sig = f"{arquivo_upload.name}_{arquivo_upload.size}"
    if st.session_state.get("ultimo_upload_sig") != upload_sig:
        try:
            conteudo_carregado = json.load(arquivo_upload)
            if isinstance(conteudo_carregado, dict):
                st.session_state.progresso.update(conteudo_carregado)
                salvar_progresso(st.session_state.progresso)
                st.session_state.ultimo_upload_sig = upload_sig
                st.sidebar.success(f"✅ {len(conteudo_carregado)} questões restauradas!")
                st.rerun()
            else:
                st.sidebar.error("Formato inválido do arquivo JSON.")
        except Exception as e:
            st.sidebar.error(f"Erro ao ler arquivo: {e}")

bloco_sel = "Todos os Blocos"
origem_sel = "Todas as Origens"
assunto_sel = "Todos os Assuntos"
subtema_sel = "Todos os Subtemas"
modo_estudo = "Todas as Questões"
formato_visualizacao = "Uma por vez (Modo Estudo / Slide)"
tam_bloco = 10

if modo_aplicacao == "Estudo por cadernos":
    st.sidebar.divider()
    st.sidebar.subheader("🔍 Filtros de Busca")

    origens_disponiveis = sorted({q["fonte"] for q in todas_questoes})
    origem_sel = st.sidebar.selectbox(
        "1. Origem das questões:", ["Todas as Origens"] + origens_disponiveis,
        key="filtro_origem"
    )

    bloco_sel = st.sidebar.selectbox(
        "2. Bloco do Edital:", ["Todos os Blocos", "OURO", "PRATA", "BRONZE"],
        key="filtro_bloco"
    )

    assuntos_filtrados = sorted(list(set(q["assunto"] for q in todas_questoes if (
        (origem_sel == "Todas as Origens" or q["fonte"] == origem_sel) and
        (bloco_sel == "Todos os Blocos" or q["bloco"] == bloco_sel)
    ))))
    assunto_sel = st.sidebar.selectbox(
        "3. Assunto (Macro):", ["Todos os Assuntos"] + assuntos_filtrados,
        key="filtro_assunto"
    )

    subtemas_filtrados = sorted(list(set(q["subtema"] for q in todas_questoes if (
        (origem_sel == "Todas as Origens" or q["fonte"] == origem_sel) and
        (bloco_sel == "Todos os Blocos" or q["bloco"] == bloco_sel) and
        (assunto_sel == "Todos os Assuntos" or q["assunto"] == assunto_sel)
    ))))
    subtema_sel = st.sidebar.selectbox(
        "4. Subtema / Tag:", ["Todos os Subtemas"] + subtemas_filtrados,
        key="filtro_subtema"
    )

    modo_estudo = st.sidebar.radio(
        "5. Status das Questões:",
        ["Todas as Questões", "Caderno de Erros (Apenas Erradas)", "Apenas Não Resolvidas"],
        key="filtro_status"
    )

    st.sidebar.divider()
    st.sidebar.subheader("👁️ Formato de Visualização")
    formato_visualizacao = st.sidebar.radio(
        "Como deseja visualizar?",
        ["Uma por vez (Modo Estudo / Slide)", "Em blocos menores (Paginação)", "Lista completa contínua"],
        key="filtro_visualizacao"
    )

    if formato_visualizacao == "Em blocos menores (Paginação)":
        tam_bloco = st.sidebar.select_slider("Tamanho do bloco:", options=[5, 10, 15, 20, 25], value=10)

# --- Aplicação dos Filtros ---
questoes_filtradas = todas_questoes
if origem_sel != "Todas as Origens":
    questoes_filtradas = [q for q in questoes_filtradas if q["fonte"] == origem_sel]

if bloco_sel != "Todos os Blocos":
    questoes_filtradas = [q for q in questoes_filtradas if q["bloco"] == bloco_sel]

if assunto_sel != "Todos os Assuntos":
    questoes_filtradas = [q for q in questoes_filtradas if q["assunto"] == assunto_sel]

if subtema_sel != "Todos os Subtemas":
    questoes_filtradas = [q for q in questoes_filtradas if q["subtema"] == subtema_sel]

if modo_estudo == "Caderno de Erros (Apenas Erradas)":
    questoes_filtradas = [q for q in questoes_filtradas if q["id"] in progresso and not progresso[q["id"]].get("acertou")]
elif modo_estudo == "Apenas Não Resolvidas":
    questoes_filtradas = [q for q in questoes_filtradas if q["id"] not in progresso]

# --- Função de Renderização de Card de Questão ---
def html_para_markdown(fragmento):
    """Converte o HTML simples dos cadernos em Markdown compatível com KaTeX."""
    soup = BeautifulSoup(fragmento or "", "html.parser")
    for quebra in soup.find_all("br"):
        quebra.replace_with("\n\n")
    for negrito in soup.find_all(["strong", "b"]):
        negrito.replace_with(f"**{negrito.get_text()}**")
    return soup.get_text("", strip=False).strip()


def renderizar_fragmento(fragmento):
    """Renderiza Markdown/KaTeX e imagens locais mantendo a ordem do HTML."""
    soup = BeautifulSoup(fragmento or "", "html.parser")
    imagens = []
    for indice, img in enumerate(soup.find_all("img")):
        marcador = f"@@IMAGEM_LOCAL_{indice}@@"
        imagens.append({"src": img.get("src", ""), "alt": img.get("alt", "Diagrama da questão")})
        img.replace_with(f"\n\n{marcador}\n\n")

    conteudo = html_para_markdown(str(soup))
    partes = re.split(r"(@@IMAGEM_LOCAL_\d+@@)", conteudo)
    raiz_questoes = os.path.realpath(QUESTOES_DIR)
    for parte in partes:
        match = re.fullmatch(r"@@IMAGEM_LOCAL_(\d+)@@", parte.strip())
        if not match:
            if parte.strip():
                st.markdown(parte.strip())
            continue

        imagem = imagens[int(match.group(1))]
        caminho = os.path.realpath(os.path.join(QUESTOES_DIR, imagem["src"]))
        if caminho.startswith(raiz_questoes + os.sep) and os.path.isfile(caminho):
            st.image(caminho, caption=imagem["alt"], use_container_width=True)
        else:
            st.warning("Imagem da questão não encontrada.")


def extrair_alternativas(q):
    alternativas = []
    for indice, alt in enumerate(q["alternativas"]):
        match = re.search(r"<strong>([A-E])\)<\/strong>\s*(.*)", alt, re.DOTALL)
        if match:
            letra = match.group(1).upper()
            texto = html_para_markdown(match.group(2))
        else:
            letra = chr(ord("A") + indice)
            texto = html_para_markdown(alt)
        alternativas.append((letra, texto))
    return alternativas


def carregar_historico_simulados():
    return carregar_persistente(
        "simulados", st.session_state.usuario_id, SIMULADOS_FILE, []
    )


def salvar_resultado_simulado(resultado):
    historico = carregar_historico_simulados()
    historico.append(resultado)
    salvar_persistente(
        "simulados", st.session_state.usuario_id, SIMULADOS_FILE, historico[-50:]
    )


def limpar_estado_simulado():
    for chave in list(st.session_state):
        if chave.startswith("sim_resp_") or chave in {
            "simulado_ids", "simulado_inicio", "simulado_finalizado",
            "simulado_resultado", "simulado_temas_ausentes", "simulado_distribuicao"
        }:
            st.session_state.pop(chave, None)


def gerar_questoes_simulado(questoes):
    elegiveis = []
    for q in questoes:
        alternativas = extrair_alternativas(q)
        letras = [letra for letra, _ in alternativas]
        if len(alternativas) == 4 and q["gabarito"] in letras and q["gabarito"] in "ABCD":
            elegiveis.append(q)

    por_assunto = {}
    for q in elegiveis:
        por_assunto.setdefault(q["assunto"], []).append(q)
    for lista in por_assunto.values():
        random.shuffle(lista)

    escolhidas = []
    ids_escolhidos = set()
    contagem = {assunto: 0 for assunto in por_assunto}
    temas_ausentes = []

    for assunto, info in MAPEAMENTO_ASSUNTOS.items():
        candidatas = por_assunto.get(assunto, [])
        quantidade = min(info["esperadas"], len(candidatas))
        for q in candidatas[:quantidade]:
            escolhidas.append(q)
            ids_escolhidos.add(q["id"])
            contagem[assunto] = contagem.get(assunto, 0) + 1
        if quantidade < info["esperadas"]:
            temas_ausentes.append(assunto)

    restantes = {
        assunto: [q for q in lista if q["id"] not in ids_escolhidos]
        for assunto, lista in por_assunto.items()
    }
    while len(escolhidas) < TOTAL_QUESTOES_SIMULADO:
        disponiveis = [assunto for assunto, lista in restantes.items() if lista]
        if not disponiveis:
            break
        menor_contagem = min(contagem.get(assunto, 0) for assunto in disponiveis)
        menos_representados = [
            assunto for assunto in disponiveis if contagem.get(assunto, 0) == menor_contagem
        ]
        assunto = random.choice(menos_representados)
        q = restantes[assunto].pop()
        escolhidas.append(q)
        ids_escolhidos.add(q["id"])
        contagem[assunto] = contagem.get(assunto, 0) + 1

    random.shuffle(escolhidas)
    distribuicao = {
        assunto: quantidade for assunto, quantidade in sorted(contagem.items()) if quantidade > 0
    }
    return escolhidas, temas_ausentes, distribuicao


def iniciar_simulado():
    limpar_estado_simulado()
    escolhidas, ausentes, distribuicao = gerar_questoes_simulado(todas_questoes)
    if len(escolhidas) < TOTAL_QUESTOES_SIMULADO:
        return False
    st.session_state.simulado_ids = [q["id"] for q in escolhidas]
    st.session_state.simulado_inicio = time.time()
    st.session_state.simulado_finalizado = False
    st.session_state.simulado_temas_ausentes = ausentes
    st.session_state.simulado_distribuicao = distribuicao
    return True


def finalizar_simulado(questoes_simulado):
    respostas = {
        q["id"]: st.session_state.get(f"sim_resp_{q['id']}")
        for q in questoes_simulado
    }
    acertos = sum(1 for q in questoes_simulado if respostas[q["id"]] == q["gabarito"])
    duracao = max(0, int(time.time() - st.session_state.simulado_inicio))
    detalhes = []
    por_assunto = {}

    for q in questoes_simulado:
        resposta = respostas[q["id"]]
        acertou = resposta == q["gabarito"]
        registrar_tentativa(q, resposta, acertou, origem="simulado_especifico")
        resumo = por_assunto.setdefault(q["assunto"], {"total": 0, "acertos": 0})
        resumo["total"] += 1
        resumo["acertos"] += int(acertou)
        detalhes.append({
            "id": q["id"], "resposta": resposta, "gabarito": q["gabarito"], "acertou": acertou
        })

    salvar_progresso(progresso)
    resultado = {
        "data": datetime.now().isoformat(timespec="seconds"),
        "total": len(questoes_simulado),
        "acertos": acertos,
        "pontos": acertos * 2,
        "duracao_segundos": duracao,
        "por_assunto": por_assunto,
        "detalhes": detalhes
    }
    salvar_resultado_simulado(resultado)
    st.session_state.simulado_resultado = resultado
    st.session_state.simulado_finalizado = True


def formatar_duracao(segundos):
    minutos, segundos = divmod(segundos, 60)
    horas, minutos = divmod(minutos, 60)
    return f"{horas:02d}:{minutos:02d}:{segundos:02d}"


def renderizar_plano_simulado():
    linhas = []
    for assunto, info in MAPEAMENTO_ASSUNTOS.items():
        disponiveis = sum(1 for q in todas_questoes if q["assunto"] == assunto)
        linhas.append({
            "Bloco": info["bloco"].title(),
            "Tema": assunto,
            "Esperadas/20": info["esperadas"],
            "Meta do banco": info["meta"],
            "Disponíveis": disponiveis
        })
    st.dataframe(linhas, use_container_width=True, hide_index=True)


def renderizar_simulado():
    st.title("📝 Simulado específico • Engenharia Elétrica")
    st.caption(
        "Modelo: 20 questões, alternativas A–D, 2 pontos por acerto e total de 40 pontos. "
        "O tempo-alvo de 90 minutos é proporcional às 3 horas da prova e serve apenas para treino."
    )

    with st.expander(f"Ver divisão planejada dos {len(MAPEAMENTO_ASSUNTOS)} temas", expanded=False):
        st.info(
            "A quantidade por tema é uma estimativa estratégica. O edital define 20 questões específicas, "
            "mas não fixa quantas serão cobradas de cada assunto."
        )
        renderizar_plano_simulado()

    if "simulado_ids" not in st.session_state:
        st.subheader("Pronto para começar?")
        st.write(
            "A correção e as resoluções só aparecem depois da finalização. "
            "Enquanto faltarem cadernos, as vagas dos temas indisponíveis serão distribuídas de forma equilibrada entre os existentes."
        )
        if st.button("Gerar simulado de 20 questões", type="primary", use_container_width=True):
            if iniciar_simulado():
                st.rerun()
            else:
                st.error("Ainda não há 20 questões elegíveis com quatro alternativas e gabarito válido.")
        return

    por_id = {q["id"]: q for q in todas_questoes}
    questoes_simulado = [por_id[q_id] for q_id in st.session_state.simulado_ids if q_id in por_id]
    if len(questoes_simulado) != TOTAL_QUESTOES_SIMULADO:
        st.error("Um dos cadernos usados neste simulado foi alterado. Gere um novo simulado.")
        if st.button("Descartar e gerar novamente"):
            limpar_estado_simulado()
            st.rerun()
        return

    if st.session_state.get("simulado_temas_ausentes"):
        st.warning(
            f"Cobertura parcial do edital: {len(st.session_state.simulado_temas_ausentes)} dos {len(MAPEAMENTO_ASSUNTOS)} temas ainda não possuem caderno. "
            "As vagas foram redistribuídas entre os temas disponíveis."
        )

    finalizado = st.session_state.get("simulado_finalizado", False)
    if not finalizado:
        decorrido = int(time.time() - st.session_state.simulado_inicio)
        st.info(f"Tempo decorrido: **{formatar_duracao(decorrido)}** • tempo-alvo: **01:30:00**")

    for indice, q in enumerate(questoes_simulado, start=1):
        with st.container(border=True):
            st.markdown(f"### Questão {indice} de {TOTAL_QUESTOES_SIMULADO}")
            if finalizado:
                st.caption(f"{q['assunto']} • {q['subtema']}")
            else:
                st.caption("Engenharia Elétrica • tema não identificado durante a prova")
            renderizar_fragmento(q["enunciado"])
            alternativas = extrair_alternativas(q)
            for letra, texto in alternativas:
                st.markdown(f"**{letra})** {texto}")

            if not finalizado:
                st.radio(
                    "Sua resposta:",
                    [letra for letra, _ in alternativas],
                    key=f"sim_resp_{q['id']}",
                    index=None,
                    horizontal=True
                )
            else:
                resultado = st.session_state.simulado_resultado
                detalhe = next(item for item in resultado["detalhes"] if item["id"] == q["id"])
                if detalhe["acertou"]:
                    st.success(f"Você marcou **{detalhe['resposta']}**. Gabarito: **{detalhe['gabarito']}**.")
                else:
                    st.error(f"Você marcou **{detalhe['resposta']}**. Gabarito: **{detalhe['gabarito']}**.")
                with st.expander("Ver resolução", expanded=False):
                    renderizar_fragmento(q["resolucao"])
                    if q["dica"]:
                        renderizar_fragmento(q["dica"])

    if not finalizado:
        respondidas = sum(
            bool(st.session_state.get(f"sim_resp_{q['id']}")) for q in questoes_simulado
        )
        st.progress(respondidas / TOTAL_QUESTOES_SIMULADO)
        st.write(f"**Respondidas:** {respondidas} de {TOTAL_QUESTOES_SIMULADO}")
        if st.button(
            "Finalizar e corrigir",
            type="primary",
            use_container_width=True,
            disabled=respondidas < TOTAL_QUESTOES_SIMULADO
        ):
            finalizar_simulado(questoes_simulado)
            st.rerun()
        if respondidas < TOTAL_QUESTOES_SIMULADO:
            st.caption("Responda às 20 questões para liberar a correção.")
    else:
        resultado = st.session_state.simulado_resultado
        st.divider()
        st.subheader("Resultado")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Acertos", f"{resultado['acertos']} / {resultado['total']}")
        col2.metric("Pontuação", f"{resultado['pontos']} / 40")
        col3.metric("Aproveitamento", f"{resultado['acertos'] / resultado['total'] * 100:.1f}%")
        col4.metric("Tempo", formatar_duracao(resultado["duracao_segundos"]))
        linhas = [
            {
                "Tema": assunto,
                "Acertos": dados["acertos"],
                "Questões": dados["total"],
                "Aproveitamento": f"{dados['acertos'] / dados['total'] * 100:.0f}%"
            }
            for assunto, dados in sorted(resultado["por_assunto"].items())
        ]
        st.dataframe(linhas, use_container_width=True, hide_index=True)
        st.button(
            "Fazer novo simulado",
            type="primary",
            use_container_width=True,
            on_click=limpar_estado_simulado
        )


def abrir_tema_para_estudo(assunto, bloco, somente_pendentes=False):
    st.session_state["modo_aplicacao_app"] = "Estudo por cadernos"
    st.session_state["filtro_origem"] = "Todas as Origens"
    st.session_state["filtro_bloco"] = bloco
    st.session_state["filtro_assunto"] = assunto
    st.session_state["filtro_subtema"] = "Todos os Subtemas"
    st.session_state["filtro_status"] = (
        "Apenas Não Resolvidas" if somente_pendentes else "Todas as Questões"
    )
    st.session_state["filtro_visualizacao"] = "Uma por vez (Modo Estudo / Slide)"
    st.session_state.idx_individual = 0


def renderizar_trilha_edital():
    dados = calcular_trilha(todas_questoes, progresso, st.session_state.trilha)
    st.title("🧭 Trilha do edital")
    st.caption(
        "O painel combina importância estratégica, domínio estimado, atraso de revisão "
        "e subtemas ainda não praticados para sugerir o estudo do dia."
    )

    st.subheader("O que estudar hoje")
    colunas = st.columns(3)
    for indice, (coluna, item) in enumerate(zip(colunas, dados[:3]), start=1):
        with coluna:
            with st.container(border=True):
                st.caption(f"PRIORIDADE {indice} • BLOCO {item['bloco']}")
                st.markdown(f"#### {item['assunto']}")
                st.metric("Prioridade", f"{item['prioridade']:.0f}/100")
                st.write(f"**Estado:** {item['estado']}")
                st.write(item["acao"])
                st.button(
                    "Estudar agora",
                    key=f"abrir_trilha_{indice}",
                    use_container_width=True,
                    on_click=abrir_tema_para_estudo,
                    args=(item["assunto"], item["bloco"], bool(item["subtemas_pendentes"]))
                )

    estados = Counter(item["estado"] for item in dados)
    consolidados = estados.get("Consolidado", 0)
    iniciados = len(dados) - estados.get("Não iniciado", 0)
    dominio_medio = sum(item["dominio"] for item in dados) / len(dados) if dados else 0
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Temas iniciados", f"{iniciados}/{len(dados)}")
    m2.metric("Consolidados", consolidados)
    m3.metric("Domínio médio", f"{dominio_medio:.0f}%")
    m4.metric("Questões respondidas", len(progresso))

    st.subheader("Painel completo")
    linhas = []
    for item in dados:
        dias = "Nunca" if item["dias_sem_revisar"] is None else item["dias_sem_revisar"]
        linhas.append({
            "Prioridade": item["prioridade"],
            "Tema": item["assunto"],
            "Bloco": item["bloco"].title(),
            "Estado": item["estado"],
            "Respondidas": f"{item['respondidas']}/{item['disponiveis']}",
            "Acerto": f"{item['taxa_acerto'] * 100:.0f}%" if item["tentativas"] else "—",
            "Subtemas pendentes": f"{len(item['subtemas_pendentes'])}/{item['subtemas_total']}",
            "Dias sem revisar": dias,
            "Domínio": item["dominio"],
        })
    st.dataframe(
        linhas,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Prioridade": st.column_config.ProgressColumn(
                "Prioridade", min_value=0, max_value=100, format="%.0f"
            ),
            "Domínio": st.column_config.ProgressColumn(
                "Domínio estimado", min_value=0, max_value=100, format="%.0f%%"
            ),
        },
    )

    with st.expander("Como a prioridade e o domínio são calculados"):
        st.markdown(
            "**Prioridade = 35% peso estratégico + 30% lacuna de domínio + "
            "20% atraso de revisão + 15% lacuna de cobertura.**\n\n"
            "O peso estratégico é Ouro = 100%, Prata = 70% e Bronze = 45%. "
            "O domínio não é apenas a taxa de acerto: ele também exige volume de questões "
            "e cobertura de subtemas, evitando considerar um assunto dominado após poucos acertos."
        )

    st.subheader("Ajustar tema e registrar revisão")
    nomes = [item["assunto"] for item in dados]
    tema = st.selectbox("Tema", nomes, key="trilha_tema_ajuste")
    item = next(d for d in dados if d["assunto"] == tema)
    configuracao = st.session_state.trilha.get(tema, {})
    opcoes_estado = ["Automático"] + ESTADOS_TRILHA
    estado_salvo = configuracao.get("estado", "Automático")
    if estado_salvo not in opcoes_estado:
        estado_salvo = "Automático"
    estado_escolhido = st.selectbox(
        "Estado do tema",
        opcoes_estado,
        index=opcoes_estado.index(estado_salvo),
        help=f"Estado sugerido atualmente: {item['estado_automatico']}",
        key=f"trilha_estado_{hashlib.sha1(tema.encode('utf-8')).hexdigest()[:10]}",
    )

    c1, c2 = st.columns(2)
    if c1.button("Salvar estado", type="primary", use_container_width=True):
        registro = st.session_state.trilha.setdefault(tema, {})
        if estado_escolhido == "Automático":
            registro.pop("estado", None)
        else:
            registro["estado"] = estado_escolhido
        salvar_trilha(st.session_state.trilha)
        st.rerun()
    if c2.button("Registrar revisão de hoje", use_container_width=True):
        registro = st.session_state.trilha.setdefault(tema, {})
        registro["ultima_revisao"] = datetime.now().isoformat(timespec="seconds")
        salvar_trilha(st.session_state.trilha)
        st.rerun()

    if item["subtemas_pendentes"]:
        st.markdown(f"**Subtemas ainda não cobrados no seu estudo ({len(item['subtemas_pendentes'])}):**")
        for subtema in item["subtemas_pendentes"]:
            st.markdown(f"- {subtema}")
    else:
        st.success("Todos os subtemas disponíveis deste caderno já apareceram no seu estudo.")


def renderizar_questao(q):
    q_id = q["id"]
    historico = progresso.get(q_id, None)
    cor_bloco = "🥇 OURO" if q["bloco"] == "OURO" else ("🥈 PRATA" if q["bloco"] == "PRATA" else "🥉 BRONZE")
    
    with st.container(border=True):
        col_t1, col_t2 = st.columns([3, 1])
        col_t1.markdown(f"### {q['numero']} • `{q['subtema']}`")
        col_t1.caption(f"**Assunto:** {q['assunto']} &nbsp;|&nbsp; **Bloco:** {cor_bloco}")
        if q["fonte"] != "Questões autorais":
            referencia = q["prova_fonte"]
            if q["questao_original"]:
                referencia += f" • questão original {q['questao_original']}"
            col_t1.caption(f"**Origem:** {q['fonte']} &nbsp;|&nbsp; {referencia}")
        
        if historico:
            if historico.get("acertou"):
                col_t2.success("✅ Acertou")
            else:
                col_t2.warning(f"❌ Errada (Marcou: {historico.get('resposta', '-')})")
        
        renderizar_fragmento(q["enunciado"])
        st.write("")
        
        letras_disponiveis = []
        for letra, texto_markdown in extrair_alternativas(q):
            letras_disponiveis.append(letra)
            st.markdown(f"**{letra})** {texto_markdown}")

        escolha = st.radio(
            "Selecione a alternativa:",
            letras_disponiveis,
            key=f"radio_{q_id}",
            index=None,
            horizontal=True
        )
        
        col_btn1, col_btn2 = st.columns([1, 4])
        confirmar = col_btn1.button("Confirmar Resposta", key=f"btn_{q_id}", type="primary")
        
        if confirmar and escolha:
            letra_escolhida = escolha
            gabarito_correto = q["gabarito"]
            acertou = (letra_escolhida == gabarito_correto)
            
            registrar_tentativa(q, letra_escolhida, acertou)
            salvar_progresso(progresso)
            st.rerun()

        st.write("")
        if historico:
            rotulo_gabarito = "Gabarito comentado" if q["fonte"] != "Questões autorais" else "Gabarito oficial"
            with st.expander(f"💡 Ver {rotulo_gabarito} & Resolução Detalhada", expanded=False):
                if historico.get("acertou"):
                    st.success(f"**{rotulo_gabarito}:** Alternativa **{q['gabarito']}** (Você acertou!)")
                else:
                    st.error(f"**{rotulo_gabarito}:** Alternativa **{q['gabarito']}** (Na última tentativa você marcou **{historico.get('resposta')}**)")
                renderizar_fragmento(q["resolucao"])
                if q["dica"]:
                    renderizar_fragmento(q["dica"])
        else:
            st.caption("Confirme uma resposta para liberar o gabarito e a resolução.")

# --- Área Principal ---
if modo_aplicacao == "Trilha do edital":
    renderizar_trilha_edital()
    st.stop()

if modo_aplicacao == "Simulado específico":
    renderizar_simulado()
    st.stop()

st.title("📚 Resolução de Questões IDECAN")

if assunto_sel != "Todos os Assuntos":
    if origem_sel != "Todas as Origens":
        questoes_origem = [
            q for q in todas_questoes
            if q["assunto"] == assunto_sel and q["fonte"] == origem_sel
        ]
        feitas_origem = sum(q["id"] in progresso for q in questoes_origem)
        st.info(
            f"📌 **Assunto:** {assunto_sel} | **{origem_sel}:** "
            f"{feitas_origem} de {len(questoes_origem)} questões feitas"
        )
    else:
        meta_atual = next((q["meta"] for q in todas_questoes if q["assunto"] == assunto_sel), 50)
        feitas_assunto = sum(
            1 for q in todas_questoes
            if q["assunto"] == assunto_sel
            and q["fonte"] == "Questões autorais"
            and q["id"] in progresso
        )
        st.info(
            f"📌 **Assunto:** {assunto_sel} | **Progresso do caderno-base:** "
            f"{feitas_assunto} de {meta_atual} questões feitas "
            f"({min(feitas_assunto/meta_atual*100, 100.0):.0f}% da meta)"
        )

total_q = len(questoes_filtradas)

if total_q == 0:
    st.success("🎉 Nenhuma questão encontrada com os filtros selecionados!")
else:
    # 1. Modo Individual (Slide / Um por vez)
    if formato_visualizacao == "Uma por vez (Modo Estudo / Slide)":
        if st.session_state.idx_individual >= total_q:
            st.session_state.idx_individual = total_q - 1
        if st.session_state.idx_individual < 0:
            st.session_state.idx_individual = 0

        col_nav1, col_nav2, col_nav3 = st.columns([1, 2, 1])
        
        with col_nav1:
            if st.button("⬅️ Anterior", disabled=(st.session_state.idx_individual == 0), use_container_width=True):
                st.session_state.idx_individual -= 1
                st.rerun()
                
        with col_nav2:
            novo_idx = st.selectbox(
                "Ir para questão:",
                options=list(range(total_q)),
                index=st.session_state.idx_individual,
                format_func=lambda x: f"Questão {x+1} de {total_q} ({questoes_filtradas[x]['numero']})",
                label_visibility="collapsed"
            )
            if novo_idx != st.session_state.idx_individual:
                st.session_state.idx_individual = novo_idx
                st.rerun()

        with col_nav3:
            if st.button("Próxima ➡️", disabled=(st.session_state.idx_individual >= total_q - 1), use_container_width=True):
                st.session_state.idx_individual += 1
                st.rerun()

        st.divider()
        renderizar_questao(questoes_filtradas[st.session_state.idx_individual])

    # 2. Modo em Blocos Menores (Paginação)
    elif formato_visualizacao == "Em blocos menores (Paginação)":
        total_pags = (total_q + tam_bloco - 1) // tam_bloco
        
        if st.session_state.pagina_lote > total_pags:
            st.session_state.pagina_lote = max(1, total_pags)

        col_pag1, col_pag2, col_pag3 = st.columns([1, 2, 1])
        
        with col_pag1:
            if st.button("⬅️ Bloco Anterior", disabled=(st.session_state.pagina_lote <= 1), use_container_width=True):
                st.session_state.pagina_lote -= 1
                st.rerun()
                
        with col_pag2:
            st.markdown(f"<p style='text-align:center; font-size:16px; margin-top:5px;'><b>Bloco {st.session_state.pagina_lote} de {total_pags}</b> (Mostrando {tam_bloco} questões por página)</p>", unsafe_allow_html=True)
            
        with col_pag3:
            if st.button("Próximo Bloco ➡️", disabled=(st.session_state.pagina_lote >= total_pags), use_container_width=True):
                st.session_state.pagina_lote += 1
                st.rerun()

        inicio = (st.session_state.pagina_lote - 1) * tam_bloco
        fim = min(inicio + tam_bloco, total_q)
        
        st.divider()
        for q in questoes_filtradas[inicio:fim]:
            renderizar_questao(q)

    # 3. Modo Lista Completa Contínua
    else:
        st.caption(f"Mostrando todas as **{total_q}** questões em rolagem única:")
        for q in questoes_filtradas:
            renderizar_questao(q)
