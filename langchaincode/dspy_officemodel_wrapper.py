import os
import uuid
import base64
import requests
from datetime import datetime
from dotenv import load_dotenv
from OfficeModel_a2a_core.common.utils import log_handler
from dspy.clients.base_lm import BaseLM

logger = log_handler.OfficeModelLogger().get_logger()

class OfficeModelDSPyLM(BaseLM):
    """
    DSPy-compatible wrapper for OfficeModel API via Apigee.
    """

    def __init__(
        self,
        model: str = "gpt-4-turbo",
        **kwargs,
    ):
        # Initialize BaseLM with model name and default kwargs
        super().__init__(model=model, **kwargs)
        load_dotenv()
        # Mandatory env vars
        self.api_key = os.getenv("OfficeModel_API_KEY")
        self.base_url = os.getenv(
            "OfficeModel_BASE_URL",
            os.environ.get("OfficeModel_GENERATION_ENDPOINT", "https://OfficeModel.api/v1/openai/v1"),
        )
        self.cert_path = os.getenv("CERTS_PATH")
        self.usecase_id = os.getenv("OfficeModel_USECASE_ID")
        self._validate_env_vars()

        # Prepare Apigee credentials
        self.apigee_url = os.getenv("APIGEE_OAUTH_URL")
        self.apigee_consumer_key = os.getenv("APIGEE_CONSUMER_KEY")
        self.apigee_consumer_secret = os.getenv("APIGEE_CONSUMER_SECRET")
        self.apigee_token = self._get_apigee_access_token()

    def _validate_env_vars(self):
        missing = [
            name for name in ["OfficeModel_API_KEY","OfficeModel_BASE_URL","CERTS_PATH","OfficeModel_USECASE_ID"]
            if getattr(self, name.lower(), None) is None
        ]
        if missing:
            logger.error(f"Missing environment variables: {missing}")
            raise RuntimeError(f"Please set {missing} in your environment")

    def _get_apigee_access_token(self) -> str:
        creds = f"{self.apigee_consumer_key}:{self.apigee_consumer_secret}"
        auth = base64.b64encode(creds.encode("utf-8")).decode("utf-8")
        resp = requests.post(
            self.apigee_url,
            headers={"Authorization": f"Basic {auth}"},
            data={"grant_type": "client_credentials"},
            verify=self.cert_path,
        )
        resp.raise_for_status()
        return resp.json()["access_token"]

    def __call__(
        self,
        prompt: str = None,
        messages: list[dict] = None,
        **kwargs,
    ) -> dict:
        """
        Conform to BaseLM.__call__ signature so DSPy can invoke us.
        DSPy adapters will supply either `prompt` (short-form) or `messages`.
        """
        # Build standard headers
        headers = {
            "x-request-id": str(uuid.uuid4()),
            "x-correlation-id": str(uuid.uuid4()),
            "x-wf-client-id": self.usecase_id,
            "x-wf-request-date": datetime.utcnow().isoformat(),
            "x-wf-api-key": self.api_key,
            "x-wf-usecase-id": self.usecase_id,
            "Authorization": f"Bearer {self.apigee_token}",
            "Content-Type": "application/json",
        }

        payload = {"model": self.model, **self.kwargs}
        if prompt is not None:
            payload["prompt"] = prompt
        elif messages is not None:
            payload["messages"] = messages
        else:
            raise ValueError("Either `prompt` or `messages` must be provided")

        response = requests.post(
            self.base_url,
            headers=headers,
            json=payload,
            verify=self.cert_path,
        )
        response.raise_for_status()
        return response.json()
