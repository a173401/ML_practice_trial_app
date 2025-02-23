import streamlit as st
from webui.api_client import APIClient, UnauthorizedException, NotFoundException
from webui.web_main import make_sidebar
from lib.models.trial_dto import Trial, TrialStatus
from lib.models.agent_dto import Agent, AgentType, AgentResponse

def display_chat_message(response: AgentResponse):
    agent_type_icons = {
        AgentType.OPTIMIST: "😊",
        AgentType.PESSIMIST: "😟",
        AgentType.COORDINATOR: "👔"
    }
    
    agent_type_colors = {
        AgentType.OPTIMIST: "#E8F5E9",
        AgentType.PESSIMIST: "#FFEBEE",
        AgentType.COORDINATOR: "#E3F2FD"
    }
    
    with st.chat_message(
        name=f"{agent_type_icons[response.agent_type]} {response.agent_name}",
        avatar=agent_type_icons[response.agent_type]
    ):
        st.markdown(f"**{response.agent_name}** ({response.agent_type.value})")
        st.write(response.response)
        st.caption(f"Стоимость: {response.cost:.4f}")

def show_trial_details(api_client: APIClient):
    if 'current_trial' not in st.session_state or not st.session_state.current_trial:
        st.error("Обсуждение не выбрано")
        st.switch_page("pages/trial.py")
        return
    
    try:
        trial: Trial = api_client.get_trial_by_id(st.session_state.current_trial)
        
        st.header(f"Детали обсуждения #{trial.id}")
        st.markdown(f"**Статус:** {trial.status.value} | **Текущий раунд:** {trial.current_round}/{trial.max_rounds}")
        
        if trial.status == TrialStatus.COMPLETED:
            st.success(f"Финальная цена: ₽{trial.final_price:.2f}")
            st.markdown(f"**Итоговое резюме:** {trial.summary}")
        
        st.subheader("История обсуждения")
        sorted_responses = sorted(trial.communication_history, key=lambda x: x.created_at)

        for response in sorted_responses:
            display_chat_message(response)
        
        if st.button("Вернуться к списку обсуждений"):
            st.session_state.current_trial = None
            st.switch_page("pages/trial.py")
            
    except NotFoundException:
        st.error("Обсуждение не найдено")
        st.session_state.current_trial = None
        st.switch_page("pages/trial.py")
    except Exception as e:
        st.error(f"Ошибка загрузки деталей обсуждения: {str(e)}")

make_sidebar()
if 'client' in st.session_state:
    try:
        show_trial_details(st.session_state.client)
    except UnauthorizedException:
        st.session_state.clear()
        st.rerun()
else:
    st.warning("Пожалуйста, авторизуйтесь для доступа к этой странице.")
    st.switch_page("web_main.py")