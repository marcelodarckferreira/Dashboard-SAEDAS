import streamlit as st

def footer_personal():
    st.markdown(
        """
    <style>
    .custom-footer {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        color: #ccc;
        text-align: center;
        background-color: #0e1117;
        padding: 10px;
        font-size: 0.85em;
        z-index: 9999;
        border-top: 1px solid #444;
    }
    </style>

    <div class="custom-footer">
        &copy; 2025 Prefeitura da Cidade de Nova Iguaçu &bull; SEMED &bull; Sistema SAEDAS
    </div>
    """,
        unsafe_allow_html=True,
    )
