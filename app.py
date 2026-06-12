import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime

# ==============================================================================
# 1. CONFIGURAÇÕES VISUAIS E IDENTIDADE VISUAL
# ==============================================================================
st.set_page_config(page_title="Highline Management System", layout="wide", page_icon="🏋️‍♂️")

# Injeção de CSS para o menu lateral verde e comportamento de impressão
st.markdown("""
    <style>
        [data-testid="stSidebar"] { background-color: #2E5A44 !important; }
        [data-testid="stSidebar"] * { color: white !important; }
        .stRadio input[type="radio"]:checked + div { color: #FFD700 !important; font-weight: bold !important; }
        
        @media print {
            [data-testid="stSidebar"], button, .no-print, header, [data-testid="stHeader"] { 
                display: none !important; 
            }
            body { background: white !important; }
        }
    </style>
""", unsafe_allow_html=True)

# --- MENU DE NAVEGAÇÃO LATERAL (CORREÇÃO DO NAMEERROR NA LINHA 174) ---
with st.sidebar:
    st.markdown("## Highline Studio")
    st.markdown("---")
    menu = st.radio(
        "Menu de Navegação",
        ["📅 Agenda", "👥 Alunos", "📝 Cadastro", "📈 Evolução", "⏳ Espera", "💰 Financeiro", "👤 Perfil", "⚙️ Preços", "📁 Arquivo Morto", "🖨️ Imprimir Prontuário"]
    )
    st.markdown("---")
    st.markdown("🟢 **Banco de Dados Online**")

# Estilos CSS estruturados para a renderização visual do Prontuário Clínico
ESTILO_PRONTUARIO_HTML = """
<style>
    .prontuario-card {
        background-color: #ffffff !important;
        color: #000000 !important;
        padding: 25px;
        border: 3px solid #2E5A44;
        border-radius: 10px;
        font-family: 'Arial', sans-serif;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.1);
        margin: 10px;
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
        font-size: 14px;
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
</style>
"""

# ==============================================================================
# 2. MECANISMOS DE TRATAMENTO DE DADOS (PARSERS E SANITIZADORES)
# ==============================================================================
def limpar_dataframe(df):
    if df is None: return pd.DataFrame()
    try:
        df = df.loc[:, ~df.columns.astype(str).str.contains('^Unnamed')]
        df.columns = df.columns.str.strip()
        df = df.fillna("")
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
        v = str(valor).replace("R$", "").replace(" ", "").replace(".", "")
        if "," in v: v = v.replace(",", ".")
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
# 3. CONEXÃO DIRETA COM GOOGLE SHEETS
# ==============================================================================
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_alunos = limpar_dataframe(conn.read(worksheet="alunos", ttl=0))
    df_financeiro = limpar_dataframe(conn.read(worksheet="financeiro", ttl=0))
    df_espera = limpar_dataframe(conn.read(worksheet="espera", ttl=0))
    df_precos = limpar_dataframe(conn.read(worksheet="precos", ttl=0))
    df_evolucoes = limpar_dataframe(conn.read(worksheet="evolucao", ttl=0))
    df_arquivo_morto = limpar_dataframe(conn.read(worksheet="arquivo_morto", ttl=0))
except Exception as e:
    st.error(f"Erro Crítico de Inicialização do Banco de Dados: {e}")
    st.stop()

# Mapeamento Base de Preços
dict_precos = {"1x semana": 180.0, "2x semana": 220.0, "3x semana": 300.0}
if not df_precos.empty and "Plano" in df_precos.columns and "Valor" in df_precos.columns:
    for _, r in df_precos.iterrows():
        dict_precos[str(r["Plano"]).strip()] = converter_para_float(r["Valor"])

LISTA_QUEIXAS_PADRAO = [
    "Dor Lombar (Lombalgia)", "Hérnia de Disco / Protrusão", "Dor / Lesão nos Ombros", 
    "Dor Cervical (Cervicalgia)", "Dor / Lesão nos Joelhos", "Melhoria Postural Operacional", 
    "Pilates para Gestantes", "Pilates para Terceira Idade (Idosos)", "Condicionamento Físico Geral"
]

# ==============================================================================
# 4. DIRECIONAMENTO DE TELAS E REGRAS DE NEGÓCIO
# ==============================================================================

# --- TELA: AGENDA ---
if menu == "📅 Agenda":
    st.title("📅 Agenda de Treinos Diária")
    hoje = datetime.now()
    
    # Validação de aniversariantes do dia
    if not df_alunos.empty and "Nascimento" in df_alunos.columns:
        niver = []
        for _, r in df_alunos.iterrows():
            val_nasc = str(r["Nascimento"]).strip()
            if "/" in val_nasc:
                partes = val_nasc.split("/")
                try:
                    if int(partes[0]) == hoje.day and int(partes[1]) == hoje.month:
                        niver.append(str(r["Nome"]))
                except: pass
        if niver: 
            st.markdown(f"""<div style='background-color:#FFD700; padding:15px; border-radius:5px; color:black; font-weight:bold; margin-bottom:15px;'>
                🎉 Aniversariantes de Hoje ({hoje.strftime('%d/%m')}): {', '.join(niver)}! 🎂
            </div>""", unsafe_allow_html=True)

    dias_map = {0: ["SEG", "SEGUNDA"], 1: ["TER", "TERÇA"], 2: ["QUA", "QUARTA"], 3: ["QUI", "QUINTA"], 4: ["SEX", "SEXTA"], 5: ["SAB", "SÁBADO"], 6: ["DOM", "DOMINGO"]}
    busca_dias = dias_map.get(hoje.weekday(), [])
    
    if not df_alunos.empty and "Status" in df_alunos.columns:
        ativos = df_alunos[df_alunos["Status"].astype(str).str.upper() == "ATIVO"]
        if "Dias" in ativos.columns:
            df_agenda = ativos[ativos["Dias"].astype(str).str.upper().apply(lambda x: any(d in x for d in busca_dias))]
            if not df_agenda.empty:
                sort_col = "Horario" if "Horario" in df_agenda.columns else df_agenda.columns[0]
                df_agenda_ordenada = df_agenda.sort_values(by=sort_col)
                exibir_cols = [c for c in ["Horario", "Nome", "Plano", "Dias", "Queixa"] if c in df_agenda_ordenada.columns]
                st.dataframe(df_agenda_ordenada[exibir_cols], use_container_width=True, hide_index=True)
            else: 
                st.info("Nenhum aluno agendado ou ativo encontrado para a escala de hoje.")
        else:
            st.error("Coluna 'Dias' não foi detectada na planilha.")

# --- TELA: GERENCIAMENTO DE ALUNOS ---
elif menu == "👥 Alunos":
    st.title("👥 Alteração Rápida e Gerenciamento de Alunos")
    
    if not df_alunos.empty and "Status" in df_alunos.columns:
        ativos = df_alunos[df_alunos["Status"].astype(str).str.upper() == "ATIVO"]
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
                    c1, c2 = st.columns(2)
                    lista_p = ["1x semana", "2x semana", "3x semana"]
                    plano_atual = dados.get("Plano", "1x semana")
                    idx_p = lista_p.index(plano_atual) if plano_atual in lista_p else 0
                    
                    novo_p = c1.selectbox("Novo Plano Contratado:", lista_p, index=idx_p)
                    novos_d = c2.text_input("Novos Dias de Aula (Ex: SEG/QUA):", value=str(dados.get("Dias", "")))
                    
                    c3, c4 = st.columns(2)
                    valor_atual_float = converter_para_float(dados.get("Valor", 0.0))
                    novo_val = c3.number_input("Confirmar Valor Mensal (R$):", value=valor_atual_float, step=10.0)
                    novo_h = c4.text_input("Novo Horário (Ex: 08:30):", value=str(dados.get("Horario", "")))
                    
                    q_at = str(dados.get("Queixa", ""))
                    st.markdown("### 🩺 Atualizar Anamnese: Queixas Principais e Sintomas")
                    
                    ch1, ch2, ch3 = st.columns(3)
                    e_lom = ch1.checkbox("Dor Lombar (Lombalgia)", value="Lombar" in q_at or "lombar" in q_at.lower())
                    e_her = ch2.checkbox("Hérnia de Disco / Protrusão", value="Hérnia" in q_at or "hernia" in q_at.lower())
                    e_omb = ch3.checkbox("Dor / Lesão nos Ombros", value="Ombros" in q_at or "ombro" in q_at.lower())
                    e_cev = ch1.checkbox("Dor Cervical (Cervicalgia)", value="Cervical" in q_at or "cervical" in q_at.lower())
                    e_joe = ch2.checkbox("Dor / Lesão nos Joelhos", value="Joelhos" in q_at or "joelho" in q_at.lower())
                    e_pos = ch3.checkbox("Melhoria Postural Operacional", value="Postural" in q_at or "postural" in q_at.lower())
                    e_ges = ch1.checkbox("Pilates para Gestantes", value="Gestantes" in q_at or "gestante" in q_at.lower())
                    e_ido = ch2.checkbox("Pilates para Terceira Idade (Idosos)", value="Idosos" in q_at or "idoso" in q_at.lower())
                    e_con = ch3.checkbox("Condicionamento Físico Geral", value="Condicionamento" in q_at or "condicionamento" in q_at.lower())
                    
                    e_extra = st.text_input("Outras Queixas Adicionais / Observações Clínicas:", value=" | ".join([t for t in q_at.split(" | ") if t not in LISTA_QUEIXAS_PADRAO and t.strip() != "nan"]))
                    
                    conduta_atual = str(dados.get("Conduta", ""))
                    if conduta_atual.lower() == "nan": conduta_atual = ""
                    e_cond = st.text_area("Diretrizes de Conduta Específicas:", value=conduta_atual)
                    
                    col_b1, col_b2 = st.columns(2)
                    gravar = col_b1.form_submit_button("💾 Gravar Alterações")
                    arquivar = col_b2.form_submit_button("❌ Mover ao Arquivo Morto")
                    
                    # PROCESSAMENTO DO FORMULÁRIO (BLINDAGEM ANTI-ERRO DE API)
                    if gravar:
                        queixas_novas = [t for t, m in [
                            ("Dor Lombar (Lombalgia)", e_lom), ("Hérnia de Disco / Protrusão", e_her), 
                            ("Dor / Lesão nos Ombros", e_omb), ("Dor Cervical (Cervicalgia)", e_cev),
                            ("Dor / Lesão nos Joelhos", e_joe), ("Melhoria Postural Operacional", e_pos),
                            ("Pilates para Gestantes", e_ges), ("Pilates para Terceira Idade (Idosos)", e_ido),
                            ("Condicionamento Físico Geral", e_con)
                        ] if m]
                        if e_extra.strip() and e_extra.strip().lower() != "nan": 
                            queixas_novas.append(e_extra.strip())
                        
                        df_alunos.at[idx, "Plano"] = novo_p
                        df_alunos.at[idx, "Valor"] = float(novo_val)
                        df_alunos.at[idx, "Dias"] = novos_d.upper()
                        df_alunos.at[idx, "Horario"] = novo_h
                        df_alunos.at[idx, "Queixa"] = " | ".join(queixas_novas) if queixas_novas else ""
                        df_alunos.at[idx, "Conduta"] = e_cond.strip()
                        
                        # Higienização completa da tabela para evitar gspread APIError 400
                        df_alunos_salvar = df_alunos.fillna("").astype(str).replace("nan", "")
                        df_alunos_salvar.at[idx, "Valor"] = str(float(novo_val))
                        
                        conn.update(worksheet="alunos", data=df_alunos_salvar)
                        st.success("Cadastro e anamnese atualizados com sucesso!")
                        st.cache_data.clear()
                        st.rerun()
                        
                    if arquivar:
                        df_alunos.at[idx, "Status"] = "Inativo"
                        row_arquivada = pd.DataFrame([df_alunos.loc[idx].to_dict()])
                        
                        if df_arquivo_morto.empty:
                            df_arquivo_morto = row_arquivada
                        else:
                            df_arquivo_morto = pd.concat([df_arquivo_morto, row_arquivada], ignore_index=True)
                        
                        df_alunos_salvar = df_alunos.fillna("").astype(str).replace("nan", "")
                        df_morto_salvar = df_arquivo_morto.fillna("").astype(str).replace("nan", "")
                        
                        conn.update(worksheet="alunos", data=df_alunos_salvar)
                        conn.update(worksheet="arquivo_morto", data=df_morto_salvar)
                        st.warning("Aluno movido para o arquivo morto.")
                        st.cache_data.clear()
                        st.rerun()
        else:
            st.info("Nenhum aluno ativo mapeado.")

# --- TELA: CADASTRO COMPLETO ---
elif menu == "📝 Cadastro":
    st.title("📝 Cadastro e Verificação Dinâmica de Vagas")
    st.markdown("### 🔍 Passo 1: Disponibilidade de Grade (Máx 3 por Horário)")
    horario_teste = st.text_input("Horário Desejado (Ex: 08:30):", value="08:30")
    
    chx1, chx2, chx3, chx4, chx5, chx6 = st.columns(6)
    d_seg = chx1.checkbox("SEG")
    d_ter = chx2.checkbox("TER")
    d_qua = chx3.checkbox("QUA")
    d_qui = chx4.checkbox("QUI")
    d_sex = chx5.checkbox("SEX")
    d_sab = chx6.checkbox("SAB")
    
    dias_sel = [d for d, m in [("SEG", d_seg), ("TER", d_ter), ("QUA", d_qua), ("QUI", d_qui), ("SEX", d_sex), ("SAB", d_sab)] if m]
    
    bloqueado = False
    if dias_sel:
        for d in dias_sel:
            vagas = 0
            if not df_alunos.empty and "Dias" in df_alunos.columns and "Horario" in df_alunos.columns:
                ativos = df_alunos[df_alunos["Status"].astype(str).str.upper() == "ATIVO"]
                filtro = ativos[(ativos["Dias"].astype(str).str.upper().str.contains(d)) & (ativos["Horario"].astype(str).str.strip() == horario_teste.strip())]
                vagas = len(filtro)
            
            restantes = 3 - vagas
            if restantes <= 0:
                st.error(f"❌ Horário Esgotado na {d} às {horario_teste}! ({vagas}/3 preenchidas).")
                bloqueado = True
            else:
                st.success(f"🟢 {d} às {horario_teste} disponível ({restantes} vagas livres).")
                
    st.markdown("---")
    st.markdown("### 2. Formulário de Cadastro")
    with st.form("f_cadastro_global", clear_on_submit=True):
        cc1, cc2 = st.columns(2)
        plano = cc1.selectbox("Plano Contratado:", ["1x semana", "2x semana", "3x semana"])
        valor = cc2.number_input("Valor Mensal Combinado (R$):", value=float(dict_precos.get(plano, 180.0)))
        
        c1, c2, c3 = st.columns(3)
        nome = c1.text_input("Nome Completo:")
        tel = c2.text_input("WhatsApp com DDD:")
        nasc = c3.text_input("Nascimento (DD/MM/AAAA):")
        
        c4, c5, c6 = st.columns(3)
        cpf = c4.text_input("CPF:")
        genero = c5.selectbox("Gênero:", ["Feminino", "Masculino", "Outro"])
        venc = c6.number_input("Vencimento (Dia):", min_value=1, max_value=31, value=10)
        
        ca1, ca2, ca3 = st.columns(3)
        endereco = ca1.text_input("Endereço:")
        bairro = ca2.text_input("Bairro:")
        inicio = ca3.text_input("Data de Início:", value=datetime.now().strftime("%d/%m/%Y"))
        
        conduta_inicial = st.text_area("Diretrizes de Conduta Iniciais:")
        
        if st.form_submit_button("💾 Salvar Novo Aluno"):
            if not nome.strip() or bloqueado:
                st.error("Verifique se o nome foi preenchido ou se a grade está bloqueada.")
            else:
                nova_linha = {
                    "Nome": nome.strip(), "Telefone": tel.strip(), "Nascimento": nasc.strip(),
                    "CPF": cpf.strip(), "Genero": genero, "Vencimento": venc, "Endereco": endereco.strip(),
                    "Bairro": bairro.strip(), "Inicio_Aulas": inicio.strip(), "Plano": plano,
                    "Valor": valor, "Status": "Ativo", "Dias": "/".join(dias_sel), "Horario": horario_teste.strip(),
                    "Queixa": "", "Conduta": conduta_inicial.strip()
                }
                df_alunos = pd.concat([df_alunos, pd.DataFrame([nova_linha])], ignore_index=True)
                conn.update(worksheet="alunos", data=df_alunos.fillna("").astype(str))
                st.success("Aluno registrado com sucesso!")
                st.cache_data.clear()
                st.rerun()

# --- TELA: EVOLUÇÃO ---
elif menu == "📈 Evolução":
    st.title("📈 Registro de Evolução Clínico-Funcional")
    nomes_disponiveis = sorted(list(df_alunos["Nome"].dropna().unique())) if not df_alunos.empty else []
    
    with st.form("f_ev_clinica", clear_on_submit=True):
        aluno_sel = st.selectbox("Selecione o Aluno:", ["-- Escolha --"] + nomes_disponiveis)
        texto_evolucao = st.text_area("Descrição da Evolução:")
        
        if st.form_submit_button("💾 Gravar Histórico"):
            if aluno_sel == "-- Escolha --" or not texto_evolucao.strip():
                st.error("Preencha todos os campos do formulário.")
            else:
                nova_ev = {"Data": datetime.now().strftime("%d/%m/%Y"), "Nome do Aluno": aluno_sel, "Evolução": texto_evolucao.strip()}
                df_evolucoes = pd.concat([df_evolucoes, pd.DataFrame([nova_ev])], ignore_index=True)
                conn.update(worksheet="evolucao", data=df_evolucoes.fillna("").astype(str))
                st.success("Evolução armazenada!")
                st.cache_data.clear()
                st.rerun()
    st.markdown("---")
    if not df_evolucoes.empty:
        st.dataframe(df_evolucoes.sort_index(ascending=False), use_container_width=True, hide_index=True)

# --- TELA: LISTA DE ESPERA ---
elif menu == "⏳ Espera":
    st.title("⏳ Fila de Espera Dinâmica")
    if not df_espera.empty:
        st.dataframe(df_espera, use_container_width=True, hide_index=True)
        
    with st.form("f_lista_esp", clear_on_submit=True):
        n_esp = st.text_input("Nome do Interessado:")
        t_esp = st.text_input("Telefone:")
        d_esp = st.text_input("Dias de Preferência:")
        h_esp = st.text_input("Horário de Preferência:")
        
        if st.form_submit_button("➕ Adicionar à Espera"):
            if n_esp.strip():
                nova_esp = {"Nome": n_esp.strip(), "Telefone": t_esp.strip(), "Dia Preferencia": d_esp.strip().upper(), "Hora Preferencia": h_esp.strip()}
                df_espera = pd.concat([df_espera, pd.DataFrame([nova_esp])], ignore_index=True)
                conn.update(worksheet="espera", data=df_espera.fillna("").astype(str))
                st.success("Adicionado com sucesso!")
                st.cache_data.clear()
                st.rerun()

# --- TELA: FINANCEIRO ---
elif menu == "💰 Financeiro":
    st.title("💰 Painel Financeiro Integrado")
    tot_recebido = 0.0
    if not df_financeiro.empty and "Status" in df_financeiro.columns:
        tot_recebido = df_financeiro[df_financeiro["Status"].astype(str).str.upper() == "PAGO"]["Valor"].apply(converter_para_float).sum()
        
    tot_previsto = 0.0
    if not df_alunos.empty and "Status" in df_alunos.columns:
        ativos = df_alunos[df_alunos["Status"].astype(str).str.upper() == "ATIVO"]
        if "Valor" in ativos.columns:
            tot_previsto = ativos["Valor"].apply(converter_para_float).sum()

    m1, m2 = st.columns(2)
    m1.metric("Total Recebido (PAGO)", formatar_brl(tot_recebido))
    m2.metric("Total Líquido Previsto", formatar_brl(tot_previsto))
    
    if not df_alunos.empty and "Status" in df_alunos.columns:
        ativos = df_alunos[df_alunos["Status"].astype(str).str.upper() == "ATIVO"]
        lista_pagamento = [f"{r['Nome']} | Vencimento Dia: {r.get('Vencimento', '-')} | Valor: {formatar_brl(r.get('Valor', 0))}" for _, r in ativos.iterrows()]
        
        if lista_pagamento:
            st.markdown("### 💵 Registrar Baixa de Mensalidade")
            sel_p = st.selectbox("Selecione o Aluno:", lista_pagamento)
            forma = st.radio("Método:", ["PIX", "Dinheiro"], horizontal=True)
            
            if st.button("Confirmar Entrada"):
                nome_aluno = sel_p.split(" | ")[0]
                aluno_row = ativos[ativos["Nome"] == nome_aluno].iloc[0]
                val_p = converter_para_float(aluno_row.get("Valor", 0.0))
                
                novo_lancamento = {"Aluno": nome_aluno, "Valor": val_p, "Data": datetime.now().strftime("%d/%m/%Y"), "Forma": forma, "Status": "PAGO"}
                df_financeiro = pd.concat([df_financeiro, pd.DataFrame([novo_lancamento])], ignore_index=True)
                conn.update(worksheet="financeiro", data=df_financeiro.fillna("").astype(str))
                st.success("Entrada financeira registrada!")
                st.cache_data.clear()
                st.rerun()
    st.markdown("---")
    if not df_financeiro.empty:
        st.dataframe(df_financeiro.sort_index(ascending=False), use_container_width=True, hide_index=True)

# --- TELA: PERFIL ---
elif menu == "👤 Perfil":
    st.title("👤 Indicadores Analíticos Studio Highline")
    if not df_alunos.empty and "Status" in df_alunos.columns:
        ativos = df_alunos[df_alunos["Status"].astype(str).str.upper() == "ATIVO"]
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Matrículas Ativas", len(ativos))
        fat = ativos["Valor"].apply(converter_para_float).sum() if "Valor" in ativos.columns else 0.0
        c2.metric("Faturamento Mensal Estimado", formatar_brl(fat))
        c3.metric("Fila de Espera", len(df_espera))
        
        st.markdown("### Concentração por Modalidade/Plano")
        if "Plano" in ativos.columns and not list(ativos["Plano"].dropna().unique()) == []:
            st.bar_chart(ativos["Plano"].value_counts())
            
        st.markdown("### Ocupação Semanal por Dia de Aula")
        if "Dias" in ativos.columns:
            dias_acumulados = []
            for d_str in ativos["Dias"].dropna().astype(str):
                for termo in d_str.replace("/", " ").split():
                    if termo in ["SEG", "TER", "QUA", "QUI", "SEX", "SAB"]:
                        dias_acumulados.append(termo)
            if dias_acumulados:
                st.bar_chart(pd.Series(dias_acumulados).value_counts())

# --- TELA: PREÇOS ---
elif menu == "⚙️ Preços":
    st.title("⚙️ Tabela Padrão de Precificação")
    with st.form("f_tabela_precos"):
        p1 = st.number_input("Valor Plano 1x semana (R$):", value=dict_precos.get("1x semana", 180.0))
        p2 = st.number_input("Valor Plano 2x semana (R$):", value=dict_precos.get("2x semana", 220.0))
        p3 = st.number_input("Valor Plano 3x semana (R$):", value=dict_precos.get("3x semana", 300.0))
        
        if st.form_submit_button("Salvar Modificações de Base"):
            df_novos_p = pd.DataFrame([{"Plano": "1x semana", "Valor": p1}, {"Plano": "2x semana", "Valor": p2}, {"Plano": "3x semana", "Valor": p3}]).astype(str)
            conn.update(worksheet="precos", data=df_novos_p)
            st.success("Tabela padrão redefinida!")
            st.cache_data.clear()
            st.rerun()

# --- TELA: ARQUIVO MORTO ---
elif menu == "📁 Arquivo Morto":
    st.title("📁 Alunos Inativos e Histórico (Arquivo Morto)")
    df_f_morto = pd.DataFrame()
    if not df_arquivo_morto.empty:
        df_f_morto = df_arquivo_morto.copy()
    if not df_alunos.empty and "Status" in df_alunos.columns:
        inativos = df_alunos[df_alunos["Status"].astype(str).str.upper() == "INATIVO"]
        if not inativos.empty:
            df_f_morto = pd.concat([df_f_morto, inativos], ignore_index=True).drop_duplicates(subset=["Nome"])
            
    if not df_f_morto.empty:
        st.dataframe(df_f_f_morto := df_f_morto.fillna("").replace("nan", ""), use_container_width=True, hide_index=True)
    else:
        st.info("O Arquivo Morto está completamente limpo.")

# --- TELA: IMPRESSÃO DE PRONTUÁRIO ---
elif menu == "🖨️ Imprimir Prontuário":
    st.title("🖨️ Visualização e Emissão de Prontuário Clínico")
    if not df_alunos.empty:
        opcoes = ["-- Escolha --"] + sorted(list(df_alunos["Nome"].dropna().unique()))
        sel_aluno = st.selectbox("Selecione o Aluno para emissão:", opcoes)
        
        if sel_aluno != "-- Escolha --":
            row = df_alunos[df_alunos["Nome"] == sel_aluno].iloc[0]
            idade = calcular_idade(row.get("Nascimento", ""))
            
            q_p = str(row.get('Queixa', ''))
            q_html = "Nenhuma cadastrada." if q_p.lower() == "nan" or not q_p.strip() else q_p.replace(' | ', '<br>● ')
            
            c_p = str(row.get('Conduta', ''))
            c_html = "Nenhuma diretriz estipulada." if c_p.lower() == "nan" or not c_p.strip() else c_p

            html_prontuario_final = f"""
            <html>
            <head>{ESTILO_PRONTUARIO_HTML}</head>
            <body>
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
                        <td colspan="2"><strong>Endereço:</strong> {row.get('Endereco', '-')} | <strong>Bairro:</strong> {row.get('Bairro', '-')}</td>
                    </tr>
                </table>
                
                <div class="prontuario-secao">2. QUADRO CLÍNICO E QUEIXAS MAPEADAS</div>
                <p style="color:#000000 !important; font-size:14px; margin-top:12px; line-height:1.6; padding-left:5px;">
                    ● {q_html}
                </p>
                
                <div class="prontuario-secao">3. DIRETRIZES TERAPÊUTICAS E CONDUTA RECOMENDADA</div>
                <p style="color:#000000 !important; font-size:14px; margin-top:12px; line-height:1.6; padding-left:5px; white-space: pre-line;">
                    {c_html}
                </p>
            </div>
            </body>
            </html>
            """
            # CORREÇÃO: Renderiza o componente HTML de forma isolada na interface web
            st.components.v1.html(html_prontuario_final, height=600, scrolling=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("""
                <button class="no-print" onclick="window.print()" style="
                    padding: 12px 24px; background-color: #2E5A44; color: white; border: none; 
                    border-radius: 6px; font-weight: bold; cursor: pointer; box-shadow: 0px 2px 5px rgba(0,0,0,0.2);
                ">🖨️ Executar Impressão Física / Salvar em PDF</button>
            """, unsafe_allow_html=True)
