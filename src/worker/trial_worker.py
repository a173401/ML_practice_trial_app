import pika
import json
import traceback
from uuid import UUID
from pydantic import BaseModel
from lib.trial_service import TrialService
from lib.trial import TrialController
from lib.app.settings import WorkerSettings
from lib.models.mq_events import MQEvent
from lib.database.trial_repository import TrialRepository
from lib.database.agent_response_repository import AgentResponseRepository
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
engine = create_engine(
    f"postgresql://{settings.postgres_user}:{settings.postgres_password}@{settings.postgres_host}/{settings.postgres_db}"
)

# Declare the input and output queues
try:
    channel.queue_declare(queue='trial')
    channel.exchange_declare(exchange='common_exchange', exchange_type='direct')
    channel.queue_bind(exchange='common_exchange', queue='trial', routing_key='trial')
    logging.info("Queues and exchange declared and bound")
except Exception as e:
    logging.error(f"Failed to declare queues and exchange: {e}")
    raise

# Internal queue for communication between threads
internal_queue = queue.Queue()

# Function to process the message in a separate thread
def rabbitmq_listener():
    def callback(ch, method, properties, body):
        try:
            # Parse the message body into an MQEvent object
            event = MQEvent(**json.loads(body))
            logging.info(f"Received message: {event}")
            # Put the message into the internal queue
            internal_queue.put((event, method.delivery_tag))
        except Exception as e:
            logging.error(f"Failed to parse message: {e}")
            logging.error(traceback.format_exc())
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    channel.basic_consume(queue='trial', on_message_callback=callback)
    logging.info('RabbitMQ listener started. Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

# Function to process the message from the internal queue
def message_processor():
    while True:
        try:
            event, delivery_tag = internal_queue.get()
            logging.info(f"Processing message from internal queue: {event}")

            session = Session(engine)
            trial_service = TrialService(TrialRepository(session))
            logging.info("Database session created")

            agents_response_repository = AgentResponseRepository(session)
            # Get the trial data
            trial = trial_service.get_trial_by_id(event.trial_id)
            logging.info(f"Trial retrieved: {trial}")

            # Initialize the provider
            bothub_token = settings.bothub_token
            provider = BothubProvider("https://bothub.chat/api/v2", token=bothub_token, chat_id=settings.bothub_chat_id)
            logging.info("Provider initialized")

            # Initialize the trial controller
            trial.max_rounds = 2        
            trial_controller = TrialController(TrialRepository(session), agents_response_repository, 
                                               trial, provider)
            logging.info("Trial controller initialized")

            # Start the trial
            logging.info("Trial started")
            trial_controller.start_trial()
            logging.info("Trial finished")

            channel = connection.channel()
            channel.basic_ack(delivery_tag=delivery_tag)
            channel.close()
            session.close()
            logging.info(f"Message acknowledged: {delivery_tag}")
            internal_queue.task_done()
        except Exception as e:
            logging.error(f"Failed to process message: {e}")
            logging.error(traceback.format_exc())
            internal_queue.task_done()

# Start RabbitMQ listener thread
rabbitmq_thread = threading.Thread(target=rabbitmq_listener, daemon=True)
rabbitmq_thread.start()

# Start message processor thread
processor_thread = threading.Thread(target=message_processor, daemon=True)
processor_thread.start()

# Keep the main thread alive
try:
    while True:
        internal_queue.join()
except KeyboardInterrupt:
    logging.info('Shutting down...')
    connection.close()