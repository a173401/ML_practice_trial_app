import streamlit as st
from pydantic import SecretStr
from webui.api_client import APIClient

def show_auth_forms(api_client: APIClient):
    if 'active_form' not in st.session_state:
        st.session_state.active_form = 'login'
    
    login_expanded = st.session_state.active_form == 'login'
    register_expanded = st.session_state.active_form == 'register'

    with st.expander("Авторизация", expanded=login_expanded):
        with st.form("login_form"):
            username = st.text_input("Логин")
            password = st.text_input("Пароль", type="password")
            submit_login = st.form_submit_button("Войти")
            
            if submit_login:
                try:
                    response = api_client.login(
                        username=username,
                        password=SecretStr(password)
                    )
                    st.session_state.token = response.access_token
                    st.session_state.user = api_client.get_user()
                    st.rerun()
                except Exception as e:
                    st.error(f"Ошибка авторизации: {str(e)}")
            
            if st.form_submit_button("Нет аккаунта? Зарегистрироваться"):
                st.session_state.active_form = 'register'
                st.rerun()

    with st.expander("Регистрация", expanded=register_expanded):
        with st.form("register_form"):
            new_username = st.text_input("Логин")
            new_email = st.text_input("Email")
            new_password = st.text_input("Пароль", type="password")
            submit_register = st.form_submit_button("Зарегистрироваться")
            
            if submit_register:
                try:
                    response = api_client.register(
                        username=new_username,
                        password=SecretStr(new_password),
                        email=new_email
                    )
                    st.success("Регистрация прошла успешно! Теперь вы можете войти")
                    st.session_state.active_form = 'login'
                    st.rerun()
                except Exception as e:
                    st.error(f"Ошибка регистрации: {str(e)}")
            
            if st.form_submit_button("Уже есть аккаунт? Войти"):
                st.session_state.active_form = 'login'
                st.rerun()
