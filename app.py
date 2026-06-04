import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# 1. CONFIGURAÇÕES DA PÁGINA E IDENTIDADE VISUAL
st.set_page_config(
    page_title="Studio Highline - Gestão Integrada",
    page_icon="🏋️‍♂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS Customizada para o Layout Premium do Studio
st.markdown("""
<style>
    .main { background-color: #f8fafc; }
    .stTabs [data-baseweb="tab"] {
        font-size: 15px;
        font-weight: 600;
        height: 48px;
        padding: 0px 20px;
    }
    div[data-testid="stMetricValue"] {
        font-size: 36px;
        color: #1e3a8a;
        font-weight: 700;
    }
    .metric-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        border-left: 5px solid #1e3a8a;
        margin-bottom: 15px;
    }
    .cadastro-header {
        color: #1e3a8a;
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# 2. SISTEMA DE CONEXÃO DE DADOS (PANDAS DIRECT LINK)
SPREADSHEET_ID = "13OigffmPV0Eu8qzEpQC3g1ReKbb2lO01iZgWXSzFRhw"

@st.cache_data(ttl=5)
def carregar_aba_planilha(nome_aba):
    # Conexão direta via exportação CSV para evitar falhas de módulos externos
    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&sheet={nome_aba}"
    try:
        df = pd.read_csv(url)
        # Limpeza de linhas e colunas completamente nulas
        df = df.dropna(how='all', axis=1).dropna(how='all', axis=0)
        # Padronização de nomes de colunas sem espaços extras
        df.columns = [c.strip() for c in df.columns]
        return df
    except Exception as e:
        return pd.DataFrame()

# Importação síncrona das 3 tabelas operacionais
df_alunos = carregar_aba_planilha("alunos")
df_financeiro = carregar_aba_planilha("financeiro")
df_espera = carregar_aba_planilha("espera")

# Mapeador de segurança para integridade das colunas do sistema
def assegurar_estrutura(df, colunas_obrigatorias):
    if df.empty:
        return pd.DataFrame(columns=colunas_obrigatorias)
    for col in colunas_obrigatorias:
        if col not in df.columns:
            df[col] = ""
    return df

# Tratamento das colunas idênticas às do seu Google Sheets
df_alunos = assegurar_estrutura(df_alunos, ['Nome', 'Telefone', 'Bairro', 'Plano', 'Valor', 'Vencimento', 'Dias', 'Horario', 'Status', 'Queixa', 'Conduta', 'Genero', 'Nascimento', 'Inicio_Aulas'])
df_financeiro = assegurar_estrutura(df_financeiro, ['Data', 'Descricao', 'Valor', 'Tipo', 'Categoria'])
df_espera = assegurar_estrutura(df_espera, ['Nome', 'Telefone', 'Horario_Desejado', 'Data_Entrada', 'Notas'])


# 3. BARRA LATERAL DINÂMICA (SIDEBAR)
st.sidebar.title("Studio Highline")
st.sidebar.markdown("**Painel de Controle v1.0**")
st.sidebar.markdown("---")

# Seção de Horário e Data em tempo real
agora = datetime.now()
data_formatada = agora.strftime('%d/%m/%Y')
hora_formatada = agora.strftime('%H:%M')

st.sidebar.markdown(f"""
<div style="background-color: #e0f2fe; padding: 12px; border-radius: 8px; margin-bottom: 20px;">
    <span style="color: #0369a1; font-weight: bold;">📅 Data:</span> {data_formatada} 
    <br>
    <span style="color: #0369a1; font-weight: bold;">🕒 Hora:</span> {hora_formatada}
</div>
""", unsafe_allow_html=True)

# Processamento de métricas rápidas da Barra Lateral
if not df_alunos.empty and 'Status' in df_alunos.columns:
    contagem_ativos = len(df_alunos[df_alunos['Status'].str.lower() == 'ativo'])
else:
    contagem_ativos = 0

contagem_espera = len(df_espera) if not df_espera.empty else 0

st.sidebar.markdown("<p style='margin-bottom: -5px; font-weight: 500;'>Alunos Ativos</p>", unsafe_allow_html=True)
st.sidebar.markdown(f"<p style='font-size: 36px; font-weight: bold; color: #1e3a8a; margin-top: 0px;'>{contagem_ativos}</p>", unsafe_allow_html=True)

st.sidebar.markdown("<p style='margin-bottom: -5px; font-weight: 500;'>Fila de Espera</p>", unsafe_allow_html=True)
st.sidebar.markdown(f"<p style='font-size: 36px; font-weight: bold; color: #1e3a8a; margin-top: 0px;'>{contagem_espera}</p>", unsafe_allow_html=True)

st.sidebar.markdown("---")
if not df_alunos.empty:
    st.sidebar.markdown("""
    <div style="background-color: #fef08a; padding: 10px; border-radius: 6px; color: #854d0e; font-size: 13px; font-weight: 500;">
        ⚠️ Planilha conectada, mas sem registros ativos.
    </div>
    """, unsafe_allow_html=True)
else:
    st.sidebar.markdown("""
    <div style="background-color: #fee2e2; padding: 10px; border-radius: 6px; color: #991b1b; font-size: 13px; font-weight: 500;">
        ❌ Aguardando carga de dados do Google Sheets.
    </div>
    """, unsafe_allow_html=True)


# 4. CORPO PRINCIPAL E NAVEGAÇÃO POR ABAS
st.markdown("# 🏋️‍♂️ Sistema de Gestão Integrada")
st.markdown("Controle operacional, financeiro e clínico-desportivo do Studio Highline.")
st.markdown("---")

# Geração das 5 Abas Originais
tab_agenda, tab_alunos, tab_financeiro, tab_espera, tab_cadastro = st.tabs([
    "🗓️ Agenda do Dia", 
    "👥 Alunos Ativos", 
    "📊 Relatório Financeiro", 
    "⏳ Lista de Espera", 
    "➕ Novos Cadastros"
])


# --- ABA 1: AGENDA DO DIA ---
with tab_agenda:
    st.subheader("🗓️ Agendamentos e Horários Disponíveis")
    st.markdown("Consulte os fluxos de alunos distribuídos por faixas de horários e dias da semana.")
    
    if df_alunos.empty:
        st.info("Nenhum registro encontrado para estruturar a agenda.")
    else:
        # Filtros Avançados Combinados
        fil1, fil2, fil3 = st.columns(3)
        with fil1:
            dias_disponiveis = ["Todos"] + list(df_alunos['Dias'].dropna().unique())
            f_dia = st.selectbox("Filtrar por Dia da Semana:", dias_disponiveis, key="agenda_dia")
        with fil2:
            horas_disponiveis = ["Todos"] + sorted(list(df_alunos['Horario'].dropna().unique()))
            f_hora = st.selectbox("Filtrar por Faixa Horária:", horas_disponiveis, key="agenda_hora")
        with fil3:
            status_disponiveis = ["Todos"] + list(df_alunos['Status'].dropna().unique())
            f_status = st.selectbox("Filtrar por Situação/Status:", status_disponiveis, key="agenda_status")
            
        df_filtrado_agenda = df_alunos.copy()
        if f_dia != "Todos":
            df_filtrado_agenda = df_filtrado_agenda[df_filtrado_agenda['Dias'] == f_dia]
        if f_hora != "Todos":
            df_filtrado_agenda = df_filtrado_agenda[df_filtrado_agenda['Horario'] == f_hora]
        if f_status != "Todos":
            df_filtrado_agenda = df_filtrado_agenda[df_filtrado_agenda['Status'] == f_status]
            
        st.markdown(f"### Visualização dos Treinos Filtrados ({len(df_filtrado_agenda)})")
        st.dataframe(df_filtrado_agenda[['Nome', 'Horario', 'Dias', 'Plano', 'Telefone', 'Status']], use_container_width=True)


# --- ABA 2: GESTÃO E FICHA DE ALUNOS ---
with tab_alunos:
    st.subheader("👥 Fichas Cadastrais e Prontuários")
    
    if df_alunos.empty:
        st.info("A base de dados de alunos está vazia.")
    else:
        # Sistema de busca por texto e gênero
        col_busca1, col_busca2 = st.columns([3, 1])
        with col_busca1:
            termo_busca = st.text_input("🔍 Pesquisar Aluno (Nome Completo ou Parcial):", "")
        with col_busca2:
            generos = ["Todos"] + list(df_alunos['Genero'].dropna().unique())
            f_genero = st.selectbox("Filtrar por Gênero:", generos)
            
        df_mestre_alunos = df_alunos.copy()
        if termo_busca:
            df_mestre_alunos = df_mestre_alunos[df_mestre_alunos['Nome'].str.contains(termo_busca, case=False, na=False)]
        if f_genero != "Todos":
            df_mestre_alunos = df_mestre_alunos[df_mestre_alunos['Genero'] == f_genero]
            
        st.markdown("### 🗃️ Base Geral de Alunos")
        st.dataframe(df_mestre_alunos, use_container_width=True)
        
        # Módulo Clínico Avançado (Queixas e Condutas Específicas)
        st.markdown("---")
        st.subheader("🩺 Inspeção de Prontuário Clínico-Desportivo")
        aluno_alvo = st.selectbox("Selecione um aluno para expandir o prontuário de restrições e anamnese:", ["-- Selecione --"] + list(df_mestre_alunos['Nome'].unique()))
        
        if aluno_alvo != "-- Selecione --":
            ficha_aluno = df_mestre_alunos[df_mestre_alunos['Nome'] == aluno_alvo].iloc[0]
            cq1, cq2 = st.columns(2)
            with cq1:
                st.markdown(f"""
                <div style="background-color:#fee2e2; padding:15px; border-radius:8px; border-left:6px solid #ef4444;">
                    <h4 style="margin-top:0; color:#991b1b;">⚠️ Histórico de Queixas / Dores</h4>
                    <p style="color:#7f1d1d; font-size:15px;">{ficha_aluno['Queixa'] if pd.notna(ficha_aluno['Queixa']) and ficha_aluno['Queixa'] != '' else 'Nenhuma queixa ou patologia registrada.'}</p>
                </div>
                """, unsafe_allow_html=True)
            with cq2:
                st.markdown(f"""
                <div style="background-color:#dcfce7; padding:15px; border-radius:8px; border-left:6px solid #22c55e;">
                    <h4 style="margin-top:0; color:#166534;">📋 Conduta Técnica / Restrições de Exercício</h4>
                    <p style="color:#14532d; font-size:15px;">{ficha_aluno['Conduta'] if pd.notna(ficha_aluno['Conduta']) and ficha_aluno['Conduta'] != '' else 'Livre para todas as modalidades sem restrições.'}</p>
                </div>
                """, unsafe_allow_html=True)


# --- ABA 3: INTELIGÊNCIA FINANCEIRA ---
with tab_financeiro:
    st.subheader("📊 Relatórios Financeiros e Estatísticas")
    
    # Bloco superior de Indicadores (KPIs)
    f_previsto = 0
    if 'Valor' in df_alunos.columns and not df_alunos.empty:
        # Tratamento completo de strings de moeda antes da soma
        valores_limpos = df_alunos['Valor'].astype(str).str.replace('R$', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip()
        f_previsto = pd.to_numeric(valores_limpos, errors='coerce').sum()
        
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Faturamento Mensal Estimado", f"R$ {f_previsto:,.2f}")
    with m2:
        t_medio = f_previsto / len(df_alunos) if len(df_alunos) > 0 else 0
        st.metric("Ticket Médio Geral", f"R$ {t_medio:,.2f}")
    with m3:
        st.metric("Lançamentos de Caixa", len(df_financeiro) if not df_financeiro.empty else 0)
        
    st.markdown("---")
    
    # Gráficos de Inteligência de Mercado
    g1, g2 = st.columns(2)
    with g1:
        st.markdown("#### 📦 Distribuição por Modalidade de Planos")
        if not df_alunos.empty and 'Plano' in df_alunos.columns:
            df_planos = df_alunos['Plano'].value_counts().reset_index()
            df_planos.columns = ['Plano', 'Alunos']
            fig1 = px.pie(df_planos, values='Alunos', names='Plano', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.info("Sem dados para exibição do gráfico de planos.")
            
    with g2:
        st.markdown("#### 📈 Fluxo Recente do Extrato de Finanças")
        if not df_financeiro.empty:
            st.dataframe(df_financeiro, use_container_width=True)
        else:
            st.info("Aba 'financeiro' não possui dados inseridos.")


# --- ABA 4: LISTA DE ESPERA ---
with tab_espera:
    st.subheader("⏳ Controle de Clientes em Espera")
    if df_espera.empty or len(df_espera) == 0:
        st.success("🎉 Ninguém aguardando! Todos os clientes em fila foram alocados nos horários.")
    else:
        st.warning(f"Atenção: Há {len(df_espera)} clientes aguardando abertura de vagas.")
        st.dataframe(df_espera, use_container_width=True)


# --- ABA 5: GERADOR DE CARGA PARA NOVOS CADASTROS ---
with tab_cadastro:
    st.markdown('<div class="cadastro-header">🏋️‍♂️ Gerador de Carga para Novos Alunos</div>', unsafe_allow_html=True)
    st.markdown("Preencha o formulário abaixo para validar e gerar a linha perfeitamente formatada para o Google Sheets.")
    
    # Formulário idêntico à interface original da imagem enviada
    with st.form("formulario_cadastro_highline", clear_on_submit=True):
        input_nome = st.text_input("Nome Completo:")
        input_tel = st.text_input("WhatsApp com DDD:")
        input_bairro = st.text_input("Bairro:")
        
        # Grid de inputs triplos paralelos
        col_c1, col_c2, col_c3 = st.columns(3)
        with col_c1:
            input_plano = st.selectbox("Modalidade de Contrato", ["Mensal", "Trimestral", "Semestral", "Anual", "Check-in Avulso"])
        with col_c2:
            input_valor = st.number_input("Preço Mensal (R$):", min_value=0.0, value=150.0, step=5.0)
        with col_c3:
            input_vencimento = st.number_input("Dia do Vencimento:", min_value=1, max_value=31, value=10)
            
        # Grid de inputs duplos paralelos
        col_c4, col_c5 = st.columns(2)
        with col_c4:
            input_dias = st.text_input("Dias de Aula (ex: Ter/Qui):")
        with col_c5:
            input_horario = st.text_input("Horário Escolhido (ex: 19:30):")
            
        # Inputs de Texto Longo para Prontuário Médico-Desportivo
        input_queixa = st.text_area("Queixas Principais / Restrições Físicas:")
        input_conduta = st.text_area("Condutas e Exercícios Recomendados:")
        
        # Botão de submissão do formulário
        btn_gerar = st.form_submit_button("Validar Dados e Criar Registro")
        
        if btn_gerar:
            if not input_nome or not input_tel:
                st.error("❌ Os campos 'Nome Completo' e 'WhatsApp com DDD' são estritamente obrigatórios.")
            else:
                st.success("💪 Dados validados com sucesso! Copie o texto abaixo e cole na próxima linha livre da aba 'alunos' do Sheets:")
                # Formatação em formato CSV nativo de linha
                linha_gerada = f"{input_nome},{input_tel},{input_bairro},{input_plano},{input_valor},{input_vencimento},{input_dias},{input_horario},Ativo,{input_queixa},{input_conduta}"
                st.code(linha_gerada, language="text")
