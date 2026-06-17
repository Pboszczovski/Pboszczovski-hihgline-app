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
        .prontuario-secao {
            background-color: #2E5A44;
            color: white;
            padding: 8px;
            font-weight: bold;
            margin-top: 15px;
            margin-bottom: 5px;
            border-radius: 4px;
        }
        .bloco-texto {
            border: 1px solid #ccc;
            padding: 10px;
            background-color: #f9f9f9;
            min-height: 60px;
            border-radius: 4px;
        }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. CONEXÃO COM O BANCO DE DADOS (GSHEETS)
# ==========================================
@st.cache_data(ttl=600)
def carregar_dados_aba(nome_aba):
    try:
        # Tenta conectar usando o conector oficial do Streamlit
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet=nome_aba)
        # Remove linhas completamente vazias
        df = df.dropna(how='all')
        return df
    except Exception as e:
        st.error(f"⚠️ Erro ao conectar à aba '{nome_aba}': {e}")
        return pd.DataFrame()

# Carregamento global dos dados
df_clientes = carregar_dados_aba("Clientes")
df_evolucoes = carregar_dados_aba("Evolucoes")
df_precos = carregar_dados_aba("Precos")  # Nova ou restaurada para a aba de Preços

# Botão de emergência no rodapé da barra lateral para limpar cache
with st.sidebar:
    st.markdown("---")
    if st.button("🔄 Forçar Recarregamento do Banco"):
        st.cache_data.clear()
        st.rerun()

# ==========================================
# 3. NAVEGAÇÃO / MENU LATERAL
# ==========================================
with st.sidebar:
    st.markdown('<div class="logo-container"><h1>Highline 🏋️‍♂️</h1></div>', unsafe_allow_html=True)
    st.markdown("### Navegação")
    menu = st.radio(
        "Ir para:",
        ["Dashboard Geral", "Prontuário Eletrônico", "Financeiro", "Preços", "Perfil", "Arquivo Morto"]
    )

# ==========================================
# 4. ABA: DASHBOARD GERAL
# ==========================================
if menu == "Dashboard Geral":
    st.title("📊 Dashboard Geral")
    
    if not df_clientes.empty:
        total_ativos = len(df_clientes[df_clientes['Status'].str.upper() == 'ATIVO']) if 'Status' in df_clientes.columns else len(df_clientes)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Alunos Ativos", total_ativos)
        col2.metric("Total Cadastrados", len(df_clientes))
        col3.metric("Evoluções Registradas", len(df_evolucoes) if not df_evolucoes.empty else 0)
        
        st.markdown("---")
        st.subheader("Lista Rápida de Clientes Ativos")
        st.dataframe(df_clientes, use_container_width=True)
    else:
        st.warning("Sem dados de clientes para exibir no Dashboard. Verifique a conexão com a planilha.")

# ==========================================
# 5. ABA: PRONTUÁRIO ELETRÔNICO & IMPRESSÃO
# ==========================================
elif menu == "Prontuário Eletrônico":
    st.title("🩺 Prontuário Eletrônico")
    
    if df_clientes.empty:
        st.error("Não foi possível carregar os dados dos clientes para o Prontuário.")
    else:
        # Filtro de paciente ativo
        lista_pacientes = df_clientes['Nome'].dropna().unique().tolist()
        paciente_selecionado = st.selectbox("Selecione o Cliente/Paciente:", lista_pacientes)
        
        if paciente_selecionado:
            # Dados cadastrais do indivíduo
            dados_paciente = df_clientes[df_clientes['Nome'] == paciente_selecionado].iloc[0]
            
            st.markdown(f"### Histórico de: {paciente_selecionado}")
            
            col1, col2, col3 = st.columns(3)
            col1.write(f"**Nascimento:** {dados_paciente.get('Nascimento', 'Não informado')}")
            col2.write(f"**Telefone:** {dados_paciente.get('Telefone', 'Não informado')}")
            col3.write(f"**Objetivo:** {dados_paciente.get('Objetivo', 'Não informado')}")
            
            # Filtrar evoluções do paciente
            if not df_evolucoes.empty and 'Nome' in df_evolucoes.columns:
                evolucoes_paciente = df_evolucoes[df_evolucoes['Nome'] == paciente_selecionado]
            else:
                evolucoes_paciente = pd.DataFrame()
                
            st.markdown("---")
            st.subheader("Gerar Prontuário para Impressão")
            
            # Montagem do Bloco HTML de Evoluções
            html_bloco_evolucoes = ""
            if not evolucoes_paciente.empty:
                for _, row_ev in evolucoes_paciente.sort_values(by=evolucoes_paciente.columns[0], ascending=False).iterrows():
                    data_ev = row_ev.get('Data', 'S/D')
                    detalhe_ev = row_ev.get('Evolucao', 'Sem descrição.')
                    html_bloco_evolucoes += f"""
                    <div style='border-bottom: 1px dashed #ccc; padding: 5px 0;'>
                        <strong>Data:</strong> {data_ev}<br>
                        {detalhe_ev}
                    </div>
                    """
            else:
                html_bloco_evolucoes = "<p>Nenhuma evolução registrada para este paciente.</p>"

            # Template HTML Completo para o Iframe de Impressão (Resolve o erro do prontuário em branco)
            html_prontuario = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; color: #333; }}
                    .header {{ text-align: center; border-bottom: 2px solid #2E5A44; padding-bottom: 10px; }}
                    .titulo {{ font-size: 22px; font-weight: bold; color: #2E5A44; margin: 5px 0; }}
                    .subtitulo {{ font-size: 14px; color: #666; }}
                    .ficha-tecnica {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
                    .ficha-tecnica td {{ padding: 6px; border: 1px solid #ddd; font-size: 13px; }}
                    .prontuario-secao {{ background-color: #2E5A44; color: white; padding: 6px; font-weight: bold; margin-top: 15px; font-size: 14px; border-radius: 4px; }}
                    .bloco-texto {{ border: 1px solid #ccc; padding: 10px; background-color: #f9f9f9; min-height: 50px; font-size: 13px; margin-top: 5px; border-radius: 4px; }}
                    @media print {{
                        .btn-imprimir {{ display: none; }}
                    }}
                </style>
            </head>
            <body>
                <div style="text-align: right;">
                    <button class="btn-imprimir" onclick="window.print();" style="padding: 8px 15px; background-color: #2E5A44; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold;">
                        🖨️ Imprimir Prontuário
                    </button>
                </div>
                
                <div class="header">
                    <div class="titulo">HIGHLINE MANAGEMENT</div>
                    <div class="subtitulo">Prontuário de Acompanhamento Integrado</div>
                </div>
                
                <table class="ficha-tecnica">
                    <tr>
                        <td style="font-weight: bold; background-color: #f5f5f5; width: 15%;">Paciente:</td>
                        <td colspan="3"><strong>{paciente_selecionado}</strong></td>
                    </tr>
                    <tr>
                        <td style="font-weight: bold; background-color: #f5f5f5;">Nascimento:</td>
                        <td>{dados_paciente.get('Nascimento', 'Não Informado')}</td>
                        <td style="font-weight: bold; background-color: #f5f5f5; width: 15%;">Objetivo:</td>
                        <td>{dados_paciente.get('Objetivo', 'Não Informado')}</td>
                    </tr>
                </table>
                
                <div class="prontuario-secao">🩺 Diagnóstico Clínico e Anamnese / Queixa</div>
                <div class="bloco-texto">
                    {dados_paciente.get('Queixa', 'Nenhuma condição ou queixa inicial mapeada.')}
                </div>
                
                <div class="prontuario-secao">📋 Diretrizes de Conduta e Observações</div>
                <div class="bloco-texto" style="white-space: pre-wrap;">
                    {dados_paciente.get('Conduta', 'Sem restrições ou diretrizes específicas cadastradas.')}
                </div>
                
                <div class="prontuario-secao">📈 Histórico de Evolução do Tratamento</div>
                <div style="margin-top: 5px;">
                    {html_bloco_evolucoes}
                </div>
                
                <div style="margin-top: 50px; text-align: center;">
                    <div style="border-top: 1px solid #000; width: 280px; margin: 0 auto; padding-top: 5px; font-size: 12px;">
                        Assinatura do Profissional Responsável
                    </div>
                </div>
            </body>
            </html>
            """
            # Renderiza o componente de impressão em tela de forma segura
            components.html(html_prontuario, height=600, scrolling=True)

# ==========================================
# 6. ABA: FINANCEIRO
# ==========================================
elif menu == "Financeiro":
    st.title("💰 Gestão Financeira")
    st.markdown("Área destinada ao controle de faturamento, mensalidades e fluxo de caixa do ecossistema Highline.")
    
    # Exemplo de lógica baseada na coluna de pagamentos se houver no seu sheets
    if not df_clientes.empty and 'Valor' in df_clientes.columns:
        st.subheader("Visão Geral de Receitas Estimadas")
        df_clientes['Valor'] = pd.to_numeric(df_clientes['Valor'], errors='coerce').fillna(0)
        total_estimado = df_clientes['Valor'].sum()
        st.metric("Faturamento Mensal Estimado (Ativos)", f"R$ {total_estimado:,.2f}")
        st.dataframe(df_clientes[['Nome', 'Valor', 'Status']], use_container_width=True)
    else:
        st.info("💡 Dica: Para extrair relatórios financeiros automáticos aqui, certifique-se de ter as colunas 'Valor' e 'Status' preenchidas na sua planilha mãe.")

# ==========================================
# 7. ABA: PREÇOS
# ==========================================
elif menu == "Preços":
    st.title("🏷️ Tabela de Preços e Planos")
    st.markdown("Visualize ou gerencie a estrutura mercadológica de planos vigentes (Mensal, Trimestral, Semestral).")
    
    if not df_precos.empty:
        st.dataframe(df_precos, use_container_width=True)
    else:
        # Tabela padrão caso a aba física ainda não exista no Sheets
        st.info("Exibindo tabela de referência padrão (Crie uma aba chamada 'Precos' no seu Sheets para customizar):")
        dados_padrao_precos = {
            "Plano": ["Individual Mensal", "Trimestral", "Semestral", "Consultoria Online"],
            "Preço Base": ["R$ 350,00", "R$ 900,00", "R$ 1.650,00", "R$ 250,00"],
            "Benefícios": ["Acesso livre + Avaliação", "Até 3x na semana", "Livre + Toalha inclusa", "Planilha via App"]
        }
        st.table(pd.DataFrame(dados_padrao_precos))

# ==========================================
# 8. ABA: PERFIL
# ==========================================
elif menu == "Perfil":
    st.title("👤 Perfil Administrativo")
    st.markdown("Configurações da conta master e visualização de parâmetros operacionais do sistema.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Nome da Unidade / Empresa", value="Highline Management", disabled=True)
        st.text_input("E-mail Responsável", value="contato@highlinemanagement.com", disabled=True)
    with col2:
        st.text_input("Nível de Acesso", value="Administrador Master / Síndico", disabled=True)
        st.text_input("Status do Banco de Dados", value="Conectado via Streamlit Connections", disabled=True)

# ==========================================
# 9. ABA: ARQUIVO MORTO
# ==========================================
elif menu == "Arquivo Morto":
    st.title("🗄️ Arquivo Morto (Inativos)")
    st.markdown("Visualização de registros históricos de alunos ou pacientes que estão atualmente com o status **Inativo**.")
    
    if not df_clientes.empty and 'Status' in df_clientes.columns:
        df_inativos = df_clientes[df_clientes['Status'].str.upper() == 'INATIVO']
        if not df_inativos.empty:
            st.dataframe(df_inativos, use_container_width=True)
        else:
            st.success("Nenhum cliente ou registro localizado no arquivo morto (Todos constam como ativos).")
    else:
        st.warning("Não foi possível filtrar o arquivo morto. Certifique-se de que a coluna 'Status' existe no seu Google Sheets.")
