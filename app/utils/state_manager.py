import streamlit as st
import datetime
import pandas as pd
import os

# Silencia avisos de downcasting do Pandas 2.2+ (FutureWarning)
pd.set_option('future.no_silent_downcasting', True)

def get_max_year_from_data():
    """Tenta obter o maior ano disponível no dataset principal da Home."""
    try:
        # Caminho relativo ao diretório raiz da aplicação
        csv_path = "app/data/DashboardHome.csv"
        if os.path.exists(csv_path):
            # Lemos apenas a coluna Ano para ser performático
            df_temp = pd.read_csv(csv_path, sep=';', usecols=['Ano'])
            if not df_temp.empty:
                return int(df_temp['Ano'].max())
    except Exception:
        pass
    return datetime.datetime.now().year

def init_global_state():
    """Inicializa as chaves do session_state se não existirem."""
    if "global_years" not in st.session_state:
        # O único valor default permitido em todo o dashboard é o do maior ano disponível
        max_year = get_max_year_from_data()
        st.session_state["global_years"] = [max_year]
        
    if "global_urgs" not in st.session_state:
        st.session_state["global_urgs"] = []

    # Inicializa as chaves dos widgets para evitar erros de sincronização
    if "sidebar_year_filter" not in st.session_state:
        st.session_state["sidebar_year_filter"] = st.session_state["global_years"]
        
    if "home_year_buttons" not in st.session_state:
        st.session_state["home_year_buttons"] = st.session_state["global_years"]

    if "sidebar_urg_filter" not in st.session_state:
        st.session_state["sidebar_urg_filter"] = st.session_state["global_urgs"]

    if "sidebar_escola_filter" not in st.session_state:
        st.session_state["sidebar_escola_filter"] = []

    if "_prev_urg_filter_val" not in st.session_state:
        st.session_state["_prev_urg_filter_val"] = st.session_state["global_urgs"]

    if "_prev_escola_filter_val" not in st.session_state:
        st.session_state["_prev_escola_filter_val"] = st.session_state["sidebar_escola_filter"]

    # --- Persistência de Filtros Locais (Evita poda do Streamlit na navegação) ---
    # Todos os filtros locais devem iniciar vazios (equivalente a "Todos")
    if "persistent_consulta_encaminhamento" not in st.session_state:
        st.session_state["persistent_consulta_encaminhamento"] = []
    
    if "persistent_vacinacao_vacina" not in st.session_state:
        st.session_state["persistent_vacinacao_vacina"] = []

    if "persistent_exame_regulacao" not in st.session_state:
        st.session_state["persistent_exame_regulacao"] = []

    if "persistent_nutricao_situacao" not in st.session_state:
        st.session_state["persistent_nutricao_situacao"] = []

def sync_sidebar_to_home():
    """Callback disparada quando a sidebar muda (Anos)."""
    st.session_state["global_years"] = st.session_state["sidebar_year_filter"]
    st.session_state["home_year_buttons"] = st.session_state["sidebar_year_filter"]

def sync_home_to_sidebar():
    """Callback disparada quando os botões da Home mudam (Anos)."""
    st.session_state["global_years"] = st.session_state["home_year_buttons"]
    st.session_state["sidebar_year_filter"] = st.session_state["home_year_buttons"]

def sync_sidebar_urg_to_home():
    """Callback disparada quando a sidebar muda (URGs)."""
    st.session_state["global_urgs"] = st.session_state["sidebar_urg_filter"]
    # Marca que a mudança veio da sidebar para evitar que a tabela a sobrescreva no próximo rerun
    st.session_state["last_interaction_source"] = "sidebar"

def sync_home_urg_to_sidebar():
    """Callback disparada quando a seleção na tabela/botões da Home muda (URGs)."""
    st.session_state["sidebar_urg_filter"] = st.session_state["global_urgs"]
    st.session_state["last_interaction_source"] = "table"

def sync_sidebar_escola_to_global():
    """Callback disparada quando a sidebar muda (Escolas)."""
    # Marca que a mudança veio da sidebar
    st.session_state["last_interaction_source"] = "sidebar"

def sync_global_escola_to_sidebar():
    """Mantém a sidebar em paridade com as seleções de tabela de escola."""
    pass # Geralmente as tabelas de escola já atualizam o sidebar_escola_filter diretamente

def apply_pending_table_filters():
    """Apply pending table selections before sidebar widgets are rendered."""
    pending_table_urgs = st.session_state.pop("pending_sidebar_urg_filter", None)
    if pending_table_urgs is not None:
        pending_table_urgs = list(pending_table_urgs)
        st.session_state["sidebar_urg_filter"] = pending_table_urgs
        st.session_state["global_urgs"] = pending_table_urgs
        st.session_state["last_interaction_source"] = "table"

    pending_table_escolas = st.session_state.pop("pending_sidebar_escola_filter", None)
    if pending_table_escolas is not None:
        pending_table_escolas = list(pending_table_escolas)
        st.session_state["sidebar_escola_filter"] = pending_table_escolas
        st.session_state["last_interaction_source"] = "table_escola"

def sync_sidebar_escola_selection(table_key: str):
    """Mirror sidebar Escola changes into the page-specific table selection key."""
    current_sidebar_escolas = list(st.session_state.get("sidebar_escola_filter", []))
    previous_state_key = f"{table_key}__prev_sidebar_escola_filter"
    prev_sidebar_escolas = list(st.session_state.get(previous_state_key, []))

    if set(map(str, current_sidebar_escolas)) != set(map(str, prev_sidebar_escolas)):
        st.session_state["last_interaction_source"] = "sidebar"
        st.session_state[f"{table_key}__selected_values"] = current_sidebar_escolas

    st.session_state[previous_state_key] = current_sidebar_escolas

# --- Callbacks de Sincronização de Filtros Locais ---
def sync_local_consulta_encaminhamento():
    st.session_state["persistent_consulta_encaminhamento"] = st.session_state["consulta_encaminhamento_multiselect"]

def sync_local_vacinacao_vacina():
    st.session_state["persistent_vacinacao_vacina"] = st.session_state["vacinacao_vacina_multiselect"]

def sync_local_exame_regulacao():
    st.session_state["persistent_exame_regulacao"] = st.session_state["exame_regulacao_multiselect"]

def sync_local_nutricao_situacao():
    st.session_state["persistent_nutricao_situacao"] = st.session_state["nutricao_situacao_multiselect"]
