import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# ==========================================
# 1. CONFIGURAÇÃO DE IDENTIDADE VISUAL (CSS)
# ==========================================
st.set_page_config(page_title="Highline Management", layout="wide", page_icon="🏋️‍♂️")

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
# FUNÇÃO AUXILIAR DE VALIDAÇÃO DE CAPACIDADE
# ==========================================
def verificar_lotacao(df, dias_input, horario_input, aluno_ignorados=None):
    if "Status" not in df.columns or "Dias" not in df.columns or "Horario" not in df.columns:
        return [], []
        
    df_ativos = df[df["Status"].astype(str).str.upper() == "ATIVO"]
    if aluno_ignorados:
        df_ativos = df_ativos[df_ativos["Nome"] != aluno_ignorados]
        
    h_alvo = str(horario_input).strip()
    if not h_alvo or not dias_input:
        return [], []
        
    dias_solicitados = [d.strip().upper() for d in str(dias_input).replace("/", " ").replace(",", " ").split() if d.strip()]
    
    conflitos = []
    alunos_no_horario = []
    
    for idx, row in df_ativos.iterrows():
        h_atual = str(row["Horario"]).strip()
        if h_atual == h_alvo:
            d_atual = [d.strip().upper() for d in str(row["Dias"]).replace("/", " ").replace(",", " ").split() if d.strip()]
            dias_comuns = set(dias_solicitados).intersection(set(d_atual))
            if dias_comuns:
                alunos_no_horario.append(f"{row['Nome']} ({row['Dias']})")
                
    for dia in dias_solicitados:
        qtd_no_dia = 0
        for idx, row in df_ativos.iterrows():
            if str(row["Horario"]).strip() == h_alvo:
                d_atual = [d.strip().upper() for d in str(row["Dias"]).replace("/", " ").replace(",", " ").split() if d.strip()]
                if dia in d_atual:
                    qtd_no_dia += 1
        if qtd_no_dia >= 3:
            conflitos.append((dia, qtd_no_dia))
            
    return conflitos, alunos_no_horario

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
    if "Status" in df_alunos.columns:
        df_ativos = df_alunos[df_alunos["Status"].astype(str).str.upper() == "ATIVO"]
    else:
        df_ativos = df_alunos.copy()

    st.metric("Total de Alunos Ativos Atualmente", len(df_ativos))
    busca = st.text_input("🔍 Filtrar aluno por nome na tabela:", placeholder="Digite o nome completo ou parcial...")
    if busca and "Nome" in df_ativos.columns:
        df_ativos_tabela = df_ativos[df_ativos["Nome"].astype(str).str.contains(busca, case=False, na=False)]
    else:
        df_ativos_tabela = df_ativos
    
    st.dataframe(df_ativos_tabela, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("### ✏️ Alteração Rápida e Gerenciamento de Alunos")
    
    if "Nome" in df_ativos.columns and not df_ativos.empty:
        aluno_para_editar = st.selectbox("Selecione um aluno ativo para alterar dados ou desativar:", ["-- Escolha um Aluno --"] + df_ativos["Nome"].tolist())
        
        if aluno_para_editar != "-- Escolha um Aluno --":
            dados_atuais = df_ativos[df_ativos["Nome"] == aluno_para_editar].iloc[0]
            c_ed1, c_ed2, c_ed3 = st.columns(3)
            
            with c_ed1:
                lista_planos = ["1x semana", "2x semana", "3x semana", "Outro"]
                plano_atual = dados_atuais.get("Plano", "1x semana")
                idx_plano = lista_planos.index(plano_atual) if plano_atual in lista_planos else 0
                novo_plano = st.selectbox("Novo Plano Contratado:", lista_planos, index=idx_plano)
                
                valor_sugerido = dados_atuais.get("Valor", "220,00")
                if novo_plano == "1x semana": valor_sugerido = "180,00"
                elif novo_plano == "2x semana": valor_sugerido = "220,00"
                elif novo_plano == "3x semana": valor_sugerido = "300,00"
                novo_valor = st.text_input("Confirmar Valor Mensal (R$):", value=valor_sugerido)
                
            with c_ed2:
                novos_dias = st.text_input("Novos Dias de Aula Fixados (Ex: Ter/Qui):", value=dados_atuais.get("Dias", ""))
                novo_horario = st.text_input("Novo Horário Escolhido (Ex: 08:30):", value=dados_atuais.get("Horario", ""))
                
            bloqueio_edicao = False
            if novos_dias and novo_horario:
                conflitos_ed, alunos_ed = verificar_lotacao(df_alunos, novos_dias, novo_horario, aluno_ignorados=aluno_para_editar)
                if conflitos_ed:
                    bloqueio_edicao = True
                    for dia_conf, qtd in conflitos_ed:
                        st.error(f"❌ **BLOQUEADO:** O dia **{dia_conf}** no horário **{novo_horario}** já atingiu a capacidade máxima de {qtd}/3 alunos.")
                    st.warning(f"Alunos agendados neste horário: {', '.join(alunos_ed)}")

            with c_ed3:
                st.markdown("**Ações Disponíveis:**")
                btn_salvar_alt = st.button("💾 Gerar Linha Atualizada", disabled=bloqueio_edicao)
                btn_inativar_alt = st.button("❌ Inativar (Mover para Arquivo Morto)")
            
            if btn_salvar_alt and not bloqueio_edicao:
                st.success(f"Dados prontos! Substitua a linha antiga de {aluno_para_editar} na planilha por esta:")
                linha_atualizada_csv = f'"{aluno_para_editar}","{dados_atuais.get("Telefone","")}","{dados_atuais.get("Bairro","")}","{novo_plano}","{novo_valor}",{dados_atuais.get("Vencimento",10)},"{novos_dias}","{novo_horario}","Ativo","{dados_atuais.get("Queixa","")}","{dados_atuais.get("Conduta","")}","{dados_atuais.get("Genero","")}","{dados_atuais.get("Nascimento","")}","{dados_atuais.get("Inicio_Aulas","")}","{dados_atuais.get("CPF","")}","{dados_atuais.get("Endereco","")}"'
                st.code(linha_atualizada_csv, language="text")
                
            if btn_inativar_alt:
                st.warning(f"Linha de desativação gerada para {aluno_para_editar}. Substitua a linha dele na planilha por esta para movê-lo ao Arquivo Morto:")
                linha_inativo_csv = f'"{aluno_para_editar}","{dados_atuais.get("Telefone","")}","{dados_atuais.get("Bairro","")}","{dados_atuais.get("Plano","")}","{dados_atuais.get("Valor","")}",{dados_atuais.get("Vencimento",10)},"{dados_atuais.get("Dias","")}","{dados_atuais.get("Horario","")}","Inativo","{dados_atuais.get("Queixa","")}","{dados_atuais.get("Conduta","")}","{dados_atuais.get("Genero","")}","{dados_atuais.get("Nascimento","")}","{dados_atuais.get("Inicio_Aulas","")}","{dados_atuais.get("CPF","")}","{dados_atuais.get("Endereco","")}"'
                st.code(linha_inativo_csv, language="text")
    else:
        st.info("Nenhum aluno ativo disponível para gerenciamento.")

# --- 3. TELA: ARQUIVO MORTO ---
elif menu == "📁 Arquivo Morto":
    st.title("📁 Arquivo Morto")
    if "Status" in df_alunos.columns:
        df_inativos = df_alunos[df_alunos["Status"].astype(str).str.upper() != "ATIVO"]
        st.metric("Total de Alunos no Arquivo Morto", len(df_inativos))
        st.dataframe(df_inativos, use_container_width=True, hide_index=True)

# --- 4. TELA: ESPERA ---
elif menu == "⏳ Espera":
    st.title("⏳ Lista de Espera")
    st.metric("Total de Clientes em Espera", len(df_espera))
    busca_espera = st.text_input("🔍 Filtrar lista de espera por nome:", placeholder="Digite para filtrar...")
    df_espera_tabela = df_espera.copy()
    if busca_espera and not df_espera.empty:
        col_nome_esp = df_espera.columns[0]
        df_espera_tabela = df_espera[df_espera[col_nome_esp].astype(str).str.contains(busca_espera, case=False, na=False)]
    st.dataframe(df_espera_tabela, use_container_width=True, hide_index=True)

# --- 5. TELA: MAPA ---
elif menu == "🗺️ Mapa":
    st.title("🗺️ Mapa de Distribuição Geográfica")
    if "Bairro" in df_alunos.columns:
        df_bairros = df_alunos[df_alunos["Status"].astype(str).str.upper() == "ATIVO"] if "Status" in df_alunos.columns else df_alunos.copy()
        contagem = df_bairros["Bairro"].value_counts().reset_index()
        contagem.columns = ["Bairro", "Quantidade de Alunos"]
        st.bar_chart(data=contagem, x="Bairro", y="Quantidade de Alunos")

# --- 6. TELA: PERFIL (SEM O TERMO CORRIGIDO) ---
elif menu == "👤 Perfil":
    st.title("👤 Prontuário Individual e Indicadores da Base Ativa")
    
    if "Status" in df_alunos.columns:
        df_ativos = df_alunos[df_alunos["Status"].astype(str).str.upper() == "ATIVO"]
    else:
        df_ativos = df_alunos.copy()

    if "Nome" in df_alunos.columns:
        aluno_sel = st.selectbox("Selecione um aluno para extrair o prontuário completo:", ["-- Escolha um Aluno --"] + df_alunos["Nome"].tolist())
        if aluno_sel != "-- Escolha um Aluno --":
            ficha = df_alunos[df_alunos["Nome"] == aluno_sel].iloc[0]
            st.markdown(f"## Ficha de: {aluno_sel}")
            st.markdown("---")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"📞 **Telefone:** {ficha.get('Telefone', 'N/D')}")
                st.markdown(f"🏡 **Bairro:** {ficha.get('Bairro', 'N/D')}")
                st.markdown(f"🧬 **Gênero:** {ficha.get('Genero', 'N/D')}")
                st.markdown(f"🪪 **CPF:** {ficha.get('CPF', 'N/D')}")
            with c2:
                st.markdown(f"📅 **Nascimento:** {ficha.get('Nascimento', 'N/D')}")
                st.markdown(f"🚀 **Início das Aulas:** {ficha.get('Inicio_Aulas', 'N/D')}")
                st.markdown(f"💎 **Plano:** {ficha.get('Plano', 'N/D')}")
            with c3:
                st.markdown(f"💰 **Valor Mensal:** {ficha.get('Valor', 'N/D')}")
                st.markdown(f"📆 **Vencimento:** Dia {ficha.get('Vencimento', 'N/D')}")
                st.markdown(f"⚡ **Status:** {ficha.get('Status', 'N/D')}")
            
            st.markdown(f"📍 **Endereço Completo:** {ficha.get('Endereco', 'N/D')}")
            st.markdown("---")
            col_q, col_c = st.columns(2)
            with col_q:
                st.subheader("📋 Queixa Principal / Anamnese")
                st.info(ficha.get('Queixa', 'Nenhum registro adicionado.'))
            with col_c:
                st.subheader("🛠️ Conduta & Evolução")
                st.success(ficha.get('Conduta', 'Nenhuma conduta desenhada.'))

    # ==========================================
    # PAINEL DE GRÁFICOS ANALÍTICOS GERAIS
    # ==========================================
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("## 📊 Painel Demográfico e Indicadores Estruturais (Base Ativa)")
    
    if not df_ativos.empty:
        g_col1, g_col2 = st.columns(2)
        
        # (a) Gráfico de Pizza: Distribuição de Gênero
        with g_col1:
            st.markdown("### Distribuição por Gênero")
            if "Genero" in df_ativos.columns:
                df_gen = df_ativos["Genero"].value_counts().reset_index()
                df_gen.columns = ["Gênero", "Quantidade"]
                fig_pizza = px.pie(df_gen, names="Gênero", values="Quantidade", hole=0.3,
                                   color_discrete_sequence=px.colors.qualitative.Pastel)
                st.plotly_chart(fig_pizza, use_container_width=True)
            else:
                st.info("Dados de Gênero indisponíveis.")

        # (b) Gráfico de Barras: Distribuição por Faixa Etária
        with g_col2:
            st.markdown("### Faixa Etária dos Alunos")
            if "Nascimento" in df_ativos.columns:
                idades = []
                ano_atual = datetime.now().year
                for nasc in df_ativos["Nascimento"]:
                    try:
                        ano_nasc = pd.to_datetime(nasc, dayfirst=True).year
                        idades.append(ano_atual - ano_nasc)
                    except:
                        continue
                
                if idades:
                    df_idades = pd.DataFrame({"Idade": idades})
                    bins = [0, 25, 35, 45, 55, 120]
                    labels = ["Até 25 anos", "26 a 35 anos", "36 a 45 anos", "46 a 55 anos", "Mais de 55 anos"]
                    df_idades["Faixa Etária"] = pd.cut(df_idades["Idade"], bins=bins, labels=labels, right=True)
                    df_faixas = df_idades["Faixa Etária"].value_counts().reindex(labels, fill_value=0).reset_index()
                    df_faixas.columns = ["Faixa Etária", "Alunos"]
                    
                    fig_idades = px.bar(df_faixas, x="Faixa Etária", y="Alunos", text="Alunos",
                                        color_discrete_sequence=["#2E5A44"])
                    st.plotly_chart(fig_idades, use_container_width=True)
                else:
                    st.info("Nenhuma data de nascimento válida registrada.")
            else:
                st.info("Dados de Nascimento indisponíveis.")

        st.markdown("---")
        g_col3, g_col4 = st.columns(2)

        # (c) Gráfico de Barras: Valores a Receber ao Longo dos 31 Dias do Mês
        with g_col3:
            st.markdown("### Previsão Diária de Recebimento (Fluxo do Mês)")
            if "Vencimento" in df_ativos.columns and "Valor" in df_ativos.columns:
                df_fin_rec = df_ativos.copy()
                df_fin_rec["Valor_Limpo"] = df_fin_rec["Valor"].astype(str).str.replace("R$", "", regex=False)
                df_fin_rec["Valor_Limpo"] = df_fin_rec["Valor_Limpo"].str.replace(".", "", regex=False).str.replace(",", ".", regex=False).str.strip()
                df_fin_rec["Valor_Num"] = pd.to_numeric(df_fin_rec["Valor_Limpo"], errors="coerce").fillna(0)
                
                df_fin_rec["Dia_Venc"] = pd.to_numeric(df_fin_rec["Vencimento"], errors="coerce").fillna(10).astype(int)
                
                fluxo_mensal = df_fin_rec.groupby("Dia_Venc")["Valor_Num"].sum().reset_index()
                estrutura_mes = pd.DataFrame({"Dia_Venc": list(range(1, 32))})
                fluxo_completo = pd.merge(estrutura_mes, fluxo_mensal, on="Dia_Venc", how="left").fillna(0)
                fluxo_completo.columns = ["Dia do Vencimento", "Total a Receber (R$)"]
                
                fig_fluxo = px.bar(fluxo_completo, x="Dia do Vencimento", y="Total a Receber (R$)",
                                   color_discrete_sequence=["#FFD700"])
                fig_fluxo.update_layout(xaxis=dict(tickmode='linear', tick0=1, dtick=2))
                st.plotly_chart(fig_fluxo, use_container_width=True)
            else:
                st.info("Dados financeiros incompletos para geração de fluxo de caixa.")

        # (d) Gráfico de Barras: Principais Queixas dos Alunos Tratados
        with g_col4:
            st.markdown("### Mapeamento de Queixas Clínicas")
            if "Queixa" in df_ativos.columns:
                todas_queixas = []
                for q_linha in df_ativos["Queixa"]:
                    if q_linha and q_linha != "Sem queixas registradas":
                        partes = [p.strip() for p in str(q_linha).split("|") if p.strip()]
                        todas_queixas.extend(partes)
                
                if todas_queixas:
                    df_q_cont = pd.Series(todas_queixas).value_counts().reset_index()
                    df_q_cont.columns = ["Queixa Clínica", "Ocorrências"]
                    fig_queixas = px.bar(df_q_cont.head(8), x="Ocorrências", y="Queixa Clínica", orientation='h',
                                         color_discrete_sequence=["#A2B9AF"])
                    fig_queixas.update_layout(yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig_queixas, use_container_width=True)
                else:
                    st.info("Nenhuma patologia/queixa marcada na ficha dos alunos ativos atuais.")
            else:
                st.info("Coluna de Queixas indisponível.")
    else:
        st.info("Cadastre alunos ativos para popular os indicadores visuais.")

# --- 7. TELA: CADASTRO ---
elif menu == "📝 Cadastro":
    st.title("📝 Cadastro e Anamnese Estruturada")
    st.subheader("📌 Planejamento de Dias e Horários (Verificação de Vagas)")
    col_dias, col_hora = st.columns(2)
    with col_dias:
        dias_c = st.text_input("Dias de Aula Desejados (Ex: Ter/Qui):")
    with col_hora:
        horario_c = st.text_input("Horário Escolhido (Ex: 08:30):")
        
    bloqueio_cadastro = False
    if dias_c and horario_c:
        conflitos, alunos_existentes = verificar_lotacao(df_alunos, dias_c, horario_c)
        if conflitos:
            bloqueio_cadastro = True
            for dia_lotado, qtd in conflitos:
                st.error(f"🛑 **IMPOSSÍVEL SELECIONAR:** O dia **{dia_lotado}** às **{horario_c}** já está lotado ({qtd}/3 alunos ativos).")
            st.warning(f"Alunos no horário: {', '.join(alunos_existentes)}")
        else:
            st.success(f"✅ Horário disponível para {dias_c} às {horario_c}.")

    with st.form("form_novo_aluno_anamnese_avancada"):
        st.subheader("1. Dados Pessoais e de Contrato")
        nome_c = st.text_input("Nome Completo:")
        col_id1, col_id2 = st.columns(2)
        with col_id1: tel_c = st.text_input("WhatsApp com DDD:")
        with col_id2: cpf_c = st.text_input("CPF:")
        col_end1, col_end2 = st.columns([1, 2])
        with col_end1: bairro_c = st.text_input("Bairro:")
        with col_end2: endereco_c = st.text_input("Endereço Completo:")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            genero_c = st.selectbox("Gênero:", ["Masculino", "Feminino", "Outro"])
            nasc_c = st.text_input("Data de Nascimento (DD/MM/AAAA):")
        with col2:
            plano_c = st.selectbox("Plano Contratado:", ["1x semana", "2x semana", "3x semana", "Outro"])
            valor_c = st.text_input("Valor Combinado (R$):", value="220,00")
        with col3:
            venc_c = st.number_input("Dia de Vencimento Mensal:", min_value=1, max_value=31, value=10)
            inicio_c = st.text_input("Data de Início:", value=datetime.now().strftime("%d/%m/%Y"))
            
        st.subheader("2. Anamnese: Queixas Principais e Sintomas")
        col_q1, col_q2, col_q3 = st.columns(3)
        with col_q1:
            q_lombar = st.checkbox("Dor Lombar (Lombalgia)")
            q_cervical = st.checkbox("Dor Cervical (Cervicalgia)")
            q_hernia = st.checkbox("Hérnia de Disco / Protrusão")
        with col_q2:
            q_joelho = st.checkbox("Dor / Lesão nos Joelhos")
            q_ombro = st.checkbox("Dor / Lesão nos Ombros")
        with col_q3:
            q_postura = st.checkbox("Melhoria Postural Operacional")
            q_flexi = st.checkbox("Ganho de Flexibilidade / Mobilidade")
            
        queixa_extra = st.text_input("Outras Queixas Adicionais:")
        conduta_extra = st.text_input("Diretrizes de Conduta Específicas:")
        progresso_c = st.text_area("Evolução Inicial do Aluno:")

        if bloqueio_cadastro:
            st.form_submit_button("Cadastro Bloqueado devido à Lotação", disabled=True)
        else:
            if st.form_submit_button("Validar e Gerar Linha de Cadastro"):
                if nome_c and tel_c:
                    checkpoint_queixas = []
                    if q_lombar: checkpoint_queixas.append("Dor Lombar")
                    if q_cervical: checkpoint_queixas.append("Dor Cervical")
                    if q_hernia: checkpoint_queixas.append("Hérnia de Disco")
                    if q_joelho: checkpoint_queixas.append("Lesão Joelho")
                    if q_ombro: checkpoint_queixas.append("Lesão Ombro")
                    if q_postura: checkpoint_queixas.append("Melhoria Postural")
                    if q_flexi: checkpoint_queixas.append("Ganho Flexibilidade")
                    if queixa_extra: checkpoint_queixas.append(queixa_extra)
                    string_queixas = " | ".join(checkpoint_queixas) if checkpoint_queixas else "Sem queixas registradas"

                    st.success("🎉 Linha estruturada gerada!")
                    linha_csv = f'"{nome_c}","{tel_c}","{bairro_c}","{plano_c}","{valor_c}",{venc_c},"{dias_c}","{horario_c}","Ativo","{string_queixas}","{conduta_extra}","{genero_c}","{nasc_c}","{inicio_c}","{cpf_c}","{endereco_c}"'
                    st.code(linha_csv, language="text")

# --- 8. TELA: FINANCEIRO ---
elif menu == "💰 Financeiro":
    st.title("💰 Relatório e Movimentação Financeira")
    if "Valor" in df_financeiro.columns:
        valores_limpos = df_financeiro["Valor"].astype(str).str.replace("R$", "", regex=False).str.replace(".", "", regex=False).str.replace(",", ".", regex=False).str.strip()
        valores_numericos = pd.to_numeric(valores_limpos, errors="coerce")
        st.metric(label="Faturamento Total Acumulado", value=f"R$ {valores_numericos.sum():,.2f}")
    st.dataframe(df_financeiro, use_container_width=True, hide_index=True)

# --- 9. TELA: PREÇOS ---
elif menu == "⚙️ Preços":
    st.title("⚙️ Tabela de Preços e Modelos de Planos")
    dados_precos_oficiais = {"Frequência Semanal": ["1x na semana", "2x na semana", "3x na semana"], "Valor Mensal": ["R$ 180,00", "R$ 220,00", "R$ 300,00"]}
    st.table(pd.DataFrame(dados_precos_oficiais))
