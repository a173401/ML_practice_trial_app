import pika
import json
import random
import time
from uuid import UUID
from pydantic import BaseModel
from lib.user_service import UserService
from lib.trial_service import TrialService
from lib.app.settings import WorkerSettings
from lib.models.mq_events import MQEvent
from lib.database.user_account_repository import UserAccountsRepository
from lib.database.trial_repository import TrialRepository
from sqlmodel import create_engine, Session
from sqlalchemy import Engine
from lib.llm_providers.bothub_provider import BothubProvider
import boto3
from botocore.client import Config
from lib.context_builder import ContextBuilder
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load settings
settings = WorkerSettings()

# Create a connection to RabbitMQ
try:
    connection = pika.BlockingConnection(pika.ConnectionParameters(settings.rabbitmq_host, 
                                                                   credentials=pika.PlainCredentials(settings.rabbitmq_user, settings.rabbitmq_password)))
    channel = connection.channel()
    logging.info("Connected to RabbitMQ")
except Exception as e:
    logging.error(f"Failed to connect to RabbitMQ: {e}")
    raise

# Declare the input and output queues
try:
    channel.queue_declare(queue='analysis')
    channel.queue_declare(queue='trial')
    channel.exchange_declare(exchange='common_exchange', exchange_type='direct')
    channel.queue_bind(exchange='common_exchange', queue='analysis', routing_key='analysis')
    channel.queue_bind(exchange='common_exchange', queue='trial', routing_key='trial')
    logging.info("Queues and exchange declared and bound")
except Exception as e:
    logging.error(f"Failed to declare queues and exchange: {e}")
    raise


bothub_token = settings.bothub_token
random_sleep = random.uniform(0, 10)
time.sleep(random_sleep)

provider = BothubProvider("https://bothub.chat/api/v2", token=bothub_token)
provider.send_message("скажи ок")

# Function to process the message
def process_message(ch, method, properties, body):
    try:
        # Parse the message body into an MQEvent object
        event = MQEvent(**json.loads(body))
        logging.info(f"Received message: {event}")

        # Create the database engine and session
        engine = create_engine(
            f"postgresql://{settings.postgres_user}:{settings.postgres_password}@{settings.postgres_host}/{settings.postgres_db}"
        )
        session = Session(engine)
        user_service = UserService(UserAccountsRepository(session))
        trial_service = TrialService(TrialRepository(session))
        logging.info("Database session created")

        # Create the S3 client
        s3_client = boto3.client(
            's3',
            endpoint_url=settings.minio_endpoint,
            aws_access_key_id=settings.minio_access_key,
            aws_secret_access_key=settings.minio_secret_key,
            config=Config(signature_version='s3v4')
        )
        logging.info("S3 client created")

        # Get the user request
        user_request_to_process = user_service.get_user_request_by_id(str(event.user_request_id))
        logging.info(f"User request retrieved: {user_request_to_process}")

        # Initialize the provider and context builder
        
        provider.set_system_context("Тебя зовут Игорь, ты профессиональный оценщик автомобилей. Твой глаз наметан ты видишь все недостатки и тебя невозможно обмануть. Твои отчеты всегда верны и точны")
        provider.set_model("qwen-2-vl-72b-instruct")
        builder = ContextBuilder("Оценка автомобиля")
        builder.add_textual_info_section(f"Заявленная цена: {user_request_to_process.price}")
        logging.info("Provider and context builder initialized")

        # Analyze each attachment
        analysis_per_photo = []
        for i, attachment in enumerate(user_request_to_process.attachments):
            # Get the object from MinIO
            response = s3_client.get_object(Bucket=settings.minio_bucket, Key=attachment.object_name)
            # Read the file content
            file_content = response['Body'].read()
            photo_analysis = provider.send_message_with_files(
                "Дано изображение автомобиля. Напиши, что на нем изображено и оцени его состояние. Попробуй написать модель автомобиля и какая его часть видна. Эти данные пойдут в отчет.",
                ("image.png", file_content, "image/png")
            )
            builder.add_photo_analysis_section(f"Фотография {i}", photo_analysis)
            analysis_per_photo.append(photo_analysis)
            logging.info(f"Analyzed photo {i}: {photo_analysis}")

        # Analyze the advertisement text
        provider.set_model("claude-3.5-haiku")
        auto_report = user_request_to_process.description
        advertisment_data = provider.send_message(
            f"""Дано объявление по машине:
```text
{auto_report}
Оно может быть неструктурированным и иметь лишнюю информацию. Оформи его для последующего анализа оценщиками автомобилей. Никакая информация не должна потеряться. Вся информация должна быть в виде markdown, для удобства анализа людьми. Заголовки должны быть второго уровня, так как эта информация пойдет в отдельный раздел. 
""" ) 
        builder.add_textual_info_section(advertisment_data)
        logging.info(f"Analyzed advertisement text: {advertisment_data}")

        trial = trial_service.get_trial_by_id(event.trial_id)
        trial.context = builder.generate_context()
        trial_service.update_trial(trial)

        # Create a new event and publish it to the output queue
        new_event = MQEvent(user_request_id=event.user_request_id, trial_id=event.trial_id)
        channel.basic_publish(exchange='common_exchange', body=new_event.model_dump_json(), routing_key="trial")
        logging.info(f"Published new event: {new_event}")

        # Acknowledge the message
        channel.basic_ack(delivery_tag=method.delivery_tag)
        logging.info(f"Message acknowledged: {method.delivery_tag}")
    except Exception as e:
        logging.error(f"Failed to process message: {e}")

channel.basic_consume(queue='analysis', on_message_callback=process_message)

logging.info('Waiting for messages. To exit press CTRL+C') 
channel.start_consuming()