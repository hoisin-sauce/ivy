# Datatypes for easy request handling
from dataclasses import dataclass
from types import UnionType
from typing import Optional
from enum import Enum

number: UnionType = float | int

class ReasoningOptions(Enum):
    OFF = "off"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ON = "on"

@dataclass
class ImageInput:
    data_url: str

    type: str = "image"

@dataclass
class TextInput:
    content: str

    type: str = "message"

@dataclass
class Plugin:
    id: str
    allowed_tools: Optional[list[str]] = None

    type: str = "plugin"

@dataclass
class EphemeralMCP:
    server_label: str
    server_url: str
    allowed_tools: Optional[list[str]] = None
    headers: Optional[dict[str, ...]] = None
    type: str = "ephemeral_mcp"

@dataclass
class ModelRequest:
    model: str
    input: str | list[TextInput | ImageInput]
    system_prompt: Optional[str] = None
    integrations: Optional[list[str | Plugin | EphemeralMCP]] = None
    stream: Optional[bool] = None # Defaults to false
    temperature: Optional[number] = None
    top_p: Optional[number] = None
    top_k: Optional[int] = None
    min_p: Optional[number] = None
    repeat_penalty: Optional[number] = None
    max_output_tokens: Optional[int] = None
    reasoning: Optional[ReasoningOptions] = None
    context_length: Optional[int] = None
    store: Optional[bool] = None
    previous_response_id: Optional[str] = None

@dataclass
class Message:
    content: str
    type: str = "message"

@dataclass
class PluginInfo:
    plugin_id: str
    type: str = "plugin"

class EphemeralMCPInfo:
    server_label: str
    type: str = "ephemeral_mcp"

@dataclass
class ToolCall:
    tool: str
    arguments: dict[str, ...]
    output: str
    provider_info: PluginInfo | EphemeralMCPInfo
    type: str = "tool_call"

@dataclass
class Reasoning:
    content: str
    type: str = "reasoning"

@dataclass
class InvalidToolName:
    tool_name: str
    type: str = "invalid_name"

@dataclass
class InvalidToolArguments:
    tool_name: str
    arguments: dict[str, ...]
    provider_info: PluginInfo | EphemeralMCPInfo
    type: str = "invalid_arguments"

@dataclass
class InvalidToolCall:
    reason: str
    metadata: InvalidToolName | InvalidToolArguments
    type: str = "invalid_tool_call"

@dataclass
class Stats:
    input_tokens: number
    total_output_tokens: number
    reasoning_output_tokens: number
    tokens_per_second: number
    time_to_first_token_seconds: number
    mean_load_time_seconds: Optional[number] = None

@dataclass
class ModelResponse:
    model_instance_id: str
    output: list[Message | ToolCall | Reasoning | InvalidToolCall]
    stats: Stats
    response_id: Optional[str] = None

    @staticmethod
    def from_json(json: dict) -> "ModelResponse":
        args = {}
        for key, value in json.items():
            match key:
                case "model_instance_id":
                    args["model_instance_id"] = value
                case "output":
                    output_list: list[Message | ToolCall | Reasoning | InvalidToolCall] = list()
                    for output in value:
                        match output["type"]:
                            case "message":
                                output_list.append(Message(**output))
                            case "tool_call":
                                output_list.append(ToolCall(**output))
                            case "reasoning":
                                output_list.append(Reasoning(**output))
                            case "invalid_tool_call":
                                match output["metadata"][type]:
                                    case "invalid_arguments":
                                        output["metadata"] = InvalidToolArguments(**output["metadata"])
                                    case "invalid_name":
                                        output["metadata"] = InvalidToolName(**output["metadata"])
                    args["output"] = output_list
                case "stats":
                    args["stats"] = Stats(**value)
                case "response_id":
                    args["response_id"] = value
        return ModelResponse(**args)
