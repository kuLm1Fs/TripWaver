from tripweaver.core.config import get_settings

settings = get_settings()

print("search_provider:", settings.search_provider)
print("llm_provider:", settings.llm_provider)
print("brave_base_url:", settings.brave_base_url)
print("ark_base_url:", settings.ark_base_url)
print("ark_model:", settings.ark_model)
print("has_brave_key:", bool(settings.brave_api_key))
print("has_ark_key:", bool(settings.ark_api_key))
