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
    st.header("Screening — Seleção de Ações por Filtro")
    setores = sb_select("setores", "id,nome", ordem="nome")
    setores_df = pd.DataFrame(setores) if setores else pd.DataFrame(columns=["id","nome"])
    c1,c2,c3,c4,c5 = st.columns(5)
    pl_max = c1.number_input("P/L máximo", value=15.0)
    usar_pl = c1.checkbox("Aplicar filtro P/L", value=True)
    roe_min = c2.number_input("ROE mínimo (%)", value=12.0)
    usar_roe = c2.checkbox("Aplicar filtro ROE", value=True)
    lucro_min = c3.number_input("Lucro líquido mínimo", value=0.0)
    usar_lucro = c3.checkbox("Aplicar filtro Lucro", value=False)
    divliq_max = c4.number_input("Dív.Líq/PL máximo", value=1.0)
    usar_div = c4.checkbox("Aplicar filtro Dív/PL", value=False)
    setor_nome = c5.selectbox("Setor", ["Todos"] + [s["nome"] for s in setores])

    if st.button("🔍 Buscar ações"):
        # Para o Supabase, a função de screening vai direto na tabela
        # (sem conexão SQLite) — usa a mesma lógica mas via API
        from supabase import create_client
        sb = get_supabase()
        q = sb.table("balancos_dre").select(
            "empresa_id,data_referencia,net_income,total_equity,net_debt,share_issued,preco_mercado_referencia,"
            "empresas!inner(id,ticker,razao_social,setores!inner(nome))"
        )
        rows = q.execute().data or []
        # pega só o balanço mais recente por empresa
        latest = {}
        for r in rows:
            eid = r["empresa_id"]
            if eid not in latest or r["data_referencia"] > latest[eid]["data_referencia"]:
                latest[eid] = r
        resultado = []
        for r in latest.values():
            emp = r.get("empresas", {})
            setor_r = (emp.get("setores") or {}).get("nome","")
            if setor_nome != "Todos" and setor_r != setor_nome:
                continue
            share = r.get("share_issued")
            ni = r.get("net_income")
            eq = r.get("total_equity")
            nd = r.get("net_debt")
            preco = r.get("preco_mercado_referencia")
            lpa = ni/share if (ni and share) else None
            roe = ni/eq*100 if (ni and eq) else None
            pl = preco/lpa if (preco and lpa) else None
            dpl = nd/eq if (nd and eq) else None
            if usar_pl and (pl is None or pl > pl_max): continue
            if usar_roe and (roe is None or roe < roe_min): continue
            if usar_lucro and (ni is None or ni < lucro_min): continue
            if usar_div and (dpl is None or dpl > divliq_max): continue
            resultado.append({"ticker": emp.get("ticker"), "razao_social": emp.get("razao_social"),
                               "setor": setor_r, "data_referencia": r["data_referencia"],
                               "P/L": round(pl,2) if pl else None, "ROE (%)": round(roe,2) if roe else None,
                               "Lucro Líquido": ni, "Dív.Líq/PL": round(dpl,2) if dpl else None,
                               "empresa_id": r["empresa_id"]})
        st.session_state["screening_resultado"] = resultado

    if "screening_resultado" in st.session_state:
        resultado = st.session_state["screening_resultado"]
        if not resultado:
            st.warning("Nenhuma ação encontrada.")
        else:
            df_res = pd.DataFrame(resultado)
            st.success(f"{len(df_res)} ação(ões) encontrada(s).")
            escolhidas = st.multiselect("Selecione quais ações analisar (1 a 10)",
                                         df_res["ticker"].tolist(), max_selections=10, key="screening_escolhidas")
            st.dataframe(df_res.drop(columns=["empresa_id"]), use_container_width=True)
            if escolhidas and st.button("💾 Guardar seleção para analisar uma a uma"):
                uid = usuario_id()
                for tk in escolhidas:
                    eid = int(df_res[df_res["ticker"]==tk]["empresa_id"].iloc[0])
                    sb_upsert("lista_analise", {"empresa_id": eid, "usuario_id": uid,
                               "data_selecao": pd.Timestamp.now().isoformat(), "status": "pendente"})
                st.success(f"{len(escolhidas)} ação(ões) guardada(s) em 'Minha Lista de Análise'.")

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
                st.write("**Etapa 1 — Lance ou confirme o balanço mais recente.**")
                bals = sb_select("balancos_dre","data_referencia", filtros={"empresa_id": emp_id}, ordem="data_referencia")
                if bals:
                    st.success(f"Balanço existente: {', '.join([b['data_referencia'] for b in bals])}. Pode seguir ou lançar um novo.")
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
                        "fonte": "Lançado via Fluxo de Análise"
                    }
                    if st.form_submit_button("💾 Salvar balanço"):
                        sb_upsert("balancos_dre", dados_bal)
                        st.success("Balanço salvo.")
                        st.rerun()

            elif step == 2:
                st.write("**Etapa 2 — Indicadores e valor intrínseco.**")
                bals = sb_select("balancos_dre","*", filtros={"empresa_id": emp_id}, ordem="data_referencia")
                if not bals:
                    st.warning("Sem balanço. Volte para a Etapa 1.")
                else:
                    datas = [b["data_referencia"] for b in bals]
                    data_ref = st.selectbox("Data", datas)
                    bal = next(b for b in bals if b["data_referencia"] == data_ref)
                    ind = calc.calcular_indicadores(bal)
                    st.dataframe(pd.DataFrame([{"Indicador":k,"Valor":round(v,4) if v else None} for k,v in ind.items()]), use_container_width=True)
                    if st.button("💾 Gravar indicadores"):
                        inds_def = sb_select("indicadores_definicao","id,nome")
                        for nome, valor in ind.items():
                            match = next((x for x in inds_def if x["nome"]==nome), None)
                            if match and valor is not None:
                                sb_upsert("indicadores_calculados",{"empresa_id":emp_id,"data_referencia":data_ref,"indicador_id":match["id"],"valor":valor})
                        st.success("Indicadores gravados.")
                    c1,c2,c3 = st.columns(3)
                    g = c1.number_input("g (%)",value=6.0,key="fg")
                    y = c2.number_input("Y (%)",value=6.5,key="fy")
                    wacc = c3.number_input("WACC (%)",value=10.0,key="fw")
                    lpa,vpa,fcf = ind.get("LPA"),ind.get("VPA"),ind.get("FCF")
                    preco = bal.get("preco_mercado_referencia")
                    vi_s = calc.graham_simplificado(lpa,g=g)
                    vi_c = calc.graham_complexo(lpa,g,y)
                    vi_f,_ = calc.fluxo_caixa_descontado(fcf,g/100,wacc/100,anos=5,g_terminal=0.03,divida_liquida=bal.get("net_debt") or 0,num_acoes=bal.get("share_issued"))
                    r1,r2,r3 = st.columns(3)
                    r1.metric("Graham Simplif.",f"R$ {vi_s:.2f}" if vi_s else "—")
                    r2.metric("Graham Complexo",f"R$ {vi_c:.2f}" if vi_c else "—")
                    r3.metric("FCD",f"R$ {vi_f:.2f}" if vi_f else "—")
                    if st.button("💾 Gravar valores intrínsecos"):
                        pr = json.dumps({"g":g,"y":y,"wacc":wacc})
                        for metodo,vi in [("simplificado",vi_s),("complexo",vi_c),("fcd",vi_f)]:
                            if vi: sb_upsert("valor_intrinseco",{"empresa_id":emp_id,"data_referencia":data_ref,"metodo":metodo,"valor":vi,"premissas_json":{"g":g,"y":y,"wacc":wacc}})
                        st.success("Valores intrínsecos gravados.")

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
    aba_imp_i, aba_man_i = st.tabs(["📥 Importar Excel","✏️ Cadastrar"])
    with aba_imp_i:
        arq_i = st.file_uploader("Arquivo .xlsx (colunas: Índice, Data, Valor)", type=["xlsx"], key="idx_up")
        if arq_i:
            df_i = pd.read_excel(arq_i)
            st.dataframe(df_i.head(20), use_container_width=True)
            if st.button("✅ Importar índices"):
                qtd_i, av_i = calc.importar_indices_excel(None, df_i, arquivo_origem=arq_i.name)
                st.info("Use a aba manual para lançar os índices individualmente por enquanto — "
                        "a importação em lote via Supabase está prevista para a próxima versão.")
    with aba_man_i:
        with st.form("form_idx"):
            c1,c2,c3,c4 = st.columns(4)
            ind_n = c1.selectbox("Índice",["Selic","CDI","IPCA","IGP-M","Ibovespa"])
            dt_i = c2.text_input("Data")
            vl_i = c3.number_input("Valor",value=0.0)
            ft_i = c4.text_input("Fonte","Banco Central/B3")
            if st.form_submit_button("Salvar") and dt_i:
                sb_upsert("indices_macroeconomicos",{"indice":ind_n,"data_referencia":dt_i,"valor":vl_i,"fonte":ft_i})
                st.success("Índice salvo."); st.rerun()
    filtro_i = st.selectbox("Filtrar por índice",["Todos","Selic","CDI","IPCA","IGP-M","Ibovespa"])
    hist_i = sb_select("indices_macroeconomicos","indice,data_referencia,valor,fonte",
                        filtros={"indice":filtro_i} if filtro_i!="Todos" else None, ordem="data_referencia")
    st.dataframe(pd.DataFrame(hist_i), use_container_width=True)

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
