import streamlit as st
import time
import pandas as pd
import json
from pydantic import SecretStr
from lib.app.models import UserResponse
from webui.api_client import APIClient, UnauthorizedException
from webui.web_main import make_sidebar

def show_page(api_client: APIClient):
    st.header("Личный кабинет")
    
    # Информация о пользователе
    user: UserResponse = st.session_state.user
    col1, col2, col3 = st.columns([3,3,2])
    account = api_client.get_current_account()
    with col3:
        st.markdown(f"""
        **Логин:** {user.username}  
        **Роль:** {user.role.value}  
        **Баланс:** {account.balance}
        """)
    
    # Смена пароля
    with st.expander("Смена пароля"):
        with st.form("change_password"):
            old_pass = st.text_input("Старый пароль", type="password")
            new_pass = st.text_input("Новый пароль", type="password")
            if st.form_submit_button("Изменить пароль"):
                try:
                    api_client.change_password(
                        old_password=SecretStr(old_pass),
                        new_password=SecretStr(new_pass)
                    )
                    st.success("Пароль успешно изменен")
                except Exception as e:
                    st.error(f"Ошибка: {str(e)}")
    
    # Пополнение баланса
    with st.expander("Пополнение баланса"):
        with st.form("deposit_balance"):
            amount = st.number_input("Сумма пополнения", min_value=0.01, step=0.01)
            description = st.text_input("Описание пополнения")
            if st.form_submit_button("Пополнить баланс"):
                try:
                    api_client.deposit_current_account(amount, description)
                    st.success("Баланс успешно пополнен")
                    # Обновляем информацию о балансе
                    time.sleep(3)
                    st.rerun()
                except Exception as e:
                    st.error(f"Ошибка: {str(e)}")
    
    # История транзакций
    st.subheader("История операций")
    try:
        transactions = api_client.get_user_transactions()
        # Преобразуем список транзакций в DataFrame
        if transactions:
            df = pd.DataFrame([json.loads(t.model_dump_json()) for t in transactions])
            # Определяем цвета для строк в зависимости от типа операции
            def color_row(row):
                if row['operation_type'] in ['deposit', 'admin_deposit']:
                    return ['background-color: green'] * len(row)
                elif row['operation_type'] == 'user_request':
                    return ['background-color: red'] * len(row)
                else:
                    return ['background-color: white'] * len(row)
            # Применяем цветовую разметку к DataFrame
            df = df[["created_at", "operation_type", "amount", "description"]]
            styled_df = df.style.apply(color_row, axis=1)
            
            # Конфигурация колонок
            column_config = {
                "created_at": st.column_config.DatetimeColumn(
                    "Дата и время",
                    format="DD.MM.YYYY HH:mm:ss"
                ),
                "operation_type": st.column_config.TextColumn(
                    "Тип операции"
                ),
                "amount": st.column_config.NumberColumn(
                    "Сумма",
                    format="%.2f"
                ),
                "description": st.column_config.TextColumn(
                    "Описание"
                )
            }
            
            # Отображаем DataFrame в Streamlit с конфигурацией колонок
            st.dataframe(styled_df, column_config=column_config, use_container_width=True)
        else:
            st.info("Нет операций для отображения")
    except Exception as e:
        st.error(f"Ошибка загрузки операций: {str(e)}")

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
