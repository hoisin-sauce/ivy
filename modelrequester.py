from dataclasses import dataclass
from dotenv import load_dotenv
from typing import Optional
import requests
import json
import os
from modeldata import ModelRequest, ModelResponse
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

    def send_request(self, request: ModelRequest) -> ModelResponse:
        headers = {
            "Authorization": f"Bearer {self.authentication_token}",
            "Content-Type": "application/json"
        }

        data = json.dumps(utils.object_to_dict(request))

        r = requests.post(url=self.url + "/api/v1/chat", headers=headers, data=data)

        return ModelResponse.from_json(r.json())

def main():
    load_dotenv()

    request = ModelRequest(
        model=os.environ.get("LM_STUDIO_MODEL"),
        input="What is the weather today?",
    )

    requester: ModelRequester = ModelRequester()

    print(requester.send_request(request))

if __name__ == "__main__":
    main()