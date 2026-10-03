"""Rough implemenation/proof of concept on interactions with LM Studio
"""
from dataclasses import dataclass
from dotenv import load_dotenv
from typing import Optional
import requests
import json
import os
from modeldata import ModelChatRequest, ModelResponse, Plugin, Reasoning
import lm_utils

@dataclass
class ModelRequester:
    authentication_token: Optional[str] = None
    url: Optional[str] = None

    def __post_init__(self):
        if not self.url:
            self.url = os.environ.get("LM_STUDIO_ENDPOINT")
        if not self.authentication_token:
            self.authentication_token = os.environ.get("LM_STUDIO_TOKEN")

    def send_request(self, request: ModelChatRequest) -> ModelResponse:
        headers = {
            "Authorization": f"Bearer {self.authentication_token}",
            "Content-Type": "application/json"
        }

        data = json.dumps(lm_utils.object_to_dict(request))

        r = requests.post(url=self.url + "/api/v1/chat", headers=headers, data=data)
        return ModelResponse.from_json(r.json())

    def get_manager(self) -> lm_utils.FunctionScheduler[ModelChatRequest, ModelResponse]:
        return lm_utils.FunctionScheduler(self.send_request)

class ContinuityError(Exception):
    ...

@dataclass
class ConversationFrame:
    prompt: ModelChatRequest
    response: ModelResponse
    parent: Optional["ConversationFrame"]

    def __post_init__(self):
        if self.parent:
            if self.parent.response.response_id != self.prompt.previous_response_id:
                raise ContinuityError("Prompt's parent is not correct")

    def get_response_id(self) -> Optional[str]:
        return self.response.response_id

    def get_thoughts(self) -> list[Reasoning]:
        reasoning_blocks = filter(
            lambda x: isinstance(x, Reasoning),
            self.response.output
        )

        return list(reasoning_blocks)

@dataclass
class ConversationTree:
    ...

def main():
    load_dotenv()

    request = ModelChatRequest(
        model=os.environ.get("LM_STUDIO_MODEL"),
        input="What have I asked in this conversation?",
        integrations=[
            Plugin(
                id="mcp/playwright"
            )
        ],
        store=True,
        context_length=10000
    )

    requester: ModelRequester = ModelRequester()

    output = requester.send_request(request)
    print(lm_utils.object_to_dict(output))

if __name__ == "__main__":
    main()