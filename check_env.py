import os

print(f"GOOGLE_API_KEY: {os.environ.get('GOOGLE_API_KEY')}")
print(f"LLM_PROVIDER: {os.environ.get('LLM_PROVIDER')}")
print(f"LITELLM_MODEL: {os.environ.get('LITELLM_MODEL')}")