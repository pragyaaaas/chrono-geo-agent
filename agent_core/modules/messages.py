import json

class BaseMessage:
    msg_class: str = "BaseMessage"

    def __init__(
            self, 
            role, 
            content="", 
            message=None, 
            prompt_tokens=None, 
            cached_tokens=None, 
            completion_tokens=None, 
            total_tokens=None, 
            time_elapsed=None, 
            tool_calls=None, 
            source=None
        ):
        """
        BaseMessage holds common attributes for all message types.
        """
        self.role = role
        self.content = content
        self.message = message
        self.prompt_tokens = prompt_tokens
        self.cached_tokens = cached_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = total_tokens
        self.time_elapsed = time_elapsed
        self.tool_calls = tool_calls
        self.source = source
        self.msg_class = self.__class__.msg_class
        # This attribute will be set on ToolResponseMessage objects
        self.tool_call_id = None

    def __str__(self):
        parts = [f"Role: {self.role}"]
        if self.content:
            parts.append(f"Content: {self.content}")
        if self.prompt_tokens is not None:
            parts.append(f"Input Tokens: {self.prompt_tokens}")
        if self.cached_tokens is not None:
            parts.append(f"Cached Tokens: {self.cached_tokens}")
        if self.completion_tokens is not None:
            parts.append(f"Output Tokens: {self.completion_tokens}")
        if self.tool_calls:
            parts.append(f"Tool Calls: {[str(tc) for tc in self.tool_calls]}")
        if self.source:
            parts.append(f"Source: {self.source}")
        if self.time_elapsed is not None:
            parts.append(f"Time Elapsed: {self.time_elapsed}")
        return " | ".join(parts)

    def to_dict(self) -> dict:
        result = {
            "msg_class": self.msg_class,
            "role": self.role,
            "content": self.content,
            "prompt_tokens": self.prompt_tokens,
            "cached_tokens": self.cached_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "time_elapsed": self.time_elapsed,
            "source": self.source,
            "tool_calls": [tc.to_dict() for tc in self.tool_calls] if self.tool_calls else None,
        }
        if self.message is not None:
            result["message"] = str(self.message)
        return result

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


class TextMessage(BaseMessage):
    msg_class: str = "TextMessage"
    def __init__(self, role, content="", **kwargs):
        super().__init__(role, content, **kwargs)
    
    def __str__(self):
        return f"TextMessage: {super().__str__()}"


class ChatResponseMessage(BaseMessage):
    msg_class: str = "ChatResponseMessage"
    def __init__(self, role, content="", **kwargs):
        super().__init__(role, content, **kwargs)
    
    def __str__(self):
        return f"ChatResponseMessage: {super().__str__()}"


class ToolCallRequestMessage(BaseMessage):
    msg_class: str = "ToolCallRequestMessage"
    def __init__(self, role, content="", **kwargs):
        super().__init__(role, content, **kwargs)
    
    def __str__(self):
        return f"ToolCallRequestMessage: {super().__str__()}"


class UserProgramToolCallRequest(BaseMessage):
    msg_class: str = "UserProgramToolCallRequest"
    def __init__(self, role, content="", **kwargs):
        super().__init__(role, content, **kwargs)
    
    def __str__(self):
        return f"UserProgramToolCallRequest: {super().__str__()}"


class ToolResponseMessage(BaseMessage):
    msg_class: str = "ToolResponseMessage"
    def __init__(self, role, content="", **kwargs):
        super().__init__(role, content, **kwargs)
    
    def __str__(self):
        return f"ToolResponseMessage: {super().__str__()}"


class HandoffMessage(BaseMessage):
    msg_class: str = "HandoffMessage"
    def __init__(self, role, content="", **kwargs):
        super().__init__(role, content, **kwargs)
    
    def __str__(self):
        return f"HandoffMessage: {super().__str__()}"


class ToolCall:
    def __init__(self, id, name, arguments, tool_type):
        self.id = id
        self.name = name
        self.arguments = arguments
        self.tool_type = tool_type

    def __str__(self):
        return f"ToolCall(id={self.id}, name={self.name}, arguments={self.arguments}, type={self.tool_type})"

    def to_dict(self) -> dict:
        # This format is compatible with OpenAI/Groq tool_calls
        if self.tool_type == 'function':
            return {
                "id": self.id,
                "type": "function",
                "function": {"name": self.name, "arguments": self.arguments},
            }
        return vars(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

class Messages:
    def __init__(self):
        self.messages = []

    def add_message(self, message: BaseMessage):
        self.messages.append(message)

    def reset_messages(self):
        self.messages = []

    def __len__(self):
        return len(self.messages)

    def __iter__(self):
        return iter(self.messages)
    
    def __getitem__(self, index):
        return self.messages[index]

    def to_list(self):
        return self.messages

    # --- THIS FUNCTION IS THE CORE OF THE FIX ---
    def get_openai_client_messages(self):
        """
        Returns messages in a format suitable for OpenAI/Groq API calls.
        This now correctly handles roles, content, and tool calls.
        """
        api_messages = []
        for msg in self.messages:
            # Start with the basic message structure
            api_msg = {"role": msg.role}

            # Add content only if it exists
            if msg.content:
                api_msg["content"] = str(msg.content)

            # If it's a tool response, it MUST have the tool_call_id
            if isinstance(msg, ToolResponseMessage) and msg.tool_call_id:
                api_msg['tool_call_id'] = msg.tool_call_id
            
            # If it's an assistant's request for a tool call, format it correctly
            elif isinstance(msg, ToolCallRequestMessage) and msg.tool_calls:
                api_msg['tool_calls'] = [tc.to_dict() for tc in msg.tool_calls]
                # Per API standards, content can be null when tool_calls are present
                if not msg.content:
                    api_msg['content'] = None

            # Ensure content is not None for user messages, even if empty
            if api_msg.get("role") == "user" and "content" not in api_msg:
                api_msg["content"] = ""

            api_messages.append(api_msg)
        return api_messages

    def get_client_messages(self, client_class):
        """
        Wrapper function. Returns the conversation messages based on the client type.
        """
        # --- ADDED GroqClient TO THIS LIST ---
        if client_class in ["OpenAIClient", "OllamaClient", "GroqClient"]:
            return self.get_openai_client_messages()
        elif client_class == "VLLMClient":
            raise ValueError(f"Unsupported client: {client_class}")
        else:
            return self.get_openai_client_messages() # Fallback to default

    def __str__(self):
        return "\n".join(str(m) for m in self.messages)

    def to_list_dict(self, start=0, end=None):
        return [message.to_dict() for message in self.messages[start:end]]