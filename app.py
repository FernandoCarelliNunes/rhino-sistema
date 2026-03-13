import streamlit as st
from supabase import create_client
import pandas as pd

page = 0

logins = {"ADM":"1234"}

# 1. Configuração da Página
st.set_page_config(page_title="RHINO RH - Gestão", layout="wide", page_icon="🦏")

# Conexão com Supabase
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
except Exception as e:
    st.error("Erro ao carregar credenciais. Verifique os Secrets no Streamlit Cloud.")
    st.stop()

def loginPage():
    st.title("RHINO RH")

    login = st.text_input("Login")
    senha = st.text_input("Senha")
    if st.button("Entrar"):
        if login in logins.keys():
            if str(senha) == logins[login]:
                page = 1


def homePage():
    st.title("🦏 RHINO RH - Sistema de Recrutamento")

    # 2. Menu Lateral
    menu = st.sidebar.selectbox("Navegação", ["📊 Dashboard", "💼 Gestão de Vagas", "👥 Candidatos por Vaga", "📥 Importar Planilha"])

    # --- ABA: DASHBOARD ---
    if menu == "📊 Dashboard":
        st.header("Painel de Indicadores")
        
        vagas_res = supabase.table("vagas").select("*").execute()
        cand_res = supabase.table("candidatos").select("*").execute()
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Vagas Ativas", len(vagas_res.data))
        col2.metric("Total de Candidatos", len(cand_res.data))
        
        if len(cand_res.data) > 0:
            df_cands = pd.DataFrame(cand_res.data)
            # Filtro seguro para contratados
            contratados = df_cands[df_cands['status_fase'].astype(str).str.contains('Contratado', case=False, na=False)]
            col3.metric("Contratados", len(contratados))
            
            st.divider()
            st.subheader("Candidatos por Fase")
            st.bar_chart(df_cands['status_fase'].value_counts())
        else:
            st.info("O banco de dados está vazio. Use a aba 'Importar Planilha'.")

    # --- ABA: VAGAS ---
    elif menu == "💼 Gestão de Vagas":
        st.header("Controle de Vagas")
        vagas_data = supabase.table("vagas").select("*").order("data_abertura", desc=True).execute()
        if vagas_data.data:
            st.dataframe(pd.DataFrame(vagas_data.data), use_container_width=True)
        else:
            st.info("Nenhuma vaga cadastrada.")

    # --- ABA: CANDIDATOS ---
    elif menu == "👥 Candidatos por Vaga":
        st.header("Gestão de Candidatos")
        vagas_res = supabase.table("vagas").select("id, titulo_vaga, cliente").execute()
        
        if not vagas_res.data:
            st.warning("Nenhuma vaga encontrada.")
        else:
            dict_vagas = {f"{v['cliente']} - {v['titulo_vaga']}": v['id'] for v in vagas_res.data}
            vaga_selecionada = st.selectbox("Selecione a Vaga:", options=list(dict_vagas.keys()))
            id_vaga = dict_vagas[vaga_selecionada]

            cands_vaga = supabase.table("candidatos").select("*").eq("vaga_id", id_vaga).execute()
            if cands_vaga.data:
                df_display = pd.DataFrame(cands_vaga.data)
                # Colunas que queremos mostrar (se existirem)
                cols_desejadas = ['nome', 'status_fase', 'contato', 'pretensao_salarial', 'observacoes']
                cols_presentes = [c for c in cols_desejadas if c in df_display.columns]
                st.dataframe(df_display[cols_presentes], use_container_width=True)
            else:
                st.info("Nenhum candidato nesta vaga.")

    # --- ABA: IMPORTAR ---
    elif menu == "📥 Importar Planilha":
        st.header("Importar Excel (Migração)")
        st.write("Selecione sua planilha `.xlsx` para carregar os dados.")
        
        arquivo_excel = st.file_uploader("Subir planilha RHINO", type=['xlsx'])
        
        if arquivo_excel:
            xl = pd.ExcelFile(arquivo_excel)
            abas_clientes = [a for a in xl.sheet_names if a != 'Painel de Vagas RHINO']
            selecionadas = st.multiselect("Selecione as abas:", abas_clientes, default=abas_clientes)
            
            if st.button("Executar Importação"):
                barra = st.progress(0)
                for i, aba in enumerate(selecionadas):
                    try:
                        # 1. Cria a Vaga
                        v_res = supabase.table("vagas").insert({"cliente": aba, "titulo_vaga": f"Recrutamento {aba}"}).execute()
                        vaga_id = v_res.data[0]['id']
                        
                        # 2. Lê a aba
                        df = pd.read_excel(arquivo_excel, sheet_name=aba)
                        # Normaliza nomes de colunas: sem espaços, tudo maiúsculo, sem acentos básicos
                        df.columns = [str(c).strip().upper().replace('Á', 'A').replace('É', 'E') for c in df.columns]
                        
                        for _, row in df.iterrows():
                            nome = str(row.get('CANDIDATO', '')).strip()
                            if nome and nome.lower() not in ['nan', 'none', '']:
                                # Monta o objeto de inserção com nomes de colunas do BANCO
                                obj_insert = {
                                    "vaga_id": int(vaga_id),
                                    "nome": nome,
                                    "status_fase": str(row.get('STATUS', 'Triagem')),
                                    "contato": str(row.get('CONTATO', '')),
                                    "pretensao_salarial": str(row.get('SALARIO', row.get('REMUNERACAO', ''))),
                                    "observacoes": f"Migrado via planilha (Aba {aba})"
                                }
                                # Tenta inserir no Supabase
                                supabase.table("candidatos").insert(obj_insert).execute()
                    except Exception as e:
                        st.error(f"Erro ao processar aba {aba}: {e}")
                    
                    barra.progress((i + 1) / len(selecionadas))
                
                st.success("✅ Importação finalizada! Verifique o Dashboard.")

if page == 0:
    loginPage()
elif page == 1:
    homePage()