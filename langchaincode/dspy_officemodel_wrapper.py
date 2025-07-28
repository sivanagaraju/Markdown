#!/usr/bin/env python3
"""
DSPy Wrapper for OfficeModelLangchainClient
This wrapper enables DSPy to use the OfficeModelLangchainClient for LLM connections.
It provides a bridge between DSPy's LM interface and OfficeModel's enterprise API.
"""

import dspy
from typing import Any, Dict, List, Optional, Union
import json
import logging
from OfficeModel_langchain_client import OfficeModelLangchainClient

# Configure logging
logger = logging.getLogger(__name__)


class OfficeModelDSPyLM(dspy.LM):
    """
    DSPy Language Model wrapper for OfficeModelLangchainClient.

    This wrapper allows DSPy to use the OfficeModelLangchainClient by implementing
    the required DSPy LM interface methods. It handles the translation between
    DSPy's expected format and OfficeModel's API responses.

    Args:
        model_name (str): The model name to use (default: "gemini-2.0-flash")
        **kwargs: Additional arguments passed to OfficeModelLangchainClient

    Example:
        ```python
        import dspy
        from dspy_OfficeModel_wrapper import OfficeModelDSPyLM

        # Configure DSPy with OfficeModel wrapper
        OfficeModel_lm = OfficeModelDSPyLM(model_name="gemini-2.0-flash")
        dspy.configure(lm=OfficeModel_lm)

        # Use DSPy modules as normal
        qa = dspy.ChainOfThought("question -> answer")
        result = qa(question="What is the capital of France?")
        print(result.answer)
        ```
    """

    def __init__(self, model_name: str = "gemini-2.0-flash", **kwargs):
        # Initialize parent DSPy LM class
        super().__init__(model=model_name, **kwargs)

        # Initialize the OfficeModelLangchainClient
        try:
            self.client = OfficeModelLangchainClient(model_name=model_name, **kwargs)
            logger.info(f"OfficeModelDSPyLM initialized with model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize OfficeModelLangchainClient: {e}")
            raise

        self.model_name = model_name
        self.kwargs = kwargs

    def basic_request(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        Make a basic request to the OfficeModel API via LangChain interface.

        This method is called by DSPy's internal machinery to get completions
        from the language model. It translates DSPy's request format to
        LangChain's message format and back.

        Args:
            prompt (str): The prompt text to send to the model
            **kwargs: Additional parameters like temperature, max_tokens, etc.

        Returns:
            Dict[str, Any]: Response in OpenAI-compatible format for DSPy
        """
        try:
            # Merge instance kwargs with call-time kwargs
            merged_kwargs = {**self.kwargs, **kwargs}

            # Remove DSPy-specific kwargs that shouldn't be passed to LangChain
            dspy_specific_keys = ['n', 'stop', 'logprobs', 'top_logprobs']
            for key in dspy_specific_keys:
                merged_kwargs.pop(key, None)

            # Convert prompt to LangChain message format
            if isinstance(prompt, str):
                messages = [{"role": "user", "content": prompt}]
            elif isinstance(prompt, list):
                # Handle case where prompt is already a list of messages
                messages = prompt
            else:
                raise ValueError(f"Unsupported prompt format: {type(prompt)}")

            # Call the OfficeModelLangchainClient
            response = self.client.invoke(messages, **merged_kwargs)

            # Convert LangChain response to OpenAI-compatible format for DSPy
            if hasattr(response, 'content'):
                content = response.content
            elif isinstance(response, str):
                content = response
            else:
                content = str(response)

            # Format response in OpenAI-compatible structure
            formatted_response = {
                "choices": [
                    {
                        "text": content,
                        "message": {
                            "role": "assistant", 
                            "content": content
                        },
                        "finish_reason": "stop",
                        "index": 0
                    }
                ],
                "usage": {
                    "prompt_tokens": len(prompt.split()) if isinstance(prompt, str) else 0,
                    "completion_tokens": len(content.split()),
                    "total_tokens": len(prompt.split()) + len(content.split()) if isinstance(prompt, str) else len(content.split())
                }
            }

            logger.debug(f"Successfully processed request for model: {self.model_name}")
            return formatted_response

        except Exception as e:
            logger.error(f"Error in basic_request: {e}")
            # Return a formatted error response
            return {
                "choices": [
                    {
                        "text": f"Error: {str(e)}",
                        "message": {
                            "role": "assistant",
                            "content": f"Error processing request: {str(e)}"
                        },
                        "finish_reason": "error",
                        "index": 0
                    }
                ],
                "error": str(e)
            }

    def __call__(self, prompt: str, only_completed: bool = True, return_sorted: bool = False, **kwargs) -> List[str]:
        """
        Main interface method called by DSPy modules.

        This method handles DSPy's standard calling convention and returns
        a list of completion strings as expected by DSPy.

        Args:
            prompt (str): The input prompt
            only_completed (bool): Whether to return only completed responses
            return_sorted (bool): Whether to sort responses
            **kwargs: Additional generation parameters

        Returns:
            List[str]: List of completion strings
        """
        try:
            # Handle number of completions
            n = kwargs.get('n', 1)
            completions = []

            for _ in range(n):
                response = self.basic_request(prompt, **kwargs)

                if 'error' in response:
                    logger.warning(f"Error in completion: {response['error']}")
                    if only_completed:
                        continue
                    else:
                        completions.append(response['choices'][0]['text'])
                else:
                    completions.append(response['choices'][0]['text'])

            # Ensure we have at least one completion
            if not completions and n > 0:
                completions = ["Error: No valid completions generated"]

            return completions[:n] if return_sorted else completions

        except Exception as e:
            logger.error(f"Error in __call__: {e}")
            return [f"Error: {str(e)}"]

    def generate(self, prompt: Union[str, List[str]], **kwargs) -> List[List[str]]:
        """
        Generate completions for single or multiple prompts.

        This method supports batch processing of prompts and returns
        completions in the format expected by DSPy optimizers.

        Args:
            prompt (Union[str, List[str]]): Single prompt or list of prompts
            **kwargs: Generation parameters

        Returns:
            List[List[str]]: List of completion lists, one per input prompt
        """
        if isinstance(prompt, str):
            prompts = [prompt]
        else:
            prompts = prompt

        results = []
        for p in prompts:
            completions = self(p, **kwargs)
            results.append(completions)

        return results

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model configuration.

        Returns:
            Dict[str, Any]: Model configuration details
        """
        base_info = self.client.get_model_info()
        return {
            **base_info,
            "wrapper_type": "DSPy-OfficeModel",
            "dspy_compatible": True
        }

    def copy(self, **kwargs) -> 'OfficeModelDSPyLM':
        """
        Create a copy of this LM with potentially different parameters.

        This method is used by DSPy optimizers to create variations
        of the language model with different settings.

        Args:
            **kwargs: Parameters to override in the copy

        Returns:
            OfficeModelDSPyLM: New instance with updated parameters
        """
        new_kwargs = {**self.kwargs, **kwargs}
        return OfficeModelDSPyLM(model_name=self.model_name, **new_kwargs)


# Factory function for easy instantiation
def create_OfficeModel_dspy_lm(model_name: str = "gemini-2.0-flash", **kwargs) -> OfficeModelDSPyLM:
    """
    Factory function to create a OfficeModelDSPyLM instance.

    Args:
        model_name (str): The model name to use
        **kwargs: Additional configuration parameters

    Returns:
        OfficeModelDSPyLM: Configured DSPy language model
    """
    return OfficeModelDSPyLM(model_name=model_name, **kwargs)


# Example usage and testing
if __name__ == "__main__":
    import os

    # Example usage
    try:
        print("Testing OfficeModelDSPyLM wrapper...")

        # Create the DSPy LM wrapper
        OfficeModel_lm = create_OfficeModel_dspy_lm(
            model_name="gemini-2.0-flash",
            temperature=0.7,
            max_tokens=100
        )

        # Configure DSPy to use our wrapper
        dspy.configure(lm=OfficeModel_lm)

        print("✅ OfficeModelDSPyLM wrapper created successfully!")
        print(f"Model info: {OfficeModel_lm.get_model_info()}")

        # Test basic functionality
        test_prompt = "What is artificial intelligence?"
        completions = OfficeModel_lm(test_prompt)
        print(f"✅ Test completion generated: {completions[0][:100]}...")

        # Test with DSPy modules
        qa_module = dspy.ChainOfThought("question -> answer")
        result = qa_module(question="What are the benefits of using DSPy?")
        print(f"✅ DSPy module test: {result.answer[:100]}...")

        print("🎉 All tests passed! OfficeModelDSPyLM is ready for use.")

    except Exception as e:
        print(f"❌ Error during testing: {e}")
        print("Make sure all required environment variables are set:")
        print("- OfficeModel_API_KEY")
        print("- OfficeModel_BASE_URL") 
        print("- OfficeModel_USECASE_ID")
        print("- CERTS_PATH")
        print("- APIGEE_OAUTH_URL")
        print("- APIGEE_CONSUMER_KEY")
        print("- APIGEE_CONSUMER_SECRET")
        print("- USE_API_GATEWAY")
