import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import os
import streamlit.components.v1 as components

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
    </style>
""", unsafe_allow_html=True)

# ==========================================
# FUNÇÕES AUXILIARES DE LIMPEZA E FORMATAÇÃO
# ==========================================

# DICIONÁRIO DE PREÇOS PADRÃO (Adicionado para evitar NameError)
dict_precos_padrao = {
    "1x semana": 180.0,
    "2x semana": 250.0,
    "3x semana": 320.0
}

# FUNÇÃO DE VERIFICAÇÃO DE LOTAÇÃO (Adicionado para evitar looping e NameError)
def verificar_lotacao(df, dias_c, horarios_selecionados, limite_maximo=3):
    conflitos = []
    if df is None or df.empty or "Dias" not in df.columns or "Horario" not in df.columns:
        return conflitos, {}
    
    # Filtra apenas alunos ativos
    df_ativos = df[df["Status"].astype(str).str.upper() == "ATIVO"] if "Status" in df.columns else df
    
    dias_solicitados = [d.strip().upper() for d in dias_c.split("/") if d.strip()]
    
    for dia in dias_solicitados:
        for hora in horarios_selecionados:
            # Conta quantos alunos ativos batem no mesmo dia e horário
            qtd = 0
            for idx, row in df_ativos.iterrows():
                row_dias = str(row["Dias"]).upper()
                row_horas = str(row["Horario"])
                if dia in row_dias and hora in row_horas:
                    qtd += 1
            if qtd >= limite_maximo:
                conflitos.append((dia, hora, qtd))
                
    return conflitos, {}

def limpiar_dataframe(df):
    if df is None:
        return pd.DataFrame()
    if isinstance(df, pd.DataFrame):
        if df.empty:
            return pd.DataFrame()
        return df.dropna(how="all")
    return pd.DataFrame()

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
# 2. CONEXÃO COM GOOGLE SHEETS
# ==========================================
conexao_ok = False

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    @st.cache_data(ttl=15)
    def ler_dados_planilha(aba):
        return conn.read(worksheet=aba)
    
    df_alunos = limpiar_dataframe(ler_dados_planilha("alunos"))
    df_financeiro = limpiar_dataframe(ler_dados_planilha("financeiro"))
    df_espera = limpiar_dataframe(ler_dados_planilha("espera"))
    df_precos = limpiar_dataframe(ler_dados_planilha("precos"))
    df_evolucoes = limpiar_dataframe(ler_dados_planilha("evolucao"))

    conexao_ok = True
except Exception as e:
    st.error(f"Erro ao conectar com Google Sheets: {e}")
    df_alunos = pd.DataFrame()
    df_financeiro = pd.DataFrame()
    df_espera = pd.DataFrame()
    df_precos = pd.DataFrame()
    df_evolucoes = pd.DataFrame()

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

LISTA_CONDUTAS_PADRAO = [
    "Fortalecimento de Core (Powerhouse)",
    "Mobilização e Articulação de Coluna",
    "Alongamento de Cadeia Posterior",
    "Estabilização Escapular / Pélvica",
    "Evitar Flexões Intensas de Tronco",
    "Evitar Extensões/Hiperlordose",
    "Exercícios de Baixo Impacto Articular",
    "Treino de Equilíbrio e Propriocepção",
    "Controle e Reeducação Respiratória"
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
                
                st.markdown("#### #### 🩺 Atualizar Anamnese: Queixas Principais e Sintomas")
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
                
                st.markdown("#### 📋 Atualizar Diretrizes de Conduta Operacional")
                conduta_atual_str = str(dados_atuais.get("Conduta", ""))
                
                c_cond1, c_cond2, c_cond3 = st.columns(3)
                with c_cond1:
                    ed_c_core = st.checkbox("Fortalecimento de Core (Powerhouse)", value=("Fortalecimento de Core (Powerhouse)" in conduta_atual_str))
                    ed_c_escap = st.checkbox("Estabilização Escapular / Pélvica", value=("Estabilização Escapular / Pélvica" in conduta_atual_str))
                    ed_c_baixo = st.checkbox("Exercícios de Baixo Impacto Articular", value=("Exercícios de Baixo Impacto Articular" in conduta_atual_str))
                with c_cond2:
                    ed_c_coluna = st.checkbox("Mobilização e Articulação de Coluna", value=("Mobilização e Articulação de Coluna" in conduta_atual_str))
                    ed_c_flex = st.checkbox("Evitar Flexões Intensas de Tronco", value=("Evitar Flexões Intensas de Tronco" in conduta_atual_str))
                    ed_c_equil = st.checkbox("Treino de Equilíbrio e Propriocepção", value=("Treino de Equilíbrio e Propriocepção" in conduta_atual_str))
                with c_cond3:
                    ed_c_post = st.checkbox("Alongamento de Cadeia Posterior", value=("Alongamento de Cadeia Posterior" in conduta_atual_str))
                    ed_c_ext = st.checkbox("Evitar Extensões/Hiperlordose", value=("Evitar Extensões/Hiperlordose" in conduta_atual_str))
                    ed_c_resp = st.checkbox("Controle e Reeducação Respiratória", value=("Controle e Reeducação Respiratória" in conduta_atual_str))
                
                condutas_limpas = []
                for c in conduta_atual_str.split(" | "):
                    c_strip = c.strip()
                    if c_strip and c_strip not in LISTA_CONDUTAS_PADRAO and c_strip.lower() != "nan":
                        condutas_limpas.append(c_strip)
                condutas_adicionais_existentes = " | ".join(condutas_limpas)
                
                ed_conduta_extra = st.text_input("Outras Diretrizes Clínicas / Restrições Adicionais:", value=condutas_adicionais_existentes)
                
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
                        if marcado: novos_tratamentos.append(nome_queixa)
                    if ed_queixa_extra.strip(): novos_tratamentos.append(ed_queixa_extra.strip())
                    
                    novas_condutas = []
                    mapeamento_conduta_check = [
                        ("Fortalecimento de Core (Powerhouse)", ed_c_core),
                        ("Mobilização e Articulação de Coluna", ed_c_coluna),
                        ("Alongamento de Cadeia Posterior", ed_c_post),
                        ("Estabilização Escapular / Pélvica", ed_c_escap),
                        ("Evitar Flexões Intensas de Tronco", ed_c_flex),
                        ("Evitar Extensões/Hiperlordose", ed_c_ext),
                        ("Exercícios de Baixo Impacto Articular", ed_c_baixo),
                        ("Treino de Equilíbrio e Propriocepção", ed_c_equil),
                        ("Controle e Reeducação Respiratória", ed_c_resp)
                    ]
                    for nome_conduta, marcado in mapeamento_conduta_check:
                        if marcado: novas_condutas.append(nome_conduta)
                    if ed_conduta_extra.strip(): novas_condutas.append(ed_conduta_extra.strip())
                    
                    df_alunos.at[idx_real_planilha, "Plano"] = novo_plano
                    df_alunos.at[idx_real_planilha, "Valor"] = valor_calc  
                    df_alunos.at[idx_real_planilha, "Dias"] = novos_dias.upper()
                    df_alunos.at[idx_real_planilha, "Horario"] = novo_horario
                    df_alunos.at[idx_real_planilha, "Queixa"] = " | ".join(novos_tratamentos) if novos_tratamentos else ""
                    df_alunos.at[idx_real_planilha, "Conduta"] = " | ".join(novas_condutas) if novas_condutas else ""
                    
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
        
        c_q1, c_q2, c_q3 = st.columns(3)
        with c_q1:
            t_lombar = st.checkbox("Dor Lombar (Lombalgia)", key="k_lombar")
            t_cervical = st.checkbox("Dor Cervical (Cervicalgia)", key="k_cervical")
            t_gestante = st.checkbox("Pilates para Gestantes", key="k_gestante")
        with c_q2:
            t_hernia = st.checkbox("Hérnia de Disco / Protrusão", key="k_hernia")
            t_joelhos = st.checkbox("Dor / Lesão nos Joelhos", key="k_joelhos")
            t_idoso = st.checkbox("Pilates para Terceira Idade (Idosos)", key="k_idoso")
        with c_q3:
            t_ombros = st.checkbox("Dor / Lesão nos Ombros", key="k_ombros")
            t_postural = st.checkbox("Melhoria Postural Operacional", key="k_postural")
            t_condic = st.checkbox("Condicionamento Físico Geral", key="k_condic")
            
        queixa_extra = st.text_input("Outras Queixas Adicionais / Observações Clínicas:")
        
        st.subheader("4. Diretrizes de Conduta Operacional (Tratamento)")
        st.write("Marque as condutas e restrições padrão para o plano de aula do aluno:")
        
        c_cn1, c_cn2, c_cn3 = st.columns(3)
        with c_cn1:
            c_core = st.checkbox("Fortalecimento de Core (Powerhouse)", key="k_c_core")
            c_escap = st.checkbox("Estabilização Escapular / Pélvica", key="k_c_escap")
            c_baixo = st.checkbox("Exercícios de Baixo Impacto Articular", key="k_c_baixo")
        with c_cn2:
            c_coluna = st.checkbox("Mobilização e Articulação de Coluna", key="k_c_coluna")
            c_flex = st.checkbox("Evitar Flexões Intensas de Tronco", key="k_c_flex")
            c_equil = st.checkbox("Treino de Equilíbrio e Propriocepção", key="k_c_equil")
        with c_cn3:
            c_post = st.checkbox("Alongamento de Cadeia Posterior", key="k_c_post")
            c_ext = st.checkbox("Evitar Extensões/Hiperlordose", key="k_c_ext")
            c_resp = st.checkbox("Controle e Reeducação Respiratória", key="k_c_resp")
            
        conduta_extra = st.text_input("Outras Condutas Específicas / Observações Clínicas Extras:")

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
                        ("Dor Lombar (Lombalgia)", t_lombar), ("Hérnia de Disco / Protrusão", t_hernia),
                        ("Dor / Lesão nos Ombros", t_ombros), ("Dor Cervical (Cervicalgia)", t_cervical),
                        ("Dor / Lesão nos Joelhos", t_joelhos), ("Melhoria Postural Operacional", t_postural),
                        ("Pilates para Gestantes", t_gestante), ("Pilates para Terceira Idade (Idosos)", t_idoso),
                        ("Condicionamento Físico Geral", t_condic)
                    ]
                    for nome_queixa, marcado in mapeamento_cadastro:
                        if marcado: tratamentos.append(nome_queixa)
                    if queixa_extra.strip(): tratamentos.append(queixa_extra.strip())
                    
                    condutas_selecionadas = []
                    mapeamento_condutas_cad = [
                        ("Fortalecimento de Core (Powerhouse)", c_core), ("Mobilização e Articulação de Coluna", c_coluna),
                        ("Alongamento de Cadeia Posterior", c_post), ("Estabilização Escapular / Pélvica", c_escap),
                        ("Evitar Flexões Intensas de Tronco", c_flex), ("Evitar Extensões/Hiperlordose", c_ext),
                        ("Exercícios de Baixo Impacto Articular", c_baixo), ("Treino de Equilíbrio e Propriocepção", c_equil),
                        ("Controle e Reeducação Respiratória", c_resp)
                    ]
                    for nome_conduta, marcado in mapeamento_condutas_cad:
                        if marcado: condutas_selecionadas.append(nome_conduta)
                    if conduta_extra.strip(): condutas_selecionadas.append(conduta_extra.strip())
                    
                    nova_linha = {
                        "Nome": nome_c, "Telefone": tel_c, "Bairro": bairro_c, "Plano": plano_c, 
                        "Valor": float(valor_c), "Vencimento": int(venc_c), "Dias": dias_c, "Horario": horario_c, 
                        "Status": "Ativo", "Queixa": " | ".join(tratamentos), "Conduta": " | ".join(condutas_selecionadas), 
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
                "Nome": str(nome_esp),
                "Telefone": str(tel_esp),
                "Dia Preferencia": str(dia_esp),
                "Hora Preferencia": str(hora_esp)
            }
            df_espera = pd.concat([df_espera, pd.DataFrame([nova_esp_row])], ignore_index=True)
            conn.update(worksheet="espera", data=df_espera.fillna("").astype(str))
            st.cache_data.clear()
            st.success("🎉 Adicionado à lista de espera!")
            st.rerun()
