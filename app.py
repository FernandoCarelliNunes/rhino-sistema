import streamlit as st
from st_supabase_connection import SupabaseConnection

# Configuração da Página
st.set_page_config(page_title="RHINO RH - Sistema de Recrutamento", layout="wide")

# Conexão com Banco de Dados (Configuraremos as chaves no próximo passo)
conn = st.connection("supabase", type=SupabaseConnection)

st.title("🦏 RHINO RH - Gestão de Recrutamento")

# Sidebar para Navegação
menu = st.sidebar.selectbox("Menu", ["Dashboard", "Cadastrar Vaga", "Gerenciar Candidatos"])

if menu == "Dashboard":
    st.header("📊 Indicadores Gerais")
    col1, col2, col3 = st.columns(3)
    
    # Exemplo de métrica (buscando do banco)
    vagas_ativas = conn.table("vagas").select("*", count="exact").execute()
    candidatos_total = conn.table("candidatos").select("*", count="exact").execute()
    
    col1.metric("Vagas Abertas", len(vagas_ativas.data))
    col2.metric("Total de Candidatos", len(candidatos_total.data))
    col3.metric("Taxa de Fechamento", "85%") # Cálculo futuro

    # Gráfico simples
    st.subheader("Candidatos por Fase")
    if len(candidatos_total.data) > 0:
        import pandas as pd
        df = pd.DataFrame(candidatos_total.data)
        st.bar_chart(df['status_fase'].value_counts())

elif menu == "Cadastrar Vaga":
    st.header("🆕 Nova Vaga")
    with st.form("form_vaga"):
        cliente = st.text_input("Nome do Cliente")
        titulo = st.text_input("Título da Vaga")
        if st.form_submit_button("Salvar Vaga"):
            conn.table("vagas").insert({"cliente": cliente, "titulo_vaga": titulo}).execute()
            st.success("Vaga cadastrada!")

elif menu == "Gerenciar Candidatos":
    st.header("👥 Candidatos no Processo")
    # Filtro por Vaga
    vagas_data = conn.table("vagas").select("id, titulo_vaga, cliente").execute()
    vagas_dict = {f"{v['cliente']} - {v['titulo_vaga']}": v['id'] for v in vagas_data.data}
    
    vaga_selecionada = st.selectbox("Selecione a Vaga", options=list(vagas_dict.keys()))
    
    with st.expander("➕ Adicionar Novo Candidato"):
        nome = st.text_input("Nome completo")
        fase = st.selectbox("Fase Atual", ["Triagem", "Entrevista", "Finalista", "Contratado"])
        if st.form_submit_button("Adicionar"):
            conn.table("candidatos").insert({
                "nome": nome, 
                "vaga_id": vagas_dict[vaga_selecionada], 
                "status_fase": fase
            }).execute()
            st.rerun()

    # Listagem de Candidatos daquela vaga
    res = conn.table("candidatos").select("*").eq("vaga_id", vagas_dict[vaga_selecionada]).execute()
    if res.data:
        st.table(res.data)