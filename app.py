"""
app.py — Sistema de Value Investing (Etapa 5 — Supabase + Login)

VERSÃO DESTE ARQUIVO: v2.5
GERADO EM: 2026-07-03 04:05 UTC (horário real do relógio do sistema no momento da geração)
ÚLTIMA MUDANÇA: Fluxo Guiado agora sempre começa em branco quando acessado
pelo menu lateral (antes continuava com a última empresa analisada, sem
avisar).

HISTÓRICO:
- v1.0 (2026-07-01): Correção do scraping do Fundamentus (bug 'Dív.Brut/Patrim.'),
  cotação em tempo real via yfinance, cadastro/edição de empresa com rating e
  dados de banco, Índice de Boa Empresa (cálculo + tela de screening).
- v1.1 (2026-07-02): Cabeçalho de versão adicionado.
- v1.2 (2026-07-02): Tela de Empresas reestruturada — ticker vira lista (uma
  empresa pode ter vários, ex: PETR3/PETR4) usando a tabela ativos_empresa;
  "Tipo mercado" agora representa Segmento de listagem B3 (Novo Mercado,
  Nível 1/2, Tradicional), separado de "Tipo de ativo"; Rating virou botão de
  busca (links de conferência manual, já que não há fonte pública raspável)
  + formulário de edição manual; todos os campos exceto Ticker e Razão Social
  agora são opcionais, com mensagem de erro clara quando falta algo
  obrigatório; "Novo setor" foi movido para a tela 10 (Tabelas de Apoio);
  botões de Indicadores / Análise de Boa Empresa / Histórico de Lucros /
  Notícias Relevantes / Futuro da Empresa agora só aparecem em modo edição
  (empresa já salva), não durante o cadastro de uma nova empresa.
- v1.3 (2026-07-02): Corrigido bug em que o Rating não gravava no banco (o
  upsert de uma empresa já existente agora usa UPDATE por id em vez de
  UPSERT, evitando depender de qual coluna o upsert usa como chave de
  conflito). Adicionada a função gravar_com_confirmacao(), aplicada em TODOS
  os pontos de gravação do app (~30 lugares): toda gravação agora mostra
  "✅ ... salvo com sucesso" SÓ quando o banco realmente confirmou, e
  "❌ Não foi possível salvar" com o motivo quando falha — nenhuma tela
  finge sucesso silenciosamente mais.
- v1.4 (2026-07-02): Causa raiz do bug do Rating CONFIRMADA pelo erro real
  que a v1.3 finalmente revelou: "null value in column razao_social... not
  null constraint" — ou seja, o sb_upsert("empresas", ...) do formulário de
  Rating estava tentando INSERIR uma linha nova (sem razao_social) em vez de
  ATUALIZAR a empresa existente. Troquei para sb_update por id (mesmo padrão
  já usado com sucesso no formulário principal). Ponto corrigido e validado.
- v1.5 (2026-07-02): Corrigido o motivo de "salvou mas não apareceu mensagem
  nenhuma" — o st.success()/st.error() era chamado logo antes de um
  st.rerun(), e o rerun recarregava a página rápido demais pra mensagem
  chegar a ser desenhada na tela. Agora a mensagem também é guardada em
  st.session_state e reexibida no topo da página assim que ela recarrega,
  então ela sempre aparece de fato. Também: a partir de agora a data/hora
  deste cabeçalho vem do relógio real no momento da geração, não é mais
  digitada à mão.
- v1.6 (2026-07-02): Comparando Fundamentus/Status Invest vs Yahoo Finance
  pra B3SA3, confirmado que o Yahoo Finance não tem balanço/DRE completo
  pra várias ações brasileiras ("Não encontrou dados de balanço recentes").
  Criada _buscar_fundamentus_detalhes() (raspa a página individual do papel
  no Fundamentus — mesma fonte já usada e comprovada no Screening) como
  fonte PRINCIPAL de balanço/DRE, com Yahoo Finance como reserva só se o
  Fundamentus não tiver a ação. Aplicado nos dois botões que buscam balanço
  automaticamente (Fluxo Guiado Etapa 1, e "Atualizar" na tela de Empresas).
  A fonte real (Fundamentus ou Yahoo Finance) agora aparece na mensagem de
  confirmação e fica registrada na coluna 'fonte'.
- v1.7 (2026-07-02): buscar_cotacao_tempo_real() agora também aceita índices
  (IBOV, S&P500 etc — equivalente ao =GOOGLEFINANCE("INDEXBVMF:IBOV") do
  Google Sheets) e devolve (preço, data_hora). Conectada na tela de Carteira:
  botão "🔄 Buscar cotações automáticas agora (todas)" busca o preço de
  todas as ações da carteira de uma vez e grava com data E hora completas
  (antes só gravava a data). O ajuste manual continua disponível como
  reserva/correção, mostrando quando cada preço foi atualizado pela última
  vez.
- v1.8 (2026-07-02): CAUSA RAIZ CONFIRMADA do bug "P/L, P/VP, Div.Yield e
  EV/EBITDA sempre zerados no Screening": a correspondência aproximada de
  colunas do Fundamentus checava se cada LETRA do nome aparecia solta em
  qualquer lugar da coluna — "P/L" (letras p, l) batia incorretamente com a
  coluna "papel" (que também tem p e l soltos em qualquer posição), e como
  "papel" é texto (não número), virava 0 pra todo mundo. Trocado por
  correspondência de SUBSTRING CONTÍGUA (ex.: "pl" precisa aparecer junto),
  testado e confirmado que resolve o caso exato do bug. Também ampliada a
  lista de nomes aceitos pra P/L, P/VP, Div.Yield e EV/EBITDA. Adicionada
  busca avançada por CNPJ/Razão Social na tela de Screening (dentro das
  empresas já cadastradas, complementando o filtro por indicadores que
  varre a B3 inteira).
- v1.9 (2026-07-02): O Screening (resultado.php) nunca teve CNPJ/razão
  social — confirmado que o Fundamentus só tem essas informações na página
  de detalhe de CADA papel, não na lista completa. Cadastro automático (ao
  clicar "Guardar seleção") agora chama buscar_perfil_empresa_fundamentus()
  pra pegar razão social/setor de verdade (cria o setor sozinho se ele ainda
  não existir), e buscar_cnpj_brapi() tenta o CNPJ via BrAPI (gratuita) —
  isso é best-effort: pode não vir pra toda ação, e nesse caso fica em
  branco pra completar manualmente na tela de Empresas. Atenção: a parte do
  BrAPI não pôde ser testada ao vivo neste ambiente (rede restrita), então
  vale conferir na prática se costuma retornar o CNPJ.
- v2.0 (2026-07-02): Descoberto que o valor estranho no ticker da B3
  (BRB3SAACNOR6) era na verdade o Código ISIN, colado no campo errado.
  Pesquisei e confirmei uma fonte oficial pra CNPJ: o cadastro público da
  CVM (dados.cvm.gov.br/dados/CIA_ABERTA/CAD/DADOS/cad_cia_aberta.csv),
  atualizado diariamente. Criada buscar_cnpj_cvm() com correspondência de
  nome (remove sufixo de classe de ação tipo "ON"/"PN" e busca por nome que
  COMECE com o que sobrou — testado e confirmado que "B3 ON" encontra
  "B3 S.A. - BRASIL, BOLSA, BALCÃO" corretamente), com BrAPI como reserva
  se a CVM não achar. Agora é a fonte principal de CNPJ tanto no cadastro
  automático do Screening quanto num novo botão "🔎 Buscar CNPJ" na tela de
  Empresas (aparece quando a empresa editada ainda não tem CNPJ salvo) —
  não raspamos o Google diretamente porque ele bloqueia isso.
- v2.1 (2026-07-02): Tela de Screening reorganizada por pedido do usuário:
  "Filtro básico" compacto (P/L, ROE, Div.Yield sempre visíveis) + expander
  "Filtro avançado" com os outros 9 indicadores em grade de 3 colunas
  (em vez de 1 por linha) — ocupa muito menos espaço vertical. Confirmado
  (e documentado explicitamente na tela) que a combinação de filtros
  SEMPRE foi por E, nunca por OU — mais filtros ativos = resultado menor,
  como esperado. Removida a caixa de busca separada; CNPJ/Razão Social/
  Setor/Segmento agora são filtros de verdade dentro do mesmo Screening,
  cruzando a lista do Fundamentus com as empresas já cadastradas no banco
  (testado: ticker já cadastrado traz razão social/CNPJ/segmento reais,
  ticker não cadastrado fica em branco — não é bug, é limite da fonte).
  Tabela de resultado agora mostra mais linhas de uma vez (altura 500px).
- v2.2 (2026-07-02): Esclarecido que "8. Informações Relevantes" NÃO é
  sobre uma empresa (isso já existe dentro da tela de Empresas) — é um
  painel macro de mercado (Brasil/mundo/índices) tipo jornal diário.
  Confirmei fontes RSS públicas e gratuitas reais (InfoMoney Mercados/
  Economia/Mundo, G1 Economia) e testei o parsing e a ordenação por data.
  Implementada a tela com cotações do dia (Ibovespa, Dólar, S&P500 — usando
  buscar_cotacao_tempo_real, que ganhou mapeamento pra câmbio) + lista de
  notícias agregadas e ordenadas por data mais recente, com filtro por
  fonte. Cada fonte que falhar é pulada sem travar as demais.
- v2.3 (2026-07-03): Por decisão do usuário, removidas do menu as 3 telas
  que duplicavam o Fluxo de Análise Guiado sem ter conteúdo próprio
  ("2. Balanço/DRE", "3. Indicadores e Valor Intrínseco",
  "5. Avaliação Buffett") — essa funcionalidade já vive nas Etapas 1-3 do
  Fluxo Guiado. Implementada de verdade a tela "7. Relatório da Ação":
  filtro pra escolher a empresa e relatório somente-leitura consolidando
  tudo que já foi levantado sobre ela (balanço, indicadores, valor
  intrínseco, avaliação Buffett, Índice de Boa Empresa, histórico de
  lucro), com atalho pra abrir o Fluxo Guiado se quiser atualizar algo.
- v2.4 (2026-07-03): Identificado que "buscou com sucesso mas os campos
  continuam 0" não era bug — o formulário "Ou lance manualmente" sempre foi
  um formulário separado com valores fixos em 0,00, que nunca refletia o
  que a busca automática trouxe. Corrigido: a Etapa 1 do Fluxo Guiado agora
  mostra um resumo com os valores reais do balanço mais recente logo após
  a mensagem de sucesso, e o formulário manual vem pré-preenchido com esses
  valores (em vez de zeros), para editar em cima em vez de digitar tudo de
  novo. Também alerta se o balanço salvo estiver com os campos principais
  vazios (sinal de uma busca anterior incompleta).
- v2.5 (2026-07-03): Corrigido o Fluxo Guiado sempre "resumir" a última
  empresa analisada, mesmo entrando por ele de novo pelo menu lateral —
  isso é o comportamento normal do Streamlit (mantém o estado da sessão),
  mas não era o esperado pelo usuário. Agora um flag (_fluxo_ativo_
  confirmado) distingue "entrei pelo menu" (sempre pede pra escolher a
  ação) de "vim de um botão Iniciar Fluxo de Análise" de outra tela (aí sim
  continua direto na empresa escolhida). O "🔁 Trocar de ação" e a
  navegação entre Etapas continuam funcionando como antes.

Rodar localmente: streamlit run app.py
Na nuvem: publicado via Streamlit Community Cloud conectado ao GitHub
"""
import json
import streamlit as st
import pandas as pd
from datetime import date

from db_supabase import (get_supabase, sb_select, sb_insert, sb_upsert,
                          sb_update, sb_delete, usuario_id, sou_admin, get_perfil)
from login_page import tela_login, barra_usuario
import calculos as calc

st.set_page_config(page_title="Value Investing", layout="wide", page_icon="📈")

# ---------- LOGIN ----------
if not tela_login():
    st.stop()

# ---------- SIDEBAR ----------
barra_usuario()
st.sidebar.title("📈 Value Investing")

# Mostra a confirmação de uma gravação feita no ciclo anterior (antes do
# st.rerun() que trouxe a página até aqui) — sem isso, a mensagem de sucesso
# ou erro nunca chegaria a aparecer na tela.
if "_flash" in st.session_state:
    _tipo_flash, _msg_flash = st.session_state.pop("_flash")
    if _tipo_flash == "success":
        st.success(_msg_flash)
    else:
        st.error(_msg_flash)
pagina = st.sidebar.radio("Navegação", [
    "0. Screening de Ações",
    "0b. Minha Lista de Análise",
    "🧭 Fluxo de Análise (guiado)",
    "1. Empresas e Setores",
    "4. Critérios e Índice de Qualidade",
    "6. Carteira",
    "7. Relatório da Ação",
    "8. Informações Relevantes",
    "9. Índices Macroeconômicos",
    "10. Tabelas de Apoio",
    "11. Administração de Usuários",
], key="nav_radio")

# Se o usuário está em QUALQUER outra tela, "desarma" o Fluxo Guiado — assim,
# ao entrar nele pelo menu lateral, sempre começa em branco (pedindo pra
# escolher a ação). Só continua de onde parou quando vem de um botão
# "Iniciar Fluxo de Análise" (que usa iniciar_fluxo_analise() e marca esse
# mesmo flag como True antes de navegar pra cá).
if pagina != "🧭 Fluxo de Análise (guiado)":
    st.session_state["_fluxo_ativo_confirmado"] = False

# ---------- HELPERS ----------

import re
import io
import unicodedata
import requests


def _normalizar_nome_coluna(c):
    """snake_case sem acento, sem pontuação, sem underscore duplicado."""
    c = str(c).strip().lower()
    c = "".join(x for x in unicodedata.normalize("NFKD", c) if not unicodedata.combining(x))
    c = re.sub(r"[.\s/]+", "_", c)
    c = re.sub(r"_+", "_", c).strip("_")
    return c


# cada campo final aceita várias variações possíveis de nome — o Fundamentus
# muda o cabeçalho de tempos em tempos (foi isso que quebrava a lib antiga)
_MAPA_FUNDAMENTUS = {
    "ticker":       ["papel"],
    "razao_social": ["nome", "empresa"],
    "setor":        ["setor"],
    "cotacao":      ["cotacao"],
    "pl":           ["p_l", "pl"],
    "pvp":          ["p_vp", "pvp"],
    "psr":          ["psr"],
    "dy":           ["div_yield", "dy", "dividend_yield"],
    "pa":           ["p_ativo"],
    "pcg":          ["p_cap_giro"],
    "pebit":        ["p_ebit"],
    "pacl":         ["p_ativ_circ_liq"],
    "evebit":       ["ev_ebit"],
    "evebitda":     ["ev_ebitda", "evebitda"],
    "mrgebit":      ["mrg_ebit"],
    "mrgliq":       ["mrg_liq"],
    "roic":         ["roic"],
    "roe":          ["roe"],
    "liqc":         ["liq_corr"],
    "liq2meses":    ["liq_2meses", "liq2meses"],
    "patrliq":      ["patrim_liq"],
    "divpl":        ["div_brut_patrim", "div_bruta_patrim", "div_liq_patrim"],
    "cagr5":        ["cresc_rec_5a", "cresc_rec5a"],
}

_CAMPOS_PERCENTUAIS = ["dy", "mrgebit", "mrgliq", "roic", "roe", "cagr5"]
_CAMPOS_NUMERICOS = ["cotacao", "pl", "pvp", "psr", "pa", "pcg", "pebit", "pacl",
                      "evebit", "evebitda", "liqc", "liq2meses", "patrliq", "divpl"]


def _buscar_fundamentus_bruto():
    """
    Busca a tabela completa de ações do Fundamentus (resultado.php) direto por
    requests + pandas, SEM depender da lib 'fundamentus' do PyPI — ela quebra
    (KeyError: 'Dív.Brut/ Patrim.') toda vez que o site muda algum cabeçalho,
    porque tem nomes de coluna fixos no código dela.
    Aqui cada indicador tem várias variações de nome aceitas e, se nenhuma for
    encontrada, o campo vira 0 em vez de estourar erro.
    Retorna: (DataFrame, lista_de_campos_que_nao_foram_encontrados)
    """
    url = "https://www.fundamentus.com.br/resultado.php"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
        "Accept-Language": "pt-BR,pt;q=0.9",
    }
    resp = requests.get(url, headers=headers, timeout=25)
    resp.encoding = "iso-8859-1"

    tabelas = pd.read_html(io.StringIO(resp.text), decimal=",", thousands=".")
    if not tabelas:
        return None, []

    bruto = tabelas[0]
    bruto.columns = [_normalizar_nome_coluna(c) for c in bruto.columns]

    resultado = pd.DataFrame(index=bruto.index)
    colunas_ausentes = []

    colunas_usadas = set()
    for campo_final, variantes in _MAPA_FUNDAMENTUS.items():
        col_encontrada = next((v for v in variantes if v in bruto.columns and v not in colunas_usadas), None)
        if col_encontrada is None:
            # aproximação SEGURA: exige que o nome esperado apareça como
            # substring CONTÍGUA (ex.: "pl" precisa aparecer junto, não cada
            # letra solta em qualquer lugar — era isso que fazia "P/L" bater
            # errado com "papel", zerando o indicador pra todo mundo)
            alvo = variantes[0].replace("_", "")
            col_encontrada = next(
                (c for c in bruto.columns
                 if c not in colunas_usadas and alvo and alvo in c.replace("_", "")),
                None
            )
        if col_encontrada is not None:
            try:
                resultado[campo_final] = bruto[col_encontrada]
                colunas_usadas.add(col_encontrada)
            except Exception:
                resultado[campo_final] = 0
                colunas_ausentes.append(campo_final)
        else:
            resultado[campo_final] = 0
            colunas_ausentes.append(campo_final)

    # campos percentuais às vezes vêm como texto "12,3%"
    for campo in _CAMPOS_PERCENTUAIS:
        if campo in resultado.columns:
            resultado[campo] = (
                resultado[campo].astype(str)
                .str.replace("%", "", regex=False)
                .str.replace(".", "", regex=False)
                .str.replace(",", ".", regex=False)
            )
            resultado[campo] = pd.to_numeric(resultado[campo], errors="coerce").fillna(0)

    for campo in _CAMPOS_NUMERICOS:
        if campo in resultado.columns:
            resultado[campo] = pd.to_numeric(resultado[campo], errors="coerce").fillna(0)

    resultado.reset_index(drop=True, inplace=True)
    return resultado, colunas_ausentes


def buscar_perfil_empresa_fundamentus(ticker):
    """
    Busca razão social aproximada e setor/subsetor na página de detalhes do
    Fundamentus — usado no cadastro automático quando uma ação é selecionada
    no Screening (a lista completa do Fundamentus não traz razão social).
    Nunca estoura erro; devolve {} se não achar nada.
    """
    try:
        url = f"https://www.fundamentus.com.br/detalhes.php?papel={ticker.upper()}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
            "Accept-Language": "pt-BR,pt;q=0.9",
        }
        resp = requests.get(url, headers=headers, timeout=20)
        resp.encoding = "iso-8859-1"
        tabelas = pd.read_html(io.StringIO(resp.text), decimal=",", thousands=".")
        pares = {}
        for t in tabelas:
            n_cols = t.shape[1]
            if n_cols < 2 or n_cols % 2 != 0:
                continue
            for _, row in t.iterrows():
                for i in range(0, n_cols, 2):
                    chave = _normalizar_nome_coluna(str(row.iloc[i]))
                    valor = row.iloc[i + 1]
                    if chave and chave not in pares:
                        pares[chave] = valor
        return {
            "razao_social": (str(pares.get("empresa") or "").strip() or None),
            "setor": (str(pares.get("setor") or "").strip() or None),
            "subsetor": (str(pares.get("subsetor") or "").strip() or None),
        }
    except Exception:
        return {}


@st.cache_data(ttl=86400, show_spinner=False)
def _baixar_cadastro_cvm():
    """
    Baixa o cadastro oficial da CVM com CNPJ de TODAS as companhias abertas
    do Brasil (fonte pública, gratuita e estável — muito melhor que tentar
    adivinhar via scraping do Google, que a própria plataforma bloqueia).
    Fica em cache por 24h pra não baixar esse arquivo (que é grande) toda
    vez que alguém cadastra uma empresa.
    """
    url = "http://dados.cvm.gov.br/dados/CIA_ABERTA/CAD/DADOS/cad_cia_aberta.csv"
    resp = requests.get(url, timeout=30)
    resp.encoding = "latin-1"
    df = pd.read_csv(io.StringIO(resp.text), sep=";", encoding="latin-1", dtype=str, on_bad_lines="skip")
    df.columns = [_normalizar_nome_coluna(c) for c in df.columns]
    return df


_SUFIXOS_CLASSE_ACAO = [" ON N1", " ON N2", " ON NM", " PN N1", " PN N2", " PN NM",
                         " ON", " PN", " PNA", " PNB", " PNC", " UNT", " UNIT"]


def _limpar_nome_para_busca(nome):
    """Remove sufixos de classe de ação (ON/PN/UNT etc.) que o Fundamentus
    põe no final do nome, pra sobrar só o nome de fato da empresa."""
    n = nome.strip().upper()
    for suf in sorted(_SUFIXOS_CLASSE_ACAO, key=len, reverse=True):
        if n.endswith(suf):
            return n[: -len(suf)].strip()
    return n


def buscar_cnpj_cvm(razao_social_aproximada):
    """
    Busca o CNPJ no cadastro oficial da CVM por aproximação de nome — a
    razão social que vem do Fundamentus (ex: "B3 ON") quase nunca bate
    100% com o nome oficial da CVM (ex: "B3 S.A. - BRASIL, BOLSA, BALCÃO").
    Estratégia: 1) remove o sufixo de classe de ação (ON/PN/UNT) e tenta
    achar um nome da CVM que COMECE com o que sobrou (muito mais confiável
    pra nomes curtos do que similaridade de texto); 2) se não achar, cai
    pra comparação de similaridade como reserva.
    Nunca estoura erro. Retorna (cnpj, nome_oficial_cvm) ou (None, None).
    """
    if not razao_social_aproximada:
        return None, None
    try:
        df = _baixar_cadastro_cvm()
        col_cnpj = next((c for c in df.columns if "cnpj" in c), None)
        col_nome = next((c for c in df.columns if c == "denom_social"), None) \
            or next((c for c in df.columns if "denom" in c), None)
        if not col_cnpj or not col_nome:
            return None, None

        alvo = _limpar_nome_para_busca(razao_social_aproximada)
        nomes_upper = df[col_nome].astype(str).str.upper()

        if len(alvo) >= 3:
            match_idx = nomes_upper[nomes_upper.str.startswith(alvo)].index
            if len(match_idx) > 0:
                linha = df.loc[match_idx[0]]
                return str(linha[col_cnpj]).strip(), str(linha[col_nome])

        import difflib
        melhores = difflib.get_close_matches(alvo, nomes_upper.tolist(), n=1, cutoff=0.5)
        if not melhores:
            return None, None
        linha = df[nomes_upper == melhores[0]].iloc[0]
        return str(linha[col_cnpj]).strip(), str(linha[col_nome])
    except Exception:
        return None, None


def buscar_cnpj_brapi(ticker):
    """
    Tenta buscar o CNPJ via BrAPI (brapi.dev), API gratuita de dados da B3.
    Isso é BEST-EFFORT: a BrAPI nem sempre tem esse campo preenchido pra
    toda ação, e o formato pode mudar sem aviso — por isso nunca estoura
    erro, só devolve None quando não consegue (o cadastro segue sem CNPJ,
    pra completar manualmente depois).
    """
    try:
        url = f"https://brapi.dev/api/quote/{ticker.upper()}?modules=summaryProfile"
        resp = requests.get(url, timeout=15)
        if resp.status_code != 200:
            return None
        data = resp.json()
        resultados = data.get("results") or []
        if not resultados:
            return None
        perfil = resultados[0].get("summaryProfile") or {}
        cnpj = perfil.get("cnpj") or resultados[0].get("cnpj")
        return str(cnpj).strip() if cnpj else None
    except Exception:
        return None


# ---------- INFORMAÇÕES RELEVANTES DO MERCADO (painel macro, tipo "jornal") ----------
# Isso é diferente das "Notícias Relevantes" de uma empresa específica (que
# ficam dentro da tela de Empresas) — aqui é o cenário geral: Brasil, mundo,
# índices, câmbio, o que pode afetar a bolsa como um todo.

_FONTES_NOTICIAS_MERCADO = [
    ("InfoMoney - Mercados", "https://www.infomoney.com.br/mercados/feed/"),
    ("InfoMoney - Economia", "https://www.infomoney.com.br/economia/feed/"),
    ("InfoMoney - Mundo", "https://www.infomoney.com.br/mundo/feed/"),
    ("G1 - Economia", "https://g1.globo.com/dynamo/economia/rss2.xml"),
]


def _parse_data_rss(data_str):
    from datetime import datetime as _dt
    for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z"):
        try:
            return _dt.strptime(data_str.strip(), fmt)
        except Exception:
            continue
    return None


def buscar_noticias_mercado(max_por_fonte=8):
    """
    Busca notícias de Mercado/Economia/Mundo em feeds RSS públicos e
    gratuitos (InfoMoney, G1) — um "jornal" diário do que pode afetar a
    bolsa, o Brasil e o mundo, sem ser sobre uma empresa específica.
    Cada fonte que falhar é simplesmente pulada — nunca trava as demais.
    """
    import xml.etree.ElementTree as ET
    todas = []
    for fonte_nome, url in _FONTES_NOTICIAS_MERCADO:
        try:
            resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
            root = ET.fromstring(resp.content)
            for item in root.findall(".//item")[:max_por_fonte]:
                titulo = (item.findtext("title") or "").strip()
                link = (item.findtext("link") or "").strip()
                data_str = item.findtext("pubDate") or ""
                if titulo:
                    todas.append({"fonte": fonte_nome, "titulo": titulo, "link": link,
                                  "data_dt": _parse_data_rss(data_str), "data_str": data_str})
        except Exception:
            continue
    todas.sort(key=lambda x: x["data_dt"].timestamp() if x["data_dt"] else 0, reverse=True)
    return todas


def _buscar_fundamentus_detalhes(ticker):
    """
    Busca a página de detalhes de UM papel no Fundamentus
    (fundamentus.com.br/detalhes.php?papel=XXXX3) — muito mais completa e
    estável para ações brasileiras do que o Yahoo Finance, que frequentemente
    não tem balanço/DRE completo pra B3.
    Retorna um dict no formato da tabela balancos_dre, ou None se não achar
    dados úteis pra esse ticker.
    """
    url = f"https://www.fundamentus.com.br/detalhes.php?papel={ticker.upper()}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
        "Accept-Language": "pt-BR,pt;q=0.9",
    }
    resp = requests.get(url, headers=headers, timeout=25)
    resp.encoding = "iso-8859-1"

    tabelas = pd.read_html(io.StringIO(resp.text), decimal=",", thousands=".")
    pares = {}
    for t in tabelas:
        n_cols = t.shape[1]
        if n_cols < 2 or n_cols % 2 != 0:
            continue
        for _, row in t.iterrows():
            for i in range(0, n_cols, 2):
                chave = _normalizar_nome_coluna(str(row.iloc[i]))
                valor = row.iloc[i + 1]
                if chave and chave not in pares:
                    pares[chave] = valor

    def _num(*chaves):
        for c in chaves:
            if c in pares:
                v = pares[c]
                if isinstance(v, str):
                    v = v.replace("%", "").replace(".", "").replace(",", ".")
                try:
                    return float(v)
                except (TypeError, ValueError):
                    continue
        return None

    data_ref_raw = None
    for c in ["ult_balanco_processado", "ultimo_balanco_processado", "balanco_processado"]:
        if c in pares:
            data_ref_raw = str(pares[c])
            break

    data_ref = None
    if data_ref_raw:
        try:
            d, m, a = data_ref_raw.strip().split("/")
            data_ref = f"{a}-{m}-{d}"
        except Exception:
            data_ref = None

    ativo = _num("ativo")
    ativo_circulante = _num("ativo_circulante")
    div_bruta = _num("div_bruta")
    div_liquida = _num("div_liquida")
    patrim_liq = _num("patrim_liq")
    receita_liq = _num("receita_liquida")
    ebit = _num("ebit")
    lucro_liquido = _num("lucro_liquido")
    cotacao = _num("cotacao")
    nro_acoes = _num("nro_acoes")

    if not data_ref and ativo is None:
        return None  # ticker provavelmente não existe no Fundamentus

    total_liabilities = (ativo - patrim_liq) if (ativo is not None and patrim_liq is not None) else None

    return {
        "data_referencia": data_ref or date.today().isoformat(),
        "total_assets": ativo,
        "total_liabilities": total_liabilities,
        "total_equity": patrim_liq,
        "net_debt": div_liquida,
        "share_issued": nro_acoes,
        "preco_mercado_referencia": cotacao,
        "total_revenue": receita_liq,
        "net_income": lucro_liquido,
        "ebit": ebit,
        "fonte": "Fundamentus",
    }


def buscar_balanco_multi_fonte(ticker):
    """
    Tenta o Fundamentus primeiro (mais completo/estável pra ações
    brasileiras) e só cai pro Yahoo Finance se o Fundamentus não retornar
    nada útil pra esse ticker. Nunca estoura erro — na pior das hipóteses
    devolve um dict vazio (o chamador já trata isso mostrando um aviso).
    """
    try:
        dados = _buscar_fundamentus_detalhes(ticker)
        if dados and (dados.get("total_assets") or dados.get("net_income")):
            return dados
    except Exception:
        pass
    try:
        return calc.buscar_balanco_yfinance(ticker) or {}
    except Exception:
        return {}


# índices que não seguem o padrão "TICKER.SA" — mapeados pro código do Yahoo Finance
_MAPA_INDICES_YF = {
    "IBOV": "^BVSP", "IBOVESPA": "^BVSP", "INDEXBVMF:IBOV": "^BVSP",
    "SP500": "^GSPC", "S&P500": "^GSPC", "DOW": "^DJI", "NASDAQ": "^IXIC",
    "IFIX": "^IFIX.SA",
    "DOLAR": "BRL=X", "DÓLAR": "BRL=X", "USD": "BRL=X", "USDBRL": "BRL=X",
    "USDBRL=X": "BRL=X", "EUR": "EURBRL=X",
}


def buscar_cotacao_tempo_real(ticker):
    """
    Cotação em tempo real (na prática, ~15 min de atraso — padrão do Yahoo
    Finance para a B3) via yfinance. É o equivalente ao GOOGLEFINANCE() do
    Google Sheets, mas chamável de dentro do Python. Aceita tanto ações
    (ex: PETR4) quanto índices (ex: IBOV, equivalente ao
    =GOOGLEFINANCE("INDEXBVMF:IBOV") do Sheets).
    Retorna (preco, timestamp_iso) — preco é 0.0 se não conseguir buscar;
    nunca estoura erro pra tela.
    Uso recomendado: 1 ativo por vez (relatório da ação, carteira, fluxo
    guiado). Não usar para a lista inteira da B3 no screening — seria lento
    e a B3/Yahoo limitam requisições em massa.
    """
    try:
        import yfinance as yf
        t = ticker.strip().upper()
        if t in _MAPA_INDICES_YF:
            tk = _MAPA_INDICES_YF[t]
        elif t.startswith("^"):
            tk = t
        elif t.endswith(".SA"):
            tk = t
        else:
            tk = f"{t}.SA"
        info = yf.Ticker(tk).fast_info
        preco = info.get("last_price") or info.get("lastPrice") or 0.0
        agora = pd.Timestamp.now().isoformat()
        return (float(preco) if preco else 0.0), agora
    except Exception:
        return 0.0, pd.Timestamp.now().isoformat()


# ---------- ÍNDICE DE BOA EMPRESA ----------
# Critérios definidos no docx: Valuation 30% (ou Rating 30% quando a empresa
# tem rating de crédito) + Qualidade Financeira 45% + Qualidade do Negócio 25%.
# Rating só pontua de A- pra cima. Bancos usam Índice de Basileia em vez de
# Dívida Bruta/Patrimônio dentro da Qualidade Financeira.
# Nota final 0-100: >=70 Boa empresa | 50-70 Observar | <50 Evitar.
# Qualquer dado que faltar entra como 0/neutro e nunca trava o cálculo —
# os critérios abaixo são a proposta inicial pra você validar/ajustar.

def _norm_chave(s):
    s = str(s).strip().lower()
    s = "".join(x for x in unicodedata.normalize("NFKD", s) if not unicodedata.combining(x))
    return re.sub(r"[^a-z0-9]+", "", s)


def _buscar_indicador(ind_dict, *nomes_candidatos):
    if not ind_dict:
        return None
    chaves_norm = {_norm_chave(k): v for k, v in ind_dict.items()}
    for nome in nomes_candidatos:
        n = _norm_chave(nome)
        if n in chaves_norm:
            try:
                return float(chaves_norm[n])
            except (TypeError, ValueError):
                return None
    for nome in nomes_candidatos:
        n = _norm_chave(nome)
        for k, v in chaves_norm.items():
            if n and (n in k or k in n):
                try:
                    return float(v)
                except (TypeError, ValueError):
                    continue
    return None


def _interp(x, x0, y0, x1, y1):
    if x1 == x0:
        return y0
    return y0 + (y1 - y0) * (x - x0) / (x1 - x0)


def _score_crescente(x, pontos):
    """pontos: [(x0,score0), (x1,score1), ...] em ordem crescente de x."""
    if x is None:
        return None
    if x <= pontos[0][0]:
        return pontos[0][1]
    for (x0, y0), (x1, y1) in zip(pontos, pontos[1:]):
        if x <= x1:
            return _interp(x, x0, y0, x1, y1)
    return pontos[-1][1]


def _score_pl(pl):
    if pl is None:
        return None
    if pl <= 0:
        return 0.0
    if pl <= 8:
        return 100.0
    if pl <= 15:
        return _interp(pl, 8, 100, 15, 60)
    if pl <= 25:
        return _interp(pl, 15, 60, 25, 20)
    return 0.0


def _score_pvp(pvp):
    if pvp is None:
        return None
    if pvp <= 0:
        return 0.0
    if pvp <= 1:
        return 100.0
    if pvp <= 2:
        return _interp(pvp, 1, 100, 2, 60)
    if pvp <= 4:
        return _interp(pvp, 2, 60, 4, 20)
    return 0.0


def _score_margem_seguranca(margem_pct):
    """margem = (VI médio - preço) / VI médio * 100. 0% = neutro (50 pts)."""
    if margem_pct is None:
        return None
    return max(0.0, min(100.0, 50 + margem_pct))


def _score_divida_pl(x):
    if x is None:
        return None
    if x <= 0.3:
        return 100.0
    if x <= 0.7:
        return _interp(x, 0.3, 100, 0.7, 60)
    if x <= 1.5:
        return _interp(x, 0.7, 60, 1.5, 20)
    return 0.0


def _score_basileia(x):
    """Mínimo regulatório do BCB é ~11%; abaixo disso é zerado."""
    if x is None:
        return None
    if x < 11:
        return 0.0
    if x <= 14:
        return _interp(x, 11, 40, 14, 70)
    if x <= 18:
        return _interp(x, 14, 70, 18, 100)
    return 100.0


_MAPA_RATING = {
    "AAA": 100.0, "AA+": 95.0, "AA": 90.0, "AA-": 85.0,
    "A+": 80.0, "A": 75.0, "A-": 70.0,
}


def _score_rating(rating_str):
    """Só ganha ponto de A- pra cima — abaixo disso vira 0, conforme pedido."""
    if not rating_str:
        return None
    return _MAPA_RATING.get(rating_str.strip().upper(), 0.0)


def _calc_cagr(valores):
    vs = [v for v in valores if v]
    if len(vs) < 2:
        return None
    primeiro, ultimo, n = vs[0], vs[-1], len(vs) - 1
    if primeiro <= 0 or ultimo <= 0 or n <= 0:
        return None
    try:
        return ((ultimo / primeiro) ** (1 / n) - 1) * 100
    except Exception:
        return None


def _calc_pct_anos_lucro(valores):
    vs = [v for v in valores if v is not None]
    if not vs:
        return None
    return sum(1 for v in vs if v > 0) / len(vs) * 100


def _media_ignorando_none(*valores):
    vals = [v for v in valores if v is not None]
    return sum(vals) / len(vals) if vals else 0.0


def calcular_indice_boa_empresa(emp, ind=None, preco=None, vi_medio=None,
                                 av=None, banco_dados=None, historico_lucros=None):
    """
    Calcula o Índice de Boa Empresa (0-100) de uma empresa.
    Nunca estoura erro: qualquer dado ausente entra como 0/neutro no cálculo
    e fica registrado em 'detalhes' para você conferir o que faltou.
    Retorna um dict pronto para exibir e para gravar em indice_boa_empresa.
    """
    ind = ind or {}
    av = av or {}
    banco_dados = banco_dados or {}
    historico_lucros = historico_lucros or []

    pl = _buscar_indicador(ind, "P/L", "PL")
    pvp = _buscar_indicador(ind, "P/VP", "PVP")
    roe = _buscar_indicador(ind, "ROE")
    roic = _buscar_indicador(ind, "ROIC")
    margem_liq = _buscar_indicador(ind, "Margem Líquida", "Margem Liquida", "Mrg Liq")
    divida_pl = _buscar_indicador(ind, "Dívida Bruta/Patrimônio", "Divida Bruta Patrimonio", "Div Brut Patrim")

    margem_seguranca = None
    if preco and vi_medio and vi_medio > 0:
        margem_seguranca = (vi_medio - preco) / vi_medio * 100

    cagr5 = _calc_cagr(historico_lucros)
    pct_anos_lucro = _calc_pct_anos_lucro(historico_lucros)

    score_pl = _score_pl(pl)
    score_pvp = _score_pvp(pvp)
    score_margem_seg = _score_margem_seguranca(margem_seguranca)
    score_roe = _score_crescente(roe, [(0, 0), (5, 30), (15, 70), (25, 100)])
    score_roic = _score_crescente(roic, [(0, 0), (5, 30), (15, 70), (25, 100)])
    score_margem_liq = _score_crescente(margem_liq, [(0, 0), (5, 30), (15, 70), (30, 100)])

    eh_banco = bool(emp.get("eh_banco"))
    if eh_banco:
        score_alavancagem = _score_basileia(banco_dados.get("indice_basileia"))
        nome_criterio_alavancagem = "Índice de Basileia (%)"
        valor_alavancagem = banco_dados.get("indice_basileia")
    else:
        score_alavancagem = _score_divida_pl(divida_pl)
        nome_criterio_alavancagem = "Dívida Bruta/Patrimônio"
        valor_alavancagem = divida_pl

    score_cresc5a = _score_crescente(cagr5, [(0, 0), (5, 40), (15, 80), (25, 100)])
    score_hist_positivo = pct_anos_lucro

    nota_valuation = _media_ignorando_none(score_pl, score_pvp, score_margem_seg)
    nota_qualidade_financeira = _media_ignorando_none(
        score_roe, score_roic, score_margem_liq, score_alavancagem, score_cresc5a, score_hist_positivo)

    moat_score = {"nenhum": 0.0, "fraco": 33.0, "moderado": 66.0, "forte": 100.0}.get(av.get("moat"))
    gestao_val = av.get("qualidade_gestao")
    gestao_score = (float(gestao_val) - 1) / 4 * 100 if gestao_val is not None else None
    prev_score = {"baixa": 0.0, "media": 50.0, "alta": 100.0}.get(av.get("previsibilidade"))
    circulo_score = None
    if "circulo_competencia" in av and av.get("circulo_competencia") is not None:
        circulo_score = 100.0 if av.get("circulo_competencia") else 0.0

    nota_qualidade_negocio = _media_ignorando_none(moat_score, gestao_score, prev_score, circulo_score)

    rating_str = (emp.get("rating") or "").strip()
    nota_rating = _score_rating(rating_str) if rating_str else None

    if nota_rating is not None:
        componente_30, fonte_30 = nota_rating, "Rating"
    else:
        componente_30, fonte_30 = nota_valuation, "Valuation"

    nota_final = round(componente_30 * 0.30 + nota_qualidade_financeira * 0.45 + nota_qualidade_negocio * 0.25, 1)
    if nota_final >= 70:
        classificacao = "Boa empresa"
    elif nota_final >= 50:
        classificacao = "Observar"
    else:
        classificacao = "Evitar"

    return {
        "nota_final": nota_final,
        "classificacao": classificacao,
        "componente_30_fonte": fonte_30,
        "nota_valuation": round(nota_valuation, 1),
        "nota_qualidade_financeira": round(nota_qualidade_financeira, 1),
        "nota_qualidade_negocio": round(nota_qualidade_negocio, 1),
        "nota_rating": round(nota_rating, 1) if nota_rating is not None else None,
        "detalhes": {
            "valuation (peso 30%, ou Rating se disponível)": {
                "P/L": pl, "score": score_pl,
                "P/VP": pvp, "score_pvp": score_pvp,
                "margem_seguranca_%": round(margem_seguranca, 1) if margem_seguranca is not None else None,
                "score_margem_seguranca": score_margem_seg,
            },
            "qualidade_financeira (peso 45%)": {
                "ROE_%": roe, "score_roe": score_roe,
                "ROIC_%": roic, "score_roic": score_roic,
                "margem_liquida_%": margem_liq, "score_margem_liquida": score_margem_liq,
                nome_criterio_alavancagem: valor_alavancagem, "score_alavancagem": score_alavancagem,
                "crescimento_lucro_5a_%": round(cagr5, 1) if cagr5 is not None else None,
                "score_crescimento_5a": score_cresc5a,
                "pct_anos_com_lucro": round(pct_anos_lucro, 1) if pct_anos_lucro is not None else None,
            },
            "qualidade_negocio (peso 25%)": {
                "moat": av.get("moat"), "score_moat": moat_score,
                "qualidade_gestao_1a5": gestao_val, "score_gestao": gestao_score,
                "previsibilidade": av.get("previsibilidade"), "score_previsibilidade": prev_score,
                "circulo_competencia": av.get("circulo_competencia"), "score_circulo": circulo_score,
            },
            "rating": {"rating": rating_str or None, "nota_rating": nota_rating},
        },
    }


def renderizar_diagnostico_boa_empresa(emp_id, emp, permitir_salvar=True):
    """
    Busca tudo que é preciso (balanço, indicadores, VI, avaliação qualitativa,
    dados de banco, histórico de lucros) e desenha o diagnóstico do Índice de
    Boa Empresa na tela. Reaproveitado no Fluxo Guiado e na tela de Empresas.
    Nunca estoura erro — se faltar balanço, avisa e para por aí.
    """
    bals = sb_select("balancos_dre", "*", filtros={"empresa_id": emp_id}, ordem="data_referencia")
    if not bals:
        st.warning("Sem balanço cadastrado para esta empresa ainda. "
                   "Lance um balanço (Fluxo de Análise guiado, Etapa 1) para calcular o diagnóstico.")
        return
    bal = bals[-1]
    ind = calc.calcular_indicadores(bal)
    preco = bal.get("preco_mercado_referencia")
    vis = sb_select("valor_intrinseco", "metodo,valor",
                     filtros={"empresa_id": emp_id, "data_referencia": bal["data_referencia"]})
    vi_medio = (sum(v["valor"] for v in vis) / len(vis)) if vis else None
    av = sb_select("avaliacao_qualitativa_buffett", "*", filtros={"empresa_id": emp_id})
    banco_reg = sb_select("bancos_dados", "*", filtros={"empresa_id": emp_id}) if emp.get("eh_banco") else []
    historico_lucros = [b.get("net_income") for b in sorted(bals, key=lambda x: x["data_referencia"])
                         if b.get("net_income") is not None]

    resultado = calcular_indice_boa_empresa(
        emp=emp, ind=ind, preco=preco, vi_medio=vi_medio,
        av=(av[0] if av else {}), banco_dados=(banco_reg[0] if banco_reg else {}),
        historico_lucros=historico_lucros,
    )
    cor = {"Boa empresa": "green", "Observar": "orange", "Evitar": "red"}[resultado["classificacao"]]
    st.markdown(f"### Nota final: **{resultado['nota_final']}/100** — :{cor}[{resultado['classificacao']}]")
    b1, b2, b3 = st.columns(3)
    b1.metric(f"Valuation/Rating (30% — {resultado['componente_30_fonte']})",
              resultado['nota_rating'] if resultado['nota_rating'] is not None else resultado['nota_valuation'])
    b2.metric("Qualidade Financeira (45%)", resultado['nota_qualidade_financeira'])
    b3.metric("Qualidade do Negócio (25%)", resultado['nota_qualidade_negocio'])
    with st.expander("Ver detalhamento critério a critério (para validar)"):
        st.json(resultado["detalhes"])
    if permitir_salvar and st.button("💾 Salvar este diagnóstico", key=f"salvar_ibe_{emp_id}"):
        gravar_com_confirmacao(sb_upsert, "indice_boa_empresa", {
            "empresa_id": emp_id, "data_calculo": date.today().isoformat(),
            "nota_valuation": resultado["nota_valuation"],
            "nota_qualidade_financeira": resultado["nota_qualidade_financeira"],
            "nota_qualidade_negocio": resultado["nota_qualidade_negocio"],
            "nota_rating": resultado["nota_rating"],
            "nota_final": resultado["nota_final"],
            "classificacao": resultado["classificacao"],
            "detalhes": resultado["detalhes"],
        }, msg_ok="✅ Diagnóstico salvo com sucesso.", msg_erro="❌ Não foi possível salvar o diagnóstico.")


def buscar_rating_links(nome_empresa):
    """
    Não existe fonte pública gratuita e estável para raspar rating de crédito
    automaticamente (Fitch/Moody's/S&P não expõem isso em página simples).
    Em vez de fingir uma busca automática que não funcionaria de verdade,
    devolve links diretos de busca em cada agência para conferência manual rápida.
    """
    import urllib.parse
    q = urllib.parse.quote(nome_empresa)
    return {
        "Fitch Ratings": f"https://www.fitchratings.com/search?query={q}",
        "Moody's": f"https://www.moodys.com/search?keyword={q}",
        "S&P Global": f"https://www.spglobal.com/ratings/en/search-results?query={q}",
        "Busca geral": f"https://www.google.com/search?q={q}+rating+de+cr%C3%A9dito",
    }


def gravar_com_confirmacao(func, *args, msg_ok="✅ Atualização com sucesso.",
                            msg_erro="❌ Não foi possível salvar.", permitir_vazio=False, **kwargs):
    """
    Executa uma gravação no banco (sb_insert/sb_upsert/sb_update/sb_delete) e
    SEMPRE mostra na tela se funcionou ou não — nunca fica em silêncio nem
    finge sucesso quando o banco não confirmou nada.
    A mensagem é guardada em st.session_state["_flash"] e também mostrada na
    hora — isso garante que ela sobreviva a um st.rerun() chamado logo em
    seguida (sem isso, o rerun recarrega a página tão rápido que a mensagem
    nunca chega a aparecer na tela).
    permitir_vazio=True: use para DELETE, que às vezes retorna lista vazia
    mesmo quando funcionou — nesse caso só uma exceção real conta como erro.
    Devolve o resultado pra quem chamou continuar usando (ex: pegar o id
    gerado), ou None se falhou.
    """
    try:
        resultado = func(*args, **kwargs)
    except Exception as e:
        msg = f"{msg_erro} Detalhe técnico: {e}"
        st.session_state["_flash"] = ("error", msg)
        st.error(msg)
        return None
    if not permitir_vazio and (resultado is None or resultado == [] or resultado == {} or resultado is False):
        msg = (f"{msg_erro} (o banco não confirmou a gravação — confira os campos "
               "obrigatórios e as permissões de escrita desta tabela)")
        st.session_state["_flash"] = ("error", msg)
        st.error(msg)
        return None
    st.session_state["_flash"] = ("success", msg_ok)
    st.success(msg_ok)
    return resultado if resultado not in (None, [], {}, False) else True


def lista_empresas():
    dados = sb_select("empresas", "id,ticker,cnpj,razao_social,setor_id,subsetor_id", ordem="ticker")
    return pd.DataFrame(dados) if dados else pd.DataFrame()

def selecionar_empresa(label="Ação", key=None):
    df = lista_empresas()
    if df.empty:
        st.info("Nenhuma empresa cadastrada ainda.")
        return None
    opcoes = df["ticker"] + " - " + df["razao_social"]
    idx = 0
    fluxo_id = st.session_state.get("fluxo_empresa_id")
    if fluxo_id:
        matches = df[df["id"] == fluxo_id].index
        if len(matches):
            idx = int(matches[0])
    opcao = st.selectbox(label, opcoes, index=idx, key=key)
    ticker = opcao.split(" - ")[0]
    return df[df["ticker"] == ticker].iloc[0]

def iniciar_fluxo_analise(empresa_id):
    st.session_state["fluxo_empresa_id"] = int(empresa_id)
    st.session_state["fluxo_step"] = 1
    st.session_state["_fluxo_ativo_confirmado"] = True
    st.session_state["nav_radio"] = "🧭 Fluxo de Análise (guiado)"
    st.rerun()

def minhas_carteiras():
    uid = usuario_id()
    if sou_admin():
        return sb_select("carteiras", "id,nome,usuario_id", ordem="nome")
    return sb_select("carteiras", "id,nome,usuario_id", filtros={"usuario_id": uid}, ordem="nome")

# ================================================================
if pagina == "0. Screening de Ações":
    st.header("Screening — Seleção de Ações da B3")
    st.caption("Busca **todas as ações da B3** no Fundamentus em tempo real e aplica seus filtros — "
               "todo critério ativo é combinado com **E** (a ação precisa passar em todos ao mesmo "
               "tempo, não em qualquer um). CNPJ/Razão Social/Setor/Segmento só existem para empresas "
               "que você já cadastrou (o Fundamentus não traz isso na lista completa).")

    INDICADORES_SCREEN = [
        ("P/L",         "pl",    "≤", 15.0,  True),
        ("P/VP",        "pvp",   "≤", 1.5,   False),
        ("ROE (%)",     "roe",   "≥", 12.0,  True),
        ("ROIC (%)",    "roic",  "≥", 10.0,  False),
        ("Div.Yield(%)", "dy",   "≥", 0.0,   False),
        ("Margem Líq.(%)", "mrgliq", "≥", 10.0, False),
        ("Dív/PL",      "divpl", "≤", 1.0,   False),
        ("EV/EBITDA",   "evebitda","≤", 8.0, False),
        ("P/EBITDA",    "pebitda", "≤", 8.0, False),
        ("Cresc.Rec.5a(%)", "cagr5", "≥", 0.0, False),
        ("Liq. Corrente","liqc",  "≥", 1.0,  False),
        ("Liquidez (Vol.)", "liq2meses", "≥", 1000000.0, False),
    ]

    if "filtros_screen" not in st.session_state:
        st.session_state["filtros_screen"] = {
            ind[1]: {"sinal": ind[2], "valor": ind[3], "ativo": ind[4]}
            for ind in INDICADORES_SCREEN
        }
    if "filtros_texto_screen" not in st.session_state:
        st.session_state["filtros_texto_screen"] = {"cnpj": "", "razao_social": "", "setor": "Todos", "segmento": ""}

    SINAIS = ["≤", "≥", "="]

    def _widget_indicador(nome, chave):
        estado = st.session_state["filtros_screen"][chave]
        ativo = st.checkbox(nome, value=estado["ativo"], key=f"ativo_{chave}")
        cc1, cc2 = st.columns([1, 2])
        sinal = cc1.selectbox(" ", SINAIS, index=SINAIS.index(estado["sinal"]),
                               key=f"sinal_{chave}", label_visibility="collapsed")
        valor = cc2.number_input(" ", value=float(estado["valor"]),
                                  key=f"val_{chave}", label_visibility="collapsed")
        st.session_state["filtros_screen"][chave] = {"sinal": sinal, "valor": valor, "ativo": ativo}

    # ── Filtro básico: os 3 critérios mais comuns, sempre visíveis ──
    st.subheader("Filtro básico")
    b1, b2, b3 = st.columns(3)
    with b1: _widget_indicador("P/L", "pl")
    with b2: _widget_indicador("ROE (%)", "roe")
    with b3: _widget_indicador("Div.Yield(%)", "dy")

    # ── Filtro avançado: todos os demais indicadores + CNPJ/Razão Social/Setor/Segmento ──
    with st.expander("🔧 Filtro avançado — todos os indicadores + CNPJ, Razão Social, Setor, Segmento"):
        st.caption("Tudo aqui combina com **E** junto do filtro básico — quanto mais critérios você "
                   "ativar, menor (mais restrito) tende a ser o resultado.")
        outros = [i for i in INDICADORES_SCREEN if i[1] not in ("pl", "roe", "dy")]
        cols_adv = st.columns(3)
        for idx, (nome, chave, *_resto) in enumerate(outros):
            with cols_adv[idx % 3]:
                _widget_indicador(nome, chave)

        st.markdown("---")
        st.caption("Filtros por atributo da empresa (só funcionam para empresas já cadastradas no seu banco):")
        setores_disp = ["Todos"] + [s["nome"] for s in sb_select("setores","nome",ordem="nome")]
        t1, t2 = st.columns(2)
        cnpj_filtro = t1.text_input("CNPJ contém", value=st.session_state["filtros_texto_screen"]["cnpj"])
        razao_filtro = t2.text_input("Razão Social contém", value=st.session_state["filtros_texto_screen"]["razao_social"])
        t3, t4 = st.columns(2)
        idx_setor = setores_disp.index(st.session_state["filtros_texto_screen"]["setor"]) \
            if st.session_state["filtros_texto_screen"]["setor"] in setores_disp else 0
        setor_filtro = t3.selectbox("Setor", setores_disp, index=idx_setor)
        segmento_filtro = t4.text_input("Segmento contém", value=st.session_state["filtros_texto_screen"]["segmento"])
        st.session_state["filtros_texto_screen"] = {
            "cnpj": cnpj_filtro, "razao_social": razao_filtro, "setor": setor_filtro, "segmento": segmento_filtro}

    st.markdown("---")
    col_btn1, col_btn2 = st.columns([2, 5])
    buscar = col_btn1.button("🔍 Buscar ações na B3 (Fundamentus)", type="primary")
    col_btn2.caption("Busca todas as ações da B3 em tempo real — pode levar 10 a 30 segundos.")

    if buscar:
        with st.spinner("Buscando todas as ações da B3 no Fundamentus... aguarde."):
            try:
                df_fund, colunas_ausentes = _buscar_fundamentus_bruto()

                if df_fund is None or df_fund.empty:
                    st.error("O Fundamentus não retornou dados agora (site fora do ar, bloqueando o acesso "
                              "ou mudou de layout novamente).")
                    st.info("Tente novamente em alguns minutos.")
                else:
                    # enriquece com os dados que JÁ temos cadastrados (razão social, setor,
                    # segmento, CNPJ) — o Fundamentus não traz isso na lista completa
                    nossas_empresas = sb_select("empresas", "ticker,cnpj,razao_social,setor_id,segmento") or []
                    setores_map = {s["id"]: s["nome"] for s in (sb_select("setores","id,nome") or [])}
                    df_nossas = pd.DataFrame(nossas_empresas)
                    if not df_nossas.empty:
                        df_nossas["setor_nome_cadastrado"] = df_nossas["setor_id"].map(setores_map)
                        df_nossas = df_nossas.rename(columns={"razao_social":"razao_social_cadastrada",
                                                                "cnpj":"cnpj_cadastrado",
                                                                "segmento":"segmento_cadastrado"})
                        df_fund = df_fund.merge(
                            df_nossas[["ticker","cnpj_cadastrado","razao_social_cadastrada",
                                       "setor_nome_cadastrado","segmento_cadastrado"]],
                            on="ticker", how="left")
                    else:
                        for c in ["cnpj_cadastrado","razao_social_cadastrada","setor_nome_cadastrado","segmento_cadastrado"]:
                            df_fund[c] = None
                    # usa o dado cadastrado quando existir; senão mantém o que o Fundamentus deu (0/vazio)
                    df_fund["razao_social"] = df_fund["razao_social_cadastrada"].fillna(df_fund.get("razao_social", ""))
                    df_fund["setor"] = df_fund["setor_nome_cadastrado"].fillna(df_fund.get("setor", ""))
                    df_fund["cnpj"] = df_fund["cnpj_cadastrado"]
                    df_fund["segmento"] = df_fund["segmento_cadastrado"]

                    if colunas_ausentes:
                        st.warning("⚠️ O Fundamentus não trouxe estes indicadores agora (foram preenchidos com 0): "
                                   + ", ".join(sorted(set(colunas_ausentes))))

                    # aplicar filtros numéricos — tudo combinado com E; um indicador com
                    # problema não derruba os demais
                    filtros = st.session_state["filtros_screen"]
                    mask = pd.Series([True] * len(df_fund), index=df_fund.index)
                    for chave, cfg in filtros.items():
                        if not cfg["ativo"] or chave not in df_fund.columns:
                            continue
                        try:
                            val = cfg["valor"]
                            sinal = cfg["sinal"]
                            col_series = pd.to_numeric(df_fund[chave], errors="coerce").fillna(0)
                            if sinal == "≤":
                                mask &= col_series <= val
                            elif sinal == "≥":
                                mask &= col_series >= val
                            elif sinal == "=":
                                mask &= col_series == val
                        except Exception:
                            continue  # ignora só esse filtro, não trava a busca inteira

                    # aplicar filtros de texto/atributo — também combinados com E
                    ft = st.session_state["filtros_texto_screen"]
                    if ft["cnpj"].strip():
                        alvo = re.sub(r"[^0-9]", "", ft["cnpj"])
                        mask &= df_fund["cnpj"].astype(str).str.replace(r"[^0-9]", "", regex=True).str.contains(alvo, na=False)
                    if ft["razao_social"].strip():
                        mask &= df_fund["razao_social"].astype(str).str.lower().str.contains(ft["razao_social"].strip().lower(), na=False)
                    if ft["setor"] != "Todos":
                        mask &= df_fund["setor"].astype(str).str.contains(ft["setor"], case=False, na=False)
                    if ft["segmento"].strip():
                        mask &= df_fund["segmento"].astype(str).str.lower().str.contains(ft["segmento"].strip().lower(), na=False)

                    df_result = df_fund[mask].copy()

                    st.session_state["screening_resultado_fund"] = df_result
                    st.session_state["screening_total_fund"] = len(df_fund)

            except Exception as e:
                st.error(f"Erro ao buscar dados no Fundamentus: {e}")
                st.info("Verifique se o Streamlit Cloud tem acesso à internet para o Fundamentus. "
                        "Se o erro persistir, tente novamente em alguns minutos.")

    if "screening_resultado_fund" in st.session_state:
        df_result = st.session_state["screening_resultado_fund"]
        total = st.session_state.get("screening_total_fund", "?")

        if df_result.empty:
            st.warning(f"Nenhuma ação passou pelos filtros (de {total} ações consultadas). "
                       "Tente afrouxar algum critério (lembre-se: mais filtros ativos = resultado menor).")
        else:
            st.success(f"✅ {len(df_result)} ação(ões) encontrada(s) de {total} consultadas.")

            # colunas a exibir
            cols_exibir = [c for c in ["ticker","razao_social","setor","segmento","cnpj","pl","pvp","roe","roic",
                                         "dy","mrgliq","divpl","evebitda","liqc"] if c in df_result.columns]
            df_show = df_result[cols_exibir].copy()
            df_show.columns = [c.upper() for c in df_show.columns]
            st.dataframe(df_show, use_container_width=True, height=500)

            st.subheader("Selecione as ações para analisar")
            tickers_disp = df_result["ticker"].tolist() if "ticker" in df_result.columns else []
            escolhidas = st.multiselect(
                "Escolha de 1 a 10 ações para guardar na lista de análise",
                tickers_disp, max_selections=10, key="screening_escolhidas_fund")

            if escolhidas and st.button("💾 Guardar seleção para analisar uma a uma", type="primary"):
                uid = usuario_id()
                cadastradas = 0
                setores_existentes = sb_select("setores", "id,nome") or []
                with st.spinner("Cadastrando empresas novas (buscando razão social, setor e CNPJ)..."):
                    for tk in escolhidas:
                        # verifica se empresa já existe no banco; se não, cria automaticamente
                        emps = sb_select("empresas", "id", filtros={"ticker": tk})
                        if emps:
                            eid = emps[0]["id"]
                        else:
                            perfil = buscar_perfil_empresa_fundamentus(tk)
                            nome_emp = perfil.get("razao_social") or tk
                            setor_id_auto = None
                            if perfil.get("setor"):
                                match_s = next((s for s in setores_existentes if s["nome"].lower() == perfil["setor"].lower()), None)
                                if match_s:
                                    setor_id_auto = match_s["id"]
                                else:
                                    novo_s = sb_insert("setores", {"nome": perfil["setor"]})
                                    if novo_s:
                                        setor_id_auto = novo_s[0]["id"]
                                        setores_existentes.append(novo_s[0])
                            cnpj_auto, nome_oficial_cvm = buscar_cnpj_cvm(nome_emp)
                            if not cnpj_auto:
                                cnpj_auto = buscar_cnpj_brapi(tk)
                            r_emp = sb_insert("empresas", {
                                "ticker": tk, "razao_social": str(nome_emp), "ativo": True,
                                "setor_id": setor_id_auto, "cnpj": cnpj_auto,
                                "segmento": perfil.get("subsetor"),
                            })
                            eid = r_emp[0]["id"] if r_emp else None
                            cadastradas += 1
                        if eid:
                            sb_upsert("lista_analise", {
                                "empresa_id": eid, "usuario_id": uid,
                                "data_selecao": pd.Timestamp.now().isoformat(),
                                "status": "pendente",
                                "origem": json.dumps({"fonte": "Fundamentus", "filtros_ativos":
                                    [k for k,v in st.session_state["filtros_screen"].items() if v["ativo"]]})
                            })
                if cadastradas:
                    st.info(f"{cadastradas} empresa(s) nova(s) criada(s) automaticamente no banco "
                            "(razão social e setor via Fundamentus; CNPJ via BrAPI quando disponível — "
                            "confira e complete manualmente se algum campo não veio).")
                st.success(f"✅ {len(escolhidas)} ação(ões) guardada(s) em 'Minha Lista de Análise'. "
                           "Vá para a Tela 0b para começar a análise.")


# ================================================================
elif pagina == "0b. Minha Lista de Análise":
    st.header("Minha Lista de Análise")
    uid = usuario_id()
    filtro = {"usuario_id": uid} if not sou_admin() else None
    lista_raw = sb_select("lista_analise",
                           "id,empresa_id,data_selecao,status,empresas(ticker,razao_social)", ordem="data_selecao")
    if filtro:
        lista_raw = [r for r in lista_raw if r.get("usuario_id") == uid]
    if not lista_raw:
        st.info("Nenhuma ação guardada ainda. Vá para a Tela 0 (Screening), selecione ações e guarde.")
    else:
        lista = pd.DataFrame([{
            "id": r["id"], "ticker": r["empresas"]["ticker"],
            "razao_social": r["empresas"]["razao_social"],
            "data_selecao": r["data_selecao"], "status": r["status"],
            "empresa_id": r["empresa_id"]} for r in lista_raw])
        st.dataframe(lista[["ticker","razao_social","data_selecao","status"]], use_container_width=True)
        item = st.selectbox("Escolha qual ação analisar agora", lista["ticker"] + " — " + lista["status"])
        ticker_sel = item.split(" — ")[0]
        linha = lista[lista["ticker"]==ticker_sel].iloc[0]
        c1,c2,c3 = st.columns(3)
        if c1.button("▶️ Em análise"):
            if gravar_com_confirmacao(sb_update, "lista_analise", {"status": "em_analise"}, {"id": int(linha["id"])}):
                st.rerun()
        if c2.button("✅ Analisada"):
            if gravar_com_confirmacao(sb_update, "lista_analise", {"status": "analisada"}, {"id": int(linha["id"])}):
                st.rerun()
        if c3.button("🗑️ Remover"):
            if gravar_com_confirmacao(sb_delete, "lista_analise", {"id": int(linha["id"])},
                                       msg_ok="✅ Removido com sucesso.", permitir_vazio=True):
                st.rerun()
        st.markdown("---")
        if st.button(f"🧭 Iniciar Fluxo de Análise guiado para {ticker_sel}", type="primary"):
            sb_update("lista_analise", {"status": "em_analise"}, {"id": int(linha["id"])})
            iniciar_fluxo_analise(int(linha["empresa_id"]))

# ================================================================
elif pagina == "🧭 Fluxo de Análise (guiado)":
    if not st.session_state.get("_fluxo_ativo_confirmado", False):
        # chegou aqui pelo menu lateral (não por um botão "Iniciar Fluxo de
        # Análise" de outra tela) — limpa a empresa anterior pra sempre
        # pedir escolha, em vez de continuar de onde parou sem avisar.
        st.session_state.pop("fluxo_empresa_id", None)
    st.session_state["_fluxo_ativo_confirmado"] = True

    st.header("🧭 Fluxo de Análise Guiado")
    if "fluxo_empresa_id" not in st.session_state:
        st.info("Escolha a ação para começar.")
        empresa_ini = selecionar_empresa("Ação a analisar")
        if empresa_ini is not None and st.button("▶️ Começar análise", type="primary"):
            st.session_state["fluxo_empresa_id"] = int(empresa_ini["id"])
            st.session_state["fluxo_step"] = 1
            st.rerun()
    else:
        emp_id = st.session_state["fluxo_empresa_id"]
        step = st.session_state.get("fluxo_step", 1)
        emp_rows = sb_select("empresas","*", filtros={"id": emp_id})
        if not emp_rows:
            st.error("Empresa não encontrada.")
            del st.session_state["fluxo_empresa_id"]
        else:
            emp = emp_rows[0]
            etapas = ["1. Balanço / DRE","2. Indicadores e Valor Intrínseco","3. Avaliação Qualitativa","4. Relatório Final"]
            st.subheader(f"Analisando: {emp['ticker']} — {emp['razao_social']}")
            st.progress(step/4, text=f"Etapa {step} de 4 — {etapas[step-1]}")
            if st.button("🔁 Trocar de ação"):
                del st.session_state["fluxo_empresa_id"]
                st.rerun()
            st.markdown("---")

            if step == 1:
                st.write("**Etapa 1 — Balanço / DRE**")
                bals = sb_select("balancos_dre","*", filtros={"empresa_id": emp_id}, ordem="data_referencia")
                ultimo_bal = bals[-1] if bals else {}
                if bals:
                    st.success(f"✅ Balanço já existe: {', '.join([b['data_referencia'] for b in bals])}. "
                               "Pode avançar ou buscar dados mais recentes.")
                    st.markdown(f"**Dados atuais do balanço mais recente ({ultimo_bal['data_referencia']}, "
                                f"fonte: {ultimo_bal.get('fonte','—')}):**")
                    m1,m2,m3,m4 = st.columns(4)
                    m1.metric("Ativo Total", f"{ultimo_bal.get('total_assets') or 0:,.0f}")
                    m2.metric("Patrim. Líquido", f"{ultimo_bal.get('total_equity') or 0:,.0f}")
                    m3.metric("Dívida Líquida", f"{ultimo_bal.get('net_debt') or 0:,.0f}")
                    m4.metric("Preço mercado", f"R$ {ultimo_bal.get('preco_mercado_referencia') or 0:,.2f}")
                    m5,m6,m7 = st.columns(3)
                    m5.metric("Receita", f"{ultimo_bal.get('total_revenue') or 0:,.0f}")
                    m6.metric("EBIT", f"{ultimo_bal.get('ebit') or 0:,.0f}")
                    m7.metric("Lucro Líquido", f"{ultimo_bal.get('net_income') or 0:,.0f}")
                    if not any([ultimo_bal.get('total_assets'), ultimo_bal.get('net_income')]):
                        st.warning("⚠️ Esse balanço existe no banco mas está com os valores principais vazios "
                                   "(provavelmente uma busca anterior não trouxe dados completos). Clique em "
                                   "'Buscar balanço automático agora' de novo, ou preencha manualmente abaixo.")

                st.subheader("🌐 Buscar balanço automaticamente (Fundamentus, com Yahoo Finance de reserva)")
                st.caption("Clique para buscar os dados mais recentes do balanço e DRE — tenta o Fundamentus "
                           "primeiro (mais completo para ações brasileiras) e só usa o Yahoo Finance se necessário.")
                if st.button("🔄 Buscar balanço automático agora", type="primary"):
                    with st.spinner(f"Buscando dados de {emp['ticker']}..."):
                        try:
                            dados = buscar_balanco_multi_fonte(emp["ticker"])
                            if dados.get("data_referencia"):
                                dados["empresa_id"] = emp_id
                                r = gravar_com_confirmacao(sb_upsert, "balancos_dre",
                                    {k:v for k,v in dados.items() if v is not None},
                                    msg_ok=f"✅ Balanço de {dados['data_referencia']} importado da fonte "
                                           f"{dados.get('fonte','desconhecida')} e salvo com sucesso.",
                                    msg_erro="❌ Não foi possível salvar o balanço buscado.")
                                if r:
                                    st.rerun()
                            else:
                                st.warning("Não encontrou dados de balanço nem no Fundamentus nem no Yahoo "
                                           "Finance para este ticker. Use o lançamento manual.")
                        except Exception as e:
                            st.error(f"Erro ao buscar balanço: {e}")
                            st.info("Verifique se o ticker está correto (ex.: TRIS3, B3SA3) e tente novamente.")

                st.markdown("---")
                st.subheader("✏️ Ou lance/edite manualmente")
                st.caption("Este formulário já vem preenchido com o último balanço salvo (se existir), "
                           "pra você ajustar em vez de digitar tudo de novo.")
                with st.form("fluxo_balanco"):
                    data_ref = st.text_input("Data de referência", ultimo_bal.get("data_referencia", "2024-12-31"))
                    c1,c2,c3 = st.columns(3)
                    dados_bal = {
                        "empresa_id": emp_id, "data_referencia": data_ref,
                        "total_assets": c1.number_input("Total Assets",value=float(ultimo_bal.get("total_assets") or 0.0)),
                        "total_liabilities": c2.number_input("Total Liabilities",value=float(ultimo_bal.get("total_liabilities") or 0.0)),
                        "total_equity": c3.number_input("Total Equity",value=float(ultimo_bal.get("total_equity") or 0.0)),
                        "net_debt": c1.number_input("Dívida Líquida",value=float(ultimo_bal.get("net_debt") or 0.0)),
                        "share_issued": c2.number_input("Nº Ações (milhares)",value=float(ultimo_bal.get("share_issued") or 0.0)),
                        "preco_mercado_referencia": c3.number_input("Preço de mercado",value=float(ultimo_bal.get("preco_mercado_referencia") or 0.0)),
                        "total_revenue": c1.number_input("Total Revenue",value=float(ultimo_bal.get("total_revenue") or 0.0)),
                        "net_income": c2.number_input("Net Income",value=float(ultimo_bal.get("net_income") or 0.0)),
                        "ebitda": c3.number_input("EBITDA",value=float(ultimo_bal.get("ebitda") or 0.0)),
                        "ebit": c1.number_input("EBIT",value=float(ultimo_bal.get("ebit") or 0.0)),
                        "depreciacao_amortizacao": c2.number_input("Depreciação",value=float(ultimo_bal.get("depreciacao_amortizacao") or 0.0)),
                        "capex": c3.number_input("CAPEX",value=float(ultimo_bal.get("capex") or 0.0)),
                        "fonte": "Lançado manualmente"
                    }
                    if st.form_submit_button("💾 Salvar balanço manual"):
                        r = gravar_com_confirmacao(sb_upsert, "balancos_dre", dados_bal,
                            msg_ok="✅ Balanço salvo com sucesso.", msg_erro="❌ Não foi possível salvar o balanço.")
                        if r:
                            st.rerun()

            elif step == 2:
                st.write("**Etapa 2 — Indicadores e Valor Intrínseco**")
                st.caption("CDI e Selic são buscados automaticamente do banco de índices. WACC = Selic + 4%.")
                bals = sb_select("balancos_dre","*", filtros={"empresa_id": emp_id}, ordem="data_referencia")
                if not bals:
                    st.warning("Sem balanço. Volte para a Etapa 1.")
                else:
                    datas = [b["data_referencia"] for b in bals]
                    data_ref = st.selectbox("Data de referência", datas, key="fluxo_data_ref")
                    bal = next(b for b in bals if b["data_referencia"] == data_ref)

                    sb = get_supabase()
                    cdi_anual, selic_anual = calc.buscar_cdi_selic_atual(sb)
                    st.info(f"📊 CDI anual: **{cdi_anual:.2f}%** | Selic anual: **{selic_anual:.2f}%** | WACC: **{selic_anual+4:.2f}%** (Selic + 4%)")

                    ind = calc.calcular_indicadores(bal)
                    st.subheader("Indicadores fundamentalistas")
                    st.dataframe(pd.DataFrame([{"Indicador":k,"Valor":round(v,4) if v is not None else "—"} for k,v in ind.items()]), use_container_width=True)

                    if st.button("💾 Gravar indicadores no banco"):
                        inds_def = sb_select("indicadores_definicao","id,nome")
                        ok_count, falha_count = 0, 0
                        for nome, valor in ind.items():
                            match = next((x for x in inds_def if x["nome"]==nome), None)
                            if match and valor is not None:
                                try:
                                    res = sb_upsert("indicadores_calculados",{"empresa_id":emp_id,"data_referencia":data_ref,"indicador_id":match["id"],"valor":valor})
                                    ok_count += 1 if res else 0
                                    falha_count += 0 if res else 1
                                except Exception:
                                    falha_count += 1
                        if falha_count == 0 and ok_count > 0:
                            st.success(f"✅ {ok_count} indicador(es) gravado(s) com sucesso.")
                        elif ok_count > 0:
                            st.warning(f"⚠️ {ok_count} gravado(s), mas {falha_count} falharam.")
                        else:
                            st.error("❌ Não foi possível gravar os indicadores.")

                    st.markdown("---")
                    st.subheader("Valor Intrínseco")
                    g_auto = 6.0
                    historico_lucros = [b.get("net_income") for b in sorted(bals, key=lambda x: x["data_referencia"]) if b.get("net_income")]
                    if len(historico_lucros) >= 2:
                        g_auto = round(calc.calcular_g_cagr(historico_lucros), 2)
                        st.caption(f"Taxa g calculada pelo CAGR do lucro: **{g_auto:.2f}%**")

                    g = st.number_input("Taxa de crescimento g (%) — ajuste se necessário", value=g_auto, step=0.5, key="fluxo_g")

                    resultado_vi = calc.calcular_valor_intrinseco_completo(
                        bal, g_pct=g, cdi_pct=cdi_anual, selic_pct=selic_anual, anos_fcd=5, g_terminal_pct=3.0)

                    r1,r2,r3,r4 = st.columns(4)
                    r1.metric("Graham Simplif.", f"R$ {resultado_vi['vi_simplificado']:.2f}" if resultado_vi['vi_simplificado'] else "—")
                    r2.metric("Número Graham",   f"R$ {resultado_vi['vi_numero_graham']:.2f}" if resultado_vi['vi_numero_graham'] else "—")
                    r3.metric("Graham Complexo", f"R$ {resultado_vi['vi_complexo']:.2f}" if resultado_vi['vi_complexo'] else "—")
                    r4.metric("FCD",             f"R$ {resultado_vi['vi_fcd']:.2f}" if resultado_vi['vi_fcd'] else "—")

                    preco = resultado_vi['preco_mercado']
                    vi_medio = resultado_vi['vi_medio']
                    margem = resultado_vi['margem_seguranca_pct']
                    classe = resultado_vi['classificacao']
                    if preco and vi_medio:
                        cor = "green" if classe=="Comprar" else ("orange" if classe=="Observar" else "red")
                        st.markdown(f"**Preço:** R$ {preco:.2f} | **VI médio:** R$ {vi_medio:.2f} | **Margem:** {margem:.1f}% | **:{cor}[{classe}]**")

                    with st.expander("Ver premissas e detalhe do FCD"):
                        st.json(resultado_vi['premissas'])

                    if st.button("💾 Gravar valores intrínsecos no banco"):
                        ok_count, falha_count = 0, 0
                        for metodo, vi in [("simplificado",resultado_vi['vi_simplificado']),
                                           ("numero_graham",resultado_vi['vi_numero_graham']),
                                           ("complexo",resultado_vi['vi_complexo']),
                                           ("fcd",resultado_vi['vi_fcd'])]:
                            if vi:
                                try:
                                    res = sb_upsert("valor_intrinseco",{"empresa_id":emp_id,"data_referencia":data_ref,
                                        "metodo":metodo,"valor":vi,"premissas_json":resultado_vi['premissas']})
                                    ok_count += 1 if res else 0
                                    falha_count += 0 if res else 1
                                except Exception:
                                    falha_count += 1
                        if falha_count == 0 and ok_count > 0:
                            st.success(f"✅ {ok_count} valor(es) intrínseco(s) gravado(s) com sucesso.")
                        elif ok_count > 0:
                            st.warning(f"⚠️ {ok_count} gravado(s), mas {falha_count} falharam.")
                        else:
                            st.error("❌ Não foi possível gravar os valores intrínsecos.")

            elif step == 3:
                st.write("**Etapa 3 — Avaliação qualitativa.**")
                av = sb_select("avaliacao_qualitativa_buffett","*",filtros={"empresa_id":emp_id})
                atual = av[0] if av else {}
                with st.form("fluxo_buffett"):
                    moat = st.selectbox("Moat",["nenhum","fraco","moderado","forte"],index=["nenhum","fraco","moderado","forte"].index(atual.get("moat","nenhum")) if atual.get("moat") else 0)
                    moat_just = st.text_area("Justificativa do moat", atual.get("moat_justificativa",""))
                    gestao = st.slider("Qualidade da gestão (1-5)",1,5,int(atual.get("qualidade_gestao",3) or 3))
                    prev = st.selectbox("Previsibilidade",["baixa","media","alta"],index=["baixa","media","alta"].index(atual.get("previsibilidade","media")) if atual.get("previsibilidade") else 1)
                    circulo = st.checkbox("Dentro do meu círculo de competência?", bool(atual.get("circulo_competencia",False)))
                    if st.form_submit_button("💾 Salvar avaliação"):
                        gravar_com_confirmacao(sb_upsert, "avaliacao_qualitativa_buffett",
                            {"empresa_id":emp_id,"moat":moat,"moat_justificativa":moat_just,"qualidade_gestao":gestao,
                             "previsibilidade":prev,"circulo_competencia":circulo,"data_avaliacao":date.today().isoformat()},
                            msg_ok="✅ Avaliação salva com sucesso.", msg_erro="❌ Não foi possível salvar a avaliação.")

            elif step == 4:
                st.write("**Etapa 4 — Relatório final: Comprar, Manter ou Vender?**")
                bals = sb_select("balancos_dre","*",filtros={"empresa_id":emp_id},ordem="data_referencia")
                if not bals:
                    st.warning("Sem balanço. Volte para a Etapa 1.")
                else:
                    bal = bals[-1]
                    preco = bal.get("preco_mercado_referencia")
                    vis = sb_select("valor_intrinseco","metodo,valor",filtros={"empresa_id":emp_id,"data_referencia":bal["data_referencia"]})
                    st.markdown(f"#### {emp['ticker']} — {emp['razao_social']}")
                    st.write(f"Preço de mercado: **R$ {preco:.2f}**" if preco else "Sem preço lançado.")
                    if vis:
                        df_vi = pd.DataFrame(vis)
                        st.dataframe(df_vi, use_container_width=True)
                        vi_medio = sum(v["valor"] for v in vis) / len(vis)
                        margem = calc.margem_seguranca(vi_medio, preco)
                        classe = calc.classificar(margem)
                        cor = "green" if classe=="Comprar" else ("orange" if classe=="Observar" else "red")
                        st.markdown(f"**Valor intrínseco médio: R$ {vi_medio:.2f} | Margem: {margem:.1f}% | Classificação: :{cor}[{classe}]**")
                    av = sb_select("avaliacao_qualitativa_buffett","*",filtros={"empresa_id":emp_id})
                    if av:
                        a = av[0]
                        st.write(f"Avaliação: Moat **{a['moat']}** | Gestão nota **{a['qualidade_gestao']}** | Previsibilidade **{a['previsibilidade']}**")

                    st.markdown("---")
                    st.subheader("⭐ Índice de Boa Empresa")
                    renderizar_diagnostico_boa_empresa(emp_id, emp)

                    st.markdown("---")
                    if st.button("✅ Concluir análise desta ação", type="primary"):
                        gravar_com_confirmacao(sb_update, "lista_analise", {"status":"analisada"},
                            {"empresa_id":emp_id,"usuario_id":usuario_id()},
                            msg_ok="✅ Análise concluída com sucesso!", msg_erro="❌ Não foi possível concluir a análise.")

            st.markdown("---")
            n1,n2,_ = st.columns([1,1,4])
            if step>1 and n1.button("⬅️ Voltar"):
                st.session_state["fluxo_step"]=step-1; st.rerun()
            if step<4 and n2.button("Próximo ➡️",type="primary"):
                st.session_state["fluxo_step"]=step+1; st.rerun()

# ================================================================
elif pagina == "1. Empresas e Setores":
    st.header("Empresas e Setores")
    st.dataframe(lista_empresas(), use_container_width=True)
    st.caption("Para cadastrar um novo Setor, use a tela '10. Tabelas de Apoio'.")
    st.subheader("Cadastrar ou editar empresa")

    setores = sb_select("setores","id,nome",ordem="nome")
    tipos_mercado = sb_select("tipo_mercado","codigo",ordem="codigo")
    sits = sb_select("situacao_empresa","codigo",ordem="codigo")
    tipos_ativo = sb_select("tipos_ativo","id,nome",ordem="nome")

    # ---- escolher empresa existente pra editar (opcional) ----
    df_emp_edit = lista_empresas()
    mapa_edicao = {"➕ Nova empresa": None}
    if not df_emp_edit.empty:
        for _, r in df_emp_edit.iterrows():
            rotulo = f"{r['razao_social']} ({r['ticker'] or 'sem ticker'})"
            mapa_edicao[rotulo] = int(r["id"])
    escolha_edit = st.selectbox("Selecione uma empresa para editar, ou cadastre uma nova", list(mapa_edicao.keys()))
    empresa_id_edicao = mapa_edicao[escolha_edit]

    dados_atuais = {}
    banco_atual = {}
    tickers_atuais = []
    if empresa_id_edicao:
        registro = sb_select("empresas", "*", filtros={"id": empresa_id_edicao})
        if registro:
            dados_atuais = registro[0]
            if dados_atuais.get("setor_id"):
                s_match = next((s for s in setores if s["id"] == dados_atuais["setor_id"]), None)
                dados_atuais["setor_nome"] = s_match["nome"] if s_match else ""
            if dados_atuais.get("tipo_ativo_id") and tipos_ativo:
                t_match = next((t for t in tipos_ativo if t["id"] == dados_atuais["tipo_ativo_id"]), None)
                dados_atuais["tipo_ativo_nome"] = t_match["nome"] if t_match else "Ação"
            banco_reg = sb_select("bancos_dados", "*", filtros={"empresa_id": empresa_id_edicao})
            if banco_reg:
                banco_atual = banco_reg[0]
            tickers_atuais = sb_select("ativos_empresa", "*", filtros={"empresa_id": empresa_id_edicao}, ordem="codigo") or []

    # ---- Tickers / código(s) da ação — uma empresa pode ter mais de um (ex: PETR3 e PETR4) ----
    st.markdown("**Ticker(s) / Código(s) da ação**")
    st.caption("O ticker é o código da ação na bolsa, não uma informação que você digita livremente — "
               "uma mesma empresa pode ter mais de um (ex: PETR3 e PETR4 são ambos da Petrobras).")
    if empresa_id_edicao:
        if tickers_atuais:
            df_tk = pd.DataFrame(tickers_atuais)
            df_tk["tipo_ativo"] = df_tk["tipo_ativo_id"].apply(
                lambda tid: next((t["nome"] for t in tipos_ativo if t["id"] == tid), "—"))
            st.dataframe(df_tk[["codigo","tipo_ativo","ativo"]], use_container_width=True, hide_index=True)
        else:
            st.caption("Nenhum ticker cadastrado ainda para esta empresa.")
        with st.form("form_add_ticker", clear_on_submit=True):
            ct1, ct2, ct3 = st.columns([2,2,1])
            novo_codigo = ct1.text_input("Novo ticker (ex: PETR3)")
            tipo_ativo_nomes_tk = [t["nome"] for t in tipos_ativo] if tipos_ativo else ["Ação"]
            novo_tipo_nome = ct2.selectbox("Tipo de ativo", tipo_ativo_nomes_tk, key="novo_tipo_ativo_tk")
            ct3.write("")
            if ct3.form_submit_button("➕ Adicionar") :
                if not novo_codigo.strip():
                    st.error("❌ Digite o código do ticker antes de adicionar.")
                else:
                    ta_id_tk = next((t["id"] for t in tipos_ativo if t["nome"] == novo_tipo_nome), None)
                    r1 = gravar_com_confirmacao(sb_upsert, "ativos_empresa",
                        {"empresa_id": empresa_id_edicao, "codigo": novo_codigo.upper(),
                         "tipo_ativo_id": ta_id_tk, "ativo": True},
                        msg_ok=f"✅ Ticker {novo_codigo.upper()} adicionado com sucesso.",
                        msg_erro="❌ Não foi possível adicionar o ticker.")
                    # se a empresa ainda não tem ticker principal, este vira o principal
                    if r1 and not dados_atuais.get("ticker"):
                        sb_update("empresas", {"ticker": novo_codigo.upper()}, {"id": empresa_id_edicao})
                    if r1:
                        st.rerun()
    else:
        st.info("Salve a empresa primeiro (com pelo menos um ticker abaixo) para depois adicionar tickers extras.")

    if empresa_id_edicao and not dados_atuais.get("cnpj"):
        cc1, cc2 = st.columns([1, 3])
        if cc1.button("🔎 Buscar CNPJ"):
            with st.spinner("Buscando no cadastro oficial da CVM..."):
                cnpj_encontrado, nome_cvm = buscar_cnpj_cvm(dados_atuais.get("razao_social", ""))
                fonte_cnpj = "CVM"
                if not cnpj_encontrado:
                    cnpj_encontrado = buscar_cnpj_brapi(dados_atuais.get("ticker", ""))
                    fonte_cnpj = "BrAPI"
            if cnpj_encontrado:
                r_cnpj = gravar_com_confirmacao(sb_update, "empresas", {"cnpj": cnpj_encontrado}, {"id": empresa_id_edicao},
                    msg_ok=f"✅ CNPJ encontrado via {fonte_cnpj} e salvo: {cnpj_encontrado}"
                           + (f" (nome oficial: {nome_cvm})" if fonte_cnpj == "CVM" and nome_cvm else ""),
                    msg_erro="❌ CNPJ encontrado mas não foi possível salvar.")
                if r_cnpj:
                    st.rerun()
            else:
                st.warning("Não encontrou o CNPJ automaticamente (nem na CVM, nem via BrAPI). "
                           "Pode digitar manualmente no campo CNPJ abaixo.")
        cc2.caption("Busca primeiro no cadastro oficial da CVM (por nome aproximado), "
                    "com BrAPI como reserva.")

    st.markdown("---")
    with st.form("form_emp"):
        c1,c2,c3 = st.columns(3)
        ticker_principal = c1.text_input("Ticker principal *", value=dados_atuais.get("ticker","") or "",
                                          help="Usado para identificar a empresa nas telas de análise. "
                                               "Se a empresa tiver mais de um ticker, cadastre os demais acima depois de salvar.")
        razao = c2.text_input("Razão social *", value=dados_atuais.get("razao_social","") or "")
        cnpj = c3.text_input("CNPJ (opcional)", value=dados_atuais.get("cnpj","") or "")

        c4,c5,c6 = st.columns(3)
        setor_nomes = [""]+[s["nome"] for s in setores]
        setor_idx = setor_nomes.index(dados_atuais.get("setor_nome","")) if dados_atuais.get("setor_nome") in setor_nomes else 0
        setor_nome = c4.selectbox("Setor (opcional)", setor_nomes, index=setor_idx)
        segmento = c5.text_input("Segmento (opcional)", value=dados_atuais.get("segmento","") or "")
        tipo_ativo_nomes = [t["nome"] for t in tipos_ativo] if tipos_ativo else ["Ação"]
        ta_idx = tipo_ativo_nomes.index(dados_atuais.get("tipo_ativo_nome","Ação")) if dados_atuais.get("tipo_ativo_nome") in tipo_ativo_nomes else 0
        tipo_ativo_nome = c6.selectbox("Tipo de ativo principal (opcional)", tipo_ativo_nomes, index=ta_idx)

        c7,c8 = st.columns(2)
        tipos_m_opcoes = [""]+[t["codigo"] for t in tipos_mercado] if tipos_mercado else [""]
        tm_idx = tipos_m_opcoes.index(dados_atuais.get("tipo_mercado_codigo","")) if dados_atuais.get("tipo_mercado_codigo","") in tipos_m_opcoes else 0
        tipo_m = c7.selectbox("Segmento de listagem B3 (opcional)", tipos_m_opcoes, index=tm_idx,
                               help="Novo Mercado, Nível 1, Nível 2 ou Tradicional — não confundir com 'Tipo de ativo'.")
        sits_opcoes = [""]+[s["codigo"] for s in sits] if sits else [""]
        sit_idx = sits_opcoes.index(dados_atuais.get("situacao_codigo","")) if dados_atuais.get("situacao_codigo","") in sits_opcoes else 0
        sit = c8.selectbox("Situação (opcional)", sits_opcoes, index=sit_idx)

        na_bolsa = st.checkbox("Empresa negociada na bolsa (B3)", value=dados_atuais.get("na_bolsa", True))
        if not na_bolsa:
            st.caption("⚠️ Fora da bolsa: não dá pra buscar indicadores automáticos. "
                       "Os dados terão que ser preenchidos manualmente com base no último balanço.")

        site = st.text_input("Site (opcional)", value=dados_atuais.get("site","") or "")
        desc = st.text_area("Descrição do negócio (opcional)", value=dados_atuais.get("descricao_negocio","") or "")
        futuro = st.text_area("Análise de futuro (opcional)", value=dados_atuais.get("analise_futuro","") or "")

        eh_banco = st.checkbox("É um banco (habilita Índice de Basileia e Carteira de Crédito)",
                                value=dados_atuais.get("eh_banco", False))
        indice_basileia = carteira_credito = fator_risco = link_info_banco = None
        if eh_banco:
            cb1,cb2 = st.columns(2)
            indice_basileia = cb1.number_input("Índice de Basileia (%) (opcional)", min_value=0.0, step=0.01,
                value=float(banco_atual.get("indice_basileia") or 0.0))
            carteira_credito = cb2.number_input("Carteira de Crédito (R$) (opcional)", min_value=0.0, step=1000.0,
                value=float(banco_atual.get("carteira_credito") or 0.0))
            fator_risco = st.text_input("Fator de risco (opcional)", value=banco_atual.get("fator_risco","") or "")
            link_info_banco = st.text_input("Link com informações do banco (BCB, RI etc.) (opcional)",
                value=banco_atual.get("link_informacoes","") or "")

        st.caption("* Campos obrigatórios")
        enviado = st.form_submit_button("💾 Salvar empresa")

        if enviado:
            faltando = []
            if not ticker_principal.strip():
                faltando.append("Ticker principal")
            if not razao.strip():
                faltando.append("Razão social")
            if faltando:
                st.error(f"❌ Não foi possível salvar — preencha: {', '.join(faltando)}.")
            else:
                setor_id = next((s["id"] for s in setores if s["nome"]==setor_nome), None)
                ta_id = next((t["id"] for t in tipos_ativo if t["nome"] == tipo_ativo_nome), None)
                payload = {
                    "ticker": ticker_principal.strip().upper(), "cnpj": cnpj, "razao_social": razao,
                    "setor_id": setor_id, "tipo_mercado_codigo": tipo_m or None, "situacao_codigo": sit or None,
                    "site": site, "descricao_negocio": desc, "analise_futuro": futuro,
                    "segmento": segmento, "na_bolsa": na_bolsa, "eh_banco": eh_banco,
                }
                if ta_id:
                    payload["tipo_ativo_id"] = ta_id

                if empresa_id_edicao:
                    # empresa já existe — UPDATE por id (não upsert, pra não depender de
                    # qual coluna o upsert usa como chave de conflito)
                    r_emp = gravar_com_confirmacao(sb_update, "empresas", payload, {"id": empresa_id_edicao},
                        msg_ok=f"✅ Empresa {ticker_principal.strip().upper()} atualizada com sucesso.",
                        msg_erro="❌ Não foi possível atualizar a empresa.")
                    eid_salvo = empresa_id_edicao if r_emp else None
                else:
                    # empresa nova — INSERT
                    r_emp = gravar_com_confirmacao(sb_insert, "empresas", payload,
                        msg_ok=f"✅ Empresa {ticker_principal.strip().upper()} cadastrada com sucesso.",
                        msg_erro="❌ Não foi possível cadastrar a empresa (confira se o ticker já existe).")
                    eid_salvo = r_emp[0]["id"] if r_emp else None

                # garante que o ticker principal também exista na lista de ativos
                if eid_salvo:
                    ja_existe_tk = sb_select("ativos_empresa","id",filtros={"empresa_id":eid_salvo,"codigo":ticker_principal.strip().upper()})
                    if not ja_existe_tk:
                        gravar_com_confirmacao(sb_upsert, "ativos_empresa",
                            {"empresa_id": eid_salvo, "codigo": ticker_principal.strip().upper(),
                             "tipo_ativo_id": ta_id, "ativo": True},
                            msg_ok="✅ Ticker principal registrado na lista de ativos.",
                            msg_erro="⚠️ Empresa salva, mas não foi possível registrar o ticker na lista de ativos.")

                if eh_banco and eid_salvo:
                    gravar_com_confirmacao(sb_upsert, "bancos_dados", {
                        "empresa_id": eid_salvo, "cnpj": cnpj,
                        "indice_basileia": indice_basileia, "carteira_credito": carteira_credito,
                        "fator_risco": fator_risco, "link_informacoes": link_info_banco,
                        "data_referencia": str(date.today()), "fonte": "Manual",
                    }, msg_ok="✅ Dados de banco salvos com sucesso.",
                       msg_erro="⚠️ Empresa salva, mas houve um erro ao salvar dados de banco.")

                if eid_salvo:
                    st.rerun()

    # ---- Rating: busca (links de conferência) + edição manual — só em modo edição ----
    if empresa_id_edicao:
        st.markdown("---")
        st.subheader("Rating")
        atual_rating = dados_atuais.get("rating") or "—"
        st.write(f"Rating atual: **{atual_rating}** "
                 f"({dados_atuais.get('rating_agencia') or '—'}, perspectiva {dados_atuais.get('rating_perspectiva') or '—'})")
        if st.button("🔎 Buscar Rating"):
            st.info("Não existe uma fonte pública gratuita e estável para buscar rating de crédito 100% "
                    "automaticamente. Aqui estão links diretos de busca em cada agência para conferir rápido:")
            links = buscar_rating_links(dados_atuais.get("razao_social",""))
            for nome, url in links.items():
                st.markdown(f"- [{nome}]({url})")
        with st.form("form_rating_manual"):
            rm1, rm2, rm3, rm4 = st.columns(4)
            novo_rating = rm1.text_input("Rating (opcional)", value=dados_atuais.get("rating","") or "")
            nova_agencia = rm2.selectbox("Agência (opcional)", ["","Fitch","Moody's","S&P","Outra"],
                index=(["","Fitch","Moody's","S&P","Outra"].index(dados_atuais.get("rating_agencia",""))
                       if dados_atuais.get("rating_agencia","") in ["","Fitch","Moody's","S&P","Outra"] else 0))
            nova_persp = rm3.selectbox("Perspectiva (opcional)", ["","Positiva","Estável","Negativa"],
                index=(["","Positiva","Estável","Negativa"].index(dados_atuais.get("rating_perspectiva",""))
                       if dados_atuais.get("rating_perspectiva","") in ["","Positiva","Estável","Negativa"] else 0))
            novo_preco_alvo = rm4.number_input("Preço alvo analistas (opcional)", min_value=0.0, step=0.01,
                                                value=float(dados_atuais.get("preco_alvo_analistas") or 0.0))
            if st.form_submit_button("💾 Salvar rating"):
                r = gravar_com_confirmacao(sb_update, "empresas", {
                    "rating": novo_rating, "rating_agencia": nova_agencia,
                    "rating_perspectiva": nova_persp, "preco_alvo_analistas": novo_preco_alvo,
                }, {"id": empresa_id_edicao},
                   msg_ok="✅ Rating salvo com sucesso.", msg_erro="❌ Não foi possível salvar o rating.")
                if r:
                    st.rerun()

    # ---- Botões extras — só aparecem em modo edição ----
    if empresa_id_edicao:
        st.markdown("---")
        st.subheader("Mais sobre esta empresa")
        bt1, bt2, bt3, bt4, bt5 = st.columns(5)
        if bt1.button("📊 Indicadores"): st.session_state["emp_secao_ativa"] = "indicadores"
        if bt2.button("⭐ Análise de Boa Empresa"): st.session_state["emp_secao_ativa"] = "diagnostico"
        if bt3.button("📈 Histórico de Lucros"): st.session_state["emp_secao_ativa"] = "historico"
        if bt4.button("📰 Notícias Relevantes"): st.session_state["emp_secao_ativa"] = "noticias"
        if bt5.button("🔮 Futuro da Empresa"): st.session_state["emp_secao_ativa"] = "futuro"

        secao = st.session_state.get("emp_secao_ativa")

        if secao == "indicadores":
            st.markdown("#### 📊 Indicadores (Buffett / Value Investing)")
            inds_calc = sb_select("indicadores_calculados","*",filtros={"empresa_id":empresa_id_edicao})
            inds_def = sb_select("indicadores_definicao","id,nome")
            if inds_calc:
                df_ic = pd.DataFrame(inds_calc)
                df_ic["indicador"] = df_ic["indicador_id"].apply(
                    lambda iid: next((i["nome"] for i in inds_def if i["id"]==iid), f"#{iid}"))
                cols_show = [c for c in ["indicador","valor","data_referencia","fonte","atualizado_em"] if c in df_ic.columns]
                st.dataframe(df_ic[cols_show], use_container_width=True, hide_index=True)
            else:
                st.caption("Nenhum indicador calculado ainda para esta empresa.")
            if st.button("🔄 Atualizar (buscar balanço mais recente e recalcular)"):
                try:
                    dados_bal = buscar_balanco_multi_fonte(dados_atuais["ticker"])
                    if dados_bal.get("data_referencia"):
                        fonte_dados = dados_bal.get("fonte", "desconhecida")
                        dados_bal["empresa_id"] = empresa_id_edicao
                        r_bal = gravar_com_confirmacao(sb_upsert, "balancos_dre",
                            {k:v for k,v in dados_bal.items() if v is not None},
                            msg_ok=f"✅ Balanço de {dados_bal['data_referencia']} salvo (fonte: {fonte_dados}).",
                            msg_erro="❌ Não foi possível salvar o balanço buscado.")
                        if r_bal:
                            ind_novo = calc.calcular_indicadores(dados_bal)
                            ok_count, falha_count = 0, 0
                            for nome, valor in ind_novo.items():
                                match = next((x for x in inds_def if x["nome"]==nome), None)
                                if match and valor is not None:
                                    try:
                                        res = sb_upsert("indicadores_calculados", {
                                            "empresa_id": empresa_id_edicao, "data_referencia": dados_bal["data_referencia"],
                                            "indicador_id": match["id"], "valor": valor,
                                            "fonte": fonte_dados, "atualizado_em": pd.Timestamp.now().isoformat(),
                                        })
                                        ok_count += 1 if res else 0
                                        falha_count += 0 if res else 1
                                    except Exception:
                                        falha_count += 1
                            if falha_count == 0 and ok_count > 0:
                                st.success(f"✅ {ok_count} indicador(es) atualizado(s) com sucesso "
                                           f"(fonte: {fonte_dados}, data: {dados_bal['data_referencia']}).")
                                st.rerun()
                            elif ok_count > 0:
                                st.warning(f"⚠️ {ok_count} atualizado(s), mas {falha_count} falharam.")
                            else:
                                st.error("❌ Não foi possível atualizar os indicadores.")
                    else:
                        st.warning("Não encontrou dados de balanço recentes para este ticker.")
                except Exception as e:
                    st.error(f"Erro ao atualizar: {e}")

        elif secao == "diagnostico":
            st.markdown("#### ⭐ Análise de Boa Empresa — diagnóstico")
            renderizar_diagnostico_boa_empresa(empresa_id_edicao, dados_atuais)

        elif secao == "historico":
            st.markdown("#### 📈 Histórico de Lucros")
            hist = sb_select("historico_resultados","*",filtros={"empresa_id":empresa_id_edicao},ordem="ano")
            if hist:
                st.dataframe(pd.DataFrame(hist)[["ano","lucro_liquido","teve_prejuizo"]], use_container_width=True, hide_index=True)
            else:
                bals_h = sb_select("balancos_dre","data_referencia,net_income",filtros={"empresa_id":empresa_id_edicao})
                if bals_h:
                    st.caption("Sem histórico dedicado ainda — mostrando o que existe nos balanços lançados:")
                    st.dataframe(pd.DataFrame(bals_h), use_container_width=True, hide_index=True)
                else:
                    st.caption("Nenhum histórico de lucro cadastrado ainda.")
            with st.form("form_hist_lucro"):
                hc1, hc2, hc3 = st.columns([1,1,1])
                ano_h = hc1.number_input("Ano", min_value=1990, max_value=2100, value=date.today().year-1, step=1)
                lucro_h = hc2.number_input("Lucro líquido (negativo = prejuízo)", step=1000.0)
                if hc3.form_submit_button("➕ Adicionar"):
                    r = gravar_com_confirmacao(sb_upsert, "historico_resultados",
                        {"empresa_id": empresa_id_edicao, "ano": int(ano_h), "lucro_liquido": lucro_h, "fonte": "Manual"},
                        msg_ok="✅ Registro adicionado com sucesso.", msg_erro="❌ Não foi possível adicionar o registro.")
                    if r:
                        st.rerun()

        elif secao == "noticias":
            st.markdown("#### 📰 Notícias Relevantes")
            st.caption("Não são armazenadas — sempre buscadas na hora. Cobrem: resultados (lucro/prejuízo), "
                       "dividendos, novos negócios, expansão, posição no Ibovespa, aumento de preços, "
                       "problemas judiciais, recuperação judicial, recompra de títulos, parcerias, venda de "
                       "ativos, indicadores fora do padrão, inovação, aquisição, mudança societária, expansão "
                       "nos EUA, acordos, investigações, projeções e impacto de decisões políticas — dos "
                       "últimos ~2 meses.")
            import urllib.parse as _up
            termo = _up.quote(f"{dados_atuais.get('razao_social','')} notícias")
            st.markdown(f"🔗 [Buscar notícias recentes no Google News](https://news.google.com/search?q={termo}&hl=pt-BR&gl=BR)")
            st.info("Dica: peça no chat 'notícias relevantes sobre [empresa]' para eu pesquisar e resumir "
                    "direto na conversa — o app publicado sozinho não tem acesso a busca de notícias em tempo real.")

        elif secao == "futuro":
            st.markdown("#### 🔮 Futuro da Empresa")
            st.caption("Também não é armazenado separadamente — cobre notícias do segmento, perspectiva do "
                       "país que afetam o setor, governança da empresa e novos negócios.")
            if dados_atuais.get("analise_futuro"):
                st.write(dados_atuais["analise_futuro"])
            else:
                st.caption("Nenhuma análise de futuro escrita ainda — preencha o campo 'Análise de futuro' no formulário acima.")
            import urllib.parse as _up2
            termo2 = _up2.quote(f"{dados_atuais.get('razao_social','')} perspectivas futuro setor governança")
            st.markdown(f"🔗 [Buscar perspectivas futuras no Google News](https://news.google.com/search?q={termo2}&hl=pt-BR&gl=BR)")

# ================================================================
elif pagina == "4. Critérios e Índice de Qualidade":
    st.header("⭐ Índice de Boa Empresa — Screening")
    st.caption("Critérios: Valuation 30% (ou Rating 30% quando disponível) + Qualidade Financeira 45% "
               "+ Qualidade do Negócio 25%. Nota final ≥70 = Boa empresa, 50–70 = Observar, <50 = Evitar. "
               "Recalcular usa os dados já cadastrados de cada empresa (balanço, indicadores, avaliação qualitativa).")

    df_todas = lista_empresas()
    if df_todas.empty:
        st.info("Nenhuma empresa cadastrada ainda. Cadastre em '1. Empresas e Setores'.")
    else:
        c1, c2 = st.columns([1, 3])
        recalcular_tudo = c1.button("🔄 Recalcular todas agora", type="primary")
        classes_filtro = c2.multiselect("Filtrar por classificação",
                                         ["Boa empresa", "Observar", "Evitar", "Não calculado"],
                                         default=["Boa empresa", "Observar", "Evitar", "Não calculado"])

        if recalcular_tudo:
            progresso = st.progress(0.0, text="Calculando...")
            erros = []
            total = len(df_todas)
            for i, row in df_todas.reset_index(drop=True).iterrows():
                eid = int(row["id"])
                try:
                    emp_rows = sb_select("empresas", "*", filtros={"id": eid})
                    if not emp_rows:
                        continue
                    emp_c = emp_rows[0]
                    bals_c = sb_select("balancos_dre", "*", filtros={"empresa_id": eid}, ordem="data_referencia")
                    if not bals_c:
                        erros.append(f"{row['ticker']}: sem balanço cadastrado, pulado")
                        continue
                    bal_c = bals_c[-1]
                    ind_c = calc.calcular_indicadores(bal_c)
                    preco_c = bal_c.get("preco_mercado_referencia")
                    vis_c = sb_select("valor_intrinseco", "metodo,valor",
                                       filtros={"empresa_id": eid, "data_referencia": bal_c["data_referencia"]})
                    vi_medio_c = (sum(v["valor"] for v in vis_c) / len(vis_c)) if vis_c else None
                    av_c = sb_select("avaliacao_qualitativa_buffett", "*", filtros={"empresa_id": eid})
                    banco_c = sb_select("bancos_dados", "*", filtros={"empresa_id": eid}) if emp_c.get("eh_banco") else []
                    historico_c = [b.get("net_income") for b in bals_c if b.get("net_income") is not None]

                    resultado_c = calcular_indice_boa_empresa(
                        emp=emp_c, ind=ind_c, preco=preco_c, vi_medio=vi_medio_c,
                        av=(av_c[0] if av_c else {}), banco_dados=(banco_c[0] if banco_c else {}),
                        historico_lucros=historico_c,
                    )
                    res_ibe = sb_upsert("indice_boa_empresa", {
                        "empresa_id": eid, "data_calculo": date.today().isoformat(),
                        "nota_valuation": resultado_c["nota_valuation"],
                        "nota_qualidade_financeira": resultado_c["nota_qualidade_financeira"],
                        "nota_qualidade_negocio": resultado_c["nota_qualidade_negocio"],
                        "nota_rating": resultado_c["nota_rating"],
                        "nota_final": resultado_c["nota_final"],
                        "classificacao": resultado_c["classificacao"],
                        "detalhes": resultado_c["detalhes"],
                    })
                    if not res_ibe:
                        erros.append(f"{row['ticker']}: calculado mas não confirmado salvo no banco")
                except Exception as e:
                    erros.append(f"{row['ticker']}: {e}")
                progresso.progress((i + 1) / total, text=f"{i+1}/{total} — {row['ticker']}")
            progresso.empty()
            if erros:
                st.warning("Algumas empresas não puderam ser calculadas/salvas (dado faltando não trava as demais):\n\n"
                           + "\n".join(f"- {e}" for e in erros))
            sucesso_count = total - len(erros)
            if sucesso_count > 0:
                st.success(f"✅ {sucesso_count} de {total} empresa(s) recalculada(s) e salva(s) com sucesso.")
            else:
                st.error("❌ Nenhuma empresa pôde ser calculada/salva.")

        linhas = []
        for _, row in df_todas.iterrows():
            eid = int(row["id"])
            ult = sb_select("indice_boa_empresa", "*", filtros={"empresa_id": eid}, ordem="data_calculo")
            if ult:
                u = ult[-1]
                linhas.append({
                    "Ticker": row["ticker"], "Empresa": row["razao_social"],
                    "Nota Final": u["nota_final"], "Classificação": u["classificacao"],
                    "Valuation/Rating": u["nota_rating"] if u["nota_rating"] is not None else u["nota_valuation"],
                    "Qualid. Financeira": u["nota_qualidade_financeira"],
                    "Qualid. Negócio": u["nota_qualidade_negocio"],
                    "Calculado em": u["data_calculo"],
                })
            else:
                linhas.append({
                    "Ticker": row["ticker"], "Empresa": row["razao_social"],
                    "Nota Final": None, "Classificação": "Não calculado",
                    "Valuation/Rating": None, "Qualid. Financeira": None, "Qualid. Negócio": None,
                    "Calculado em": None,
                })

        df_ibe = pd.DataFrame(linhas)
        df_ibe = df_ibe[df_ibe["Classificação"].isin(classes_filtro)]
        df_ibe = df_ibe.sort_values("Nota Final", ascending=False, na_position="last")
        st.dataframe(df_ibe, use_container_width=True, hide_index=True)
        st.caption("Para calcular uma empresa específica com o detalhamento completo, use a Etapa 4 do "
                   "'🧭 Fluxo de Análise (guiado)'.")

# ================================================================
elif pagina == "6. Carteira":
    st.header("Carteira de Ações")
    uid = usuario_id()
    with st.form("nova_carteira"):
        nome_c = st.text_input("Nova carteira")
        if st.form_submit_button("Criar") and nome_c:
            r = gravar_com_confirmacao(sb_insert, "carteiras", {"nome":nome_c,"usuario_id":uid},
                msg_ok=f"✅ Carteira '{nome_c}' criada com sucesso.", msg_erro="❌ Não foi possível criar a carteira.")
            if r:
                st.rerun()

    carteiras = minhas_carteiras()
    if not carteiras:
        st.info("Crie uma carteira para começar.")
    else:
        cart_df = pd.DataFrame(carteiras)
        cart_nome = st.selectbox("Carteira", cart_df["nome"])
        cart_id = int(cart_df[cart_df["nome"]==cart_nome]["id"].iloc[0])

        aba_imp,aba_res,aba_hist,aba_prov = st.tabs(["📥 Importar Excel","📊 Resultado","🔁 Histórico","💰 Proventos"])

        with aba_imp:
            st.write("Arquivo .xlsx com colunas: **CNPJ** (opcional), **Código da Ação**, **Quantidade**, **Valor Médio**.")
            arq = st.file_uploader("Arquivo Excel (.xlsx)", type=["xlsx"])
            if arq:
                df_prev = pd.read_excel(arq)
                st.dataframe(df_prev.head(20), use_container_width=True)
                if st.button("✅ Confirmar importação"):
                    import unicodedata, datetime as dt
                    def norm(c):
                        c=str(c).strip().lower()
                        c="".join(x for x in unicodedata.normalize("NFKD",c) if not unicodedata.combining(x))
                        return c.replace(" ","_")
                    df_p = df_prev.copy()
                    df_p.columns = [norm(c) for c in df_p.columns]
                    mapa = {"ticker":["codigo_da_acao","codigo_acao","ticker","codigo","acao"],
                            "qtd":["quantidade","qtde","qtd"],
                            "vm":["valor_medio","preco_medio","valormedio"],
                            "cnpj":["cnpj","cnpj_empresa"]}
                    def ac(campo):
                        for n in mapa[campo]:
                            if n in df_p.columns: return n
                        return None
                    ct,cq,cv,cc = ac("ticker"),ac("qtd"),ac("vm"),ac("cnpj")
                    if not ct or not cq or not cv:
                        st.error("Colunas não encontradas. Verifique o arquivo.")
                    else:
                        hoje = dt.date.today().isoformat()
                        imp, falhas = 0, 0
                        for _,row in df_p.iterrows():
                            tk = str(row[ct]).strip().upper()
                            if not tk or tk=="NAN": continue
                            emps = sb_select("empresas","id",filtros={"ticker":tk})
                            if emps: eid = emps[0]["id"]
                            else:
                                r = sb_insert("empresas",{"ticker":tk,"razao_social":tk})
                                eid = r[0]["id"] if r else None
                                if eid:
                                    st.warning(f"Empresa '{tk}' criada automaticamente. Complete o cadastro na Tela 1.")
                            if eid:
                                res_pos = sb_upsert("carteira_posicoes_importadas",{"carteira_id":cart_id,"empresa_id":eid,
                                    "quantidade":float(row[cq]),"valor_medio":float(row[cv]),
                                    "data_importacao":hoje,"arquivo_origem":arq.name})
                                if res_pos:
                                    imp+=1
                                else:
                                    falhas+=1
                            else:
                                falhas+=1
                        if imp > 0:
                            st.success(f"✅ {imp} posição(ões) importada(s) com sucesso.")
                        if falhas > 0:
                            st.error(f"❌ {falhas} posição(ões) não puderam ser importadas.")
                        if imp > 0:
                            st.rerun()

        with aba_res:
            ano = pd.Timestamp.now().year
            posicoes = sb_select("carteira_posicoes_importadas","empresa_id",filtros={"carteira_id":cart_id})
            movs_emp = sb_select("movimentos_carteira","empresa_id",filtros={"carteira_id":cart_id})
            eids = list(set([p["empresa_id"] for p in posicoes] + [m["empresa_id"] for m in movs_emp]))
            if not eids:
                st.info("Nenhuma ação na carteira. Importe um Excel ou registre operações.")
            else:
                st.subheader("Atualizar preço atual")
                with st.expander("✏️ Atualizar preço atual das ações"):
                    emps_c = sb_select("empresas","id,ticker")
                    emps_map = {e["id"]:e["ticker"] for e in emps_c if e["id"] in eids}

                    if st.button("🔄 Buscar cotações automáticas agora (todas)"):
                        ok_count, falha_count = 0, 0
                        with st.spinner("Buscando cotações no Yahoo Finance..."):
                            for eid, tk in emps_map.items():
                                preco, agora = buscar_cotacao_tempo_real(tk)
                                if preco > 0:
                                    res = sb_upsert("cotacao_atual_manual", {
                                        "carteira_id": cart_id, "empresa_id": eid,
                                        "preco_atual": preco, "data_atualizacao": agora,
                                    })
                                    ok_count += 1 if res else 0
                                    falha_count += 0 if res else 1
                                else:
                                    falha_count += 1
                        if ok_count > 0:
                            st.success(f"✅ {ok_count} cotação(ões) atualizada(s) com sucesso "
                                       f"({pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')}).")
                        if falha_count > 0:
                            st.warning(f"⚠️ {falha_count} ticker(s) não retornaram cotação (verifique se o "
                                       "código está correto ou tente novamente em alguns minutos).")
                        if ok_count > 0:
                            st.rerun()

                    st.caption("Ou ajuste manualmente uma ação específica:")
                    cols = st.columns(4)
                    for i,(eid,tk) in enumerate(emps_map.items()):
                        atual_r = sb_select("cotacao_atual_manual","preco_atual,data_atualizacao",filtros={"carteira_id":cart_id,"empresa_id":eid})
                        v0 = float(atual_r[0]["preco_atual"]) if atual_r else 0.0
                        label = tk
                        if atual_r and atual_r[0].get("data_atualizacao"):
                            try:
                                dt_fmt = pd.Timestamp(atual_r[0]["data_atualizacao"]).strftime("%d/%m %H:%M")
                                label = f"{tk} (atualizado {dt_fmt})"
                            except Exception:
                                pass
                        novo = cols[i%4].number_input(label,value=v0,key=f"p_{eid}")
                        if novo>0 and novo != v0:
                            r_cot = gravar_com_confirmacao(sb_upsert, "cotacao_atual_manual",
                                {"carteira_id":cart_id,"empresa_id":eid,"preco_atual":novo,
                                 "data_atualizacao":pd.Timestamp.now().isoformat()},
                                msg_ok=f"✅ Preço de {tk} atualizado manualmente.",
                                msg_erro=f"❌ Não foi possível salvar o preço de {tk}.")
                linhas = []
                for eid in eids:
                    tk_r = sb_select("empresas","ticker,razao_social",filtros={"id":eid})
                    if not tk_r: continue
                    tk,rz = tk_r[0]["ticker"],tk_r[0]["razao_social"]
                    pr = sb_select("cotacao_atual_manual","preco_atual",filtros={"carteira_id":cart_id,"empresa_id":eid})
                    preco_a = float(pr[0]["preco_atual"]) if pr else 0
                    mov_r = sb_select("movimentos_carteira","tipo,data,quantidade,preco_unitario,taxas",filtros={"carteira_id":cart_id,"empresa_id":eid},ordem="data")
                    pos_r = sb_select("carteira_posicoes_importadas","quantidade,valor_medio,data_importacao",filtros={"carteira_id":cart_id,"empresa_id":eid},ordem="data_importacao")
                    movs_l = mov_r if mov_r else ([{"tipo":"compra","data":pos_r[-1]["data_importacao"],"quantidade":pos_r[-1]["quantidade"],"preco_unitario":pos_r[-1]["valor_medio"],"taxas":0}] if pos_r else [])
                    prov_r = sb_select("proventos_recebidos","data,valor",filtros={"carteira_id":cart_id,"empresa_id":eid})
                    prov_ano = sum(p["valor"] for p in prov_r if str(p["data"])[:4]==str(ano))
                    prov_ant = sum(p["valor"] for p in prov_r if str(p["data"])[:4]!=str(ano))
                    apur = calc.apurar_carteira(movs_l, preco_a) if movs_l else {"quantidade_atual":0,"preco_medio":0,"custo_total_posicao":0,"valor_mercado_atual":0,"lucro_prejuizo_nao_realizado":0,"lucro_prejuizo_realizado":0}
                    ti = apur["custo_total_posicao"]
                    ta = apur["valor_mercado_atual"] + prov_ano + prov_ant
                    res = ta - ti
                    ev = round(res/ti*100,2) if ti else None
                    dy = round(prov_ano/apur["valor_mercado_atual"]*100,2) if apur["valor_mercado_atual"] else None
                    linhas.append({"Ação":tk,"Preço Atual":preco_a,"Prov.Ant.":prov_ant,f"Prov.{ano}":prov_ano,"Qtd":apur["quantidade_atual"],"Preço Médio":round(apur["preco_medio"],2),"Total Investido":ti,"Total Atual":round(ta,2),"Resultado (R$)":round(res,2),"Evolução %":ev,"DY %":dy})
                if linhas:
                    df_r = pd.DataFrame(linhas)
                    st.dataframe(df_r, use_container_width=True)
                    t_inv = sum(l["Total Investido"] for l in linhas)
                    t_at = sum(l["Total Atual"] for l in linhas)
                    r_at = t_at - t_inv
                    ev_total = round(r_at/t_inv*100,2) if t_inv else None
                    c1,c2,c3,c4 = st.columns(4)
                    c1.metric("Total Investido",f"R$ {t_inv:,.2f}")
                    c2.metric("Total Atual",f"R$ {t_at:,.2f}")
                    c3.metric("Resultado",f"R$ {r_at:,.2f}")
                    c4.metric("Evolução",f"{ev_total:.2f}%" if ev_total else "—")
                    st.markdown("---")
                    st.subheader("🧭 Analisar uma ação da carteira")
                    tk_an = st.selectbox("Ação",[l["Ação"] for l in linhas],key="cart_anal")
                    if st.button(f"Iniciar Fluxo de Análise guiado para {tk_an}", type="primary"):
                        eid_an = sb_select("empresas","id",filtros={"ticker":tk_an})
                        if eid_an: iniciar_fluxo_analise(eid_an[0]["id"])

        with aba_hist:
            empresa = selecionar_empresa("Ação",key="hist_emp")
            if empresa is not None:
                with st.form("form_mov"):
                    c1,c2,c3,c4 = st.columns(4)
                    tipo = c1.selectbox("Tipo",["compra","venda"])
                    data_m = c2.text_input("Data",str(date.today()))
                    qtd = c3.number_input("Quantidade",value=100.0)
                    preco_u = c4.number_input("Preço unitário",value=10.0)
                    taxas = st.number_input("Taxas",value=0.0)
                    tot = qtd*preco_u + (taxas if tipo=="compra" else -taxas)
                    st.write(f"**Total da operação: R$ {tot:,.2f}**")
                    if st.form_submit_button("Registrar operação"):
                        r = gravar_com_confirmacao(sb_insert, "movimentos_carteira",
                            {"carteira_id":cart_id,"empresa_id":int(empresa["id"]),"tipo":tipo,"data":data_m,
                             "quantidade":qtd,"preco_unitario":preco_u,"taxas":taxas,"total_operacao":tot,"origem":"manual"},
                            msg_ok="✅ Operação registrada com sucesso.", msg_erro="❌ Não foi possível registrar a operação.")
                        if r:
                            st.rerun()
                movs = sb_select("movimentos_carteira","tipo,data,quantidade,preco_unitario,taxas,total_operacao",filtros={"carteira_id":cart_id,"empresa_id":int(empresa["id"])},ordem="data")
                st.dataframe(pd.DataFrame(movs), use_container_width=True)

        with aba_prov:
            empresa_p = selecionar_empresa("Ação do provento",key="prov_emp")
            if empresa_p is not None:
                with st.form("form_prov"):
                    c1,c2,c3 = st.columns(3)
                    dp = c1.text_input("Data",str(date.today()))
                    tp = c2.selectbox("Tipo",["dividendo","jcp"])
                    vp = c3.number_input("Valor",value=0.0)
                    obs = st.text_input("Observação")
                    if st.form_submit_button("Registrar") and dp and vp:
                        r = gravar_com_confirmacao(sb_insert, "proventos_recebidos",
                            {"carteira_id":cart_id,"empresa_id":int(empresa_p["id"]),"data":dp,"tipo":tp,"valor":vp,"observacao":obs},
                            msg_ok="✅ Provento registrado com sucesso.", msg_erro="❌ Não foi possível registrar o provento.")
                        if r:
                            st.rerun()
                provs = sb_select("proventos_recebidos","data,tipo,valor,observacao",filtros={"carteira_id":cart_id,"empresa_id":int(empresa_p["id"])},ordem="data")
                st.dataframe(pd.DataFrame(provs), use_container_width=True)

# ================================================================
elif pagina == "11. Administração de Usuários":
    if not sou_admin():
        st.error("Acesso restrito a administradores.")
    else:
        st.header("Administração de Usuários")
        perfis = sb_select("perfis","id,codigo,nome,email,cpf,telefone,tipo,criado_em",ordem="nome")
        st.dataframe(pd.DataFrame(perfis), use_container_width=True)
        st.subheader("Alterar tipo de acesso")
        if perfis:
            emails = [p["email"] for p in perfis]
            email_alvo = st.selectbox("Usuário", emails)
            novo_tipo = st.selectbox("Novo tipo", ["usuario","administrador"])
            if st.button("💾 Salvar alteração"):
                uid_alvo = next(p["id"] for p in perfis if p["email"]==email_alvo)
                r = gravar_com_confirmacao(sb_update, "perfis", {"tipo":novo_tipo}, {"id":uid_alvo},
                    msg_ok=f"✅ Tipo de acesso de {email_alvo} alterado para {novo_tipo}.",
                    msg_erro="❌ Não foi possível alterar o tipo de acesso.")
                if r:
                    st.rerun()
        st.subheader("Atualizar dados do perfil de um usuário")
        if perfis:
            email_p = st.selectbox("Usuário (perfil)", emails, key="upd_perfil")
            p_sel = next(p for p in perfis if p["email"]==email_p)
            with st.form("form_upd_perfil"):
                cod = st.text_input("Código", p_sel.get("codigo","") or "")
                cpf = st.text_input("CPF", p_sel.get("cpf","") or "")
                nome = st.text_input("Nome", p_sel.get("nome","") or "")
                tel = st.text_input("Telefone", p_sel.get("telefone","") or "")
                if st.form_submit_button("Salvar"):
                    r = gravar_com_confirmacao(sb_update, "perfis",
                        {"codigo":cod,"cpf":cpf,"nome":nome,"telefone":tel}, {"id":p_sel["id"]},
                        msg_ok="✅ Perfil atualizado com sucesso.", msg_erro="❌ Não foi possível atualizar o perfil.")
                    if r:
                        st.rerun()

# ================================================================
elif pagina == "7. Relatório da Ação":
    st.header("📄 Relatório da Ação")
    st.caption("Consulta o que já foi levantado sobre uma empresa (balanço, indicadores, valor "
               "intrínseco, avaliação qualitativa e Índice de Boa Empresa). Para atualizar os dados, "
               "use o '🧭 Fluxo de Análise (guiado)'.")

    empresa_rel = selecionar_empresa("Escolha a ação para ver o relatório", key="relatorio_empresa_sel")
    if empresa_rel is None:
        st.info("Cadastre uma empresa em '1. Empresas e Setores' para poder ver um relatório.")
    else:
        emp_id_rel = int(empresa_rel["id"])
        emp_rel = sb_select("empresas", "*", filtros={"id": emp_id_rel})[0]

        st.subheader(f"{emp_rel['ticker']} — {emp_rel['razao_social']}")
        i1, i2, i3, i4 = st.columns(4)
        i1.metric("Setor", emp_rel.get("setor_id") and next(
            (s["nome"] for s in sb_select("setores","id,nome") if s["id"]==emp_rel["setor_id"]), "—") or "—")
        i2.metric("Rating", emp_rel.get("rating") or "—")
        i3.metric("Situação", emp_rel.get("situacao_codigo") or "—")
        i4.metric("Segmento", emp_rel.get("segmento") or "—")
        if emp_rel.get("descricao_negocio"):
            with st.expander("Descrição do negócio"):
                st.write(emp_rel["descricao_negocio"])

        st.markdown("---")
        bals_rel = sb_select("balancos_dre", "*", filtros={"empresa_id": emp_id_rel}, ordem="data_referencia")
        if not bals_rel:
            st.warning("Sem balanço lançado ainda para esta empresa. Use o Fluxo de Análise guiado, Etapa 1.")
        else:
            bal_rel = bals_rel[-1]
            st.subheader(f"📊 Balanço / DRE (referência: {bal_rel['data_referencia']}, fonte: {bal_rel.get('fonte','—')})")
            r1,r2,r3,r4 = st.columns(4)
            r1.metric("Ativo Total", f"R$ {bal_rel.get('total_assets',0):,.0f}" if bal_rel.get("total_assets") else "—")
            r2.metric("Patrimônio Líq.", f"R$ {bal_rel.get('total_equity',0):,.0f}" if bal_rel.get("total_equity") else "—")
            r3.metric("Dívida Líquida", f"R$ {bal_rel.get('net_debt',0):,.0f}" if bal_rel.get("net_debt") is not None else "—")
            r4.metric("Preço de mercado", f"R$ {bal_rel.get('preco_mercado_referencia',0):,.2f}" if bal_rel.get("preco_mercado_referencia") else "—")
            r5,r6,r7 = st.columns(3)
            r5.metric("Receita (12m)", f"R$ {bal_rel.get('total_revenue',0):,.0f}" if bal_rel.get("total_revenue") else "—")
            r6.metric("EBIT (12m)", f"R$ {bal_rel.get('ebit',0):,.0f}" if bal_rel.get("ebit") else "—")
            r7.metric("Lucro Líquido (12m)", f"R$ {bal_rel.get('net_income',0):,.0f}" if bal_rel.get("net_income") else "—")

            st.markdown("---")
            st.subheader("📈 Indicadores fundamentalistas")
            inds_calc_rel = sb_select("indicadores_calculados","*",filtros={"empresa_id":emp_id_rel})
            if inds_calc_rel:
                inds_def_rel = sb_select("indicadores_definicao","id,nome")
                df_ic_rel = pd.DataFrame(inds_calc_rel)
                df_ic_rel["indicador"] = df_ic_rel["indicador_id"].apply(
                    lambda iid: next((i["nome"] for i in inds_def_rel if i["id"]==iid), f"#{iid}"))
                cols_show_rel = [c for c in ["indicador","valor","data_referencia","fonte"] if c in df_ic_rel.columns]
                st.dataframe(df_ic_rel[cols_show_rel], use_container_width=True, hide_index=True)
            else:
                st.caption("Nenhum indicador calculado ainda — use a Etapa 2 do Fluxo Guiado.")

            st.markdown("---")
            st.subheader("💰 Valor Intrínseco")
            vis_rel = sb_select("valor_intrinseco","metodo,valor",filtros={"empresa_id":emp_id_rel,"data_referencia":bal_rel["data_referencia"]})
            if vis_rel:
                st.dataframe(pd.DataFrame(vis_rel), use_container_width=True, hide_index=True)
                vi_medio_rel = sum(v["valor"] for v in vis_rel)/len(vis_rel)
                preco_rel = bal_rel.get("preco_mercado_referencia")
                if preco_rel:
                    margem_rel = calc.margem_seguranca(vi_medio_rel, preco_rel)
                    classe_rel = calc.classificar(margem_rel)
                    cor_rel = "green" if classe_rel=="Comprar" else ("orange" if classe_rel=="Observar" else "red")
                    st.markdown(f"**VI médio: R$ {vi_medio_rel:.2f} | Margem: {margem_rel:.1f}% | :{cor_rel}[{classe_rel}]**")
            else:
                st.caption("Valor intrínseco ainda não calculado — use a Etapa 2 do Fluxo Guiado.")

        st.markdown("---")
        st.subheader("🧠 Avaliação Qualitativa (Buffett)")
        av_rel = sb_select("avaliacao_qualitativa_buffett","*",filtros={"empresa_id":emp_id_rel})
        if av_rel:
            a_rel = av_rel[0]
            av1,av2,av3,av4 = st.columns(4)
            av1.metric("Moat", a_rel.get("moat") or "—")
            av2.metric("Qualidade gestão", a_rel.get("qualidade_gestao") or "—")
            av3.metric("Previsibilidade", a_rel.get("previsibilidade") or "—")
            av4.metric("Círculo de competência", "Sim" if a_rel.get("circulo_competencia") else "Não")
            if a_rel.get("moat_justificativa"):
                st.caption(f"Justificativa do moat: {a_rel['moat_justificativa']}")
        else:
            st.caption("Avaliação qualitativa ainda não feita — use a Etapa 3 do Fluxo Guiado.")

        st.markdown("---")
        st.subheader("⭐ Índice de Boa Empresa")
        renderizar_diagnostico_boa_empresa(emp_id_rel, emp_rel)

        st.markdown("---")
        st.subheader("📈 Histórico de Lucros")
        hist_rel = sb_select("historico_resultados","*",filtros={"empresa_id":emp_id_rel},ordem="ano")
        if hist_rel:
            st.dataframe(pd.DataFrame(hist_rel)[["ano","lucro_liquido","teve_prejuizo"]], use_container_width=True, hide_index=True)
        else:
            st.caption("Sem histórico de lucro cadastrado (pode adicionar na tela '1. Empresas e Setores').")

        st.markdown("---")
        if st.button("🧭 Ir para o Fluxo de Análise guiado desta ação", type="primary"):
            iniciar_fluxo_analise(emp_id_rel)

elif pagina == "8. Informações Relevantes":
    st.header("📰 Informações Relevantes do Mercado")
    st.caption("Painel diário do que pode afetar a bolsa, o Brasil e o mundo — Ibovespa, câmbio, índices "
               "internacionais e as principais notícias de mercado/economia. Isso é diferente das "
               "'Notícias Relevantes' de uma empresa específica (que ficam dentro da tela de Empresas).")

    st.subheader("📊 Cotações do dia")
    with st.spinner("Buscando cotações..."):
        ibov_preco, ibov_hora = buscar_cotacao_tempo_real("IBOV")
        dolar_preco, dolar_hora = buscar_cotacao_tempo_real("USDBRL=X")
        sp500_preco, sp500_hora = buscar_cotacao_tempo_real("SP500")
    q1, q2, q3 = st.columns(3)
    q1.metric("Ibovespa", f"{ibov_preco:,.0f} pts" if ibov_preco else "—")
    q2.metric("Dólar (USD/BRL)", f"R$ {dolar_preco:,.2f}" if dolar_preco else "—")
    q3.metric("S&P 500", f"{sp500_preco:,.0f} pts" if sp500_preco else "—")
    st.caption(f"Atualizado em {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')} "
               "(~15 min de atraso, padrão do Yahoo Finance).")

    st.markdown("---")
    st.subheader("🗞️ Últimas notícias de mercado, economia e mundo")
    if st.button("🔄 Atualizar notícias"):
        st.session_state.pop("noticias_mercado_cache", None)

    if "noticias_mercado_cache" not in st.session_state:
        with st.spinner("Buscando notícias..."):
            st.session_state["noticias_mercado_cache"] = buscar_noticias_mercado()

    noticias = st.session_state["noticias_mercado_cache"]
    if not noticias:
        st.warning("Não consegui buscar notícias agora (fontes fora do ar ou mudaram de formato). "
                   "Tente 'Atualizar notícias' novamente em alguns minutos.")
    else:
        fontes_disp = ["Todas"] + sorted(set(n["fonte"] for n in noticias))
        fonte_sel = st.selectbox("Filtrar por fonte", fontes_disp)
        for n in noticias:
            if fonte_sel != "Todas" and n["fonte"] != fonte_sel:
                continue
            data_fmt = n["data_dt"].strftime("%d/%m %H:%M") if n["data_dt"] else n["data_str"]
            st.markdown(f"**[{n['titulo']}]({n['link']})**")
            st.caption(f"{n['fonte']} — {data_fmt}")
        st.caption("Fontes: InfoMoney (Mercados, Economia, Mundo) e G1 Economia — feeds públicos e gratuitos.")

elif pagina == "9. Índices Macroeconômicos":
    st.header("Índices Macroeconômicos")
    st.caption("IPCA, CDI, IGP-M, Selic e Ibovespa — série histórica completa e valores mensais. "
               "Usados como referência no Graham complexo, WACC do FCD e comparativo de rentabilidade da carteira.")

    INDICES_LISTA = ["CDI", "Selic", "IPCA", "IGP-M", "Ibovespa"]

    aba_imp_i, aba_man_i, aba_hist_i = st.tabs([
        "📥 Importar série histórica (Excel)", "✏️ Cadastrar valor mensal", "📊 Histórico"])

    with aba_imp_i:
        st.write("Use o **template padronizado** (baixe abaixo) para montar a série histórica de qualquer índice.")
        st.caption("Layout: **Ano | Mês | No mês | Em 3 meses | Em 6 meses | No Ano | Em 12 meses**. "
                   "O nome do índice fica na célula A1 da planilha. Campos opcionais podem ficar em branco.")

        indicador_imp = st.selectbox("Qual índice você está importando?", INDICES_LISTA, key="imp_idx_nome")
        arq_i = st.file_uploader("Selecione o arquivo Excel (.xlsx)", type=["xlsx"], key="idx_up")

        if arq_i:
            # lê a partir da linha 2 (cabeçalho) — linha 1 é o nome do índice
            df_raw = pd.read_excel(arq_i, header=None)
            # linha 0 = nome do índice, linha 1 = cabeçalho, linha 2+ = dados
            cabecalho_row = 1
            df_i = pd.read_excel(arq_i, header=cabecalho_row)
            # remove linhas de instrução (aviso em laranja) se existir
            df_i = df_i.dropna(subset=[df_i.columns[0]])
            df_i = df_i[pd.to_numeric(df_i.iloc[:,0], errors="coerce").notna()]
            st.write(f"Pré-visualização ({len(df_i)} registros):")
            st.dataframe(df_i.head(10), use_container_width=True)

            if st.button("✅ Confirmar importação"):
                # processar com a nova função
                import calendar as cal_mod
                import unicodedata

                def norm(c):
                    c = str(c).strip().lower()
                    c = "".join(x for x in unicodedata.normalize("NFKD",c) if not unicodedata.combining(x))
                    return c.replace(" ","_")

                df_proc = df_i.copy()
                df_proc.columns = [norm(c) for c in df_proc.columns]
                cols = list(df_proc.columns)

                col_no_mes = next((c for c in cols if "no_mes" in c), None)
                col_3m = next((c for c in cols if "3" in c and "mes" in c), None)
                col_6m = next((c for c in cols if "6" in c and "mes" in c), None)
                col_no_ano = next((c for c in cols if "no_ano" in c), None)
                col_12m = next((c for c in cols if "12" in c), None)

                registros = []
                avisos_imp = []
                importadas = 0
                for _, row in df_proc.iterrows():
                    try:
                        ano, mes = int(row["ano"]), int(row["mes"])
                    except Exception:
                        continue
                    ultimo_dia = cal_mod.monthrange(ano, mes)[1]
                    data_str = f"{ano:04d}-{mes:02d}-{ultimo_dia:02d}"

                    def safe(col):
                        if col is None: return None
                        v = row.get(col)
                        if v is None or str(v).strip() in ("","nan","None"): return None
                        try: return float(v)
                        except: return None

                    no_mes_v = safe(col_no_mes)
                    if no_mes_v is None:
                        continue

                    reg = {"indice": indicador_imp, "data_referencia": data_str,
                           "valor": no_mes_v, "no_mes": no_mes_v, "fonte": arq_i.name}
                    if col_3m: reg["em_3_meses"] = safe(col_3m)
                    if col_6m: reg["em_6_meses"] = safe(col_6m)
                    if col_no_ano: reg["no_ano"] = safe(col_no_ano)
                    if col_12m: reg["em_12_meses"] = safe(col_12m)
                    reg = {k:v for k,v in reg.items() if v is not None}
                    registros.append(reg)
                    importadas += 1

                if registros:
                    sb = get_supabase()
                    sb.table("indices_macroeconomicos").upsert(registros).execute()
                    st.success(f"✅ {importadas} registro(s) de {indicador_imp} importado(s) com sucesso!")
                    for a in avisos_imp:
                        st.warning(a)
                    st.rerun()
                else:
                    st.error("Nenhum registro válido encontrado. Verifique o formato do arquivo.")

    with aba_man_i:
        st.caption("Para atualizar o valor do mês atual sem precisar de uma planilha.")
        with st.form("form_idx"):
            c1, c2 = st.columns(2)
            ind_n = c1.selectbox("Índice", INDICES_LISTA)
            ano_m = c1.number_input("Ano", value=2026, step=1)
            mes_m = c2.selectbox("Mês", list(range(1,13)))
            no_mes_m = c2.number_input("No mês (%)", value=0.0, step=0.01)
            c3, c4 = st.columns(2)
            no_ano_m = c3.number_input("No Ano (acumulado, opcional)", value=0.0)
            em_12m_m = c4.number_input("Em 12 meses (opcional)", value=0.0)
            fonte_m = st.text_input("Fonte", "Banco Central do Brasil / B3")
            if st.form_submit_button("💾 Salvar") and ano_m and mes_m:
                import calendar as cal_m
                ult = cal_m.monthrange(int(ano_m), int(mes_m))[1]
                data_m = f"{int(ano_m):04d}-{int(mes_m):02d}-{ult:02d}"
                reg = {"indice": ind_n, "data_referencia": data_m,
                       "valor": no_mes_m, "no_mes": no_mes_m, "fonte": fonte_m}
                if no_ano_m: reg["no_ano"] = no_ano_m
                if em_12m_m: reg["em_12_meses"] = em_12m_m
                r = gravar_com_confirmacao(sb_upsert, "indices_macroeconomicos", reg,
                    msg_ok=f"✅ {ind_n} {int(ano_m)}/{int(mes_m):02d} salvo com sucesso.",
                    msg_erro="❌ Não foi possível salvar o índice.")
                if r:
                    st.rerun()

    with aba_hist_i:
        filtro_i = st.selectbox("Filtrar por índice", ["Todos"] + INDICES_LISTA)
        hist_i = sb_select("indices_macroeconomicos",
                            "indice,data_referencia,no_mes,em_3_meses,em_6_meses,no_ano,em_12_meses,fonte",
                            filtros={"indice": filtro_i} if filtro_i != "Todos" else None,
                            ordem="data_referencia")
        df_hist = pd.DataFrame(hist_i) if hist_i else pd.DataFrame()
        if not df_hist.empty:
            df_hist.columns = ["Índice","Data","No mês","Em 3 meses","Em 6 meses","No Ano","Em 12 meses","Fonte"]
            st.dataframe(df_hist, use_container_width=True)
            st.caption(f"Total: {len(df_hist)} registros.")
        else:
            st.info("Nenhum registro. Importe a série histórica ou cadastre valores na aba ao lado.")


# ================================================================
elif pagina == "10. Tabelas de Apoio":
    st.header("Tabelas de Apoio")
    st.subheader("Setores")
    df_set_apoio = pd.DataFrame(sb_select("setores","id,nome",ordem="nome"))
    if not df_set_apoio.empty:
        st.dataframe(df_set_apoio, use_container_width=True, hide_index=True)
    with st.form("form_setor_apoio"):
        ns_apoio = st.text_input("Novo setor")
        if st.form_submit_button("➕ Adicionar"):
            if not ns_apoio.strip():
                st.error("❌ Digite o nome do setor.")
            else:
                r = gravar_com_confirmacao(sb_insert, "setores", {"nome":ns_apoio.strip()},
                    msg_ok=f"✅ Setor '{ns_apoio.strip()}' adicionado com sucesso.",
                    msg_erro="❌ Não foi possível adicionar o setor.")
                if r:
                    st.rerun()
    st.markdown("---")
    st.subheader("Tipo de Mercado (Segmento de listagem B3)")
    st.dataframe(pd.DataFrame(sb_select("tipo_mercado")), use_container_width=True)
    st.subheader("Situação da Empresa")
    st.dataframe(pd.DataFrame(sb_select("situacao_empresa")), use_container_width=True)
    st.subheader("Tipos de Ativo")
    st.dataframe(pd.DataFrame(sb_select("tipos_ativo","id,nome,descricao",ordem="nome")), use_container_width=True)
    st.subheader("Indicadores")
    st.dataframe(pd.DataFrame(sb_select("indicadores_definicao","codigo,nome,categoria,tipo_calculo,grandeza,valor_referencia,formula",ordem="categoria")), use_container_width=True)
    st.markdown("---")
    st.subheader("➕ Cadastrar novo indicador")
    with st.form("form_ind_new"):
        c1,c2,c3 = st.columns(3)
        cod_i = c1.text_input("Código")
        nom_i = c2.text_input("Nome")
        cat_i = c3.selectbox("Categoria",["valuation","rentabilidade","endividamento","crescimento","liquidez","geracao_caixa","previsibilidade","eficiencia","patrimonial","qualitativo"])
        form_i = st.text_input("Fórmula")
        c4,c5 = st.columns(2)
        gr_i = c4.selectbox("Grandeza",["menor_que","maior_que","igual","intervalo"])
        vr_i = c5.text_input("Valor de referência")
        fi_i = st.text_input("Descrição faixa ideal")
        tc_i = st.selectbox("Tipo cálculo",["fundamentalista_atual","fundamentalista_historico","qualitativo","pendente_implementacao"],index=3)
        if st.form_submit_button("Cadastrar") and cod_i and nom_i:
            r = gravar_com_confirmacao(sb_upsert, "indicadores_definicao",
                {"codigo":cod_i.upper(),"nome":nom_i,"categoria":cat_i,"formula":form_i,
                 "faixa_ideal":fi_i,"tipo_calculo":tc_i,"grandeza":gr_i,"valor_referencia":vr_i},
                msg_ok=f"✅ Indicador '{nom_i}' cadastrado com sucesso.", msg_erro="❌ Não foi possível cadastrar o indicador.")
            if r:
                st.rerun()

else:
    # Para telas não implementadas neste arquivo ainda, mostrar aviso informativo
    st.info(f"Tela '{pagina}' — em implementação. Use as telas já disponíveis.")
