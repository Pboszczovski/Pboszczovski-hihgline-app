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
            padding: 10px 0px 10px 0px;
        }
        .prontuario-card {
            background-color: #ffffff !important;
            color: #000000 !important;
            padding: 25px;
            border: 2px solid #2E5A44;
            border-radius: 8px;
            font-family: Arial, sans-serif;
            margin-top: 15px;
            box-shadow: 0px 2px 5px rgba(0,0,0,0.05);
        }
        .prontuario-header {
            text-align: center;
            border-bottom: 3px solid #2E5A44;
            padding-bottom: 10px;
            color: #2E5A44 !important;
            margin-bottom: 20px;
        }
        .prontuario-secao {
            border-bottom: 1px solid #ccc;
            margin-top: 20px;
            padding-bottom: 5px;
            color: #2E5A44 !important;
            font-weight: bold;
        }
        .tabela-prontuario {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }
        .tabela-prontuario td {
            padding: 8px;
            border: 1px solid #ddd;
            color: #000000 !important;
        }
        @media print {
            [data-testid="stSidebar"], .stHeader, footer, .no-print, button, .stMarkdownCmds {
                display: none !important;
            }
            .prontuario-card {
                border: none !important;
                padding: 0 !important;
                box-shadow: none !important;
            }
        }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# FUNÇÕES AUXILIARES DE LIMPEZA E FORMATAÇÃO
# ==========================================
def limpiar_dataframe(df):
    if df is None or df.empty:
        return pd.DataFrame()
    try:
        df = df.loc[:, ~df.columns.astype(str).str.contains('^Unnamed')]
        df.columns = df.columns.str.strip()
        df = df.dropna(how="all")
    except:
        return pd.DataFrame()
    return df

def formatar_brl(valor):
    try:
        if pd.isna(valor) or valor == "" or valor is None:
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
        return "R$ 0,00"

def converter_para_float(valor):
    try:
        if pd.isna(valor) or valor == "" or valor is None:
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

def calcular_idade(data_nasc_str):
    try:
        if pd.isna(data_nasc_str) or not data_nasc_str or str(data_nasc_str).strip() == "":
            return None
        data_nasc = pd.to_datetime(str(data_nasc_str).strip(), dayfirst=True, errors='coerce')
        if pd.isna(data_nasc):
            return None
        hoje = datetime.now()
        return hoje.year - data_nasc.year - ((hoje.month, hoje.day) < (data_nasc.month, data_nasc.day))
    except:
        return None

# ==========================================
# 2. CONEXÃO AUTOMÁTICA COM GOOGLE SHEETS
# ==========================================
conexao_ok = False
erro_msg = ""

df_alunos = pd.DataFrame(columns=["Nome", "Telefone", "Bairro", "Plano", "Valor", "Vencimento", "Dias", "Horario", "Status", "Queixa", "Conduta", "Genero", "Nascimento", "Inicio_Aulas", "CPF", "Endereco"])
df_financeiro = pd.DataFrame(columns=["Aluno", "Valor", "Data", "Forma", "Categoria", "Status"])
df_espera = pd.DataFrame(columns=["Nome", "Telefone"])
df_precos = pd.DataFrame(columns=["Plano", "Valor"])
df_evolucoes = pd.DataFrame(columns=["Data", "Nome do Aluno", "Evolução"])

try:
    if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
        if "private_key" in st.secrets["connections"]["gsheets"]:
            p_key = st.secrets["connections"]["gsheets"]["private_key"]
            if "\\n" in p_key:
                st.secrets["connections"]["gsheets"]["private_key"] = p_key.replace("\\n", "\n")

    conn = st.connection("gsheets", type=GSheetsConnection)
    
    try: df_alunos = limpiar_dataframe(conn.read(worksheet="alunos", ttl=60))
    except: pass
    
    try: df_financeiro = limpiar_dataframe(conn.read(worksheet="financeiro", ttl=60))
    except: pass
    
    try: df_espera = limpiar_dataframe(conn.read(worksheet="espera", ttl=60))
    except: pass
    
    try: df_precos = limpiar_dataframe(conn.read(worksheet="precos", ttl=60))
    except: pass
    
    try: df_evolucoes = limpiar_dataframe(conn.read(worksheet="evolucao", ttl=60))
    except: pass

    if not df_alunos.empty:
        if "Valor Mensal" in df_alunos.columns and "Valor" not in df_alunos.columns:
            df_alunos["Valor"] = df_alunos["Valor Mensal"]
        elif "Valor Mensal" in df_alunos.columns and "Valor" in df_alunos.columns:
            df_alunos["Valor"] = df_alunos["Valor"].fillna(df_alunos["Valor Mensal"])

    conexao_ok = True
except Exception as e:
    erro_msg = str(e)

dict_precos_padrao = {}
if df_precos is not None and not df_precos.empty and "Plano" in df_precos.columns:
    for _, r in df_precos.iterrows():
        dict_precos_padrao[str(r["Plano"])] = converter_para_float(r["Valor"])
else:
    dict_precos_padrao = {"1x semana": 180.0, "2x semana": 220.0, "3x semana": 300.0}

def verificar_lotacao(df, dias_input, horarios_input_list, aluno_ignorados=None):
    if df is None or df.empty or "Status" not in df.columns or "Dias" not in df.columns or "Horario" not in df.columns:
        return [], []
        
    df_ativos = df[df["Status"].astype(str).str.upper() == "ATIVO"]
    if aluno_ignorados:
        df_ativos = df_ativos[df_ativos["Nome"] != aluno_ignorados]
        
    dias_solicitados = [d.strip().upper() for d in str(dias_input).replace("/", " ").replace(",", " ").split() if d.strip()]
    horarios_solicitados = [str(h).strip() for h in horarios_input_list if str(h).strip()]
    
    if not horarios_solicitados or not dias_solicitados:
        return [], []
        
    conflitos = []
    
    for h_alvo in horarios_solicitados:
        for dia in dias_solicitados:
            qtd_no_bloco = 0
            for idx, row in df_ativos.iterrows():
                h_atual = str(row["Horario"]).strip()
                if h_atual == h_alvo:
                    d_atual = [d.strip().upper() for d in str(row["Dias"]).replace("/", " ").replace(",", " ").split() if d.strip()]
                    if dia in d_atual:
                        qtd_no_bloco += 1
            if qtd_no_bloco >= 3:
                conflitos.append((dia, h_alvo, qtd_no_bloco))
                
    return conflitos, []

# ==========================================
# 3. BARRA LATERAL - LOGO LOCAL E MENU
# ==========================================
with st.sidebar:
    st.markdown('<div class="logo-container">', unsafe_allow_html=True)
    if os.path.exists("Highline Logo.png"):
        st.image("Highline Logo.png", use_container_width=True)
    else:
        st.markdown("<h1 style='text-align: center; margin-bottom: 20px; font-size: 45px;'>🏋️‍♂️</h1>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center; color: white; margin-top: -20px; font-family: sans-serif; letter-spacing: 1px;'>Highline</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #FFD700; font-size: 12px; text-transform: uppercase; letter-spacing: 2px;'>Management</p>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
        
    st.markdown("🔒 **Menu de Navegação**")
    
    menu = st.radio(
        "",
        [
            "📅 Agenda",
            "👥 Alunos",
            "📝 Cadastro",
            "📈 Evolução",
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

LISTA_QUEIXAS_PADRAO = [
    "Dor Lombar (Lombalgia)",
    "Hérnia de Disco / Protrusão",
    "Dor / Lesão nos Ombros",
    "Dor Cervical (Cervicalgia)",
    "Dor / Lesão nos Joelhos",
    "Melhoria Postural Operacional",
    "Pilates para Gestantes",
    "Pilates para Terceira Idade (Idosos)",
    "Condicionamento Físico Geral"
]

# --- 1. TELA: AGENDA ---
if menu == "📅 Agenda":
    st.title("📅 Agenda de Treinos")
    hoje_datetime = datetime.now()
    hoje_mm_dd = hoje_datetime.strftime("%m-%d")
    niver_hoje = []
    
    if not df_alunos.empty and "Nascimento" in df_alunos.columns and "Nome" in df_alunos.columns:
        for idx, row in df_alunos.iterrows():
            try:
                if pd.notna(row["Nascimento"]) and str(row["Nascimento"]).strip() != "":
                    data_nasc = pd.to_datetime(str(row["Nascimento"]).strip(), dayfirst=True, errors='coerce')
                    if not pd.isna(data_nasc) and data_nasc.strftime("%m-%d") == hoje_mm_dd:
                        niver_hoje.append(row["Nome"])
            except:
                continue
                
    if niver_hoje:
        st.info(f"🎉 **Hoje é aniversário de:** {', '.join(niver_hoje)}! 🎂")
        
    dia_semana_num = hoje_datetime.weekday()
    if dia_semana_num == 0:     dias_validos_busca, nome_dia_formatado = ["SEG", "2A", "SEGUNDA"], "Segunda-feira"
    elif dia_semana_num == 1:   dias_validos_busca, nome_dia_formatado = ["TER", "3A", "TERÇA", "TERCA"], "Terça-feira"
    elif dia_semana_num == 2:   dias_validos_busca, nome_dia_formatado = ["QUA", "4A", "QUARTA"], "Quarta-feira"
    elif dia_semana_num == 3:   dias_validos_busca, nome_dia_formatado = ["QUI", "5A", "QUINTA"], "Quinta-feira"
    elif dia_semana_num == 4:   dias_validos_busca, nome_dia_formatado = ["SEX", "6A", "SEXTA"], "Sexta-feira"
    elif dia_semana_num == 5:   dias_validos_busca, nome_dia_formatado = ["SAB", "SÁBADO", "SABADO"], "Sábado"
    else:                       dias_validos_busca, nome_dia_formatado = ["DOM", "DOMINGO"], "Domingo"

    st.markdown(f"### 📋 Horários Agendados para Hoje ({nome_dia_formatado})")
    
    if not df_alunos.empty and "Status" in df_alunos.columns:
        df_ativos = df_alunos[df_alunos["Status"].astype(str).str.upper() == "ATIVO"]
        
        if not df_ativos.empty:
            if "Dias" in df_ativos.columns:
                condicao_dia = df_ativos["Dias"].astype(str).str.upper().apply(lambda x: any(termo in x for termo in dias_validos_busca))
                df_agenda = df_ativos[condicao_dia]
            else:
                df_agenda = df_ativos.copy()
                
            if not df_agenda.empty and "Horario" in df_agenda.columns:
                df_agenda = df_agenda.sort_values(by="Horario")
                colunas_agenda = [c for c in ["Horario", "Nome", "Status", "Queixa", "Conduta", "Dias"] if c in df_agenda.columns]
                st.dataframe(df_agenda[colunas_agenda], use_container_width=True, hide_index=True)
            else:
                st.warning(f"Nenhum aluno agendado para esta {nome_dia_formatado}.")
        else:
            st.warning("Nenhum aluno ativo encontrado.")
    else:
        st.warning("Nenhum aluno cadastrado.")

# --- 2. TELA: ALUNOS ---
elif menu == "👥 Alunos":
    st.title("👥 Base de Alunos Ativos")
    
    if not df_alunos.empty and "Status" in df_alunos.columns:
        df_ativos = df_alunos[df_alunos["Status"].astype(str).str.upper() == "ATIVO"]
    else:
        df_ativos = pd.DataFrame()

    if not df_ativos.empty:
        st.metric("Total de Alunos Ativos Atualmente", len(df_ativos))
        busca = st.text_input("🔍 Filtrar aluno por nome na tabela:", placeholder="Digite o nome do aluno...")
        df_ativos_tabela = df_ativos[df_ativos["Nome"].astype(str).str.contains(busca, case=False, na=False)] if busca else df_ativos
        
        df_ativos_visivel = df_ativos_tabela.copy()
        if "Valor" in df_ativos_visivel.columns:
            df_ativos_visivel["Valor"] = df_ativos_visivel["Valor"].apply(formatar_brl)
        
        st.dataframe(df_ativos_visivel, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown("### ✏️ Alteração Rápida e Gerenciamento de Alunos")
        
        opcoes_alunos = ["-- Escolha um Aluno --"] + [f"{row['Nome']} (Reg: {idx})" for idx, row in df_ativos.iterrows()]
        aluno_selecionado_str = st.selectbox("Selecione um aluno ativo para alterar dados ou desativar:", opcoes_alunos)
        
        if aluno_selecionado_str != "-- Escolha um Aluno --":
            idx_real_planilha = int(aluno_selecionado_str.split("(Reg: ")[1].replace(")", ""))
            dados_atuais = df_alunos.loc[idx_real_planilha]
            aluno_para_editar = dados_atuais["Nome"]
            
            c_ed1, c_ed2, c_ed3 = st.columns(3)
            with c_ed1:
                options_planos = ["1x semana", "2x semana", "3x semana"]
                plano_atual = dados_atuais.get("Plano", "1x semana")
                idx_plano = options_planos.index(plano_atual) if plano_atual in options_planos else 0
                novo_plano = st.selectbox("Novo Plano Contratado:", options_planos, index=idx_plano)
                novo_valor = st.number_input("Confirmar Valor Mensal (R$):", value=converter_para_float(dados_atuais.get("Valor", 220.0)))
                
            with c_ed2:
                novos_dias = st.text_input("Novos Dias de Aula (Ex: Ter/Qui):", value=str(dados_atuais.get("Dias", "")))
                novo_horario = st.text_input("Novo Horário (Ex: 08:30):", value=str(dados_atuais.get("Horario", "")))
                
            bloqueio_edicao = False
            if novos_dias and novo_horario:
                conflitos_ed, _ = verificar_lotacao(df_alunos, novos_dias, [novo_horario], aluno_ignorados=aluno_para_editar)
                if conflitos_ed:
                    bloqueio_edicao = True
                    for dia_conf, hora_conf, qtd in conflitos_ed:
                        st.error(f"❌ Horário lotado em {dia_conf} às {hora_conf} ({qtd}/3 alunos).")
            
            with c_ed3:
                st.markdown("**Ações Disponíveis:**")
                btn_salvar_alt = st.button("💾 Gravar Alterações", disabled=bloqueio_edicao)
                btn_inativar_alt = st.button("❌ Mover ao Arquivo Morto")
            
            st.markdown("#### 🩺 Atualizar Anamnese: Queixas Principais e Sintomas")
            queixa_atual_str = str(dados_atuais.get("Queixa", ""))
            
            c_ch1, c_ch2, c_ch3 = st.columns(3)
            with c_ch1:
                ed_q_lombar = st.checkbox("Dor Lombar (Lombalgia)", value=("Dor Lombar (Lombalgia)" in queixa_atual_str))
                ed_q_cervical = st.checkbox("Dor Cervical (Cervicalgia)", value=("Dor Cervical (Cervicalgia)" in queixa_atual_str))
                ed_q_gestante = st.checkbox("Pilates para Gestantes", value=("Pilates para Gestantes" in queixa_atual_str))
            with c_ch2:
                ed_q_hernia = st.checkbox("Hérnia de Disco / Protrusão", value=("Hérnia de Disco / Protrusão" in queixa_atual_str))
                ed_q_joelhos = st.checkbox("Dor / Lesão nos Joelhos", value=("Dor / Lesão nos Joelhos" in queixa_atual_str))
                ed_q_idoso = st.checkbox("Pilates para Terceira Idade (Idosos)", value=("Pilates para Terceira Idade (Idosos)" in queixa_atual_str))
            with c_ch3:
                ed_q_ombros = st.checkbox("Dor / Lesão nos Ombros", value=("Dor / Lesão nos Ombros" in queixa_atual_str))
                ed_q_postural = st.checkbox("Melhoria Postural Operacional", value=("Melhoria Postural Operacional" in queixa_atual_str))
                ed_q_condic = st.checkbox("Condicionamento Físico Geral", value=("Condicionamento Físico Geral" in queixa_atual_str))
            
            termos_limpos = []
            for t in queixa_atual_str.split(" | "):
                t_strip = t.strip()
                if t_strip and t_strip not in LISTA_QUEIXAS_PADRAO and t_strip.upper() != "NAN":
                    termos_limpos.append(t_strip)
            queixas_adicionais_existentes = " | ".join(termos_limpos)
            
            ed_queixa_extra = st.text_input("Outras Queixas Adicionais / Observações Clínicas:", value=queixas_adicionais_existentes)
            
            conduta_atual = str(dados_atuais.get("Conduta", ""))
            if conduta_atual.lower() == "nan" or conduta_atual.strip() == "":
                conduta_atual = ""
            ed_conduta_extra = st.text_input("Diretrizes de Conduta Específicas:", value=conduta_atual)
            
            if btn_salvar_alt and not bloqueio_edicao:
                novos_tratamentos = []
                mapeamento_check = [
                    ("Dor Lombar (Lombalgia)", ed_q_lombar),
                    ("Hérnia de Disco / Protrusão", ed_q_hernia),
                    ("Dor / Lesão nos Ombros", ed_q_ombros),
                    ("Dor Cervical (Cervicalgia)", ed_q_cervical),
                    ("Dor / Lesão nos Joelhos", ed_q_joelhos),
                    ("Melhoria Postural Operacional", ed_q_postural),
                    ("Pilates para Gestantes", ed_q_gestante),
                    ("Pilates para Terceira Idade (Idosos)", ed_q_idoso),
                    ("Condicionamento Físico Geral", ed_q_condic)
                ]
                
                for nome_queixa, marcado in mapeamento_check:
                    if marcado:
                        novos_tratamentos.append(nome_queixa)
                        
                if ed_queixa_extra.strip(): 
                    novos_tratamentos.append(ed_queixa_extra.strip())
                
                df_alunos.at[idx_real_planilha, "Plano"] = novo_plano
                df_alunos.at[idx_real_planilha, "Valor"] = float(novo_valor)  
                df_alunos.at[idx_real_planilha, "Dias"] = novos_dias
                df_alunos.at[idx_real_planilha, "Horario"] = novo_horario
                df_alunos.at[idx_real_planilha, "Queixa"] = " | ".join(novos_tratamentos) if novos_tratamentos else ""
                df_alunos.at[idx_real_planilha, "Conduta"] = ed_conduta_extra.strip()
                
                conn.update(worksheet="alunos", data=df_alunos)
                st.success("🎉 Alterações salvas no banco de dados!")
                st.cache_data.clear()
                
            if btn_inativar_alt:
                df_alunos.at[idx_real_planilha, "Status"] = "Inativo"
                conn.update(worksheet="alunos", data=df_alunos)
                st.success("❌ Aluno arquivado!")
                st.cache_data.clear()
    else:
        st.info("Nenhum aluno ativo cadastrado.")

# --- 3. TELA: CADASTRO ---
elif menu == "📝 Cadastro":
    st.title("📝 Cadastro e Anamnese Estruturada")
    
    with st.form("form_dados_anamnese_completo", clear_on_submit=True):
        st.subheader("📌 Escolha de Dias e Horários de Treino")
        c_dia1, c_dia2, c_dia3, c_dia4, c_dia5, c_dia6 = st.columns(6)
        with c_dia1: d_seg = st.checkbox("SEG")
        with c_dia2: d_ter = st.checkbox("TER")
        with c_dia3: d_qua = st.checkbox("QUA")
        with c_dia4: d_qui = st.checkbox("QUI")
        with c_dia5: d_sex = st.checkbox("SEX")
        with c_dia6: d_sab = st.checkbox("SAB")
        
        lista_horarios_disponiveis = ["7:30", "8:30", "9:30", "10:30", "11:30", "12:30", "15:30", "16:30", "17:30", "18:30", "19:30"]
        st.markdown("**Horários Disponíveis (Selecione um ou mais):**")
        cols_horarios = st.columns(6)
        horarios_selecionados = []
        for index, hora_item in enumerate(lista_horarios_disponiveis):
            with cols_horarios[index % 6]:
                if st.checkbox(hora_item, key=f"cad_h_{hora_item}"):
                    horarios_selecionados.append(hora_item)

        st.subheader("1. Dados Pessoais e de Contrato")
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            plano_c = st.selectbox("Plano Contratado:", ["1x semana", "2x semana", "3x semana"])
        with col_p2:
            valor_c = st.number_input("Valor Combinado Mensal (R$):", value=float(dict_precos_padrao.get(plano_c, 220.0)))

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
        st.write("Marque abaixo todas as condições clínicas e objetivos aplicáveis a este aluno:")
        
        t_lombar = st.checkbox("Dor Lombar (Lombalgia)", key="k_lombar")
        t_cervical = st.checkbox("Dor Cervical (Cervicalgia)", key="k_cervical")
        t_gestante = st.checkbox("Pilates para Gestantes", key="k_gestante")
        t_hernia = st.checkbox("Hérnia de Disco / Protrusão", key="k_hernia")
        t_joelhos = st.checkbox("Dor / Lesão nos Joelhos", key="k_joelhos")
        t_idoso = st.checkbox("Pilates para Terceira Idade (Idosos)", key="k_idoso")
        t_ombros = st.checkbox("Dor / Lesão nos Ombros", key="k_ombros")
        t_postural = st.checkbox("Melhoria Postural Operacional", key="k_postural")
        t_condic = st.checkbox("Condicionamento Físico Geral", key="k_condic")
            
        queixa_extra = st.text_input("Outras Queixas Adicionais / Observações Clínicas:")
        conduta_extra = st.text_input("Diretrizes de Conduta Específicas:")

        btn_enviar = st.form_submit_button("💾 Salvar Novo Aluno")
        
        if btn_enviar:
            dias_lista = [dia for dia, marcado in [("SEG", d_seg), ("TER", d_ter), ("QUA", d_qua), ("QUI", d_qui), ("SEX", d_sex), ("SAB", d_sab)] if marcado]
            dias_c = "/".join(dias_lista)
            horario_c = ", ".join(horarios_selecionados)

            if not dias_c or not horario_c:
                st.error("❌ Selecione pelo menos um Dia e Horário!")
            elif not nome_c or not tel_c:
                st.error("❌ Preencha o Nome e o WhatsApp!")
            else:
                conflitos, _ = verificar_lotacao(df_alunos, dias_c, horarios_selecionados)
                if conflitos:
                    for dia_lotado, hora_lotada, qtd in conflitos:
                        st.error(f"🛑 O dia {dia_lotado} às {hora_lotada} atingiu o limite máximo ({qtd}/3 alunos).")
                else:
                    tratamentos = []
                    mapeamento_cadastro = [
                        ("Dor Lombar (Lombalgia)", t_lombar),
                        ("Hérnia de Disco / Protrusão", t_hernia),
                        ("Dor / Lesão nos Ombros", t_ombros),
                        ("Dor Cervical (Cervicalgia)", t_cervical),
                        ("Dor / Lesão nos Joelhos", t_joelhos),
                        ("Melhoria Postural Operacional", t_postural),
                        ("Pilates para Gestantes", t_gestante),
                        ("Pilates para Terceira Idade (Idosos)", t_idoso),
                        ("Condicionamento Físico Geral", t_condic)
                    ]
                    
                    for nome_queixa, marcado in mapeamento_cadastro:
                        if marcado:
                            tratamentos.append(nome_queixa)
                            
                    if queixa_extra.strip(): 
                        tratamentos.append(queixa_extra.strip())
                    
                    nova_linha = {
                        "Nome": nome_c, "Telefone": tel_c, "Bairro": bairro_c, "Plano": plano_c, 
                        "Valor": float(valor_c), "Vencimento": int(venc_c), "Dias": dias_c, "Horario": horario_c, 
                        "Status": "Ativo", "Queixa": " | ".join(tratamentos), "Conduta": conduta_extra.strip(), 
                        "Genero": genero_c, "Nascimento": nasc_c, "Inicio_Aulas": inicio_c, "CPF": cpf_c, 
                        "Endereco": f"{endereco_base} {complemento_c}".strip()
                    }
                    
                    df_alunos = pd.concat([df_alunos, pd.DataFrame([nova_linha])], ignore_index=True)
                    conn.update(worksheet="alunos", data=df_alunos)
                    st.success(f"🎉 Aluno {nome_c} adicionado com sucesso!")
                    st.cache_data.clear()

# --- 4. TELA: EVOLUÇÃO ---
elif menu == "📈 Evolução":
    st.title("📈 Evolução Clínica dos Alunos")
    
    lista_nomes_alunos = sorted(list(df_alunos["Nome"].dropna().unique())) if not df_alunos.empty else []
    
    with st.form("form_nova_evolucao", clear_on_submit=True):
        nome_aluno_evol = st.selectbox("Selecione o Aluno:", lista_nomes_alunos)
        texto_evol = st.text_area("Registro de Evolução/Conduta do dia:")
        data_registro = st.date_input("Data do Registro:", datetime.now())
        
        if st.form_submit_button("Salvar Evolução"):
            if not texto_evol.strip():
                st.error("❌ Digite um texto descritivo para salvar.")
            else:
                nova_evol = {"Data": data_registro.strftime("%d/%m/%Y"), "Nome do Aluno": nome_aluno_evol, "Evolução": texto_evol}
                df_evolucoes = pd.concat([df_evolucoes, pd.DataFrame([nova_evol])], ignore_index=True)
                conn.update(worksheet="evolucao", data=df_evolucoes)
                st.success("🎉 Evolução registrada com sucesso!")
                st.cache_data.clear()

    st.markdown("---")
    
    if not df_alunos.empty:
        opcoes_filtro = ["Todos"] + sorted(list(df_alunos["Nome"].dropna().unique()))
        aluno_filtro = st.selectbox("Ver histórico do aluno:", opcoes_filtro)
        
        if not df_evolucoes.empty:
            df_exibicao = df_evolucoes if aluno_filtro == "Todos" else df_evolucoes[df_evolucoes["Nome do Aluno"] == aluno_filtro]
            st.dataframe(df_exibicao.sort_index(ascending=False), use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum registro clínico encontrado.")

# --- 5. TELA: ESPERA ---
elif menu == "⏳ Espera":
    st.title("⏳ Gerenciamento da Lista de Espera")
    if not df_espera.empty:
        st.dataframe(df_espera[["Nome", "Telefone"]], use_container_width=True, hide_index=True)
        
    with st.form("form_espera", clear_on_submit=True):
        nome_esp = st.text_input("Nome do Interessado:")
        tel_esp = st.text_input("Telefone de Contato:")
        if st.form_submit_button("Adicionar à Lista") and nome_esp:
            df_espera = pd.concat([df_espera, pd.DataFrame([{"Nome": nome_esp, "Telefone": tel_esp}])], ignore_index=True)
            conn.update(worksheet="espera", data=df_espera)
            st.success("✅ Adicionado!")
            st.cache_data.clear()

# --- 6. TELA: FINANCEIRO ---
elif menu == "💰 Financeiro":
    st.title("💰 Painel Financeiro")
    total_recebido = df_financeiro[df_financeiro["Status"].astype(str).str.upper() == "PAGO"]["Valor"].apply(converter_para_float).sum() if not df_financeiro.empty and "Status" in df_financeiro.columns else 0.0
    total_pendente = df_financeiro[df_financeiro["Status"].astype(str).str.upper() == "PENDENTE"]["Valor"].apply(converter_para_float).sum() if not df_financeiro.empty and "Status" in df_financeiro.columns else 0.0
    
    f_col1, f_col2 = st.columns(2)
    with f_col1: st.metric("Total Recebido", formatar_brl(total_recebido))
    with f_col2: st.metric("Total Pendente", formatar_brl(total_pendente))
        
    st.markdown("### 📥 Registrar Baixa de Pagamento")
    if not df_alunos.empty and "Status" in df_alunos.columns:
        opcoes_baixa = [f"{r['Nome']} | Vencimento: {r.get('Vencimento','10')} | Valor: {formatar_brl(r.get('Valor', 0))}" for _, r in df_alunos.iterrows() if str(r.get("Status")).upper() == "ATIVO"]
        if opcoes_baixa:
            sel_baixa = st.selectbox("Selecione o aluno:", opcoes_baixa)
            nome_f = sel_baixa.split(" | ")[0]
            
            row_aluno_atual = df_alunos[df_alunos["Nome"] == nome_f].iloc[0]
            v_sugerido = converter_para_float(row_aluno_atual.get("Valor", 0.0))
            
            val_baixa_input = st.number_input("Valor Recebido (R$):", value=v_sugerido, step=10.0)
            
            if st.button("Confirmar Pagamento"):
                nova_baixa = {
                    "Aluno": nome_f, 
                    "Valor": float(val_baixa_input), 
                    "Data": datetime.now().strftime("%d/%m/%Y"), 
                    "Forma": "PIX", 
                    "Categoria": "Mensalidade", 
                    "Status": "PAGO"
                }
                
                df_financeiro = pd.concat([df_financeiro, pd.DataFrame([nova_baixa])], ignore_index=True)
                
                try:
                    conn.update(worksheet="financeiro", data=df_financeiro)
                    st.success(f"🎉 Pagamento de {nome_f} gravado com sucesso!")
                    st.cache_data.clear()
                except Exception as api_err:
                    st.error("🛑 Erro de Gravação na Planilha!")
                    st.info(f"Detalhe técnico do erro: {api_err}")
                
    st.markdown("---")
    st.markdown("### 📊 Histórico de Transações")
    if not df_financeiro.empty:
        df_fin_exibicao = df_financeiro.copy()
        if "Valor" in df_fin_exibicao.columns:
            df_fin_exibicao["Valor"] = df_fin_exibicao["Valor"].apply(formatar_brl)
        st.dataframe(df_fin_exibicao, use_container_width=True, hide_index=True)

# --- 7. TELA: PERFIL ---
elif menu == "👤 Perfil":
    st.title("👤 Configurações de Perfil e Estatísticas")
    st.write(f"**Conexão do Banco de Dados:** {'Operacional' if conexao_ok else 'Erro de Comunicação'}")
    if erro_msg: st.error(erro_msg)
    
    st.markdown("---")
    st.markdown("### 📊 Métricas e Previsões Estatísticas")
    
    if not df_alunos.empty and "Status" in df_alunos.columns:
        try:
            df_ativos_graficos = df_alunos[df_alunos["Status"].astype(str).str.upper() == "ATIVO"].copy()
            if df_ativos_graficos.empty:
                df_ativos_graficos = df_alunos.copy()
                
            cg1, cg2 = st.columns(2)
            
            with cg1:
                st.markdown("#### Distribuição dos Alunos por Faixa Etária")
                if "Nascimento" in df_ativos_graficos.columns:
                    df_ativos_graficos["Idade"] = df_ativos_graficos["Nascimento"].apply(calcular_idade)
                    
                    df_validos = df_ativos_graficos.dropna(subset=["Idade"])
                    if not df_validos.empty:
                        def categorizar_faixa(idade):
                            try:
                                id_int = int(idade)
                                if id_int < 18: return "Menor de 18"
                                elif id_int <= 29: return "18-29 anos"
                                elif id_int <= 45: return "30-45 anos"
                                elif id_int <= 60: return "46-60 anos"
                                else: return "Acima de 60"
                            except:
                                return "Não Informado"
                                
                        df_ativos_graficos["Faixa Etária"] = df_ativos_graficos["Idade"].apply(categorizar_faixa)
                        df_faixa = df_ativos_graficos["Faixa Etária"].value_counts().reset_index()
                        df_faixa.columns = ["Faixa Etária", "Quantidade"]
                        
                        fig_faixa = px.bar(df_faixa, x="Faixa Etária", y="Quantidade", text="Quantidade", color_discrete_sequence=["#FFD700"])
                        fig_faixa.update_layout(margin=dict(l=20, r=20, t=10, b=20), height=300)
                        st.plotly_chart(fig_faixa, use_container_width=True)
                    else:
                        st.info("Aguardando inserção de idades estruturadas para exibição térmica.")
                else:
                    st.info("Coluna 'Nascimento' ausente.")
                    
            with cg2:
                st.markdown("#### Previsão de Recebimento Mensal (Por Dia de Vencimento)")
                if "Vencimento" in df_ativos_graficos.columns and "Valor" in df_ativos_graficos.columns:
                    df_ativos_graficos["Valor_Float"] = df_ativos_graficos["Valor"].apply(converter_para_float)
                    df_ativos_graficos["Dia Vencimento"] = df_ativos_graficos["Vencimento"].fillna(10).astype(str)
                    
                    df_prev = df_ativos_graficos.groupby("Dia Vencimento")["Valor_Float"].sum().reset_index()
                    if not df_prev.empty:
                        fig_prev = px.bar(df_prev, x="Dia Vencimento", y="Valor_Float", text="Valor_Float", color_discrete_sequence=["#2E5A44"])
                        fig_prev.update_traces(texttemplate='R$ %{text:,.2f}', textposition='outside')
                        fig_prev.update_layout(margin=dict(l=20, r=20, t=10, b=20), height=300, yaxis_title="Total Previsto (R$)", xaxis_title="Dia do Mês")
                        st.plotly_chart(fig_prev, use_container_width=True)
                else:
                    st.info("Dados insuficientes para calcular previsões financeiras.")
                    
            cg3, cg4 = st.columns(2)
            with cg3:
                st.markdown("#### Alunos por Tipo de Plano")
                if "Plano" in df_ativos_graficos.columns and not df_ativos_graficos["Plano"].dropna().empty:
                    df_contagem_plano = df_ativos_graficos["Plano"].value_counts().reset_index()
                    df_contagem_plano.columns = ["Plano", "Quantidade"]
                    fig1 = px.bar(df_contagem_plano, x="Plano", y="Quantidade", text="Quantidade", color_discrete_sequence=["#2E5A44"])
                    fig1.update_layout(margin=dict(l=20, r=20, t=10, b=20), height=300)
                    st.plotly_chart(fig1, use_container_width=True)
                else:
                    st.info("Sem dados de planos cadastrados.")
            with cg4:
                st.markdown("#### Distribuição por Gênero")
                if "Genero" in df_ativos_graficos.columns and not df_ativos_graficos["Genero"].dropna().empty:
                    df_contagem_genero = df_ativos_graficos["Genero"].value_counts().reset_index()
                    df_contagem_genero.columns = ["Gênero", "Quantidade"]
                    fig2 = px.pie(df_contagem_genero, names="Gênero", values="Quantidade", color_discrete_sequence=["#2E5A44", "#FFD700", "#7f7f7f"])
                    fig2.update_layout(margin=dict(l=20, r=20, t=10, b=20), height=300)
                    st.plotly_chart(fig2, use_container_width=True)
                else:
                    st.info("Sem dados de gêneros.")
        except Exception as graph_err:
            st.warning("⚠️ O motor gráfico detectou dados inconsistentes e foi pausado para evitar crash.")
    else:
        st.info("Nenhum gráfico para exibir. Adicione alunos no banco de dados.")

# --- 8. TELA: PREÇOS ---
elif menu == "⚙️ Preços":
    st.title("⚙️ Tabela de Preços Base")
    df_precos_exibicao = pd.DataFrame(list(dict_precos_padrao.items()), columns=["Plano de Treinamento", "Valor Sugerido"])
    df_precos_exibicao["Valor Sugerido"] = df_precos_exibicao["Valor Sugerido"].apply(formatar_brl)
    st.dataframe(df_precos_exibicao, use_container_width=True, hide_index=True)

# --- 9. TELA: ARQUIVO MORTO ---
elif menu == "📁 Arquivo Morto":
    st.title("📁 Alunos Inativos")
    if not df_alunos.empty and "Status" in df_alunos.columns:
        st.dataframe(df_alunos[df_alunos["Status"].astype(str).str.upper() == "INATIVO"], use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum registro inativo encontrado.")

# --- 10. TELA: IMPRIMIR PRONTUÁRIO ---
elif menu == "🖨️ Imprimir Prontuário":
    st.title("🖨️ Ficha Cadastral e Prontuário do Aluno")
    
    if not df_alunos.empty and "Nome" in df_alunos.columns:
        lista_prontuario_geral = sorted(list(df_alunos["Nome"].dropna().unique()))
        aluno_p = st.selectbox("Selecione o Aluno para Emitir Documentação:", lista_prontuario_geral)
        
        if aluno_p:
            dados = df_alunos[df_alunos["Nome"] == aluno_p].iloc[0]
            evolucoes_aluno = df_evolucoes[df_evolucoes["Nome do Aluno"] == aluno_p] if not df_evolucoes.empty and "Nome do Aluno" in df_evolucoes.columns else pd.DataFrame()
            
            html_evolucoes = ""
            if not evolucoes_aluno.empty:
                for _, r in evolucoes_aluno.sort_index(ascending=False).iterrows():
                    html_evolucoes += f"<p style='margin:4px 0; border-bottom:1px dashed #eee; padding-bottom:4px; color:#000000;'><b>{r['Data']}:</b> {r['Evolução']}</p>"
            else:
                html_evolucoes = "<p style='color: #777; font-style: italic;'>Nenhum histórico clínico lançado para este aluno.</p>"
            
            conduta_doc = dados.get('Conduta', '')
            if pd.isna(conduta_doc) or str(conduta_doc).lower().strip() == 'nan' or str(conduta_doc).strip() == '':
                conduta_doc = 'Sem restrições ou condutas excepcionais mapeadas.'

            st.write(f"""
            <div class="prontuario-card">
                <div class="prontuario-header">
                    <h2 style="margin:0; letter-spacing: 1px; color:#2E5A44;">STUDIO HIGHLINE PILATES</h2>
                    <span style="font-size:12px; text-transform: uppercase; color:#555;">Ficha Prontuário de Acompanhamento Técnico</span>
                </div>
                <table class="tabela-prontuario">
                    <tr>
                        <td style="width:50%;"><b>Nome do Aluno:</b> {dados.get('Nome', '-')}</td>
                        <td style="width:50%;"><b>CPF:</b> {dados.get('CPF', '-')}</td>
                    </tr>
                    <tr>
                        <td><b>WhatsApp / Contato:</b> {dados.get('Telefone', '-')}</td>
                        <td><b>Data de Nascimento:</b> {dados.get('Nascimento', '-')}</td>
                    </tr>
                    <tr>
                        <td><b>Gênero:</b> {dados.get('Genero', '-')}</td>
                        <td><b>Início das Atividades:</b> {dados.get('Inicio_Aulas', '-')}</td>
                    </tr>
                    <tr>
                        <td><b>Plano Vinculado:</b> {dados.get('Plano', '-')}</td>
                        <td><b>Grade Horária Fixa:</b> {dados.get('Dias', '-')} às {dados.get('Horario', '-')}</td>
                    </tr>
                    <tr>
                        <td colspan="2"><b>Endereço Residencial:</b> {dados.get('Endereco', '-')} (Bairro: {dados.get('Bairro', '-')})</td>
                    </tr>
                </table>
                <div class="prontuario-secao">📌 HISTÓRICO DE QUEIXAS E SINTOMAS (ANAMNESE)</div>
                <p style="margin: 10px 0; line-height: 1.5; font-size:14px; color:#000000;">{dados.get('Queixa', 'Nenhuma queixa inicial registrada.')}</p>
                <div class="prontuario-secao">🎯 DIRETRIZES TÉCNICAS E RESTRIÇÕES DE CONDUTA</div>
                <p style="margin: 10px 0; line-height: 1.5; font-size:14px; color:#000000;">{conduta_doc}</p>
                <div class="prontuario-secao">📈 REGISTROS DE EVOLUÇÕES CLÍNICAS</div>
                <div style="background-color:#fafafa; padding:12px; border-radius:4px; border:1px solid #eee; margin-top:10px; font-size:13px; max-height: 400px; overflow-y: auto;">
                    {html_evolucoes}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.write("")
            st.markdown("<p class='no-print' style='color:#666; font-size:13px;'>💡 <b>Suporte para Impressão limpa:</b> Pressione <b>Ctrl + P</b> (ou <b>Cmd + P</b> no Mac). A barra lateral verde e os botões serão ocultados de forma automática na folha.</p>", unsafe_allow_html=True)
    else:
        st.info("Nenhum registro de aluno cadastrado no banco de dados para montagem do prontuário.")
