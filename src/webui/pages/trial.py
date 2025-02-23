import streamlit as st
from webui.api_client import APIClient, UnauthorizedException, NotFoundException
from webui.web_main import make_sidebar
from lib.app.models import UserRole, TrialStatusResponse, TrialResult
from lib.models.trial_dto import Trial, TrialStatus
import pandas as pd
import json

def show_active_trials(api_client: APIClient):
    st.subheader("Активные обсуждения")
    try:
        active_trials = api_client.get_active_trials()
        
        if not active_trials:
            st.info("Нет активных обсуждений")
            return
            
        for trial in active_trials:
            cols = st.columns([3, 4, 3, 2])
            cols[0].markdown(f"**ID:** {trial.trial_id}")
            cols[1].markdown(f"**Запрос:** {trial.request_id}")
            cols[2].markdown(f"**Статус:** {trial.trial_status.value}")
            
            if cols[3].button("Открыть", key=f"active_{trial.trial_id}"):
                st.session_state.current_trial = trial.trial_id
                st.switch_page("pages/trial_details.py")
                
            st.divider()
        
        if st.button("🆕 Создать новое обсуждение"):
            st.session_state.current_trial = None
            st.switch_page("pages/trial_create_form.py")
            
    except NotFoundException:
        st.info("Нет активных обсуждений")
    except Exception as e:
        st.error(f"Ошибка загрузки активных обсуждений: {str(e)}")

def show_completed_trials(api_client: APIClient):
    st.subheader("История обсуждений")
    try:
        completed_trials = api_client.get_completed_trials()
        
        if not completed_trials:
            st.info("Нет завершенных обсуждений")
            return
            
        for trial in completed_trials:
            cols = st.columns([3, 5, 3, 3, 2])
            cols[0].markdown(f"**ID:** {trial.id}")
            cols[1].markdown(f"**Описание:** {trial.summary}")
            cols[2].markdown(f"**Статус:** {trial.status.value}")
            cols[3].markdown(f"**Цена:** ${trial.final_price:.2f}")
            
            if cols[4].button("Открыть", key=f"completed_{trial.id}"):
                st.session_state.current_trial = trial.id
                st.switch_page("pages/trial_details.py")
                
            st.divider()
            
    except NotFoundException:
        st.info("Нет завершенных обсуждений")
    except Exception as e:
        st.error(f"Ошибка загрузки завершенных обсуждений: {str(e)}")

def show_page(api_client: APIClient):
    st.header("Обсуждения")
    
    tab1, tab2 = st.tabs(["Активные обсуждения", "История обсуждений"])
    
    with tab1:
        show_active_trials(api_client)
    
    with tab2:
        show_completed_trials(api_client)

make_sidebar()
if 'client' in st.session_state:
    try:
        show_page(st.session_state.client)
    except UnauthorizedException:
        st.session_state.clear()
        st.rerun()
    except Exception as error:
        st.error(f"Произошла ошибка: {str(error)}")
else:
    st.warning("Пожалуйста, авторизуйтесь для доступа к этой странице.")
    st.switch_page("web_main.py")
