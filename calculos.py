"""
calculos.py
Funções de cálculo: indicadores fundamentalistas, valor intrínseco (Graham e DCF),
índice de qualidade ponderado e apuração de carteira (preço médio / lucro-prejuízo).

Tudo em Python puro, sem dependências externas além do sqlite3 já embutido.
"""
import json
import sqlite3
from datetime import datetime

# ---------- Indicadores fundamentalistas ----------

def calcular_indicadores(bal: dict) -> dict:
    """Recebe um dict com os campos de balancos_dre e devolve os indicadores calculados.
    `bal` deve conter também 'preco_mercado_referencia' e pode receber 'lucro_ano_anterior',
    'lucro_dois_anos_atras', 'receita_ano_anterior' via dict opcional para crescimento."""

    preco = bal.get("preco_mercado_referencia")
    share = bal.get("share_issued")
    net_income = bal.get("net_income")
    equity = bal.get("total_equity")
    assets = bal.get("total_assets")
    revenue = bal.get("total_revenue")
    gross_profit = bal.get("gross_profit")
    op_income = bal.get("operating_income")
    ebit = bal.get("ebit")
    ebitda = bal.get("ebitda")
    total_debt = bal.get("total_debt")
    net_debt = bal.get("net_debt")
    working_capital = bal.get("working_capital")
    capex = bal.get("capex")
    dep_amort = bal.get("depreciacao_amortizacao")

    ind = {}

    lpa = (net_income / share) if (net_income is not None and share) else None
    vpa = (equity / share) if (equity is not None and share) else None
    ind["LPA"] = lpa
    ind["VPA"] = vpa

    ind["P/L"] = (preco / lpa) if (preco and lpa) else None
    ind["P/VP"] = (preco / vpa) if (preco and vpa) else None
    ind["Margem Líquida"] = (net_income / revenue * 100) if (net_income is not None and revenue) else None
    ind["Margem Bruta"] = (gross_profit / revenue * 100) if (gross_profit is not None and revenue) else None
    ind["Margem Operacional"] = (op_income / revenue * 100) if (op_income is not None and revenue) else None
    ind["ROE"] = (net_income / equity * 100) if (net_income is not None and equity) else None
    ind["ROA"] = (net_income / assets * 100) if (net_income is not None and assets) else None
    ind["Dívida Líquida/EBITDA"] = (net_debt / ebitda) if (net_debt is not None and ebitda) else None
    ind["P/EBITDA"] = (preco * share / ebitda) if (preco and share and ebitda) else None
    ev = (preco * share + (net_debt or 0)) if (preco and share) else None
    ind["EV/EBITDA"] = (ev / ebitda) if (ev and ebitda) else None
    ind["PSR"] = (preco * share / revenue) if (preco and share and revenue) else None

    # FCF (Fluxo de Caixa Livre) - aproximação Buffett: EBIT*(1-IR) + Depreciação - CAPEX - ΔCapGiro
    taxa_imposto = bal.get("taxa_imposto", 0.25)
    delta_cap_giro = bal.get("delta_capital_giro", 0)
    if ebit is not None:
        fcf = ebit * (1 - taxa_imposto) + (dep_amort or 0) - (capex or 0) - delta_cap_giro
        ind["FCF"] = fcf
    else:
        ind["FCF"] = None

    return ind


def calcular_crescimento(lucro_atual, lucro_anterior):
    if lucro_atual is None or lucro_anterior in (None, 0):
        return None
    return (lucro_atual / lucro_anterior - 1) * 100


def cagr(valor_final, valor_inicial, anos):
    if not valor_final or not valor_inicial or valor_inicial <= 0 or anos <= 0:
        return None
    return ((valor_final / valor_inicial) ** (1 / anos) - 1) * 100


# ---------- Valor intrínseco ----------

def graham_simplificado(lpa, multiplo_sem_crescimento=8.5, g=0):
    """V = LPA x (8,5 + 2g)  -- g em % (ex.: 6 para 6%)"""
    if lpa is None:
        return None
    return lpa * (multiplo_sem_crescimento + 2 * g)


def graham_numero(lpa, vpa):
    if lpa is None or vpa is None or lpa <= 0 or vpa <= 0:
        return None
    return (22.5 * lpa * vpa) ** 0.5


def graham_complexo(lpa, g, y, multiplo_sem_crescimento=8.5, fator_aaa=4.4):
    """V = [LPA x (8,5 + 2g) x 4,4] / Y   -- g e y em % """
    if lpa is None or y in (None, 0):
        return None
    return (lpa * (multiplo_sem_crescimento + 2 * g) * fator_aaa) / y


def fluxo_caixa_descontado(fcf0, g, wacc, anos=5, g_terminal=0.03, divida_liquida=0, num_acoes=None):
    """Retorna (valor_por_acao, detalhe) usando FCF ano 0, crescimento g (decimal),
    WACC (decimal), horizonte `anos`, crescimento terminal g_terminal (decimal)."""
    if fcf0 is None or num_acoes in (None, 0):
        return None, {}
    fluxos = []
    fcf = fcf0
    pv_total = 0
    for t in range(1, anos + 1):
        fcf = fcf * (1 + g)
        pv = fcf / ((1 + wacc) ** t)
        fluxos.append({"ano": t, "fcf": fcf, "vp": pv})
        pv_total += pv
    valor_terminal = fcf * (1 + g_terminal) / (wacc - g_terminal)
    vp_terminal = valor_terminal / ((1 + wacc) ** anos)
    ev = pv_total + vp_terminal
    equity_value = ev - divida_liquida
    valor_acao = equity_value / num_acoes
    detalhe = {
        "fluxos": fluxos,
        "pv_total_fcfs": pv_total,
        "valor_terminal": valor_terminal,
        "vp_terminal": vp_terminal,
        "enterprise_value": ev,
        "equity_value": equity_value,
        "valor_por_acao": valor_acao,
    }
    return valor_acao, detalhe


def margem_seguranca(valor_intrinseco, preco_mercado):
    if not valor_intrinseco or not preco_mercado:
        return None
    return (1 - preco_mercado / valor_intrinseco) * 100


def classificar(margem_pct, limite_compra=30, limite_observar=0):
    if margem_pct is None:
        return "Sem dados"
    if margem_pct >= limite_compra:
        return "Comprar"
    if margem_pct >= limite_observar:
        return "Observar"
    return "Evitar"


# ---------- Índice de qualidade ponderado ----------

def pontuar_indicador(valor, limite_ideal, regra):
    """Pontuação simples de 0 a 100. regra: 'menor_melhor' ou 'maior_melhor'."""
    if valor is None or limite_ideal is None:
        return None
    try:
        limite = float(limite_ideal)
    except (TypeError, ValueError):
        return None
    if regra == "menor_melhor":
        if valor <= 0:
            return 0
        razao = limite / valor
        return max(0, min(100, razao * 70))  # quanto menor que o limite, mais perto/acima de 70-100
    else:  # maior_melhor
        if limite <= 0:
            return 0
        razao = valor / limite
        return max(0, min(100, razao * 70))


def calcular_indice_qualidade(conn: sqlite3.Connection, empresa_id, perfil, data_referencia):
    cur = conn.cursor()
    cur.execute("""
        SELECT d.nome, c.peso, c.limite_ideal, c.regra_pontuacao, ic.valor
        FROM criterios_pesos c
        JOIN indicadores_definicao d ON d.id = c.indicador_id
        LEFT JOIN indicadores_calculados ic
          ON ic.indicador_id = c.indicador_id
         AND ic.empresa_id = ?
         AND ic.data_referencia = ?
        WHERE c.perfil = ? AND c.ativo = 1
    """, (empresa_id, data_referencia, perfil))
    rows = cur.fetchall()

    detalhe = []
    indice_final = 0.0
    peso_total = 0.0
    for nome, peso, limite_ideal, regra, valor in rows:
        nota = pontuar_indicador(valor, limite_ideal, regra)
        if nota is None:
            continue
        indice_final += nota * peso
        peso_total += peso
        detalhe.append({"indicador": nome, "valor": valor, "nota": round(nota, 1), "peso": peso})

    indice_normalizado = (indice_final / peso_total) if peso_total > 0 else None
    return indice_normalizado, detalhe


# ---------- Screening / seleção de ações por filtro ----------

def screening_acoes(conn, pl_max=None, roe_min=None, lucro_min=None, divliq_pl_max=None,
                     setor_id=None, data_referencia=None):
    """Retorna lista de empresas que atendem aos filtros informados,
    usando o balanço mais recente (ou a data_referencia indicada) de cada empresa."""
    sql = """
        SELECT e.id, e.ticker, e.razao_social, s.nome as setor,
               b.data_referencia, b.net_income, b.total_equity, b.net_debt,
               b.preco_mercado_referencia, b.share_issued
        FROM empresas e
        JOIN setores s ON s.id = e.setor_id
        JOIN balancos_dre b ON b.empresa_id = e.id
        WHERE b.id = (
            SELECT id FROM balancos_dre b2
            WHERE b2.empresa_id = e.id
              AND (? IS NULL OR b2.data_referencia = ?)
            ORDER BY b2.data_referencia DESC LIMIT 1
        )
    """
    params = [data_referencia, data_referencia]
    if setor_id:
        sql += " AND e.setor_id = ?"
        params.append(setor_id)

    rows = conn.execute(sql, params).fetchall()
    resultado = []
    for r in rows:
        r = dict(r)
        lpa = (r["net_income"] / r["share_issued"]) if r["share_issued"] else None
        vpa = (r["total_equity"] / r["share_issued"]) if r["share_issued"] else None
        pl = (r["preco_mercado_referencia"] / lpa) if (lpa and r["preco_mercado_referencia"]) else None
        roe = (r["net_income"] / r["total_equity"] * 100) if r["total_equity"] else None
        divliq_pl = (r["net_debt"] / r["total_equity"]) if r["total_equity"] else None

        if pl_max is not None and (pl is None or pl > pl_max):
            continue
        if roe_min is not None and (roe is None or roe < roe_min):
            continue
        if lucro_min is not None and (r["net_income"] is None or r["net_income"] < lucro_min):
            continue
        if divliq_pl_max is not None and (divliq_pl is None or divliq_pl > divliq_pl_max):
            continue

        resultado.append({
            "ticker": r["ticker"], "razao_social": r["razao_social"], "setor": r["setor"],
            "data_referencia": r["data_referencia"], "P/L": round(pl, 2) if pl else None,
            "ROE (%)": round(roe, 2) if roe else None,
            "Lucro Líquido": r["net_income"],
            "Dív.Líq/PL": round(divliq_pl, 2) if divliq_pl else None,
        })
    return resultado




def apurar_carteira(movimentos: list, preco_atual: float):
    """movimentos: lista de dicts {tipo, quantidade, preco_unitario, taxas, data}
    Retorna posição atual, preço médio, lucro/prejuízo realizado e não realizado."""
    qtd_atual = 0.0
    custo_total = 0.0
    lucro_realizado = 0.0

    for m in sorted(movimentos, key=lambda x: x["data"]):
        qtd = m["quantidade"]
        preco = m["preco_unitario"]
        taxas = m.get("taxas", m.get("custos", 0)) or 0
        if m["tipo"] == "compra":
            custo_total += qtd * preco + taxas
            qtd_atual += qtd
        elif m["tipo"] == "venda":
            preco_medio_atual = (custo_total / qtd_atual) if qtd_atual > 0 else 0
            lucro_realizado += (preco - preco_medio_atual) * qtd - taxas
            custo_total -= preco_medio_atual * qtd
            qtd_atual -= qtd

    preco_medio = (custo_total / qtd_atual) if qtd_atual > 0 else 0
    valor_mercado_atual = qtd_atual * (preco_atual or 0)
    lucro_nao_realizado = valor_mercado_atual - custo_total

    return {
        "quantidade_atual": qtd_atual,
        "preco_medio": round(preco_medio, 4),
        "custo_total_posicao": round(custo_total, 2),
        "valor_mercado_atual": round(valor_mercado_atual, 2),
        "lucro_prejuizo_nao_realizado": round(lucro_nao_realizado, 2),
        "lucro_prejuizo_realizado": round(lucro_realizado, 2),
    }


def resumo_posicao_empresa(conn, carteira_id, empresa_id, preco_atual, ano_atual):
    """Junta movimentos + posição importada (se houver) + proventos, devolvendo o resumo
    completo pedido: total investido, valor atual, proventos do ano e de anos anteriores."""
    movs = [dict(r) for r in conn.execute(
        """SELECT tipo, data, quantidade, preco_unitario, taxas FROM movimentos_carteira
           WHERE carteira_id=? AND empresa_id=?""", (carteira_id, empresa_id)).fetchall()]

    # posição importada do Excel também entra como uma "compra" inicial pelo valor médio informado
    importadas = conn.execute(
        """SELECT quantidade, valor_medio, data_importacao FROM carteira_posicoes_importadas
           WHERE carteira_id=? AND empresa_id=? ORDER BY data_importacao DESC LIMIT 1""",
        (carteira_id, empresa_id)).fetchone()
    if importadas and not movs:
        movs = [{"tipo": "compra", "data": importadas["data_importacao"],
                 "quantidade": importadas["quantidade"], "preco_unitario": importadas["valor_medio"],
                 "taxas": 0}]

    apuracao = apurar_carteira(movs, preco_atual) if movs else {
        "quantidade_atual": 0, "preco_medio": 0, "custo_total_posicao": 0,
        "valor_mercado_atual": 0, "lucro_prejuizo_nao_realizado": 0, "lucro_prejuizo_realizado": 0}

    proventos = conn.execute(
        """SELECT data, valor FROM proventos_recebidos WHERE carteira_id=? AND empresa_id=?""",
        (carteira_id, empresa_id)).fetchall()
    proventos_ano_atual = sum(p["valor"] for p in proventos if p["data"][:4] == str(ano_atual))
    proventos_anos_anteriores = sum(p["valor"] for p in proventos if p["data"][:4] != str(ano_atual))

    apuracao["proventos_ano_atual"] = round(proventos_ano_atual, 2)
    apuracao["proventos_anos_anteriores"] = round(proventos_anos_anteriores, 2)
    apuracao["total_investido"] = apuracao["custo_total_posicao"]
    apuracao["valor_atual"] = apuracao["valor_mercado_atual"]
    return apuracao




# ---------- Importação de carteira via Excel ----------

def pd_notna(v):
    try:
        import pandas as pd
        return pd.notna(v)
    except Exception:
        return v is not None


def importar_carteira_excel(conn, carteira_id, df, arquivo_origem="upload"):
    """df deve ter colunas (nome flexível, ver normalização): cnpj, codigo_acao/ticker,
    quantidade, valor_medio. Cria a empresa se não existir (pelo ticker), grava em
    carteira_posicoes_importadas. Retorna (qtd_importadas, avisos: list[str])."""
    import unicodedata
    import datetime as dt

    def normaliza(col):
        col = str(col).strip().lower()
        col = "".join(c for c in unicodedata.normalize("NFKD", col) if not unicodedata.combining(c))
        col = col.replace(" ", "_").replace(".", "")
        return col

    df = df.copy()
    df.columns = [normaliza(c) for c in df.columns]

    mapa_possiveis = {
        "cnpj": ["cnpj", "cnpj_empresa"],
        "ticker": ["codigo_da_acao", "codigo_acao", "ticker", "codigo", "acao"],
        "quantidade": ["quantidade", "qtde", "qtd"],
        "valor_medio": ["valor_medio", "preco_medio", "valormedio"],
    }

    def achar_coluna(campo):
        for nome in mapa_possiveis[campo]:
            if nome in df.columns:
                return nome
        return None

    col_cnpj = achar_coluna("cnpj")
    col_ticker = achar_coluna("ticker")
    col_qtd = achar_coluna("quantidade")
    col_vm = achar_coluna("valor_medio")

    avisos = []
    if not col_ticker or not col_qtd or not col_vm:
        avisos.append(f"Colunas não encontradas. Esperado algo como 'Código da Ação', 'Quantidade', "
                       f"'Valor Médio' (e opcionalmente 'CNPJ'). Colunas recebidas: {list(df.columns)}")
        return 0, avisos

    data_hoje = dt.date.today().isoformat()
    importadas = 0
    cur = conn.cursor()

    for _, row in df.iterrows():
        ticker = str(row[col_ticker]).strip().upper()
        if not ticker or ticker == "NAN":
            continue
        qtd = row[col_qtd]
        vm = row[col_vm]
        cnpj = str(row[col_cnpj]).strip() if col_cnpj and pd_notna(row[col_cnpj]) else None

        cur.execute("SELECT id FROM empresas WHERE ticker=?", (ticker,))
        emp = cur.fetchone()
        if emp:
            emp_id = emp[0]
            if cnpj:
                cur.execute("UPDATE empresas SET cnpj=? WHERE id=? AND (cnpj IS NULL OR cnpj='')",
                            (cnpj, emp_id))
        else:
            cur.execute("INSERT INTO empresas (ticker, cnpj, razao_social) VALUES (?,?,?)",
                        (ticker, cnpj, ticker))
            emp_id = cur.lastrowid
            avisos.append(f"Empresa '{ticker}' não existia e foi criada automaticamente (sem setor/dados "
                           f"de balanço). Complete o cadastro na Tela 1.")

        cur.execute("""INSERT OR REPLACE INTO carteira_posicoes_importadas
            (carteira_id, empresa_id, quantidade, valor_medio, data_importacao, arquivo_origem)
            VALUES (?,?,?,?,?,?)""", (carteira_id, emp_id, float(qtd), float(vm), data_hoje, arquivo_origem))
        importadas += 1

    conn.commit()
    return importadas, avisos

# ---------- Relatório de Resultado da Carteira (modelo "Leitão em Ação") ----------

def relatorio_resultado_carteira(conn, carteira_id, ano_atual, precos_atuais: dict = None):
    """Replica o modelo de planilha de controle de carteira do usuário:
    Ação, Preço Atual, Proventos Anos Anteriores, Proventos deste Ano, Nº Operações,
    Qtd Total, Preço Médio, Total Investido, % Distrib. Compras, Total Atual (c/ proventos),
    % Distrib. Atual, Resultado Atual (R$), Evolução (%) = rentabilidade, Total Atual s/Proventos,
    % Distrib. s/Proventos, DY do ano (%).

    precos_atuais: dict opcional {empresa_id: preco} para sobrepor o preço vindo do balanço/cotação manual.
    """
    precos_atuais = precos_atuais or {}

    empresas_df = conn.execute("""
        SELECT DISTINCT e.id, e.ticker, e.razao_social
        FROM empresas e
        LEFT JOIN movimentos_carteira m ON m.empresa_id = e.id AND m.carteira_id = ?
        LEFT JOIN carteira_posicoes_importadas p ON p.empresa_id = e.id AND p.carteira_id = ?
        WHERE m.id IS NOT NULL OR p.id IS NOT NULL
    """, (carteira_id, carteira_id)).fetchall()

    linhas = []
    for e in empresas_df:
        empresa_id = e["id"]

        # preço atual: prioridade -> override manual passado por parâmetro -> cotacao_atual_manual -> balanço
        preco_atual = precos_atuais.get(empresa_id)
        if preco_atual is None:
            row_manual = conn.execute(
                "SELECT preco_atual FROM cotacao_atual_manual WHERE carteira_id=? AND empresa_id=?",
                (carteira_id, empresa_id)).fetchone()
            if row_manual:
                preco_atual = row_manual["preco_atual"]
        if preco_atual is None:
            row_bal = conn.execute(
                """SELECT preco_mercado_referencia FROM balancos_dre WHERE empresa_id=?
                   ORDER BY data_referencia DESC LIMIT 1""", (empresa_id,)).fetchone()
            preco_atual = row_bal["preco_mercado_referencia"] if row_bal else 0
        preco_atual = preco_atual or 0

        movs = [dict(r) for r in conn.execute(
            """SELECT tipo, data, quantidade, preco_unitario, taxas FROM movimentos_carteira
               WHERE carteira_id=? AND empresa_id=?""", (carteira_id, empresa_id)).fetchall()]
        num_operacoes = len(movs)

        importadas = conn.execute(
            """SELECT quantidade, valor_medio, data_importacao FROM carteira_posicoes_importadas
               WHERE carteira_id=? AND empresa_id=? ORDER BY data_importacao DESC LIMIT 1""",
            (carteira_id, empresa_id)).fetchone()
        if importadas and not movs:
            movs = [{"tipo": "compra", "data": importadas["data_importacao"],
                     "quantidade": importadas["quantidade"], "preco_unitario": importadas["valor_medio"],
                     "taxas": 0}]

        apur = apurar_carteira(movs, preco_atual) if movs else {
            "quantidade_atual": 0, "preco_medio": 0, "custo_total_posicao": 0,
            "valor_mercado_atual": 0, "lucro_prejuizo_nao_realizado": 0, "lucro_prejuizo_realizado": 0}

        proventos = conn.execute(
            "SELECT data, valor FROM proventos_recebidos WHERE carteira_id=? AND empresa_id=?",
            (carteira_id, empresa_id)).fetchall()
        prov_ano = sum(p["valor"] for p in proventos if p["data"][:4] == str(ano_atual))
        prov_anteriores = sum(p["valor"] for p in proventos if p["data"][:4] != str(ano_atual))

        qtd = apur["quantidade_atual"]
        preco_medio = apur["preco_medio"]
        total_investido = apur["custo_total_posicao"]
        total_atual_sem_proventos = qtd * preco_atual
        total_atual_com_proventos = total_atual_sem_proventos + prov_ano + prov_anteriores
        resultado_atual = total_atual_com_proventos - total_investido
        evolucao = (resultado_atual / total_investido) if total_investido else None
        dy_ano = (prov_ano / total_atual_sem_proventos) if total_atual_sem_proventos else None

        if qtd == 0 and total_investido == 0 and not proventos:
            continue  # ação sem posição nem histórico relevante

        linhas.append({
            "empresa_id": empresa_id, "ticker": e["ticker"], "razao_social": e["razao_social"],
            "preco_atual": preco_atual,
            "proventos_anos_anteriores": round(prov_anteriores, 2),
            "proventos_ano": round(prov_ano, 2),
            "num_operacoes": num_operacoes,
            "qtd_total": qtd,
            "preco_medio": preco_medio,
            "total_investido": round(total_investido, 2),
            "total_atual": round(total_atual_com_proventos, 2),
            "total_atual_sem_proventos": round(total_atual_sem_proventos, 2),
            "resultado_atual": round(resultado_atual, 2),
            "evolucao_pct": round(evolucao * 100, 2) if evolucao is not None else None,
            "dy_ano_pct": round(dy_ano * 100, 2) if dy_ano is not None else None,
        })

    soma_investido = sum(l["total_investido"] for l in linhas) or 1
    soma_atual = sum(l["total_atual"] for l in linhas) or 1
    soma_atual_sp = sum(l["total_atual_sem_proventos"] for l in linhas) or 1

    for l in linhas:
        l["distrib_compras_pct"] = round(l["total_investido"] / soma_investido * 100, 2)
        l["distrib_atual_pct"] = round(l["total_atual"] / soma_atual * 100, 2)
        l["distrib_atual_sem_proventos_pct"] = round(l["total_atual_sem_proventos"] / soma_atual_sp * 100, 2)

    totais = {
        "total_investido": round(sum(l["total_investido"] for l in linhas), 2),
        "total_atual": round(sum(l["total_atual"] for l in linhas), 2),
        "total_atual_sem_proventos": round(sum(l["total_atual_sem_proventos"] for l in linhas), 2),
        "resultado_atual": round(sum(l["resultado_atual"] for l in linhas), 2),
        "proventos_ano": round(sum(l["proventos_ano"] for l in linhas), 2),
        "proventos_anos_anteriores": round(sum(l["proventos_anos_anteriores"] for l in linhas), 2),
    }
    soma_inv = totais["total_investido"] or 1
    totais["evolucao_pct"] = round(totais["resultado_atual"] / soma_inv * 100, 2) if soma_inv else None

    return linhas, totais

# ---------- Atualização em lote de indicadores/valor intrínseco da carteira ----------

def atualizar_indicadores_carteira(conn, carteira_id, g=6.0, y=6.5, wacc=10.0):
    """Para cada empresa com posição nesta carteira, recalcula indicadores e valor
    intrínseco a partir do balanço mais recente, gravando tudo de uma vez.
    Usa premissas padrão (g, y, wacc) — quem quiser ajustar premissa por empresa
    específica continua podendo fazer isso manualmente na Tela 3 / Fluxo de Análise.
    Retorna lista de avisos (empresas sem balanço, por exemplo)."""
    avisos = []
    empresas_ids = [r[0] for r in conn.execute("""
        SELECT DISTINCT e.id FROM empresas e
        LEFT JOIN movimentos_carteira m ON m.empresa_id = e.id AND m.carteira_id = ?
        LEFT JOIN carteira_posicoes_importadas p ON p.empresa_id = e.id AND p.carteira_id = ?
        WHERE m.id IS NOT NULL OR p.id IS NOT NULL
    """, (carteira_id, carteira_id)).fetchall()]

    cur = conn.cursor()
    atualizadas = 0
    for empresa_id in empresas_ids:
        bal_row = cur.execute(
            "SELECT * FROM balancos_dre WHERE empresa_id=? ORDER BY data_referencia DESC LIMIT 1",
            (empresa_id,)).fetchone()
        ticker_row = cur.execute("SELECT ticker FROM empresas WHERE id=?", (empresa_id,)).fetchone()
        ticker = ticker_row[0] if ticker_row else f"id={empresa_id}"

        if not bal_row:
            avisos.append(f"{ticker}: sem balanço lançado — não foi possível calcular indicadores.")
            continue

        bal = dict(bal_row)
        data_ref = bal["data_referencia"]
        ind = calcular_indicadores(bal)

        for nome, valor in ind.items():
            row = cur.execute("SELECT id FROM indicadores_definicao WHERE nome=?", (nome,)).fetchone()
            if row and valor is not None:
                cur.execute("""INSERT OR REPLACE INTO indicadores_calculados
                    (empresa_id, data_referencia, indicador_id, valor) VALUES (?,?,?,?)""",
                    (empresa_id, data_ref, row[0], valor))

        lpa, vpa, fcf = ind.get("LPA"), ind.get("VPA"), ind.get("FCF")
        preco = bal.get("preco_mercado_referencia")
        share = bal.get("share_issued")
        net_debt = bal.get("net_debt") or 0

        vi_simpl = graham_simplificado(lpa, g=g)
        vi_complexo = graham_complexo(lpa, g, y)
        vi_fcd, _ = fluxo_caixa_descontado(fcf, g/100, wacc/100, anos=5, g_terminal=0.03,
                                            divida_liquida=net_debt, num_acoes=share)
        premissas = __import__("json").dumps({"g": g, "y": y, "wacc": wacc, "origem": "atualizacao_em_lote"})
        for metodo, vi in [("simplificado", vi_simpl), ("complexo", vi_complexo), ("fcd", vi_fcd)]:
            if vi:
                cur.execute("""INSERT OR REPLACE INTO valor_intrinseco
                    (empresa_id, data_referencia, metodo, valor, premissas_json)
                    VALUES (?,?,?,?,?)""", (empresa_id, data_ref, metodo, vi, premissas))

        atualizadas += 1

    conn.commit()
    return atualizadas, avisos

# ---------- Importação de série histórica de índices macroeconômicos via Excel ----------

def importar_indices_excel(conn, df, arquivo_origem="upload"):
    """df deve ter colunas: Índice (ou Indice/indicador), Data, Valor, Fonte (opcional).
    Aceita uma planilha com várias linhas (datas) por índice, ex. série histórica completa
    de Selic, CDI, IPCA, IGP-M, Ibovespa. Retorna (qtd_importadas, avisos)."""
    import unicodedata

    def normaliza(col):
        col = str(col).strip().lower()
        col = "".join(c for c in unicodedata.normalize("NFKD", col) if not unicodedata.combining(c))
        col = col.replace(" ", "_")
        return col

    df = df.copy()
    df.columns = [normaliza(c) for c in df.columns]

    mapa = {
        "indice": ["indice", "indicador", "nome_indice"],
        "data": ["data", "data_referencia", "mes", "data_mes"],
        "valor": ["valor", "valor_indice", "taxa"],
        "fonte": ["fonte", "origem"],
    }

    def achar(campo):
        for nome in mapa[campo]:
            if nome in df.columns:
                return nome
        return None

    col_indice = achar("indice")
    col_data = achar("data")
    col_valor = achar("valor")
    col_fonte = achar("fonte")

    avisos = []
    if not col_indice or not col_data or not col_valor:
        avisos.append(f"Colunas não encontradas. Esperado algo como 'Índice', 'Data', 'Valor' (e "
                       f"opcionalmente 'Fonte'). Colunas recebidas: {list(df.columns)}")
        return 0, avisos

    importadas = 0
    cur = conn.cursor()
    for _, row in df.iterrows():
        indice = str(row[col_indice]).strip()
        if not indice or indice.lower() == "nan":
            continue
        data_val = row[col_data]
        # aceita tanto data já em texto AAAA-MM-DD quanto datetime do Excel
        try:
            data_str = pd_to_iso_date(data_val)
        except Exception:
            avisos.append(f"Data inválida na linha do índice '{indice}': {data_val!r} — linha ignorada.")
            continue
        valor = row[col_valor]
        fonte = str(row[col_fonte]).strip() if col_fonte and pd_notna(row[col_fonte]) else arquivo_origem

        cur.execute("""INSERT OR REPLACE INTO indices_macroeconomicos (indice, data_referencia, valor, fonte)
                        VALUES (?,?,?,?)""", (indice, data_str, float(valor), fonte))
        importadas += 1

    conn.commit()
    return importadas, avisos


def pd_to_iso_date(v):
    import datetime as dt
    if isinstance(v, str):
        return v[:10]
    if isinstance(v, (dt.date, dt.datetime)):
        return v.strftime("%Y-%m-%d")
    import pandas as pd
    return pd.to_datetime(v).strftime("%Y-%m-%d")
