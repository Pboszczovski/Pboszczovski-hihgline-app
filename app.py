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
        .price-card {
            background-color: #f8f9fa;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            margin-bottom: 15px;
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
# 2. CONEXÃO COM GOOGLE SHEETS (COM CACHE)
# ==========================================
conexao_ok = False
erro_msg = ""

df_alunos = pd.DataFrame(columns=["Nome", "Telefone", "Bairro", "Plano", "Valor", "Vencimento", "Dias", "Horario", "Status", "Queixa", "Conduta", "Genero", "Nascimento", "Inicio_Aulas", "CPF", "Endereco"])
df_financeiro = pd.DataFrame(columns=["Aluno", "Valor", "Data", "Forma", "Categoria", "Status"])
df_espera = pd.DataFrame(columns=["Nome", "Telefone", "Dia Preferencia", "Hora Preferencia"])
df_precos = pd.DataFrame(columns=["Plano", "Valor"])
df_evolucoes = pd.DataFrame(columns=["Data", "Nome do Aluno", "Evolução"])

try:
    if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
        if "private_key" in st.secrets["connections"]["gsheets"]:
            p_key = st.secrets["connections"]["gsheets"]["private_key"]
            if "\\n" in p_key:
                p_key = p_key.replace("\\n", "\n")

    conn = st.connection("gsheets", type=GSheetsConnection)
    
    @st.cache_data(ttl=15)
    def ler_dados_planilha(aba):
        return conn.read(worksheet=aba)
    
    try: df_alunos = limpiar_dataframe(ler_dados_planilha("alunos"))
    except: df_alunos = pd.DataFrame()
    
    try: df_financeiro = limpiar_dataframe(ler_dados_planilha("financeiro"))
    except: df_financeiro = pd.DataFrame()
    
    try: df_espera = limpiar_dataframe(ler_dados_planilha("espera"))
    except: df_espera = pd.DataFrame()
    
    try: df_precos = limpiar_dataframe(ler_dados_planilha("precos"))
    except: df_precos = pd.DataFrame()
    
    try: df_evolucoes = limpiar_dataframe(ler_dados_planilha("evolucao"))
    except: df_evolucoes = pd.DataFrame()

    if not df_alunos.empty:
        if "Valor Mensal" in df_alunos.columns and "Valor" not in df_alunos.columns:
            df_alunos["Valor"] = df_alunos["Valor Mensal"]
        elif "Valor Mensal" in df_alunos.columns and "Valor" in df_alunos.columns:
            df_alunos["Valor"] = df_alunos["Valor"].fillna(df_alunos["Valor Mensal"])

    conexao_ok = True
except Exception as e:
    erro_msg = str(e)

if df_precos is None or df_precos.empty or "Plano" not in df_precos.columns:
    df_precos = pd.DataFrame([
        {"Plano": "1x semana", "Valor": 180.0},
        {"Plano": "2x semana", "Valor": 220.0},
        {"Plano": "3x semana", "Valor": 300.0}
    ])

dict_precos_padrao = {}
for _, r in df_precos.iterrows():
    dict_precos_padrao[str(r["Plano"])] = converter_para_float(r["Valor"])

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
                if h_alvo in h_atual:
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
    st.title("📅 Agenda de Treinos Diária")
    hoje_datetime = datetime.now()
    hoje_dia_mes = hoje_datetime.strftime("%d/%m")
    niver_hoje = []
    
    if not df_alunos.empty and "Nascimento" in df_alunos.columns and "Nome" in df_alunos.columns:
        for idx, row in df_alunos.iterrows():
            try:
                val_nasc = str(row["Nascimento"]).strip()
                if "/" in val_nasc:
                    partes = val_nasc.split("/")
                    if f"{int(partes[0]):02d}/{int(partes[1]):02d}" == hoje_dia_mes:
                        niver_hoje.append(row["Nome"])
            except:
                continue
                
    if niver_hoje:
        st.markdown(f"""<div style='background-color:#FFD700; padding:15px; border-radius:5px; color:black; font-weight:bold; margin-bottom:15px;'>
            🎉 Aniversariantes de Hoje ({hoje_dia_mes}): {', '.join(niver_hoje)}! 🎂
        </div>""", unsafe_allow_html=True)
        
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
                colunas_agenda = [c for c in ["Horario", "Nome", "Plano", "Dias", "Queixa"] if c in df_agenda.columns]
                st.dataframe(df_agenda[colunas_agenda], use_container_width=True, hide_index=True)
            else:
                st.info(f"Nenhum aluno agendado para esta {nome_dia_formatado}.")
        else:
            st.warning("Nenhum aluno ativo encontrado.")
    else:
        st.warning("Nenhum aluno cadastrado no banco de dados.")

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
            # CORREÇÃO CRÍTICA DO LOOP: Ajustado de formatb_brl para formatar_brl
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
            
            with st.form(f"form_edicao_{idx_real_planilha}"):
                c_ed1, c_ed2, c_ed3 = st.columns(3)
                with c_ed1:
                    options_planos = ["1x semana", "2x semana", "3x semana"]
                    plano_atual = dados_atuais.get("Plano", "1x semana")
                    idx_plano = options_planos.index(plano_atual) if plano_atual in options_planos else 0
                    novo_plano = st.selectbox("Novo Plano Contratado:", options_planos, index=idx_plano)
                    
                with c_ed2:
                    novos_dias = st.text_input("Novos Dias de Aula (Ex: Ter/Qui):", value=str(dados_atuais.get("Dias", "")))
                    novo_horario = st.text_input("Novo Horário (Ex: 08:30):", value=str(dados_atuais.get("Horario", "")))
                    
                with c_ed3:
                    st.markdown("**Ações Disponíveis:**")
                    btn_salvar_alt = st.form_submit_button("💾 Gravar Alterações")
                
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
                ed_conduta_extra = st.text_area("Diretrizes de Conduta Específicas:", value=conduta_atual)
                
                if btn_salvar_alt:
                    valor_calc = float(dict_precos_padrao.get(novo_plano, 180.0))
                    
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
                    df_alunos.at[idx_real_planilha, "Valor"] = valor_calc  
                    df_alunos.at[idx_real_planilha, "Dias"] = novos_dias.upper()
                    df_alunos.at[idx_real_planilha, "Horario"] = novo_horario
                    df_alunos.at[idx_real_planilha, "Queixa"] = " | ".join(novos_tratamentos) if novos_tratamentos else ""
                    df_alunos.at[idx_real_planilha, "Conduta"] = ed_conduta_extra.strip()
                    
                    df_alunos_salvar = df_alunos.fillna("").astype(str).replace("nan", "")
                    conn.update(worksheet="alunos", data=df_alunos_salvar)
                    st.cache_data.clear()
                    st.success("🎉 Alterações salvas no banco de dados!")
                    st.rerun()
            
            if st.button("❌ Mover ao Arquivo Morto", key="btn_inativar_manual"):
                df_alunos.at[idx_real_planilha, "Status"] = "Inativo"
                conn.update(worksheet="alunos", data=df_alunos.fillna("").astype(str))
                st.cache_data.clear()
                st.success("❌ Aluno arquivado com sucesso!")
                st.rerun()
    else:
        st.info("Nenhum aluno ativo cadastrado.")

# --- 3. TELA: CADASTRO ---
elif menu == "📝 Cadastro":
    st.title("📝 Cadastro e Anamnese Estruturada")
    
    st.subheader("1. Dados de Contrato (Selecione o Plano)")
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        plano_c = st.selectbox("Plano Contratado:", ["1x semana", "2x semana", "3x semana"])
    
    valor_sugerido_plano = float(dict_precos_padrao.get(plano_c, 180.0))
    with col_p2:
        valor_c = st.number_input("Valor Combinado Mensal (R$):", value=valor_sugerido_plano, step=10.0)

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

        st.subheader("2. Dados Pessoais do Aluno")
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
            genero_c = st.selectbox("Gênero:", ["Feminino", "Masculino", "Outro"])
            nasc_c = st.text_input("Data de Nascimento (DD/MM/AAAA):")
        with col2:
            venc_c = st.number_input("Dia de Vencimento Mensal:", min_value=1, max_value=31, value=10)
            inicio_c = st.text_input("Data de Início:", value=datetime.now().strftime("%d/%m/%Y"))
            
        st.subheader("3. Anamnese: Queixas Principais e Sintomas")
        st.write("Marque abaixo todas as condições clínicas aplicáveis:")
        
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
        conduta_extra = st.text_area("Diretrizes de Conduta Específicas:")

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
                    conn.update(worksheet="alunos", data=df_alunos.fillna("").astype(str))
                    st.cache_data.clear()
                    st.success(f"🎉 Aluno {nome_c} adicionado com sucesso!")
                    st.rerun()

# --- 4. TELA: EVOLUÇÃO ---
elif menu == "📈 Evolução":
    st.title("📈 Evolução Clínica dos Alunos")
    
    lista_nomes_alunos = []
    if not df_alunos.empty and "Nome" in df_alunos.columns:
        df_limpo_nomes = df_alunos.dropna(subset=["Nome"])
        lista_nomes_alunos = sorted([str(n).strip() for n in df_limpo_nomes["Nome"].unique() if str(n).strip() != ""])
    
    if lista_nomes_alunos:
        nome_aluno_evol = st.selectbox("Selecione o Aluno para Evoluir:", lista_nomes_alunos, key="sel_aluno_evol_direto")
        data_registro = st.date_input("Data do Registro:", datetime.now(), key="date_evol_direto")
        
        with st.form("form_nova_evolucao_clean", clear_on_submit=True):
            texto_evol = st.text_area("Registro de Evolução/Conduta do dia:")
            submit_evol = st.form_submit_button("Salvar Evolução")
            
            if submit_evol:
                if not texto_evol.strip():
                    st.error("❌ Digite um texto descritivo para salvar.")
                else:
                    nova_evol = {
                        "Data": data_registro.strftime("%d/%m/%Y"), 
                        "Nome do Aluno": nome_aluno_evol, 
                        "Evolução": texto_evol.strip()
                    }
                    df_evolucoes = pd.concat([df_evolucoes, pd.DataFrame([nova_evol])], ignore_index=True)
                    conn.update(worksheet="evolucao", data=df_evolucoes.fillna("").astype(str))
                    st.cache_data.clear()
                    st.success("🎉 Evolução registrada com sucesso!")
                    st.rerun()
    else:
        st.info("Nenhum aluno cadastrado no sistema para registrar evolução.")

    st.markdown("---")
    if lista_nomes_alunos:
        opcoes_filtro = ["Todos"] + lista_nomes_alunos
        aluno_filtro = st.selectbox("Ver histórico do aluno:", opcoes_filtro)
        
        if not df_evolucoes.empty:
            df_exibicao = df_evolucoes if aluno_filtro == "Todos" else df_evolucoes[df_evolucoes["Nome do Aluno"] == aluno_filtro]
            st.dataframe(df_exibicao.sort_index(ascending=False), use_container_width=True, hide_index=True)

# --- 5. TELA: ESPERA ---
elif menu == "⏳ Espera":
    st.title("⏳ Gerenciamento da Lista de Espera")
    
    if not df_espera.empty:
        df_espera.columns = df_espera.columns.str.strip()
        df_espera_vis = df_espera.copy()
        
        for col in ["Nome", "Telefone", "Dia Preferencia", "Hora Preferencia"]:
            if col not in df_espera_vis.columns:
                df_espera_vis[col] = ""
                
        st.dataframe(df_espera_vis[["Nome", "Telefone", "Dia Preferencia", "Hora Preferencia"]], use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum interessado aguardando vaga.")
        
    with st.form("form_espera", clear_on_submit=True):
        nome_esp = st.text_input("Nome do Interessado:")
        tel_esp = st.text_input("Telefone de Contato:")
        dia_esp = st.text_input("Dia da Semana de Preferência (Ex: TER/QUI):")
        hora_esp = st.text_input("Horário de Preferência (Ex: 18:30):")
        
        if st.form_submit_button("Adicionar à Lista") and nome_esp:
            nova_esp_row = {
                "Nome": str(nome_esp).strip(), 
                "Telefone": str(tel_esp).strip(), 
                "Dia Preferencia": str(dia_esp).upper().strip(), 
                "Hora Preferencia": str(hora_esp).strip()
            }
            df_espera = pd.concat([df_espera, pd.DataFrame([nova_esp_row])], ignore_index=True)
            conn.update(worksheet="espera", data=df_espera.fillna("").astype(str))
            st.cache_data.clear()
            st.success("✅ Interessado adicionado com sucesso!")
            st.rerun()

# --- 6. TELA: FINANCEIRO ---
elif menu == "💰 Financeiro":
    st.title("💰 Gestão e Lançamentos Financeiros")
    
    # 1. KPIs no topo do financeiro
    if not df_financeiro.empty:
        df_fin_calc = df_financeiro.copy()
        df_fin_calc["Valor_Float"] = df_fin_calc["Valor"].apply(converter_para_float)
        
        receita_total = df_fin_calc[df_fin_calc["Categoria"].astype(str).str.upper() == "RECEITA"]["Valor_Float"].sum()
        despesa_total = df_fin_calc[df_fin_calc["Categoria"].astype(str).str.upper() == "DESPESA"]["Valor_Float"].sum()
        saldo_geral = receita_total - despesa_total
        
        c_kpi1, c_kpi2, c_kpi3 = st.columns(3)
        with c_kpi1: st.metric("Total de Receitas", formatar_brl(receita_total))
        with c_kpi2: st.metric("Total de Despesas (Saídas)", formatar_brl(despesa_total))
        with c_kpi3: st.metric("Saldo de Caixa", formatar_brl(saldo_geral))
        
        st.markdown("---")
        st.subheader("📋 Histórico de Lançamentos")
        df_fin_visivel = df_financeiro.copy()
        if "Valor" in df_fin_visivel.columns:
            df_fin_visivel["Valor"] = df_fin_visivel["Valor"].apply(formatar_brl)
        st.dataframe(df_fin_visivel.sort_index(ascending=False), use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum lançamento financeiro registrado até o momento.")
        
    st.markdown("---")
    st.subheader("✍️ Registrar Novo Movimento de Caixa")
    
    lista_alunos_fin = ["-- Gasto Geral / Despesa --"]
    if not df_alunos.empty and "Nome" in df_alunos.columns:
        lista_alunos_fin += sorted(list(df_alunos["Nome"].dropna().unique()))
        
    with st.form("form_financeiro_novo", clear_on_submit=True):
        c_f1, c_f2, c_f3 = st.columns(3)
        with c_f1:
            aluno_fin = st.selectbox("Vincular a um Aluno (Se aplicável):", lista_alunos_fin)
            cat_fin = st.selectbox("Categoria do Fluxo:", ["Receita", "Despesa"])
        with c_f2:
            val_fin = st.number_input("Valor do Lançamento (R$):", min_value=0.0, step=10.0)
            forma_fin = st.selectbox("Forma de Pagamento:", ["Pix", "Dinheiro", "Cartão", "Transferência"])
        with c_f3:
            data_fin = st.date_input("Data da Operação:", datetime.now())
            status_fin = st.selectbox("Status:", ["Pago/Recebido", "Pendente"])
            
        if st.form_submit_button("Gravar Movimentação"):
            nome_entidade = "Gasto Geral" if aluno_fin == "-- Gasto Geral / Despesa --" else aluno_fin
            if val_fin <= 0:
                st.error("❌ O valor do lançamento deve ser maior do que zero!")
            else:
                novo_lancamento = {
                    "Aluno": nome_entidade,
                    "Valor": float(val_fin),
                    "Data": data_fin.strftime("%d/%m/%Y"),
                    "Forma": forma_fin,
                    "Categoria": cat_fin,
                    "Status": status_fin
                }
                df_financeiro = pd.concat([df_financeiro, pd.DataFrame([novo_lancamento])], ignore_index=True)
                conn.update(worksheet="financeiro", data=df_financeiro.fillna("").astype(str))
                st.cache_data.clear()
                st.success("🎉 Movimentação financeira salva com sucesso!")
                st.rerun()

# --- 7. TELA: PERFIL ---
elif menu == "👤 Perfil":
    st.title("👤 Ficha cadastral Completa e Perfil Clínico")
    
    if not df_alunos.empty and "Nome" in df_alunos.columns:
        lista_perfis = sorted(list(df_alunos[df_alunos["Status"].astype(str).str.upper() == "ATIVO"]["Nome"].dropna().unique()))
        
        if lista_perfis:
            aluno_perfil = st.selectbox("Selecione o aluno para inspecionar:", lista_perfis)
            row_p = df_alunos[df_alunos["Nome"] == aluno_perfil].iloc[0]
            
            c_p1, c_p2 = st.columns(2)
            with c_p1:
                st.markdown(f"**📱 WhatsApp:** {row_p.get('Telefone', 'Não Informado')}")
                st.markdown(f"**🏠 Bairro:** {row_p.get('Bairro', 'Não Informado')}")
                st.markdown(f"**📍 Endereço:** {row_p.get('Endereco', 'Não Informado')}")
                st.markdown(f"**💳 CPF:** {row_p.get('CPF', 'Não Informado')}")
            with c_p2:
                st.markdown(f"**📋 Plano:** {row_p.get('Plano', 'Não Informado')}")
                st.markdown(f"**💰 Valor:** {formatar_brl(row_p.get('Valor', 0))}")
                st.markdown(f"**📅 Dias Contratados:** {row_p.get('Dias', 'Não Informado')}")
                st.markdown(f"**🕒 Horário das Aulas:** {row_p.get('Horario', 'Não Informado')}")
                
            st.markdown("---")
            st.subheader("🩺 Prontuário Clínico & Conduta Operacional")
            st.info(f"**Queixas Mapeadas:** {row_p.get('Queixa', 'Nenhuma queixa registrada.')}")
            st.warning(f"**Conduta e Restrições:** {row_p.get('Conduta', 'Nenhuma diretriz de conduta configurada.')}")
        else:
            st.info("Nenhum aluno ativo encontrado para exibir perfil.")
    else:
        st.warning("Banco de dados de alunos indisponível.")

# --- 8. TELA: PREÇOS ---
elif menu == "⚙️ Preços":
    st.title("⚙️ Gerenciamento de Preços de Planos Padrão")
    
    st.subheader("Valores Vigentes na Tabela de Preços")
    df_precos_vis = df_precos.copy()
    if "Valor" in df_precos_vis.columns:
        df_precos_vis["Valor"] = df_precos_vis["Valor"].apply(formatar_brl)
    st.dataframe(df_precos_vis, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    st.subheader("🔄 Alterar Valor de um Plano")
    
    with st.form("form_ajuste_precos"):
        plano_alterar = st.selectbox("Selecione o plano:", list(dict_precos_padrao.keys()))
        novo_valor_plano = st.number_input("Definir novo valor mensal (R$):", min_value=0.0, value=float(dict_precos_padrao.get(plano_alterar, 180.0)), step=10.0)
        
        if st.form_submit_button("Atualizar Preço Base"):
            idx_plano = df_precos[df_precos["Plano"] == plano_alterar].index
            if not idx_plano.empty:
                df_precos.at[idx_plano[0], "Valor"] = float(novo_valor_plano)
            else:
                df_precos = pd.concat([df_precos, pd.DataFrame([{"Plano": plano_alterar, "Valor": float(novo_valor_plano)}])], ignore_index=True)
                
            conn.update(worksheet="precos", data=df_precos.fillna("").astype(str))
            st.cache_data.clear()
            st.success("🎉 Preço base do plano atualizado com sucesso!")
            st.rerun()

# --- 9. TELA: ARQUIVO MORTO ---
elif menu == "📁 Arquivo Morto":
    st.title("📁 Arquivo Morto (Alunos Inativos)")
    
    if not df_alunos.empty and "Status" in df_alunos.columns:
        df_inativos = df_alunos[df_alunos["Status"].astype(str).str.upper() == "INATIVO"]
    else:
        df_inativos = pd.DataFrame()
        
    if not df_inativos.empty:
        df_inativos_vis = df_inativos.copy()
        if "Valor" in df_inativos_vis.columns:
            df_inativos_vis["Valor"] = df_inativos_vis["Valor"].apply(formatar_brl)
        st.dataframe(df_inativos_vis, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.subheader("🔄 Reativar Matrícula de Aluno")
        opcoes_reativar = ["-- Selecione um Aluno para Reativar --"] + [f"{row['Nome']} (Reg: {idx})" for idx, row in df_inativos.iterrows()]
        aluno_reativar_str = st.selectbox("Selecione:", opcoes_reativar)
        
        if aluno_reativar_str != "-- Selecione um Aluno para Reativar --":
            idx_reativar = int(aluno_reativar_str.split("(Reg: ")[1].replace(")", ""))
            
            if st.button("✅ Restaurar para Base Ativa"):
                df_alunos.at[idx_reativar, "Status"] = "Ativo"
                conn.update(worksheet="alunos", data=df_alunos.fillna("").astype(str))
                st.cache_data.clear()
                st.success("🎉 Aluno reativado com sucesso!")
                st.rerun()
    else:
        st.info("Nenhum aluno inativado no momento.")

# --- 10. TELA: IMPRIMIR PRONTUÁRIO ---
elif menu == "🖨️ Imprimir Prontuário":
    st.title("🖨️ Emissão e Impressão de Prontuário Clínico")
    
    if not df_alunos.empty and "Nome" in df_alunos.columns:
        lista_print = sorted(list(df_alunos["Nome"].dropna().unique()))
        aluno_print = st.selectbox("Selecione o aluno para gerar o documento:", lista_print, key="sb_print_pront")
        
        row_pr = df_alunos[df_alunos["Nome"] == aluno_print].iloc[0]
        idade_calc = calcular_idade(row_pr.get("Nascimento", ""))
        idade_str = f"{idade_calc} anos" if idade_calc is not None else "Não Informada"
        
        st.markdown("""
            <div class="no-print" style="margin-bottom: 20px;">
                <p>💡 <b>Dica de Impressão:</b> Clique no botão abaixo para abrir a janela de impressão do seu navegador. Nas configurações, marque a opção <i>'Imprimir cores de fundo'</i> para reter a identidade visual.</p>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("🖨️ Acionar Comando de Impressão"):
            st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
            
        # Layout estruturado do Prontuário Clínico para Impressão HTML
        st.markdown(f"""
            <div class="prontuario-card">
                <div class="prontuario-header">
                    <h2 style="margin:0; font-size: 26px;">HIGHLINE MANAGEMENT</h2>
                    <p style="margin:5px 0 0 0; font-size: 14px; letter-spacing: 1px; text-transform: uppercase;">Ficha Cadastral e Prontuário de Pilates</p>
                </div>
                
                <div class="prontuario-secao">📌 DADOS PESSOAIS E CONTRATUAIS</div>
                <table class="tabela-prontuario">
                    <tr>
                        <td style="width: 15%; font-weight: bold;">Nome:</td>
                        <td style="width: 50%;">{row_pr.get('Nome', '')}</td>
                        <td style="width: 15%; font-weight: bold;">Gênero:</td>
                        <td style="width: 20%;">{row_pr.get('Genero', 'Não Informado')}</td>
                    </tr>
                    <tr>
                        <td style="font-weight: bold;">Nascimento:</td>
                        <td>{row_pr.get('Nascimento', 'Não Informado')} ({idade_str})</td>
                        <td style="font-weight: bold;">CPF:</td>
                        <td>{row_pr.get('CPF', 'Não Informado')}</td>
                    </tr>
                    <tr>
                        <td style="font-weight: bold;">WhatsApp:</td>
                        <td>{row_pr.get('Telefone', 'Não Informado')}</td>
                        <td style="font-weight: bold;">Início:</td>
                        <td>{row_pr.get('Inicio_Aulas', 'Não Informado')}</td>
                    </tr>
                    <tr>
                        <td style="font-weight: bold;">Endereço:</td>
                        <td colspan="3">{row_pr.get('Endereco', 'Não Informado')}</td>
                    </tr>
                </table>
                
                <div class="prontuario-secao">📌 ROTINA DE TREINOS</div>
                <table class="tabela-prontuario">
                    <tr>
                        <td style="width: 15%; font-weight: bold;">Plano:</td>
                        <td style="width: 35%;">{row_pr.get('Plano', '')}</td>
                        <td style="width: 15%; font-weight: bold;">Horário:</td>
                        <td style="width: 35%;">{row_pr.get('Horario', '')}</td>
                    </tr>
                    <tr>
                        <td style="font-weight: bold;">Dias Fixos:</td>
                        <td colspan="3">{row_pr.get('Dias', '')}</td>
                    </tr>
                </table>
                
                <div class="prontuario-secao">🩺 DIAGNÓSTICO CLÍNICO E ANAMNESE</div>
                <div style="background-color: #f9f9f9; padding: 15px; border: 1px solid #ddd; border-radius: 4px; margin-top: 10px; color: black !important;">
                    {row_pr.get('Queixa', 'Nenhuma condição mapeada.')}
                </div>
                
                <div class="prontuario-secao">📋 DIRETRIZES DE CONDUTA OPERACIONAL</div>
                <div style="background-color: #f9f9f9; padding: 15px; border: 1px solid #ddd; border-radius: 4px; margin-top: 10px; white-space: pre-wrap; color: black !important;">
                    {row_pr.get('Conduta', 'Sem restrições ou diretrizes específicas cadastradas.')}
                </div>
                
                <div style="margin-top: 80px; text-align: center;" class="no-print">
                    <p style="border-top: 1px solid #000; width: 300px; margin: 0 auto; padding-top: 5px; color: black !important;">Assinatura do Profissional Responsável</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("Banco de dados de alunos vazio.")
