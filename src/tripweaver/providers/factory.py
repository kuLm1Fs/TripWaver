from multiprocessing import Value
from tripweaver.core.config import Settings
from tripweaver.providers.base import LLMProvider, SearchProvider
from tripweaver.providers.llm import MockLLMProvider
from tripweaver.providers.search import MockSearchProvider


def build_search_provider(settings: Settings) -> SearchProvider:
    if settings.search_provider == "mock":
        return MockSearchProvider()

    raise ValueError(f"Unsupported search provider:{settings.search_provider}")


def build_llm_provider(settings: Settings) -> LLMProvider:
    if settings.llm_provider == "mock":
        return MockLLMProvider()

    raise ValueError(f"Unsupported llm provider:{settings.llm_provider}")
