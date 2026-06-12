import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import os
import modulos  # Importa o arquivo criado acima

# Configuração de Layout e CSS
st.set_page_config(page_title="Highline Management", layout="wide", page_icon="🏋️‍♂️")
st.markdown("""
    <style>
        [data-testid="stSidebar"] { background-color: #2E5A44 !important; }
        [data-testid="stSidebar"] * { color: white !important; }
        .stRadio input[type="radio"]:checked + div { color: #FFD700 !important; font-weight: bold !important; }
        .prontuario-card { background: white !important; color: black !important; padding: 25px; border: 2px solid #2E5A44; border-radius: 8px; margin-top: 15px; }
        .prontuario-header { text-align: center; border-bottom: 3px solid #2E5A44; color: #2E5A44 !important; }
        .prontuario-secao { border-bottom: 1px solid #ccc; margin-top: 20px; color: #2E5A44 !important; font-weight: bold; }
        .tabela-prontuario { width: 100%; border-collapse: collapse; }
        .tabela-prontuario td { padding: 8px; border: 1px solid #ddd; color: black !important; }
        @media print { [data-testid="stSidebar"], button, .no-print { display: none !important; } }
    </style>
""", unsafe_allow_html=True)

# Conexão com Google Sheets
df_alunos, df_financeiro, df_espera, df_precos, df_evolucoes = pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
try:
    if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
        if "private_key" in st.secrets["connections"]["gsheets"]:
            st.secrets["connections"]["gsheets"]["private_key"] = st.secrets["connections"]["gsheets"]["private_key"].replace("\\n", "\n")
    
    conn = st.connection("gsheets", type=GSheetsConnection)
    try: df_alunos = modulos.limpiar_dataframe(conn.read(worksheet="alunos", ttl=2))
    except: pass
    try: df_financeiro = modulos.limpiar_dataframe(conn.read(worksheet="financeiro", ttl=2))
    except: pass
    try: df_espera = modulos.limpiar_dataframe(conn.read(worksheet="espera", ttl=2))
    except: pass
    try: df_precos = modulos.limpiar_dataframe(conn.read(worksheet="precos", ttl=2))
    except: pass
    try: df_evolucoes = modulos.limpiar_dataframe(conn.read(worksheet="evolucao", ttl=2))
    except: pass
except Exception as e:
    st.error(f"Erro de conexão: {e}")

# Mapeamento de preços
dict_precos = {"1x semana": 180.0, "2x semana": 220.0, "3x semana": 300.0}
if not df_precos.empty and "Plano" in df_precos.columns:
    for _, r in df_precos.iterrows():
        dict_precos[str(r["Plano"])] = modulos.converter_para_float(r["Valor"])

# Menu Lateral
with st.sidebar:
    if os.path.exists("Highline Logo.png"): st.image("Highline Logo.png", use_container_width=True)
    menu = st.radio("🔒 Navegação", ["📅 Agenda", "👥 Alunos", "📝 Cadastro", "📈 Evolução", "⏳ Espera", "💰 Financeiro", "👤 Perfil", "⚙️ Preços", "🖨️ Imprimir Prontuário"])

# Redirecionamento das Páginas
if menu == "📅 Agenda": modulos.mostrar_agenda(df_alunos)
elif menu == "👥 Alunos": modulos.mostrar_alunos(df_alunos, dict_precos, conn)
elif menu == "📝 Cadastro": modulos.mostrar_cadastro(df_alunos, dict_precos, conn)
elif menu == "📈 Evolução": modulos.mostrar_evolucao(df_evolucoes, df_alunos, conn)
elif menu == "⏳ Espera": modulos.mostrar_espera(df_espera, conn)
elif menu == "💰 Financeiro": modulos.mostrar_financeiro(df_financeiro, df_alunos, conn)
elif menu == "👤 Perfil": modulos.mostrar_perfil(df_alunos)
elif menu == "⚙️ Preços": modulos.mostrar_precos(dict_precos, conn)
elif menu == "🖨️ Imprimir Prontuário": modulos.mostrar_prontuario(df_alunos)
