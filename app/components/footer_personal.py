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
        color: var(--text-muted);
        text-align: center;
        background-color: var(--surface-elevated);
        padding: 10px;
        font-size: 0.85em;
        z-index: 9999;
        border-top: 1px solid var(--border-ui);
    }
    </style>

    <div class="custom-footer">
        &copy; 2026 Prefeitura da Cidade de Nova Iguaçu &bull; SEMED &bull; Sistema SAEDAS
    </div>
    """,
        unsafe_allow_html=True,
    )
