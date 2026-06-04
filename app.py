import streamlit as st
import pandas as pd
from datetime import datetime

# Configuração da página do Streamlit (Deve ser estritamente a primeira linha de código)
st.set_page_config(page_title="Studio Highline - Gestão", layout="wide", page_icon="🏋️‍♂️")

# Título Lateral (Sidebar)
st.sidebar.markdown("# 🏋️‍♂️ Studio Highline")
st.sidebar.markdown("### Painel de Controle v1.0")

# Data e Hora Atual
data_atual = datetime.now().strftime("%d/%m/%Y")
hora_atual = datetime.now().strftime("%H:%M")
st.sidebar.info(f"📅 **Data de hoje:** {data_atual}\n\n🕒 **Hora:** {hora_atual}")

# ID Corrigido da sua Planilha "Banco Highline"
PLANILHA_ID = "130igffmPV0Eu8qzepQC3g1ReKbb2IO01iZgWXSZFRhw"

# Função para carregar os dados via API de Visualização do Google
@st.cache_data(ttl=30, show_spinner="Sincronizando banco de dados com a nuvem...")
def carregar_dados_sheets():
    # Usando o endpoint /gviz/tq que é o mais estável do Google para aplicativos web
    base_url = f"https://docs.google.com/spreadsheets/d/{PLANILHA_ID}/gviz/tq?tqx=out:csv"
    
    url_alunos = f"{base_url}&gid=0"
    url_financeiro = f"{base_url}&gid=1020408012"
    url_espera = f"{base_url}&gid=1228435040"
    
    # Leitura individual forçando tratamento de strings para evitar quebras por formatação antiga
    df_a = pd.read_csv(url_alunos, keep_default_na=False)
    df_f = pd.read_csv(url_financeiro, keep_default_na=False)
    df_e = pd.read_csv(url_espera, keep_default_na=False)
    
    return df_a, df_f, df_e

try:
    df_alunos, df_financeiro, df_espera = carregar_dados_sheets()
    st.sidebar.success("✅ Banco de dados sincronizado!")
except Exception as e:
    st.sidebar.error("❌ Erro na sincronização.")
    st.error(
        f"Não foi possível ler as abas da planilha. \n\n"
        f"Se o erro persistir, abra sua planilha no navegador e copie novamente o código longo "
        f"que fica entre '/d/' e '/edit' na barra de endereços para atualizar o PLANILHA_ID.\n\n"
        f"Detalhes: {e}"
    )
    st.stop()

# Cálculos de Métricas Seguras
total_matriculados = 0
if df_alunos is not None and not df_alunos.empty:
    if "Status" in df_alunos.columns:
        total_matriculados = len(df_alunos[df_alunos["Status"].astype(str).str.upper() == "ATIVO"])
    else:
        total_matriculados = len(df_alunos)

total_espera = len(df_espera) if df_espera is not None else 0

st.sidebar.metric(label="Alunos Ativos", value=total_matriculados)
st.sidebar.metric(label="Fila de Espera", value=total_espera)

# Título Principal do App
st.title("Sistema de Gestão Integrada")
st.markdown("Controle operacional, financeiro e clínico-desportivo do Studio Highline.")
st.markdown("---")

# Definição das Abas de Navegação no App
tab_agenda, tab_alunos, tab_financeiro, tab_espera, tab_novos = st.tabs([
    "📅 Agenda do Dia", 
    "👥 Alunos Ativos", 
    "📊 Relatório Financeiro", 
    "⏳ Lista de Espera", 
    "➕ Novos Cadastros"
])

# ==========================================
# 1. ABA: AGENDA DO DIA
# ==========================================
with tab_agenda:
    st.subheader("📅 Agendamentos e Horários")
    
    if df_alunos is not None and not df_alunos.empty:
        df_hoje = df_alunos
        if "Status" in df_hoje.columns:
            df_hoje = df_hoje[df_hoje["Status"].astype(str).str.upper() == "ATIVO"]
            
        if "Horario" in df_hoje.columns and not df_hoje.empty:
            df_hoje = df_hoje.sort_values(by="Horario")
            colunas_agenda = [c for c in ["Horario", "Nome", "Status", "Queixa", "Conduta", "Dias"] if c in df_hoje.columns]
            st.dataframe(df_hoje[colunas_agenda], use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum registro com horário definido para exibição.")
    else:
        st.info("Insira dados na planilha para visualizar a agenda de treinos.")

# ==========================================
# 2. ABA: ALUNOS ATIVOS
# ==========================================
with tab_alunos:
    st.subheader("👥 Controle de Alunos")
    
    if df_alunos is not None and not df_alunos.empty:
        df_ativos = df_alunos[df_alunos["Status"].astype(str).str.upper() == "ATIVO"] if "Status" in df_alunos.columns else df_alunos
        st.metric(label="Total de Alunos Matriculados", value=len(df_ativos))
        
        busca_nome = st.text_input("🔍 Buscar aluno pelo nome:", placeholder="Digite o nome...", key="busca_at")
        if busca_nome and "Nome" in df_ativos.columns:
            df_ativos = df_ativos[df_ativos["Nome"].astype(str).str.contains(busca_nome, case=False, na=False)]
            
        st.dataframe(df_ativos, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum aluno cadastrado.")

# ==========================================
# 3. ABA: RELATÓRIO FINANCEIRO
# ==========================================
with tab_financeiro:
    st.subheader("📊 Relatório Financeiro")
    
    if df_financeiro is not None and not df_financeiro.empty:
        if "Valor" in df_financeiro.columns:
            valores = pd.to_numeric(df_financeiro["Valor"].astype(str).str.replace("R$", "").str.replace(".", "").str.replace(",", ".").str.strip(), errors="coerce")
            faturamento_total = valores.sum()
            valor_formatado = f"R$ {faturamento_total:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")
            st.metric(label="Faturamento Estimado", value=valor_formatado)
        
        st.dataframe(df_financeiro, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum registro financeiro localizado.")

# ==========================================
# 4. ABA: LISTA DE ESPERA
# ==========================================
with tab_espera:
    st.subheader("⏳ Lista de Espera")
    
    if df_espera is not None and not df_espera.empty:
        st.dataframe(df_espera, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum aluno na fila de espera no momento.")

# ==========================================
# 5. ABA: NOVOS CADASTROS
# ==========================================
with tab_novos:
    st.subheader("➕ Gerador de Carga para Novos Alunos")
    
    with st.form("form_novo_aluno", clear_on_submit=True):
        nome_completo = st.text_input("Nome Completo:")
        whatsapp = st.text_input("WhatsApp com DDD:")
        bairro = st.text_input("Bairro:")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            modalidade = st.selectbox("Modalidade de Contrato:", ["Mensal", "Trimestral", "Semestral", "Anual"])
        with col2:
            preco_mensal = st.number_input("Preço Mensal (R$):", min_value=0.0, value=150.00, step=10.00)
        with col3:
            dia_vencimento = st.number_input("Dia do Vencimento:", min_value=1, max_value=31, value=10, step=1)
            
        dias_aula = st.text_input("Dias de Aula (ex: Ter/Qui):")
        horario_escolhido = st.text_input("Horário Escolhido (ex: 19:30):")
        
        botao_validar = st.form_submit_button("Validar Dados")
        
        if botao_validar:
            if nome_completo and whatsapp:
                st.success(f"🎉 Dados validados para **{nome_completo}**!")
                nova_linha = {
                    "Nome": nome_completo, "Telefone": whatsapp, "Bairro": bairro,
                    "Plano": modalidade, "Valor": preco_mensal, "Vencimento": dia_vencimento,
                    "Dias": dias_aula, "Horario": horario_escolhido, "Status": "Ativo"
                }
                st.json(nova_linha)
            else:
                st.error("⚠️ Preencha os campos obrigatórios (Nome e WhatsApp).")
