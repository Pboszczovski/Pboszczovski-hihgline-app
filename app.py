import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
import os

# ==============================================================================
# 1. CONFIGURAÇÕES VISUAIS, IDENTIDADE VISUAL E COMPORTAMENTO DE IMPRESSÃO
# ==============================================================================
st.set_page_config(page_title="Highline Management System", layout="wide", page_icon="🏋️‍♂️")

st.markdown("""
    <style>
        [data-testid="stSidebar"] { background-color: #2E5A44 !important; }
        [data-testid="stSidebar"] * { color: white !important; }
        .stRadio input[type="radio"]:checked + div { color: #FFD700 !important; font-weight: bold !important; }
        
        .prontuario-card {
            background-color: #ffffff !important;
            color: #000000 !important;
            padding: 30px;
            border: 3px solid #2E5A44;
            border-radius: 10px;
            font-family: 'Arial', sans-serif;
            margin-top: 20px;
            box-shadow: 0px 4px 10px rgba(0,0,0,0.1);
        }
        .prontuario-header { 
            text-align: center; 
            border-bottom: 4px solid #2E5A44; 
            padding-bottom: 15px; 
            color: #2E5A44 !important; 
        }
        .prontuario-secao { 
            background-color: #2E5A44;
            color: white !important;
            padding: 6px 12px;
            margin-top: 25px; 
            font-weight: bold; 
            border-radius: 4px;
        }
        .tabela-prontuario { 
            width: 100%; 
            border-collapse: collapse; 
            margin-top: 12px; 
        }
        .tabela-prontuario td { 
            padding: 10px; 
            border: 1px solid #cccccc; 
            color: #000000 !important; 
            font-size: 14px;
        }
        @media print {
            [data-testid="stSidebar"], button, .no-print, header, [data-testid="stHeader"] { 
                display: none !important; 
            }
            .prontuario-card { 
                border: none !important; 
                box-shadow: none !important;
                padding: 0 !important; 
            }
            body { background: white !important; }
        }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. MECANISMOS DE TRATAMENTO DE DADOS (CONVERSORES E PARSERS)
# ==============================================================================
def limpar_dataframe(df):
    if df is None: return pd.DataFrame()
    try:
        df = df.loc[:, ~df.columns.astype(str).str.contains('^Unnamed')]
        df.columns = df.columns.str.strip()
        return df.dropna(how="all")
    except:
        return pd.DataFrame()

def formatar_brl(valor):
    try:
        if pd.isna(valor) or valor == "" or valor is None: return "R$ 0,00"
        if isinstance(valor, (int, float)): 
            val_float = float(valor)
        else:
            v = str(valor).replace("R$", "").replace(" ", "")
            if "," in v and "." in v: v = v.replace(".", "").replace(",", ".")
            elif "," in v: v = v.replace(",", ".")
            val_float = float(v)
        return f"R$ {val_float:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"

def converter_para_float(valor):
    try:
        if pd.isna(valor) or valor == "" or valor is None: return 0.0
        if isinstance(valor, (int, float)): return float(valor)
        v = str(valor).replace("R$", "").replace(" ", "")
        if "," in v and "." in v: v = v.replace(".", "").replace(",", ".")
        elif "," in v: v = v.replace(",", ".")
        return float(v)
    except:
        return 0.0

def calcular_idade(data_nasc_str):
    try:
        if pd.isna(data_nasc_str) or not str(data_nasc_str).strip(): return None
        dt = pd.to_datetime(str(data_nasc_str).strip(), dayfirst=True, errors='coerce')
        if pd.isna(dt): return None
        hoje = datetime.now()
        return hoje.year - dt.year - ((hoje.month, hoje.day) < (dt.month, dt.day))
    except:
        return None

# ==============================================================================
# 3. MOTOR DE CONEXÃO ROBUSTA COM GOOGLE SHEETS
# ==============================================================================
df_alunos = pd.DataFrame()
df_financeiro = pd.DataFrame()
df_espera = pd.DataFrame()
df_precos = pd.DataFrame()
df_evolucoes = pd.DataFrame()
df_arquivo_morto = pd.DataFrame()
conexao_ok = False

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    try: df_alunos = limpar_dataframe(conn.read(worksheet="alunos", ttl=0))
    except: df_alunos = pd.DataFrame()
    
    try: df_financeiro = limpar_dataframe(conn.read(worksheet="financeiro", ttl=0))
    except: df_financeiro = pd.DataFrame()
    
    try: df_espera = limpar_dataframe(conn.read(worksheet="espera", ttl=0))
    except: df_espera = pd.DataFrame()
    
    try: df_precos = limpar_dataframe(conn.read(worksheet="precos", ttl=0))
    except: df_precos = pd.DataFrame()
    
    try: df_evolucoes = limpar_dataframe(conn.read(worksheet="evolucao", ttl=0))
    except: df_evolucoes = pd.DataFrame()
    
    try: df_arquivo_morto = limpar_dataframe(conn.read(worksheet="arquivo_morto", ttl=0))
    except: df_arquivo_morto = pd.DataFrame()
    
    # Padronização de colunas para evitar erros de caixa (Maiúsculo/Minúsculo)
    for df in [df_alunos, df_financeiro, df_espera, df_precos, df_evolucoes, df_arquivo_morto]:
        if not df.empty:
            df.columns = df.columns.str.strip()
            
    conexao_ok = True
except Exception as e:
    st.error(f"Erro de Conexão: {e}")

dict_precos = {"1x semana": 180.0, "2x semana": 220.0, "3x semana": 300.0}
if not df_precos.empty and "Plano" in df_precos.columns and "Valor" in df_precos.columns:
    for _, r in df_precos.iterrows():
        dict_precos[str(r["Plano"]).strip()] = converter_para_float(r["Valor"])

# ==============================================================================
# 4. BARRA LATERAL E CONTROLO DE SESSÃO
# ==============================================================================
with st.sidebar:
    if os.path.exists("Highline Logo.png"):
        st.image("Highline Logo.png", use_container_width=True)
    else:
        st.markdown("<h2 style='text-align: center; color: white;'>📌 HIGHLINE</h2>", unsafe_allow_html=True)
    
    menu = st.radio("🔒 Menu de Navegação", [
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
    ])
    st.markdown("---")
    if conexao_ok: 
        st.success("🟢 Banco de Dados Online")
    else: 
        st.error("🔴 Banco de Dados Offline")

LISTA_QUEIXAS_PADRAO = [
    "Dor Lombar (Lombalgia)", "Hérnia de Disco / Protrusão", "Dor / Lesão nos Ombros", 
    "Dor Cervical (Cervicalgia)", "Dor / Lesão nos Joelhos", "Melhoria Postural Operacional", 
    "Pilates para Gestantes", "Pilates para Terceira Idade (Idosos)", "Condicionamento Físico Geral"
]

# ==============================================================================
# 5. EXECUÇÃO INTEGRAL DAS TELAS DO SISTEMA
# ==============================================================================

# --- TELA: AGENDA DE TREINOS ---
if menu == "📅 Agenda":
    st.title("📅 Agenda de Treinos Diária")
    hoje = datetime.now()
    
    if not df_alunos.empty and "Nascimento" in df_alunos.columns:
        niver = []
        for _, r in df_alunos.iterrows():
            if pd.notna(r["Nascimento"]):
                try:
                    dt_nasc = pd.to_datetime(str(r["Nascimento"]).strip(), dayfirst=True, errors='coerce')
                    if not pd.isna(dt_nasc) and dt_nasc.strftime("%m-%d") == hoje.strftime("%m-%d"):
                        niver.append(str(r["Nome"]))
                except: pass
        if niver: st.info(f"🎉 **Aniversariantes de Hoje:** {', '.join(niver)}! 🎂")

    # Mapeamento robusto incluindo indexação correta para Sexta-feira (4)
    dias_map = {0: ["SEG", "SEGUNDA"], 1: ["TER", "TERÇA"], 2: ["QUA", "QUARTA"], 3: ["QUI", "QUINTA"], 4: ["SEX", "SEXTA"], 5: ["SAB", "SÁBADO"], 6: ["DOM", "DOMINGO"]}
    busca_dias = dias_map.get(hoje.weekday(), [])
    
    col_status = [c for c in df_alunos.columns if c.lower() == "status"]
    if not df_alunos.empty and col_status:
        ativos = df_alunos[df_alunos[col_status[0]].astype(str).str.upper() == "ATIVO"]
        col_dias = [c for c in ativos.columns if c.lower() == "dias"]
        
        if col_dias:
            df_agenda = ativos[ativos[col_dias[0]].astype(str).str.upper().apply(lambda x: any(d in x for d in busca_dias))]
            if not df_agenda.empty:
                col_horario = [c for c in df_agenda.columns if c.lower() in ["horario", "horário"]]
                sort_col = col_horario[0] if col_horario else df_agenda.columns[0]
                df_agenda_ordenada = df_agenda.sort_values(by=sort_col)
                
                exibir_cols = [c for c in ["Horario", "Horário", "Nome", "Plano", "Dias", "Queixa"] if c in df_agenda_ordenada.columns]
                st.dataframe(df_agenda_ordenada[exibir_cols], use_container_width=True, hide_index=True)
            else: 
                st.warning("Nenhum aluno agendado para o dia de hoje.")
        else:
            st.error("Coluna 'Dias' não encontrada na tabela.")
    else:
        st.info("Nenhum aluno ativo encontrado para montagem da agenda hoje.")

# --- TELA: BASE DE ALUNOS ATIVOS ---
elif menu == "👥 Alunos":
    st.title("👥 Alteração Rápida e Gerenciamento de Alunos")
    
    col_status = [c for c in df_alunos.columns if c.lower() == "status"]
    if not df_alunos.empty and col_status:
        ativos = df_alunos[df_alunos[col_status[0]].astype(str).str.upper() == "ATIVO"]
        if not ativos.empty:
            st.metric("Total de Alunos Ativos", len(ativos))
            busca = st.text_input("🔍 Filtrar aluno por nome:")
            df_f = ativos[ativos["Nome"].astype(str).str.contains(busca, case=False, na=False)] if busca else ativos
            
            df_vis = df_f.copy()
            if "Valor" in df_vis.columns: df_vis["Valor"] = df_vis["Valor"].apply(formatar_brl)
            st.dataframe(df_vis, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            opcoes = ["-- Escolha um Aluno --"] + [f"{r['Nome']} (Reg: {i})" for i, r in ativos.iterrows()]
            selecionado = st.selectbox("Selecione um aluno ativo para alterar dados ou desativar:", opcoes)
            
            if selecionado != "-- Escolha um Aluno --":
                idx = int(selecionado.split("(Reg: ")[1].replace(")", ""))
                dados = df_alunos.loc[idx]
                
                with st.form(f"f_ed_{idx}"):
                    c1, c2, c3, c4 = st.columns(4)
                    plano_atual = dados.get("Plano", "1x semana")
                    lista_p = ["1x semana", "2x semana", "3x semana"]
                    idx_p = lista_p.index(plano_atual) if plano_atual in lista_p else 0
                    
                    novo_p = c1.selectbox("Novo Plano Contratado:", lista_p, index=idx_p)
                    novos_d = c2.text_input("Novos Dias de Aula (Ex: Ter/Qui):", value=str(dados.get("Dias", "")))
                    novo_h = c3.text_input("Novo Horário (Ex: 08:30):", value=str(dados.get("Horario", "")))
                    novo_val = c4.number_input("Confirmar Valor Mensal (R$):", value=converter_para_float(dados.get("Valor", 0.0)))
                    
                    q_at = str(dados.get("Queixa", ""))
                    st.markdown("### 🩺 Atualizar Anamnese: Queixas Principais e Sintomas (Jonathan)")
                    
                    ch1, ch2, ch3 = st.columns(3)
                    e_lom = ch1.checkbox("Dor Lombar (Lombalgia)", value="Dor Lombar" in q_at)
                    e_her = ch2.checkbox("Hérnia de Disco / Protrusão", value="Hérnia" in q_at)
                    e_omb = ch3.checkbox("Dor / Lesão nos Ombros", value="Ombros" in q_at)
                    
                    e_cev = ch1.checkbox("Dor Cervical (Cervicalgia)", value="Cervical" in q_at)
                    e_joe = ch2.checkbox("Dor / Lesão nos Joelhos", value="Joelhos" in q_at)
                    e_pos = ch3.checkbox("Melhoria Postural Operacional", value="Postural" in q_at)
                    
                    e_ges = ch1.checkbox("Pilates para Gestantes", value="Gestantes" in q_at)
                    e_ido = ch2.checkbox("Pilates para Terceira Idade (Idosos)", value="Idosos" in q_at)
                    e_con = ch3.checkbox("Condicionamento Físico Geral", value="Condicionamento" in q_at)
                    
                    e_extra = st.text_input("Outras Queixas Adicionais / Observações Clínicas:", value=" | ".join([t for t in q_at.split(" | ") if t not in LISTA_QUEIXAS_PADRAO]))
                    e_cond = st.text_area("Diretrizes de Conduta Específicas:", value=str(dados.get("Conduta", "")))
                    
                    col_b1, col_b2 = st.columns(2)
                    gravar = col_b1.form_submit_button("💾 Gravar Alterações")
                    arquivar = col_b2.form_submit_button("❌ Mover ao Arquivo Morto")
                    
                    if gravar:
                        queixas_novas = [t for t, m in [
                            ("Dor Lombar (Lombalgia)", e_lom), ("Hérnia de Disco / Protrusão", e_her), 
                            ("Dor / Lesão nos Ombros", e_omb), ("Dor Cervical (Cervicalgia)", e_cev),
                            ("Dor / Lesão nos Joelhos", e_joe), ("Melhoria Postural Operacional", e_pos),
                            ("Pilates para Gestantes", e_ges), ("Pilates para Terceira Idade (Idosos)", e_ido),
                            ("Condicionamento Físico Geral", e_con)
                        ] if m]
                        if e_extra.strip(): queixas_novas.append(e_extra.strip())
                        
                        df_alunos.at[idx, "Plano"] = novo_p
                        df_alunos.at[idx, "Valor"] = novo_val
                        df_alunos.at[idx, "Dias"] = novos_d
                        df_alunos.at[idx, "Horario"] = novo_h
                        df_alunos.at[idx, "Queixa"] = " | ".join(queixas_novas)
                        df_alunos.at[idx, "Conduta"] = e_cond
                        
                        conn.update(worksheet="alunos", data=df_alunos)
                        st.success("Dados do aluno atualizados com sucesso!")
                        st.cache_data.clear()
                        st.rerun()
                        
                    if arquivar:
                        df_alunos.at[idx, col_status[0]] = "Inativo"
                        row_arquivada = pd.DataFrame([df_alunos.loc[idx].to_dict()])
                        df_arquivo_morto = pd.concat([df_arquivo_morto, row_arquivada], ignore_index=True)
                        
                        conn.update(worksheet="alunos", data=df_alunos)
                        conn.update(worksheet="arquivo_morto", data=df_arquivo_morto)
                        st.warning("Aluno movido para o arquivo morto.")
                        st.cache_data.clear()
                        st.rerun()
        else:
            st.info("Nenhum aluno ativo encontrado.")
    else:
        st.error("A tabela de alunos está vazia ou inacessível no momento.")

# --- TELA: CADASTRO E DISPONIBILIDADE (MÁXIMO 3 ALUNOS) ---
elif menu == "📝 Cadastro":
    st.title("📝 Cadastro e Validação de Vagas (Máx. 3 por Horário)")
    
    st.markdown("### 🔍 Passo 1: Verificar Disponibilidade de Horário")
    cx1, cx2 = st.columns(2)
    dia_teste = cx1.selectbox("Selecione o Dia da Semana Desejado:", ["SEG", "TER", "QUA", "QUI", "SEX", "SAB"])
    horario_teste = cx2.text_input("Digite o Horário Desejado (Ex: 08:30):", value="08:30")
    
    vagas_ocupadas = 0
    if not df_alunos.empty and "Dias" in df_alunos.columns and "Horario" in df_alunos.columns:
        col_status = [c for c in df_alunos.columns if c.lower() == "status"]
        ativos = df_alunos[df_alunos[col_status[0]].astype(str).str.upper() == "ATIVO"] if col_status else df_alunos
        filtro_vaga = ativos[(ativos["Dias"].astype(str).str.upper().str.contains(dia_teste)) & (ativos["Horario"].astype(str).str.strip() == horario_teste.strip())]
        vagas_ocupadas = len(filtro_vaga)
        
    vagas_restantes = 3 - vagas_ocupadas
    
    if vagas_restantes <= 0:
        st.error(f"❌ Horário Esgotado! Já existem {vagas_ocupadas} alunos ativos nesse horário às {dia_teste}s.")
    else:
        st.success(f"🟢 Horário Disponível! ({vagas_restantes} de 3 vagas restantes).")
        
        st.markdown("---")
        st.markdown("### 2. Formulário de Cadastro Completo")
        with st.form("f_cadastro_completo", clear_on_submit=True):
            st.markdown("#### Dados Pessoais e de Contrato")
            cc1, cc2 = st.columns(2)
            plano = cc1.selectbox("Plano Contratado:", ["1x semana", "2x semana", "3x semana"])
            valor = cc2.number_input("Valor Combinado Mensal (R$):", value=float(dict_precos.get(plano, 180.0)))
            
            c1, c2, c3 = st.columns(3)
            nome = c1.text_input("Nome Completo:")
            tel = c2.text_input("WhatsApp com DDD:")
            nasc = c3.text_input("Nascimento (DD/MM/AAAA):")
            
            c4, c5, c6 = st.columns(3)
            cpf = c4.text_input("CPF:")
            genero = c5.selectbox("Gênero:", ["Feminino", "Masculino", "Outro"])
            venc = c6.number_input("Dia do Vencimento da Mensalidade:", min_value=1, max_value=31, value=10)
            
            st.markdown("#### Informações de Endereço")
            ca1, ca2, ca3 = st.columns(3)
            endereco = ca1.text_input("Endereço (Rua, Número):")
            bairro = ca2.text_input("Bairro:")
            inicio = ca3.text_input("Data de Início das Aulas (DD/MM/AAAA):", value=datetime.now().strftime("%d/%m/%Y"))
            
            st.markdown("#### 🩺 Ficha Clínica / Queixas Principais (Jonathan)")
            ch1, ch2, ch3 = st.columns(3)
            q_lom = ch1.checkbox("Dor Lombar (Lombalgia)")
            q_her = ch2.checkbox("Hérnia de Disco / Protrusão")
            q_omb = ch3.checkbox("Dor / Lesão nos Ombros")
            q_cev = ch1.checkbox("Dor Cervical (Cervicalgia)")
            q_joe = ch2.checkbox("Dor / Lesão nos Joelhos")
            q_pos = ch3.checkbox("Melhoria Postural Operacional")
            q_ges = ch1.checkbox("Pilates para Gestantes")
            q_ido = ch2.checkbox("Pilates para Terceira Idade (Idosos)")
            q_con = ch3.checkbox("Condicionamento Físico Geral")
            
            outras_q = st.text_input("Outras Queixas Clínicas Adicionais:")
            conduta_inicial = st.text_area("Diretrizes Iniciais de Conduta:")
            
            if st.form_submit_button("💾 Salvar Cadastro no Banco de Dados"):
                if not nome.strip() or not tel.strip():
                    st.error("Erro: Nome Completo e WhatsApp são campos obrigatórios!")
                else:
                    q_list = [t for t, m in [
                        ("Dor Lombar (Lombalgia)", q_lom), ("Hérnia de Disco / Protrusão", q_her), 
                        ("Dor / Lesão nos Ombros", q_omb), ("Dor Cervical (Cervicalgia)", q_cev),
                        ("Dor / Lesão nos Joelhos", q_joe), ("Melhoria Postural Operacional", q_pos),
                        ("Pilates para Gestantes", q_ges), ("Pilates para Terceira Idade (Idosos)", q_ido),
                        ("Condicionamento Físico Geral", q_con)
                    ] if m]
                    if outras_q.strip(): q_list.append(outras_q.strip())
                    
                    nova_linha = {
                        "Nome": nome.strip(), "Telefone": tel.strip(), "Nascimento": nasc.strip(),
                        "CPF": cpf.strip(), "Genero": genero, "Vencimento": venc, "Endereco": endereco.strip(),
                        "Bairro": bairro.strip(), "Inicio_Aulas": inicio.strip(), "Plano": plano,
                        "Valor": valor, "Status": "Ativo", "Dias": dia_teste, "Horario": horario_teste.strip(),
                        "Queixa": " | ".join(q_list), "Conduta": conduta_inicial.strip()
                    }
                    
                    df_alunos = pd.concat([df_alunos, pd.DataFrame([nova_linha])], ignore_index=True)
                    conn.update(worksheet="alunos", data=df_alunos)
                    st.success(f"Aluno {nome} cadastrado com sucesso para {dia_teste} às {horario_teste}!")
                    st.cache_data.clear()
                    st.rerun()

# --- TELA: EVOLUÇÃO CLÍNICA ---
elif menu == "📈 Evolução":
    st.title("📈 Registro de Evolução Clínica")
    
    nomes_disponiveis = sorted(list(df_alunos["Nome"].dropna().unique())) if not df_alunos.empty else []
    
    with st.form("f_evolucao", clear_on_submit=True):
        aluno_sel = st.selectbox("Selecione o Aluno para registrar evolução:", ["-- Escolha --"] + nomes_disponiveis)
        texto_evolucao = st.text_area("Descreva a Evolução Clínico-Funcional:")
        
        if st.form_submit_button("💾 Gravar Evolução"):
            if aluno_sel == "-- Escolha --" or not texto_evolucao.strip():
                st.error("Erro: Selecione o Aluno e preencha o campo de texto.")
            else:
                nova_ev = {
                    "Data": datetime.now().strftime("%d/%m/%Y"),
                    "Nome do Aluno": aluno_sel,
                    "Evolução": texto_evolucao.strip()
                }
                df_evolucoes = pd.concat([df_evolucoes, pd.DataFrame([nova_ev])], ignore_index=True)
                conn.update(worksheet="evolucao", data=df_evolucoes)
                st.success("Evolução clínica gravada com sucesso!")
                st.cache_data.clear()
                st.rerun()
                
    st.markdown("---")
    st.subheader("Histórico Recente de Evoluções")
    if not df_evolucoes.empty:
        st.dataframe(df_evolucoes.sort_index(ascending=False), use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum histórico registrado até o momento.")

# --- TELA: LISTA DE ESPERA ---
elif menu == "⏳ Espera":
    st.title("⏳ Gerenciamento de Lista de Espera")
    
    if not df_espera.empty:
        st.dataframe(df_espera, use_container_width=True, hide_index=True)
    else:
        st.info("A lista de espera está vazia no momento.")
        
    with st.form("f_lista_espera", clear_on_submit=True):
        st.markdown("### Adicionar Novo Interessado")
        n_esp = st.text_input("Nome do Interessado:")
        t_esp = st.text_input("Telefone de Contato:")
        q_esp = st.text_input("Objetivo / Queixa Principal:")
        
        if st.form_submit_button("➕ Incluir na Lista"):
            if not n_esp.strip():
                st.error("O campo Nome é obrigatório.")
            else:
                nova_espera = {"Nome": n_esp.strip(), "Telefone": t_esp.strip(), "Queixa": q_esp.strip()}
                df_espera = pd.concat([df_espera, pd.DataFrame([nova_espera])], ignore_index=True)
                conn.update(worksheet="espera", data=df_espera)
                st.success("Interessado adicionado com sucesso.")
                st.cache_data.clear()
                st.rerun()

# --- TELA: FINANCEIRO ---
elif menu == "💰 Financeiro":
    st.title("💰 Painel de Controlo Financeiro")
    
    tot_recebido = 0.0
    if not df_financeiro.empty and "Status" in df_financeiro.columns:
        tot_recebido = df_financeiro[df_financeiro["Status"].astype(str).str.upper() == "PAGO"]["Valor"].apply(converter_para_float).sum()
        
    st.metric("Total de Receitas Registradas (PAGO)", formatar_brl(tot_recebido))
    
    col_status = [c for c in df_alunos.columns if c.lower() == "status"]
    if not df_alunos.empty and col_status:
        ativos = df_alunos[df_alunos[col_status[0]].astype(str).str.upper() == "ATIVO"]
        lista_pagamento = [f"{r['Nome']} | Valor: {formatar_brl(r.get('Valor', 0))}" for _, r in ativos.iterrows()]
        
        if lista_pagamento:
            st.markdown("### Registrar Baixa de Pagamento")
            selecionado_pag = st.selectbox("Selecione o Aluno para dar baixa na mensalidade:", lista_pagamento)
            
            if st.button("Confirmar Recebimento via PIX"):
                nome_aluno = selecionado_pag.split(" | ")[0]
                aluno_row = ativos[ativos["Nome"] == nome_aluno].iloc[0]
                valor_pago = converter_para_float(aluno_row.get("Valor", 0.0))
                
                novo_lancamento = {
                    "Aluno": nome_aluno,
                    "Valor": valor_pago,
                    "Data": datetime.now().strftime("%d/%m/%Y"),
                    "Forma": "PIX",
                    "Status": "PAGO"
                }
                df_financeiro = pd.concat([df_financeiro, pd.DataFrame([novo_lancamento])], ignore_index=True)
                conn.update(worksheet="financeiro", data=df_financeiro)
                st.success(f"Pagamento de {nome_aluno} processado com sucesso!")
                st.cache_data.clear()
                st.rerun()
                
    st.markdown("---")
    st.subheader("Fluxo de Caixa de Mensalidades")
    if not df_financeiro.empty:
        df_fin_vis = df_financeiro.copy()
        if "Valor" in df_fin_vis.columns: df_fin_vis["Valor"] = df_fin_vis["Valor"].apply(formatar_brl)
        st.dataframe(df_fin_vis.sort_index(ascending=False), use_container_width=True, hide_index=True)

# --- TELA: PERFIL / INDICADORES ---
elif menu == "👤 Perfil":
    st.title("👤 Indicadores Estratégicos Highline Studio")
    
    col_status = [c for c in df_alunos.columns if c.lower() == "status"]
    if not df_alunos.empty and col_status:
        ativos = df_alunos[df_alunos[col_status[0]].astype(str).str.upper() == "ATIVO"]
        c1, c2 = st.columns(2)
        c1.metric("Matrículas Ativas", len(ativos))
        if "Valor" in ativos.columns:
            c2.metric("Faturamento Mensal Estimado", formatar_brl(ativos["Valor"].apply(converter_para_float).sum()))
    else:
        st.info("Sem métricas consolidadas.")

# --- TELA: CONFIGURAÇÃO DE PREÇOS ---
elif menu == "⚙️ Preços":
    st.title("⚙️ Tabela Padrão de Preços dos Planos")
    
    with st.form("f_tabela_precos"):
        p1 = st.number_input("Valor Padrão Plano 1x semana (R$):", value=dict_precos.get("1x semana", 180.0))
        p2 = st.number_input("Valor Padrão Plano 2x semana (R$):", value=dict_precos.get("2x semana", 220.0))
        p3 = st.number_input("Valor Padrão Plano 3x semana (R$):", value=dict_precos.get("3x semana", 300.0))
        
        if st.form_submit_button("⚙️ Atualizar Tabela de Preços"):
            novos_precos_df = pd.DataFrame([
                {"Plano": "1x semana", "Valor": p1},
                {"Plano": "2x semana", "Valor": p2},
                {"Plano": "3x semana", "Valor": p3}
            ])
            conn.update(worksheet="precos", data=novos_precos_df)
            st.success("Tabela de preços base atualizada globalmente!")
            st.cache_data.clear()
            st.rerun()

# --- TELA: ARQUIVO MORTO ---
elif menu == "📁 Arquivo Morto":
    st.title("📁 Alunos Inativos / Arquivo Morto")
    if not df_arquivo_morto.empty:
        st.dataframe(df_arquivo_morto, use_container_width=True, hide_index=True)
    else:
        st.info("O Arquivo Morto está completamente limpo.")

# --- TELA: IMPRESSÃO DE PRONTUÁRIO CLÍNICO ---
elif menu == "🖨️ Imprimir Prontuário":
    st.title("🖨️ Visualização e Emissão de Prontuário Clínico")
    
    if not df_alunos.empty:
        opcao_prontuario = ["-- Escolha --"] + sorted(list(df_alunos["Nome"].dropna().unique()))
        sel_aluno = st.selectbox("Selecione o Aluno para gerar Prontuário:", opcao_prontuario)
        
        if sel_aluno != "-- Escolha --":
            row = df_alunos[df_alunos["Nome"] == sel_aluno].iloc[0]
            idade = calcular_idade(row.get("Nascimento", ""))
            
            q_p = str(row.get('Queixa', ''))
            q_html = "Nenhuma queixa registrada." if q_p.lower() == "nan" or not q_p.strip() else q_p.replace(' | ', '<br>● ')
            
            c_p = str(row.get('Conduta', ''))
            c_html = "Nenhuma conduta ou diretriz estipulada." if c_p.lower() == "nan" or not c_p.strip() else c_p

            html_prontuario_final = f"""
            <div class="prontuario-card">
                <div class="prontuario-header">
                    <h2>HIGHLINE STUDIO PILATES</h2>
                    <p style="font-size:16px; font-weight:bold; color:#2E5A44;">Ficha Clínico-Funcional & Anamnese Estruturada</p>
                </div>
                
                <div class="prontuario-secao">1. DADOS IDENTIFICATÓRIOS DO ALUNO</div>
                <table class="tabela-prontuario">
                    <tr>
                        <td><strong>Nome Completo:</strong> {row.get('Nome', '-')}</td>
                        <td><strong>Gênero:</strong> {row.get('Genero', '-')}</td>
                    </tr>
                    <tr>
                        <td><strong>Nascimento:</strong> {row.get('Nascimento', '-')} ({f"{idade} anos" if idade else "-"})</td>
                        <td><strong>CPF:</strong> {row.get('CPF', '-')}</td>
                    </tr>
                    <tr>
                        <td><strong>WhatsApp/Contato:</strong> {row.get('Telefone', '-')}</td>
                        <td><strong>Início das Atividades:</strong> {row.get('Inicio_Aulas', '-')}</td>
                    </tr>
                    <tr>
                        <td colspan="2"><strong>Endereço Residencial:</strong> {row.get('Endereco', '-')} | <strong>Bairro:</strong> {row.get('Bairro', '-')}</td>
                    </tr>
                </table>
                
                <div class="prontuario-secao">2. QUADRO CLÍNICO E QUEIXAS MAPEADAS</div>
                <p style="color:#000000 !important; font-size:15px; margin-top:12px; line-height:1.6; padding-left:5px;">
                    ● {q_html}
                </p>
                
                <div class="prontuario-secao">3. DIRETRIZES TERAPÊUTICAS E CONDUTA RECOMENDADA</div>
                <p style="color:#000000 !important; font-size:15px; margin-top:12px; line-height:1.6; padding-left:5px; white-space: pre-line;">
                    {c_html}
                </p>
            </div>
            """
            
            st.markdown(html_prontuario_final, unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("""
                <button class="no-print" onclick="window.print()" style="
                    padding: 12px 24px; 
                    background-color: #2E5A44; 
                    color: white; 
                    border: none; 
                    border-radius: 6px; 
                    font-weight: bold;
                    cursor: pointer;
                    box-shadow: 0px 2px 5px rgba(0,0,0,0.2);
                ">🖨️ Executar Impressão Física / Salvar em PDF</button>
            """, unsafe_allow_html=True)
    else:
        st.warning("Não há dados cadastrados suficientes para gerar prontuários.")
