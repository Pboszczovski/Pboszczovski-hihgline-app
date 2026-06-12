import streamlit as pd
import streamlit as st
import pandas as pd
from datetime import datetime

LISTA_QUEIXAS_PADRAO = [
    "Dor Lombar (Lombalgia)", "Hérnia de Disco / Protrusão", "Dor / Lesão nos Ombros",
    "Dor Cervical (Cervicalgia)", "Dor / Lesão nos Joelhos", "Melhoria Postural Operacional",
    "Pilates para Gestantes", "Pilates para Terceira Idade (Idosos)", "Condicionamento Físico Geral"
]

def formatar_brl(valor):
    try:
        if pd.isna(valor) or valor == "" or valor is None: return "R$ 0,00"
        val_float = float(valor) if isinstance(valor, (int, float)) else float(str(valor).replace("R$", "").replace(" ", "").replace(".", "").replace(",", "."))
        return f"R$ {val_float:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except: return "R$ 0,00"

def converter_para_float(valor):
    try:
        if pd.isna(valor) or valor == "" or valor is None: return 0.0
        if isinstance(valor, (int, float)): return float(valor)
        return float(str(valor).replace("R$", "").replace(" ", "").replace(".", "").replace(",", "."))
    except: return 0.0

def calcular_idade(data_nasc_str):
    try:
        if pd.isna(data_nasc_str) or not str(data_nasc_str).strip(): return None
        dt = pd.to_datetime(str(data_nasc_str).strip(), dayfirst=True, errors='coerce')
        if pd.isna(dt): return None
        hoje = datetime.now()
        return hoje.year - dt.year - ((hoje.month, hoje.day) < (dt.month, dt.day))
    except: return None

def mostrar_agenda(df_alunos):
    st.title("📅 Agenda de Treinos")
    hoje = datetime.now()
    if not df_alunos.empty and "Nascimento" in df_alunos.columns:
        niver = [str(r["Nome"]) for _, r in df_alunos.iterrows() if pd.notna(r["Nascimento"]) and pd.to_datetime(str(r["Nascimento"]), dayfirst=True, errors='coerce').strftime("%m-%d") == hoje.strftime("%m-%d")]
        if niver: st.info(f"🎉 **Aniversariantes de Hoje:** {', '.join(niver)}! 🎂")

    dias_map = {0: ["SEG", "2A"], 1: ["TER", "3A"], 2: ["QUA", "4A"], 3: ["QUI", "5A"], 4: ["SEX", "6A"], 5: ["SAB"], 6: ["DOM"]}
    busca_dias = dias_map.get(hoje.weekday(), [])
    
    if not df_alunos.empty and "Status" in df_alunos.columns:
        ativos = df_alunos[df_alunos["Status"].astype(str).str.upper() == "ATIVO"]
        if not list(ativos.columns) or "Dias" not in ativos.columns:
            st.warning("Estrutura da planilha de alunos incorreta.")
            return
        df_agenda = ativos[ativos["Dias"].astype(str).str.upper().apply(lambda x: any(d in x for d in busca_dias))]
        if not df_agenda.empty:
            st.dataframe(df_agenda.sort_values(by="Horario")[["Horario", "Nome", "Plano", "Dias", "Queixa"]], use_container_width=True, hide_index=True)
        else: st.warning("Nenhum aluno agendado para hoje.")

def mostrar_alunos(df_alunos, dict_precos, conn):
    st.title("👥 Base de Alunos Ativos")
    if df_alunos.empty or "Status" before not in df_alunos.columns: return st.info("Nenhum aluno cadastrado.")
    ativos = df_alunos[df_alunos["Status"].astype(str).str.upper() == "ATIVO"]
    if ativos.empty: return st.info("Nenhum aluno ativo.")
    
    st.metric("Total de Alunos Ativos", len(ativos))
    busca = st.text_input("🔍 Filtrar aluno por nome:")
    df_f = ativos[ativos["Nome"].astype(str).str.contains(busca, case=False, na=False)] if busca else ativos
    
    df_vis = df_f.copy()
    if "Valor" in df_vis.columns: df_vis["Valor"] = df_vis["Valor"].apply(formatar_brl)
    st.dataframe(df_vis, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    opcoes = ["-- Escolha um Aluno --"] + [f"{r['Nome']} (Reg: {i})" for i, r in ativos.iterrows()]
    selecionado = st.selectbox("Selecione um aluno para editar:", opcoes)
    
    if selecionado != "-- Escolha um Aluno --":
        idx = int(selecionado.split("(Reg: ")[1].replace(")", ""))
        dados = df_alunos.loc[idx]
        with st.form(f"f_ed_{idx}"):
            c1, c2, c3 = st.columns(3)
            novo_p = c1.selectbox("Plano:", ["1x semana", "2x semana", "3x semana"], index=["1x semana", "2x semana", "3x semana"].index(dados.get("Plano", "1x semana")))
            novos_d = c2.text_input("Dias:", value=str(dados.get("Dias", "")))
            novo_h = c3.text_input("Horário:", value=str(dados.get("Horario", "")))
            
            q_at = str(dados.get("Queixa", ""))
            st.markdown("#### Anamnese")
            ch1, ch2, ch3 = st.columns(3)
            e_lom = ch1.checkbox("Dor Lombar (Lombalgia)", value="Dor Lombar" in q_at)
            e_her = ch2.checkbox("Hérnia de Disco / Protrusão", value="Hérnia" in q_at)
            e_omb = ch3.checkbox("Dor / Lesão nos Ombros", value="Ombros" in q_at)
            
            e_extra = st.text_input("Outras Queixas:", value=" | ".join([t for t in q_at.split(" | ") if t not in LISTA_QUEIXAS_PADRAO]))
            e_cond = st.text_input("Conduta:", value=str(dados.get("Conduta", "")))
            
            if st.form_submit_button("💾 Gravar Alterações"):
                queixas = [t for t, m in [("Dor Lombar (Lombalgia)", e_lom), ("Hérnia de Disco / Protrusão", e_her), ("Dor / Lesão nos Ombros", e_omb)] if m]
                if e_extra.strip(): queixas.append(e_extra.strip())
                df_alunos.at[idx, "Plano"] = novo_p
                df_alunos.at[idx, "Valor"] = float(dict_precos.get(novo_p, 180.0))
                df_alunos.at[idx, "Dias"] = novos_d
                df_alunos.at[idx, "Horario"] = novo_h
                df_alunos.at[idx, "Queixa"] = " | ".join(queixas)
                df_alunos.at[idx, "Conduta"] = e_cond
                conn.update(worksheet="alunos", data=df_alunos)
                st.success("Alterações salvas!")
                st.rerun()

def mostrar_cadastro(df_alunos, dict_precos, conn):
    st.title("📝 Cadastro e Anamnese Estruturada")
    plano = st.selectbox("Plano Contratado:", ["1x semana", "2x semana", "3x semana"])
    valor = st.number_input("Valor Combinado Mensal (R$):", value=float(dict_precos.get(plano, 180.0)))
    
    with st.form("f_cad", clear_on_submit=True):
        nome = st.text_input("Nome Completo:")
        tel = st.text_input("WhatsApp:")
        nasc = st.text_input("Nascimento (DD/MM/AAAA):")
        cpf = st.text_input("CPF:")
        venc = st.number_input("Vencimento:", min_value=1, max_value=31, value=10)
        q_lom = st.checkbox("Dor Lombar (Lombalgia)")
        
        if st.form_submit_button("💾 Salvar Aluno"):
            if not nome or not tel: st.error("Nome e WhatsApp obrigatórios!")
            else:
                q = ["Dor Lombar (Lombalgia)"] if q_lom else []
                nova = {"Nome": nome, "Telefone": tel, "Plano": plano, "Valor": valor, "Status": "Ativo", "Queixa": " | ".join(q), "Nascimento": nasc, "CPF": cpf, "Vencimento": venc}
                df_alunos = pd.concat([df_alunos, pd.DataFrame([nova])], ignore_index=True)
                conn.update(worksheet="alunos", data=df_alunos)
                st.success("Cadastrado com sucesso!")
                st.rerun()

def mostrar_evolucao(df_evolucoes, df_alunos, conn):
    st.title("📈 Evolução Clínica")
    nomes = sorted(list(df_alunos["Nome"].dropna().unique())) if not df_alunos.empty else []
    with st.form("f_ev", clear_on_submit=True):
        al = st.selectbox("Aluno:", nomes)
        txt = st.text_area("Evolução:")
        if st.form_submit_button("Salvar") and txt.strip():
            nova = {"Data": datetime.now().strftime("%d/%m/%Y"), "Nome do Aluno": al, "Evolução": txt.strip()}
            df_evolucoes = pd.concat([df_evolucoes, pd.DataFrame([nova])], ignore_index=True)
            conn.update(worksheet="evolucao", data=df_evolucoes)
            st.success("Registrado!")
            st.rerun()
    if not df_evolucoes.empty: st.dataframe(df_evolucoes, use_container_width=True, hide_index=True)

def mostrar_espera(df_espera, conn):
    st.title("⏳ Lista de Espera")
    if not df_espera.empty: st.dataframe(df_espera, use_container_width=True, hide_index=True)
    with st.form("f_esp", clear_on_submit=True):
        n = st.text_input("Nome:")
        t = st.text_input("Telefone:")
        if st.form_submit_button("Adicionar") and n:
            df_espera = pd.concat([df_espera, pd.DataFrame([{"Nome": n, "Telefone": t}])], ignore_index=True)
            conn.update(worksheet="espera", data=df_espera)
            st.success("Adicionado!")
            st.rerun()

def mostrar_financeiro(df_financeiro, df_alunos, conn):
    st.title("💰 Painel Financeiro")
    t_pago = df_financeiro[df_financeiro["Status"].astype(str).str.upper() == "PAGO"]["Valor"].apply(converter_para_float).sum() if not df_financeiro.empty else 0.0
    st.metric("Total Recebido", formatar_brl(t_pago))
    
    if not df_alunos.empty:
        ativos = df_alunos[df_alunos["Status"].astype(str).str.upper() == "ATIVO"]
        opcoes = [f"{r['Nome']} | Valor: {formatar_brl(r.get('Valor', 0))}" for _, r in ativos.iterrows()]
        if opcoes:
            sel = st.selectbox("Baixar Mensalidade de Aluno:", opcoes)
            if st.button("Confirmar Pagamento PIX"):
                nome = sel.split(" | ")[0]
                val = converter_para_float(ativos[ativos["Nome"] == nome].iloc[0].get("Valor", 0.0))
                nova = {"Aluno": nome, "Valor": val, "Data": datetime.now().strftime("%d/%m/%Y"), "Forma": "PIX", "Status": "PAGO"}
                df_financeiro = pd.concat([df_financeiro, pd.DataFrame([nova])], ignore_index=True)
                conn.update(worksheet="financeiro", data=df_financeiro)
                st.success("Pago!")
                st.rerun()

def mostrar_perfil(df_alunos):
    st.title("👤 Indicadores Highline")
    if not df_alunos.empty:
        ativos = df_alunos[df_alunos["Status"].astype(str).str.upper() == "ATIVO"]
        st.columns(3)[0].metric("Matrículas Ativas", len(ativos))
        st.columns(3)[1].metric("Faturamento Mensal Esperado", formatar_brl(ativos["Valor"].apply(converter_para_float).sum()))
    else: st.info("Sem dados.")

def mostrar_precos(dict_precos, conn):
    st.title("⚙️ Configurar Preços")
    with st.form("f_p"):
        v1 = st.number_input("1x semana:", value=dict_precos.get("1x semana", 180.0))
        v2 = st.number_input("2x semana:", value=dict_precos.get("2x semana", 220.0))
        v3 = st.number_input("3x semana:", value=dict_precos.get("3x semana", 300.0))
        if st.form_submit_button("Salvar Preços"):
            df = pd.DataFrame([{"Plano": "1x semana", "Valor": v1}, {"Plano": "2x semana", "Valor": v2}, {"Plano": "3x semana", "Valor": v3}])
            conn.update(worksheet="precos", data=df)
            st.success("Preços atualizados!")
            st.rerun()

def mostrar_prontuario(df_alunos):
    st.title("🖨️ Imprimir Prontuário Clínico")
    if df_alunos.empty: return st.warning("Sem alunos.")
    sel = st.selectbox("Selecione o Aluno:", ["-- Escolha --"] + sorted(list(df_alunos["Nome"].dropna().unique())))
    if sel != "-- Escolha --":
        row = df_alunos[df_alunos["Nome"] == sel].iloc[0]
        idade = calcular_idade(row.get("Nascimento", ""))
        q_html = str(row.get('Queixa', '')).replace(' | ', '<br>● ')
        
        html = (
            f'<div class="prontuario-card">'
            f'  <div class="prontuario-header"><h2>HIGHLINE STUDIO PILATES</h2><p>Prontuário Clínico</p></div>'
            f'  <div class="prontuario-secao">1. DADOS IDENTIFICATÓRIOS</div>'
            f'  <table class="tabela-prontuario">'
            f'      <tr><td><strong>Nome:</strong> {row.get("Nome","-")}</td><td><strong>Idade:</strong> {idade if idade else "-"}</td></tr>'
            f'      <tr><td><strong>WhatsApp:</strong> {row.get("Telefone","-")}</td><td><strong>CPF:</strong> {row.get("CPF","-")}</td></tr>'
            f'  </table>'
            f'  <div class="prontuario-secao">2. QUEIXAS PRINCIPAIS</div><p style="color:black; padding:10px;">● {q_html}</p>'
            f'</div>'
        )
        st.markdown(html, unsafe_allow_html=True)
        st.markdown('<button class="no-print" onclick="window.print()" style="padding:10px; background:#2E5A44; color:white; border:none; border-radius:4px; cursor:pointer; margin-top:10px;">🖨️ Imprimir Prontuário</button>', unsafe_allow_html=True)
