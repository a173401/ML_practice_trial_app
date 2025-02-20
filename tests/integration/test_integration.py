import os
import requests
import pytest
from sqlmodel import Session
from lib.models.user_account_dto import UserRole
from lib.app.models import TrialRequest
from init_db import init_db

def test_integration():
    BASE_URL = "http://localhost:8080"
    
    user_create_request = {
        "username": "testuser",
        "password": "testpassword",
        "email": "testuser@example.com",
        "role": UserRole.USER.value
    }


    login_request = {
        "username": user_create_request["username"],
        "password": user_create_request["password"]
    }
    response = requests.post(f"{BASE_URL}/auth/login", json=login_request)
    if response.status_code != 200:
        response = requests.post(f"{BASE_URL}/auth/register", json=user_create_request)
        response = requests.post(f"{BASE_URL}/auth/login", json=login_request)

    token_data = response.json()
    token = token_data["access_token"]

    # Путь к директории с файлами
    directory_path = 'test_data/'

    # Получаем список всех файлов в директории
    files = os.listdir(directory_path)

    # Фильтруем только файлы с расширением .png
    png_files = [f for f in files if f.endswith('.png')]

    # Список для хранения данных из attachment_data.json()["attachment"]
    attachments_info = []

    # Проходим по каждому файлу и загружаем его
    for file_name in png_files:
        # Полный путь к файлу
        file_path = os.path.join(directory_path, file_name)
        
        # Получаем presigned_upload_url для каждого файла
        attachment_data = requests.post(f"{BASE_URL}/attachments/upload-url", 
                                        params={"file_name": file_name, "content_type": "image/png"}, 
                                        headers={"X-token": token})
        
        presigned_upload_url = attachment_data.json()["upload_url"]
        
        # Сохраняем данные из attachment_data.json()["attachment"] в список
        attachments_info.append(attachment_data.json()["attachment"])
        
        presigned_upload_url = presigned_upload_url.replace("minio", "localhost")
        # Открываем файл в бинарном режиме
        with open(file_path, 'rb') as file:
            # Выполняем PUT-запрос на presigned_upload_url с содержимым файла
            response = requests.put(presigned_upload_url, data=file)
        
        # Проверяем успешность загрузки
        if response.status_code == 200:
            print(f"Файл {file_name} успешно загружен в S3.")
        else:
            print(f"Ошибка при загрузке файла {file_name}: {response.status_code} - {response.text}")
    response = requests.get(f"{BASE_URL}/agents/list", headers={"X-token": token})
    agents_data = response.json()

    trial_request = TrialRequest(
    current_price=2670000,
    description="""
        Характеристики.
        Год выпуска: 2017
        Поколение: I рестайлинг (2016—2020)
        Пробег: 138 300 км
        История пробега: 19 записей в отчёте Автотеки
        Владельцев по ПТС: 2
        Состояние: Не битый
        Модификация: 3.0 D 4WD AT (250 л.с.)
        Объём двигателя: 3 л
        Тип двигателя: Дизель
        Коробка передач: Автомат
        Привод: Полный
        Тип кузова: Внедорожник 5-дверный
        Цвет: Белый
        Руль: Левый
        VIN или номер кузова: XWEK*************
        Обмен: Возможен
            Описание.
        2 сoбствeнникa
        Нe иcпользовался в кoммеpческих пеpевозкaх (тaкcи, кapшeринг)
        Отличноe тeхничecкoе coстояниe
        Пpoзpaчная история обслуживaния
        ПTC oригинал
        7 местный сaлон
        Автoмoбиль c пpoбeгом oт oфициального дилeрa KIA «У Ceрвиc+».
        Данный aвтомoбиль пpoшeл юpидическую проверку, а также комплексную диагностику. При покупке Вы получаете лист с заключением о состоянии автомобиля.
        - Автомобиль прошел диагностику и предпродажную подготовку.
        - Гарантия юридической чистоты.
        - Автомобиль можно приобрести за наличный расчет, безналичным платежом.
        - Трейд-ин — обмен Вашего автомобиля на любой представленный автомобиль с пробегом в нашем салоне.
        - Страхование КАСКО, ОСАГО.
        - Кредитование (возможно без первоначального взноса).
        - Оформление кредита по двум документам.
        - КАСКО не обязательно.
        - Мы гарантируем безопасность сделки и правильное оформление всех необходимых документов.

        Работаем ежедневно, без праздников и выходных с 9:00 до 21:00
        Более подробную информацию Вы можете получить у менеджеров по продаже автомобилей с пробегом по указанному номеру в объявлении.
        """,
        attachments=attachments_info,
        agents=agents_data)
    headers = {"X-Token": token}
    response = requests.post(f"{BASE_URL}/trials/trial", json=trial_request.model_dump(mode='json'), headers=headers)


    

    