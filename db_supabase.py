"""
db_supabase.py
Conexão com o Supabase (PostgreSQL gerenciado) e funções de autenticação.
Substitui o db.py que usava SQLite local.
"""
import streamlit as st
from supabase import create_client, Client

# ---------- Conexão ----------

@st.cache_resource
def get_supabase() -> Client:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)


# ---------- Autenticação ----------

def login(email: str, senha: str):
    """Tenta fazer login. Retorna (True, usuario) ou (False, mensagem_de_erro)."""
    sb = get_supabase()
    try:
        resp = sb.auth.sign_in_with_password({"email": email, "password": senha})
        st.session_state["usuario"] = resp.user
        st.session_state["session"] = resp.session
        return True, resp.user
    except Exception as e:
        return False, str(e)


def logout():
    sb = get_supabase()
    try:
        sb.auth.sign_out()
    except Exception:
        pass
    for k in ["usuario", "session"]:
        st.session_state.pop(k, None)


def registrar(email: str, senha: str, nome: str):
    """Cria novo usuário. Retorna (True, usuario) ou (False, mensagem)."""
    sb = get_supabase()
    try:
        resp = sb.auth.sign_up({
            "email": email,
            "password": senha,
            "options": {"data": {"nome": nome}}
        })
        return True, resp.user
    except Exception as e:
        return False, str(e)


def usuario_logado():
    """Retorna o usuário da sessão ou None."""
    return st.session_state.get("usuario")


def usuario_id():
    u = usuario_logado()
    return str(u.id) if u else None


def sou_admin():
    """Verifica se o usuário logado é administrador consultando a tabela perfis."""
    uid = usuario_id()
    if not uid:
        return False
    sb = get_supabase()
    try:
        resp = sb.table("perfis").select("tipo").eq("id", uid).single().execute()
        return resp.data and resp.data.get("tipo") == "administrador"
    except Exception:
        return False


def get_perfil():
    """Retorna o perfil completo do usuário logado."""
    uid = usuario_id()
    if not uid:
        return None
    sb = get_supabase()
    try:
        resp = sb.table("perfis").select("*").eq("id", uid).single().execute()
        return resp.data
    except Exception:
        return None


def promover_para_admin(email_alvo: str):
    """Promove um usuário para administrador (só admin pode chamar). Uso via SQL Editor do Supabase."""
    # Esta operação é feita diretamente no SQL Editor do Supabase:
    # UPDATE perfis SET tipo = 'administrador' WHERE email = 'email@exemplo.com';
    pass


# ---------- Helpers de query ----------

def sb_select(tabela: str, colunas: str = "*", filtros: dict = None, ordem: str = None):
    """SELECT genérico. Retorna lista de dicts."""
    sb = get_supabase()
    q = sb.table(tabela).select(colunas)
    if filtros:
        for col, val in filtros.items():
            q = q.eq(col, val)
    if ordem:
        q = q.order(ordem)
    try:
        return q.execute().data or []
    except Exception as e:
        st.error(f"Erro ao consultar {tabela}: {e}")
        return []


def sb_insert(tabela: str, dados: dict):
    """INSERT. Retorna o registro inserido ou None."""
    sb = get_supabase()
    try:
        return sb.table(tabela).insert(dados).execute().data
    except Exception as e:
        st.error(f"Erro ao inserir em {tabela}: {e}")
        return None


def sb_upsert(tabela: str, dados: dict):
    """INSERT OR REPLACE (upsert). Retorna os dados ou None."""
    sb = get_supabase()
    try:
        return sb.table(tabela).upsert(dados).execute().data
    except Exception as e:
        st.error(f"Erro ao salvar em {tabela}: {e}")
        return None


def sb_update(tabela: str, dados: dict, filtros: dict):
    """UPDATE. Retorna os dados atualizados ou None."""
    sb = get_supabase()
    try:
        q = sb.table(tabela).update(dados)
        for col, val in filtros.items():
            q = q.eq(col, val)
        return q.execute().data
    except Exception as e:
        st.error(f"Erro ao atualizar {tabela}: {e}")
        return None


def sb_delete(tabela: str, filtros: dict):
    """DELETE. Retorna os dados removidos ou None."""
    sb = get_supabase()
    try:
        q = sb.table(tabela).delete()
        for col, val in filtros.items():
            q = q.eq(col, val)
        return q.execute().data
    except Exception as e:
        st.error(f"Erro ao deletar de {tabela}: {e}")
        return None
