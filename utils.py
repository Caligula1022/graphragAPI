from functools import lru_cache
import os
from typing import Dict, Any, List
from logger import get_logger
import requests

logger = get_logger(__name__)


@lru_cache()
def get_kb_root() -> str:
    return os.getenv("KB_ROOT", "./kbs")


def normalize_api_base(api_base: str) -> str:
    """Normalize the API base URL by removing trailing slashes and /v1 or /api suffixes."""
    api_base = api_base.rstrip("/")
    if api_base.endswith("/v1") or api_base.endswith("/api"):
        api_base = api_base[:-3]
    return api_base


def get_models_endpoint(api_base: str, api_type: str) -> str:
    """Get the appropriate models endpoint based on the API type."""
    normalized_base = normalize_api_base(api_base)
    if api_type.lower() == "openai":
        return f"{normalized_base}/v1/models"
    elif api_type.lower() == "azure":
        return f"{normalized_base}/openai/deployments?api-version=2022-12-01"
    else:  # For other API types (e.g., local LLMs)
        return f"{normalized_base}/models"


async def fetch_available_models(settings: Dict[str, Any]) -> List[str]:
    """Fetch available models from the API."""
    api_base = settings["api_base"]
    api_type = settings["api_type"]
    api_key = settings["api_key"]
    models_endpoint = get_models_endpoint(api_base, api_type)
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    try:
        response = requests.get(models_endpoint, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if api_type.lower() == "openai":
            return [model["id"] for model in data["data"]]
        elif api_type.lower() == "azure":
            return [model["id"] for model in data["value"]]
        else:
            # Adjust this based on the actual response format of your local LLM API
            return [model["name"] for model in data["models"]]
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching models: {str(e)}")
        return []
