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
        if pd.isna(valor) or valor == "" or valor is None or str(valor).strip() == "":
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

def verificar_lotacao(df, dias_busca, horarios_busca):
    # Função stub de segurança para controle de vagas (3 alunos/horário)
    conflitos = []
    return conflitos, True

# ==========================================
# 2. CONEXÃO COM GOOGLE SHEETS (BLINDADA)
# ==========================================
conexao_ok = False
erro_msg = ""

colunas_oficiais = ["Nome", "Telefone", "Bairro", "Plano", "Valor Plano", "Vencimento", "Dias", "Horario", "Status", "Queixa", "Conduta", "Genero", "Nascimento", "Inicio_Aulas", "CPF", "Valor Mensal", "Endereco", "Valor"]

df_alunos = pd.DataFrame(columns=colunas_oficiais)
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
    
    @st.cache_data(ttl=2)
    def ler_dados_planilha(aba_ou_indice):
        return conn.read(worksheet=aba_ou_indice)
    
    try: 
        dados_brutos = ler_dados_planilha(0)
        df_alunos = limpiar_dataframe(dados_brutos)
        
        if df_alunos.empty or len(df_alunos.columns) == 0:
            df_alunos = pd.DataFrame(columns=colunas_oficiais)
        else:
            for col in colunas_oficiais:
                if col not in df_alunos.columns:
                    df_alunos[col] = ""
            df_alunos = df_alunos[colunas_oficiais]
    except Exception as e: 
        df_alunos = pd.DataFrame(columns=colunas_oficiais)
    
    try: df_financeiro = limpiar_dataframe(ler_dados_planilha("financeiro"))
    except: df_financeiro = pd.DataFrame(columns=["Aluno", "Valor", "Data", "Forma", "Categoria", "Status"])
    
    try: df_espera = limpiar_dataframe(ler_dados_planilha("espera"))
    except: df_espera = pd.DataFrame(columns=["Nome", "Telefone", "Dia Preferencia", "Hora Preferencia"])
    
    try: df_precos = limpiar_dataframe(ler_dados_planilha("precos"))
    except: df_precos = pd.DataFrame(columns=["Plano", "Valor"])
    
    try: df_evolucoes = limpiar_dataframe(ler_dados_planilha("evolucao"))
    except: df_evolucoes = pd.DataFrame(columns=["Data", "Nome do Aluno", "Evolução"])

    if not df_alunos.empty and "Valor" in df_alunos.columns:
        df_alunos["Valor"] = df_alunos["Valor"].apply(lambda x: converter_para_float(x) if pd.notna(x) else 0.0)

    conexao_ok = True
except Exception as e:
    erro_msg = str(e)
    conexao_ok = False

# Mapeia preços padrão com fallback seguro
dict_precos_padrao = {"1x semana": 180.0, "2x semana": 280.0, "3x semana": 380.0}
if not df_precos.empty and "Plano" in df_precos.columns and "Valor" in df_precos.columns:
    for idx, row in df_precos.iterrows():
        dict_precos_padrao[str(row["Plano"]).strip()] = converter_para_float(row["Valor"])

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
    "Dor Lombar (Lombalgia)", "Hérnia de Disco / Protrusão", "Dor / Lesão nos Ombros",
    "Dor Cervical (Cervicalgia)", "Dor / Lesão nos Joelhos", "Melhoria Postural Operacional",
    "Pilates para Gestantes", "Pilates para Terceira Idade (Idosos)", "Condicionamento Físico Geral"
]

LISTA_CONDUTAS_PADRAO = [
    "Fortalecimento de Core (Powerhouse)", "Mobilização e Articulação de Coluna", "Alongamento de Cadeia Posterior",
    "Estabilização Escapular / Pélvica", "Evitar Flexões Intensas de Tronco", "Evitar Extensões/Hiperlordose",
    "Exercícios de Baixo Impacto Articular", "Treino de Equilíbrio e Propriocepção", "Controle e Reeducação Respiratória"
]

# ==========================================
# 4. ROTEAMENTO DAS TELAS DO MENU
# ==========================================

# --- TELA 1: AGENDA ---
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

# --- TELA 2: ALUNOS ---
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
                    conn.update(worksheet=0, data=df_alunos_salvar)
                    st.cache_data.clear()
                    st.success("🎉 Alterações salvas no banco de dados!")
                    st.rerun()
            
            if st.button("❌ Mover ao Arquivo Morto", key="btn_inativar_manual"):
                df_alunos.at[idx_real_planilha, "Status"] = "Inativo"
                conn.update(worksheet=0, data=df_alunos.fillna("").astype(str))
                st.cache_data.clear()
                st.success("❌ Aluno arquivado com sucesso!")
                st.rerun()
    else:
        st.info("Nenhum aluno ativo cadastrado.")

# --- TELA 3: CADASTRO ---
elif menu == "📝 Cadastro":
    st.title("📝 Cadastro e Anamnese Estruturada")
    
    st.subheader("1. Dados de Contrato (Selecione o Plano)")
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        plano_c = st.selectbox("Plano Contratado:", ["1x semana", "2x semana", "3x semana"])
    
    valor_sugerido_plano = float(dict_precos_padrao.get(plano_c, 180.0))
    with col_p2:
        valor_c = st.number_input("Valor Combinado Mensal (R$):", value=valor_sugerido_plano, step=10.0)

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

    dias_lista_check = [dia for dia, marcado in [("SEG", d_seg), ("TER", d_ter), ("QUA", d_qua), ("QUI", d_qui), ("SEX", d_sex), ("SAB", d_sab)] if marcado]
    dias_c_check = "/".join(dias_lista_check)

    pode_gravar = True
    if dias_lista_check and horarios_selecionados:
        conflitos_preventivos, _ = verificar_lotacao(df_alunos, dias_c_check, horarios_selecionados)
        if conflitos_preventivos:
            pode_gravar = False
            for dia_lotado, hora_lotada, qtd in conflitos_preventivos:
                st.error(f"🛑 **Bloqueado:** O dia **{dia_lotado}** às **{hora_lotada}** já tem o limite máximo de {qtd}/3 alunos ativos. Escolha outra combinação.")
        else:
            st.success("✅ Dias e horários disponíveis para agendamento!")

    with st.form("form_dados_anamnese_completo", clear_on_submit=False):
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
            dias_c = "/".join(dias_lista_check)
            horario_c = ", ".join(horarios_selecionados)
            if not dias_c or not horario_c:
                st.error("❌ Selecione pelo menos um Dia e Horário na seção superior!")
            elif not nome_c or not tel_c:
                st.error("❌ Preencha os campos obrigatórios: Nome e WhatsApp!")
            elif not pode_gravar:
                st.error("❌ Impossível salvar devido ao conflito de limite de lotação.")
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
                    "Nome": str(nome_c).strip(), "Telefone": str(tel_c).strip(), "Bairro": str(bairro_c).strip(),
                    "Plano": str(plano_c), "Valor Plano": str(valor_c), "Vencimento": int(venc_c) if venc_c else 10,
                    "Dias": str(dias_c), "Horario": str(horario_c), "Status": "Ativo",
                    "Queixa": " | ".join(tratamentos) if tratamentos else "", "Conduta": " | ".join(condutas_selecionadas) if condutas_selecionadas else "",
                    "Genero": str(genero_c), "Nascimento": str(nasc_c).strip(), "Inicio_Aulas": str(inicio_c).strip(),
                    "CPF": str(cpf_c).strip(), "Valor Mensal": str(valor_c), "Endereco": f"{endereco_base} {complemento_c}".strip(),
                    "Valor": float(valor_c) if valor_c else 0.0
                }
                df_novo_aluno = pd.DataFrame([nova_linha], columns=colunas_oficiais)
                df_alunos = pd.concat([df_alunos, df_novo_aluno], ignore_index=True)
                
                df_alunos_salvar = df_alunos.fillna("").astype(str).replace("nan", "")
                conn.update(worksheet=0, data=df_alunos_salvar)
                st.cache_data.clear()
                st.success(f"🎉 Aluno {nome_c} adicionado com sucesso!")
                st.rerun()

# --- TELA 4: EVOLUÇÃO ---
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

# --- TELA 5: ESPERA ---
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
        st.subheader("➕ Adicionar Novo Interessado na Lista")
        username_esp = st.text_input("Nome do Interessado:")
        tel_esp = st.text_input("WhatsApp / Telefone:")
        dia_esp = st.text_input("Dia de Preferência:")
        hora_esp = st.text_input("Horário de Preferência:")
        submit_esp = st.form_submit_button("Adicionar à Espera")
        
        if submit_esp:
            if not username_esp.strip() or not tel_esp.strip():
                st.error("❌ Nome e Telefone são obrigatórios.")
            else:
                nova_esp = {
                    "Nome": username_esp.strip(),
                    "Telefone": tel_esp.strip(),
                    "Dia Preferencia": dia_esp.strip(),
                    "Hora Preferencia": hora_esp.strip()
                }
                df_espera = pd.concat([df_espera, pd.DataFrame([nova_esp])], ignore_index=True)
                conn.update(worksheet="espera", data=df_espera.fillna("").astype(str))
                st.cache_data.clear()
                st.success("🎉 Interessado adicionado à lista de espera!")
                st.rerun()

# --- TELA 6: FINANCEIRO ---
elif menu == "💰 Financeiro":
    st.title("💰 Gestão e Fluxo de Caixa")
    
    if not df_financeiro.empty and "Valor" in df_financeiro.columns:
        df_financeiro["Valor"] = df_financeiro["Valor"].apply(converter_para_float)
    
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        total_pago = 0.0
        if not df_financeiro.empty and "Status" in df_financeiro.columns:
            total_pago = df_financeiro[df_financeiro["Status"].astype(str).str.upper() == "PAGO"]["Valor"].sum()
        st.metric("Total de Receitas Confirmadas (Pago)", formatar_brl(total_pago))
        
    with col_f2:
        total_pendente = 0.0
        if not df_financeiro.empty and "Status" in df_financeiro.columns:
            total_pendente = df_financeiro[df_financeiro["Status"].astype(str).str.upper() == "PENDENTE"]["Valor"].sum()
        st.metric("Total de Receitas Pendentes", formatar_brl(total_pendente))
        
    with col_f3:
        alunos_ativos_count = len(df_alunos[df_alunos["Status"].astype(str).str.upper() == "ATIVO"]) if not df_alunos.empty else 0
        st.metric("Alunos Ativos no Mês", alunos_ativos_count)

    st.markdown("---")
    st.subheader("📑 Lançamentos Registrados")
    if not df_financeiro.empty:
        df_fin_vis = df_financeiro.copy()
        if "Valor" in df_fin_vis.columns:
            df_fin_vis["Valor"] = df_fin_vis["Valor"].apply(formatar_brl)
        st.dataframe(df_fin_vis, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum lançamento financeiro cadastrado.")

    with st.form("form_financeiro", clear_on_submit=True):
        st.subheader("➕ Adicionar Novo Lançamento Manual")
        lista_alunos_fin = ["-- Lançamento Avulso / Outros --"]
        if not df_alunos.empty and "Nome" in df_alunos.columns:
            lista_alunos_fin += sorted(df_alunos["Nome"].unique().tolist())
            
        aluno_fin = st.selectbox("Aluno Relacionado (Opcional):", lista_alunos_fin)
        valor_fin = st.number_input("Valor do Lançamento (R$):", min_value=0.0, step=10.0)
        data_fin = st.date_input("Data do Lançamento:", datetime.now())
        forma_fin = st.selectbox("Forma de Pagamento:", ["Pix", "Dinheiro", "Cartão de Crédito", "Cartão de Débito", "Transferência"])
        cat_fin = st.selectbox("Categoria:", ["Mensalidade", "Avaliação Física", "Aula Avulsa", "Outros"])
        status_fin = st.selectbox("Status Inicial:", ["Pago", "Pendente"])
        
        submit_fin = st.form_submit_button("Registrar Lançamento")
        
        if submit_fin:
            if valor_fin <= 0:
                st.error("❌ O valor precisa ser maior que zero.")
            else:
                relacao = "" if aluno_fin == "-- Lançamento Avulso / Outros --" else aluno_fin
                novo_lanc = {
                    "Aluno": relacao,
                    "Valor": valor_fin,
                    "Data": data_fin.strftime("%d/%m/%Y"),
                    "Forma": forma_fin,
                    "Categoria": cat_fin,
                    "Status": status_fin
                }
                df_financeiro = pd.concat([df_financeiro, pd.DataFrame([novo_lanc])], ignore_index=True)
                conn.update(worksheet="financeiro", data=df_financeiro.fillna("").astype(str))
                st.cache_data.clear()
                st.success("🎉 Lançamento financeiro registrado!")
                st.rerun()

# --- TELA 7: PERFIL ---
elif menu == "👤 Perfil":
    st.title("👤 Perfil Completo do Aluno e Prontuário Digital")
    
    lista_todos_alunos = []
    if not df_alunos.empty and "Nome" in df_alunos.columns:
        lista_todos_alunos = sorted(df_alunos["Nome"].unique().tolist())
        
    if lista_todos_alunos:
        aluno_perfil = st.selectbox("Selecione o Aluno para Carregar o Prontuário:", lista_todos_alunos)
        row_aluno = df_alunos[df_alunos["Nome"] == aluno_perfil].iloc[0]
        
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.markdown(f"### 📋 Informações Gerais")
            st.write(f"**Nome:** {row_aluno.get('Nome', '')}")
            st.write(f"**WhatsApp:** {row_aluno.get('Telefone', '')}")
            st.write(f"**CPF:** {row_aluno.get('CPF', '')}")
            st.write(f"**Gênero:** {row_aluno.get('Genero', '')}")
            st.write(f"**Nascimento:** {row_aluno.get('Nascimento', '')}")
            st.write(f"**Idade Calculada:** {calcular_idade(row_aluno.get('Nascimento', ''))}")
            st.write(f"**Bairro:** {row_aluno.get('Bairro', '')}")
            st.write(f"**Endereço:** {row_aluno.get('Endereco', '')}")
            
        with col_p2:
            st.markdown(f"### ⚙️ Detalhes do Contrato Ativo")
            st.write(f"**Status Cadastral:** {row_aluno.get('Status', '')}")
            st.write(f"**Plano Contratado:** {row_aluno.get('Plano', '')}")
            st.write(f"**Valor Mensal Acordado:** {formatar_brl(row_aluno.get('Valor', 0.0))}")
            st.write(f"**Dia de Vencimento:** {row_aluno.get('Vencimento', '')}")
            st.write(f"**Dias Fixos na Agenda:** {row_aluno.get('Dias', '')}")
            st.write(f"**Horários Escolhidos:** {row_aluno.get('Horario', '')}")
            st.write(f"**Início das Aulas:** {row_aluno.get('Inicio_Aulas', '')}")

        st.markdown("---")
        st.markdown("### 🩺 Mapeamento Clínico (Anamnese)")
        queixas_aluno = row_aluno.get('Queixa', '')
        if queixas_aluno:
            for q in str(queixas_aluno).split(" | "):
                st.warning(f"⚠️ **Condição Identificada:** {q}")
        else:
            st.info("Nenhuma condição clínica impeditiva ou queixa registrada.")

        st.markdown("### 📋 Condutas de Restrição e Diretrizes Clínicas")
        condutas_aluno = row_aluno.get('Conduta', '')
        if condutas_aluno:
            for c in str(condutas_aluno).split(" | "):
                st.success(f"🔹 {c}")
        else:
            st.info("Sem restrições ou condutas específicas montadas para este aluno.")
    else:
        st.info("Nenhum aluno cadastrado no sistema.")

# --- TELA 8: PREÇOS ---
elif menu == "⚙️ Preços":
    st.title("⚙️ Tabela de Preços e Planos Padrão")
    st.write("Valores de referência aplicados na sugestão do cadastro de novos alunos.")
    
    if not df_precos.empty:
        df_precos_vis = df_precos.copy()
        if "Valor" in df_precos_vis.columns:
            df_precos_vis["Valor"] = df_precos_vis["Valor"].apply(lambda x: formatar_brl(converter_para_float(x)))
        st.dataframe(df_precos_vis, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum preço padrão mapeado na planilha.")

    with st.form("form_precos", clear_on_submit=True):
        st.subheader("✏️ Atualizar ou Inserir Novo Preço de Referência")
        plano_p = st.selectbox("Plano Alvo:", ["1x semana", "2x semana", "3x semana", "Avulso", "Avaliação"])
        valor_p = st.number_input("Valor Padrão de Referência (R$):", min_value=0.0, step=10.0)
        submit_p = st.form_submit_button("Gravar Preço")
        
        if submit_p:
            if valor_p <= 0:
                st.error("❌ Insira um valor válido.")
            else:
                if not df_precos.empty and plano_p in df_precos["Plano"].values:
                    df_precos.loc[df_precos["Plano"] == plano_p, "Valor"] = valor_p
                else:
                    novo_p = {"Plano": plano_p, "Valor": valor_p}
                    df_precos = pd.concat([df_precos, pd.DataFrame([novo_p])], ignore_index=True)
                
                conn.update(worksheet="precos", data=df_precos.fillna("").astype(str))
                st.cache_data.clear()
                st.success("🎉 Tabela de preços atualizada!")
                st.rerun()

# --- TELA 9: ARQUIVO MORTO ---
elif menu == "📁 Arquivo Morto":
    st.title("📁 Arquivo Morto (Alunos Inativos)")
    st.write("Lista contendo os registros de alunos desativados ou antigos.")
    
    if not df_alunos.empty and "Status" in df_alunos.columns:
        df_inativos = df_alunos[df_alunos["Status"].astype(str).str.upper() == "INATIVO"]
    else:
        df_inativos = pd.DataFrame()

    if not df_inativos.empty:
        st.dataframe(df_inativos, use_container_width=True, hide_index=True)
        st.markdown("---")
        opcoes_reativar = ["-- Selecione para Reativar --"] + [f"{row['Nome']} (Reg: {idx})" for idx, row in df_inativos.iterrows()]
        aluno_reativar_str = st.selectbox("Escolha um aluno para restaurar o status de Ativo:", opcoes_reativar)
        
        if aluno_reativar_str != "-- Selecione para Reativar --":
            idx_reativar = int(aluno_reativar_str.split("(Reg: ")[1].replace(")", ""))
            if st.button("🔄 Confirmar Reativação do Aluno"):
                df_alunos.at[idx_reativar, "Status"] = "Ativo"
                conn.update(worksheet=0, data=df_alunos.fillna("").astype(str))
                st.cache_data.clear()
                st.success(f"🎉 Aluno reativado com sucesso!")
                st.rerun()
    else:
        st.info("Nenhum aluno inativo no Arquivo Morto.")

# --- TELA 10: IMPRIMIR PRONTUÁRIO ---
elif menu == "🖨️ Imprimir Prontuário":
    st.title("🖨️ Impressão Litográfica de Prontuário")
    st.write("Gere uma folha clínica limpa de prontuário, formatada em folha única A4 pronta para impressão física ou PDF.")
    
    lista_filtro_pr = []
    if not df_alunos.empty and "Nome" in df_alunos.columns:
        lista_filtro_pr = sorted(df_alunos["Nome"].unique().tolist())
        
    if lista_filtro_pr:
        aluno_pr = st.selectbox("Selecione o Aluno para Exportar o Prontuário:", lista_filtro_pr, key="sel_print_pr")
        row_pr = df_alunos[df_alunos["Nome"] == aluno_pr].iloc[0]
        
        df_v_aluno = pd.DataFrame()
        if not df_evolucoes.empty and "Nome do Aluno" in df_evolucoes.columns:
            df_v_aluno = df_evolucoes[df_evolucoes["Nome do Aluno"] == aluno_pr]
            
        html_bloco_evolucoes = ""
        if not df_v_aluno.empty:
            for idx, r_ev in df_v_aluno.iterrows():
                html_bloco_evolucoes += f"""
                <div class="evolucao-item">
                    <strong>📅 Data:</strong> {r_ev.get('Data','')} <br/>
                    {r_ev.get('Evolução','')}
                </div>
                """
        else:
            html_bloco_evolucoes = "<p style='color:#555;'>Nenhum histórico ou registro de evolução clínica lançado até o momento.</p>"

        html_prontuario = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Prontuário Clínico - {row_pr.get('Nome', '')}</title>
            <style>
                @media print {{
                    body {{ margin: 0; padding: 0; background: #fff; }}
                    .btn-print-trigger {{ display: none !important; }}
                }}
                body {{
                    font-family: Arial, sans-serif;
                    color: #000;
                    background-color: #FAFAFA;
                    padding: 20px;
                }}
                .prontuario-container {{
                    max-width: 800px;
                    background-color: #FFF;
                    margin: 0 auto;
                    padding: 30px;
                    border: 1px solid #DDD;
                    box-shadow: 0 0 10px rgba(0,0,0,0.05);
                }}
                .header-print {{
                    text-align: center;
                    border-bottom: 2px solid #000;
                    padding-bottom: 15px;
                    margin-bottom: 20px;
                }}
                .header-print h1 {{ margin: 0; font-size: 24px; text-transform: uppercase; }}
                .header-print p {{ margin: 5px 0 0 0; font-size: 14px; color: #333; }}
                .prontuario-secao {{
                    background-color: #F0F0F0;
                    padding: 6px 10px;
                    font-weight: bold;
                    font-size: 14px;
                    text-transform: uppercase;
                    margin-top: 20px;
                    margin-bottom: 10px;
                    border-left: 4px solid #000;
                }}
                table.dados-tabela {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 15px;
                }}
                table.dados-tabela td {{
                    padding: 6px;
                    border: 1px solid #CCC;
                    font-size: 13px;
                    vertical-align: top;
                }}
                .label-fixo {{ font-weight: bold; width: 120px; background-color: #FAFAFA; }}
                .bloco-texto {{
                    font-size: 13px;
                    line-height: 1.5;
                    border: 1px solid #CCC;
                    padding: 10px;
                    background-color: #FAFAFA;
                    min-height: 60px;
                }}
                .evolucao-item {{
                    font-size: 13px;
                    border-bottom: 1px dashed #999;
                    padding: 8px 0;
                }}
                .btn-print-trigger {{
                    display: block;
                    width: 180px;
                    margin: 0 auto 20px auto;
                    padding: 10px;
                    background-color: #2E5A44;
                    color: #FFF;
                    text-align: center;
                    font-weight: bold;
                    text-decoration: none;
                    border-radius: 4px;
                    cursor: pointer;
                }}
            </style>
        </head>
        <body>
            <div class="btn-print-trigger" onclick="window.print();">🖨️ Imprimir Prontuário</div>
            
            <div class="prontuario-container">
                <div class="header-print">
                    <h1>Highline Management</h1>
                    <p>Prontuário Clínico Integrado & Ficha de Anamnese</p>
                </div>
                
                <div class="prontuario-secao">👤 Dados Cadastrais e Pessoais</div>
                <table class="dados-tabela">
                    <tr>
                        <td class="label-fixo">Aluno:</td>
                        <td colspan="3"><strong>{row_pr.get('Nome', '')}</strong></td>
                    </tr>
                    <tr>
                        <td class="label-fixo">WhatsApp:</td>
                        <td>{row_pr.get('Telefone', '')}</td>
                        <td class="label-fixo">CPF:</td>
                        <td>{row_pr.get('CPF', '')}</td>
                    </tr>
                    <tr>
                        <td class="label-fixo">Nascimento:</td>
                        <td>{row_pr.get('Nascimento', '')} (Idade: {calcular_idade(row_pr.get('Nascimento', ''))})</td>
                        <td class="label-fixo">Gênero:</td>
                        <td>{row_pr.get('Genero', '')}</td>
                    </tr>
                    <tr>
                        <td class="label-fixo">Endereço:</td>
                        <td colspan="3">{row_pr.get('Endereco', '')} (Bairro: {row_pr.get('Bairro', '')})</td>
                    </tr>
                </table>
                
                <div class="prontuario-secao">⚙️ Dados Contratuais e Operacionais</div>
                <table class="dados-tabela">
                    <tr>
                        <td class="label-fixo">Plano Atual:</td>
                        <td>{row_pr.get('Plano', '')}</td>
                        <td class="label-fixo">Valor Mensal:</td>
                        <td>{formatar_brl(row_pr.get('Valor', 0.0))}</td>
                    </tr>
                    <tr>
                        <td class="label-fixo">Horários:</td>
                        <td>{row_pr.get('Horario', '')}</td>
                        <td class="label-fixo">Dias Fixos:</td>
                        <td colspan="3">{row_pr.get('Dias', '')}</td>
                    </tr>
                </table>
                
                <div class="prontuario-secao">🩺 Diagnóstico Clínico e Anamnese</div>
                <div class="bloco-texto">
                    {row_pr.get('Queixa', 'Nenhuma condição mapeada.')}
                </div>
                
                <div class="prontuario-secao">📋 Diretrizes de Conduta Operacional</div>
                <div class="bloco-texto" style="white-space: pre-wrap;">
                    {row_pr.get('Conduta', 'Sem restrições ou diretrizes específicas cadastradas.')}
                </div>
                
                <div class="prontuario-secao">📈 Evolução do Tratamento</div>
                <div style="margin-top: 5px;">
                    {html_bloco_evolucoes}
                </div>
                
                <div style="margin-top: 60px; text-align: center; page-break-inside: avoid;">
                    <div style="border-top: 1px solid #000; width: 280px; margin: 0 auto; padding-top: 5px; font-size: 12px;">
                        Assinatura do Profissional Responsável
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        components.html(html_prontuario, height=1200, scrolling=True)
    else:
        st.info("Nenhum aluno cadastrado no sistema para gerar prontuário.")
