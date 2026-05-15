import base64
from io import BytesIO
from pathlib import Path
import sys

from PIL import Image
import streamlit as st
from streamlit_option_menu import option_menu

# Ajusta caminho/namespace para permitir imports relativos mesmo executando com streamlit run main.py
if __package__ is None or __package__ == "":
    ROOT_DIR = Path(__file__).resolve().parent.parent
    if str(ROOT_DIR) not in sys.path:
        sys.path.insert(0, str(ROOT_DIR))
    __package__ = "app"

from .utils.styles import apply_global_css
from .app_pages.home import page_home
from .app_pages.consulta import page_consulta
from .app_pages.exame import page_exame
from .app_pages.vacinacao import page_vacinacao
from .app_pages.nutricao import page_nutricao
from .app_pages.enfermagem import page_enfermagem
from .app_pages.psicologo import page_psicologo
from .app_pages.assistencia_social import page_assistencia_social
from .app_pages.professor import page_professor
from .app_pages.medico import page_medico
from .app_pages.aluno import page_aluno
from .utils.state_manager import init_global_state

# Inicializa o estado global (ex: sincronização de filtros)
init_global_state()

# Configurações da página
st.set_page_config(
    page_title="Dashboard SAEDAS",
    page_icon="assets/favicon.ico",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Pode ajudar a garantir que ele seja incluído se o crawler o encontrar.
st.markdown(
    '<meta property="og:title" content="Dashboard SAEDAS" />', unsafe_allow_html=True
)

# CSS global (Sincronizado com o Design System SAEDAS)
apply_global_css()

# --- Tratamento de Parâmetros de URL (Deep-linking) ---
params = st.query_params
menu_options_all = ["Início", "Encaminhamentos", "Exames", "Vacinação", "Nutrição", "Enfermagem", "Assistente Social", "Psicólogo", "Professor", "Médico", "Aluno"]

# 1. Verifica se há um parâmetro de menu na URL
menu_from_url = False
menu_param = params.get("menu")
if isinstance(menu_param, list): menu_param = menu_param[0]

if menu_param in menu_options_all:
    st.session_state["menu_escolhido"] = menu_param
    menu_from_url = True

# 2. Lógica específica para Aluno (Busca automática)
if "aluno" in params:
    def _first(value):
        if isinstance(value, list):
            return value[0] if value else None
        return value

    aluno_param = _first(params.get("aluno"))
    nasc_param = _first(params.get("nasc"))
    if aluno_param:
        st.session_state["aluno_preselect"] = {"nome": aluno_param, "nasc": nasc_param}
    st.session_state["menu_escolhido"] = "Aluno"
    menu_from_url = True
    
# Limpa apenas os parâmetros de roteamento global processados para evitar loops, 
# mas preserva parâmetros de filtro de página (como toggle_reg)
for k in ["menu", "aluno", "nasc"]:
    if k in st.query_params:
        try:
            del st.query_params[k]
        except:
            pass


# --- Sidebar customizada ---
with st.sidebar:
    try:
        logo_pil = Image.open("assets/logo-pcni.png")  # Carrega a imagem com Pillow

        # Converter a imagem PIL para uma string base64
        buffered = BytesIO()
        logo_pil.save(
            buffered, format="PNG"
        )  # Salva a imagem em um buffer (assumindo PNG)
        img_str = base64.b64encode(buffered.getvalue()).decode()

        # Exibir a imagem centralizada usando st.markdown com HTML/CSS
        # Usamos flexbox para centralizar o conteúdo (a imagem) dentro do div.
        st.markdown(
            f"""
            <div style="
                display: flex;
                justify-content: center;
                align-items: center;
                background-color: #1e293b;
                border-radius: 12px;
                padding: 12px 8px;
                margin-bottom: 8px;
            ">
                <img src="data:image/png;base64,{img_str}" alt="Logo SAEDAS" width="200">
            </div>
            """,
            unsafe_allow_html=True,
        )
    except FileNotFoundError:
        st.warning("Logo 'logo-pcni.png' não encontrado.")

    st.markdown(
        "<h1 style='text-align: center; font-size: 1.8em;'>Dashboard SAEDAS</h1>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    menu_options = [
        "Início",
        "Encaminhamentos",
        "Exames",
        "Vacinação",
        "Nutrição",
        "Enfermagem",
        "Assistente Social",
        "Psicólogo",
        "Professor",
        "Médico",
        "Aluno",
    ]
    default_option = st.session_state.get("menu_escolhido", menu_options[0])
    default_index = (
        menu_options.index(default_option) if default_option in menu_options else 0
    )
    menu_key = "sidebar_main_menu"

    def sync_sidebar_menu(key: str) -> None:
        selected_menu = st.session_state.get(key)
        if selected_menu in menu_options:
            st.session_state["menu_escolhido"] = selected_menu

    menu_escolhido = option_menu(
        menu_title=None,
        options=menu_options,
        icons=[
            "house",
            "clipboard-check",
            "file-medical",
            "shield-plus",
            "egg-fried",
            "bandaid",
            "people",
            "person-heart",
            "mortarboard",
            "heart-pulse",
            "person",
        ],
        default_index=default_index,
        manual_select=default_index if menu_from_url else None,
        orientation="vertical",
        key=menu_key,
        on_change=sync_sidebar_menu,
    )
    selected_menu = st.session_state.get(menu_key, menu_escolhido)
    if selected_menu in menu_options:
        menu_escolhido = selected_menu
        st.session_state["menu_escolhido"] = selected_menu

# O menu_escolhido final é determinado pelo option_menu ou pelo estado injetado acima


# --- Roteamento ---
if menu_escolhido == "Início":
    page_home()
elif menu_escolhido == "Encaminhamentos":
    page_consulta()
elif menu_escolhido == "Exames":
    page_exame()
elif menu_escolhido == "Vacinação":
    page_vacinacao()
elif menu_escolhido == "Nutrição":
    page_nutricao()
elif menu_escolhido == "Enfermagem":
    page_enfermagem()
elif menu_escolhido == "Assistente Social":
    page_assistencia_social()
elif menu_escolhido == "Psicólogo":
    page_psicologo()
elif menu_escolhido == "Professor":
    page_professor()
elif menu_escolhido == "Médico":
    page_medico()
elif menu_escolhido == "Aluno":
    page_aluno()

# streamlit run main.py
