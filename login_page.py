"""
login_page.py
Tela de login, cadastro e recuperação de senha.
Chamada pelo app.py antes de qualquer outra tela.
"""
import streamlit as st
from db_supabase import login, registrar, logout, usuario_logado, get_perfil


def tela_login():
    """Exibe a tela de login/cadastro. Retorna True se o usuário está logado."""
    u = usuario_logado()
    if u:
        return True

    st.title("📈 Value Investing")
    st.subheader("Acesso ao sistema")

    aba_login, aba_cadastro = st.tabs(["🔐 Entrar", "📝 Criar conta"])

    with aba_login:
        with st.form("form_login"):
            email = st.text_input("E-mail")
            senha = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar", type="primary"):
                if not email or not senha:
                    st.warning("Preencha e-mail e senha.")
                else:
                    ok, resultado = login(email, senha)
                    if ok:
                        st.success("Login realizado com sucesso!")
                        st.rerun()
                    else:
                        if "Invalid login" in str(resultado) or "invalid" in str(resultado).lower():
                            st.error("E-mail ou senha incorretos.")
                        else:
                            st.error(f"Erro ao entrar: {resultado}")

    with aba_cadastro:
        st.caption("Crie sua conta para acessar o sistema. Após criar, faça login na aba ao lado.")
        with st.form("form_cadastro"):
            nome_novo = st.text_input("Nome completo")
            email_novo = st.text_input("E-mail")
            senha_nova = st.text_input("Senha (mínimo 6 caracteres)", type="password")
            senha_conf = st.text_input("Confirmar senha", type="password")
            if st.form_submit_button("Criar conta"):
                if not nome_novo or not email_novo or not senha_nova:
                    st.warning("Preencha todos os campos.")
                elif senha_nova != senha_conf:
                    st.error("As senhas não coincidem.")
                elif len(senha_nova) < 6:
                    st.error("A senha deve ter pelo menos 6 caracteres.")
                else:
                    ok, resultado = registrar(email_novo, senha_nova, nome_novo)
                    if ok:
                        st.success("Conta criada! Verifique seu e-mail para confirmar o cadastro, "
                                   "depois faça login na aba 'Entrar'.")
                    else:
                        if "already" in str(resultado).lower():
                            st.error("Este e-mail já está cadastrado. Use a aba 'Entrar'.")
                        else:
                            st.error(f"Erro ao criar conta: {resultado}")

    return False


def barra_usuario():
    """Exibe nome do usuário e botão de logout na sidebar."""
    u = usuario_logado()
    if not u:
        return
    perfil = get_perfil()
    nome = perfil.get("nome", u.email) if perfil else u.email
    tipo = perfil.get("tipo", "usuario") if perfil else "usuario"
    icone = "👑" if tipo == "administrador" else "👤"
    st.sidebar.markdown(f"**{icone} {nome}**")
    st.sidebar.caption(u.email)
    if st.sidebar.button("🚪 Sair"):
        logout()
        st.rerun()
    st.sidebar.markdown("---")
