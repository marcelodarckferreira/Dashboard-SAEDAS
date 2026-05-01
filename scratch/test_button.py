import streamlit as st

st.button("Line 1\nLine 2", key="test_btn")
st.markdown("<style>div[data-testid='stButton'] button { white-space: pre-wrap !important; height: 100px; }</style>", unsafe_allow_html=True)
