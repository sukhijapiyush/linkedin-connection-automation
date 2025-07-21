import os
from langchain_google_genai import ChatGoogleGenerativeAI


FAILSAFE = True
PAGE_LIMIT = 5  # Number of pages to process
API_KEY = "YOUR_API_KEY"  # Replace with your actual API key

if "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = API_KEY

smart_llm_object = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    max_tokens=None,
    timeout=None,
    max_retries=2,
    response_mime_type="application/json",
    thinking_budget=4096,
    verbose=True,
)

fast_llm_object = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite-preview-06-17",
    max_tokens=None,
    timeout=None,
    max_retries=2,
    response_mime_type="application/json",
    thinking_budget=4096,
    verbose=True,
)
