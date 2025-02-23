import streamlit as st
import time
from pydantic import SecretStr
from api_client import APIClient
from pages.auth import show_auth_forms
from lib.app.models import UserResponse, UserRole
from webui.settings import WebSettings

def make_sidebar():
    with st.sidebar:
        user: UserResponse = st.session_state.get("user", False)
        if user:
            if user.role == UserRole.USER:
                st.page_link("pages/account.py", label="Аккаунт", icon="👤")
                st.page_link("pages/trial.py", label="Обсуждение", icon="🗣️")
            if user.role == UserRole.ADMIN:
                st.page_link("pages/admin.py", label="Администрирование", icon="⚙️")
            if st.button("Выйти"):
                st.write("Выходим...")
                time.sleep(0.5)
                st.session_state.clear()
                st.switch_page("web_main.py")

def main():
    if 'client' not in st.session_state:
        settings = WebSettings()
        st.session_state.client = APIClient(settings.backend_url)
    st.set_page_config(page_title="Иван.Иваныч.", layout="wide")
    if 'user' not in st.session_state:
        show_auth_forms(st.session_state.client) 
    else:
        if st.session_state.user.role == UserRole.USER:
            st.switch_page("pages/account.py")
        else:
            st.switch_page("pages/admin.py")

if __name__ == "__main__":
    main()