import streamlit as st
import pandas as pd
from datetime import datetime

# 1. CONFIGURAÇÃO DA PÁGINA (Deve ser obrigatoriamente a primeira linha executável)
st.set_page_config(page_title="Studio Highline - Gestão", layout="wide", page_icon="🏋️‍♂️")

# 2. CONFIGURAÇÃO DA BARRA LATERAL (SIDEBAR)
st.sidebar.markdown("# 🏋️‍♂️ Studio Highline")
st.sidebar.markdown("### Painel de Controle v1.0")

# Exibição de Data e Hora
data_atual = datetime.now().strftime("%d/%m/%Y")
hora_atual = datetime.now().strftime("%H:%M")
st.sidebar.info(f"📅 **Data:** {data_atual}\n\n🕒 **Hora:** {hora_atual}")

# ID e Parâmetros de Conexão com o Google Sheets
PLANILHA_ID = "130igffmPV0Eu8qzepQC3g1ReKbb2IO01iZgWXSZFRhw"

@st.cache_data(ttl=30, show_spinner="Sincronizando tabelas com o Google Sheets...")
def carregar_dados_sheets():
    base_url = f"https://docs.google.com/spreadsheets/d/{PLANILHA_ID}/gviz/tq?tqx=out:csv"
    
    # Links construídos individualmente usando os GIDs numéricos fornecidos
    url_alunos = f"{base_url}&gid=0"
    url_financeiro = f"{base_url}&gid=1020408012"
    url_espera = f"{base_url}&gid=1228435040"
    
    # Leitura isolada convertendo dados vazios em strings limpas
    df_a = pd.read_csv(url_alunos, keep_default_na=False)
    df_f = pd.read_csv(url_financeiro, keep_default_na=False)
    df_e = pd.read_csv(url_espera, keep_default_na=False)
    
    return df_a, df_f, df_e

# Bloco de segurança para tratamento de falhas de conexão
try:
    df_alunos, df_financeiro, df_espera = carregar_dados_sheets()
    st.sidebar.success("✅ Banco de dados sincronizado!")
except Exception as e:
    st.sidebar.error("❌ Erro na sincronização.")
    st.error(f"Falha ao conectar com o Google Sheets. Detalhes técnicos: {e}")
    st.stop()

# 3. PROCESSAMENTO DE MÉTRICAS OPERACIONAIS
total_ativos = 0
if df_alunos is not None and not df_alunos.empty:
    if "Status" in df_alunos.columns:
        # Filtro insensível a maiúsculas/minúsculas para computar alunos Ativos
        total_ativos = len(df_alunos[df_alunos["Status"].astype(str).str.upper() == "ATIVO"])
    else:
        total_ativos = len(df_alunos)

total_espera = len(df_espera) if df_espera is not None else 0

st.sidebar.metric(label="Alunos Ativos", value=total_ativos)
st.sidebar.metric(label="Fila de Espera", value=total_espera)

# 4. CORPO PRINCIPAL DA APLICAÇÃO
st.title("Sistema de Gestão Integrada")
st.markdown("Controle operacional, financeiro e clínico-desportivo do Studio Highline.")
st.markdown("---")

# Construção das abas de navegação principal
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
            st.info("Nenhum registro com horário válido foi localizado na planilha.")
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
        
        busca_nome = st.text_input("🔍 Buscar aluno pelo nome:", placeholder="Digite o nome para filtrar...", key="txt_busca")
        if busca_nome and "Nome" in df_ativos.columns:
            df_ativos = df_ativos[df_ativos["Nome"].astype(str).str.contains(busca_nome, case=False, na=False)]
            
        st.dataframe(df_ativos, use_container_width=True, hide_index=True)
        
        st.markdown("### ⚙️ Ações de Gerenciamento")
        if "Nome" in df_ativos.columns and not df_ativos.empty:
            aluno_sel = st.selectbox("Selecione um aluno para desativar:", df_ativos["Nome"].tolist(), key="sb_desativar")
            if st.button("Confirmar Desativação", type="secondary", key="btn_desativar"):
                st.warning(f"Ação preventiva: Solicitação de desativação para '{aluno_sel}' registrada.")
    else:
        st.info("Nenhum aluno ativo mapeado no sistema.")

# ==========================================
# ABA 3: RELATÓRIO FINANCEIRO
# ==========================================
with tab_financeiro:
    st.subheader("📊 Relatório Financeiro")
    
    if df_financeiro is not None and not df_financeiro.empty:
        if "Valor" in df_financeiro.columns:
            # Tratamento de strings financeiras (R$, pontos e vírgulas) para conversão numérica estável
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
    st.markdown("Preencha as informações para estruturar a linha de dados formatada:")
    
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
                st.success(f"🎉 Dados validados para {nome_cad}!")
                payload = {
                    "Nome": nome_cad, "Telefone": tel_cad, "Bairro": bairro_cad,
                    "Plano": plano_cad, "Valor": valor_cad, "Vencimento": venc_cad,
                    "Dias": dias_cad, "Horario": hora_cad, "Status": "Ativo"
                }
                st.json(payload)
            else:
                st.error("⚠️ Preencha os campos obrigatórios (Nome e WhatsApp).")
