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
    page_limit: int
    current_page: int


class Linkedin_Connector:
    def __init__(self, search_string: str, page_limit: int, current_page: int = 1):
        self.search_string = search_string
        self.page_limit = page_limit
        self.current_page = current_page
        self.workflow = self.create_workflow()

    def initial_search(self, state):
        """
        Perform the initial search on LinkedIn.
        """
        search_string = state["search_string"]
        logger.info(f"Starting initial search for: {search_string}")

        # This is a placeholder for the actual pyautogui automation
        # In a real scenario, you would have code like this:
        #
        # search_bar_location = pyautogui.locateCenterOnScreen('search_bar.png', confidence=0.8)
        # if search_bar_location:
        #     pyautogui.click(search_bar_location)
        #     pyautogui.write(search_string)
        #     pyautogui.press('enter')
        #     time.sleep(2)
        #     people_filter_location = pyautogui.locateCenterOnScreen('people_filter.png', confidence=0.8)
        #     if people_filter_location:
        #         pyautogui.click(people_filter_location)
        # else:
        #     logger.error("Could not find the LinkedIn search bar.")

        print(f"Executing search for: {search_string}")
        # For the purpose of this example, we'll just log the action
        logger.info("Initial search node executed.")
        return state

    def create_workflow(self):
        """
        Creates the LangGraph workflow.
        """
        workflow = StateGraph(GraphState)

        workflow.add_node("initial_search", self.initial_search)

        workflow.set_entry_point("initial_search")

        workflow.add_edge("initial_search", END)

        return workflow.compile()

    def run_workflow(self):
        """
        Runs the LangGraph workflow.
        """
        initial_state = {
            "search_string": self.search_string,
            "page_limit": self.page_limit,
            "current_page": self.current_page,
        }
        self.workflow.invoke(initial_state)


if __name__ == "__main__":
    print("=" * 50)
    print(
        "IMPORTANT: Make sure browser is up and running. Also you have linkedin logged in and in focus"
    )
    search_string = input("\nEnter the search string: ")
    print("The Script will start in 10 seconds. Press Ctrl+C to cancel.")
    print("=" * 50)
    time.sleep(10)

    logger.info("--- LinkedIn Connection Bot Starting ---")
    logger.info("You have 5 seconds to switch to your LinkedIn window...")
    time.sleep(5)

    linkedin_connector = Linkedin_Connector(
        search_string=search_string, page_limit=PAGE_LIMIT
    )
    linkedin_connector.run_workflow()
    logger.info("--- LinkedIn Connection Bot Finished ---")
