import pika
import json
import traceback
import random
import time
from uuid import UUID
from pydantic import BaseModel
from lib.trial_service import TrialService
from lib.trial import TrialController
from lib.app.settings import WorkerSettings
from lib.models.mq_events import MQEvent
from lib.database.trial_repository import TrialRepository
from lib.database.agent_response_repository import AgentResponseRepository
from lib.database.user_account_repository import UserAccountsRepository
from lib.database.transaction_repository import TransactionRepository
from lib.user_account_service import UserAccountService, InsufficientFundsError
from lib.user_service import UserService
from sqlmodel import create_engine, Session
from sqlalchemy import Engine
from lib.llm_providers.bothub_provider import BothubProvider
import logging
import threading
import queue

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load settings
settings = WorkerSettings()

# Create a connection to RabbitMQ
try:
    connection = pika.BlockingConnection(pika.ConnectionParameters(settings.rabbitmq_host, 
                                                                   credentials=pika.PlainCredentials(settings.rabbitmq_user, 
                                                                                                     settings.rabbitmq_password),
                                                                                                     socket_timeout=300))
    channel = connection.channel()
    logging.info("Connected to RabbitMQ")
except Exception as e:
    logging.error(f"Failed to connect to RabbitMQ: {e}")
    raise

# Create the database engine


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

# Initialize the provider
bothub_token = settings.bothub_token
random_sleep = random.uniform(10, 30)
time.sleep(random_sleep)
provider = BothubProvider("https://bothub.chat/api/v2", token=bothub_token)
provider.send_message("скажи ок")

def process_message(ch, method, properties, body):
    try:
        event = MQEvent(**json.loads(body))
        logging.info(f"Received message: {event}")

        logging.info(f"Processing message from internal queue: {event}")
        engine = create_engine(
            f"postgresql://{settings.postgres_user}:{settings.postgres_password}@{settings.postgres_host}/{settings.postgres_db}"
        )
        session = Session(engine)
        trial_service = TrialService(TrialRepository(session))
        account_service = UserAccountService(UserAccountsRepository(session), 
                                             TransactionRepository(session))
        user_service = UserService(UserAccountsRepository(session))
        user_request = user_service.get_user_request_by_id(event.user_request_id)        
        account = account_service.get_user_accout_by_user_id(user_request.user_id)
        logging.info("Database session created")

        agents_response_repository = AgentResponseRepository(session)
        # Get the trial data
        trial = trial_service.get_trial_by_id(event.trial_id)
        logging.info(f"Trial retrieved: {trial}")

        # Initialize the trial controller        
        trial_controller = TrialController(TrialRepository(session), agents_response_repository, 
                                            trial, provider)
        logging.info("Trial controller initialized")

        # Start the trial
        logging.info("Trial started")
        trial_controller.start_trial()
        logging.info("Trial finished")
        total_price = trial_controller.get_trial_price()
        try:
            account_service.deduct(account, total_price, trial, user_request, "Обсуждение")
        except InsufficientFundsError:
            pass
        session.close()
        ch.basic_ack(delivery_tag=method.delivery_tag)
        logging.info(f"Message acknowledged: {method.delivery_tag}")

    except Exception as e:
        logging.error(f"Failed to process message: {e}")
        logging.error(traceback.format_exc())

channel.basic_consume(queue='trial', on_message_callback=process_message)
logging.info('RabbitMQ listener started. Waiting for messages. To exit press CTRL+C')
channel.start_consuming()
