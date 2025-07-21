import time
import random
import psutil
import logging
from typing import TypedDict, List
import pyautogui
from langgraph.graph import StateGraph, END
from langchain.prompts import ChatPromptTemplate
from config import FAILSAFE, API_KEY, smart_llm_object, fast_llm_object, PAGE_LIMIT

# --- Configuration ---

pyautogui.FAILSAFE = FAILSAFE


# --- Logging Setup ---
# Reset log file at start of each run
with open("log.log", "w") as f:
    f.write("")
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("log.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)
logger.info("Logger initialized and log file reset.")


# --- Helper Functions ---


def is_browser_running():
    """Check if a web browser process is running."""
    logger.debug("Checking for running browser processes...")
    browser_processes = ["chrome.exe", "firefox.exe", "msedge.exe", "safari.exe"]
    for proc in psutil.process_iter(["name"]):
        logger.debug(f"Examining process: {proc.info['name']}")
        if proc.info["name"] in browser_processes:
            logger.info(f"Browser process '{proc.info['name']}' is running.")
            return True
    logger.warning("No web browser process found running.")
    return False


# --- Setting the Global LLm objects ---


class LLMManager:
    def __init__(self, smart_flag=False):
        logger.info(f"Initializing LLMManager with smart_flag={smart_flag}")
        if smart_flag:
            logger.debug("Using smart_llm_object.")
            self.llm = smart_llm_object
        else:
            logger.debug("Using fast_llm_object.")
            self.llm = fast_llm_object

    def invoke(self, prompt: ChatPromptTemplate, **kwargs) -> str:
        logger.info(f"Invoking LLM with prompt: {prompt} and kwargs: {kwargs}")
        messages = prompt.format_messages(**kwargs)
        logger.debug(f"Formatted messages: {messages}")
        response = self.llm.invoke(messages)
        logger.debug(f"LLM raw response: {response}")
        logger.info(f"Received response: {response.content}")
        return response.content


smart_llm = LLMManager(smart_flag=True)
fast_llm = LLMManager(smart_flag=False)


# --- Setting the State class for workflow ---


class GraphState(TypedDict):
    search_string: str
    page_limit: int
    current_page: int
    initial_search_status: bool
    companies: List[str]
    connections: List[str]


class Linkedin_Connector:
    def __init__(
        self,
        search_string: str,
        page_limit: int,
        companies: List[str],
        connections: List[str],
        current_page: int = 1,
    ):
        self.search_string = search_string
        self.page_limit = page_limit
        self.current_page = current_page
        self.companies = companies
        self.connections = connections
        self.workflow = self.create_workflow()

    def initial_search(self, state):
        """
        Perform the initial search on LinkedIn.
        Checks if a browser is running, takes a screenshot, finds the search bar,
        types the search query, presses Enter, and clicks the 'People' filter.
        """
        search_string = state["search_string"]
        logger.info(f"Starting initial search for: '{search_string}'")
        logger.debug(f"Initial state: {state}")

        if not is_browser_running():
            logger.error(
                "Browser is not running. Please open a browser and log in to LinkedIn."
            )
            return {"initial_search_status": False}

        try:
            logger.debug("Attempting to locate LinkedIn search bar on screen...")
            search_bar_location = pyautogui.locateCenterOnScreen(
                "assets/search_bar.png", confidence=0.8
            )
            logger.debug(f"search_bar_location: {search_bar_location}")
            if not search_bar_location:
                logger.error("Could not find the LinkedIn search bar.")
                return {"initial_search_status": False}

            logger.info(f"Found search bar at: {search_bar_location}")
            pyautogui.click(search_bar_location)
            logger.debug("Clicked search bar.")
            time.sleep(1)
            pyautogui.hotkey("ctrl", "a")
            pyautogui.press("delete")
            logger.debug("Cleared search bar.")
            pyautogui.write(search_string, interval=0.2)
            logger.debug(f"Typed search string: {search_string}")
            pyautogui.press("enter")
            logger.info(
                f"Typed '{search_string}' into the search bar and pressed Enter."
            )
            time.sleep(10)  # Wait for search results to load

            logger.debug("Attempting to locate 'People' filter on screen...")
            people_filter_location = pyautogui.locateCenterOnScreen(
                "assets/people_filter.png", confidence=0.8
            )
            logger.debug(f"people_filter_location: {people_filter_location}")
            if people_filter_location:
                pyautogui.click(people_filter_location)
                logger.info("Clicked the 'People' filter.")
                time.sleep(10)
            else:
                logger.warning("Could not find the 'People' filter button.")

            logger.info("Initial search completed.")
            return {"initial_search_status": True}

        except pyautogui.PyAutoGUIException as e:
            logger.error(f"A PyAutoGUI error occurred: {e}")
            return {"initial_search_status": False}
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            return {"initial_search_status": False}

    def filter_results(self, state):
        """
        Applies filters for 'Current company' and connection level.
        """
        logger.info("Applying filters...")
        logger.debug(f"Filter state: {state}")
        companies = state.get("companies", [])
        connections = state.get("connections", [])

        try:
            # --- Apply Company Filters ---
            if companies:
                logger.debug(f"Companies to filter: {companies}")
                company_filter_location = pyautogui.locateCenterOnScreen(
                    "assets/current_company_filter.png", confidence=0.8
                )
                logger.debug(f"company_filter_location: {company_filter_location}")
                if not company_filter_location:
                    logger.warning("Could not find 'Current company' filter button.")
                else:
                    pyautogui.click(company_filter_location)
                    logger.debug("Clicked 'Current company' filter button.")
                    time.sleep(4)

                    add_company_input = pyautogui.locateCenterOnScreen(
                        "assets/add_company_input.png", confidence=0.5
                    )
                    logger.debug(f"add_company_input: {add_company_input}")
                    if not add_company_input:
                        logger.warning("Could not find 'Add a company' input field.")
                    else:
                        for company in companies:
                            logger.info(f"Filtering by company: {company}")
                            pyautogui.click(add_company_input)
                            logger.debug(
                                f"Clicked 'Add a company' input for: {company}"
                            )
                            time.sleep(1)
                            pyautogui.hotkey("ctrl", "a")
                            pyautogui.press("delete")
                            logger.debug("Cleared company input field.")
                            time.sleep(1)
                            logger.debug(f"Typing company name: {company}")
                            pyautogui.write(company, interval=0.1)
                            logger.debug(f"Typed company name: {company}")
                            time.sleep(2)
                            pyautogui.click(
                                (add_company_input.x, add_company_input.y + 30)
                            )
                            logger.info(f"Added company: {company}")
                            time.sleep(5)

                    show_results_button = pyautogui.locateCenterOnScreen(
                        "assets/show_results_button.png", confidence=0.8
                    )
                    logger.debug(f"show_results_button: {show_results_button}")
                    if show_results_button:
                        pyautogui.click(show_results_button)
                        logger.info("Clicked 'Show results' for company filters.")
                        time.sleep(5)
                    else:
                        logger.warning("Could not find 'Show results' button.")
                        pyautogui.press("esc")  # Close the dropdown if button not found

            # --- Apply Connection Filters ---
            if connections:
                logger.debug(f"Connections to filter: {connections}")
                for conn in connections:
                    conn_asset = f"assets/{conn}_connection.png"
                    logger.info(f"Applying connection filter: {conn}")
                    connection_button = pyautogui.locateCenterOnScreen(
                        conn_asset, confidence=0.8
                    )
                    logger.debug(f"connection_button for {conn}: {connection_button}")
                    if connection_button:
                        pyautogui.click(connection_button)
                        logger.info(f"Clicked '{conn}' connection filter button.")
                        time.sleep(5)
                    else:
                        logger.warning(
                            f"Could not find '{conn}' connection filter button."
                        )

        except pyautogui.PyAutoGUIException as e:
            logger.error(f"A PyAutoGUI error occurred during filtering: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred during filtering: {e}")

        logger.info("Filter results step completed.")
        return state

    def should_continue(self, state):
        """
        Determines whether to continue to the next step.
        """
        if state["initial_search_status"]:
            return "filter_results"
        else:
            return END

    def create_workflow(self):
        """
        Creates the LangGraph workflow.
        """
        workflow = StateGraph(GraphState)

        workflow.add_node("initial_search", self.initial_search)
        workflow.add_node("filter_results", self.filter_results)

        workflow.set_entry_point("initial_search")

        workflow.add_conditional_edges(
            "initial_search",
            self.should_continue,
        )
        workflow.add_edge("filter_results", END)

        return workflow.compile()

    def run_workflow(self):
        """
        Runs the LangGraph workflow.
        """
        initial_state = {
            "search_string": self.search_string,
            "page_limit": self.page_limit,
            "current_page": self.current_page,
            "companies": self.companies,
            "connections": self.connections,
            "initial_search_status": False,  # Explicitly set initial status
        }
        self.workflow.invoke(initial_state)


if __name__ == "__main__":
    print("=" * 50)
    print(
        "IMPORTANT: Make sure a browser is running with LinkedIn logged in and visible."
    )
    logger.info("Script started. Awaiting user input.")

    search_string = input("\nEnter the search string: ")
    if not search_string.strip():
        default_search = "Data Scientist"
        logger.warning("No search string provided. Using default: 'Data Scientist'.")
        search_string = default_search
    logger.debug(f"User input - search_string: {search_string}")

    companies_input = input(
        "Enter companies to filter by (comma-separated, e.g., Google,Microsoft): "
    )
    if not companies_input.strip():
        default_companies = "Google, Microsoft"
        logger.warning("No companies provided. Using default: 'Google, Microsoft'.")
        companies_input = default_companies
    logger.debug(f"User input - companies_input raw: {companies_input}")
    companies = [c.strip() for c in companies_input.split(",") if c.strip()]
    logger.debug(f"Parsed companies: {companies}")

    connections_input = input(
        "Enter connection levels to filter by (e.g., 1st,2nd,3rd+): "
    )
    if not connections_input.strip():
        default_connections = ""
        logger.warning("No connections provided. Using default: ''.")
        connections_input = default_connections
    logger.debug(f"User input - connections_input raw: {connections_input}")
    connections = [c.strip() for c in connections_input.split(",") if c.strip()]
    logger.debug(f"Parsed connections: {connections}")

    print("The Script will start in 5 seconds. Press Ctrl+C to cancel.")
    print("=" * 50)
    logger.info("Waiting 5 seconds before starting workflow.")
    time.sleep(5)

    logger.info("--- LinkedIn Connection Bot Starting ---")
    logger.info("You have 5 seconds to switch to your LinkedIn window...")
    time.sleep(5)

    logger.debug(
        f"Instantiating Linkedin_Connector with search_string={search_string}, page_limit={PAGE_LIMIT}, companies={companies}, connections={connections}"
    )
    linkedin_connector = Linkedin_Connector(
        search_string=search_string,
        page_limit=PAGE_LIMIT,
        companies=companies,
        connections=connections,
    )
    logger.info("Running workflow...")
    linkedin_connector.run_workflow()
    logger.info("--- LinkedIn Connection Bot Finished ---")
