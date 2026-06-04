import streamlit as st
import pandas as pd
from datetime import datetime, date
import os
import plotly.express as px

# Configurações do Studio
ARQUIVO_LOGO = "Highline Logo.png"
LIMITE_ALUNOS_POR_TURMA = 3

LISTA_BAIRROS_PADRAO = ["Centro", "Hamburgo Velho", "Canudos", "Pátria Nova", "Rio Branco", "Ideal", "Primavera", "Rondônia", "Mauá"]
LISTA_QUEIXAS_PADRAO = [
    "Dor Lombar (Lombalgia)", "Dor Cervical (Cervicalgia)", "Hérnia de Disco",
    "Má Postura / Escoliose / Cifose", "Dor nos Joelhos", "Dor nos Ombros (Tendinite / Bursite)",
    "Falta de Flexibilidade / Encurtamento", "Fortalecimento Geral / Condicionamento",
    "Reabilitação Pós-Operatória / Lesão", "Gestante / Pós-Parto", "Idoso / Manutenção da Autonomia",
    "Estresse / Ansiedade / Alívio de Tensões", "Outro (Detalhar abaixo)"
]

def obter_coordenadas(bairro):
    bairros_coords = {
        "centro": {"lat": -29.6842, "lon": -51.1314}, "hamburgo velho": {"lat": -29.6795, "lon": -51.1115},
        "canudos": {"lat": -29.6950, "lon": -51.1002}, "pátria nova": {"lat": -29.6912, "lon": -51.1256},
        "rio branco": {"lat": -29.6998, "lon": -51.1340}, "ideal": {"lat": -29.6770, "lon": -51.1325},
        "primavera": {"lat": -29.6685, "lon": -51.1410}, "rondônia": {"lat": -29.6920, "lon": -51.1120},
        "mauá": {"lat": -29.6690, "lon": -51.1190}
    }
    return bairros_coords.get(str(bairro).strip().lower(), {"lat": -29.6842, "lon": -51.1314})

# Conexão Nuvem Robusta via Pandas (Lê direto as abas sem depender de conectores externos no Cloud)
SPREADSHEET_ID = "13OigffmPV0Eu8qzEpQC3g1ReKbb2lO01iZgWXSzFRhw"

def carregar_dados_nuvem():
    if "preco_pacotes" not in st.session_state:
        st.session_state.preco_pacotes = {"1x por semana": 150.0, "2x por semana": 220.0, "3x por semana": 300.0}
    
    # Aba: Alunos
    try:
        url_alunos = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&sheet=alunos"
        st.session_state.df_alunos = pd.read_csv(url_alunos).fillna("")
        st.session_state.df_alunos.columns = [c.strip() for c in st.session_state.df_alunos.columns]
    except:
        st.session_state.df_alunos = pd.DataFrame(columns=["Nome", "Telefone", "Bairro", "Plano", "Valor", "Vencimento", "Dias", "Horario", "Status", "Queixa", "Conduta", "Genero", "Nascimento", "Inicio_Aulas"])
        
    # Aba: Espera
    try:
        url_espera = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&sheet=espera"
        st.session_state.df_espera = pd.read_csv(url_espera).fillna("")
        st.session_state.df_espera.columns = [c.strip() for c in st.session_state.df_espera.columns]
    except:
        st.session_state.df_espera = pd.DataFrame(columns=["Nome", "Telefone", "Data"])
        
    # Aba: Financeiro
    try:
        url_financeiro = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&sheet=financeiro"
        st.session_state.df_financeiro = pd.read_csv(url_financeiro).fillna("")
        st.session_state.df_financeiro.columns = [c.strip() for c in st.session_state.df_financeiro.columns]
    except:
        st.session_state.df_financeiro = pd.DataFrame(columns=["Aluno", "Valor", "Data", "Tipo", "Status"])

def salvar_dados_nuvem(aba, df_atualizado):
    # Nota operacional: Para gravação direta no Cloud via app, utiliza-se a API ou Coletores. 
    # Para manter o espelhamento imediato em runtime no painel:
    st.cache_data.clear()

def contar_alunos_no_horario_nuvem(dias_propostos, horario_proposto, ignorar_aluno=""):
    if st.session_state.df_alunos.empty:
        return 0
    df_ativos = st.session_state.df_alunos[st.session_state.df_alunos["Status"] == "Ativo"]
    if df_ativos.empty:
        return 0
    
    dias_prop_list = [d.strip().lower() for d in str(dias_propostos).split(",") if d.strip()]
    horario_prop_limpo = str(horario_proposto).strip().replace(":", "").zfill(4)
    contador = 0
    
    for _, aluno in df_ativos.iterrows():
        if aluno["Nome"] == ignorar_aluno:
            continue
        aluno_horario = str(aluno["Horario"]).strip().replace(":", "").zfill(4)
        if aluno_horario != horario_prop_limpo:
            continue
        aluno_dias = [d.strip().lower() for d in str(aluno["Dias"]).split(",") if d.strip()]
        if set(dias_prop_list) & set(aluno_dias):
            contador += 1
    return contador

def calcular_idade(data_nasc_str):
    try:
        dt_nasc = datetime.strptime(str(data_nasc_str).strip(), "%Y-%m-%d").date()
        hoje = date.today()
        return hoje.year - dt_nasc.year - ((hoje.month, hoje.day) < (dt_nasc.month, dt_nasc.day))
    except:
        return None

def agrupar_faixa_etaria(idade):
    if idade is None: return "Não Informado"
    if idade <= 25: return "Até 25 anos"
    elif idade <= 35: return "26-35 anos"
    elif idade <= 45: return "36-45 anos"
    elif idade <= 55: return "46-55 anos" # Corrigido bug de variável oculta (status -> idade)
    elif idade <= 65: return "56-65 anos"
    else: return "66+ anos"

# Executa a carga inicial
carregar_dados_nuvem()

st.set_page_config(page_title="Highline Management", layout="wide", page_icon="🧘‍♀️")

st.markdown("<style>[data-testid='stSidebar'] { background-color: #1a6344 !important; } [data-testid='stSidebar'] * { color: white !important; } .logo-container { display: flex; justify-content: center; padding: 20px 0; } .stButton>button { background-color: #1a6344 !important; color: white !important; } h1, h2, h3 { color: #1a6344 !important; } .metric-box { background-color: #f0f7f4; padding: 15px; border-radius: 8px; border-left: 5px solid #1a6344; }</style>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown('<div class="logo-container">', unsafe_allow_html=True)
    if os.path.exists(ARQUIVO_LOGO): st.image(ARQUIVO_LOGO, width=150)
    else: st.title("HIGHLINE")
    st.markdown('</div>', unsafe_allow_html=True)
    tela = st.radio("Menu de Navegação", ["🗓️ Agenda", "👥 Alunos", "🗂️ Arquivo Morto", "⏳ Espera", "🗺️ Mapa", "📊 Perfil", "📝 Cadastro", "💰 Financeiro"])

# 1. TELA AGENDA
if tela == "🗓️ Agenda":
    mapa_dias_semana = {0: "seg", 1: "ter", 2: "qua", 3: "qui", 4: "sex", 5: "sab", 6: "dom"}
    hoje = date.today()
    numero_dia_atual = hoje.weekday()
    termo_dia_atual = mapa_dias_semana[numero_dia_atual]
    dias_extenso = {0: "Segunda-feira", 1: "Terça-feira", 2: "Quarta-feira", 3: "Quinta-feira", 4: "Sexta-feira", 5: "Sábado", 6: "Domingo"}
    st.title(f"🗓️ Agenda de Hoje ({dias_extenso[numero_dia_atual]})")
    
    aniversariantes_hoje = []
    if not st.session_state.df_alunos.empty:
        for _, aluno in st.session_state.df_alunos.iterrows():
            if aluno["Status"] == "Ativo" and aluno["Nascimento"]:
                try:
                    dt_nasc = datetime.strptime(str(aluno["Nascimento"]).strip(), "%Y-%m-%d").date()
                    if dt_nasc.day == hoje.day and dt_nasc.month == hoje.month:
                        aniversariantes_hoje.append(aluno["Nome"])
                except: pass
                
    if aniversariantes_hoje:
        for n_aniv in aniversariantes_hoje:
            st.success(f"🎉 Hoje é aniversário de **{n_aniv}**! Não esqueça de dar os parabéns! 🎂")
            
    if not st.session_state.df_alunos.empty:
        df_agenda = st.session_state.df_alunos[st.session_state.df_alunos["Status"] == "Ativo"].copy()
        if not df_agenda.empty:
            df_agenda = df_agenda[df_agenda["Dias"].astype(str).str.lower().str.contains(termo_dia_atual)].copy()
            if not df_agenda.empty:
                df_agenda['Horario_Ordenacao'] = df_agenda['Horario'].astype(str).str.strip().str.zfill(5)
                df_agenda = df_agenda.sort_values(by="Horario_Ordenacao", ascending=True)
                st.dataframe(df_agenda[["Horario", "Nome", "Dias"]], use_container_width=True, index=False)
            else: st.info(f"Nenhum aluno agendado para hoje.")
        else: st.info("Nenhum aluno ativo cadastrado.")
    else: st.info("Nenhum aluno cadastrado no sistema.")

# 2. TELA ALUNOS
elif tela == "👥 Alunos":
    st.title("👥 Controle de Alunos Ativos")
    if not st.session_state.df_alunos.empty:
        df_ativos = st.session_state.df_alunos[st.session_state.df_alunos["Status"] == "Ativo"]
        if not df_ativos.empty:
            st.dataframe(df_ativos, use_container_width=True, index=False)
            st.markdown("---")
            col_ed1, col_ed2 = st.columns(2)
            
            with col_ed1:
                st.markdown("### ✏️ Editar Dados do Aluno")
                lista_nomes_ativos = df_ativos["Nome"].tolist()
                aluno_para_editar = st.selectbox("Selecione o aluno que deseja modificar:", lista_nomes_ativos)
                dados_aluno = st.session_state.df_alunos[st.session_state.df_alunos["Nome"] == aluno_para_editar].iloc[0].to_dict()
                
                with st.form("form_edicao_aluno"):
                    ed_tel = st.text_input("Telefone Corporativo", value=str(dados_aluno.get("Telefone", "")))
                    idx_bairro = LISTA_BAIRROS_PADRAO.index(dados_aluno["Bairro"]) if dados_aluno["Bairro"] in LISTA_BAIRROS_PADRAO else 0
                    ed_bairro = st.selectbox("Bairro Residencial", LISTA_BAIRROS_PADRAO, index=idx_bairro)
                    lista_planos = list(st.session_state.preco_pacotes.keys())
                    idx_plano = lista_planos.index(dados_aluno["Plano"]) if dados_aluno["Plano"] in lista_planos else 0
                    ed_plano = st.selectbox("Plano Contratado", lista_planos, index=idx_plano)
                    ed_dias = st.text_input("Dias da Semana", value=str(dados_aluno.get("Dias", "")))
                    ed_hora = st.text_input("Horário do Treino", value=str(dados_aluno.get("Horario", "")))
                    ed_vencimento = st.number_input("Dia de Vencimento", min_value=1, max_value=31, value=int(dados_aluno.get("Vencimento", 10)))
                    ed_conduta = st.text_area("Conduta e Objetivos Clínicos", value=str(dados_aluno.get("Conduta", "")))
                    
                    if st.form_submit_button("Salvar Alterações 💾"):
                        if contar_alunos_no_horario_nuvem(ed_dias, ed_hora, ignorar_aluno=aluno_para_editar) >= LIMITE_ALUNOS_POR_TURMA:
                            st.error(f"Inviável alterar! Turma cheia.")
                        else:
                            idx_linha = st.session_state.df_alunos[st.session_state.df_alunos["Nome"] == aluno_para_editar].index[0]
                            st.session_state.df_alunos.at[idx_linha, "Telefone"] = ed_tel
                            st.session_state.df_alunos.at[idx_linha, "Bairro"] = ed_bairro
                            st.session_state.df_alunos.at[idx_linha, "Plano"] = ed_plano
                            st.session_state.df_alunos.at[idx_linha, "Dias"] = ed_dias
                            st.session_state.df_alunos.at[idx_linha, "Horario"] = ed_hora
                            st.session_state.df_alunos.at[idx_linha, "Vencimento"] = int(ed_vencimento)
                            st.session_state.df_alunos.at[idx_linha, "Conduta"] = ed_conduta
                            st.session_state.df_alunos.at[idx_linha, "Valor"] = float(st.session_state.preco_pacotes.get(ed_plano, 0.0))
                            
                            salvar_dados_nuvem("alunos", st.session_state.df_alunos)
                            st.toast("✅ Alterações gravadas temporariamente em memória!")
                            st.rerun()
            with col_ed2:
                st.markdown("### 🚫 Desativar Aluno")
                aluno_para_desativar = st.selectbox("Selecione o aluno para desativar:", df_ativos["Nome"].tolist(), key="
