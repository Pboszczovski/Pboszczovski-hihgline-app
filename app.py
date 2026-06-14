import os
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from streamlit_gsheets import GSheetsConnection

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
        df = df.loc[:, ~df.columns.astype(str).str.contains("^Unnamed")]
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
        data_nasc = pd.to_datetime(str(data_nasc_str).strip(), dayfirst=True, errors="coerce")
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

df_alunos = pd.DataFrame(
    columns=[
        "Nome", "Telefone", "Bairro", "Plano", "Valor", "Vencimento", 
        "Dias", "Horario", "Status", "Queixa", "Conduta", "Genero", 
        "Nascimento", "Inicio_Aulas", "CPF", "Endereco"
    ]
)
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
    st.markdown("</div>", unsafe_allow_html=True)

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
    if dia_semana_num == 0: dias_validos_busca, nome_dia_formatado = ["SEG", "2A", "SEGUNDA"], "Segunda-feira"
    elif dia_semana_num == 1: dias_validos_busca, nome_dia_formatado = ["TER", "3A", "TERÇA", "TERCA"], "Terça-feira"
    elif dia_semana_num == 2: dias_validos_busca, nome_dia_formatado = ["QUA", "4A", "QUARTA"], "Quarta-feira"
    elif dia_semana_num == 3: dias_validos_busca, nome_dia_formatado = ["QUI", "5A", "QUINTA"], "Quinta-feira"
    elif dia_semana_num == 4: dias_validos_busca, nome_dia_formatado = ["SEX", "6A", "SEXTA"], "Sexta-feira"
    elif dia_semana_num == 5: dias_validos_busca, nome_dia_formatado = ["SAB", "SÁBADO", "SABADO"], "Sábado"
    else: dias_validos_busca, nome_dia_formatado = ["DOM", "DOMINGO"], "Domingo"

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
                    st.success("🎉 Alterações salvas no banco de dados!")
                    st.cache_data.clear()
                    st.rerun()

            if st.button("❌ Mover ao Arquivo Morto", key="btn_inativar_manual"):
                df_alunos.at[idx_real_planilha, "Status"] = "Inativo"
                conn.update(worksheet="alunos", data=df_alunos.fillna("").astype(str))
                st.success("❌ Aluno arquivado!")
                st.cache_data.clear()
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
                    st.success(f"🎉 Aluno {nome_c} adicionado com sucesso!")
                    st.cache_data.clear()
                    st.rerun()

# --- 4. TELA: EVOLUÇÃO ---
elif menu == "📈 Evolução":
    st.title("📈 Evolução Clinical dos Alunos")

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
                    st.success("🎉 Evolução registrada com sucesso!")
                    st.cache_data.clear()
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
            st.success("✅ Interessado adicionado com sucesso!")
            st.cache_data.clear()
            st.rerun()

# --- 6. TELA: FINANCEIRO ---
elif menu == "💰 Financeiro":
    st.title("💰 Painel Financeiro")

    if not df_financeiro.empty:
        df_financeiro["Valor_Float"] = df_financeiro["Valor"].apply(converter_para_float)
        total_recebido = df_financeiro[df_financeiro["Status"].astype(str).str.upper() == "PAGO"]["Valor_Float"].sum()
        total_pendente = df_financeiro[df_financeiro["Status"].astype(str).str.upper() == "PENDENTE"]["Valor_Float"].sum()

        col_f1, col_f2 = st.columns(2)
        with col_f1:
            st.metric("Total Recebido (PAGO)", formatar_brl(total_recebido))
        with col_f2:
            st.metric("Total em Aberto (PENDENTE)", formatar_brl(total_pendente))

        st.markdown("### 📊 Gráfico de Receitas por Categoria")
        if "Categoria" in df_financeiro.columns:
            df_agrupado = df_financeiro.groupby("Categoria", as_index=False)["Valor_Float"].sum()
            fig = px.bar(df_agrupado, x="Categoria", y="Valor_Float", text_auto=True, color="Categoria", title="Arrecadação por Categoria")
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("### 📋 Histórico de Lançamentos")
        df_financeiro_vis = df_financeiro.copy()
        if "Valor" in df_financeiro_vis.columns:
            df_financeiro_vis["Valor"] = df_financeiro_vis["Valor_Float"].apply(formatar_brl)
        colunas_exibir = [c for c in ["Aluno", "Valor", "Data", "Forma", "Categoria", "Status"] if c in df_financeiro_vis.columns]
        st.dataframe(df_financeiro_vis[colunas_exibir], use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum registro financeiro encontrado nas planilhas.")

    st.markdown("---")
    st.markdown("### ➕ Adicionar Novo Lançamento Manual")
    with st.form("form_novo_lancamento", clear_on_submit=True):
        f_aluno = st.text_input("Nome do Aluno / Descrição:")
        f_valor = st.number_input("Valor (R$):", min_value=0.0, step=10.0)
        f_data = st.text_input("Data (DD/MM/AAAA):", value=datetime.now().strftime("%d/%m/%Y"))
        f_forma = st.selectbox("Forma de Pagamento:", ["Pix", "Dinheiro", "Cartão de Crédito", "Cartão de Débito", "Transferência"])
        f_cat = st.selectbox("Categoria:", ["Mensalidade", "Avaliação", "Aula Avulsa", "Outros"])
        f_status = st.selectbox("Status Comercial:", ["Pago", "Pendente"])

        if st.form_submit_button("Registrar Transação") and f_aluno:
            nova_transacao = {
                "Aluno": f_aluno, "Valor": float(f_valor), "Data": f_data,
                "Forma": f_forma, "Categoria": f_cat, "Status": f_status
            }
            df_financeiro = pd.concat([df_financeiro, pd.DataFrame([nova_transacao])], ignore_index=True)
            conn.update(worksheet="financeiro", data=df_financeiro.fillna("").astype(str))
            st.success("💰 Lançamento financeiro adicionado!")
            st.cache_data.clear()
            st.rerun()

# --- 7. TELA: PERFIL ---
elif menu == "👤 Perfil":
    st.title("👤 Perfil Completo do Aluno")
    if not df_alunos.empty and "Nome" in df_alunos.columns:
        nomes_disponiveis = sorted(df_alunos["Nome"].dropna().unique())
        aluno_selecionado = st.selectbox("Escolha um Aluno para visualizar o perfil:", nomes_disponiveis)

        dados_aluno = df_alunos[df_alunos["Nome"] == aluno_selecionado].iloc[0]

        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.markdown(f"### 📋 Dados Pessoais")
            st.write(f"**Nome:** {dados_aluno.get('Nome', 'Não preenchido')}")
            st.write(f"**Gênero:** {dados_aluno.get('Genero', 'Não preenchido')}")
            st.write(f"**Data de Nascimento:** {dados_aluno.get('Nascimento', 'Não preenchido')}")
            st.write(f"**CPF:** {dados_aluno.get('CPF', 'Não preenchido')}")
            st.write(f"**WhatsApp:** {dados_aluno.get('Telefone', 'Não preenchido')}")
            st.write(f"**Bairro:** {dados_aluno.get('Bairro', 'Não preenchido')}")
            st.write(f"**Endereço Completo:** {dados_aluno.get('Endereco', 'Não preenchido')}")

        with col_p2:
            st.markdown(f"### 🏋️‍♂️ Contrato e Horários")
            st.write(f"**Plano Atualmente Contratado:** {dados_aluno.get('Plano', 'Não preenchido')}")
            st.write(f"**Valor Mensal:** {formatar_brl(dados_aluno.get('Valor', 0))}")
            st.write(f"**Dia do Vencimento:** {dados_aluno.get('Vencimento', 'Não preenchido')}")
            st.write(f"**Dias da Semana de Aula:** {dados_aluno.get('Dias', 'Não preenchido')}")
            st.write(f"**Horário:** {dados_aluno.get('Horario', 'Não preenchido')}")
            st.write(f"**Data de Matrícula/Início:** {dados_aluno.get('Inicio_Aulas', 'Não preenchido')}")
            st.write(f"**Status Cadastral:** {dados_aluno.get('Status', 'Não preenchido')}")

        st.markdown("---")
        st.markdown("### 🩺 Anamnese Clínica Fixada")
        st.info(f"**Queixas Principais:** {dados_aluno.get('Queixa', 'Nenhuma queixa de anamnese registrada.')}")
        st.warning(f"**Condutas e Restrições Clínicas:** {dados_aluno.get('Conduta', 'Nenhuma conduta predefinida.')}")
    else:
        st.info("Nenhum aluno cadastrado para exibir o perfil.")

# --- 8. TELA: PREÇOS ---
elif menu == "⚙️ Preços":
    st.title("⚙️ Gerenciar Tabela de Preços")
    st.markdown("Valores de mensalidades padrão cadastrados para cada modalidade de plano:")

    if not df_precos.empty:
        df_precos_vis = df_precos.copy()
        if "Valor" in df_precos_vis.columns:
            df_precos_vis["Valor"] = df_precos_vis["Valor"].apply(formatar_brl)
        st.dataframe(df_precos_vis, use_container_width=True, hide_index=True)
    else:
        st.write("Usando valores padrão em cache do sistema corporativo.")

    st.markdown("---")
    st.markdown("### ✏️ Atualizar Valor de um Plano")
    with st.form("form_precos_editar"):
        plano_alvo = st.selectbox("Selecione o plano a alterar:", ["1x semana", "2x semana", "3x semana"])
        novo_v_plano = st.number_input("Definir novo valor mensal do plano (R$):", min_value=0.0, step=10.0)

        if st.form_submit_button("Atualizar na Tabela Master"):
            if plano_alvo in df_precos["Plano"].values:
                idx_p = df_precos[df_precos["Plano"] == plano_alvo].index[0]
                df_precos.at[idx_p, "Valor"] = float(novo_v_plano)
            else:
                df_precos = pd.concat([df_precos, pd.DataFrame([{"Plano": plano_alvo, "Valor": float(novo_v_plano)}])], ignore_index=True)
            
            conn.update(worksheet="precos", data=df_precos.fillna("").astype(str))
            st.success(f"🎉 Preço do plano '{plano_alvo}' atualizado com sucesso!")
            st.cache_data.clear()
            st.rerun()

# --- 9. TELA: ARQUIVO MORTO ---
elif menu == "📁 Arquivo Morto":
    st.title("📁 Alunos Inativos / Arquivo Morto")
    st.markdown("Consulta de alunos históricos que foram desativados do ecossistema:")

    if not df_alunos.empty and "Status" in df_alunos.columns:
        df_inativos = df_alunos[df_alunos["Status"].astype(str).str.upper() == "INATIVO"]
        if not df_inativos.empty:
            df_inativos_vis = df_inativos.copy()
            if "Valor" in df_inativos_vis.columns:
                df_inativos_vis["Valor"] = df_inativos_vis["Valor"].apply(formatar_brl)
            st.dataframe(df_inativos_vis, use_container_width=True, hide_index=True)

            st.markdown("---")
            opcoes_reativar = ["-- Selecione para Reativar --"] + list(df_inativos["Nome"].unique())
            aluno_reativar = st.selectbox("Deseja reativar a matrícula de algum aluno?", opcoes_reativar)
            
            if aluno_reativar != "-- Selecione para Reativar --":
                if st.button("🔄 Confirmar Reativação de Aluno Ativo"):
                    idx_reat = df_alunos[df_alunos["Nome"] == aluno_reativar].index[0]
                    df_alunos.at[idx_reat, "Status"] = "Ativo"
                    conn.update(worksheet="alunos", data=df_alunos.fillna("").astype(str))
                    st.success(f"🎉 Aluno {aluno_reativar} reativado com sucesso!")
                    st.cache_data.clear()
                    st.rerun()
        else:
            st.info("Nenhum aluno inativo no Arquivo Morto.")
    else:
        st.info("Nenhum dado de alunos localizado para pesquisa.")

# --- 10. TELA: IMPRIMIR PRONTUÁRIO ---
elif menu == "🖨️ Imprimir Prontuário":
    st.title("🖨️ Visualização para Impressão de Prontuário")
    st.markdown("Selecione o aluno abaixo para gerar o cartão clínico limpo para impressão física ou PDF.")

    if not df_alunos.empty and "Nome" in df_alunos.columns:
        nomes_pront = sorted(df_alunos["Nome"].dropna().unique())
        aluno_pront_sel = st.selectbox("Selecionar Aluno para o Prontuário:", nomes_pront)

        dados_p = df_alunos[df_alunos["Nome"] == aluno_pront_sel].iloc[0]

        st.markdown(f"""
        <div class="prontuario-card">
            <div class="prontuario-header">
                <h2>HIGHLINE MANAGEMENT - PRONTUÁRIO CLÍNICO</h2>
                <p>Ficha de Acompanhamento de Pilates & Condicionamento</p>
            </div>
            <table class="tabela-prontuario">
                <tr>
                    <td><strong>Nome do Aluno:</strong> {dados_p.get('Nome', '')}</td>
                    <td><strong>WhatsApp:</strong> {dados_p.get('Telefone', '')}</td>
                </tr>
                <tr>
                    <td><strong>Plano Contratado:</strong> {dados_p.get('Plano', '')}</td>
                    <td><strong>Horário de Aula:</strong> {dados_p.get('Horario', '')} ({dados_p.get('Dias', '')})</td>
                </tr>
                <tr>
                    <td><strong>Data de Nascimento:</strong> {dados_p.get('Nascimento', '')}</td>
                    <td><strong>Data de Início:</strong> {dados_p.get('Inicio_Aulas', '')}</td>
                </tr>
            </table>
            
            <div class="prontuario-secao">ANAMNESE E QUEIXAS CLÍNICAS PRINCIPAIS</div>
            <p style="color: black !important; padding: 5px;">{dados_p.get('Queixa', 'Nenhuma queixa registrada.')}</p>
            
            <div class="prontuario-secao">DIRETRIZES DE CONDUTA E RESTRICÕES DE TREINAMENTO</div>
            <p style="color: black !important; padding: 5px;">{dados_p.get('Conduta', 'Nenhuma conduta específica registrada.')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.button("Clique em Ctrl+P para abrir o painel de impressão do seu navegador", help="Utilize as configurações nativas para salvar em PDF ou imprimir.")
    else:
        st.info("Nenhum aluno localizado na base ativa para emitir relatórios.")
