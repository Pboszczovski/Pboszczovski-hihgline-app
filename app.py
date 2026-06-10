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
    </style>
""", unsafe_allow_html=True)

# ==========================================
# FUNÇÕES AUXILIARES DE LIMPEZA E FORMATAÇÃO
# ==========================================
def limpiar_dataframe(df):
    if df is None or df.empty:
        return pd.DataFrame()
    df = df.loc[:, ~df.columns.astype(str).str.contains('^Unnamed')]
    df.columns = df.columns.str.strip()
    df = df.dropna(how="all")
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

# Inicialização preventiva com colunas padrão para evitar NameError/AttributeError
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
    
    # Leituras protegidas com fallback seguro
    try: df_alunos = limpiar_dataframe(conn.read(worksheet="alunos", ttl=5))
    except: pass
    
    try: df_financeiro = limpiar_dataframe(conn.read(worksheet="financeiro", ttl=5))
    except: pass
    
    try: df_espera = limpiar_dataframe(conn.read(worksheet="espera", ttl=5))
    except: pass
    
    try: df_precos = limpiar_dataframe(conn.read(worksheet="precos", ttl=5))
    except: pass
    
    try: df_evolucoes = limpiar_dataframe(conn.read(worksheet="evolucao", ttl=5))
    except: pass

    if not df_alunos.empty:
        if "Valor Mensal" in df_alunos.columns and "Valor" not in df_alunos.columns:
            df_alunos["Valor"] = df_alunos["Valor Mensal"]
        elif "Valor Mensal" in df_alunos.columns and "Valor" in df_alunos.columns:
            df_alunos["Valor"] = df_alunos["Valor"].fillna(df_alunos["Valor Mensal"])

    if not df_espera.empty and "Nome" in df_espera.columns:
        df_espera = df_espera[df_espera["Nome"].astype(str).str.strip() != ""]

    conexao_ok = True
except Exception as e:
    erro_msg = str(e)

if not conexao_ok or df_alunos.empty:
    st.warning("⚠️ O Google Sheets atingiu o limite de requisições diárias ou está instável. Exibindo dados em modo de segurança.")

dict_precos_padrao = {}
if df_precos is not None and not df_precos.empty and "Plano" in df_precos.columns:
    for _, r in df_precos.iterrows():
        dict_precos_padrao[str(r["Plano"])] = converter_para_float(r["Valor"])
else:
    dict_precos_padrao = {"1x semana": 180.0, "2x semana": 220.0, "3x semana": 300.0}

# ==========================================
# FUNÇÃO AUXILIAR DE VALIDAÇÃO DE CAPACIDADE
# ==========================================
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
    alunos_no_horario = []
    
    for h_alvo in horarios_solicitados:
        for dia in dias_solicitados:
            qtd_no_bloco = 0
            for idx, row in df_ativos.iterrows():
                h_atual = str(row["Horario"]).strip()
                if h_atual == h_alvo:
                    d_atual = [d.strip().upper() for d in str(row["Dias"]).replace("/", " ").replace(",", " ").split() if d.strip()]
                    if dia in d_atual:
                        qtd_no_bloco += 1
                        if f"{row['Nome']} ({row['Dias']} às {row['Horario']})" not in alunos_no_horario:
                            alunos_no_horario.append(f"{row['Nome']} ({row['Dias']} às {row['Horario']})")
            if qtd_no_bloco >= 3:
                conflitos.append((dia, h_alvo, qtd_no_bloco))
                
    return conflitos, alunos_no_horario

# ==========================================
# 3. BARRA LATERAL - LOGO E MENU
# ==========================================
with st.sidebar:
    st.markdown('<div class="logo-container">', unsafe_allow_html=True)
    st.markdown("## 🏋️‍♂️ Studio Highline")
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

# --- 1. TELA: AGENDA ---
if menu == "📅 Agenda":
    st.title("📅 Agenda de Treinos")
    hoje_datetime = datetime.now()
    hoje_mm_dd = hoje_datetime.strftime("%m-%d")
    niver_hoje = []
    
    if not df_alunos.empty and "Nascimento" in df_alunos.columns and "Nome" in df_alunos.columns:
        for idx, row in df_alunos.iterrows():
            try:
                data_nasc = pd.to_datetime(row["Nascimento"], dayfirst=True)
                if data_nasc.strftime("%m-%d") == hoje_mm_dd:
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
    df_ativos = df_alunos[df_alunos["Status"].astype(str).str.upper() == "ATIVO"] if not df_alunos.empty else pd.DataFrame()
        
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

# --- 2. TELA: ALUNOS ---
elif menu == "👥 Alunos":
    st.title("👥 Base de Alunos Ativos")
    df_ativos = df_alunos[df_alunos["Status"].astype(str).str.upper() == "ATIVO"] if not df_alunos.empty else pd.DataFrame()

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
            
            if btn_salvar_alt and not bloqueio_edicao:
                df_alunos.at[idx_real_planilha, "Plano"] = novo_plano
                df_alunos.at[idx_real_planilha, "Valor"] = float(novo_valor)  
                df_alunos.at[idx_real_planilha, "Dias"] = novos_dias
                df_alunos.at[idx_real_planilha, "Horario"] = novo_horario
                
                conn.update(worksheet="alunos", data=df_alunos)
                st.success("🎉 Alterações salvas! Mude de aba no menu lateral para atualizar.")
                st.cache_data.clear()
                
            if btn_inativar_alt:
                df_alunos.at[idx_real_planilha, "Status"] = "Inativo"
                conn.update(worksheet="alunos", data=df_alunos)
                st.success("❌ Aluno arquivado! Mude de aba no menu lateral para atualizar.")
                st.cache_data.clear()
    else:
        st.info("Nenhum aluno ativo cadastrado.")

# --- 3. TELA: CADASTRO ---
elif menu == "📝 Cadastro":
    st.title("📝 Cadastro e Anamnese Estruturada")
    
    st.subheader("📌 Escolha de Dias e Horários de Treino")
    c_dia1, c_dia2, c_dia3, c_dia4, c_dia5, c_dia6 = st.columns(6)
    with c_dia1: d_seg = st.checkbox("SEG")
    with c_dia2: d_ter = st.checkbox("TER")
    with c_dia3: d_qua = st.checkbox("QUA")
    with c_dia4: d_qui = st.checkbox("QUI")
    with c_dia5: d_sex = st.checkbox("SEX")
    with c_dia6: d_sab = st.checkbox("SAB")
    
    dias_lista = [dia for dia, marcado in [("SEG", d_seg), ("TER", d_ter), ("QUA", d_qua), ("QUI", d_qui), ("SEX", d_sex), ("SAB", d_sab)] if marcado]
    dias_c = "/".join(dias_lista)
    
    lista_horarios_disponiveis = ["7:30", "8:30", "9:30", "10:30", "11:30", "12:30", "15:30", "16:30", "17:30", "18:30", "19:30"]
    cols_horarios = st.columns(6)
    horarios_selecionados = []
    for index, hora_item in enumerate(lista_horarios_disponiveis):
        with cols_horarios[index % 6]:
            if st.checkbox(hora_item, key=f"cad_h_{hora_item}"):
                horarios_selecionados.append(hora_item)
    horario_c = ", ".join(horarios_selecionados)

    bloqueio_cadastro = False
    if dias_c and horarios_selecionados and not df_alunos.empty:
        conflitos, _ = verificar_lotacao(df_alunos, dias_c, horarios_selecionados)
        if conflitos:
            bloqueio_cadastro = True
            for dia_lotado, hora_lotada, qtd in conflitos:
                st.error(f"🛑 O dia {dia_lotado} às {hora_lotada} atingiu o limite máximo ({qtd}/3 alunos).")

    st.subheader("1. Dados Pessoais e de Contrato")
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        plano_c = st.selectbox("Plano Contratado:", ["1x semana", "2x semana", "3x semana"])
    with col_p2:
        valor_c = st.number_input("Valor Combinado Mensal (R$):", value=float(dict_precos_padrao.get(plano_c, 220.0)))

    with st.form("form_dados_anamnese_limpo"):
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
        c_q1, c_q2, c_q3 = st.columns(3)
        with c_q1:
            q_lombar = st.checkbox("Dor Lombar (Lombalgia)")
            q_cervical = st.checkbox("Dor Cervical (Cervicalgia)")
        with c_q2:
            q_hernia = st.checkbox("Hérnia de Disco / Protrusão")
            q_joelho = st.checkbox("Dor / Lesão nos Joelhos")
        with c_q3:
            q_ombro = st.checkbox("Dor / Lesão nos Ombros")
            q_postura = st.checkbox("Melhoria Postural Operacional")
            
        queixa_extra = st.text_input("Outras Queixas Adicionais:")
        conduta_extra = st.text_input("Diretrizes de Conduta Específicas:")

        btn_enviar = st.form_submit_button("💾 Salvar Novo Aluno", disabled=bloqueio_cadastro)
        
        if btn_enviar:
            if not dias_c or not horario_c:
                st.error("❌ Selecione pelo menos um Dia e Horário!")
            elif not nome_c or not tel_c:
                st.error("❌ Preencha o Nome e o WhatsApp!")
            else:
                queixas = [q for q, m in [("Lombar", q_lombar), ("Cervical", q_cervical), ("Hérnia", q_hernia), ("Joelho", q_joelho), ("Ombro", q_ombro), ("Postural", q_postura)] if m]
                if queixa_extra: queixas.append(queixa_extra)
                
                nova_linha = {
                    "Nome": nome_c, "Telefone": tel_c, "Bairro": bairro_c, "Plano": plano_c, 
                    "Valor": float(valor_c), "Vencimento": int(venc_c), "Dias": dias_c, "Horario": horario_c, 
                    "Status": "Ativo", "Queixa": " | ".join(queixas), "Conduta": conduta_extra, 
                    "Genero": genero_c, "Nascimento": nasc_c, "Inicio_Aulas": inicio_c, "CPF": cpf_c, 
                    "Endereco": f"{endereco_base} {complemento_c}".strip()
                }
                
                df_alunos = pd.concat([df_alunos, pd.DataFrame([nova_linha])], ignore_index=True)
                conn.update(worksheet="alunos", data=df_alunos)
                st.success(f"🎉 {nome_c} cadastrado! Recarregue trocando de aba.")
                st.cache_data.clear()

# --- 4. TELA: EVOLUÇÃO ---
elif menu == "📈 Evolução":
    st.title("📈 Evolução Clínica dos Alunos")
    
    lista_nomes_alunos = sorted(list(df_alunos["Nome"].dropna().unique())) if not df_alunos.empty else []
    
    with st.form("form_nova_evolucao"):
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
                st.success("🎉 Evolução registrada!")
                st.cache_data.clear()

    st.markdown("---")
    # CORREÇÃO CRÍTICA DO ATTRIBUTERROR (Imagem 6): Seguro contra falha de tipos e listas nulas
    opcoes_filtro = ["Todos"] + lista_nomes_alunos
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
    total_recebido = df_financeiro[df_financeiro["Status"].astype(str).str.upper() == "PAGO"]["Valor"].apply(converter_para_float).sum() if not df_financeiro.empty else 0.0
    total_pendente = df_financeiro[df_financeiro["Status"].astype(str).str.upper() == "PENDENTE"]["Valor"].apply(converter_para_float).sum() if not df_financeiro.empty else 0.0
    
    f_col1, f_col2 = st.columns(2)
    with f_col1: st.metric("Total Recebido", formatar_brl(total_recebido))
    with f_col2: st.metric("Total Pendente", formatar_brl(total_pendente))
        
    st.markdown("### 📥 Registrar Baixa de Pagamento")
    if not df_alunos.empty:
        opcoes_baixa = [f"{r['Nome']} | Vencimento: {r.get('Vencimento','10')}" for _, r in df_alunos.iterrows() if str(r.get("Status")).upper() == "ATIVO"]
        if opcoes_baixa:
            sel_baixa = st.selectbox("Selecione o aluno:", opcoes_baixa)
            nome_f = sel_baixa.split(" | ")[0]
            
            if st.button("Confirmar Pagamento"):
                nova_baixa = {"Aluno": nome_f, "Valor": 220.0, "Data": datetime.now().strftime("%d/%m/%Y"), "Forma": "PIX", "Categoria": "Mensalidade", "Status": "PAGO"}
                df_financeiro = pd.concat([df_financeiro, pd.DataFrame([nova_baixa])], ignore_index=True)
                conn.update(worksheet="financeiro", data=df_financeiro)
                st.success("✅ Sucesso!")
                st.cache_data.clear()
                
    if not df_financeiro.empty:
        st.dataframe(df_financeiro, use_container_width=True, hide_index=True)

# --- 7. TELA: PERFIL ---
elif menu == "👤 Perfil":
    st.title("👤 Configurações de Perfil")
    st.write(f"**Conexão do Banco de Dados:** {'Operacional' if conexao_ok else 'Erro de Comunicação'}")
    if erro_msg: st.error(erro_msg)

# --- 8. TELA: PREÇOS ---
elif menu == "⚙️ Preços":
    st.title("⚙️ Tabela de Preços")
    st.dataframe(pd.DataFrame(list(dict_precos_padrao.items()), columns=["Plano", "Valor"]), use_container_width=True, hide_index=True)

# --- 9. TELA: ARQUIVO MORTO ---
elif menu == "📁 Arquivo Morto":
    st.title("📁 Alunos Inativos")
    if not df_alunos.empty:
        st.dataframe(df_alunos[df_alunos["Status"].astype(str).str.upper() == "INATIVO"], use_container_width=True, hide_index=True)

# --- 10. TELA: IMPRIMIR PRONTUÁRIO ---
elif menu == "🖨️ Imprimir Prontuário":
    st.title("🖨️ Ficha Cadastral e Prontuário do Aluno")
    
    if not df_alunos.empty:
        aluno_p = st.selectbox("Selecione o Aluno para Emitir Documentação:", sorted(list(df_alunos["Nome"].dropna().unique())))
        
        if aluno_p:
            dados = df_alunos[df_alunos["Nome"] == aluno_p].iloc[0]
            evolucoes_aluno = df_evolucoes[df_evolucoes["Nome do Aluno"] == aluno_p] if not df_evolucoes.empty else pd.DataFrame()
            
            html_evolucoes = ""
            if not evolucoes_aluno.empty:
                for _, r in evolucoes_aluno.sort_index(ascending=False).iterrows():
                    html_evolucoes += f"<p style='margin:4px 0;'><b>{r['Data']}:</b> {r['Evolução']}</p>"
            else:
                html_evolucoes = "<p style='color: #777;'>Nenhum histórico lançado.</p>"
                
            # CORREÇÃO VISUAL (Imagem 4): Utilização correta de exibição sem expor código HTML cru
            html_prontuario = f"""
            <div style="padding:20px; font-family: sans-serif; border:1px solid #ccc; background-color:#fff; color:#000;">
                <h2 style="text-align:center; color:#2E5A44;">STUDIO HIGHLINE PILATES</h2>
                <p style="text-align:center; font-size:12px; margin-top:-10px;">Ficha Cadastral, Anamnese e Prontuário do Aluno</p>
                <hr/>
                <p><b>Nome:</b> {dados.get('Nome', '-')}</p>
                <p><b>WhatsApp:</b> {dados.get('Telefone', '-')} | <b>CPF:</b> {dados.get('CPF', '-')}</p>
                <p><b>Nascimento:</b> {dados.get('Nascimento', '-')} | <b>Gênero:</b> {dados.get('Genero', '-')}</p>
                <p><b>Endereço:</b> {dados.get('Endereco', '-')} (Bairro: {dados.get('Bairro', '-')})</p>
                <p><b>Plano contratado:</b> {dados.get('Plano', '-')} | <b>Horários:</b> {dados.get('Dias', '-')} às {dados.get('Horario', '-')}</p>
                <hr/>
                <h3>Anamnese e Queixas Principais:</h3>
                <p>{dados.get('Queixa', 'Sem queixas registradas.')}</p>
                <h3>Diretrizes de Conduta:</h3>
                <p>{dados.get('Conduta', 'Sem restrições especificadas.')}</p>
                <hr/>
                <h3>Histórico Clínico Recente:</h3>
                {html_evolucoes}
            </div>
            """
            st.components.v1.html(html_prontuario, height=500, scroller=True)
            st.caption("💡 Dica: Clique com o botão direito na ficha acima e selecione 'Imprimir' ou use Ctrl+P.")
