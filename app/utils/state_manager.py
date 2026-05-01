import streamlit as st
import datetime

def init_global_state():
    """Inicializa as chaves do session_state se não existirem."""
    current_year = datetime.datetime.now().year
    
    if "global_years" not in st.session_state:
        st.session_state["global_years"] = [current_year]
        
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
