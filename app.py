import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# Configuração da página do Streamlit
st.set_page_config(page_title="Studio Highline - Gestão", layout="wide", page_icon="🏋️‍♂️")

# Título Lateral (Sidebar)
st.sidebar.markdown("# 🏋️‍♂️ Studio Highline")
st.sidebar.markdown("### Painel de Controle v1.0")

# Data e Hora Atual
data_atual = datetime.now().strftime("%d/%m/%Y")
hora_atual = datetime.now().strftime("%H:%M")
st.sidebar.info(f"📅 **Data de hoje:** {data_atual}\n\n🕒 **Hora:** {hora_atual}")

# Conexão com o Google Sheets
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # Lendo as abas exatas da planilha: alunos, financeiro e espera
    df_alunos = conn.read(worksheet="alunos")
    df_financeiro = conn.read(worksheet="financeiro")
    df_espera = conn.read(worksheet="espera")
    
    st.sidebar.success("✅ Banco de dados sincronizado!")
except Exception as e:
    st.sidebar.error("❌ Erro na sincronização dos dados.")
    st.error(f"Erro ao ler as abas da planilha. Verifique as credenciais ou a conexão. Detalhes: {e}")
    st.stop()

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
    st.markdown("Abaixo estão listados os treinos e agendamentos para o período:")
    
    if not df_alunos.empty and "Horario" in df_alunos.columns:
        # Filtrando apenas quem tem status ativo para a agenda
        if "Status" in df_alunos.columns:
            df_hoje = df_alunos[df_alunos["Status"].astype(str).str.upper() == "ATIVO"]
        else:
            df_hoje = df_alunos
        
        if not df_hoje.empty:
            # Ordenar por horário para organizar a agenda do dia
            df_hoje = df_hoje.sort_values(by="Horario")
            
            # Mostrar colunas principais de interesse para o dia a dia
            colunas_agenda = [c for c in ["Horario", "Nome", "Status", "Queixa", "Conduta", "Dias"] if c in df_hoje.columns]
            st.dataframe(df_hoje[colunas_agenda], use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum registro de treino ativo localizado para hoje.")
    else:
        st.info("Insira dados na planilha para visualizar a agenda de treinos.")

# ==========================================
# 2. ABA: ALUNOS ATIVOS
# ==========================================
with tab_alunos:
    st.subheader("👥 Controle de Alunos")
    
    # Filtrar ativos com base na coluna Status
    if "Status" in df_alunos.columns:
        df_ativos = df_alunos[df_alunos["Status"].astype(str).str.upper() == "ATIVO"]
    else:
        df_ativos = df_alunos

    total_matriculados = len(df_ativos)
    
    # Exibir métrica de alunos ativos
    st.metric(label="Total de Alunos Matriculados", value=total_matriculados)
    
    # Campo de busca por nome
    busca_nome = st.text_input("🔍 Buscar aluno pelo nome:", placeholder="Digite o nome do aluno...")
    
    if busca_nome:
        df_filtrado = df_ativos[df_ativos["Nome"].astype(str).str.contains(busca_nome, case=False, na=False)]
    else:
        df_filtrado = df_ativos

    st.dataframe(df_filtrado, use_container_width=True, hide_index=True)
    
    # Área de Ações (Desativar Aluno)
    st.markdown("### ⚙️ Ações de Gerenciamento")
    if not df_ativos.empty and "Nome" in df_ativos.columns:
        aluno_para_desativar = st.selectbox(
            "Selecione o aluno para desativar:", 
            df_ativos["Nome"].tolist(), 
            key="selectbox_desativar"
        )
        
        if st.button("Confirmar Desativação", type="secondary"):
            st.warning(f"Ação solicitada para desativar: {aluno_para_desativar}. Para salvar de volta no Google Sheets, lembre-se de implementar a função de escrita `conn.update()`.")
    else:
        st.write("Nenhum aluno ativo disponível para ações.")

# ==========================================
# 3. ABA: RELATÓRIO FINANCEIRO
# ==========================================
with tab_financeiro:
    st.subheader("📊 Relatório Financeiro")
    
    if not df_financeiro.empty:
        # CORREÇÃO DA INDENTAÇÃO DA LINHA 117/118 AQUI:
        if "Valor" in df_financeiro.columns:
            # Limpa formatação de moeda para somar os valores corretamente
            valores = pd.to_numeric(df_financeiro["Valor"].astype(str).str.replace("R$", "").str.replace(".", "").str.replace(",", ".").str.strip(), errors="coerce")
            faturamento_total = valores.sum()
            
            # Exibe o valor formatado em Reais (R$)
            valor_formatado = f"R$ {faturamento_total:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")
            st.metric(label="Faturamento Estimado", value=valor_formatado)
        else:
            st.info("Coluna 'Valor' não encontrada na aba financeiro.")
        
        st.dataframe(df_financeiro, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum registro financeiro localizado.")

# ==========================================
# 4. ABA: LISTA DE ESPERA
# ==========================================
with tab_espera:
    st.subheader("⏳ Lista de Espera")
    
    # Atualiza contadores na barra lateral baseados nos dados reais das abas
    st.sidebar.metric(label="Alunos Ativos", value=total_matriculados)
    st.sidebar.metric(label="Fila de Espera", value=len(df_espera))

    if not df_espera.empty:
        st.dataframe(df_espera, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum aluno na fila de espera no momento.")

# ==========================================
# 5. ABA: NOVOS CADASTROS (GERADOR DE CARGA)
# ==========================================
with tab_novos:
    st.subheader("➕ Gerador de Carga para Novos Alunos")
    st.markdown("Preencha o formulário abaixo para validar e gerar a linha perfeitamente formatada para o Google Sheets.")
    
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
                st.success(f"🎉 Dados validados com sucesso para **{nome_completo}**!")
                
                # Estrutura mapeando as colunas da sua planilha Banco Highline
                nova_linha = {
                    "Nome": nome_completo,
                    "Telefone": whatsapp,
                    "Bairro": bairro,
                    "Plano": modalidade,
                    "Valor": preco_mensal,
                    "Vencimento": dia_vencimento,
                    "Dias": dias_aula,
                    "Horario": horario_escolhido,
                    "Status": "Ativo"
                }
                st.json(nova_linha)
                st.info("💡 Pronto! Os dados acima estão estruturados.")
            else:
                st.error("⚠️ Por favor, preencha os campos obrigatórios (Nome Completo e WhatsApp).")
