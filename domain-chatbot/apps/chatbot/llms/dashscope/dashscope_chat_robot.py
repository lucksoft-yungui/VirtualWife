import logging
import os
from typing import List

from litellm import completion

from ...memory.zep.zep_memory import ChatHistroy
from ...utils.chat_message_utils import format_chat_text
from ...utils.str_utils import remove_spaces_and_tabs

logger = logging.getLogger(__name__)


class DashScopeGeneration:
    """
    使用阿里云百炼 DashScope 兼容 OpenAI 接口的生成实现。
    """
    temperature: float = 0.7
    model_name: str
    dashscope_api_key: str
    dashscope_base_url: str

    def __init__(self) -> None:
        from dotenv import load_dotenv
        load_dotenv()
        self.dashscope_api_key = os.environ.get('DASHSCOPE_API_KEY', '')
        self.dashscope_base_url = os.environ.get(
            'DASHSCOPE_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
        self.model_name = os.environ.get('DASHSCOPE_MODEL_NAME', 'qwen-max')

    def chat(self, prompt: str, role_name: str, you_name: str, query: str,
             short_history: list[ChatHistroy], long_history: str) -> str:
        prompt = prompt + query
        messages = [{"content": prompt, "role": "user"}]
        response = completion(
            model=self.model_name,
            messages=messages,
            api_base=self.dashscope_base_url,
            api_key=self.dashscope_api_key,
            custom_llm_provider="openai",
            temperature=self.temperature,
        )
        llm_result_text = response.choices[0].message.content if response.choices else ""
        return llm_result_text

    async def chatStream(self,
                         prompt: str,
                         role_name: str,
                         you_name: str,
                         query: str,
                         history: list[str, str],
                         realtime_callback=None,
                         conversation_end_callback=None):
        messages = []
        messages.append({'role': 'system', 'content': prompt})
        for item in history:
            messages.append({"role": "user", "content": item["human"]})
            messages.append({"role": "assistant", "content": item["ai"]})
        messages.append({'role': 'user', 'content': you_name + "说" + query})

        response = completion(
            model=self.model_name,
            messages=messages,
            api_base=self.dashscope_base_url,
            api_key=self.dashscope_api_key,
            custom_llm_provider="openai",
            stream=True,
            temperature=self.temperature,
        )

        answer = ''
        for event in response:
            if not isinstance(event, dict):
                event = event.model_dump()
            if isinstance(event['choices'], List) and len(event['choices']) > 0:
                event_text = event["choices"][0]['delta']['content']
                if isinstance(event_text, str) and event_text != "":
                    content = remove_spaces_and_tabs(event_text)
                    if content == "":
                        continue
                    answer += content
                    if realtime_callback:
                        realtime_callback(role_name, you_name, content, False)

        answer = format_chat_text(role_name, you_name, answer)
        if conversation_end_callback:
            realtime_callback(role_name, you_name, "", True)
            conversation_end_callback(role_name, answer, you_name, query)
