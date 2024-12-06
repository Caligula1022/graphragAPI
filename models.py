import time
from typing import List, Optional
import uuid
from pydantic import BaseModel, Field


class Message(BaseModel):
    role: str = "assistant"
    content: str


class QueryOptions(BaseModel):
    query_type: str
    # preset: Optional[str] = None
    community_level: Optional[int] = 2
    # response_type: Optional[str] = None
    # custom_cli_args: Optional[str] = None
    selected_folder: Optional[str] = None


class ChatCompletionRequest(BaseModel):
    model: str
    # messages: List[Message]
    query: str
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 4096
    stream: Optional[bool] = False
    query_options: Optional[QueryOptions] = None


class ChatCompletionResponseChoice(BaseModel):
    index: int
    message: Message
    finish_reason: Optional[str] = None


class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    id: str = Field(default_factory=lambda: f"chatcmpl-{uuid.uuid4().hex}")
    object: str = "chat.completion"
    created: int = Field(default_factory=lambda: int(time.time()))
    model: str
    choices: List[ChatCompletionResponseChoice]
    usage: Usage
    system_fingerprint: Optional[str] = None


class IndexingRequest(BaseModel):
    api_key: str
    llm_model: str
    embed_model: str
    llm_api_base: str
    embed_api_base: str
    root: str
    verbose: bool = False
    nocache: bool = False
    resume: Optional[str] = None
    reporter: str = "rich"
    emit: List[str] = ["parquet"]
    # custom_args: Optional[str] = None
    # llm_params: Dict[str, Any] = Field(default_factory=dict)
    # embed_params: Dict[str, Any] = Field(default_factory=dict)


class InitRequest(BaseModel):
    root: str
