from dataclasses import dataclass
from dotenv import load_dotenv
from typing import Optional
import requests
import json
import os
from modeldata import ModelChatRequest, ModelResponse, Plugin, ToolCall, \
    Message
import utils

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

        data = json.dumps(utils.object_to_dict(request))

        r = requests.post(url=self.url + "/api/v1/chat", headers=headers, data=data)
        return ModelResponse.from_json(r.json())

def main():
    load_dotenv()

    request = ModelChatRequest(
        model=os.environ.get("LM_STUDIO_MODEL"),
        input="What have I asked in this conversation?",
        integrations=[
            Plugin(
                id="mcp/playwright",
            )
        ],
        store=True,
        context_length=10000,
        previous_response_id="resp_d08ac0a894baab6fa459254a4fb5df2f4b2f3d9d681bd7f3"
    )

    requester: ModelRequester = ModelRequester()

    output = requester.send_request(request)
    print(utils.object_to_dict(output))

if __name__ == "__main__":
    main()