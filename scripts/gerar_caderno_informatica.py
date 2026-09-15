from collections import Counter
from html import escape
from pathlib import Path


QUESTOES = []


def adicionar(subtema, enunciado, contexto, alternativas, gabarito, resolucao, dica):
    QUESTOES.append(
        {
            "subtema": subtema,
            "enunciado": enunciado,
            "contexto": contexto,
            "alternativas": alternativas,
            "gabarito": gabarito,
            "resolucao": resolucao,
            "dica": dica,
        }
    )


# 1–5 • Hardware, armazenamento, memórias, periféricos, extensões e arquivos.
adicionar(
    "Hardware • Memória RAM e armazenamento",
    "Um computador abre vários programas simultaneamente e passa a alternar dados com o SSD, ficando lento, embora ainda haja bastante espaço livre no disco. A providência com maior relação direta com o gargalo descrito é:",
    "Situação: uso de memória em 96%; uso do processador em 38%; unidade de armazenamento com 62% de espaço livre.",
    [
        "Trocar o monitor por outro de maior resolução, reduzindo a carga mantida na memória principal.",
        "Ampliar a memória RAM, diminuindo a necessidade de paginação frequente no armazenamento.",
        "Formatar a unidade em outro sistema de arquivos, aumentando a frequência de operação do processador.",
        "Instalar uma fonte de alimentação mais potente, elevando a capacidade lógica dos aplicativos abertos.",
    ],
    "B",
    "O uso de RAM próximo do limite faz o sistema recorrer à memória virtual no SSD, muito mais lenta que a RAM. Mais RAM reduz a paginação. Monitor, sistema de arquivos e potência da fonte não ampliam a memória disponível aos processos.",
    "Cruze os indicadores: identifique qual recurso está saturado antes de escolher o componente a substituir.",
)
adicionar(
    "Arquivos • Extensões e formatos",
    "Ao receber quatro arquivos, um servidor precisa identificar aquele que, por padrão, representa uma pasta de trabalho de planilha eletrônica moderna, preservando fórmulas e múltiplas abas. Qual extensão atende ao requisito?",
    "Arquivos recebidos: planejamento.csv | planejamento.xlsx | planejamento.pdf | planejamento.txt",
    [
        "`.csv`, pois conserva nativamente várias planilhas, fórmulas e formatação em um único arquivo.",
        "`.pdf`, pois permite recalcular fórmulas depois da importação sem converter o documento.",
        "`.txt`, pois armazena células tipadas e referências entre abas por meio de texto simples.",
        "`.xlsx`, pois é um formato de pasta de trabalho que pode manter fórmulas, estilos e várias planilhas.",
    ],
    "D",
    "XLSX é formato de pasta de trabalho do Excel e preserva fórmulas, formatação e abas. CSV e TXT são formatos textuais e não guardam toda essa estrutura; PDF prioriza apresentação, não recálculo de células.",
    "Não associe extensão apenas ao programa que consegue abri-la; observe quais estruturas o formato realmente preserva.",
)
adicionar(
    "Armazenamento • Capacidade e unidades",
    "Considerando, para fins da questão, `1 GiB = 1.024 MiB`, quantos arquivos de 256 MiB cabem integralmente em uma unidade com 5 GiB livres, desconsiderando metadados e perdas de formatação?",
    "Use exclusivamente a relação binária fornecida no enunciado.",
    [
        "20 arquivos, porque 5 GiB correspondem a 5.120 MiB e cada arquivo ocupa 256 MiB.",
        "19 arquivos, porque a conversão binária reserva automaticamente 256 MiB para o sistema operacional.",
        "21 arquivos, porque a capacidade livre deve ser arredondada para a unidade binária imediatamente superior.",
        "25 arquivos, porque cada gibibyte contém exatamente cinco blocos independentes de 256 MiB.",
    ],
    "A",
    "A capacidade é 5 × 1.024 = 5.120 MiB. Dividindo por 256 MiB, obtêm-se 20 arquivos completos. Não há reserva indicada no enunciado nem arredondamento para cima.",
    "Converta primeiro todas as grandezas para a mesma unidade e só depois faça a divisão inteira.",
)
adicionar(
    "Periféricos • Entrada, saída e funções combinadas",
    "Em um posto de atendimento, o equipamento X digitaliza documentos em papel e também imprime comprovantes. Quanto à classificação funcional, X é:",
    "O equipamento reúne scanner e impressora no mesmo gabinete e se comunica com o computador por rede.",
    [
        "Um periférico exclusivamente de entrada, porque a digitalização ocorre antes da impressão do comprovante.",
        "Um periférico exclusivamente de saída, porque o resultado final do atendimento é produzido em papel.",
        "Um periférico de entrada e saída, pois captura dados do papel e materializa dados do computador.",
        "Uma memória secundária, pois mantém temporariamente os trabalhos enviados pela rede para impressão.",
    ],
    "C",
    "A função de scanner é entrada; a de impressora é saída. A fila temporária de impressão não transforma o equipamento em memória secundária. A classificação considera todas as funções, não apenas a etapa final.",
    "Classifique cada operação pelo sentido do fluxo de dados em relação ao computador.",
)
adicionar(
    "Hardware • Processador, cache e desempenho",
    "Sobre a memória cache localizada no processador ou muito próxima dele, assinale a alternativa correta.",
    "Considere a hierarquia típica: registradores, cache, RAM e armazenamento secundário.",
    [
        "Substitui permanentemente o SSD e conserva os arquivos do usuário mesmo quando o equipamento é desligado.",
        "Mantém dados e instruções de acesso frequente para reduzir a latência média entre processador e memória principal.",
        "É utilizada apenas pelo sistema de vídeo e sua capacidade determina diretamente a resolução máxima do monitor.",
        "Possui capacidade superior à RAM e velocidade inferior ao armazenamento magnético para reduzir o consumo elétrico.",
    ],
    "B",
    "A cache explora localidade temporal e espacial para servir rapidamente dados e instruções ao processador. Ela é pequena e rápida, volátil e não substitui armazenamento persistente nem se limita ao vídeo.",
    "Na hierarquia de memória, quanto mais próxima da CPU, menor tende a ser a capacidade e maior a velocidade.",
)

# 6–11 • Windows/Linux, diretórios, atalhos, área de trabalho, clipboard e manipulação.
adicionar(
    "Sistemas operacionais • Caminhos Windows e Linux",
    "Assinale a alternativa que apresenta, respectivamente, um caminho absoluto típico do Windows e um caminho absoluto típico do Linux.",
    "A questão considera a sintaxe usual dos dois sistemas, sem compartilhamentos de rede.",
    [
        "`C:\\Projetos\\rede.xlsx` e `/home/ana/rede.xlsx`.",
        "`/C/Projetos/rede.xlsx` e `home:\\ana\\rede.xlsx`.",
        "`Projetos\\rede.xlsx` e `home/ana/rede.xlsx`.",
        "`C:Projetos/rede.xlsx` e `\\home\\ana\\rede.xlsx`.",
    ],
    "A",
    "No Windows, um caminho absoluto local normalmente começa pela letra da unidade e barra invertida. No Linux, começa por `/`, a raiz. As demais combinações omitem raiz/unidade ou misturam convenções.",
    "Procure os marcadores de raiz: `C:\\` no Windows e `/` no Linux.",
)
adicionar(
    "Manipulação de arquivos • Copiar, mover e atalhos",
    "Um usuário arrastou um arquivo para outra pasta e, depois, criou na área de trabalho um atalho para o arquivo. Sobre essas operações, assinale a afirmativa correta.",
    "O atalho possui localização própria, mas aponta para o arquivo de destino.",
    [
        "O atalho é uma segunda cópia integral; se o arquivo original for alterado, a cópia permanece necessariamente diferente.",
        "Mover e copiar são sempre equivalentes, pois ambas as operações mantêm obrigatoriamente o original no local inicial.",
        "Excluir o atalho remove também o arquivo de destino, pois os dois passam a compartilhar o mesmo conteúdo físico.",
        "Excluir apenas o atalho normalmente não exclui o arquivo apontado, embora mover o destino possa quebrar a referência.",
    ],
    "D",
    "Atalho é uma referência ao destino, não uma duplicação do conteúdo. Sua exclusão não apaga normalmente o alvo; já mover ou renomear o alvo pode invalidar a referência. Copiar e mover também não são operações equivalentes.",
    "Separe três objetos: o arquivo original, uma eventual cópia e o arquivo de atalho que contém a referência.",
)
adicionar(
    "Área de transferência • Copiar, recortar e colar",
    "Um texto foi selecionado no editor, recortado e colado em outro parágrafo. Qual descrição representa corretamente o papel da área de transferência?",
    "Sequência executada: selecionar → recortar → posicionar o cursor → colar.",
    [
        "Conserva obrigatoriamente o conteúdo de modo permanente, mesmo após reinicialização e sem recurso de histórico habilitado.",
        "Cria uma cópia impressa do trecho e impede que ele seja reutilizado em outro programa compatível.",
        "Mantém temporariamente os dados recortados ou copiados para que possam ser inseridos em outro local ou aplicativo.",
        "Armazena somente nomes de arquivos, não podendo receber texto, imagem ou outros formatos de dados.",
    ],
    "C",
    "A área de transferência é armazenamento temporário para operações de copiar/recortar e colar, podendo transportar diferentes tipos de dados. Persistência após reinicialização depende de recursos específicos, não é regra geral.",
    "Não confunda a área de transferência com uma pasta do disco: sua função é intermediar a movimentação lógica de dados.",
)
adicionar(
    "Sistemas operacionais • Permissões de acesso",
    "Em um diretório compartilhado, um usuário consegue abrir e ler um relatório, mas não consegue modificá-lo nem apagá-lo. A explicação mais compatível é que ele possui:",
    "O arquivo está íntegro e outros usuários autorizados conseguem editá-lo normalmente.",
    [
        "Permissão de execução sem leitura, condição que permite visualizar o conteúdo, mas bloqueia qualquer alteração.",
        "Permissão de leitura, sem as permissões necessárias de escrita e exclusão no arquivo ou diretório.",
        "Privilégio administrativo completo, mas com cache do navegador temporariamente desativado.",
        "Permissão de gravação sem leitura, condição que apresenta o conteúdo em modo protegido pelo sistema.",
    ],
    "B",
    "A capacidade de visualizar indica leitura; o bloqueio de edição indica ausência de escrita. A exclusão pode depender das permissões do arquivo e do diretório. Cache de navegador não explica permissões do sistema de arquivos.",
    "Trate leitura, escrita, execução e exclusão como capacidades distintas.",
)
adicionar(
    "Arquivos e pastas • Compactação",
    "Uma pasta com diversos documentos foi compactada em um arquivo `.zip` para envio. É correto afirmar que a compactação:",
    "O destinatário precisa recuperar os documentos individualmente após receber o arquivo.",
    [
        "Pode reunir vários itens em um único arquivo e, conforme os dados, reduzir seu tamanho sem alterar logicamente os originais extraídos.",
        "Transforma definitivamente todos os documentos em imagens rasterizadas, eliminando fórmulas, textos pesquisáveis e metadados estruturados dos arquivos.",
        "Criptografa obrigatoriamente todo o conteúdo com uma chave forte, dispensando senha, controle de acesso e qualquer proteção adicional no envio.",
        "Garante a mesma taxa de redução para qualquer formato, inclusive arquivos que já empregam compressão interna eficiente de dados.",
    ],
    "A",
    "ZIP pode agrupar arquivos e aplicar compressão sem perdas. A taxa varia; formatos já comprimidos podem reduzir pouco. Compactação não significa conversão para imagem nem criptografia obrigatória.",
    "Separe três conceitos frequentemente confundidos: agrupar/comprimir, converter formato e criptografar.",
)
adicionar(
    "Sistemas operacionais • Associação de arquivos",
    "Ao clicar duas vezes em um arquivo `.pdf`, ele passou a abrir em outro programa depois que o usuário alterou o aplicativo padrão. Isso ocorreu porque o sistema operacional modificou:",
    "O conteúdo e a extensão do arquivo permaneceram inalterados.",
    [
        "A tabela de partições da unidade, que determina qual programa interpreta cada documento armazenado.",
        "A permissão de execução do arquivo, convertendo o documento em aplicativo autônomo do sistema.",
        "O endereço físico dos setores do arquivo, direcionando-os ao executável selecionado pelo usuário.",
        "A associação entre o tipo/extensão do arquivo e o aplicativo usado por padrão para abri-lo.",
    ],
    "D",
    "A associação de arquivos informa qual aplicativo deve tratar determinado tipo. Ela não altera o conteúdo, a extensão, a partição ou transforma o PDF em executável.",
    "Se o mesmo arquivo abre em outro programa sem ser convertido, procure uma configuração de associação, não de formato.",
)

# 12–17 • Editores de texto.
adicionar(
    "Editor de textos • Quebra de página e de seção",
    "Em um documento, somente uma página deverá ficar em orientação paisagem, enquanto as páginas anteriores e posteriores permanecerão em retrato. O procedimento mais adequado é:",
    "A mudança deve ficar restrita à página que contém uma tabela larga.",
    [
        "Inserir várias linhas vazias antes e depois da tabela e aplicar orientação paisagem ao documento inteiro.",
        "Aplicar uma quebra de página simples antes da tabela e alterar a orientação de todas as páginas seguintes.",
        "Isolar a página com quebras de seção e definir a orientação paisagem apenas para essa seção.",
        "Converter a tabela em cabeçalho, pois cabeçalhos podem usar orientação independente dentro da mesma página.",
    ],
    "C",
    "Propriedades como orientação podem ser definidas por seção. Uma quebra de página muda o ponto de início, mas não cria necessariamente um trecho com configuração independente. Linhas vazias são solução frágil.",
    "Quando a formatação de página deve mudar apenas em uma parte, pense em seções.",
)
adicionar(
    "Editor de textos • Estilos, títulos e índice",
    "Para gerar e atualizar automaticamente um índice/sumário a partir dos títulos de um relatório, a prática mais adequada é:",
    "O relatório recebe novos capítulos durante várias revisões.",
    [
        "Aplicar estilos hierárquicos de título aos cabeçalhos e inserir um sumário baseado nesses estilos.",
        "Digitar manualmente títulos e números de página, ajustando os espaços sempre que o texto mudar.",
        "Transformar cada título em caixa de texto, pois objetos flutuantes atualizam automaticamente a paginação.",
        "Usar apenas negrito e tamanho maior, sem informar ao editor qualquer nível estrutural dos títulos.",
    ],
    "A",
    "Estilos de título fornecem estrutura semântica para o sumário automático e permitem atualização após mudanças. Aparência manual, caixas de texto ou espaços não fornecem a mesma estrutura confiável.",
    "Diferencie aparência visual de estrutura: o sumário precisa reconhecer níveis de título.",
)
adicionar(
    "Editor de textos • Cabeçalhos e numeração",
    "Um relatório possui capa sem número visível e capítulos numerados a partir da página seguinte. Qual recurso atende melhor a essa organização?",
    "A capa continua pertencendo ao arquivo, mas deve ter cabeçalho/rodapé diferente.",
    [
        "Ocultar manualmente o número com uma forma branca, mantendo todas as páginas vinculadas ao mesmo rodapé.",
        "Usar a configuração de primeira página diferente e, quando necessário, ajustar a seção e o início da numeração.",
        "Inserir o número como texto comum no final de cada página, sem utilizar cabeçalho ou rodapé.",
        "Converter a capa em imagem e removê-la do documento antes de cada impressão ou exportação.",
    ],
    "B",
    "Editores oferecem primeira página diferente e controles de seção/numeração. Isso mantém paginação automática sem artifícios gráficos ou edição manual de cada página.",
    "Procure recursos de layout que automatizem a exceção; não simule a ausência do número com objetos sobrepostos.",
)
adicionar(
    "Editor de textos • Legendas e referências cruzadas",
    "Uma figura numerada como “Figura 4” pode mudar de posição e passar a ser “Figura 5”. Para que a menção feita no texto acompanhe a alteração automaticamente, deve-se usar:",
    "O documento contém várias figuras inseridas e removidas durante a revisão.",
    [
        "Uma nota digitada manualmente, repetindo o número atual da figura em todas as ocorrências do documento.",
        "Um hiperlink para qualquer página do arquivo, pois o texto exibido é sempre renumerado pelo editor.",
        "Uma caixa de texto vinculada à margem, independente da legenda e da ordem dos objetos inseridos.",
        "Uma legenda automática associada à figura e uma referência cruzada inserida no corpo do texto.",
    ],
    "D",
    "Legenda automática cria um campo numerado; referência cruzada aponta para esse campo e pode ser atualizada após reordenação. Digitação manual e caixas de texto não garantem sincronização.",
    "Quando dois trechos precisam permanecer sincronizados, procure campos e referências, não repetição manual.",
)
adicionar(
    "Editor de textos • Tabelas e ordenação",
    "Em uma tabela de três colunas, deseja-se ordenar os registros pelo campo “Setor” e, em caso de empate, pelo campo “Servidor”, mantendo cada linha íntegra. Deve-se:",
    "Colunas: Servidor | Setor | Matrícula. A primeira linha contém cabeçalhos.",
    [
        "Selecionar apenas a coluna Setor e ordenar seus textos, deixando as demais colunas nas posições originais.",
        "Converter a tabela em imagem e ordenar visualmente as linhas com recorte e colagem de fragmentos.",
        "Ordenar a tabela inteira, indicando Setor como primeira chave e Servidor como segunda, com cabeçalho reconhecido.",
        "Classificar somente a coluna Matrícula, pois a chave numérica preserva automaticamente os vínculos das outras colunas.",
    ],
    "C",
    "A ordenação deve abranger as linhas completas e usar chaves sucessivas. Ordenar uma coluna isoladamente pode separar nomes, setores e matrículas; transformar em imagem elimina a estrutura editável.",
    "Em dados tabulares, confirme sempre se a operação movimentará registros completos ou apenas células isoladas.",
)
adicionar(
    "Editor de textos • Localizar e substituir",
    "Um documento utiliza repetidamente a expressão “Secretaria de Obras”, mas apenas as ocorrências formatadas em itálico devem ser substituídas. Qual estratégia é mais segura?",
    "Há ocorrências idênticas sem itálico que precisam permanecer inalteradas.",
    [
        "Usar localizar e substituir com critério de formatação, revisando as ocorrências antes de aplicar a substituição.",
        "Executar substituir tudo apenas pelo texto, pois o editor preservará automaticamente as ocorrências sem itálico.",
        "Apagar todas as ocorrências e redigitar somente as que deveriam continuar no documento final.",
        "Converter o documento em PDF e editar diretamente os caracteres, dispensando critérios de pesquisa.",
    ],
    "A",
    "A pesquisa avançada pode combinar conteúdo e formatação, permitindo substituir apenas o subconjunto desejado. Substituição textual simples alcançaria também ocorrências que devem permanecer.",
    "Quando há exceções, refine os critérios e evite o comando global antes de conferir uma amostra.",
)

# 18–24 • Planilhas eletrônicas.
adicionar(
    "Planilhas • Referências relativas, absolutas e mistas",
    "Na célula C2 foi digitada a fórmula `=B2*$F$1`. Ao copiá-la para C5, qual fórmula será produzida?",
    "B2 contém o valor do item da linha; F1 contém uma taxa única usada por todas as linhas.",
    [
        "`=B2*$F$1`, pois toda referência de uma fórmula copiada permanece invariável.",
        "`=B5*$F$1`, pois B2 é relativa e F1 está fixa em coluna e linha.",
        "`=$B$5*F1`, pois a cópia torna absoluta a referência que muda de linha.",
        "`=B5*$F5`, pois apenas a coluna F está protegida pelo primeiro símbolo `$`.",
    ],
    "B",
    "Ao deslocar três linhas, B2 torna-se B5. A referência `$F$1` é absoluta nos dois eixos e permanece igual. O símbolo `$` não é criado automaticamente nem fixa apenas parte quando aparece antes de coluna e linha.",
    "Leia separadamente coluna e linha: cada componente precedido por `$` fica fixo.",
)
adicionar(
    "Planilhas • Função condicional",
    "A célula D2 deve exibir “Aprovado” quando C2 for maior ou igual a 70 e “Revisar” nos demais casos. Na sintaxe em português com separador `;`, a fórmula adequada é:",
    "C2 contém uma nota numérica entre 0 e 100.",
    [
        "`=SE(C2>=70;\"Aprovado\";\"Revisar\")`.",
        "`=SOMA(C2>=70;\"Aprovado\";\"Revisar\")`.",
        "`=SE(C2<=70;\"Aprovado\";\"Revisar\")`.",
        "`=CONT.SE(C2;>=70;\"Aprovado\";\"Revisar\")`.",
    ],
    "D",
    "A função SE recebe teste lógico, valor se verdadeiro e valor se falso. O teste requerido é C2>=70. SOMA e CONT.SE têm outras finalidades, e inverter o operador aprovaria notas abaixo do limite.",
    "Traduza a regra em três partes: condição; resultado verdadeiro; resultado falso.",
)
adicionar(
    "Planilhas • Contagem por critério",
    "Na faixa B2:B101 aparecem os estados “Concluído”, “Pendente” e “Cancelado”. Para contar somente as células iguais a “Pendente”, utiliza-se:",
    "Considere nomes de funções em português e separador de argumentos `;`.",
    [
        "`=SOMA(B2:B101;\"Pendente\")`, porque textos são convertidos automaticamente em unidades.",
        "`=CONT.NÚM(B2:B101;\"Pendente\")`, porque a função conta qualquer conteúdo que não esteja vazio.",
        "`=CONT.SE(B2:B101;\"Pendente\")`, porque aplica um critério de igualdade à faixa.",
        "`=MÉDIASE(B2:B101;\"Pendente\")`, porque a média de textos corresponde ao número de ocorrências.",
    ],
    "C",
    "CONT.SE conta células que atendem a um critério. CONT.NÚM conta números; SOMA agrega valores numéricos; MÉDIASE calcula média de valores associados a um critério.",
    "Associe o verbo do enunciado à família da função: contar + uma condição = CONT.SE.",
)
adicionar(
    "Planilhas • Classificação e integridade dos registros",
    "Uma tabela possui Nome, Cargo e Nota. Para ordenar por Nota sem desassociar cada pessoa de seu cargo, é necessário:",
    "Cada linha corresponde a um único candidato e a primeira linha contém os cabeçalhos.",
    [
        "Selecionar apenas a coluna Nota e aceitar a ordenação isolada, mantendo Nome e Cargo imóveis.",
        "Ordenar o intervalo completo da tabela pela coluna Nota, reconhecendo a existência da linha de cabeçalho.",
        "Copiar a coluna Nota para outra planilha e ordenar somente essa cópia, substituindo depois os valores originais.",
        "Converter as notas em texto antes de classificar, pois textos preservam automaticamente as relações entre linhas.",
    ],
    "B",
    "A linha é o registro. Ordenar todo o intervalo move conjuntamente Nome, Cargo e Nota. Ordenar apenas a coluna pode romper a correspondência; converter números em texto ainda pode produzir ordem inadequada.",
    "Antes de classificar, identifique o limite completo da tabela e confirme se existe cabeçalho.",
)
adicionar(
    "Planilhas • Escolha de gráfico",
    "Para comparar a evolução mensal do consumo de energia de três prédios ao longo de doze meses, o gráfico geralmente mais apropriado é:",
    "O objetivo principal é observar tendência temporal e comparar as três séries.",
    [
        "Gráfico de linhas, com os meses no eixo horizontal e uma série para cada prédio.",
        "Gráfico de setores, com 36 fatias, porque cada mês deve representar uma proporção independente do tempo.",
        "Histograma, com os nomes dos prédios como classes contínuas e os meses tratados como frequências.",
        "Gráfico de dispersão sem eixo temporal, porque a ordem cronológica prejudica a comparação entre séries.",
    ],
    "A",
    "Linhas evidenciam continuidade e tendências no tempo e permitem comparar séries. Setores servem melhor a composição de um total; histograma mostra distribuição; dispersão exige pares numéricos e outro objetivo analítico.",
    "Escolha o gráfico pela pergunta: evolução no tempo costuma favorecer linhas.",
)
adicionar(
    "Planilhas • Dados externos e atualização",
    "Uma planilha importa dados de um arquivo externo que é atualizado diariamente. Para repetir a obtenção sem copiar e colar tudo a cada dia, convém:",
    "A estrutura da fonte permanece estável, mas os registros são acrescentados.",
    [
        "Inserir uma captura de tela da fonte, pois imagens atualizam automaticamente quando o arquivo original muda.",
        "Digitar uma macro desconhecida recebida por e-mail e habilitar todo conteúdo sem revisar sua origem.",
        "Converter a fonte em papel e usar reconhecimento óptico a cada atualização para preservar os tipos das células.",
        "Criar uma consulta/conexão com a fonte e usar o comando de atualização, conferindo tipos e etapas de transformação.",
    ],
    "D",
    "Consultas e conexões permitem repetir importação e transformação de dados. Capturas não mantêm estrutura; OCR adiciona erros; macros desconhecidas representam risco e não são requisito para importar dados.",
    "Quando a tarefa é repetitiva e a fonte é estável, procure um processo atualizável, não uma nova cópia manual.",
)
adicionar(
    "Planilhas • Impressão e títulos repetidos",
    "Uma planilha extensa será impressa em várias páginas. O cabeçalho das colunas deve aparecer no topo de todas elas. O recurso adequado é:",
    "A primeira linha contém os rótulos Data, Setor, Serviço e Situação.",
    [
        "Definir a primeira linha como título de impressão a repetir em cada página.",
        "Congelar a primeira linha na tela, pois o congelamento também a imprime automaticamente em todas as folhas.",
        "Inserir manualmente cópias da linha em intervalos fixos, independentemente das quebras calculadas na impressão.",
        "Aplicar filtro à primeira linha, porque os botões do filtro funcionam como cabeçalhos físicos de todas as páginas.",
    ],
    "A",
    "Títulos de impressão repetem linhas ou colunas nas páginas impressas. Congelar painéis afeta a visualização na tela, não necessariamente a impressão. Cópias manuais são frágeis quando as quebras mudam.",
    "Não confunda recursos de navegação em tela com configurações de layout de impressão.",
)

# 25–27 • Correio eletrônico.
adicionar(
    "Correio eletrônico • Cc e Cco",
    "Um comunicado será enviado a muitos destinatários externos que não devem visualizar os endereços uns dos outros. O preenchimento mais adequado é:",
    "O remetente precisa preservar a privacidade da lista de destinatários.",
    [
        "Inserir toda a lista em Cco e usar o campo Para apenas para um endereço institucional apropriado, se necessário.",
        "Inserir toda a lista em Cc, pois esse campo oculta os endereços dos demais destinatários externos.",
        "Inserir cada endereço no assunto da mensagem para que o servidor de e-mail faça a distribuição privada.",
        "Anexar a lista de endereços à mensagem e deixar vazios os campos Para, Cc e Cco.",
    ],
    "A",
    "Cco envia cópias sem expor a lista aos demais destinatários. Cc é visível; assunto não roteia mensagens; algum campo de destinatário precisa ser utilizado pelo serviço.",
    "Pergunte quem poderá enxergar cada endereço: Cc é cópia visível; Cco é cópia oculta.",
)
adicionar(
    "Correio eletrônico • Anexos e links",
    "Um arquivo grande excede o limite de anexos do serviço de e-mail. Sem reduzir sua qualidade, uma solução apropriada é:",
    "O destinatário possui autorização para acessar o documento, que não deve ficar público.",
    [
        "Renomear a extensão do arquivo para `.txt`, pois isso reduz automaticamente seu conteúdo sem causar corrupção.",
        "Divulgar o arquivo em uma rede social aberta e encaminhar a publicação a todos os destinatários.",
        "Colocar o arquivo em armazenamento em nuvem, conceder acesso restrito e enviar o link correspondente.",
        "Copiar o conteúdo binário para o corpo do e-mail, pois o limite de tamanho se aplica somente ao campo de anexo.",
    ],
    "D",
    "O procedimento tecnicamente adequado é compartilhar por nuvem com permissão restrita e enviar o link. A alternativa correspondente descreve essa ação, apesar da posição D no gabarito; renomear extensão não comprime e publicação aberta viola a restrição."
    .replace("A alternativa correspondente descreve essa ação, apesar da posição D no gabarito; ", ""),
    "Verifique conjuntamente tamanho e controle de acesso: o link deve resolver o limite sem tornar o arquivo público.",
)
adicionar(
    "Correio eletrônico • Phishing e resposta segura",
    "Uma mensagem afirma que a conta será bloqueada em dez minutos e solicita login por um botão encurtado. O remetente parece conhecido, mas o domínio apresenta uma letra trocada. A ação mais segura é:",
    "A mensagem explora urgência e imita a identidade visual do serviço utilizado pelo órgão.",
    [
        "Clicar no botão, verificar se a página parece legítima e só então decidir se informa a senha.",
        "Não usar o link; acessar o serviço pelo endereço oficial conhecido e reportar a mensagem pelo canal adequado.",
        "Responder com a senha atual para confirmar que o remetente realmente possui acesso ao cadastro institucional.",
        "Encaminhar a mensagem a todos os colegas para que cada um teste o endereço e compare o resultado obtido.",
    ],
    "B",
    "Urgência, domínio semelhante e pedido de credenciais são sinais de phishing. O acesso deve ocorrer por endereço oficial digitado ou favorito confiável, e a mensagem deve ser reportada. Testar o link ou compartilhar aumenta a exposição.",
    "Não avalie apenas o logotipo; confirme domínio, contexto do pedido e canal de acesso.",
)

# 28–30 • Comunicação e reuniões on-line.
adicionar(
    "Reuniões on-line • Compartilhamento de tela",
    "Durante uma reunião em ferramenta como Teams, Meet ou Zoom, o apresentador precisa exibir apenas os slides, sem revelar notificações de outros aplicativos. Deve preferir:",
    "Outros programas permanecerão abertos durante a apresentação.",
    [
        "Compartilhar a tela inteira e confiar que as notificações não aparecerão durante a reunião.",
        "Enviar sua senha ao organizador para que ele controle remotamente todos os aplicativos abertos.",
        "Compartilhar somente a janela ou guia da apresentação e, adicionalmente, silenciar notificações sensíveis.",
        "Ativar o microfone de todos os participantes, pois o áudio coletivo bloqueia avisos visuais do sistema.",
    ],
    "C",
    "Compartilhar apenas a janela/guia limita o conteúdo visível; desativar notificações reduz vazamentos acidentais. Tela inteira amplia a exposição; senha e microfones não são mecanismos adequados.",
    "Antes de compartilhar, delimite a menor superfície necessária para a tarefa.",
)
adicionar(
    "Reuniões on-line • Controle de participantes",
    "Em uma reunião pública com muitos participantes, começaram interrupções por microfones abertos e tentativas de entrada com nomes desconhecidos. O organizador deve:",
    "A reunião utiliza recursos comuns de moderação disponíveis em plataformas de videoconferência.",
    [
        "Utilizar sala de espera ou controle de admissão e restringir microfones conforme a dinâmica definida.",
        "Publicar o link em canais adicionais e remover a senha para facilitar a identificação dos participantes.",
        "Conceder função de organizador a todos, permitindo que qualquer participante aprove novas entradas.",
        "Desativar o registro de participantes, pois a ausência de identificação impede interrupções no áudio.",
    ],
    "A",
    "Sala de espera/admissão controla entradas, e permissões de áudio ajudam na moderação. Expor o link, retirar proteção ou ampliar privilégios piora o risco; remover registro não impede interrupções.",
    "Associe cada problema ao controle correspondente: entrada desconhecida → admissão; ruído → permissão de áudio.",
)
adicionar(
    "Ferramentas de comunicação • Sincronia e recursos",
    "Microsoft Teams, Google Meet, Zoom e serviços historicamente incluídos em editais, como Skype e Google Hangouts, são associados principalmente a:",
    "Considere a finalidade geral dessas ferramentas, sem depender da disponibilidade atual de um produto específico.",
    [
        "Particionamento de discos e recuperação física de setores defeituosos em unidades de armazenamento.",
        "Edição exclusiva de planilhas locais sem comunicação entre usuários ou compartilhamento de conteúdo.",
        "Compilação de sistemas operacionais e gerenciamento direto de memória do computador do participante.",
        "Comunicação síncrona por áudio/vídeo e colaboração remota, com recursos que variam entre os serviços.",
    ],
    "B",
    "A alternativa correta deveria descrever comunicação síncrona, que aparece na opção D; logo a posição indicada inicialmente seria inconsistente."
    .replace("A alternativa correta deveria descrever comunicação síncrona, que aparece na opção D; logo a posição indicada inicialmente seria inconsistente.", "Essas ferramentas são voltadas à comunicação síncrona e colaboração remota; particionamento, edição local exclusiva e compilação de sistemas não constituem sua finalidade principal."),
    "Identifique a categoria funcional comum, sem tentar memorizar um botão específico de cada versão.",
)

# 31–35 • Internet, intranet, extranet, protocolos, busca, navegadores, nuvem e redes sociais.
adicionar(
    "Internet • Estrutura de URL",
    "Na URL `https://portal.exemplo.gov.br/servicos?id=27`, o trecho `https` identifica:",
    "URL analisada: https://portal.exemplo.gov.br/servicos?id=27",
    [
        "O nome do arquivo físico obrigatoriamente armazenado no computador do usuário.",
        "O domínio de primeiro nível responsável por identificar o órgão governamental.",
        "O esquema/protocolo usado para acessar o recurso, com comunicação HTTP protegida por TLS.",
        "O parâmetro de consulta enviado ao servidor para selecionar o serviço de número 27.",
    ],
    "D",
    "O trecho antes de `://` é o esquema; aqui, HTTPS representa HTTP sobre uma conexão protegida por TLS. O domínio é `portal.exemplo.gov.br`, o caminho é `/servicos` e `id=27` é parâmetro."
    .replace("O trecho antes de `://` é o esquema; aqui, HTTPS representa HTTP sobre uma conexão protegida por TLS.", "O trecho antes de `://` é o esquema; aqui, HTTPS representa HTTP sobre uma conexão protegida por TLS."),
    "Decomponha a URL em esquema, domínio, caminho e parâmetros antes de analisar as alternativas.",
)
adicionar(
    "Redes • Internet, intranet e extranet",
    "Uma prefeitura mantém um portal interno para servidores e permite que empresas contratadas acessem, mediante autenticação, apenas a área de acompanhamento dos contratos. Essa área controlada para parceiros caracteriza:",
    "O acesso externo é limitado a usuários e recursos previamente autorizados.",
    [
        "Uma extranet, por estender parte dos recursos institucionais a agentes externos autenticados.",
        "Uma internet pública irrestrita, porque qualquer acesso fora do prédio elimina controles institucionais.",
        "Uma área de transferência, pois os parceiros podem enviar e receber documentos pela mesma interface.",
        "Uma rede social aberta, porque empresas e servidores pertencem a organizações distintas.",
    ],
    "C",
    "A descrição corresponde a extranet, opção A. A posição C foi usada como armadilha no rascunho e precisa ser corrigida na geração."
    .replace("A descrição corresponde a extranet, opção A. A posição C foi usada como armadilha no rascunho e precisa ser corrigida na geração.", "Extranet disponibiliza parte de uma rede ou serviço institucional a parceiros externos autenticados. Não se torna acesso público irrestrito nem se confunde com clipboard ou rede social."),
    "Pergunte quem acessa: só público interno sugere intranet; parceiros autorizados sugerem extranet; acesso geral sugere internet pública.",
)
adicionar(
    "Navegadores • Cache e cookies",
    "Após uma atualização, um portal continua exibindo uma versão antiga de uma imagem em determinado navegador. Limpar o cache resolve o problema. Isso ocorre porque o cache:",
    "O mesmo portal já mostrava a imagem nova em outro dispositivo.",
    [
        "Armazena cópias locais de recursos para acelerar acessos e pode reutilizar temporariamente uma versão anterior.",
        "Guarda exclusivamente senhas do usuário e sua limpeza modifica obrigatoriamente as credenciais no servidor.",
        "Funciona como firewall do navegador e bloqueia qualquer arquivo cujo conteúdo tenha sido atualizado recentemente.",
        "Substitui o DNS da rede e determina permanentemente qual endereço IP todos os dispositivos devem utilizar.",
    ],
    "A",
    "Cache local reduz transferências ao reutilizar recursos, podendo exibir versão desatualizada até revalidação ou limpeza. Senhas, firewall e DNS são mecanismos distintos.",
    "Se o problema afeta um dispositivo e envolve conteúdo antigo, considere dados locais do navegador.",
)
adicionar(
    "Pesquisa na internet • Operadores de busca",
    "Um usuário deseja resultados que contenham exatamente a expressão `segurança da informação`, com as palavras juntas e nessa ordem. Em mecanismos que aceitam o operador, deve pesquisar:",
    "A intenção é restringir a ocorrência à frase exata, não apenas às palavras separadas.",
    [
        "`segurança OR informação`, ampliando a busca para páginas que contenham qualquer um dos termos.",
        "`-segurança -informação`, excluindo da busca todas as páginas que contenham os dois termos.",
        "`segurança + informação`, obrigando o mecanismo a procurar exclusivamente arquivos de planilha.",
        "`\"segurança da informação\"`, solicitando a correspondência da expressão colocada entre aspas.",
    ],
    "B",
    "Aspas são usadas para pesquisa de frase exata, portanto a alternativa correspondente é D; OR amplia resultados e o sinal de menos exclui termos."
    .replace("Aspas são usadas para pesquisa de frase exata, portanto a alternativa correspondente é D; ", "Aspas delimitam uma frase exata; "),
    "Observe o efeito dos operadores: aspas restringem uma frase; OR amplia alternativas; menos exclui termos.",
)
adicionar(
    "Computação em nuvem • Sincronização e compartilhamento",
    "Um documento sincronizado na nuvem foi compartilhado com permissão “somente leitura”. Em condições normais, o destinatário:",
    "O proprietário não concedeu permissão de edição nem criou uma cópia independente para o destinatário.",
    [
        "Pode alterar o original e substituir versões anteriores, mas não consegue visualizar o conteúdo publicado.",
        "Pode visualizar o documento, porém não deve conseguir modificar diretamente o original compartilhado.",
        "Passa a ser proprietário do arquivo e pode remover o acesso de quem realizou o compartilhamento.",
        "Recebe acesso automático a todos os demais arquivos existentes na conta de nuvem do proprietário.",
    ],
    "D",
    "Permissão de somente leitura permite visualizar sem editar o original, descrição apresentada na opção B. As demais ampliam privilégios inexistentes."
    .replace("Permissão de somente leitura permite visualizar sem editar o original, descrição apresentada na opção B.", "Permissão de somente leitura permite visualizar sem editar diretamente o original."),
    "Não extrapole a permissão concedida: acesso a um item não implica propriedade nem acesso à conta inteira.",
)

# 36–40 • Segurança da informação, backup, assinatura digital, antivírus, firewall e ataques.
adicionar(
    "Segurança da informação • Confidencialidade, integridade e disponibilidade",
    "Um arquivo foi alterado sem autorização, embora tenha permanecido acessível e sem divulgação a terceiros. O princípio diretamente comprometido foi:",
    "Não houve interrupção do serviço nem evidência de leitura por pessoa não autorizada.",
    [
        "Disponibilidade, porque qualquer modificação torna o arquivo tecnicamente inacessível ao usuário autorizado.",
        "Confidencialidade, porque alteração e leitura por terceiros representam necessariamente o mesmo evento.",
        "Integridade, porque o conteúdo deixou de permanecer correto e inalterado contra modificação indevida.",
        "Autenticidade física, porque todo arquivo alterado perde obrigatoriamente sua localização no armazenamento.",
    ],
    "C",
    "Integridade protege a exatidão e a não alteração indevida. Disponibilidade trata de acesso quando necessário; confidencialidade, de divulgação não autorizada. O cenário exclui esses dois efeitos.",
    "Associe o verbo ao princípio: revelar → confidencialidade; alterar → integridade; indisponibilizar → disponibilidade.",
)
adicionar(
    "Backup • Estratégia 3-2-1",
    "Uma organização mantém os arquivos de produção e duas cópias de segurança, em pelo menos dois tipos de mídia, sendo uma cópia armazenada fora do ambiente principal. Essa prática corresponde à estratégia:",
    "O objetivo é reduzir falhas simultâneas por defeito local, erro humano ou incidente no prédio.",
    [
        "3-2-1: três cópias dos dados, em duas mídias, com uma cópia fora do local principal.",
        "1-2-3: uma cópia em duas pastas e três atalhos apontando para o mesmo arquivo físico.",
        "RAID-0: duas cópias independentes, sendo uma necessariamente mantida em outro prédio.",
        "Espelhamento simples: três nomes para o mesmo arquivo, todos sujeitos ao mesmo evento local.",
    ],
    "A",
    "A regra 3-2-1 combina redundância, diversidade de mídia e separação geográfica/lógica. Atalhos e nomes não criam cópias; RAID-0 não oferece redundância e não equivale a backup externo.",
    "Conte dados, mídias e localização separadamente; cópia no mesmo equipamento não cobre todos os riscos.",
)
adicionar(
    "Segurança • Assinatura digital e criptografia",
    "Sobre assinatura digital e criptografia, assinale a alternativa correta.",
    "Considere mecanismos criptográficos corretamente implementados e chaves protegidas.",
    [
        "A assinatura digital torna o conteúdo secreto para todos, inclusive para quem possui acesso autorizado ao documento.",
        "A criptografia garante autoria por si só, mesmo quando uma chave compartilhada é conhecida por vários usuários.",
        "A assinatura digital elimina a necessidade de verificar certificado, integridade ou vínculo da chave com o signatário.",
        "A assinatura digital auxilia na autenticidade e integridade; a criptografia pode proteger a confidencialidade do conteúdo.",
    ],
    "D",
    "Assinatura digital vincula uma chave ao ato de assinar e permite detectar alterações; criptografia restringe leitura a quem possui a chave adequada. Um mecanismo não substitui automaticamente todas as verificações do outro.",
    "Separe as finalidades: assinar não é esconder; criptografar não identifica necessariamente uma pessoa.",
)
adicionar(
    "Segurança • Firewall e antivírus",
    "Uma estação possui antivírus atualizado e firewall ativo. Sobre a atuação dessas ferramentas, é correto afirmar que:",
    "Nenhum controle isolado oferece proteção absoluta contra todos os incidentes.",
    [
        "O firewall substitui atualizações do sistema, pois todo ataque depende exclusivamente de conexão externa bloqueável.",
        "O antivírus torna desnecessário controlar privilégios, porque qualquer programa malicioso é detectado antes de executar.",
        "O firewall controla tráfego conforme regras e o antivírus procura comportamentos ou artefatos maliciosos; ambos são camadas complementares.",
        "As duas ferramentas possuem função idêntica e devem usar sempre as mesmas assinaturas e regras de rede.",
    ],
    "C",
    "Firewall filtra conexões/tráfego; antivírus detecta e trata ameaças no sistema por assinaturas e análise comportamental. Eles se complementam e não substituem atualização, menor privilégio ou comportamento seguro.",
    "Desconfie de alternativas que atribuem proteção total ou dizem que uma camada elimina todas as outras.",
)
adicionar(
    "Malwares e ataques • Ransomware",
    "Após abrir um anexo malicioso, vários arquivos de uma rede ficaram cifrados e surgiu uma exigência de pagamento para suposta recuperação. O incidente é característico de:",
    "A equipe isolou o equipamento afetado e acionou o procedimento institucional de resposta a incidentes.",
    [
        "Adware legítimo, cuja função principal é otimizar o armazenamento exibindo anúncios administrativos.",
        "Ransomware, que pode cifrar ou bloquear dados e exigir pagamento, sem garantia de recuperação.",
        "Cookie de sessão, usado pelo navegador para organizar preferências e compactar arquivos de rede.",
        "Driver de dispositivo, que converte documentos em formato protegido durante uma atualização normal.",
    ],
    "B",
    "Cifragem/bloqueio acompanhada de extorsão caracteriza ransomware. Adware exibe publicidade; cookie mantém estado de navegação; driver permite comunicação com hardware. Backup testado e resposta a incidentes são defesas relevantes.",
    "Identifique o efeito e o objetivo do código: bloquear dados para extorquir aponta para ransomware.",
)


# Ajustes de letras: as alternativas mantêm a ordem exibida e o gabarito precisa apontar
# para o conteúdo correto. Esta lista é auditada abaixo e impede regressões acidentais.
GABARITO_CORRETO = [
    "B", "D", "A", "C", "B", "A", "D", "C", "B", "A",
    "D", "C", "A", "B", "D", "C", "A", "B", "D", "C",
    "A", "B", "D", "C", "A", "D", "B", "C", "A", "B",
    "D", "C", "A", "B", "D", "C", "A", "D", "C", "B",
]

# Alguns itens foram redigidos com a alternativa conceitualmente correta em posição
# diferente durante a elaboração. Reordenar aqui mantém o banco equilibrado sem deixar
# comentários artificiais ou pistas no texto final.
CORRECOES_DE_POSICAO = {
    19: ("D", "A"),  # função SE
    21: ("A", "B"),  # ordenação do intervalo completo
    22: ("B", "A"),  # gráfico de linhas
    24: ("C", "A"),  # títulos de impressão
    26: ("D", "C"),  # compartilhamento em nuvem por link restrito
    30: ("B", "D"),  # finalidade das ferramentas de reunião
    31: ("D", "C"),  # esquema HTTPS
    32: ("C", "A"),  # extranet
    34: ("B", "D"),  # pesquisa por frase exata
    35: ("D", "B"),  # somente leitura
}

for numero, (destino, origem) in CORRECOES_DE_POSICAO.items():
    questao = QUESTOES[numero - 1]
    i_destino = ord(destino) - ord("A")
    i_origem = ord(origem) - ord("A")
    questao["alternativas"][i_destino], questao["alternativas"][i_origem] = (
        questao["alternativas"][i_origem],
        questao["alternativas"][i_destino],
    )

for questao, letra in zip(QUESTOES, GABARITO_CORRETO):
    questao["gabarito"] = letra

assert len(QUESTOES) == 40
assert Counter(q["gabarito"] for q in QUESTOES) == Counter(
    {"A": 10, "B": 10, "C": 10, "D": 10}
)

TERMOS_DA_CORRETA = [
    "memória RAM", ".xlsx", "20 arquivos", "entrada e saída", "acesso frequente",
    "C:\\Projetos", "Excluir apenas o atalho", "temporariamente os dados", "Permissão de leitura", "reunir vários itens",
    "associação entre", "quebras de seção", "estilos hierárquicos", "primeira página diferente", "referência cruzada",
    "tabela inteira", "critério de formatação", "=B5*$F$1", "=SE(C2>=70", "=CONT.SE",
    "intervalo completo", "Gráfico de linhas", "consulta/conexão", "título de impressão", "lista em Cco",
    "armazenamento em nuvem", "endereço oficial", "somente a janela", "sala de espera", "Comunicação síncrona",
    "esquema/protocolo", "Uma extranet", "cópias locais", '"segurança da informação"', "visualizar o documento",
    "Integridade", "3-2-1", "autenticidade e integridade", "camadas complementares", "Ransomware",
]
for numero, (questao, termo) in enumerate(zip(QUESTOES, TERMOS_DA_CORRETA), 1):
    indice = ord(questao["gabarito"]) - ord("A")
    assert termo.casefold() in questao["alternativas"][indice].casefold(), (
        numero,
        questao["gabarito"],
        termo,
        questao["alternativas"][indice],
    )


CSS = """
body{font-family:Arial,sans-serif;color:#1e293b;background:#f8fafc;line-height:1.48}
.header{background:#0f172a;color:white;padding:18px;border-radius:8px;margin-bottom:18px}
.header h1{color:#38bdf8;margin:0 0 7px}.header p{margin:0;color:#cbd5e1}
.question-card{background:white;border:1px solid #cbd5e1;border-radius:7px;padding:14px;margin-bottom:18px}
.q-badge-table{width:100%}.q-number{font-weight:bold}.q-tag{text-align:right;color:#0369a1;font-size:.82em}
.text-base{background:#f8fafc;border-left:4px solid #0284c7;padding:10px;margin:10px 0}
.alt-item{margin:7px 0}.solution-box{background:#f1f5f9;border:1px solid #cbd5e1;border-radius:5px;padding:11px;margin-top:11px}
.sol-header{font-weight:bold;color:#047857}.tip-box{background:#fffbeb;border-left:3px solid #d97706;padding:9px;margin-top:9px}
.tip-title{font-weight:bold;color:#92400e}
"""


def contexto_html(texto):
    if not texto:
        return ""
    linhas = "<br>".join(escape(linha) for linha in texto.splitlines())
    return f'<div class="text-base"><strong>Dados para análise:</strong><br>{linhas}</div>'


partes = [
    '<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8">',
    f"<style>{CSS}</style></head><body>",
    '<div class="header"><h1>Caderno de 40 Questões • Noções de Informática</h1>'
    '<p>Hardware, sistemas operacionais, produtividade, internet e segurança • '
    'Conhecimentos Gerais • Padrão IDECAN</p></div>',
]

for numero, questao in enumerate(QUESTOES, 1):
    alternativas = "".join(
        f'<div class="alt-item"><strong>{chr(65 + indice)})</strong> {escape(texto)}</div>'
        for indice, texto in enumerate(questao["alternativas"])
    )
    partes.append(
        '<div class="question-card">'
        '<table class="q-badge-table"><tr>'
        f'<td class="q-number">Questão {numero:02d}</td>'
        f'<td class="q-tag">{escape(questao["subtema"])}</td>'
        '</tr></table>'
        f'<div class="q-statement">{contexto_html(questao["contexto"])}'
        f'{escape(questao["enunciado"])}</div>'
        f'<div class="alternatives">{alternativas}</div>'
        '<div class="solution-box">'
        f'<span class="sol-header">Gabarito Comentado: Alternativa {questao["gabarito"]}</span>'
        f'<div class="sol-text">{escape(questao["resolucao"])}</div>'
        '<div class="tip-box"><span class="tip-title">Como pensar nesta questão:</span> '
        f'{escape(questao["dica"])}</div></div></div>'
    )

partes.append("</body></html>")
saida = (
    Path(__file__).resolve().parents[1]
    / "questoes"
    / "caderno_40_questoes_informatica_idecan.html"
)
saida.write_text("\n".join(partes), encoding="utf-8")
print(saida)
