import streamlit as st
from supabase import create_client

# Configuração da Página
st.set_page_config(page_title="RHINO RH", layout="wide")

# Tenta carregar as credenciais dos Secrets
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
except Exception as e:
    st.error(f"Erro de configuração: Verifique se os Secrets SUPABASE_URL e SUPABASE_KEY foram criados corretamente.")
    st.stop()

st.title("🦏 RHINO RH - Gestão de Recrutamento")

# Sidebar
menu = st.sidebar.selectbox("Menu", ["Dashboard", "Vagas", "Candidatos"])

if menu == "Dashboard":
    st.info("Sistema conectado com sucesso! Selecione uma opção no menu lateral.")
    
    # Teste de conexão simples
    try:
        vagas = supabase.table("vagas").select("*").execute()
        st.success(f"Conexão ativa! Total de vagas no banco: {len(vagas.data)}")
    except Exception as e:
        st.warning("O banco de dados está vazio ou as tabelas ainda não foram criadas no SQL Editor do Supabase.")

elif menu == "Vagas":
    st.subheader("Gerenciar Vagas")
    with st.form("nova_vaga"):
        cliente = st.text_input("Nome do Cliente")
        titulo = st.text_input("Título da Vaga")
        if st.form_submit_button("Salvar"):
            supabase.table("vagas").insert({"cliente": cliente, "titulo_vaga": titulo}).execute()
            st.rerun()

elif menu == "Candidatos":
    st.subheader("Gerenciar Candidatos")
    # Aqui listaremos os candidatos em breve
