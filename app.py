import streamlit as st
import pandas as pd
from datetime import datetime

# 1. Configuração da página (DEVE ser a primeira linha de código)
st.set_page_config(page_title="Studio Highline - Gestão", layout="wide", page_icon="🏋️‍♂️")

# 2. Configuração da Barra Lateral (Sidebar)
st.sidebar.markdown("# 🏋️‍♂️ Studio Highline")
st.sidebar.markdown("### Painel de Controle v1.0")

# Exibição de Data e Hora
data_atual = datetime.now().strftime("%d/%m/%Y")
hora_atual = datetime.now().strftime("%H:%M")
st.sidebar.info(f"📅 **Data:** {data_atual}\n\n🕒 **Hora:** {hora_atual}")

# ID da Planilha "Banco Highline"
PLANILHA_ID = "130igffmPV0Eu8qzepQC3g1ReKbb2IO01iZgWXSZFRhw"

@st.cache_data(ttl=30, show_spinner="Buscando dados no Google Sheets...")
def carregar_dados_seguros():
    # Formato de exportação nativo do Google (Altamente estável para o Streamlit)
    base_url = f"https://docs.google.com/spreadsheets/d/{PLANILHA_ID}/export?format=csv"
    
    url_alunos = f"{base_url}&gid=0"
    url_financeiro = f"{base_url}&gid=1020408012"
    url_espera = f"{base_url}&gid=1228435040"
    
    # Faz a leitura forçando o tratamento de dados vazios
    df_a = pd.read_csv(url_alunos, keep_default_na=False)
    df_f = pd.read_csv(url_financeiro, keep_default_na=False)
    df_e = pd.read_csv(url_espera, keep_default_na=False)
    
    return df_a, df_f, df_e

# Tenta carregar os dados
try:
    df_alunos, df_financeiro, df_espera = carregar_dados_seguros()
    st.sidebar.success("✅ Tabelas sincronizadas com sucesso!")
except Exception as e:
    st.sidebar.error("❌ Erro de conexão.")
    st.error(
        f"Não foi possível ler as abas da planilha. \n\n"
        f"O Google retornou um erro de acesso. Se o erro persistir, verifique se o ID da planilha "
        f"ou os números de 'gid' das abas foram alterados no seu Google Sheets.\n\n"
        f"Detalhes do erro: {e}"
    )
    st.stop()

# 3. Processamento das Métricas da Sidebar
total_ativos = 0
if df_alunos is not None and not df_alunos.empty:
    if "Status" in df_alunos.columns:
        total_ativos = len(df_alunos[df_alunos["Status"].astype(str).str.upper() == "ATIVO"])
    else:
        total_ativos = len(df_alunos)

total_espera = len(df_espera) if df_espera is not None else 0

st.sidebar.metric(label="Alunos Ativos", value=total_ativos)
st.sidebar.metric(label="Fila de Espera", value=total_espera)

# 4. Corpo do Aplicativo (Abas)
st.title("Sistema de Gestão Integrada")
st.markdown("Controle operacional, financeiro e clínico-desportivo do Studio Highline.")
st.markdown("---")

tab_agenda, tab_alunos, tab_financeiro, tab_espera, tab_novos = st.tabs([
    "📅 Agenda do Dia", 
    "👥 Alunos Ativos", 
    "📊 Relatório Financeiro", 
    "⏳ Lista de Espera", 
    "➕ Novos Cadastros"
])

# ==========================================
# ABA 1: AGENDA DO DIA
# ==========================================
with tab_agenda:
    st.subheader("📅 Agendamentos e Horários")
    
    if df_alunos is not None and not df_alunos.empty:
        df_hoje = df_alunos.copy()
        if "Status" in df_hoje.columns:
            df_hoje = df_hoje[df_hoje["Status"].astype(str).str.upper() == "ATIVO"]
            
        if "Horario" in df_hoje.columns and not df_hoje.empty:
            df_hoje = df_hoje.sort_values(by="Horario")
            colunas_agenda = [col for col in ["Horario", "Nome", "Status", "Queixa", "Conduta", "Dias"] if col in df_hoje.columns]
            st.dataframe(df_hoje[colunas_agenda], use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum registro com horário válido encontrado na planilha.")
    else:
        st.info("A tabela de alunos está vazia.")

# ==========================================
# ABA 2: ALUNOS ATIVOS
# ==========================================
with tab_alunos:
    st.subheader("👥 Controle de Alunos")
    
    if df_alunos is not None and not df_alunos.empty:
        df_ativos = df_alunos[df_alunos["Status"].astype(str).str.upper() == "ATIVO"] if "Status" in df_alunos.columns else df_alunos
        st.metric(label="Total de Alunos Matriculados", value=len(df_ativos))
        
        busca_nome = st.text_input("🔍 Buscar aluno pelo nome:", placeholder="Digite o nome para filtrar...", key="busca_nome_aluno")
        if busca_nome and "Nome" in df_ativos.columns:
            df_ativos = df_ativos[df_ativos["Nome"].astype(str).str.contains(busca_nome, case=False, na=False)]
            
        st.dataframe(df_ativos, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum aluno ativo mapeado no sistema.")

# ==========================================
# ABA 3: RELATÓRIO FINANCEIRO
# ==========================================
with tab_financeiro:
    st.subheader("📊 Relatório Financeiro")
    
    if df_financeiro is not None and not df_financeiro.empty:
        if "Valor" in df_financeiro.columns:
            limpeza_valores = df_financeiro["Valor"].astype(str).str.replace("R$", "", regex=False)
            limpeza_valores = limpeza_valores.str.replace(".", "", regex=False).str.replace(",", ".", regex=False).str.strip()
            valores_num = pd.to_numeric(limpeza_valores, errors="coerce")
            
            faturamento = valores_num.sum()
            txt_faturamento = f"R$ {faturamento:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")
            st.metric(label="Faturamento Estimado", value=txt_faturamento)
        
        st.dataframe(df_financeiro, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum dado financeiro localizado.")

# ==========================================
# ABA 4: LISTA DE ESPERA
# ==========================================
with tab_espera:
    st.subheader("⏳ Lista de Espera")
    
    if df_espera is not None and not df_espera.empty:
        st.dataframe(df_espera, use_container_width=True, hide_index=True)
    else:
        st.info("A fila de espera está vazia no momento.")

# ==========================================
# ABA 5: NOVOS CADASTROS
# ==========================================
with tab_novos:
    st.subheader("➕ Gerador de Carga para Novos Alunos")
    
    with st.form("form_cadastro_aluno", clear_on_submit=True):
        nome_cad = st.text_input("Nome Completo:")
        tel_cad = st.text_input("WhatsApp com DDD:")
        bairro_cad = st.text_input("Bairro:")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            plano_cad = st.selectbox("Plano:", ["Mensal", "Trimestral", "Semestral", "Anual"])
        with c2:
            valor_cad = st.number_input("Mensalidade (R$):", min_value=0.0, value=150.00, step=10.00)
        with c3:
            venc_cad = st.number_input("Dia do Vencimento:", min_value=1, max_value=31, value=10, step=1)
            
        dias_cad = st.text_input("Dias de Aula (ex: Seg/Qua/Sex):")
        hora_cad = st.text_input("Horário Escolhido (ex: 08:00):")
        
        if st.form_submit_button("Validar e Gerar Registro"):
            if nome_cad and tel_cad:
                st.success(f"🎉 Dados validados com sucesso!")
                payload = {
                    "Nome": nome_cad, "Telefone": tel_cad, "Bairro": bairro_cad,
                    "Plano": plano_cad, "Valor": valor_cad, "Vencimento": venc_cad,
                    "Dias": dias_cad, "Horario": hora_cad, "Status": "Ativo"
                }
                st.json(payload)
            else:
                st.error("⚠️ Preencha os campos obrigatórios (Nome e WhatsApp).")
