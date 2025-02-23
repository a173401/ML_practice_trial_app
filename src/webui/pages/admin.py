import streamlit as st
import pandas as pd
from uuid import UUID
from lib.models.user_account_dto import UserRole
from webui.api_client import APIClient, UnauthorizedException
from webui.web_main import make_sidebar
import json

def show_page(api_client: APIClient):
    st.header("Панель администратора")
    
    try:
        users = api_client.get_users()
        accounts = api_client.get_all_accounts()
        
        tab_users, tab_transactions = st.tabs(["Управление пользователями", "Все транзакции"])
        
        with tab_users:
            users_df = pd.DataFrame([json.loads(u.model_dump_json()) for u in users])
            accounts_df = pd.DataFrame([json.loads(a.model_dump_json()) for a in accounts])
            
            merged_df = pd.merge(users_df, accounts_df, left_on='id', how='left', right_on='user_id', suffixes=('', '_account'))
            merged_df = merged_df.drop(columns=['user_id'])
            merged_df.insert(0, 'selected', False)
            
            column_config = {
                "selected": st.column_config.CheckboxColumn("Выбран"),
                "username": st.column_config.TextColumn("Имя пользователя"),
                "email": st.column_config.TextColumn("Email"),
                "id": st.column_config.TextColumn("ID"),
                "disabled": st.column_config.CheckboxColumn("Заблокирован"),
                "balance": st.column_config.NumberColumn("Баланс", format="%.2f")
            }
            
            edited_df = st.data_editor(merged_df, column_config=column_config, use_container_width=True, num_rows="dynamic")
            
            selected_users = edited_df[edited_df['selected']]
            
            if not selected_users.empty:
                selected_user = selected_users.iloc[0]
                
                if not selected_user['disabled']:
                    if st.button("Заблокировать", key="disable_user"):
                        api_client.disable_user(UUID(selected_user['id']))
                        st.rerun()
                else:
                    if st.button("Активировать", key="enable_user"):
                        api_client.enable_user(UUID(selected_user['id']))
                        st.rerun()
                
                top_up_amount = st.number_input("Сумма пополнения", min_value=0.0, value=0.0, step=0.01, key="top_up_amount")
                
                if top_up_amount > 0:
                    description = st.text_input("Описание пополнения", key="top_up_description") or ""
                    if st.button("Пополнить баланс", key="top_up_balance"):
                        api_client.deposit_user_account(UUID(selected_user['id']), top_up_amount, description)
                        st.rerun()
            else:
                st.info("Выберите пользователя для управления его статусом или пополнения баланса.")
        
        with tab_transactions:
            st.subheader("История транзакций всех пользователей")
            
            all_transactions = []
            only_users = [user for user in users if user.role == UserRole.USER]
            for user in only_users:
                try:
                    transactions = api_client.get_user_transactions_by_id(user.id)
                    for t in transactions:
                        t_data = json.loads(t.model_dump_json())
                        t_data['user_id'] = str(user.id)
                        t_data['username'] = user.username
                        all_transactions.append(t_data)
                except Exception as e:
                    st.error(f"Ошибка получения транзакций для {user.username}: {str(e)}")
            
            if not all_transactions:
                st.info("Нет данных о транзакциях")
            else:
                df = pd.DataFrame(all_transactions)
                
                def color_row(row):
                    colors = {
                        'deposit': 'green',
                        'admin_deposit': 'green',
                        'request': 'red'
                    }
                    color = colors.get(row['operation_type'], 'white')
                    return [f'background-color: {color}'] * len(row)
                
                styled_df = df.style.apply(color_row, axis=1)
                
                column_config = {
                    "created_at": st.column_config.DatetimeColumn(
                        "Дата и время",
                        format="DD.MM.YYYY HH:mm:ss"
                    ),
                    "username": st.column_config.TextColumn("Пользователь"),
                    "operation_type": st.column_config.TextColumn("Тип операции"),
                    "amount": st.column_config.NumberColumn(
                        "Сумма",
                        format="%.2f"
                    ),
                    "description": st.column_config.TextColumn("Описание")
                }
                
                st.dataframe(
                    styled_df,
                    column_order=["created_at", "username", "operation_type", "amount", "description"],
                    column_config=column_config,
                    use_container_width=True
                )
                
    except Exception as e:
        st.error(f"Ошибка загрузки данных: {str(e)}")

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
    st.switch_page("web_main.py")
