import streamlit as st
import os
import re
from bs4 import BeautifulSoup
import json
import hashlib
import hmac
import secrets
import uuid
from datetime import datetime
from filelock import FileLock

st.set_page_config(
    page_title="Treinador IDECAN - Engenharia Elétrica",
    page_icon="⚡",
    layout="wide"
)

QUESTOES_DIR = "questoes"
DADOS_USUARIOS_DIR = "dados_usuarios"
USUARIOS_FILE = os.path.join(DADOS_USUARIOS_DIR, "usuarios.json")
PROGRESSO_LEGADO_FILE = "progresso_usuario.json"

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


def gerar_hash_pin(pin, salt_hex=None):
    salt = bytes.fromhex(salt_hex) if salt_hex else secrets.token_bytes(16)
    pin_hash = hashlib.pbkdf2_hmac("sha256", pin.encode("utf-8"), salt, 200_000)
    return salt.hex(), pin_hash.hex()


def validar_pin(usuario, pin):
    _, calculado = gerar_hash_pin(pin, usuario["pin_salt"])
    return hmac.compare_digest(calculado, usuario["pin_hash"])


def carregar_usuarios():
    return carregar_json(USUARIOS_FILE, {})


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
        salvar_json(USUARIOS_FILE, usuarios)

        progresso_novo = os.path.join(DADOS_USUARIOS_DIR, f"{usuario_id}.json")
        if len(usuarios) == 1 and os.path.exists(PROGRESSO_LEGADO_FILE):
            salvar_json(progresso_novo, carregar_json(PROGRESSO_LEGADO_FILE, {}))
        else:
            salvar_json(progresso_novo, {})
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

    st.warning(
        "No Streamlit Community Cloud, arquivos locais podem ser apagados em reinicializações. "
        "Use o backup individual disponível após entrar."
    )
    st.stop()


tela_de_perfil()
PROGRESSO_FILE = os.path.join(DADOS_USUARIOS_DIR, f"{st.session_state.usuario_id}.json")

# --- Mapeamento do Edital: Assuntos, Blocos e Metas ---
MAPEAMENTO_ASSUNTOS = {
    # BLOCO OURO (Meta: ~45 a 50 questões por assunto)
    "NBR 5410 & Instalações BT": {"bloco": "OURO", "meta": 50, "keywords": ["5410", "BAIXA TENSÃO", "BT"]},
    "NBR 14039 & Instalações MT": {"bloco": "OURO", "meta": 45, "keywords": ["14039", "MEDIA TENSAO", "MÉDIA TENSÃO", "MT", "CABINE"]},
    "NR-10 & Segurança em Eletricidade": {"bloco": "OURO", "meta": 45, "keywords": ["NR-10", "NR10", "SEGURANÇA"]},
    "Grandezas Elétricas & Circuitos": {"bloco": "OURO", "meta": 45, "keywords": ["CIRCUITO", "POTENCIA", "POTÊNCIA", "FATOR DE POTENCIA", "TRIFASICO"]},
    "Aterramento e SPDA (NBR 5419)": {"bloco": "OURO", "meta": 45, "keywords": ["5419", "SPDA", "ATERRAMENTO", "DESCARGA"]},
    "Lei nº 14.133/2021 & Orçamentação/BDI": {"bloco": "OURO", "meta": 50, "keywords": ["14.133", "14133", "LICITACAO", "LICITAÇÃO", "BDI", "ORÇAMENTO", "CRONOGRAMA"]},

    # BLOCO PRATA (Meta: ~25 a 30 questões por assunto)
    "Sistemas de Potência (SEP) & NBR 5422": {"bloco": "PRATA", "meta": 25, "keywords": ["5422", "SEP", "TRANSMISSAO", "DISTRIBUICAO", "POTENCIA"]},
    "Luminotécnica & Iluminação Pública": {"bloco": "PRATA", "meta": 25, "keywords": ["LUMINOTECNICA", "LUMINOTÉCNICA", "ILUMINACAO PUBLICA"]},
    "Legislação Profissional & CONFEA/ART": {"bloco": "PRATA", "meta": 25, "keywords": ["5.194", "5194", "CONFEA", "CREA", "ART", "ETICA", "ÉTICA"]},
    "Manutenção & Gestão Predial": {"bloco": "PRATA", "meta": 25, "keywords": ["MANUTENCAO", "MANUTENÇÃO", "PREDITIVA", "PREVENTIVA"]},
    "Detecção e Alarme de Incêndio (SDAI)": {"bloco": "PRATA", "meta": 25, "keywords": ["INCENDIO", "INCÊNDIO", "SDAI", "ALARME"]},
    "Eficiência Energética & Fontes Renováveis": {"bloco": "PRATA", "meta": 25, "keywords": ["EFICIENCIA", "SOLAR", "FOTOVOLTAICA", "EOLICA", "BIOMASSA"]},
    "Fiscalização de Obras & NBR 9050": {"bloco": "PRATA", "meta": 25, "keywords": ["FISCALIZACAO", "FISCALIZAÇÃO", "9050", "ACESSIBILIDADE", "VISTORIA"]},

    # BLOCO BRONZE (Meta: ~10 a 15 questões por assunto)
    "Redes Estruturadas & Telefonia": {"bloco": "BRONZE", "meta": 15, "keywords": ["ESTRUTURADA", "CABEAMENTO", "TELEFONIA", "DADOS"]},
    "Desenho Técnico & Simbologia": {"bloco": "BRONZE", "meta": 15, "keywords": ["DESENHO", "PLANTA", "UNIFILAR", "SIMBOLOGIA"]},
    "Legislação Urbanística (Lei 6.766/1979)": {"bloco": "BRONZE", "meta": 15, "keywords": ["6.766", "6766", "URBANO", "POSTURAS", "PLANO DIRETOR"]},
    "Licenciamento Ambiental em Obras": {"bloco": "BRONZE", "meta": 15, "keywords": ["AMBIENTAL", "LICENCA", "LICENÇA", "EIA", "RIMA"]},
    "Comandos Elétricos & Acionamentos": {"bloco": "BRONZE", "meta": 15, "keywords": ["COMANDO", "CONTATOR", "PARTIDA", "INVERSOR", "SOFT-STARTER"]}
}

def identificar_assunto_e_bloco(nome_arquivo, tag_questao):
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
    return carregar_json(PROGRESSO_FILE, {})

def salvar_progresso(progresso):
    salvar_json(PROGRESSO_FILE, progresso)

if "progresso" not in st.session_state:
    st.session_state.progresso = carregar_progresso()

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
            q_id = f"{arq}_{q_num}_{idx}"
            
            questoes.append({
                "id": q_id,
                "origem": arq,
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

# Sincronização do progresso salvo
progresso = st.session_state.progresso
houve_ajuste = False
for q in todas_questoes:
    if q["id"] in progresso:
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
if st.sidebar.button("Trocar usuário", use_container_width=True):
    for chave in ("usuario_id", "usuario_nome", "progresso", "ultimo_upload_sig"):
        st.session_state.pop(chave, None)
    st.rerun()

if not todas_questoes:
    st.warning(f"Nenhum caderno `.html` encontrado na pasta `{QUESTOES_DIR}/`.")
    st.stop()

total_respondidas = len(progresso)
total_acertos = sum(1 for v in progresso.values() if v.get("acertou"))
taxa_acerto = (total_acertos / total_respondidas * 100) if total_respondidas > 0 else 0.0

st.sidebar.metric("Questões Feitas", f"{total_respondidas} / ~530")
st.sidebar.metric("Aproveitamento Global", f"{taxa_acerto:.1f}%")

st.sidebar.divider()
st.sidebar.subheader("🎯 Progresso por Bloco")

qtd_ouro = sum(1 for q in todas_questoes if q["id"] in progresso and q["bloco"] == "OURO")
qtd_prata = sum(1 for q in todas_questoes if q["id"] in progresso and q["bloco"] == "PRATA")
qtd_bronze = sum(1 for q in todas_questoes if q["id"] in progresso and q["bloco"] == "BRONZE")

st.sidebar.write(f"🥇 **Bloco Ouro:** {qtd_ouro} / 280 questões")
st.sidebar.progress(min(qtd_ouro / 280, 1.0))

st.sidebar.write(f"🥈 **Bloco Prata:** {qtd_prata} / 190 questões")
st.sidebar.progress(min(qtd_prata / 190, 1.0))

st.sidebar.write(f"🥉 **Bloco Bronze:** {qtd_bronze} / 60 questões")
st.sidebar.progress(min(qtd_bronze / 60, 1.0))

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

st.sidebar.divider()
st.sidebar.subheader("🔍 Filtros de Busca")

bloco_sel = st.sidebar.selectbox("1. Bloco do Edital:", ["Todos os Blocos", "OURO", "PRATA", "BRONZE"])

assuntos_filtrados = sorted(list(set(q["assunto"] for q in todas_questoes if (bloco_sel == "Todos os Blocos" or q["bloco"] == bloco_sel))))
assunto_sel = st.sidebar.selectbox("2. Assunto (Macro):", ["Todos os Assuntos"] + assuntos_filtrados)

subtemas_filtrados = sorted(list(set(q["subtema"] for q in todas_questoes if (
    (bloco_sel == "Todos os Blocos" or q["bloco"] == bloco_sel) and
    (assunto_sel == "Todos os Assuntos" or q["assunto"] == assunto_sel)
))))
subtema_sel = st.sidebar.selectbox("3. Subtema / Tag:", ["Todos os Subtemas"] + subtemas_filtrados)

modo_estudo = st.sidebar.radio(
    "4. Status das Questões:",
    ["Todas as Questões", "Caderno de Erros (Apenas Erradas)", "Apenas Não Resolvidas"]
)

st.sidebar.divider()
st.sidebar.subheader("👁️ Formato de Visualização")
formato_visualizacao = st.sidebar.radio(
    "Como deseja visualizar?",
    ["Uma por vez (Modo Estudo / Slide)", "Em blocos menores (Paginação)", "Lista completa contínua"]
)

tam_bloco = 10
if formato_visualizacao == "Em blocos menores (Paginação)":
    tam_bloco = st.sidebar.select_slider("Tamanho do bloco:", options=[5, 10, 15, 20, 25], value=10)

# --- Aplicação dos Filtros ---
questoes_filtradas = todas_questoes
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


def renderizar_questao(q):
    q_id = q["id"]
    historico = progresso.get(q_id, None)
    cor_bloco = "🥇 OURO" if q["bloco"] == "OURO" else ("🥈 PRATA" if q["bloco"] == "PRATA" else "🥉 BRONZE")
    
    with st.container(border=True):
        col_t1, col_t2 = st.columns([3, 1])
        col_t1.markdown(f"### {q['numero']} • `{q['subtema']}`")
        col_t1.caption(f"**Assunto:** {q['assunto']} &nbsp;|&nbsp; **Bloco:** {cor_bloco}")
        
        if historico:
            if historico.get("acertou"):
                col_t2.success("✅ Acertou")
            else:
                col_t2.warning(f"❌ Errada (Marcou: {historico.get('resposta', '-')})")
        
        st.markdown(html_para_markdown(q["enunciado"]))
        st.write("")
        
        letras_disponiveis = []
        for alt in q["alternativas"]:
            match = re.search(r"<strong>([A-E])\)<\/strong>\s*(.*)", alt, re.DOTALL)
            if match:
                letra = match.group(1).upper()
                texto_markdown = html_para_markdown(match.group(2))
            else:
                texto_markdown = html_para_markdown(alt)
                letra = chr(ord("A") + len(letras_disponiveis))
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
            
            progresso[q_id] = {
                "resposta": letra_escolhida,
                "acertou": acertou,
                "assunto": q["assunto"],
                "tema": q["subtema"],
                "bloco": q["bloco"],
                "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            salvar_progresso(progresso)
            st.rerun()

        # Gabarito e Resolução ocultos por padrão para não dar spoiler (expander fechado)
        st.write("")
        with st.expander("💡 Ver Gabarito Oficial & Resolução Detalhada", expanded=False):
            if historico:
                if historico.get("acertou"):
                    st.success(f"**Gabarito Oficial:** Alternativa **{q['gabarito']}** (Você acertou!)")
                else:
                    st.error(f"**Gabarito Oficial:** Alternativa **{q['gabarito']}** (Na última tentativa você marcou **{historico.get('resposta')}**)")
            else:
                st.info(f"**Gabarito Oficial:** Alternativa **{q['gabarito']}**")
                
            st.markdown(html_para_markdown(q["resolucao"]))
            if q["dica"]:
                st.markdown(html_para_markdown(q["dica"]))

# --- Área Principal ---
st.title("📚 Resolução de Questões IDECAN")

if assunto_sel != "Todos os Assuntos":
    meta_atual = next((q["meta"] for q in todas_questoes if q["assunto"] == assunto_sel), 50)
    feitas_assunto = sum(1 for q in todas_questoes if q["assunto"] == assunto_sel and q["id"] in progresso)
    st.info(f"📌 **Assunto:** {assunto_sel} | **Progresso:** {feitas_assunto} de {meta_atual} questões feitas ({min(feitas_assunto/meta_atual*100, 100.0):.0f}% da meta)")

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
