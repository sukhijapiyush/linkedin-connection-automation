import time
import random
from logging import basicConfig, INFO, WARN, DEBUG, ERROR, Logger
from typing import TypedDict, List, Any, Annotated, Dict, Optional
import pyautogui
from langgraph.graph import StateGraph, END
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from config import FAILSAFE, API_KEY, smart_llm_object, fast_llm_object, PAGE_LIMIT

# --- Configuration ---

pyautogui.FAILSAFE = FAILSAFE

# Basic logging setup
basicConfig(level=INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = Logger(__name__)


# --- Setting the Global LLm objects ---


class LLMManager:
    def __init__(self, smart_flag=False):
        logger.info("Initializing LLMManager")
        if smart_flag:
            self.llm = smart_llm_object
        else:
            self.llm = fast_llm_object

    def invoke(self, prompt: ChatPromptTemplate, **kwargs) -> str:
        logger.info(f"Invoking LLM with prompt: {prompt} and kwargs: {kwargs}")
        messages = prompt.format_messages(**kwargs)
        logger.info(f"Formatted messages: {messages}")
        response = self.llm.invoke(messages)
        logger.info(f"Received response: {response}")
        return response.content


smart_llm = LLMManager(smart_flag=True)
fast_llm = LLMManager(smart_flag=False)


# --- Setting the State class for workflow ---


class GraphState(TypedDict):
    search_string: str


class Linkedin_Connector:
    def __init__(self):
        pass

    def run_workflow(self):
        pass


if __name__ == "__main__":
    print("=" * 50)
    print(
        "IMPORTANT: Make sure browser is up and running. Also you have linkedin logged in and in focus"
    )
    search_string = input("\nEnter the search string: ")
    print("The Script will start in 10 seconds. Press Ctrl+C to cancel.")
    print("=" * 50)
    time.sleep(10)  # Reduced for faster testing

    logger.info("--- LinkedIn Connection Bot Starting ---")
    logger.info("You have 5 seconds to switch to your LinkedIn window...")
    time.sleep(5)

    linkedin_connector = Linkedin_Connector(
        search_string=search_string, page_limit=PAGE_LIMIT, current_page=1
    )
    linkedin_connector.run_workflow()
    logger.info("--- LinkedIn Connection Bot Finished ---")
