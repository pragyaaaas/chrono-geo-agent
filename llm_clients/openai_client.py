# It's a good practice to rename the file to groq_client.py, but for now, we'll just change the class.
import time
from groq import Groq
from llm_clients.base_client import BaseClient
from agent_core.modules.messages import ChatResponseMessage, ToolCall, ToolCallRequestMessage

# CHANGE 1: Renamed the class for clarity.
class GroqClient(BaseClient):
    # CHANGE 2: Updated the client class name string.
    client_class: str = "GroqClient"

    def __init__(self, model, temperature=0.1, api_key=None, **kwargs):
        """
        Initialize the Groq client.

        Args:
            model (str): The model name (e.g., "llama3-70b-8192").
            api_key (str, optional): Your Groq API key.
            **kwargs: Additional parameters.
        """
        super().__init__(model, temperature, **kwargs)
        self.api_key = api_key
        # CHANGE 3: Initialize the Groq client instead of OpenAI and pass the API key.
        self.api_client = Groq(api_key=self.api_key)

    def get_response(self, messages, tools=None):
        """
        Send the conversation history (and tools, if provided) to 
        Groq's API and return the response.

        Args:
            messages (list): Conversation history.
            tools (list, optional): Tool specifications.

        Returns:
            dict: A dictionary with keys like "response", "prompt_tokens", "completion_tokens".
        """
        start_time = time.time()
        response = self.api_client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            temperature=self.temperature,
        )
        elapsed_time = round(time.time() - start_time, 4)
        if tools is not None and response.choices[0].message.tool_calls:
            message_type = ToolCallRequestMessage
            response_tool_calls = []
            for tool in response.choices[0].message.tool_calls:
                tool_call = ToolCall(
                    id=tool.id,
                    name=tool.function.name,
                    arguments=tool.function.arguments,
                    tool_type=tool.type
                )
                response_tool_calls.append(tool_call)
        else:
            message_type = ChatResponseMessage
            response_tool_calls = None
    
        response_message = message_type(
            role='assistant', 
            content=response.choices[0].message.content,
            message=response.choices[0].message,
            prompt_tokens=response.usage.prompt_tokens,
            # CHANGE 4: The Groq API does not return 'cached_tokens'. Set it to 0 to avoid an error.
            cached_tokens=0,
            completion_tokens=response.usage.completion_tokens,
            total_tokens=response.usage.total_tokens,
            time_elapsed=elapsed_time,
            tool_calls=response_tool_calls,
            source=self.client_info()
        )
        return response_message

    def to_dict(self):
        return {
            'client_class': self.client_class,
            'model': self.model,
            'temperature': self.temperature
        }