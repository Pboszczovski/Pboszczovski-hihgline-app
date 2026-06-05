import streamlit as st
import pandas as pd
from datetime import datetime

# ==========================================
# 1. CONFIGURAÇÃO DE IDENTIDADE VISUAL (CSS)
# ==========================================
st.set_page_config(page_title="Highline Management", layout="wide", page_icon="🏋️‍♂️")

# Restaura o fundo verde escuro na barra lateral idêntico ao original da foto
st.markdown("""
    <style>
        [data-testid="stSidebar"] {
            background-color: #2E5A44 !important;
        }
        [data-testid="stSidebar"] * {
            color: white !important;
        }
        .stRadio input[type="radio"]:checked + div {
            color: #FFD700 !important; /* Destaque dourado na opção selecionada */
            font-weight: bold !important;
        }
        div.stAlert {
            background-color: #E8F5E9 !important;
            border-left: 5px solid #2E5A44 !important;
            color: #1B5E20 !important;
        }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. CONEXÃO E CARREGAMENTO DE DADOS
# ==========================================
PLANILHA_ID = "130igffmPV0Eu8qzEpQC3g1ReKbb2lO01iZgWXSzFRhw"

@st.cache_data(ttl=30, show_spinner="Sincronizando com o Banco Highline...")
def carregar_dados():
    # URL de exportação nativa do Google Drive (Evita Erro 404 de API)
    base_url = f"https://docs.google.com/spreadsheets/d/{PLANILHA_ID}/export?format=csv"
    
    try:
        df_alunos = pd.read_csv(f"{base_url}&gid=0", keep_default_na=False)
        df_financeiro = pd.read_csv(f"{base_url}&gid=1020408012", keep_default_na=False)
        df_espera = pd.read_csv(f"{base_url}&gid=1228435040", keep_default_na=False)
    except Exception:
        # Contingência secundária usando a API gviz caso a primeira falhe
        alt_url = f"https://docs.google.com/spreadsheets/d/{PLANILHA_ID}/gviz/tq?tqx=out:csv"
        df_alunos = pd.read_csv(f"{alt_url}&gid=0", keep_default_na=False)
        df_financeiro = pd.read_csv(f"{alt_url}&gid=1020408012", keep_default_na=False)
        df_espera = pd.read_csv(f"{alt_url}&gid=1228435040", keep_default_na=False)
        
    return df_alunos, df_financeiro, df_espera

try:
    df_alunos, df_financeiro, df_espera = carregar_dados()
    conexao_ok = True
except Exception as e:
    conexao_ok = False
    erro_msg = str(e)

# ==========================================
# 3. BARRA LATERAL - MENU VERTICAL (FOTO)
# ==========================================
with st.sidebar:
    st.markdown("## 🏋️‍♂️ Studio Highline")
    st.markdown("🔒 **Menu de Navegação**")
    
    # Menu com as 9 opções exatamente na ordem da sua foto original
    menu = st.radio(
        "",
        [
            "📅 Agenda",
            "👥 Alunos",
            "📁 Arquivo Morto",
            "⏳ Espera",
            "🗺️ Mapa",
            "👤 Perfil",
            "📝 Cadastro",
            "💰 Financeiro",
            "⚙️ Preços"
        ]
    )
    
    st.markdown("---")
    data_hoje = datetime.now().strftime("%d/%m/%Y")
    st.write(f"📆 **Data:** {data_hoje}")
    if conexao_ok:
        st.success("● Banco de Dados Online")
    else:
        st.error("● Banco de Dados Offline")

# Interrompe a execução caso haja falha crítica na carga dos dados do Google Sheets
if not conexao_ok:
    st.error(f"Erro crítico de conexão com o Google Sheets. Detalhes: {erro_msg}")
    st.stop()

# ==========================================
# 4. TRATAMENTO COMPLETO DAS 9 TELAS
# ==========================================

# --- 1. TELA: AGENDA ---
if menu == "📅 Agenda":
    st.title("📅 Agenda de Treinos")
    
    # Bloco de Aniversariantes usando a coluna 'Nascimento' e 'Nome'
    hoje_mm_dd = datetime.now().strftime("%m-%d")
    niver_hoje = []
    
    if "Nascimento" in df_alunos.columns and "Nome" in df_alunos.columns:
        for idx, row in df_alunos.iterrows():
            try:
                # Trata formatações de data brasileiras (DD/MM/AAAA)
                data_nasc = pd.to_datetime(row["Nascimento"], dayfirst=True)
                if data_nasc.strftime("%m-%d") == hoje_mm_dd:
                    niver_hoje.append(row["Nome"])
            except:
                continue
                
    if niver_hoje:
        nomes_niver = ", ".join(niver_hoje)
        st.info(f"🎉 **Hoje é aniversário de:** {nomes_niver}! Não esqueça de dar os parabéns! 🎂")
    else:
        st.info("🎂 Nenhum aluno a fazer aniversário hoje.")
        
    st.markdown("### Horários Impulsionados para Hoje")
    
    # Filtra apenas os alunos ATIVOS para a Agenda do Dia
    if "Status" in df_alunos.columns:
        df_ativos = df_alunos[df_alunos["Status"].astype(str).str.upper() == "ATIVO"]
    else:
        df_ativos = df_alunos.copy()
        
    if not df_ativos.empty:
        # Ordena cronologicamente pelo Horário
        if "Horario" in df_ativos.columns:
            df_agenda = df_ativos.sort_values(by="Horario")
        else:
            df_agenda = df_ativos
            
        colunas_agenda = [c for c in ["Horario", "Nome", "Status", "Queixa", "Conduta", "Dias"] if c in df_agenda.columns]
        st.dataframe(df_agenda[colunas_agenda], use_container_width=True, hide_index=True)
    else:
        st.warning("Nenhum aluno ativo encontrado na base de dados.")

# --- 2. TELA: ALUNOS ---
elif menu == "👥 Alunos":
    st.title("👥 Base de Alunos Ativos")
    
    busca = st.text_input("🔍 Filtrar aluno por nome:", placeholder="Digite o nome completo ou parcial...")
    
    if "Status" in df_alunos.columns:
        df_ativos = df_alunos[df_alunos["Status"].astype(str).str.upper() == "ATIVO"]
    else:
        df_ativos = df_alunos.copy()
        
    if busca and "Nome" in df_ativos.columns:
        df_ativos = df_ativos[df_ativos["Nome"].astype(str).str.contains(busca, case=False, na=False)]
        
    st.metric("Total de Alunos Ativos Atualmente", len(df_ativos))
    st.dataframe(df_ativos, use_container_width=True, hide_index=True)

# --- 3. TELA: ARQUIVO MORTO ---
elif menu == "📁 Arquivo Morto":
    st.title("📁 Arquivo Morto")
    st.markdown("Exibição de alunos cujo status no sistema não esteja definido como 'Ativo' (Inativos, Desistentes ou Trancados).")
    
    if "Status" in df_alunos.columns:
        df_inativos = df_alunos[df_alunos["Status"].astype(str).str.upper() != "ATIVO"]
        st.metric("Total de Alunos no Arquivo Morto", len(df_inativos))
        st.dataframe(df_inativos, use_container_width=True, hide_index=True)
    else:
        st.info("A coluna 'Status' não foi localizada para processar o Arquivo Morto.")

# --- 4. TELA: ESPERA ---
elif menu == "⏳ Espera":
    st.title("⏳ Lista de Espera")
    st.markdown("Clientes em fila aguardando liberação de horários de atendimento.")
    
    st.metric("Total de Clientes em Espera", len(df_espera))
    st.dataframe(df_espera, use_container_width=True, hide_index=True)

# --- 5. TELA: MAPA ---
elif menu == "🗺️ Mapa":
    st.title("🗺️ Mapa de Distribuição Geográfica")
    st.markdown("Análise quantitativa de alunos ativos residentes por bairro.")
    
    if "Bairro" in df_alunos.columns:
        if "Status" in df_alunos.columns:
            df_bairros = df_alunos[df_alunos["Status"].astype(str).str.upper() == "ATIVO"]
        else:
            df_bairros = df_alunos.copy()
            
        contagem = df_bairros["Bairro"].value_counts().reset_index()
        contagem.columns = ["Bairro", "Quantidade de Alunos"]
        
        st.bar_chart(data=contagem, x="Bairro", y="Quantidade de Alunos")
        st.dataframe(contagem, use_container_width=True, hide_index=True)
    else:
        st.error("A coluna 'Bairro' não existe na planilha de alunos.")

# --- 6. TELA: PERFIL ---
elif menu == "👤 Perfil":
    st.title("👤 Ficha Clínica-Desportiva Analítica")
    
    if "Nome" in df_alunos.columns:
        aluno_sel = st.selectbox("Selecione um aluno para extrair o prontuário completo:", df_alunos["Nome"].tolist())
        
        if aluno_sel:
            ficha = df_alunos[df_alunos["Nome"] == aluno_sel].iloc[0]
            
            st.markdown(f"## Ficha de: {aluno_sel}")
            st.markdown("---")
            
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"📞 **Telefone:** {ficha.get('Telefone', 'N/D')}")
                st.markdown(f"🏡 **Bairro:** {ficha.get('Bairro', 'N/D')}")
                st.markdown(f"🧬 **Género:** {ficha.get('Genero', 'N/D')}")
            with c2:
                st.markdown(f"📅 **Nascimento:** {ficha.get('Nascimento', 'N/D')}")
                st.markdown(f"🚀 **Início das Aulas:** {ficha.get('Inicio_Aulas', 'N/D')}")
                st.markdown(f"💎 **Plano:** {ficha.get('Plano', 'N/D')}")
            with c3:
                st.markdown(f"💰 **Valor Mensal:** {ficha.get('Valor', 'N/D')}")
                st.markdown(f"📆 **Vencimento:** Dia {ficha.get('Vencimento', 'N/D')}")
                st.markdown(f"⚡ **Status:** {ficha.get('Status', 'N/D')}")
                
            st.markdown("---")
            col_q, col_c = st.columns(2)
            with col_q:
                st.subheader("📋 Queixa Principal / Histórico")
                st.info(ficha.get('Queixa', 'Nenhum registo de queixa adicionado.'))
            with col_c:
                st.subheader("🛠️ Conduta Clínica-Desportiva")
                st.success(ficha.get('Conduta', 'Nenhuma conduta desenhada para este aluno.'))
    else:
        st.error("Coluna 'Nome' ausente.")

# --- 7. TELA: CADASTRO ---
elif menu == "📝 Cadastro":
    st.title("📝 Cadastro de Novo Aluno")
    st.markdown("Preencha as informações para estruturar a linha de dados formatada para a planilha Alunos:")
    
    with st.form("form_novo_aluno"):
        nome_c = st.text_input("Nome Completo:")
        tel_c = st.text_input("WhatsApp com DDD (Ex: 11999998888):")
        bairro_c = st.text_input("Bairro:")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            plano_c = st.selectbox("Plano Contratado:", ["Mensal", "Trimestral", "Semestral", "Anual"])
            genero_c = st.selectbox("Género:", ["Masculino", "Feminino", "Outro"])
        with col2:
            valor_c = st.text_input("Valor Combinado (R$):", value="150,00")
            nasc_c = st.text_input("Data de Nascimento (DD/MM/AAAA):")
        with col3:
            venc_c = st.number_input("Dia de Vencimento:", min_value=1, max_value=31, value=10)
            inicio_c = st.text_input("Data de Início (DD/MM/AAAA):", value=datetime.now().strftime("%d/%m/%Y"))
            
        dias_c = st.text_input("Dias de Aula (Ex: Seg/Qua/Sex):")
        horario_c = st.text_input("Horário Escolhido (Ex: 08:00):")
        
        if st.form_submit_button("Gerar Registro em Linha"):
            if nome_c and tel_c:
                st.success("🎉 Linha estruturada com sucesso! Copie e cole na última linha da aba 'Alunos':")
                # Monta a string CSV exatamente na ordem das colunas fornecidas pelo usuário
                linha_csv = f"{nome_c},{tel_c},{bairro_c},{plano_c},{valor_c},{venc_c},{dias_c},{horario_c},Ativo,,,,{genero_c},{nasc_c},{inicio_c}"
                st.code(linha_csv, language="text")
            else:
                st.error("Erro: Os campos 'Nome' e 'WhatsApp' são estritamente obrigatórios.")

# --- 8. TELA: FINANCEIRO ---
elif menu == "💰 Financeiro":
    st.title("💰 Relatório e Movimentação Financeira")
    
    # Processamento analítico da coluna 'Valor' da tabela financeira
    if "Valor" in df_financeiro.columns:
        valores_limpos = df_financeiro["Valor"].astype(str).str.replace("R$", "", regex=False)
        valores_limpos = valores_limpos.str.replace(".", "", regex=False).str.replace(",", ".", regex=False).str.strip()
        valores_numericos = pd.to_numeric(valores_limpos, errors="coerce")
        
        faturamento_total = valores_numericos.sum()
        valor_formatado = f"R$ {faturamento_total:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")
        st.metric(label="Faturamento Total Acumulado", value=valor_formatado)
        
    st.dataframe(df_financeiro, use_container_width=True, hide_index=True)

# --- 9. TELA: PREÇOS ---
elif menu == "⚙️ Preços":
    st.title("⚙️ Tabela de Preços e Modelos de Planos")
    st.markdown("Análise comparativa de valores praticados atualmente por tipo de contrato.")
    
    if "Plano" in df_alunos.columns and "Valor" in df_alunos.columns:
        # Agrupa os valores únicos cobrados por plano para auditoria de preços
        df_precos = df_alunos.groupby("Plano")["Valor"].unique().reset_index()
        df_precos["Valores Praticados"] = df_precos["Valor"].apply(lambda x: ", ".join([str(i) for i in x if i != ""]))
        st.table(df_precos[["Plano", "Valores Praticados"]])
    else:
        st.info("Dados de planos insuficientes na tabela de alunos para gerar o relatório de auditoria.")
