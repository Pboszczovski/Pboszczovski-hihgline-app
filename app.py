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
    base_url = f"https://docs.google.com/spreadsheets/d/{PLANILHA_ID}/export?format=csv"
    try:
        df_alunos = pd.read_csv(f"{base_url}&gid=0", keep_default_na=False)
        df_financeiro = pd.read_csv(f"{base_url}&gid=1020408012", keep_default_na=False)
        df_espera = pd.read_csv(f"{base_url}&gid=1228435040", keep_default_na=False)
    except Exception:
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

if not conexao_ok:
    st.error(f"Erro crítico de conexão com o Google Sheets. Detalhes: {erro_msg}")
    st.stop()

# ==========================================
# 4. TRATAMENTO DAS TELAS
# ==========================================

# --- 1. TELA: AGENDA ---
if menu == "📅 Agenda":
    st.title("📅 Agenda de Treinos")
    
    hoje_mm_dd = datetime.now().strftime("%m-%d")
    niver_hoje = []
    
    if "Nascimento" in df_alunos.columns and "Nome" in df_alunos.columns:
        for idx, row in df_alunos.iterrows():
            try:
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
    if "Status" in df_alunos.columns:
        df_ativos = df_alunos[df_alunos["Status"].astype(str).str.upper() == "ATIVO"]
    else:
        df_ativos = df_alunos.copy()
        
    if not df_ativos.empty:
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
    if "Status" in df_alunos.columns:
        df_inativos = df_alunos[df_alunos["Status"].astype(str).str.upper() != "ATIVO"]
        st.metric("Total de Alunos no Arquivo Morto", len(df_inativos))
        st.dataframe(df_inativos, use_container_width=True, hide_index=True)
    else:
        st.info("A coluna 'Status' não foi localizada.")

# --- 4. TELA: ESPERA ---
elif menu == "⏳ Espera":
    st.title("⏳ Lista de Espera")
    st.metric("Total de Clientes em Espera", len(df_espera))
    st.dataframe(df_espera, use_container_width=True, hide_index=True)

# --- 5. TELA: MAPA ---
elif menu == "🗺️ Mapa":
    st.title("🗺️ Mapa de Distribuição Geográfica")
    if "Bairro" in df_alunos.columns:
        df_bairros = df_alunos[df_alunos["Status"].astype(str).str.upper() == "ATIVO"] if "Status" in df_alunos.columns else df_alunos.copy()
        contagem = df_bairros["Bairro"].value_counts().reset_index()
        contagem.columns = ["Bairro", "Quantidade de Alunos"]
        st.bar_chart(data=contagem, x="Bairro", y="Quantidade de Alunos")
        st.dataframe(contagem, use_container_width=True, hide_index=True)

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
                st.markdown(f"🧬 **Gênero:** {ficha.get('Genero', 'N/D')}")
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
                st.subheader("📋 Queixa Principal / Histórico (Anamnese)")
                st.info(ficha.get('Queixa', 'Nenhum registro de queixa adicionado.'))
            with col_c:
                st.subheader("🛠️ Conduta Clínica-Desportiva")
                st.success(ficha.get('Conduta', 'Nenhuma conduta desenhada para este aluno.'))

# --- 7. TELA: CADASTRO COM ANAMNESE ---
elif menu == "📝 Cadastro":
    st.title("📝 Cadastro e Ficha de Anamnese")
    st.markdown("Insira os dados completos do aluno para gerar a linha estruturada na ordem correta das colunas da planilha.")
    
    with st.form("form_novo_aluno_anamnese"):
        st.subheader("1. Dados Pessoais e de Contato")
        nome_c = st.text_input("Nome Completo:")
        tel_c = st.text_input("WhatsApp com DDD (Ex: 11999998888):")
        bairro_c = st.text_input("Bairro de Residência:")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            genero_c = st.selectbox("Gênero:", ["Masculino", "Feminino", "Outro"])
            nasc_c = st.text_input("Data de Nascimento (DD/MM/AAAA):")
        with col2:
            plano_c = st.selectbox("Plano Contratado:", ["Mensal", "Trimestral", "Semestral", "Anual"])
            valor_c = st.text_input("Valor Combinado (R$):", value="150,00")
        with col3:
            venc_c = st.number_input("Dia de Vencimento Mensal:", min_value=1, max_value=31, value=10)
            inicio_c = st.text_input("Data de Início das Aulas (DD/MM/AAAA):", value=datetime.now().strftime("%d/%m/%Y"))
            
        st.subheader("2. Planejamento de Horários")
        col_dias, col_hora = st.columns(2)
        with col_dias:
            dias_c = st.text_input("Dias de Aula Fixados (Ex: Ter/Qui ou Seg/Qua/Sex):")
        with col_hora:
            horario_c = st.text_input("Horário Escolhido (Ex: 08:30):")
            
        st.subheader("3. Ficha de Anamnese Clínica")
        queixa_c = st.text_area("Queixa Principal / Histórico de Lesões / Objetivos:", placeholder="Descreva os problemas de coluna, articulações, dores ou limitações físicas relatadas pelo aluno...")
        conduta_c = st.text_area("Conduta Clínica-Desportiva / Restrições / Exercícios Recomendados:", placeholder="Prescreva as diretrizes do treino, limitações de carga, movimentos proibidos ou foco especial do tratamento...")
        
        if st.form_submit_button("Validar e Gerar Linha de Cadastro"):
            if nome_c and tel_c:
                st.success("🎉 Cadastro e Ficha de Anamnese gerados! Copie o código abaixo e cole na última linha vazia da sua aba 'Alunos':")
                
                # Monta a string CSV respeitando estritamente a sequência de colunas:
                # Nome, Telefone, Bairro, Plano, Valor, Vencimento, Dias, Horario, Status, Queixa, Conduta, Genero, Nascimento, Inicio_Aulas
                linha_csv = f'"{nome_c}","{tel_c}","{bairro_c}","{plano_c}","{valor_c}",{venc_c},"{dias_c}","{horario_c}","Ativo","{queixa_c}","{conduta_c}","{genero_c}","{nasc_c}","{inicio_c}"'
                st.code(linha_csv, language="text")
            else:
                st.error("Erro: Os campos 'Nome' e 'WhatsApp' são obrigatórios para validar o registro.")

# --- 8. TELA: FINANCEIRO ---
elif menu == "💰 Financeiro":
    st.title("💰 Relatório e Movimentação Financeira")
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
    if "Plano" in df_alunos.columns and "Valor" in df_alunos.columns:
        df_precos = df_alunos.groupby("Plano")["Valor"].unique().reset_index()
        df_precos["Valores Praticados"] = df_precos["Valor"].apply(lambda x: ", ".join([str(i) for i in x if i != ""]))
        st.table(df_precos[["Plano", "Valores Praticados"]])
    else:
        st.info("Dados insuficientes para gerar relatório de preços.")
