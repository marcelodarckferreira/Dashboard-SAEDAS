import base64
from io import BytesIO
from pathlib import Path
import sys

from PIL import Image
import streamlit as st
import streamlit.components.v1 as components
from streamlit_option_menu import option_menu
from decouple import config

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

# --- SEGURANÇA: CONTROLE DE ACESSO VIA TOKEN ---
def render_login_screen():
    """Renderiza uma tela de login premium para validação do Token."""
    # Centraliza o conteúdo na tela
    _, col_center, _ = st.columns([1, 2, 1])
    
    with col_center:
        st.markdown("<div style='height: 10vh'></div>", unsafe_allow_html=True)
        
        # Logo e Cabeçalho
        try:
            logo_pil = Image.open("assets/logo-pcni.png")
            buffered = BytesIO()
            logo_pil.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            st.markdown(
                f"""
                <div style="display: flex; justify-content: center; margin-bottom: 24px;">
                    <img src="data:image/png;base64,{img_str}" width="240">
                </div>
                """,
                unsafe_allow_html=True
            )
        except:
            st.title("SAEDAS")

        st.markdown(
            """
            <div style="text-align: center; margin-bottom: 32px;">
                <h2 style='color: #f1f5f9; font-weight: 800; margin-bottom: 8px;'>Verificação de Segurança</h2>
                <p style='color: #94a3b8; font-size: 0.95rem;'>Insira o código de 8 dígitos para acessar o sistema</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Container do Formulário (8 Campos Segmentados)
        st.markdown(
            """
            <style>
            /* Centralização e Estilo dos Campos de Input */
            div[data-testid="stTextInput"] input {
                text-align: center !important;
                font-size: 1.8rem !important;
                font-weight: 800 !important;
                padding: 10px 0 !important;
                border: 2px solid #334155 !important;
                background: #0f172a !important;
                color: #38bdf8 !important;
                border-radius: 8px !important;
                caret-color: transparent !important;
                width: 100% !important;
            }
            div[data-testid="stTextInput"] input:focus {
                border-color: #38bdf8 !important;
                background: #1e293b !important;
                box-shadow: 0 0 15px rgba(56, 189, 248, 0.3) !important;
                outline: none !important;
            }
            
            /* Estilização de Alta Especificidade para o Botão de Validar */
            div[data-testid="stButton"] button {
                background-color: #38bdf8 !important;
                border: 2px solid #38bdf8 !important;
                border-radius: 8px !important;
                height: 54px !important;
                width: 100% !important;
                margin-top: 20px !important;
                transition: all 0.3s ease-in-out !important;
                display: flex !important;
                justify-content: center !important;
                align-items: center !important;
            }
            div.stButton > button:hover {
                background-color: #7dd3fc !important;
                box-shadow: 0 4px 15px rgba(56, 189, 248, 0.4) !important;
            }
            /* Texto do Botão - Forçar visibilidade (cobre todos os wrappers internos) */
            div[data-testid="stButton"] button,
            div[data-testid="stButton"] button *,
            div[data-testid="stButton"] button [data-testid="stMarkdownContainer"],
            div[data-testid="stButton"] button [data-testid="stMarkdownContainer"] p {
                color: #0f172a !important;
                font-weight: 800 !important;
                font-size: 1.1rem !important;
                text-transform: uppercase !important;
                margin: 0 !important;
                opacity: 1 !important;
                visibility: visible !important;
                line-height: 1.2 !important;
            }
            
            /* Separador */
            .token-dash {
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100%;
                font-size: 2rem;
                color: #38bdf8;
                font-weight: 800;
                margin-top: -5px;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        # JS injetado via components.html (st.markdown remove tags <script>)
        components.html(
            """
            <script>
            (function() {
                function manageTokenInputs() {
                    const doc = window.parent.document;
                    const allInputs = Array.from(
                        doc.querySelectorAll('div[data-testid="stTextInput"] input')
                    );
                    const inputs = allInputs.filter(el => el.getAttribute('maxlength') === '1');

                    if (inputs.length < 8) return;
                    const tokenInputs = inputs.slice(0, 8);

                    tokenInputs.forEach((input, index) => {
                        if (input.dataset.managed === "true") return;

                        input.addEventListener('input', function(e) {
                            if (this.value.length > 1) {
                                this.value = this.value.slice(-1);
                            }
                            if (this.value.length === 1 && index < 7) {
                                tokenInputs[index + 1].focus();
                                tokenInputs[index + 1].select();
                            }
                        });

                        input.addEventListener('keydown', function(e) {
                            if (e.key === 'Backspace' && this.value.length === 0 && index > 0) {
                                tokenInputs[index - 1].focus();
                            } else if (e.key === 'ArrowRight' && index < 7) {
                                e.preventDefault();
                                tokenInputs[index + 1].focus();
                            } else if (e.key === 'ArrowLeft' && index > 0) {
                                e.preventDefault();
                                tokenInputs[index - 1].focus();
                            }
                        });

                        input.dataset.managed = "true";
                    });

                    // Foca o primeiro campo vazio na carga inicial
                    if (!window._tokenAutofocused) {
                        const first = tokenInputs.find(i => !i.value) || tokenInputs[0];
                        first.focus();
                        window._tokenAutofocused = true;
                    }
                }

                setInterval(manageTokenInputs, 400);
                manageTokenInputs();
            })();
            </script>
            """,
            height=0,
        )

        with st.container(border=True):
            st.markdown("<div style='padding: 15px 0;'>", unsafe_allow_html=True)
            cols = st.columns([1, 1, 1, 1, 0.5, 1, 1, 1, 1])
            t1 = cols[0].text_input("Dígito 1", max_chars=1, key="t1", label_visibility="collapsed")
            t2 = cols[1].text_input("Dígito 2", max_chars=1, key="t2", label_visibility="collapsed")
            t3 = cols[2].text_input("Dígito 3", max_chars=1, key="t3", label_visibility="collapsed")
            t4 = cols[3].text_input("Dígito 4", max_chars=1, key="t4", label_visibility="collapsed")
            cols[4].markdown("<div class='token-dash'>-</div>", unsafe_allow_html=True)
            t5 = cols[5].text_input("Dígito 5", max_chars=1, key="t5", label_visibility="collapsed")
            t6 = cols[6].text_input("Dígito 6", max_chars=1, key="t6", label_visibility="collapsed")
            t7 = cols[7].text_input("Dígito 7", max_chars=1, key="t7", label_visibility="collapsed")
            t8 = cols[8].text_input("Dígito 8", max_chars=1, key="t8", label_visibility="collapsed")
            st.markdown("</div>", unsafe_allow_html=True)
            
            token_input = f"{t1}{t2}{t3}{t4}{t5}{t6}{t7}{t8}"
            
            st.markdown("<div style='height: 12px'></div>", unsafe_allow_html=True)
            
            if st.button("Validar Código de Acesso", use_container_width=True, type="primary"):
                # Busca o token esperado no .env (Forçando leitura do arquivo local)
                try:
                    from decouple import Config, RepositoryEnv
                    env_path = Path(__file__).parent / ".env"
                    
                    if env_path.exists():
                        local_config = Config(RepositoryEnv(str(env_path)))
                        expected_token = str(local_config("SYSTEM_TOKEN", default="00000000")).strip()
                    else:
                        expected_token = str(config("SYSTEM_TOKEN", default="00000000")).strip()
                    
                    if token_input == expected_token:
                        st.session_state["authenticated"] = True
                        st.success("Acesso autorizado! Carregando dashboards...")
                        st.rerun()
                    else:
                        st.error(f"Código incorreto. Tente novamente.")
                except Exception as e:
                    st.error(f"Erro na configuração de segurança: {str(e)}")
        
        st.markdown(
            """
            <div style="text-align: center; margin-top: 40px; color: #475569; font-size: 0.8rem;">
                © 2026 Prefeitura de Nova Iguaçu • SEMED • Sistema SAEDAS
            </div>
            """,
            unsafe_allow_html=True
        )

# Verifica se o usuário já está autenticado
if not st.session_state.get("authenticated", False):
    render_login_screen()
    st.stop() # Interrompe a execução para quem não está logado

# --- Tratamento de Parâmetros de URL (Deep-linking) ---
params = st.query_params
menu_options_all = ["Início", "Encaminhamentos", "Exames", "Vacinação", "Nutrição", "Enfermagem", "Assistente Social", "Psicólogo", "Professor", "Médico", "Aluno"]

# 1. Verifica se há um parâmetro de menu na URL
menu_from_url = False
menu_param = params.get("menu")
if isinstance(menu_param, list): menu_param = menu_param[0]

if menu_param in menu_options_all:
    st.session_state["menu_escolhido"] = menu_param
    st.session_state["sidebar_main_menu"] = menu_param
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
    st.session_state["sidebar_main_menu"] = "Aluno"
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
    if menu_from_url:
        menu_escolhido = st.session_state.get("menu_escolhido", menu_escolhido)
    elif selected_menu in menu_options:
        menu_escolhido = selected_menu
        st.session_state["menu_escolhido"] = selected_menu

    # --- Rodapé da Sidebar (Botão de Sair) ---
    st.sidebar.markdown("<div style='flex-grow: 1;'></div>", unsafe_allow_html=True) # Spacer
    st.sidebar.markdown("---")
    
    # CSS específico para o botão de sair na sidebar (para ser menor e alinhado)
    st.sidebar.markdown(
        """
        <style>
        div[data-testid="stSidebar"] div.stButton > button {
            height: 35px !important;
            padding: 0 15px !important;
            background-color: transparent !important;
            border: 1px solid #334155 !important;
            color: #94a3b8 !important;
            font-size: 0.85rem !important;
            display: flex !important;
            align-items: center !important;
            justify-content: flex-start !important;
            gap: 10px !important;
        }
        div[data-testid="stSidebar"] div.stButton > button:hover {
            border-color: #ef4444 !important;
            color: #ef4444 !important;
            background-color: rgba(239, 68, 68, 0.1) !important;
        }
        div[data-testid="stSidebar"] div.stButton > button p {
            font-size: 0.85rem !important;
            font-weight: 500 !important;
            margin: 0 !important;
            color: inherit !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    if st.sidebar.button("Sair do Sistema", use_container_width=True, icon=":material/logout:"):
        st.session_state["authenticated"] = False
        st.rerun()

# --- Detecção de Mudança de Página (Proteção de Estado) ---
current_menu = menu_escolhido
last_menu = st.session_state.get("_last_active_menu")
if current_menu != last_menu:
    st.session_state["_is_page_first_run"] = True
    st.session_state["_last_active_menu"] = current_menu
else:
    st.session_state["_is_page_first_run"] = False


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
