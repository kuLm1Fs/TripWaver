from tripweaver.core.config import Settings
from tripweaver.providers.base import LLMProvider, SearchProvider
from tripweaver.providers.llm import ARKLLMProvider, MockLLMProvider
from tripweaver.providers.search import TavilySearchProvider, MockSearchProvider


def build_search_provider(settings: Settings) -> SearchProvider:
    if settings.search_provider == "mock":
        return MockSearchProvider()
    if settings.search_provider == "tavily" or settings.search_provider == "brave":
        # 兼容旧配置，brave已替换为tavily
        if settings.search_provider == "brave":
            import warnings
            warnings.warn("SEARCH_PROVIDER=brave is deprecated, please use SEARCH_PROVIDER=tavily instead", DeprecationWarning)
        return TavilySearchProvider(settings)

    raise ValueError(f"Unsupported search provider:{settings.search_provider}")


def build_llm_provider(settings: Settings) -> LLMProvider:
    if settings.llm_provider == "mock":
        return MockLLMProvider()
    if settings.llm_provider == "ark":
        return ARKLLMProvider(settings)

    raise ValueError(f"Unsupported llm provider:{settings.llm_provider}")
