from tripweaver.core.config import Settings
from tripweaver.providers.base import LLMProvider, SearchProvider, SupplementSearchProvider
from tripweaver.providers.llm import ARKLLMProvider, MockLLMProvider
from tripweaver.providers.search import (
    MockSearchProvider,
    MockSupplementSearchProvider,
    TavilySupplementSearchProvider,
)


def build_search_provider(settings: Settings) -> SearchProvider:
    if settings.search_provider == "mock":
        return MockSearchProvider()
    if settings.search_provider == "tavily" or settings.search_provider == "brave":
        import warnings
        warnings.warn(
            "SEARCH_PROVIDER=tavily/brave is deprecated for POI search, "
            "please use SEARCH_PROVIDER=amap instead",
            DeprecationWarning,
        )
        return MockSearchProvider()
    if settings.search_provider == "amap":
        from tripweaver.providers.amap import AmapSearchProvider
        return AmapSearchProvider(settings)

    raise ValueError(f"Unsupported search provider:{settings.search_provider}")


def build_supplement_provider(settings: Settings) -> SupplementSearchProvider | None:
    """构建攻略搜索 provider（Tavily）"""
    if not settings.tavily_api_key:
        return None
    return TavilySupplementSearchProvider(settings)


def build_llm_provider(settings: Settings) -> LLMProvider:
    if settings.llm_provider == "mock":
        return MockLLMProvider()
    if settings.llm_provider == "ark":
        return ARKLLMProvider(settings)

    raise ValueError(f"Unsupported llm provider:{settings.llm_provider}")
