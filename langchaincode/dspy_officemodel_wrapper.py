import os
import ssl
import uuid
import base64
import requests
from datetime import datetime
from typing import List, Dict, Any
import logging
from dotenv import load_dotenv
import dspy
from dspy import BaseLM

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OfficeModelDSPYWrapper(BaseLM):
    """
    A DSPy wrapper for the OfficeModel API, integrating enterprise features like
    Apigee authentication, custom headers, and SSL certificate handling.
    """
    
    def __init__(self, model_name: str = "gemini-2.0-flash", **kwargs):
        """
        Initialize the wrapper with model name and configuration.
        
        Args:
            model_name (str): The name of the model to use (default: "gemini-2.0-flash").
            **kwargs: Additional parameters for the model.
        """
        # Load environment variables from .env file
        load_dotenv()
        
        # Retrieve required environment variables
        self.api_key = os.getenv("OfficeModel_API_KEY")
        self.base_url = os.getenv("OfficeModel_BASE_URL")
        self.usecase_id = os.getenv("OfficeModel_USECASE_ID")
        self.cert_path = os.getenv("CERTS_PATH")
        
        # Validate mandatory environment variables
        self.mandatory_field_validation([
            "OfficeModel_API_KEY", "OfficeModel_BASE_URL", 
            "CERTS_PATH", "OfficeModel_USECASE_ID",
            "USE_API_GATEWAY", "APIGEE_OAUTH_URL",
            "APIGEE_CONSUMER_KEY", "APIGEE_CONSUMER_SECRET"
        ])
        
        # Fetch Apigee access token for authentication
        self.apigee_access_token = self.get_apigee_access_token()
        
        # Configure request headers for API calls
        self.request_headers = {
            "x-request-id": str(uuid.uuid4()),
            "x-correlation-id": str(uuid.uuid4()),
            "x-wf-client-id": self.usecase_id,
            "x-wf-request": datetime.now().isoformat(),
            "x-wf-api-key": self.api_key,
            "x-wf-usecase-id": self.usecase_id,
            "Authorization": f"Bearer {self.apigee_access_token}"
        }
        
        # Set default parameters if not provided
        self.kwargs = kwargs
        self.kwargs.setdefault("temperature", 0)
        self.kwargs.setdefault("max_tokens", None)
        self.kwargs.setdefault("timeout", None)
        self.kwargs.setdefault("max_retries", 2)
        self.kwargs.setdefault("api_key", "dummy")
        self.kwargs.setdefault("base_url", self.base_url)
        
        # Configure SSL context for secure communication
        self.ssl_context = ssl.create_default_context(cafile=self.cert_path)
        
        # Initialize parent BaseLM class
        super().__init__(model=model_name, model_type="chat")

    def get_apigee_access_token(self) -> str:
        """
        Fetch an Apigee access token using consumer credentials.
        
        Returns:
            str: The access token.
        
        Raises:
            Exception: If authentication fails or required env vars are missing.
        """
        # Check if API gateway is enabled
        use_api_gateway = os.getenv("USE_API_GATEWAY")
        if use_api_gateway and use_api_gateway.upper() == "FALSE":
            logger.info("API gateway disabled, using dummy token")
            return "dummy"
        
        # Encode Apigee credentials for Basic Auth
        apigee_creds = f"{os.getenv('APIGEE_CONSUMER_KEY')}:{os.getenv('APIGEE_CONSUMER_SECRET')}"
        apigee_cred_b64 = base64.b64encode(apigee_creds.encode("utf-8")).decode("utf-8")
        
        try:
            # Make POST request to Apigee OAuth endpoint
            response = requests.post(
                os.getenv("APIGEE_OAUTH_URL"),
                headers={
                    "Authorization": f"Basic {apigee_cred_b64}",
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                data={"grant_type": "client_credentials"},
                verify=self.cert_path,
                timeout=30
            )
            response.raise_for_status()
            logger.info("Successfully obtained Apigee access token")
            return response.json()["access_token"]
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get Apigee access token: {e}")
            raise Exception(f"Apigee authentication failed: {e}")

    def mandatory_field_validation(self, field_names: List[str]) -> None:
        """
        Validate that all required environment variables are set.
        
        Args:
            field_names (List[str]): List of environment variable names to validate.
        
        Raises:
            Exception: If any required variable is missing or empty.
        """
        for field_name in field_names:
            value = os.getenv(field_name)
            if not value or value.strip() == "":
                error_msg = f"The field: {field_name} is missing or empty. Please provide the right value in the environment variables."
                logger.error(error_msg)
                raise Exception(error_msg)

    def __call__(self, prompt: str, **kwargs) -> List[Any]:
        """
        Handle the main invocation of the language model.
        
        Args:
            prompt (str): The input prompt.
            **kwargs: Additional parameters for the model.
            
        Returns:
            List[Any]: The model response.
        """
        # Prepare the API payload
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": kwargs.get("temperature", self.kwargs["temperature"]),
            "max_tokens": kwargs.get("max_tokens", self.kwargs["max_tokens"])
        }
        
        try:
            # Make POST request to OfficeModel API
            response = requests.post(
                self.base_url,
                headers=self.request_headers,
                json=payload,
                verify=self.cert_path,
                timeout=kwargs.get("timeout", self.kwargs["timeout"])
            )
            response.raise_for_status()
            # Extract choices from response
            choices = response.json().get("choices", [])
            return [choice["message"]["content"] for choice in choices]
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise Exception(f"Failed to invoke OfficeModel API: {e}")

    def basic_request(self, prompt: str, **kwargs) -> List[Any]:
        """
        Handle a basic request to the language model (fallback method).
        
        Args:
            prompt (str): The input prompt.
            **kwargs: Additional parameters for the model.
            
        Returns:
            List[Any]: The model response.
        """
        return self.__call__(prompt, **kwargs)

    def generate(self, prompt: str, **kwargs) -> List[str]:
        """
        Generate text completions.
        
        Args:
            prompt (str): The input prompt.
            **kwargs: Additional parameters for the model.
            
        Returns:
            List[str]: The generated text.
        """
        return self.__call__(prompt, **kwargs)

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, str]:
        """
        Handle chat-based interactions.
        
        Args:
            messages (List[Dict[str, str]]): The chat messages.
            **kwargs: Additional parameters for the model.
            
        Returns:
            Dict[str, str]: The chat response.
        """
        # Prepare the API payload with chat messages
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.kwargs["temperature"]),
            "max_tokens": kwargs.get("max_tokens", self.kwargs["max_tokens"])
        }
        
        try:
            # Make POST request to OfficeModel API
            response = requests.post(
                self.base_url,
                headers=self.request_headers,
                json=payload,
                verify=self.cert_path,
                timeout=kwargs.get("timeout", self.kwargs["timeout"])
            )
            response.raise_for_status()
            # Return the first message content
            return response.json()["choices"][0]["message"]
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise Exception(f"Failed to invoke OfficeModel API: {e}")

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model configuration.
        
        Returns:
            Dict[str, Any]: Model configuration details.
        """
        return {
            "model_name": self.model,
            "temperature": self.kwargs.get("temperature", 0),
            "max_tokens": self.kwargs.get("max_tokens"),
            "base_url": self.base_url,
            "max_retries": self.kwargs.get("max_retries", 2)
        }

# Example usage
if __name__ == "__main__":
    try:
        # Initialize the wrapper
        lm = OfficeModelDSPYWrapper(model_name="gemini-2.0-flash")
        
        # Configure DSPy to use the wrapper
        dspy.settings.configure(lm=lm)
        
        # Example prompt
        prompt = "You are a helpful assistant that translates English to Spanish. Translate: 'Hello, how are you?'"
        
        # Make a request
        response = lm(prompt)
        print("Response:", response)
        print("Model info:", lm.get_model_info())
    except Exception as e:
        logger.error(f"Error: {e}")
        print(f"Error: {e}")