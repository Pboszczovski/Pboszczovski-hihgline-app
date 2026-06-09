import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
# FUNÇÕES AUXILIARES DE LIMPEZA E FORMATAÇÃO
# ==========================================
def limpar_dataframe(df):
    if df is None or df.empty:
        return df
    df = df.loc[:, ~df.columns.astype(str).str.contains('^Unnamed')]
    df.columns = df.columns.str.strip()
    df.dropna(how="all", inplace=True)
    return df

def formatar_brl(valor):
    try:
        if pd.isna(valor) or valor == "":
            return "R$ 0,00"
        if isinstance(valor, (int, float)):
            val_float = float(valor)
        else:
            val_limpo = str(valor).replace("R$", "").replace(" ", "")
            if "," in val_limpo and "." in val_limpo:
                val_limpo = val_limpo.replace(".", "").replace(",", ".")
            elif "," in val_limpo:
                val_limpo = val_limpo.replace(",", ".")
            val_float = float(val_limpo)
        return f"R$ {val_float:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return str(valor)

def converter_para_float(valor):
    try:
        if pd.isna(valor) or valor == "":
            return 0.0
        if isinstance(valor, (int, float)):
            return float(valor)
        
        texto = str(valor).replace("R$", "").replace(" ", "")
        if "," in texto and "." in texto:
            texto = texto.replace(".", "").replace(",", ".")
        elif "," in texto:
            texto = texto.replace(",", ".")
        return float(texto)
    except:
        return 0.0

# ==========================================
# 2. CONEXÃO AUTOMÁTICA COM GOOGLE SHEETS
# ==========================================
conexao_ok = False
erro_msg = ""

try:
    if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
        if "private_key" in st.secrets["connections"]["gsheets"]:
            p_key = st.secrets["connections"]["gsheets"]["private_key"]
            if "\\n" in p_key:
                st.secrets["connections"]["gsheets"]["private_key"] = p_key.replace("\\n", "\n")

    conn = st.connection("gsheets", type=GSheetsConnection)
    
    df_alunos = limpar_dataframe(conn.read(worksheet="alunos"))
    df_financeiro = limpar_dataframe(conn.read(worksheet="financeiro"))
    df_espera = limpar_dataframe(conn.read(worksheet="espera"))
    
    try:
        df_precos = limpar_dataframe(conn.read(worksheet="precos"))
    except:
        df_precos = pd.DataFrame([
            {"Plano": "1x semana", "Valor": 180.0},
            {"Plano": "2x semana", "Valor": 220.0},
            {"Plano": "3x semana", "Valor": 300.0}
        ])

    if df_alunos is not None and not df_alunos.empty:
        if "Valor Mensal" in df_alunos.columns and "Valor" not in df_alunos.columns:
            df_alunos["Valor"] = df_alunos["Valor Mensal"]
        elif "Valor Mensal" in df_alunos.columns and "Valor" in df_alunos.columns:
            df_alunos["Valor"] = df_alunos["Valor"].fillna(df_alunos["Valor Mensal"])

    if df_espera is not None and not df_espera.empty and "Nome" in df_espera.columns:
        df_espera = df_espera[df_espera["Nome"].astype(str).str.strip() != ""]
        df_espera = df_espera[~df_espera["Nome"].astype(str).str.lower().str.contains("nan", na=True)]

    conexao_ok = True
except Exception as e:
    erro_msg = str(e)

dict_precos_padrao = {"1x semana": 180.0, "2x semana": 220.0, "3x semana": 300.0}
if df_precos is not None and not df_precos.empty and "Plano" in df_precos.columns:
    for _, r in df_precos.iterrows():
        dict_precos_padrao[str(r["Plano"])] = converter_para_float(r["Valor"])

# ==========================================
# FUNÇÃO AUXILIAR DE VALIDAÇÃO DE CAPACIDADE
# ==========================================
def verificar_lotacao(df, dias_input, horario_input, aluno_ignorados=None):
    if df is None or df.empty or "Status" not in df.columns or "Dias" not in df.columns or "Horario" not in df.columns:
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
    st.error(f"Erro crítico de configuração ou credenciais. Detalhes: {erro_msg}")
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
        
    dia_semana_num = hoje_datetime.weekday()
    dias_validos_busca = []
    if dia_semana_num == 0:     dias_validos_busca, nome_dia_formatado = ["SEG", "2A", "SEGUNDA"], "Segunda-feira"
    elif dia_semana_num == 1:   dias_validos_busca, nome_dia_formatado = ["TER", "3A", "TERÇA", "TERCA"], "Terça-feira"
    elif dia_semana_num == 2:   dias_validos_busca, nome_dia_formatado = ["QUA", "4A", "QUARTA"], "Quarta-feira"
    elif dia_semana_num == 3:   dias_validos_busca, nome_dia_formatado = ["QUI", "5A", "QUINTA"], "Quinta-feira"
    elif dia_semana_num == 4:   dias_validos_busca, nome_dia_formatado = ["SEX", "6A", "SEXTA"], "Sexta-feira"
    elif dia_semana_num == 5:   dias_validos_busca, nome_dia_formatado = ["SAB", "SÁBADO", "SABADO"], "Sábado"
    else:                       dias_validos_busca, nome_dia_formatado = ["DOM", "DOMINGO"], "Domingo"

    st.markdown(f"### 📋 Horários Agendados para Hoje ({nome_dia_formatado})")
    df_ativos = df_alunos[df_alunos["Status"].astype(str).str.upper() == "ATIVO"] if "Status" in df_alunos.columns else df_alunos.copy()
        
    if not df_ativos.empty:
        if "Dias" in df_ativos.columns:
            condicao_dia = df_ativos["Dias"].astype(str).str.upper().apply(lambda x: any(termo in x for termo in dias_validos_busca))
            df_agenda = df_ativos[condicao_dia]
        else:
            df_agenda = df_ativos.copy()
            
        if not df_agenda.empty and "Horario" in df_agenda.columns:
            df_agenda = df_agenda.sort_values(by="Horario")
            
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
    df_ativos = df_alunos[df_alunos["Status"].astype(str).str.upper() == "ATIVO"] if "Status" in df_alunos.columns else df_alunos.copy()

    st.metric("Total de Alunos Ativos Atualmente", len(df_ativos))
    busca = st.text_input("🔍 Filtrar aluno por nome na tabela:", placeholder="Digite o nome do aluno...")
    df_ativos_tabela = df_ativos[df_ativos["Nome"].astype(str).str.contains(busca, case=False, na=False)] if busca and "Nome" in df_ativos.columns else df_ativos
    
    df_ativos_visivel = df_ativos_tabela.copy()
    if "Valor" in df_ativos_visivel.columns:
        df_ativos_visivel["Valor"] = df_ativos_visivel["Valor"].apply(formatar_brl)
    
    st.dataframe(df_ativos_visivel, use_container_width=True, hide_index=True)

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
                
                valor_sugerido_bruto = dados_atuais.get("Valor", dict_precos_padrao.get(novo_plano, 220.0))
                valor_sugerido_float = converter_para_float(valor_sugerido_bruto)
                    
                novo_valor = st.number_input("Confirmar Valor Mensal (R$):", value=valor_sugerido_float)
                
            with c_ed2:
                novos_dias = st.text_input("Novos Dias de Aula (Ex: Ter/Qui):", value=dados_atuais.get("Dias", ""))
                novo_horario = st.text_input("Novo Horário (Ex: 08:30):", value=dados_atuais.get("Horario", ""))
                
            bloqueio_edicao = False
            
            # --- CORREÇÃO DO OPERADOR WALRUS E DA INDENTAÇÃO REALIZADA AQUI ---
            if novos_dias and novo_horario:
                Profiler_horario = novo_horario
                conflitos_ed, _ = verificar_lotacao(df_alunos, novos_dias, Profiler_horario, aluno_ignorados=aluno_para_editar)
                if conflitos_ed:
                    bloqueio_edicao = True
                    for dia_conf, qtd in conflitos_ed:
                        st.error(f"❌ Horário lotado em {dia_conf} ({qtd}/3 alunos).")
            
            with c_ed3:
                st.markdown("**Ações Disponíveis:**")
                btn_salvar_alt = st.button("💾 Gravar Alterações Diretamente", disabled=bloqueio_edicao)
                btn_inativar_alt = st.button("❌ Desativar e Mover ao Arquivo Morto")
            
            if btn_salvar_alt and not bloqueio_edicao:
                idx_inteiro = int(idx_real_planilha)
                df_alunos["Valor"] = df_alunos["Valor"].astype(object)
                
                df_alunos.at[idx_inteiro, "Plano"] = novo_plano
                df_alunos.at[idx_inteiro, "Valor"] = float(novo_valor)  
                if "Valor Mensal" in df_alunos.columns:
                    df_alunos.at[idx_inteiro, "Valor Mensal"] = float(novo_valor)
                df_alunos.at[idx_inteiro, "Dias"] = novos_dias
                df_alunos.at[idx_inteiro, "Horario"] = novo_horario
                
                conn.update(worksheet="alunos", data=df_alunos)
                st.success("🎉 Planilha atualizada com sucesso!")
                st.cache_data.clear()
                st.rerun()
                
            if btn_inativar_alt:
                df_alunos.at[int(idx_real_planilha), "Status"] = "Inativo"
                conn.update(worksheet="alunos", data=df_alunos)
                st.success("❌ Aluno arquivado com sucesso!")
                st.cache_data.clear()
                st.rerun()
    else:
        st.info("Nenhum aluno ativo disponível para gerenciamento.")

# --- 3. TELA: CADASTRO ---
elif menu == "📝 Cadastro":
    st.title("📝 Cadastro e Anamnese Estruturada")
    
    st.subheader("📌 Personalização de Horários")
    col_dias, col_hora = st.columns(2)
    
    with col_dias:
        dias_selecionados = st.multiselect(
            "Dias de Aula Desejados:",
            ["SEG", "TER", "QUA", "QUI", "SEX", "SAB"],
            placeholder="Escolha os dias..."
        )
        dias_c = "/".join(dias_selecionados) if dias_selecionados else ""
        
    with col_hora:
        lista_horarios = [
            "06:00", "06:30", "07:00", "07:30", "08:00", "08:30", 
            "09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
            "12:00", "12:30", "13:00", "13:30", "14:00", "14:30",
            "15:00", "15:30", "16:00", "16:30", "17:00", "17:30",
            "18:00", "18:30", "19:00", "19:30", "20:00", "20:30"
        ]
        horario_c = st.selectbox("Horário Escolhido:", ["-- Selecione um Horário --"] + lista_horarios)
        if horario_c == "-- Selecione um Horário --":
            horario_c = ""
        
    bloqueio_cadastro = False
    if dias_c and horario_c:
        conflitos, alunos_existentes = verificar_lotacao(df_alunos, dias_c, horario_c)
        if conflitos:
            bloqueio_cadastro = True
            for dia_lotado, qtd in conflitos:
                st.error(f"🛑 O dia {dia_lotado} às {horario_c} já está lotado ({qtd}/3 alunos).")
        else:
            st.success(f"✅ Horário totalmente disponível.")

    st.subheader("1. Dados Pessoais e de Contrato")
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        plano_c = st.selectbox("Plano Contratado:", ["1x semana", "2x semana", "3x semana"])
    with col_p2:
        valor_padrao = dict_precos_padrao.get(plano_c, 220.0)
        valor_c = st.number_input("Valor Combinado Mensal (R$):", value=float(valor_padrao))

    with st.form("form_novo_aluno_anamnese_avancada"):
        nome_c = st.text_input("Nome Completo:")
        col_id1, col_id2 = st.columns(2)
        with col_id1: tel_c = st.text_input("WhatsApp com DDD:")
        with col_id2: cpf_c = st.text_input("CPF:")
        
        col_end1, col_end2, col_end3 = st.columns([1, 2, 1])
        with col_end1: bairro_c = st.text_input("Bairro:")
        with col_end2: endereco_base = st.text_input("Endereço (Rua, Número):")
        with col_end3: complemento_c = st.text_input("Complemento:")
        
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
        
        st.subheader("3. Diretrizes de Conduta e Tratamentos Usuais")
        col_t1, col_t2, col_t3 = st.columns(3)
        with col_t1:
            t_fortalecimento = st.checkbox("Fortalecimento de Core / Estabilização")
            t_alongamento = st.checkbox("Alongamento de Cadeia Posterior")
            t_mobilidade = st.checkbox("Mobilidade de Quadril e Torácica")
        with col_t2:
            t_tracao = st.checkbox("Descompressão / Tração Axial Leve")
            t_impacto = st.checkbox("Evitar Impacto / Saltos")
            t_flexao = st.checkbox("Restrição de Flexão de Tronco")
        with col_t3:
            t_extensao = st.checkbox("Restrição de Extensão de Tronco")
            t_carga = st.checkbox("Progressão de Carga Controlada")
            t_postural = st.checkbox("Reeducação Postural / Alinhamento")
            
        conduta_extra = st.text_input("Diretrizes de Conduta Específicas:")
        progresso_c = st.text_area("Evolução Inicial do Aluno:")

        if bloqueio_cadastro or not dias_c or not horario_c:
            texto_botao = "Preencha Dias e Horário acima" if (not dias_c or not horario_c) else "Cadastro Bloqueado devido à Lotação"
            st.form_submit_button(texto_botao, disabled=True)
        else:
            if st.form_submit_button("💾 Salvar Novo Aluno"):
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
                    string_queixas = " | ".join(checkpoint_queixas) if checkpoint_queixas else "Sem queixas"

                    checkpoint_condutas = []
                    if t_fortalecimento: checkpoint_condutas.append("Fortalecimento Core")
                    if t_alongamento: checkpoint_condutas.append("Alongamento Cad. Posterior")
                    if t_mobilidade: checkpoint_condutas.append("Mobilidade Quadril")
                    if t_tracao: checkpoint_condutas.append("Descompressão Axial")
                    if t_impacto: checkpoint_condutas.append("Evitar Impacto")
                    if t_flexao: checkpoint_condutas.append("Restrição Flexão")
                    if t_extensao: checkpoint_condutas.append("Restrição Extensão")
                    if t_carga: checkpoint_condutas.append("Carga Controlada")
                    if t_postural: checkpoint_condutas.append("Reeducação Postural")
                    if conduta_extra: checkpoint_condutas.append(conduta_extra)
                    string_condutas = " | ".join(checkpoint_condutas) if checkpoint_condutas else "Sem restrições"

                    endereco_completo = f"{endereco_base} - {complemento_c}" if complemento_c else endereco_base

                    nova_linha = {
                        "Nome": nome_c, "Telefone": tel_c, "Bairro": bairro_c, 
                        "Plano": plano_c, "Valor": float(valor_c), "Vencimento": int(venc_c), 
                        "Dias": dias_c, "Horario": horario_c, "Status": "Ativo", 
                        "Queixa": string_queixas, "Conduta": string_condutas, "Genero": genero_c, 
                        "Nascimento": nasc_c, "Inicio_Aulas": inicio_c, "CPF": cpf_c, "Endereco": endereco_completo
                    }
                    if "Valor Mensal" in df_alunos.columns:
                        nova_linha["Valor Mensal"] = float(valor_c)

                    df_novo = pd.DataFrame([nova_linha])
                    df_alunos["Valor"] = df_alunos["Valor"].astype(object)
                    df_alunos_atualizado = pd.concat([df_alunos, df_novo], ignore_index=True)

                    conn.update(worksheet="alunos", data=df_alunos_atualizado)
                    st.success(f"🎉 {nome_c} cadastrado com sucesso!")
                    st.cache_data.clear()
                    st.rerun()

# --- 4. TELA: ESPERA ---
elif menu == "⏳ Espera":
    st.title("⏳ Gerenciamento da Lista de Espera")
    if df_espera is not None and not df_espera.empty:
        colunas_exibir = [c for c in ["Nome", "Telefone"] if c in df_espera.columns]
        st.dataframe(df_espera[colunas_exibir], use_container_width=True)
    else:
        st.info("Nenhum prospect aguardando na lista.")
        
    st.markdown("---")
    with st.form("form_novo_prospect_original", clear_on_submit=True):
        nome_esp = st.text_input("Nome do Interessado:")
        tel_esp = st.text_input("Telefone de Contato:")
        btn_adicionar_espera = st.form_submit_button("Adicionar à Lista")
        
        if btn_adicionar_espera:
            if nome_esp and tel_esp:
                nova_linha_espera = {"Nome": nome_esp, "Telefone": tel_esp}
                df_novo_esp = pd.DataFrame([nova_linha_espera])
                if df_espera is None or df_espera.empty or "Nome" not in df_espera.columns:
                    df_espera_atualizado = df_novo_esp
                else:
                    df_espera_atualizado = pd.concat([df_espera, df_novo_esp], ignore_index=True)
                
                conn.update(worksheet="espera", data=df_espera_atualizado)
                st.success(f"✅ {nome_esp} adicionado com sucesso!")
                st.cache_data.clear()
                st.rerun()

# --- 5. TELA: FINANCEIRO ---
elif menu == "💰 Financeiro":
    st.title("💰 Painel Financeiro e de Inadimplência")
    total_recebido, total_pendente = 0.0, 0.0
    
    if df_financeiro is not None and not df_financeiro.empty:
        if "Status" in df_financeiro.columns and "Valor" in df_financeiro.columns:
            df_financeiro["Valor_Num"] = df_financeiro["Valor"].apply(converter_para_float)
            total_recebido = df_financeiro[df_financeiro["Status"].astype(str).str.upper() == "PAGO"]["Valor_Num"].sum()
            total_pendente = df_financeiro[df_financeiro["Status"].astype(str).str.upper() == "PENDENTE"]["Valor_Num"].sum()
            if total_recebido == 0.0 and total_pendente == 0.0:
                total_recebido = df_financeiro["Valor_Num"].sum()
    
    f_col1, f_col2 = st.columns(2)
    with f_col1:
        st.markdown(f'<div style="background-color: #f8f9fa; padding: 22px; border-radius: 8px; border-left: 6px solid #2e7d32;"><p style="margin: 0; font-size: 15px; color: #555; font-weight: bold;">Total Recebido</p><h2 style="margin: 5px 0 0 0; color: #2e7d32; font-size: 32px;">{formatar_brl(total_recebido)}</h2></div>', unsafe_allow_html=True)
    with f_col2:
        st.markdown(f'<div style="background-color: #f8f9fa; padding: 22px; border-radius: 8px; border-left: 6px solid #c62828;"><p style="margin: 0; font-size: 15px; color: #555; font-weight: bold;">Total Pendente</p><h2 style="margin: 5px 0 0 0; color: #c62828; font-size: 32px;">{formatar_brl(total_pendente)}</h2></div>', unsafe_allow_html=True)
        
    st.markdown("<br>### 📥 Dar Baixa em Pagamentos (Busca Universal)")
    if df_alunos is not None and not df_alunos.empty:
        alunos_ativos = df_alunos[df_alunos["Status"].astype(str).str.strip().str.upper() == "ATIVO"] if "Status" in df_alunos.columns else df_alunos
        if not alunos_ativos.empty:
            opcoes_alunos = [f"{r.get('Nome')} | Vencimento: dia {r.get('Vencimento','-')} (Padrão: {formatar_brl(r.get('Valor', 0))})" for _, r in alunos_ativos.iterrows()]
            selecionado_baixa_str = st.selectbox("Selecione o aluno para registrar o pagamento:", options=opcoes_alunos)
            nome_filtrado = selecionado_baixa_str.split(" | ")[0]
            aluno_row_dados = alunos_ativos[alunos_ativos["Nome"] == nome_filtrado].iloc[0]
            
            col_b1, col_b2, col_b3 = st.columns(3)
            with col_b1:
                valor_entrada = st.number_input("Confirmar Valor Pago (R$):", value=converter_para_float(aluno_row_dados.get("Valor", 0)), step=10.0)
            with col_b2:
                forma_pagto = st.selectbox("Forma de Pagamento:", ["PIX", "Dinheiro", "Cartão de Crédito", "Cartão de Débito"])
            with col_b3:
                categoria_pagto = st.selectbox("Categoria do Lançamento:", ["Mensalidade", "Aula Avulsa", "Avaliação", "Outros"])
                
            if st.button("Confirmar Baixa e Registrar", type="primary"):
                data_registro = datetime.now().strftime("%d/%m/%Y")
                nova_linha_financeiro = {"Aluno": nome_filtrado, "Valor": float(valor_entrada), "Data": data_registro, "Forma": forma_pagto, "Categoria": categoria_pagto, "Status": "Pago"}
                if "Valor_Num" in df_financeiro.columns: df_financeiro.drop(columns=["Valor_Num"], inplace=True)
                df_financeiro_atualizado = pd.concat([df_financeiro, pd.DataFrame([nova_linha_financeiro])], ignore_index=True)
                conn.update(worksheet="financeiro", data=df_financeiro_atualizado)
                st.success(f"✅ Pagamento registrado com sucesso!")
                st.cache_data.clear()
                st.rerun()

    st.markdown("<br>### 📋 Histórico Geral de Transações")
    if df_financeiro is not None and not df_financeiro.empty:
        df_financeiro_visivel = df_financeiro[[c for c in df_financeiro.columns if c != "Valor_Num"]].copy()
        if "Valor" in df_financeiro_visivel.columns: df_financeiro_visivel["Valor"] = df_financeiro_visivel["Valor"].apply(formatar_brl)
        st.dataframe(df_financeiro_visivel, use_container_width=True, hide_index=True)

# --- 6. TELA: PERFIL ---
elif menu == "👤 Perfil":
    st.title("👤 Indicadores Estruturais da Base Ativa")
    df_ativos = df_alunos[df_alunos["Status"].astype(str).str.upper() == "ATIVO"] if "Status" in df_alunos.columns else df_alunos.copy()
    if not df_ativos.empty:
        g_col1, g_col2 = st.columns(2)
        with g_col1:
            st.markdown("### Alunos por Tipo de Plano")
            if "Plano" in df_ativos.columns:
                df_planos = df_ativos["Plano"].value_counts().reset_index()
                df_planos.columns = ["Plano", "Quantidade"]
                fig_planos = px.bar(df_planos, y="Plano", x="Quantidade", orientation="h", text="Quantidade", color_discrete_sequence=["#2E5A44"])
                fig_planos.update_layout(xaxis_title="Número de Alunos", yaxis_title="Plano", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_planos, use_container_width=True)
        with g_col2:
            st.markdown("### Distribuição por Gênero")
            if "Genero" in df_ativos.columns:
                st.plotly_chart(px.pie(df_ativos["Genero"].value_counts().reset_index(), names="Genero", values="count", hole=0.3, color_discrete_sequence=["#2E5A44", "#FFD700"]), use_container_width=True)
        
        st.markdown("---")
        g_col3, g_col4 = st.columns(2)
        with g_col3:
            st.markdown("### Perfil de Alunos por Faixa Etária")
            if "Nascimento" in df_ativos.columns:
                idades = [datetime.now().year - pd.to_datetime(n, dayfirst=True).year for n in df_ativos["Nascimento"] if not pd.isna(n)]
                if idades:
                    df_faixas = pd.cut(pd.DataFrame({"Idade": idades})["Idade"], bins=[0, 25, 35, 45, 55, 65, 120], labels=["Até 25", "26-35", "36-45", "46-55", "56-65", "66+"]).value_counts().reset_index()
                    st.plotly_chart(px.bar(df_faixas, x="Idade", y="count", text="count", color_discrete_sequence=["#2E5A44"]).update_layout(plot_bgcolor="rgba(0,0,0,0)"), use_container_width=True)
        with g_col4:
            st.markdown("### Faturamento Projetado por Dia do Mês")
            if "Vencimento" in df_ativos.columns and "Valor" in df_ativos.columns:
                faturamento_por_dia = {dia: 0.0 for dia in range(1, 32)}
                for _, row in df_ativos.iterrows():
                    try:
                        venc = int(row["Vencimento"])
                        val = converter_para_float(row["Valor"])
                        if 1 <= venc <= 31:
                            faturamento_por_dia[venc] += val
                    except:
                        continue
                df_faturamento = pd.DataFrame(list(faturamento_por_dia.items()), columns=["Dia do Vencimento", "Faturamento Projetado"])
                fig_faturamento = px.line(df_faturamento, x="Dia do Vencimento", y="Faturamento Projetado", markers=True, color_discrete_sequence=["#2E5A44"])
                fig_faturamento.update_layout(plot_bgcolor="rgba(0,0,0,0)", xaxis=dict(tickmode='linear', tick0=1, dtick=1))
                st.plotly_chart(fig_faturamento, use_container_width=True)
