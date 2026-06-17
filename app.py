import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

# Configuração de Layout
st.set_page_config(page_title="Highline Management", layout="wide")

# Estilização CSS para garantir que as seções não fiquem invisíveis
st.markdown("""
    <style>
        [data-testid="stSidebar"] { background-color: #2E5A44; }
        .prontuario-secao { background-color: #2E5A44; color: white; padding: 10px; border-radius: 5px; margin-top: 20px; }
        .bloco-texto { border: 1px solid #ccc; padding: 15px; background-color: #f9f9f9; border-radius: 5px; }
    </style>
""", unsafe_allow_html=True)

# Conexão com Banco de Dados
@st.cache_data(ttl=600)
def carregar_dados():
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_clientes = conn.read(worksheet="Clientes")
    df_evolucoes = conn.read(worksheet="Evolucoes")
    df_precos = conn.read(worksheet="Precos")
    return df_clientes, df_evolucoes, df_precos

# Tentativa de carregamento
try:
    df_clientes, df_evolucoes, df_precos = carregar_dados()
except Exception as e:
    st.error(f"Erro na conexão com o Banco: {e}. Verifique o arquivo secrets.toml")
    st.stop()

# --- MENU LATERAL ---
with st.sidebar:
    st.title("🏋️‍♂️ Highline")
    menu = st.radio("Navegação", ["Dashboard", "Prontuário", "Financeiro", "Preços", "Perfil", "Arquivo Morto"])

# --- LÓGICA DE NAVEGAÇÃO ---

if menu == "Dashboard":
    st.title("📊 Dashboard")
    col1, col2 = st.columns(2)
    col1.metric("Total Ativos", len(df_clientes[df_clientes['Status'] == 'Ativo']))
    col2.metric("Total de Cadastros", len(df_clientes))
    st.dataframe(df_clientes, use_container_width=True)

elif menu == "Prontuário":
    st.title("🩺 Prontuário Eletrônico")
    paciente = st.selectbox("Selecione o Cliente:", df_clientes['Nome'].unique())
    
    # Busca dados
    dados_p = df_clientes[df_clientes['Nome'] == paciente].iloc[0]
    evol_p = df_evolucoes[df_evolucoes['Nome'] == paciente]
    
    st.markdown(f"### Histórico de {paciente}")
    st.write(f"**Objetivo:** {dados_p.get('Objetivo', 'Não informado')}")
    
    st.markdown('<div class="prontuario-secao">Evoluções Registradas</div>', unsafe_allow_html=True)
    st.dataframe(evol_p, use_container_width=True)
    
    if st.button("Imprimir Prontuário"):
        html_pront = f"<html><body><h1>Relatório: {paciente}</h1><p>{dados_p.get('Conduta', '')}</p></body></html>"
        components.html(html_pront, height=500)

elif menu == "Financeiro":
    st.title("💰 Financeiro")
    st.dataframe(df_clientes[['Nome', 'Valor', 'Status']], use_container_width=True)

elif menu == "Preços":
    st.title("🏷️ Tabela de Preços")
    st.dataframe(df_precos, use_container_width=True)

elif menu == "Perfil":
    st.title("👤 Perfil Administrativo")
    st.write("Configurações do sistema Highline Management.")

elif menu == "Arquivo Morto":
    st.title("🗄️ Arquivo Morto")
    inativos = df_clientes[df_clientes['Status'] == 'Inativo']
    st.dataframe(inativos, use_container_width=True)
