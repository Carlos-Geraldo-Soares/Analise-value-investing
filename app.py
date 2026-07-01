"""
app.py — Sistema de Value Investing (Etapa 5 — Supabase + Login)
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
pagina = st.sidebar.radio("Navegação", [
    "0. Screening de Ações",
    "0b. Minha Lista de Análise",
    "🧭 Fluxo de Análise (guiado)",
    "1. Empresas e Setores",
    "2. Balanço / DRE",
    "3. Indicadores e Valor Intrínseco",
    "4. Critérios e Índice de Qualidade",
    "5. Avaliação Buffett (qualitativo)",
    "6. Carteira",
    "7. Relatório da Ação",
    "8. Informações Relevantes",
    "9. Índices Macroeconômicos",
    "10. Tabelas de Apoio",
    "11. Administração de Usuários",
], key="nav_radio")

# ---------- HELPERS ----------

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
    st.caption("Busca **todas as ações da B3** no Fundamentus em tempo real e aplica seus filtros. "
               "As ações selecionadas entram na lista de análise — só aí você decide quais cadastrar "
               "no banco para análise completa (balanço, valor intrínseco etc.).")

    # ── Configuração dos filtros ──────────────────────────────────
    st.subheader("Configure os filtros")
    st.caption("Defina o sinal (≤ menor ou igual, ≥ maior ou igual, = igual) e o valor limite de cada indicador.")

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

    # Inicializar estado dos filtros
    if "filtros_screen" not in st.session_state:
        st.session_state["filtros_screen"] = {
            ind[1]: {"sinal": ind[2], "valor": ind[3], "ativo": ind[4]}
            for ind in INDICADORES_SCREEN
        }

    SINAIS = ["≤", "≥", "="]
    cols_head = st.columns([3, 2, 2, 1])
    cols_head[0].markdown("**Indicador**")
    cols_head[1].markdown("**Sinal**")
    cols_head[2].markdown("**Valor limite**")
    cols_head[3].markdown("**Ativo**")

    for nome, chave, sinal_def, val_def, ativo_def in INDICADORES_SCREEN:
        estado = st.session_state["filtros_screen"][chave]
        c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
        c1.write(nome)
        novo_sinal = c2.selectbox(" ", SINAIS,
                                   index=SINAIS.index(estado["sinal"]),
                                   key=f"sinal_{chave}", label_visibility="collapsed")
        novo_val = c3.number_input(" ", value=float(estado["valor"]),
                                    key=f"val_{chave}", label_visibility="collapsed")
        novo_ativo = c4.checkbox(" ", value=estado["ativo"],
                                  key=f"ativo_{chave}", label_visibility="collapsed")
        st.session_state["filtros_screen"][chave] = {
            "sinal": novo_sinal, "valor": novo_val, "ativo": novo_ativo}

    setor_filtro = st.selectbox("Filtrar por setor (opcional)",
                                 ["Todos"] + [s["nome"] for s in sb_select("setores","nome",ordem="nome")])

    st.markdown("---")
    col_btn1, col_btn2 = st.columns([2, 5])
    buscar = col_btn1.button("🔍 Buscar ações na B3 (Fundamentus)", type="primary")
    col_btn2.caption("Busca todas as ações da B3 em tempo real — pode levar 10 a 30 segundos.")

    if buscar:
        with st.spinner("Buscando todas as ações da B3 no Fundamentus... aguarde."):
            try:
                import fundamentus
                df_fund = fundamentus.get_resultado()
                df_fund = df_fund.reset_index()
                df_fund.columns = [str(c).strip().lower() for c in df_fund.columns]

                # mapa de colunas do Fundamentus para nossos nomes
                # normaliza os nomes das colunas antes de mapear
                def norm_col(c):
                    import unicodedata
                    c = str(c).strip().lower()
                    c = "".join(x for x in unicodedata.normalize("NFKD",c) if not unicodedata.combining(x))
                    return c.replace(" ","_").replace("/","_").replace(".","_").replace("__","_")

                df_fund.columns = [norm_col(c) for c in df_fund.columns]

                # mapa flexível — cobre variações de nome do Fundamentus
                mapa_cols = {
                    "papel": "ticker", "nome": "razao_social", "setor": "setor",
                    "p_l": "pl", "p_vp": "pvp",
                    "roe": "roe", "roic": "roic",
                    "div_yield": "dy",
                    "mrg_liq_": "mrgliq", "mrg__liq_": "mrgliq",
                    "div_patrim_": "divpl", "div_brut__patrim_": "divpl",
                    "ev_ebitda": "evebitda", "p_ebitda": "pebitda",
                    "cresc__rec_5a": "cagr5", "cresc_rec_5a": "cagr5",
                    "liq__corr_": "liqc", "liq_corr_": "liqc",
                    "liq_2meses": "liq2meses",
                    "patrim__liq": "pl_val", "patrim_liq": "pl_val",
                }
                df_fund = df_fund.rename(columns={k: v for k, v in mapa_cols.items() if k in df_fund.columns})

                # converter colunas numéricas
                for col in ["pl","pvp","roe","roic","dy","mrgliq","divpl","evebitda","pebitda","cagr5","liqc","liq2meses"]:
                    if col in df_fund.columns:
                        df_fund[col] = pd.to_numeric(df_fund[col], errors="coerce")

                # converter ROE e outros para % se estiverem em decimal
                for col in ["roe","roic","dy","mrgliq","cagr5"]:
                    if col in df_fund.columns:
                        # Fundamentus já retorna em % (ex: 0.15 = 15%)
                        if df_fund[col].abs().max() < 5:
                            df_fund[col] = df_fund[col] * 100

                # aplicar filtros
                filtros = st.session_state["filtros_screen"]
                mask = pd.Series([True] * len(df_fund), index=df_fund.index)
                for chave, cfg in filtros.items():
                    if not cfg["ativo"] or chave not in df_fund.columns:
                        continue
                    val = cfg["valor"]
                    sinal = cfg["sinal"]
                    col_series = pd.to_numeric(df_fund[chave], errors="coerce")
                    if sinal == "≤":
                        mask &= col_series <= val
                    elif sinal == "≥":
                        mask &= col_series >= val
                    elif sinal == "=":
                        mask &= col_series == val

                df_result = df_fund[mask].copy()

                if setor_filtro != "Todos" and "setor" in df_result.columns:
                    df_result = df_result[df_result["setor"].str.contains(setor_filtro, case=False, na=False)]

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
                       "Tente afrouxar algum critério.")
        else:
            st.success(f"✅ {len(df_result)} ação(ões) encontrada(s) de {total} consultadas.")

            # colunas a exibir
            cols_exibir = [c for c in ["ticker","razao_social","setor","pl","pvp","roe","roic",
                                         "dy","mrgliq","divpl","evebitda","liqc"] if c in df_result.columns]
            df_show = df_result[cols_exibir].copy()
            df_show.columns = [c.upper() for c in df_show.columns]
            st.dataframe(df_show, use_container_width=True)

            st.subheader("Selecione as ações para analisar")
            tickers_disp = df_result["ticker"].tolist() if "ticker" in df_result.columns else []
            escolhidas = st.multiselect(
                "Escolha de 1 a 10 ações para guardar na lista de análise",
                tickers_disp, max_selections=10, key="screening_escolhidas_fund")

            if escolhidas and st.button("💾 Guardar seleção para analisar uma a uma", type="primary"):
                uid = usuario_id()
                cadastradas = 0
                for tk in escolhidas:
                    # verifica se empresa já existe no banco; se não, cria automaticamente
                    emps = sb_select("empresas", "id", filtros={"ticker": tk})
                    if emps:
                        eid = emps[0]["id"]
                    else:
                        # busca dados da empresa no resultado do Fundamentus
                        row_fund = df_result[df_result["ticker"] == tk]
                        nome_emp = row_fund["razao_social"].iloc[0] if "razao_social" in row_fund.columns and not row_fund.empty else tk
                        r_emp = sb_insert("empresas", {"ticker": tk, "razao_social": str(nome_emp), "ativo": True})
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
                    st.info(f"{cadastradas} empresa(s) nova(s) criada(s) automaticamente no banco.")
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
            sb_update("lista_analise", {"status": "em_analise"}, {"id": int(linha["id"])})
            st.rerun()
        if c2.button("✅ Analisada"):
            sb_update("lista_analise", {"status": "analisada"}, {"id": int(linha["id"])})
            st.rerun()
        if c3.button("🗑️ Remover"):
            sb_delete("lista_analise", {"id": int(linha["id"])})
            st.rerun()
        st.markdown("---")
        if st.button(f"🧭 Iniciar Fluxo de Análise guiado para {ticker_sel}", type="primary"):
            sb_update("lista_analise", {"status": "em_analise"}, {"id": int(linha["id"])})
            iniciar_fluxo_analise(int(linha["empresa_id"]))

# ================================================================
elif pagina == "🧭 Fluxo de Análise (guiado)":
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
                bals = sb_select("balancos_dre","data_referencia", filtros={"empresa_id": emp_id}, ordem="data_referencia")
                if bals:
                    st.success(f"✅ Balanço já existe: {', '.join([b['data_referencia'] for b in bals])}. Pode avançar ou buscar dados mais recentes.")

                st.subheader("🌐 Buscar balanço automaticamente (Yahoo Finance)")
                st.caption("Clique para buscar os dados mais recentes do balanço e DRE diretamente do Yahoo Finance.")
                if st.button("🔄 Buscar balanço automático agora", type="primary"):
                    with st.spinner(f"Buscando dados de {emp['ticker']} no Yahoo Finance..."):
                        try:
                            dados = calc.buscar_balanco_yfinance(emp["ticker"])
                            if dados.get("data_referencia"):
                                dados["empresa_id"] = emp_id
                                sb_upsert("balancos_dre", {k:v for k,v in dados.items() if v is not None})
                                st.success(f"✅ Balanço de {dados['data_referencia']} importado automaticamente!")
                                st.rerun()
                            else:
                                st.warning("Dados encontrados mas sem data de referência. Use o lançamento manual.")
                        except Exception as e:
                            st.error(f"Erro ao buscar no Yahoo Finance: {e}")
                            st.info("Verifique se o ticker está correto (ex.: TRIS3, B3SA3) e tente novamente.")

                st.markdown("---")
                st.subheader("✏️ Ou lance manualmente")
                with st.form("fluxo_balanco"):
                    data_ref = st.text_input("Data de referência", "2024-12-31")
                    c1,c2,c3 = st.columns(3)
                    dados_bal = {
                        "empresa_id": emp_id, "data_referencia": data_ref,
                        "total_assets": c1.number_input("Total Assets",value=0.0),
                        "total_liabilities": c2.number_input("Total Liabilities",value=0.0),
                        "total_equity": c3.number_input("Total Equity",value=0.0),
                        "net_debt": c1.number_input("Dívida Líquida",value=0.0),
                        "share_issued": c2.number_input("Nº Ações (milhares)",value=0.0),
                        "preco_mercado_referencia": c3.number_input("Preço de mercado",value=0.0),
                        "total_revenue": c1.number_input("Total Revenue",value=0.0),
                        "net_income": c2.number_input("Net Income",value=0.0),
                        "ebitda": c3.number_input("EBITDA",value=0.0),
                        "ebit": c1.number_input("EBIT",value=0.0),
                        "depreciacao_amortizacao": c2.number_input("Depreciação",value=0.0),
                        "capex": c3.number_input("CAPEX",value=0.0),
                        "fonte": "Lançado manualmente"
                    }
                    if st.form_submit_button("💾 Salvar balanço manual"):
                        sb_upsert("balancos_dre", dados_bal)
                        st.success("Balanço salvo.")
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
                        for nome, valor in ind.items():
                            match = next((x for x in inds_def if x["nome"]==nome), None)
                            if match and valor is not None:
                                sb_upsert("indicadores_calculados",{"empresa_id":emp_id,"data_referencia":data_ref,"indicador_id":match["id"],"valor":valor})
                        st.success("✅ Indicadores gravados.")

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
                        for metodo, vi in [("simplificado",resultado_vi['vi_simplificado']),
                                           ("numero_graham",resultado_vi['vi_numero_graham']),
                                           ("complexo",resultado_vi['vi_complexo']),
                                           ("fcd",resultado_vi['vi_fcd'])]:
                            if vi:
                                sb_upsert("valor_intrinseco",{"empresa_id":emp_id,"data_referencia":data_ref,
                                    "metodo":metodo,"valor":vi,"premissas_json":resultado_vi['premissas']})
                        st.success("✅ Todos os valores intrínsecos gravados.")

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
                        sb_upsert("avaliacao_qualitativa_buffett",{"empresa_id":emp_id,"moat":moat,"moat_justificativa":moat_just,"qualidade_gestao":gestao,"previsibilidade":prev,"circulo_competencia":circulo,"data_avaliacao":date.today().isoformat()})
                        st.success("Avaliação salva.")

            elif step == 4:
                st.write("**Etapa 4 — Relatório final: Comprar, Manter ou Vender?**")
                bals = sb_select("balancos_dre","*",filtros={"empresa_id":emp_id},ordem="data_referencia")
                if not bals:
                    st.warning("Sem balanço. Volte para a Etapa 1.")
                else:
                    bal = bals[-1]
                    ind = calc.calcular_indicadores(bal)
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
                    if st.button("✅ Concluir análise desta ação", type="primary"):
                        sb_update("lista_analise",{"status":"analisada"},{"empresa_id":emp_id,"usuario_id":usuario_id()})
                        st.success("Análise concluída!")

            st.markdown("---")
            n1,n2,_ = st.columns([1,1,4])
            if step>1 and n1.button("⬅️ Voltar"):
                st.session_state["fluxo_step"]=step-1; st.rerun()
            if step<4 and n2.button("Próximo ➡️",type="primary"):
                st.session_state["fluxo_step"]=step+1; st.rerun()

# ================================================================
elif pagina == "1. Empresas e Setores":
    st.header("Empresas e Setores")
    c1,c2 = st.columns(2)
    with c1:
        st.subheader("Setores")
        df_set = pd.DataFrame(sb_select("setores","id,nome",ordem="nome"))
        if not df_set.empty: st.dataframe(df_set, use_container_width=True)
        with st.form("form_setor"):
            ns = st.text_input("Novo setor")
            if st.form_submit_button("Adicionar") and ns:
                sb_insert("setores",{"nome":ns}); st.rerun()
    with c2:
        st.subheader("Empresas")
        st.dataframe(lista_empresas(), use_container_width=True)
    st.subheader("Cadastrar nova empresa")
    setores = sb_select("setores","id,nome",ordem="nome")
    tipos = sb_select("tipo_mercado","codigo",ordem="codigo")
    sits = sb_select("situacao_empresa","codigo",ordem="codigo")
    with st.form("form_emp"):
        c1,c2,c3 = st.columns(3)
        ticker = c1.text_input("Ticker")
        razao = c2.text_input("Razão social")
        cnpj = c3.text_input("CNPJ")
        setor_nome = st.selectbox("Setor", [""]+[s["nome"] for s in setores])
        c4,c5 = st.columns(2)
        tipo_m = c4.selectbox("Tipo mercado",[t["codigo"] for t in tipos]) if tipos else c4.text_input("Tipo")
        sit = c5.selectbox("Situação",[s["codigo"] for s in sits]) if sits else c5.text_input("Situação")
        site = st.text_input("Site")
        desc = st.text_area("Descrição do negócio")
        futuro = st.text_area("Análise de futuro")
        if st.form_submit_button("Salvar empresa") and ticker and razao:
            setor_id = next((s["id"] for s in setores if s["nome"]==setor_nome), None)
            sb_upsert("empresas",{"ticker":ticker.upper(),"cnpj":cnpj,"razao_social":razao,
                "setor_id":setor_id,"tipo_mercado_codigo":tipo_m,"situacao_codigo":sit,
                "site":site,"descricao_negocio":desc,"analise_futuro":futuro})
            st.success(f"Empresa {ticker.upper()} salva."); st.rerun()

# ================================================================
elif pagina == "6. Carteira":
    st.header("Carteira de Ações")
    uid = usuario_id()
    with st.form("nova_carteira"):
        nome_c = st.text_input("Nova carteira")
        if st.form_submit_button("Criar") and nome_c:
            sb_insert("carteiras",{"nome":nome_c,"usuario_id":uid}); st.rerun()

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
                        imp = 0
                        for _,row in df_p.iterrows():
                            tk = str(row[ct]).strip().upper()
                            if not tk or tk=="NAN": continue
                            emps = sb_select("empresas","id",filtros={"ticker":tk})
                            if emps: eid = emps[0]["id"]
                            else:
                                r = sb_insert("empresas",{"ticker":tk,"razao_social":tk})
                                eid = r[0]["id"] if r else None
                                st.warning(f"Empresa '{tk}' criada automaticamente. Complete o cadastro na Tela 1.")
                            if eid:
                                sb_upsert("carteira_posicoes_importadas",{"carteira_id":cart_id,"empresa_id":eid,
                                    "quantidade":float(row[cq]),"valor_medio":float(row[cv]),
                                    "data_importacao":hoje,"arquivo_origem":arq.name})
                                imp+=1
                        st.success(f"{imp} posição(ões) importada(s).")
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
                    cols = st.columns(4)
                    for i,(eid,tk) in enumerate(emps_map.items()):
                        atual_r = sb_select("cotacao_atual_manual","preco_atual",filtros={"carteira_id":cart_id,"empresa_id":eid})
                        v0 = float(atual_r[0]["preco_atual"]) if atual_r else 0.0
                        novo = cols[i%4].number_input(tk,value=v0,key=f"p_{eid}")
                        if novo>0:
                            sb_upsert("cotacao_atual_manual",{"carteira_id":cart_id,"empresa_id":eid,"preco_atual":novo,"data_atualizacao":date.today().isoformat()})
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
                        sb_insert("movimentos_carteira",{"carteira_id":cart_id,"empresa_id":int(empresa["id"]),"tipo":tipo,"data":data_m,"quantidade":qtd,"preco_unitario":preco_u,"taxas":taxas,"total_operacao":tot,"origem":"manual"})
                        st.success("Operação registrada."); st.rerun()
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
                        sb_insert("proventos_recebidos",{"carteira_id":cart_id,"empresa_id":int(empresa_p["id"]),"data":dp,"tipo":tp,"valor":vp,"observacao":obs})
                        st.success("Provento registrado."); st.rerun()
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
                sb_update("perfis",{"tipo":novo_tipo},{"id":uid_alvo})
                st.success(f"Tipo de acesso de {email_alvo} alterado para {novo_tipo}.")
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
                    sb_update("perfis",{"codigo":cod,"cpf":cpf,"nome":nome,"telefone":tel},{"id":p_sel["id"]})
                    st.success("Perfil atualizado."); st.rerun()

# ================================================================
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
                sb_upsert("indices_macroeconomicos", reg)
                st.success(f"{ind_n} {int(ano_m)}/{int(mes_m):02d} salvo.")
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
    st.subheader("Tipo de Mercado")
    st.dataframe(pd.DataFrame(sb_select("tipo_mercado")), use_container_width=True)
    st.subheader("Situação da Empresa")
    st.dataframe(pd.DataFrame(sb_select("situacao_empresa")), use_container_width=True)
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
            sb_upsert("indicadores_definicao",{"codigo":cod_i.upper(),"nome":nom_i,"categoria":cat_i,"formula":form_i,"faixa_ideal":fi_i,"tipo_calculo":tc_i,"grandeza":gr_i,"valor_referencia":vr_i})
            st.success(f"Indicador '{nom_i}' cadastrado."); st.rerun()

else:
    # Para telas não implementadas neste arquivo ainda, mostrar aviso informativo
    st.info(f"Tela '{pagina}' — em implementação. Use as telas já disponíveis.")
