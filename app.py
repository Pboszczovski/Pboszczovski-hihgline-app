import streamlit as st
import pandas as pd
from datetime import datetime

# ==========================================
# 1. CONFIGURAÇÃO DE IDENTIDADE VISUAL (CSS)
# ==========================================
st.set_page_config(page_title="Highline Management", layout="wide", page_icon="🏋️‍♂️")

# Mantém a barra lateral com o verde-escuro original da foto do seu app
st.markdown("""
    <style>
        [data-testid="stSidebar"] {
            background-color: #2E5A44 !important;
        }
        [data-testid="stSidebar"] * {
            color: white !important;
        }
        .stRadio input[type="radio"]:checked + div {
            color: #FFD700 !important;
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
# 3. BARRA LATERAL - MENU VERTICAL ORIGINAL
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
# 4. TRATAMENTO DAS TELAS DO APP
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
                # Exibe o CPF se a coluna existir na busca
                st.markdown(f"🪪 **CPF:** {ficha.get('CPF', 'N/D')}")
            with c2:
                st.markdown(f"📅 **Nascimento:** {ficha.get('Nascimento', 'N/D')}")
                st.markdown(f"🚀 **Início das Aulas:** {ficha.get('Inicio_Aulas', 'N/D')}")
                st.markdown(f"💎 **Plano:** {ficha.get('Plano', 'N/D')}")
            with c3:
                st.markdown(f"💰 **Valor Mensal:** {ficha.get('Valor', 'N/D')}")
                st.markdown(f"📆 **Vencimento:** Dia {ficha.get('Vencimento', 'N/D')}")
                st.markdown(f"⚡ **Status:** {ficha.get('Status', 'N/D')}")
            
            # Exibe o Endereço Completo se a coluna existir na busca
            st.markdown(f"📍 **Endereço Completo:** {ficha.get('Endereco', 'N/D')}")
            
            st.markdown("---")
            col_q, col_c = st.columns(2)
            with col_q:
                st.subheader("📋 Queixa Principal / Anamnese")
                st.info(ficha.get('Queixa', 'Nenhum registro adicionado.'))
            with col_c:
                st.subheader("🛠️ Conduta Clínica-Desportiva & Evolução")
                st.success(ficha.get('Conduta', 'Nenhuma conduta desenhada.'))

# --- 7. TELA: CADASTRO COM ANAMNESE, CPF E ENDEREÇO ---
elif menu == "📝 Cadastro":
    st.title("📝 Cadastro e Anamnese Estruturada")
    st.markdown("Selecione as opções clínicas correspondentes para gerar automaticamente a linha de dados formatada para o Google Sheets.")
    
    with st.form("form_novo_aluno_anamnese_avancada"):
        st.subheader("1. Dados Pessoais e de Contrato")
        nome_c = st.text_input("Nome Completo:")
        
        # Inclusão dos novos campos solicitados na interface
        col_id1, col_id2 = st.columns(2)
        with col_id1:
            tel_c = st.text_input("WhatsApp com DDD (Ex: 11999998888):")
        with col_id2:
            cpf_c = st.text_input("CPF (Ex: 000.000.000-00):")
            
        col_end1, col_end2 = st.columns([1, 2])
        with col_end1:
            bairro_c = st.text_input("Bairro de Residência:")
        with col_end2:
            endereco_c = st.text_input("Endereço Completo (Rua, Número, Complemento):")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            genero_c = st.selectbox("Gênero:", ["Masculino", "Feminino", "Outro"])
            nasc_c = st.text_input("Data de Nascimento (DD/MM/AAAA):")
        with col2:
            plano_c = st.selectbox("Plano Contratado:", ["1x semana", "2x semana", "3x semana", "Outro"])
            valor_c = st.text_input("Valor Combinado (R$):", value="220,00")
        with col3:
            venc_c = st.number_input("Dia de Vencimento Mensal:", min_value=1, max_value=31, value=10)
            inicio_c = st.text_input("Data de Início das Aulas (DD/MM/AAAA):", value=datetime.now().strftime("%d/%m/%Y"))
            
        st.subheader("2. Planejamento de Horários")
        col_dias, col_hora = st.columns(2)
        with col_dias:
            dias_c = st.text_input("Dias de Aula Fixados (Ex: Ter/Qui):")
        with col_hora:
            horario_c = st.text_input("Horário Escolhido (Ex: 08:30):")
            
        st.subheader("3. Anamnese: Queixas Principais e Sintomas (Múltipla Escolha)")
        st.markdown("###### Selecione todas as queixas clínicas relatadas pelo aluno:")
        
        col_q1, col_q2, col_q3 = st.columns(3)
        with col_q1:
            q_lombar = st.checkbox("Dor Lombar (Lombalgia)")
            q_cervical = st.checkbox("Dor Cervical (Cervicalgia)")
            q_hernia = st.checkbox("Hérnia de Disco / Protrusão")
            q_escoliose = st.checkbox("Escoliose / Desvios Posturais")
        with col_q2:
            q_joelho = st.checkbox("Dor / Lesão nos Joelhos")
            q_ombro = st.checkbox("Dor / Lesão nos Ombros")
            q_quadril = st.checkbox("Desconforto / Lesão no Quadril")
            q_artrose = st.checkbox("Artrose / Artrite / Osteopenia")
        with col_q3:
            q_postura = st.checkbox("Melhoria Postural Operacional")
            q_flexi = st.checkbox("Ganho de Flexibilidade / Mobilidade")
            stretching = st.checkbox("Condicionamento / Tonificação Muscular")
            q_estresse = st.checkbox("Alívio de Estresse / Bem-Estar")
            
        queixa_extra = st.text_input("Outras Queixas / Histórico Clínico Adicional:")

        st.subheader("4. Conduta Clínica-Desportiva e Tratamento (Múltipla Escolha)")
        st.markdown("###### Selecione as estratégias de tratamento e condutas aplicadas:")
        
        col_cond1, col_cond2, col_cond3 = st.columns(3)
        with col_cond1:
            c_fortalece = st.checkbox("Fortalecimento de Core / Powerhouse")
            c_reab = st.checkbox("Reabilitação / Estabilização Segmentar")
            c_alonga = st.checkbox("Alongamento Axial / Descompressão")
        with col_cond2:
            c_mobilidade = st.checkbox("Treino de Mobilidade Articular Completa")
            c_postural = st.checkbox("Correção Postural Dinâmica")
            c_respiracao = st.checkbox("Controle Respiratório e Ativação")
        with col_cond3:
            c_restricao = st.checkbox("Restrição de Carga / Movimentos Flexo-Torção")
            c_adaptado = st.checkbox("Exercícios Adaptados para Patologias")
            c_geral = st.checkbox("Pilates Clínico Geral / Manutenção")
            
        conduta_extra = st.text_input("Diretrizes de Conduta Específicas / Observações Técnicas:")
        
        st.subheader("5. Evolução e Acompanhamento Clínico")
        progresso_c = st.text_area("Evolução / Histórico de Progressos do Aluno em Relação ao Tratamento:", placeholder="Registre aqui a evolução das dores, ganho de mobilidade...")

        if st.form_submit_button("Validar e Gerar Linha de Cadastro"):
            if nome_c and tel_c:
                # Processa a string de queixas
                lista_queixas = []
                if q_lombar: lista_queixas.append("Dor Lombar")
                if q_cervical: lista_queixas.append("Dor Cervical")
                if q_hernia: lista_queixas.append("Hérnia de Disco")
                if q_escoliose: lista_queixas.append("Escoliose")
                if q_joelho: lista_queixas.append("Lesão Joelho")
                if q_ombro: lista_queixas.append("Lesão Ombro")
                if q_quadril: lista_queixas.append("Desconforto Quadril")
                if q_artrose: lista_queixas.append("Artrose/Artrite")
                if q_postura: lista_queixas.append("Melhoria Postural")
                if q_flexi: lista_queixas.append("Ganho Flexibilidade")
                if stretching: lista_queixas.append("Tonificação")
                if q_estresse: lista_queixas.append("Alívio Estresse")
                if queixa_extra: lista_queixas.append(queixa_extra)
                string_queixas = " | ".join(lista_queixas) if lista_queixas else "Sem queixas registradas"

                # Processa a string de condutas e progressos
                lista_condutas = []
                if c_fortalece: lista_condutas.append("Fortalecimento de Core")
                if c_reab: lista_condutas.append("Reabilitação")
                if c_alonga: lista_condutas.append("Alongamento Axial")
                if c_mobilidade: lista_condutas.append("Treino Mobilidade")
                if c_postural: lista_condutas.append("Correção Postural")
                if c_respiracao: lista_condutas.append("Controle Respiratório")
                if c_restricao: lista_condutas.append("Restrição Carga/Torção")
                if c_adaptado: lista_condutas.append("Exercícios Adaptados")
                if c_geral: lista_condutas.append("Pilates Clínico Geral")
                if conduta_extra: lista_condutas.append(conduta_extra)
                
                if progresso_c:
                    lista_condutas.append(f"[PROGRESSO: {progresso_c}]")
                string_condutas = " | ".join(lista_condutas) if lista_condutas else "Conduta padrão"

                st.success("🎉 Linha estruturada gerada com sucesso! Copie e cole na última linha vazia da aba 'Alunos':")
                
                # Monta a string respeitando a ordem das 14 originais + CPF e Endereço adicionados ao final
                linha_csv = f'"{nome_c}","{tel_c}","{bairro_c}","{plano_c}","{valor_c}",{venc_c},"{dias_c}","{horario_c}","Ativo","{string_queixas}","{string_condutas}","{genero_c}","{nasc_c}","{inicio_c}","{cpf_c}","{endereco_c}"'
                st.code(linha_csv, language="text")
            else:
                st.error("Erro: Os campos 'Nome' e 'WhatsApp' são obrigatórios.")

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

# --- 9. TELA: PREÇOS Tabela Oficial Fixada ---
elif menu == "⚙️ Preços":
    st.title("⚙️ Tabela de Preços e Models de Planos")
    st.markdown("Abaixo estão listados os planos de contratação oficiais vigentes no **Studio Highline**:")
    
    dados_precos_oficiais = {
        "Frequência Semanal": ["1x na semana", "2x na semana", "3x na semana"],
        "Valor Mensal": ["R$ 180,00", "R$ 220,00", "R$ 300,00"]
    }
    df_tabela_oficial = pd.DataFrame(dados_precos_oficiais)
    st.table(df_tabela_oficial)
    
    st.markdown("---")
    st.subheader("Auditoria de Valores Praticados (Planilha de Alunos)")
    if "Plano" in df_alunos.columns and "Valor" in df_alunos.columns:
        df_precos = df_alunos.groupby("Plano")["Valor"].unique().reset_index()
        df_precos["Valores em Uso na Ficha"] = df_precos["Valor"].apply(lambda x: ", ".join([str(i) for i in x if i != ""]))
        st.dataframe(df_precos[["Plano", "Valores em Uso na Ficha"]], use_container_width=True, hide_index=True)
