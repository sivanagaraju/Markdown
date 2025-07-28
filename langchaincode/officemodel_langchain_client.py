#!/usr/bin/env python3
"""
OfficeModelLangchainClient - A wrapper for connecting LLM models through OfficeModel API
This client extends ChatOpenAI to work with custom enterprise LLM endpoints.
Compatible with LangChain and LangGraph frameworks.
"""

import os
import ssl
import uuid
import base64
import httpx
import requests
from datetime import datetime
from dotenv import load_dotenv
import logging
from typing import Optional, Dict, Any, List

try:
    from langchain_openai import ChatOpenAI
except ImportError:
    from langchain.chat_models import ChatOpenAI

try:
    from OfficeModel_api_core.common.utils import log_handler
except ImportError:
    # Fallback logging if OfficeModel_api_core is not available
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
else:
    load_dotenv()
    logger_service = log_handler.OfficeModelLogger(logging.INFO)
    logger = logger_service.get_logger()


class OfficeModelLangchainClient(ChatOpenAI):
    """
    OfficeModelLangchainClient is a LangChain client for interacting with the OfficeModel API.

    This client extends ChatOpenAI to work with enterprise LLM endpoints through
    a custom OfficeModel API gateway. It handles authentication, SSL certificates,
    and API headers required for enterprise deployment.

    Args:
        model_name (str): The model name to use (default: "gemini-2.0-flash")
        **kwargs: Additional arguments passed to the parent ChatOpenAI class

    Environment Variables Required:
        - OfficeModel_API_KEY: API key for OfficeModel service
        - OfficeModel_BASE_URL: Base URL for OfficeModel API
        - OfficeModel_USECASE_ID: Use case identifier
        - CERTS_PATH: Path to SSL certificates
        - USE_API_GATEWAY: Whether to use API gateway ("TRUE"/"FALSE")
        - APIGEE_OAUTH_URL: OAuth URL for Apigee authentication
        - APIGEE_CONSUMER_KEY: Consumer key for Apigee
        - APIGEE_CONSUMER_SECRET: Consumer secret for Apigee
    """

    def __init__(self, model_name: str = "gemini-2.0-flash", **kwargs):
        load_dotenv()

        # Get required environment variables
        api_key = os.getenv("OfficeModel_API_KEY", None)
        base_url = os.getenv("OfficeModel_BASE_URL", None)
        usecase_id = os.getenv("OfficeModel_USECASE_ID", None)
        cert_path = os.getenv("CERTS_PATH", None)

        # Validate mandatory fields
        self.mandatory_field_validation([
            "OfficeModel_API_KEY", 
            "OfficeModel_BASE_URL", 
            "CERTS_PATH", 
            "OfficeModel_USECASE_ID"
        ])

        # Get Apigee access token for authentication
        apigee_access_token = self.get_apigee_access_token()

        # Set up request headers with required authentication and tracking
        request_headers = {
            "x-request-id": str(uuid.uuid4()),
            "x-correlation-id": str(uuid.uuid4()),
            "x-wf-client-id": usecase_id,
            "x-wf-request": datetime.now().isoformat(),
            "x-wf-api-key": api_key,
            "x-wf-usecase-id": usecase_id,
            "Authorization": f"Bearer {apigee_access_token}"
        }

        # Configure default parameters
        kwargs["default_headers"] = request_headers

        if "temperature" not in kwargs:
            kwargs["temperature"] = 0

        if "max_tokens" not in kwargs:
            kwargs["max_tokens"] = None

        if "timeout" not in kwargs:
            kwargs["timeout"] = None

        if "max_retries" not in kwargs:
            kwargs["max_retries"] = 2

        if "api_key" not in kwargs:
            kwargs["api_key"] = "dummy"  # Placeholder as auth is handled via headers

        if "base_url" not in kwargs:
            kwargs["base_url"] = base_url

        # Configure SSL context for secure communication
        if "http_client" not in kwargs:
            ssl_context = ssl.create_default_context(cafile=cert_path)
            kwargs["http_client"] = httpx.AsyncClient(verify=ssl_context)

        # Initialize parent ChatOpenAI class
        super().__init__(model=model_name, **kwargs)

        logger.info(f"OfficeModelLangchainClient initialized with model: {model_name}")

    def get_apigee_access_token(self) -> str:
        """
        Retrieve access token from Apigee OAuth endpoint.

        Returns:
            str: Access token for API authentication

        Raises:
            Exception: If authentication fails or required env vars are missing
        """
        use_api_gateway = os.getenv("USE_API_GATEWAY", None)
        apigee_url = os.getenv("APIGEE_OAUTH_URL", None)
        apigee_consumer_key = os.getenv("APIGEE_CONSUMER_KEY", None)
        apigee_consumer_secret = os.getenv("APIGEE_CONSUMER_SECRET", None)
        cert_path = os.getenv("CERTS_PATH", None)

        self.mandatory_field_validation([
            "APIGEE_OAUTH_URL", 
            "APIGEE_CONSUMER_KEY", 
            "APIGEE_CONSUMER_SECRET", 
            "CERTS_PATH", 
            "USE_API_GATEWAY"
        ])

        if use_api_gateway.upper() == "FALSE":
            return "dummy"

        # Encode credentials for basic auth
        apigee_creds = f"{apigee_consumer_key}:{apigee_consumer_secret}"
        apigee_cred_b64 = base64.b64encode(apigee_creds.encode("utf-8")).decode("utf-8")

        try:
            response = requests.post(
                apigee_url,
                headers={
                    "Authorization": f"Basic {apigee_cred_b64}",
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                data={"grant_type": "client_credentials"},
                verify=cert_path,
                timeout=30
            )
            response.raise_for_status()

            resp_dict = response.json()
            apigee_access_token = resp_dict["access_token"]

            logger.info("Successfully obtained Apigee access token")
            return apigee_access_token

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get Apigee access token: {e}")
            raise Exception(f"Apigee authentication failed: {e}")
        except KeyError as e:
            logger.error(f"Invalid response format from Apigee: {e}")
            raise Exception(f"Invalid Apigee response: {e}")

    def mandatory_field_validation(self, field_names: List[str]) -> None:
        """
        Validate that all required environment variables are set.

        Args:
            field_names (List[str]): List of environment variable names to validate

        Raises:
            Exception: If any required environment variable is missing or None
        """
        for field_name in field_names:
            value = os.getenv(field_name, None)
            if value is None or value.strip() == "":
                error_msg = f"The field: {field_name} is missing or empty. Please provide the right value in the environment variables."
                logger.error(error_msg)
                raise Exception(error_msg)

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model configuration.

        Returns:
            Dict[str, Any]: Model configuration details
        """
        return {
            "model_name": self.model_name,
            "temperature": self.temperature,  
            "max_tokens": self.max_tokens,
            "base_url": self.openai_api_base,
            "max_retries": self.max_retries
        }


# Example usage and testing
if __name__ == "__main__":
    try:
        # Initialize the client
        llm = OfficeModelLangchainClient(model_name="gemini-2.0-flash")

        # Test message
        messages = [
            {
                "role": "system", 
                "content": "You are a helpful assistant that translates English to Spanish. Translate the user sentence."
            },
            {
                "role": "user", 
                "content": "Hello, how are you today?"
            }
        ]

        print("OfficeModelLangchainClient initialized successfully!")
        print(f"Model info: {llm.get_model_info()}")

        # Uncomment below to test actual API call
        # response = llm.invoke(messages)
        # print(f"Response: {response.content}")

    except Exception as e:
        print(f"Error initializing OfficeModelLangchainClient: {e}")
