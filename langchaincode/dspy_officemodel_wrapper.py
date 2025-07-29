# OfficeModel_dspy_wrapper.py

import os
import ssl
import uuid
import base64
import requests
import logging
from datetime import datetime
from dotenv import load_dotenv
from typing import List, Dict, Any

import dspy

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class OfficeModelDSPYWrapper:
    """
    A DSPy wrapper for the OfficeModel API, authenticating via Apigee and exposing
    a dspy.LM instance configured to send requests through our proxy.
    """

    def __init__(self,
                 model_name: str = "gemini-2.0-flash",
                 *,
                 **lm_kwargs):
        """
        Args:
            model_name: DSPy model identifier (e.g. "gemini-2.0-flash").
            apigee_oauth_url: OAuth URL for Apigee token exchange.
            consumer_key: Apigee consumer key.
            consumer_secret: Apigee consumer secret.
            use_api_gateway: "TRUE"/"FALSE" to disable or enable real Apigee calls.
            cert_path: Path to SSL CA bundle.
            base_url: OfficeModel LLM endpoint URL.
            api_key: Static API key (OfficeModel API key).
            usecase_id: Client/use-case identifier.
            lm_kwargs: Additional parameters for dspy.LM (e.g. temperature, max_tokens).
        """
        load_dotenv()

        # Load and validate required env vars if not passed explicitly
        self.apigee_oauth_url  =  os.getenv("APIGEE_OAUTH_URL")
        self.consumer_key      =  os.getenv("APIGEE_CONSUMER_KEY")
        self.consumer_secret   = os.getenv("APIGEE_CONSUMER_SECRET")
        self.use_api_gateway   =  os.getenv("USE_API_GATEWAY", "TRUE")
        self.cert_path         = os.getenv("CERTS_PATH")
        self.base_url          =  os.getenv("OfficeModel_BASE_URL")
        self.api_key           = os.getenv("OfficeModel_API_KEY")
        self.usecase_id        =  os.getenv("OfficeModel_USECASE_ID")

        # Ensure mandatory fields are present
        missing = [name for name, val in {
            "APIGEE_OAUTH_URL": self.apigee_oauth_url,
            "APIGEE_CONSUMER_KEY": self.consumer_key,
            "APIGEE_CONSUMER_SECRET": self.consumer_secret,
            "USE_API_GATEWAY": self.use_api_gateway,
            "CERTS_PATH": self.cert_path,
            "OfficeModel_BASE_URL": self.base_url,
            "OfficeModel_API_KEY": self.api_key,
            "OfficeModel_USECASE_ID": self.usecase_id,
        }.items() if not val]
        if missing:
            raise Exception(f"Missing env vars: {', '.join(missing)}")

        # Build SSL context
        self.ssl_context = ssl.create_default_context(cafile=self.cert_path)

        # Acquire Apigee token (or dummy)
        self.apigee_token = self._fetch_apigee_token()

        # Define headers for every request
        self.default_headers = {
            "x-request-id":      str(uuid.uuid4()),
            "x-correlation-id":  str(uuid.uuid4()),
            "x-wf-client-id":    self.usecase_id,
            "x-wf-request":      datetime.utcnow().isoformat() + "Z",
            "x-wf-api-key":      self.api_key,
            "x-wf-usecase-id":   self.usecase_id,
            "Authorization":     f"Bearer {self.apigee_token}",
        }

        # Initialize the DSPy LM adapter
        lm_args = {
            "model":     model_name,
            "api_key":   self.api_key,     # forwarded to the provider adapter
            "api_base":  self.base_url,    # endpoint for OfficeModel
            **lm_kwargs
        }
        self.lm = dspy.LM(**lm_args)
        logger.info(f"OfficeModelDSPYWrapper initialized for model {model_name}")

        # Monkey-patch the LM’s request session to inject our headers & SSL
        # (Override its internal HTTP client if needed)
        import httpx
        client = httpx.Client(verify=self.cert_path, headers=self.default_headers)
        setattr(self.lm, "_client", client)

    def _fetch_apigee_token(self) -> str:
        """
        Get a bearer token from Apigee or return "dummy" if gateway is disabled.
        """
        if self.use_api_gateway.strip().upper() == "FALSE":
            logger.info("API gateway disabled; using dummy token.")
            return "dummy"

        creds = f"{self.consumer_key}:{self.consumer_secret}"
        b64 = base64.b64encode(creds.encode()).decode()
        resp = requests.post(
            self.apigee_oauth_url,
            headers={"Authorization": f"Basic {b64}"},
            data={"grant_type": "client_credentials"},
            verify=self.cert_path,
            timeout=30
        )
        resp.raise_for_status()
        token = resp.json().get("access_token")
        logger.info("Obtained Apigee access token")
        return token

    def __call__(self, *args, **kwargs) -> Any:
        """
        Delegate calls directly to the underlying DSPy LM.
        Supports both chat and text completions:
            - chat: lm(messages=[{"role": "user","content": "..."}], **kwargs)
            - text: lm("Some prompt", **kwargs)
        """
        return self.lm(*args, **kwargs)

    def get_model_info(self) -> Dict[str, Any]:
        """
        Return the wrapper and model configuration.
        """
        info = {
            "model_name":   self.lm.model,
            "temperature":  getattr(self.lm, "temperature", None),
            "max_tokens":   getattr(self.lm, "max_tokens", None),
            "base_url":     self.base_url,
            "usecase_id":   self.usecase_id,
            "num_retries":  getattr(self.lm, "num_retries", None),
        }
        return info


if __name__ == "__main__":
    # Example usage
    wrapper = OfficeModelDSPYWrapper(
        model_name="gemini-2.0-flash",
        temperature=0.7,
        max_tokens=100
    )
    dspy.config(lm=wrapper)
    
    response = dspy.lm("Translate 'Good morning' to French", temperature=0.0)
    print("Direct prompt response:", response)
    # Expected output: ["Bonjour"] or similar translation.

    # 4. Chain-of-Thought example
    qa = dspy.ChainOfThought("question -> answer")
    result = qa(question="If I have 3 apples and I buy 2 more, how many apples do I have?")
    print("Chain-of-Thought answer:", result.answer)
    # Expected output: "You have 5 apples."

