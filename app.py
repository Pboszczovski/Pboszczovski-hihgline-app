import streamlit as st
import pandas as pd
from datetime import datetime

# ==========================================
# 1. CONFIGURAÇÃO DE IDENTIDADE VISUAL (CSS)
# ==========================================
st.set_page_config(page_title="Highline Management", layout="wide", page_icon="🏋️‍♂️")

# Aplica a cor verde escura na barra lateral para voltar ao design original
st.markdown("""
    <style>
        [data-testid="stSidebar"] {
            background-color: #2E5A44 !important;
        }
        [data-testid="stSidebar"] * {
            color: white !important;
        }
        .stRadio input[type="radio"]:checked + div {
            color: #FFD700 !important; /* Destaque dourado no menu selecionado */
        }
        div.stAlert {
            background-color: #E8F5E9 !important;
            border-left: 5px solid #2E5A44 !important;
            color: #1B5E20 !important;
        }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. CONEXÃO E CARREGAMENTO DE DADOS (ROBUSTO)
# ==========================================
PLANILHA_ID = "130igffmPV0Eu8qzEpQC3g1ReKbb2lO01iZgWXSzFRhw"

@st.cache_data(ttl=30, show_spinner="Sincronizando com o Banco Highline...")
def carregar_dados():
    # Endpoints de contingência (Tenta formato export, se falhar usa gviz)
    base_url = f"https://docs.google.com/spreadsheets/d/{PLANILHA_ID}/export?format=csv"
    
    try:
        df_alunos = pd.read_csv(f"{base_url}&gid=0", keep_default_na=False)
        df_financeiro = pd.read_csv(f"{base_url}&gid=1020408012", keep_default_na=False)
        df_espera = pd.read_csv(f"{base_url}&gid=1228435040", keep_default_na=False)
    except Exception:
        # Alternativa caso o Google Sheets bloqueie o endpoint de exportação
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
# 3. BARRA LATERAL - MENU ORIGINAL (FOTO)
# ==========================================
with st.sidebar:
    st.markdown("## 🏋️‍♂️ Studio Highline")
    st.markdown("🔒 **Menu de Navegação**")
    
    # Menu vertical exatamente igual ao da foto enviada
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
    # Indicadores de Sistema na parte inferior da barra
    data_hoje = datetime.now().strftime("%d/%m/%Y")
    st.write(f"📆 **Data:** {data_hoje}")
    if conexao_ok:
        st.success("● Banco de Dados Online")
    else:
        st.error("● Banco de Dados Offline")

# Bloqueio de segurança caso a planilha falhe
if not conexao_ok:
    st.error(f"Erro crítico de conexão com o Google Sheets. Detalhes: {erro_msg}")
    st.stop()

# ==========================================
# 4. LÓGICA DAS TELAS DO SISTEMA
# ==========================================

# --- TELA: AGENDA ---
if menu == "📅 Agenda":
    st.title("📅 Agenda de Treinos")
    
    # Bloco de Aniversariantes do Dia (Igual ao Alerta Verde da foto)
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
        st.info("🎂 Nenhum aluno fazendo aniversário hoje.")
        
    st.markdown("### Horários Impulsionados para Hoje")
    # Filtra apenas quem está Ativo e ordena pelo Horário da Aula
    df_ativos = df_alunos[df_alunos["Status"].astype(str).str.upper() == "ATIVO"]
    if not df_ativos.empty:
        df_agenda = df_ativos.sort_values(by="Horario")
        colunas_visiveis = [c for c in ["Horario", "Nome", "Status", "Queixa", "Conduta", "Dias"] if c in df_agenda.columns]
        st.dataframe(df_agenda[colunas_visiveis], use_container_width=True, hide_index=True)
    else:
        st.warning("Nenhum aluno com status 'Ativo' encontrado para montar a agenda.")

# --- TELA: ALUNOS ---
elif menu == "👥 Alunos":
    st.title("👥 Gestão de Alunos Ativos")
    
    busca = st.text_input("🔍 Pesquisar por nome do aluno:", placeholder="Digite para filtrar...")
    df_ativos = df_alunos[df_alunos["Status"].astype(str).str.upper() == "ATIVO"]
    
    if busca:
        df_ativos = df_ativos[df_ativos["Nome"].astype(str).str.contains(busca, case=False, na=False)]
        
    st.metric("Total de Alunos Ativos", len(df_ativos))
    st.dataframe(df_ativos, use_container_width=True, hide_index=True)

# --- TELA: ARQUIVO MORTO ---
elif menu == "📁 Arquivo Morto":
    st.title("📁 Arquivo Morto")
    st.markdown("Alunos com matrícula trancada, cancelada ou inativa.")
    
    df_inativos = df_alunos[df_alunos["Status"].astype(str).str.upper() != "ATIVO"]
    if not df_inativos.empty:
        st.dataframe(df_inativos, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum registro no arquivo morto.")

# --- TELA: ESPERA ---
elif menu == "⏳ Espera":
    st.title("⏳ Lista de Espera Operacional")
    st.metric("Total de Clientes aguardando vaga", len(df_espera))
    st.dataframe(df_espera, use_container_width=True, hide_index=True)

# --- TELA: MAPA ---
elif menu == "🗺️ Mapa":
    st.title("🗺️ Mapa de Distribuição por Bairro")
    if "Bairro" in df_alunos.columns:
        df_bairros = df_alunos[df_alunos["Status"].astype(str).str.upper() == "ATIVO"]
        contagem = df_bairros["Bairro"].value_counts().reset_index()
        contagem.columns = ["Bairro", "Quantidade de Alunos"]
        st.bar_chart(data=contagem, x="Bairro", y="Quantidade de Alunos")
        st.dataframe(contagem, use_container_width=True, hide_index=True)

# --- TELA: PERFIL ---
elif menu == "👤 Perfil":
    st.title("👤 Ficha Clínica-Desportiva do Aluno")
    aluno_sel = st.selectbox("Selecione um aluno para abrir o prontuário:", df_alunos["Nome"].tolist())
    
    if aluno_sel:
        ficha = df_alunos[df_alunos["Nome"] == aluno_sel].iloc[0]
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**Telefone:** {ficha.get('Telefone', 'Não informado')}")
            st.markdown(f"**Data de Início:** {ficha.get('Inicio_Aulas', 'Não informado')}")
            st.markdown(f"**Plano Contratado:** {ficha.get('Plano', 'Não informado')}")
        with c2:
            st.markdown(f"**Queixa Principal:**")
            st.warning(ficha.get('Queixa', 'Sem queixas registradas.'))
            st.markdown(f"**Conduta Adotada:**")
            st.info(ficha.get('Conduta', 'Sem condutas registradas.'))

# --- TELA: CADASTRO ---
elif menu == "📝 Cadastro":
    st.title("📝 Gerador de Carga para Novos Alunos")
    with st.form("novo_cadastro"):
        nome = st.text_input("Nome Completo:")
        tel = st.text_input("WhatsApp com DDD:")
        bairro = st.text_input("Bairro:")
        c1, c2 = st.columns(2)
        with c1:
            plano = st.selectbox("Plano:", ["Mensal", "Trimestral", "Semestral", "Anual"])
            horario = st.text_input("Horário da Aula (ex: 14:00):")
        with c2:
            valor = st.text_input("Valor da Mensalidade:")
            vencimento = st.number_input("Dia do Vencimento:", 1, 31, 10)
            
        if st.form_submit_button("Gerar Linha de Dados"):
            if nome and tel:
                st.success("Registro estruturado! Copie a linha abaixo e insira na planilha:")
                txt_linha = f"{nome},{tel},{bairro},{plano},{valor},{vencimento},,{horario},Ativo,,,"
                st.code(txt_linha, language="text")
            else:
                st.error("Preencha Nome e Telefone obrigatórios.")

# --- TELA: FINANCEIRO ---
elif menu == "💰 Financeiro":
    st.title("💰 Painel de Controle Financeiro")
    
    # Cálculo dinâmico usando a coluna "Valor" fornecida da aba financeira
    if "Valor" in df_financeiro.columns:
        valores_limpos = df_financeiro["Valor"].astype(str).str.replace("R$", "", regex=False)
        valores_limpos = valores_limpos.str.replace(".", "", regex=False).str.replace(",", ".", regex=False).str.strip()
        valores_num = pd.to_numeric(valores_limpos, errors="coerce")
        
        faturamento = valores_num.sum()
        st.metric(label="Faturamento Total Computado", value=f"R$ {faturamento:,.2f}".replace(",", "v").replace(".", ",").replace("v", "."))
        
    st.dataframe(df_financeiro, use_container_width=True, hide_index=True)

# --- TELA: PREÇOS ---
elif menu == "⚙️ Preços":
    st.title("⚙️ Tabela de Preços e Planos Vigentes")
    st.info("Esta tela exibe os valores de referência configurados para o Studio Highline.")
    # Exibe um resumo analítico baseado nos planos dos alunos cadastrados atualmente
    if "Plano" in df_alunos.columns and "Valor" in df_alunos.columns:
        df_precos = df_alunos.groupby("Plano")["Valor"].unique().reset_index()
        st.table(df_precos)
