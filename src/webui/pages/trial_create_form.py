import streamlit as st
import time
from pydantic import SecretStr
from webui.api_client import APIClient, UnauthorizedException
from webui.web_main import make_sidebar
from lib.app.models import TrialRequest, Agent, Attachment
from lib.models.agent_dto import AgentType
from lib.models.trial_dto import TrialStatus
import uuid
import requests
import os
import traceback

def show_page(api_client: APIClient):
    st.header("Создание обсуждения стоимости автомобиля")
    
    # Форма для ввода данных
    with st.form("create_trial"):
        current_price = st.number_input("Цена автомобиля в объявлении", min_value=0.01, step=0.01)
        description = st.text_area("Описание объявления")
        
        # Выбор агентов для анализа
        agents = api_client.list_agents()
        selected_agents = st.multiselect("Выберите агентов для анализа", agents, default=agents)
        # Зона drag and drop для отправки фотографий автомобиля
        uploaded_files = st.file_uploader("Загрузите фотографии автомобиля", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
        
        if st.form_submit_button("Создать обсуждение"):
            try:
                # Загрузка файлов
                attachments = []
                for index, file in enumerate(uploaded_files):
                    presigned_url = api_client.get_presigned_url_for_upload(f"file_{index}.png", file.type)
                    presigned_upload_url = presigned_url['upload_url']
                    response = requests.put(presigned_upload_url, data=file)
                    response.raise_for_status()
                    attachment = presigned_url["attachment"]
                    attachments.append(attachment)
                
                # Создание запроса на создание обсуждения
                trial_request = TrialRequest(
                    current_price=current_price,
                    description=description,
                    attachments=attachments,
                    agents=[Agent(id=agent.id, name=agent.name, system_context=agent.system_context, model=agent.model, agent_type=agent.agent_type, cost_per_token=agent.cost_per_token, version=agent.version) for agent in selected_agents]
                )
                
                # Отправка запроса на создание обсуждения
                trial_status_response = api_client.request_trial(trial_request)
                st.success(f"Обсуждение успешно создано. ID запроса: {trial_status_response.request_id}")
            except Exception as e:
                st.error(f"Ошибка: {str(e)}")
                st.error(traceback.format_exc())

make_sidebar()
if 'client' in st.session_state:
    try:
        show_page(st.session_state.client)
    except Exception as error:
        if error.__class__.__name__ == UnauthorizedException.__name__: 
            st.session_state.clear()
            st.rerun()
        else:
            st.error(f"Произошла ошибка: {str(error)}")
else:
    st.warning("Пожалуйста, авторизуйтесь для доступа к этой странице.")
    time.sleep(0.5)
    st.switch_page("web_main.py")