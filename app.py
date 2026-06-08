import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import os

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
        .logo-container {
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 10px 0px 20px 0px;
        }
        @media print {
            [data-testid="stSidebar"], .stHeader, footer, .no-print, button {
                display: none !important;
            }
            .print-container {
                width: 100%;
                border: none !important;
                padding: 0 !important;
            }
        }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. CONEXÃO AUTOMÁTICA COM GOOGLE SHEETS
# ==========================================
conexao_ok = False
try:
    # Tratamento seguro da Private Key contra quebras de linha corrompidas
    if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
        if "private_key" in st.secrets["connections"]["gsheets"]:
            p_key = st.secrets["connections"]["gsheets"]["private_key"]
            if "\\n" in p_key:
                st.secrets["connections"]["gsheets"]["private_key"] = p_key.replace("\\n", "\n")

    conn = st.connection("gsheets", type=GSheetsConnection)
    df_alunos = conn.read(worksheet="alunos")
    df_financeiro = conn.read(worksheet="financeiro")
    df_espera = conn.read(worksheet="espera", keep_default_na=False)
    
    # Padronização de Colunas (Trata acentos como 'Horário' ou 'Horario')
    for df in [df_alunos, df_financeiro, df_espera]:
        if df is not None and not df.empty:
            df.columns = df.columns.str.strip()
            # Se encontrar 'Horário', espelha para 'Horario' para manter compatibilidade interna
            if "Horário" in df.columns and "Horario" not in df.columns:
                df["Horario"] = df["Horário"]
                
    conexao_ok = True
except Exception as e:
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
# 3. BARRA LATERAL - LOGO E MENU
# ==========================================
with st.sidebar:
    USUARIO_GITHUB = "pboszczovski"
    REPOSITORIO_GITHUB = "highline-app"
    
    url_logo_internet = f"https://raw.githubusercontent.com/{USUARIO_GITHUB}/{REPOSITORIO_GITHUB}/main/Highline%20Logo.png"
    arquivo_logo_local = "Highline Logo.png"
    
    st.markdown('<div class="logo-container">', unsafe_allow_html=True)
    if os.path.exists(arquivo_logo_local):
        st.image(arquivo_logo_local, width=180)
    else:
        try:
            st.image(url_logo_internet, width=180)
        except:
            st.markdown("## 🏋️‍♂️ Studio Highline")
    st.markdown('</div>', unsafe_allow_html=True)
        
    st.markdown("🔒 **Menu de Navegação**")
    
    menu = st.radio(
        "",
        [
            "📅 Agenda",
            "👥 Alunos",
            "📝 Cadastro",
            "⏳ Espera",
            "💰 Financeiro",
            "👤 Perfil",
            "🗺️ Mapa",
            "⚙️ Preços",
            "📁 Arquivo Morto",
            "🖨️ Imprimir Prontuário"
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
    st.error(f"Erro crítico de conexão com o Google Sheets. Verifique as configurações das credenciais. Detalhes: {erro_msg}")
    st.stop()

# ==========================================
# 4. TRATAMENTO DAS TELAS DO APP
# ==========================================

# --- 1. TELA: AGENDA ---
if menu == "📅 Agenda":
    st.title("📅 Agenda de Treinos")
    hoje_datetime = datetime.now()
    hoje_mm_dd = hoje_datetime.strftime("%m-%d")
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
        st.info(f"🎉 **Hoje é aniversário de:** {nomes_niver}! 🎂")
    else:
        st.info("🎂 Nenhum aluno a fazer aniversário hoje.")
        
    # Mapeamento do dia da semana atual para corresponder à entrada de texto da planilha
    dia_semana_num = hoje_datetime.weekday()
    
    dias_validos_busca = []
    if dia_semana_num == 0:
        dias_validos_busca = ["SEG", "2A", "SEGUNDA"]
        nome_dia_formatado = "Segunda-feira"
    elif dia_semana_num == 1:
        dias_validos_busca = ["TER", "3A", "TERÇA", "TERCA"]
        nome_dia_formatado = "Terça-feira"
    elif dia_semana_num == 2:
        dias_validos_busca = ["QUA", "4A", "QUARTA"]
        nome_dia_formatado = "Quarta-feira"
    elif dia_semana_num == 3:
        dias_validos_busca = ["QUI", "5A", "QUINTA"]
        nome_dia_formatado = "Quinta-feira"
    elif dia_semana_num == 4:
        dias_validos_busca = ["SEX", "6A", "SEXTA"]
        nome_dia_formatado = "Sexta-feira"
    elif dia_semana_num == 5:
        dias_validos_busca = ["SAB", "SÁBADO", "SABADO"]
        nome_dia_formatado = "Sábado"
    else:
        dias_validos_busca = ["DOM", "DOMINGO"]
        nome_dia_formatado = "Domingo"

    st.markdown(f"### 📋 Horários Agendados para Hoje ({nome_dia_formatado})")
    if "Status" in df_alunos.columns:
        df_ativos = df_alunos[df_alunos["Status"].astype(str).str.upper() == "ATIVO"]
    else:
        df_ativos = df_alunos.copy()
        
    if not df_ativos.empty:
        # Filtragem com base no dia da semana na coluna 'Dias'
        if "Dias" in df_ativos.columns:
            condicao_dia = df_ativos["Dias"].astype(str).str.upper().apply(
                lambda x: any(termo in x for termo in dias_validos_busca)
            )
            df_agenda = df_ativos[condicao_dia]
        else:
            df_agenda = df_ativos.copy()
            
        # Ordenação por Horário
        if not df_agenda.empty and "Horario" in df_agenda.columns:
            df_agenda = df_agenda.sort_values(by="Horario")
            
        # Exibição dos resultados filtrados do dia
        if not df_agenda.empty:
            colunas_agenda = [c for c in ["Horario", "Nome", "Status", "Queixa", "Conduta", "Dias"] if c in df_agenda.columns]
            st.dataframe(df_agenda[colunas_agenda], use_container_width=True, hide_index=True)
        else:
            st.warning(f"Nenhum aluno agendado para esta {nome_dia_formatado}.")
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
    busca = st.text_input("🔍 Filtrar aluno por nome na tabela:", placeholder="Digite o nome completo...")
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
            idx_real_planilha = df_alunos[df_alunos["Nome"] == aluno_para_editar].index[0]
            dados_atuais = df_alunos.loc[idx_real_planilha]
            
            c_ed1, c_ed2, c_ed3 = st.columns(3)
            with c_ed1:
                options_planos = ["1x semana", "2x semana", "3x semana"]
                plano_atual = dados_atuais.get("Plano", "1x semana")
                idx_plano = options_planos.index(plano_atual) if plano_atual in options_planos else 0
                novo_plano = st.selectbox("Novo Plano Contratado:", options_planos, index=idx_plano)
                
                valor_sugerido = dados_atuais.get("Valor", "220,00")
                if novo_plano == "1x semana": valor_sugerido = "180,00"
                elif novo_plano == "2x semana": valor_sugerido = "220,00"
                elif novo_plano == "3x semana": valor_sugerido = "300,00"
                novo_valor = st.text_input("Confirmar Valor Mensal (R$):", value=valor_sugerido)
                
            with c_ed2:
                novos_dias = st.text_input("Novos Dias de Aula (Ex: Ter/Qui):", value=dados_atuais.get("Dias", ""))
                novo_horario = st.text_input("Novo Horário (Ex: 08:30):", value=dados_atuais.get("Horario", ""))
                
            bloqueio_edicao = False
            if novos_dias and novo_horario:
                conflitos_ed, alunos_ed = verificar_lotacao(df_alunos, novos_dias, novo_horario, aluno_ignorados=aluno_para_editar)
                if conflitos_ed:
                    bloqueio_edicao = True
                    for dia_conf, qtd in conflitos_ed:
                        st.error(f"❌ Horário lotado em {dia_conf} ({qtd}/3 alunos).")
            
            with c_ed3:
                st.markdown("**Ações Disponíveis:**")
                btn_salvar_alt = st.button("💾 Gravar Alterações Diretamente", disabled=bloqueio_edicao)
                btn_inativar_alt = st.button("❌ Desativar e Mover ao Arquivo Morto")
            
            if btn_salvar_alt and not bloqueio_edicao:
                df_alunos.at[idx_real_planilha, "Plano"] = novo_plano
                df_alunos.at[idx_real_planilha, "Valor"] = novo_valor
                df_alunos.at[idx_real_planilha, "Dias"] = novos_dias
                df_alunos.at[idx_real_planilha, "Horario"] = novo_horario
                if "Horário" in df_alunos.columns:
                    df_alunos.at[idx_real_planilha, "Horário"] = novo_horario
                
                conn.update(worksheet="alunos", data=df_alunos)
                st.success("🎉 Planilha updated!")
                st.cache_data.clear()
                st.rerun()
                
            if btn_inativar_alt:
                df_alunos.at[idx_real_planilha, "Status"] = "Inativo"
                conn.update(worksheet="alunos", data=df_alunos)
                st.success("❌ Aluno arquivado!")
                st.cache_data.clear()
                st.rerun()
    else:
        st.info("Nenhum aluno ativo disponível para gerenciamento.")

# --- 3. TELA: CADASTRO ---
elif menu == "📝 Cadastro":
    st.title("📝 Cadastro e Anamnese Estruturada")
    
    st.subheader("📌 Personalização de Horários")
    col_dias, col_hora = st.columns(2)
    with col_dias: dias_c = st.text_input("Dias de Aula Desejados (Ex: Ter/Qui):")
    with col_hora: horario_c = st.text_input("Horário Escolhido (Ex: 08:30):")
        
    bloqueio_cadastro = False
    if dias_c and horario_c:
        conflitos, alunos_existentes = verificar_lotacao(df_alunos, dias_c, horario_c)
        if conflitos:
            bloqueio_cadastro = True
            for dia_lotado, qtd in conflitos:
                st.error(f"🛑 O dia {dia_lotado} às {horario_c} já está lotado ({qtd}/3 alunos).")
        else:
            st.success(f"✅ Horário disponível.")

    st.subheader("1. Dados Pessoais e de Contrato")
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        plano_c = st.selectbox("Plano Contratado:", ["1x semana", "2x semana", "3x semana"])
    with col_p2:
        if plano_c == "1x semana": valor_padrao = "180,00"
        elif plano_c == "2x semana": valor_padrao = "220,00"
        elif plano_c == "3x semana": valor_padrao = "300,00"
        else: valor_padrao = "220,00"
        valor_c = st.text_input("Valor Combinado Mensal (R$):", value=valor_padrao)

    with st.form("form_novo_aluno_anamnese_avancada"):
        nome_c = st.text_input("Nome Completo:")
        col_id1, col_id2 = st.columns(2)
        with col_id1: tel_c = st.text_input("WhatsApp com DDD:")
        with col_id2: cpf_c = st.text_input("CPF:")
        
        col_end1, col_end2, col_end3 = st.columns([1, 2, 1])
        with col_end1: bairro_c = st.text_input("Bairro:")
        with col_end2: endereco_base = st.text_input("Endereço (Rua, Número, etc.):")
        with col_end3: complemento_c = st.text_input("Complemento (Apto, Casa, Bloco):")
        
        col1, col2 = st.columns(2)
        with col1:
            genero_c = st.selectbox("Gênero:", ["Masculino", "Feminino", "Outro"])
            nasc_c = st.text_input("Data de Nascimento (DD/MM/AAAA):")
        with col2:
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
            if st.form_submit_button("💾 Salvar Novo Aluno Automaticamente"):
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

                    endereco_completo = f"{endereco_base} - {complemento_c}" if complemento_c else endereco_base

                    nova_linha = {
                        "Nome": nome_c, "Telefone": tel_c, "Bairro": bairro_c, 
                        "Plano": plano_c, "Valor": valor_c, "Vencimento": int(venc_c), 
                        "Dias": dias_c, "Horario": horario_c, "Status": "Ativo", 
                        "Queixa": string_queixas, "Conduta": conduta_extra, "Genero": genero_c, 
                        "Nascimento": nasc_c, "Inicio_Aulas": inicio_c, "CPF": cpf_c, "Endereco": endereco_completo
                    }
                    
                    if "Horário" in df_alunos.columns:
                        nova_linha["Horário"] = horario_c

                    df_novo = pd.DataFrame([nova_linha])
                    df_alunos_atualizado = pd.concat([df_alunos, df_novo], ignore_index=True)
                    
                    if "Horario" in df_alunos_atualizado.columns and "Horário" in df_alunos.columns:
                        df_alunos_atualizado = df_alunos_atualizado.drop(columns=["Horario"])

                    conn.update(worksheet="alunos", data=df_alunos_atualizado)
                    
                    st.success(f"🎉 {nome_c} cadastrado!")
                    st.cache_data.clear()
                    st.rerun()

# --- 4. TELA: ESPERA ---
elif menu == "⏳ Espera":
    st.title("⏳ Lista de Espera")
    st.metric("Total de Clientes em Espera", len(df_espera))
    st.dataframe(df_espera, use_container_width=True, hide_index=True)

# --- 5. TELA: FINANCEIRO ---
elif menu == "💰 Financeiro":
    st.title("💰 Relatório e Movimentação Financeira")
    if "Valor" in df_financeiro.columns and not df_financeiro.empty:
        valores_limpos = df_financeiro["Valor"].astype(str).str.replace("R$", "", regex=False).str.replace(".", "", regex=False).str.replace(",", ".", regex=False).str.strip()
        valores_numericos = pd.to_numeric(valores_limpos, errors="coerce")
        st.metric(label="Faturamento Total Acumulado", value=f"R$ {valores_numericos.sum():,.2f}")
    st.dataframe(df_financeiro, use_container_width=True, hide_index=True)

# --- 6. TELA: PERFIL ---
elif menu == "👤 Perfil":
    st.title("👤 Indicadores Estruturais da Base Ativa")
    
    if "Status" in df_alunos.columns:
        df_ativos = df_alunos[df_alunos["Status"].astype(str).str.upper() == "ATIVO"]
    else:
        df_ativos = df_alunos.copy()

    if not df_ativos.empty:
        g_col1, g_col2 = st.columns(2)
        with g_col1:
            st.markdown("### Distribuição por Gênero")
            if "Genero" in df_ativos.columns:
                df_gen = df_ativos["Genero"].value_counts().reset_index()
                df_gen.columns = ["Gênero", "Quantidade"]
                fig_pizza = px.pie(df_gen, names="Gênero", values="Quantidade", hole=0.3, color_discrete_sequence=px.colors.qualitative.Pastel)
                st.plotly_chart(fig_pizza, use_container_width=True)
        with g_col2:
            st.markdown("### Faixa Etária dos Alunos")
            if "Nascimento" in df_ativos.columns:
                idades = []
                ano_atual = datetime.now().year
                for nasc in df_ativos["Nascimento"]:
                    try:
                        ano_nasc = pd.to_datetime(nasc, dayfirst=True).year
                        idades.append(ano_atual - ano_nasc)
                    except: continue
                if idades:
                    df_idades = pd.DataFrame({"Idade": idades})
                    bins = [0, 25, 35, 45, 55, 120]
                    labels = ["Até 25 anos", "26 a 35 anos", "36 a 45 anos", "46 a 55 anos", "Mais de 55 anos"]
                    df_idades["Faixa Etária"] = pd.cut(df_idades["Idade"], bins=bins, labels=labels, right=True)
                    df_faixas = df_idades["Faixa Etária"].value_counts().reindex(labels, fill_value=0).reset_index()
                    df_faixas.columns = ["Faixa Etária", "Alunos"]
                    fig_idades = px.bar(df_faixas, x="Faixa Etária", y="Alunos", text="Alunos", color_discrete_sequence=["#2E5A44"])
                    st.plotly_chart(fig_idades, use_container_width=True)
    else:
        st.info("Gráficos indisponíveis.")

# --- 7. TELA: MAPA ---
elif menu == "🗺️ Mapa":
    st.title("🗺️ Mapa de Distribuição Geográfica")
    if "Bairro" in df_alunos.columns and not df_alunos.empty:
        df_bairros = df_alunos[df_alunos["Status"].astype(str).str.upper() == "ATIVO"] if "Status" in df_alunos.columns else df_alunos.copy()
        contagem = df_bairros["Bairro"].value_counts().reset_index()
        st.bar_chart(data=contagem, x="Bairro", y="count")

# --- 8. TELA: PREÇOS ---
elif menu == "⚙️ Preços":
    st.title("⚙️ Tabela de Preços e Modelos de Planos")
    dados_precos_oficiais = {"Frequência Semanal": ["1x na semana", "2x na semana", "3x na semana"], "Valor Mensal": ["R$ 180,00", "R$ 220,00", "R$ 300,00"]}
    st.table(pd.DataFrame(dados_precos_oficiais))

# --- 9. TELA: ARQUIVO MORTO ---
elif menu == "📁 Arquivo Morto":
    st.title("📁 Arquivo Morto (Alunos Inativos)")
    if "Status" in df_alunos.columns:
        df_inativos = df_alunos[df_alunos["Status"].astype(str).str.upper() != "ATIVO"]
        st.metric("Total de Alunos no Arquivo Morto", len(df_inativos))
        st.dataframe(df_inativos, use_container_width=True, hide_index=True)

# --- 10. TELA: 🖨️ IMPRIMIR PRONTUÁRIO ---
elif menu == "🖨️ Imprimir Prontuário":
    st.title("🖨️ Impressão de Prontuário de Aluno")
    if "Nome" in df_alunos.columns:
        aluno_sel = st.selectbox("Selecione o aluno para gerar o prontuário:", ["-- Escolha um Aluno --"] + df_alunos["Nome"].tolist())
        if aluno_sel != "-- Escolha um Aluno --":
            ficha = df_alunos[df_alunos["Nome"] == aluno_sel].iloc[0]
            
            st.markdown('<div class="no-print">', unsafe_allow_html=True)
            if st.button("🖨️ Abrir Janela de Impressão / Salvar PDF"):
                st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            conteudo_html = f"""
            <div class="print-container" style="border: 2px solid #2E5A44; padding: 30px; border-radius: 10px; background-color: #ffffff; color: #000000; font-family: Arial, sans-serif;">
                <div style="text-align: center; margin-bottom: 25px;">
                    <h1 style="color: #2E5A44; margin: 0;">STUDIO HIGHLINE</h1>
                    <p style="margin: 5px 0; color: #555;">Ficha Cadastral e Prontuário Individual de Acompanhamento</p>
                </div>
                <hr style="border: 0; border-top: 1px solid #ccc; margin-bottom: 20px;">
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 8px; font-weight: bold; width: 30%;">Nome Completo:</td>
                        <td style="padding: 8px;">{ficha.get('Nome', 'Não Informado')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; font-weight: bold;">WhatsApp:</td>
                        <td style="padding: 8px;">{ficha.get('Telefone', 'Não Informado')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; font-weight: bold;">Plano Atual:</td>
                        <td style="padding: 8px;">{ficha.get('Plano', 'Não Informado')} - R$ {ficha.get('Valor', '0,00')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; font-weight: bold;">Dias/Horários fixos:</td>
                        <td style="padding: 8px;">{ficha.get('Horario', 'Não Informado')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; font-weight: bold; vertical-align: top;">Histórico de Queixas / Anamnese:</td>
                        <td style="padding: 8px; color: #b22222; font-weight: bold;">{ficha.get('Queixa', 'Nenhuma registrada')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; font-weight: bold; vertical-align: top;">Diretrizes de Conduta Técnica:</td>
                        <td style="padding: 8px; font-style: italic;">{ficha.get('Conduta', 'Sem restrições especificadas')}</td>
                    </tr>
                </table>
            </div>
            """
            st.markdown(conteudo_html, unsafe_allow_html=True)
