import time
import random
import psutil
from logging import basicConfig, INFO, Logger
from typing import TypedDict
import pyautogui
from langgraph.graph import StateGraph, END
from langchain.prompts import ChatPromptTemplate
from config import FAILSAFE, API_KEY, smart_llm_object, fast_llm_object, PAGE_LIMIT

# --- Configuration ---

pyautogui.FAILSAFE = FAILSAFE

# Basic logging setup
basicConfig(level=INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = Logger(__name__)


# --- Helper Functions ---


def is_browser_running():
    """Check if a web browser process is running."""
    # Add browser executable names you use, e.g., 'msedge.exe' for Microsoft Edge
    browser_processes = ["chrome.exe", "firefox.exe", "msedge.exe", "safari.exe"]
    for proc in psutil.process_iter(["name"]):
        if proc.info["name"] in browser_processes:
            logger.info(f"Browser process '{proc.info['name']}' is running.")
            return True
    logger.warning("No web browser process found running.")
    return False


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
    intial_search_status: bool


class Linkedin_Connector:
    def __init__(self, search_string: str, page_limit: int, current_page: int = 1):
        self.search_string = search_string
        self.page_limit = page_limit
        self.current_page = current_page
        self.workflow = self.create_workflow()

    def initial_search(self, state):
        """
        Perform the initial search on LinkedIn.
        Checks if a browser is running, takes a screenshot, finds the search bar,
        types the search query, and presses Enter.,
        """
        search_string = state["search_string"]
        logger.info(f"Starting initial search for: '{search_string}'")

        if not is_browser_running():
            logger.error(
                "Browser is not running. Please open a browser and log in to LinkedIn."
            )
            return {"initial_search_status": False}

        try:

            # IMPORTANT: You need to create a 'search_bar.png' image.
            # This image should be a small screenshot of the LinkedIn search bar.
            search_bar_location = pyautogui.locateCenterOnScreen(
                "assets/search_bar.png"
            )
            logger.info("Attempting to locate the LinkedIn search bar on the screen...")

            if search_bar_location:
                logger.info(f"Found search bar at: {search_bar_location}")
                pyautogui.click(search_bar_location)
                time.sleep(1)  # Wait a moment for the click to register
                pyautogui.write(search_string, interval=0.1)
                pyautogui.press("enter")
                logger.info(
                    f"Typed '{search_string}' into the search bar and pressed Enter."
                )
                return {
                    "initial_search_status": True,
                }
            else:
                logger.error(
                    "Could not find the LinkedIn search bar on the screen. Make sure the browser window is visible."
                )
                return {"initial_search_status": False}

        except pyautogui.PyAutoGUIException as e:
            logger.error(f"An error occurred with PyAutoGUI: {e}")
            return {"initial_search_status": False}
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            return {"initial_search_status": False}

    def create_workflow(self):
        """
        Creates the LangGraph workflow.
        """
        workflow = StateGraph(GraphState)

        workflow.add_node("initial_search", self.initial_search)

        workflow.set_entry_point("initial_search")

        # For now, the workflow ends after the initial search.
        # We will add more nodes later.
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
        # The invoke method will execute the workflow starting from the entry point.
        self.workflow.invoke(initial_state)


if __name__ == "__main__":
    print("=" * 50)
    print(
        "IMPORTANT: Make sure a browser is running with LinkedIn logged in and visible on the screen."
    )
    search_string = input("\nEnter the search string: ")
    print("The Script will start in 5 seconds. Press Ctrl+C to cancel.")
    print("=" * 50)
    time.sleep(5)

    logger.info("--- LinkedIn Connection Bot Starting ---")
    logger.info("You have 5 seconds to switch to your LinkedIn window...")
    time.sleep(5)

    linkedin_connector = Linkedin_Connector(
        search_string=search_string, page_limit=PAGE_LIMIT
    )
    linkedin_connector.run_workflow()
    logger.info("--- LinkedIn Connection Bot Finished ---")
