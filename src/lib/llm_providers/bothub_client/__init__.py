# __init__.py
import time
from .client import APIClient
from .auth import AuthAPI
from .chat import ChatAPI
from .group import GroupAPI
from .job import JobAPI
from .message import MessageAPI
from .model import ModelAPI
from .plan import PlanAPI
from .preset import PresetAPI
from .referral import ReferralAPI
from .shortcut import ShortcutAPI
from .transaction import TransactionAPI
from .user import UserAPI

class API:
    def __init__(self, base_url, token=None):
        self.client = APIClient(base_url, token)
        self.auth = AuthAPI(self.client)
        self.chat = ChatAPI(self.client)
        self.group = GroupAPI(self.client)
        self.job = JobAPI(self.client)
        self.message = MessageAPI(self.client)
        self.model = ModelAPI(self.client)
        self.plan = PlanAPI(self.client)
        self.preset = PresetAPI(self.client)
        self.referral = ReferralAPI(self.client)
        self.shortcut = ShortcutAPI(self.client)
        self.transaction = TransactionAPI(self.client)
        self.user = UserAPI(self.client)
        self.token_accumulator = 0
    
    def signin(self, email: str, password: str):
        """
        Авторизация в системе.

        :param email: Электронная почта
        :param password: Пароль.
        :return: dict: Словарь с доступными данными (accessToken).
        """
        access_data = self.auth.signin({"email": email, "password": password})
        self.client.set_token(access_data["accessToken"])
        return access_data
    
    def update_system_prompt(self, chat_id: str, prompt: str) -> None:
        """
        Обновляет системный промпт в чате.

        :param chat_id: str: Идентификатор чата, в котором нужно обновить системный промпт.
        :param prompt: str: Новый системный промпт.
        """
        self.chat.update_chat_settings(chat_id, 
                                    {
                                        "name": "system_prompt",
                                        "value": prompt
                                    })
    
    def update_chat_model(self, chat_id: str, model_id: str) -> None:
        """
        Обновляет модель чата.

        :param chat_id: str: Идентификатор чата, в котором нужно обновить модель.
        :param model_id: str: Идентификатор новой модели.
        """
        self.chat.update_chat(chat_id, {"modelId": model_id})

    def set_chat_model_settings(self, chat_id: str, model_name: str) -> None:
        """
        Устанавливает конкретную модель для чата.

        :param chat_id: str: Идентификатор чата, в котором нужно установить модель.
        :param model_name: str: Название модели.
        """
        self.chat.update_chat_settings(chat_id, {"name": "model", "value": model_name})
    
    def ask_llm(self, chat_id: str, question: str, timeout: int = 180) -> str:
        """
        Отправляет вопрос в LLM (Large Language Model) и ожидает ответа.

        Эта функция отправляет сообщение с вопросом в чат, идентифицированный chat_id, 
        и ожидает ответа от LLM в течение указанного времени (timeout). Если ответ не 
        получен в течение времени ожидания, выбрасывается исключение TimeoutError.

        :param chat_id: str: Идентификатор чата, в который отправляется вопрос.
        :param question: str: Вопрос, который нужно задать LLM.
        :param timeout: int, optional: Максимальное время ожидания ответа в секундах. По умолчанию 60 секунд.
        
        :return: str: Ответ от LLM.
        
        :raises TimeoutError: Если время ожидания ответа превышено.
        """
        response = self.message.send_message(
            {
                "chatId": chat_id,
                "message": question
            })
        message_id = response.get("id", None)
        reply_string = ""
        token_amount = 0
        if message_id:
            start_time = time.time()
            reply = self.message.get_message(message_id)
            while reply["status"] != "DONE":
                if time.time() - start_time > timeout:
                    raise TimeoutError("Превышено время ожидания ответа.")
                time.sleep(1)
                reply = self.message.get_message(message_id)
            reply_string = reply["content"]
            token_amount = reply["tokens"]
        else:
            print(f"Не удалось получить данные: {response}")
        self.token_accumulator += token_amount
        self.chat.clear_chat_context(chat_id)
        return reply_string
    
    def ask_llm_with_file(self, chat_id: str, question: str, file, timeout: int = 60) -> str:
        """
        Отправляет запрос к LLM с файлом и возвращает ответ.
        :param chat_id: Идентификатор чата.
        :param question: Вопрос для отправки.
        :param file_path: Путь к файлу, который нужно отправить вместе с вопросом.
        :param timeout: Максимальное время ожидания ответа в секундах.
        :return: Ответ от LLM.
        """
        response = self.message.send_message_with_file(
            {
                "chatId": (None, chat_id),
                "message": (None, question),
                "files": file
            })
        message_id = response.get("id", None)
        reply_string = ""
        token_amount = 0
        if message_id:
            start_time = time.time()
            reply = self.message.get_message(message_id)
            while reply["status"] != "DONE":
                if time.time() - start_time > timeout:
                    raise TimeoutError("Превышено время ожидания ответа.")
                time.sleep(1)
                reply = self.message.get_message(message_id)
            reply_string = reply["content"]
            token_amount = reply["tokens"]
        else:
            print(f"Не удалось получить данные: {response}")
        self.token_accumulator += token_amount
        self.chat.clear_chat_context(chat_id)
        return reply_string
    
    def create_chat(self) -> str:
        """
        Создает новый чат и возвращает его ID.
        :return: ID нового чата.
        """
        graphql_request = {"operationName":"GetChatPageData","variables":{"includeMe": False,"includeSidebarData": False,"includeModels": False,"includeChat": True,"currentGroupId": None,"chatId": None,"initialChatModelId":"claude-3.7-sonnet","messagesQuantity":10},"query":"query GetChatPageData($includeMe: Boolean!, $includeSidebarData: Boolean!, $currentGroupId: String, $chatId: String, $initialChatModelId: String, $messagesQuantity: Int!, $includeChat: Boolean!, $includeModels: Boolean!) {\n  me @include(if: $includeMe) {\n    ...UserFragment\n    __typename\n  }\n  groups(page: 1, search: \"\", sort: null, sortDirection: \"DESC\") @include(if: $includeSidebarData) {\n    ...GroupsFragment\n    __typename\n  }\n  chats(\n    page: 1\n    groupId: null\n    search: \"\"\n    sort: null\n    sortDirection: \"DESC\"\n    quantity: 20\n  ) @include(if: $includeSidebarData) {\n    ...ChatsFragment\n    __typename\n  }\n  groupChats: chats(page: 1, groupId: $currentGroupId) @include(if: $includeSidebarData) {\n    ...ChatsFragment\n    __typename\n  }\n  models(platform: \"WEB\") @include(if: $includeModels) {\n    id\n    label\n    icon_id\n    icon {\n      ...FileFragment\n      __typename\n    }\n    created_at\n    owned_by\n    parent_id\n    disabled\n    order\n    functions {\n      id\n      name\n      label\n      is_default\n      model_id\n      features\n      created_at\n      __typename\n    }\n    features\n    max_tokens\n    is_allowed\n    allowed_plan_type\n    is_default\n    message_color\n    __typename\n  }\n  chat(chatId: $chatId, modelId: $initialChatModelId) @include(if: $includeChat) {\n    ...ChatFragment\n    settings(all: false, elements: true, platform: \"WEB\") {\n      ...ChatSettingsFragment\n      __typename\n    }\n    messages(page: 1, quantity: $messagesQuantity) {\n      ...MessageFragment\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment UserFragment on User {\n  id\n  avatar\n  tg_id\n  receiveEmails\n  hadSubscriptedForEmails\n  email\n  name\n  role\n  employees {\n    id\n    user_id\n    role\n    enterprise_id\n    enterprise {\n      id\n      name\n      created_at\n      common_pool\n      subscription {\n        id\n        plan_id\n        payment_plan\n        balance\n        credit_limit\n        created_at\n        plan {\n          id\n          type\n          price\n          currency\n          tokens\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  subscription {\n    id\n    plan_id\n    user_id\n    payment_plan\n    balance\n    credit_limit\n    created_at\n    plan {\n      id\n      type\n      price\n      currency\n      tokens\n      __typename\n    }\n    __typename\n  }\n  useEncryption\n  __typename\n}\n\nfragment GroupsFragment on GroupsList {\n  data {\n    id\n    name\n    highlight\n    order\n    user_id\n    created_at\n    __typename\n  }\n  pages\n  __typename\n}\n\nfragment ChatsFragment on ChatsList {\n  data {\n    id\n    name\n    group_id\n    model_id\n    model_function_id\n    user_id\n    initial\n    platform\n    total_caps\n    order\n    highlight\n    created_at\n    __typename\n  }\n  pages\n  __typename\n}\n\nfragment ChatFragment on Chat {\n  id\n  name\n  group_id\n  model_id\n  model {\n    ...ModelFragment\n    __typename\n  }\n  model_function_id\n  model_function {\n    ...ModelFunctionFragment\n    __typename\n  }\n  user_id\n  initial\n  platform\n  total_caps\n  order\n  highlight\n  created_at\n  __typename\n}\n\nfragment ModelFragment on Model {\n  id\n  label\n  icon_id\n  icon {\n    ...FileFragment\n    __typename\n  }\n  created_at\n  owned_by\n  parent_id\n  parent {\n    id\n    label\n    icon_id\n    icon {\n      ...FileFragment\n      __typename\n    }\n    created_at\n    owned_by\n    disabled\n    order\n    functions {\n      id\n      name\n      label\n      is_default\n      model_id\n      features\n      created_at\n      __typename\n    }\n    features\n    max_tokens\n    is_allowed\n    allowed_plan_type\n    is_default\n    message_color\n    __typename\n  }\n  disabled\n  order\n  functions {\n    id\n    name\n    label\n    is_default\n    model_id\n    features\n    created_at\n    __typename\n  }\n  features\n  max_tokens\n  is_allowed\n  allowed_plan_type\n  is_default\n  message_color\n  __typename\n}\n\nfragment FileFragment on File {\n  id\n  type\n  name\n  url\n  path\n  size\n  isEncrypted\n  created_at\n  __typename\n}\n\nfragment ModelFunctionFragment on ModelFunction {\n  id\n  name\n  label\n  is_default\n  model_id\n  features\n  created_at\n  __typename\n}\n\nfragment MessageFragment on Message {\n  id\n  role\n  action_type\n  status\n  choiced\n  version\n  previous_version_id\n  next_version_id\n  model_id\n  model {\n    ...ModelFragment\n    __typename\n  }\n  model_version\n  content\n  reasoning_content\n  reasoning_time_ms\n  search_status\n  search_results\n  set {\n    id\n    choiced\n    chat_id\n    length\n    __typename\n  }\n  chat_id\n  user_id\n  tokens\n  disabled\n  created_at\n  transaction_id\n  transaction {\n    ...TransactionFragment\n    __typename\n  }\n  request_id\n  images {\n    ...MessageImageFragment\n    __typename\n  }\n  buttons {\n    ...MessageButtonFragment\n    __typename\n  }\n  attachments {\n    id\n    message_id\n    file_id\n    file {\n      ...FileFragment\n      __typename\n    }\n    __typename\n  }\n  voice_id\n  voice {\n    id\n    content\n    wave_data\n    duration\n    file_id\n    file {\n      ...FileFragment\n      __typename\n    }\n    __typename\n  }\n  job_id\n  job {\n    id\n    name\n    status\n    is_stop_allowed\n    progress\n    error\n    error_code\n    mj_remaining_timeout\n    __typename\n  }\n  __typename\n}\n\nfragment MessageImageFragment on MessageImage {\n  id\n  status\n  message_id\n  width\n  height\n  preview_width\n  preview_height\n  original_id\n  original {\n    ...FileFragment\n    __typename\n  }\n  preview_id\n  preview {\n    ...FileFragment\n    __typename\n  }\n  buttons {\n    ...MessageButtonFragment\n    __typename\n  }\n  created_at\n  __typename\n}\n\nfragment MessageButtonFragment on MessageButton {\n  id\n  type\n  action\n  mj_native_custom\n  mj_native_label\n  disabled\n  message_id\n  parent_message_id\n  parent_image_id\n  created_at\n  __typename\n}\n\nfragment TransactionFragment on Transaction {\n  id\n  provider\n  amount\n  currency\n  status\n  type\n  plan_id\n  user_id\n  created_at\n  external_id\n  __typename\n}\n\nfragment ChatSettingsFragment on ChatSettings {\n  id\n  created_at\n  elements {\n    ... on ChatSettingsTextElement {\n      id\n      code\n      name\n      type\n      field_type\n      value\n      reload_on_update\n      __typename\n    }\n    ... on ChatSettingsTextAreaElement {\n      id\n      code\n      name\n      type\n      field_type\n      value\n      reload_on_update\n      __typename\n    }\n    ... on ChatSettingsSelectElement {\n      id\n      code\n      name\n      type\n      field_type\n      value\n      reload_on_update\n      data {\n        id\n        code\n        value\n        label\n        disabled\n        __typename\n      }\n      __typename\n    }\n    ... on ChatSettingsRangeElement {\n      id\n      code\n      name\n      type\n      field_type\n      rangeValue: value\n      min\n      max\n      step\n      reload_on_update\n      __typename\n    }\n    ... on ChatSettingsPresetSelectElement {\n      id\n      code\n      name\n      type\n      field_type\n      preset_id: value\n      custom_type\n      reload_on_update\n      presetData: data {\n        preset {\n          id\n          name\n          description\n          system_prompt\n          access\n          usage_count\n          created_at\n          __typename\n        }\n        __typename\n      }\n      __typename\n    }\n    ... on ChatSettingsModelSelectElement {\n      id\n      code\n      name\n      type\n      field_type\n      model_id: value\n      custom_type\n      reload_on_update\n      model: data {\n        ...ModelFragment\n        __typename\n      }\n      __typename\n    }\n    ... on ChatSettingsFilesElement {\n      id\n      code\n      name\n      type\n      field_type\n      custom_type\n      reload_on_update\n      files: value {\n        ...FileFragment\n        __typename\n      }\n      __typename\n    }\n    ... on ChatSettingsCheckboxElement {\n      id\n      code\n      name\n      type\n      field_type\n      checked\n      reload_on_update\n      __typename\n    }\n    __typename\n  }\n  text {\n    id\n    model\n    system_prompt\n    temperature\n    max_tokens\n    top_p\n    frequency_penalty\n    presence_penalty\n    system_prompt_tokens\n    analyze_urls\n    enable_web_search\n    include_context\n    created_at\n    __typename\n  }\n  image {\n    id\n    model\n    quality\n    size\n    style\n    created_at\n    __typename\n  }\n  speech {\n    id\n    model\n    voice\n    speed\n    response_format\n    created_at\n    __typename\n  }\n  mj {\n    id\n    mode\n    version\n    style\n    quality\n    chaos\n    stylize\n    weird\n    stop\n    aspect\n    no\n    tile\n    created_at\n    __typename\n  }\n  __typename\n}"}
        response = self.client.post("/graphql", data=graphql_request)
        return response["data"]["chat"]["id"]

    def delete_chat(self, chat_id):
        """
        Удаление чата по ID.
        """
        self.client.delete_with_body("/chat", {"ids": [chat_id]})
        