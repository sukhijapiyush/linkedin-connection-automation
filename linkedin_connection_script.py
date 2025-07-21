import time
import random
import psutil
import logging
from typing import TypedDict, List
import pyautogui
from langgraph.graph import StateGraph, END
from langchain.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from config import FAILSAFE, API_KEY, smart_llm_object, fast_llm_object, PAGE_LIMIT
from screenshot import scroll_screenshot
import base64
import json
import tkinter as tk

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


def countdown(seconds, message=""):
    """Displays a countdown timer popup and waits for the specified duration."""
    root = tk.Tk()
    root.title("LinkedIn Bot Status")

    # Make window borderless and stay on top
    root.overrideredirect(True)
    root.attributes("-topmost", True)

    # Create a label with the message and timer
    label_text = f"{message}\nContinuing in {seconds} seconds..."
    label = tk.Label(
        root,
        text=label_text,
        font=("Helvetica", 14),
        bg="lightblue",
        fg="black",
        padx=20,
        pady=20,
    )
    label.pack()

    # Center the window on the screen
    root.update_idletasks()  # Update geometry
    window_width = root.winfo_width()
    window_height = root.winfo_height()
    position_right = int(root.winfo_screenwidth() / 2 - window_width / 2)
    position_down = int(root.winfo_screenheight() / 2 - window_height / 2)
    root.geometry(f"+{position_right}+{position_down}")

    def update_clock(sec):
        new_text = f"{message}\nContinuing in {sec} seconds..."
        label.config(text=new_text)
        if sec > 0:
            root.after(1000, update_clock, sec - 1)
        else:
            root.destroy()

    # Start the countdown
    root.after(1000, update_clock, seconds - 1)
    root.mainloop()


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

    def invoke(self, prompt, **kwargs) -> str:
        logger.info(f"Invoking LLM with prompt and kwargs...")
        if isinstance(prompt, ChatPromptTemplate):
            messages = prompt.format_messages(**kwargs)
        else:  # Handle direct message objects for vision
            messages = prompt

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
    profiles_to_connect: List[dict]


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
            countdown(10, "Waiting for search results to load...")

            logger.debug("Attempting to locate 'People' filter on screen...")
            people_filter_location = pyautogui.locateCenterOnScreen(
                "assets/people_filter.png", confidence=0.8
            )
            logger.debug(f"people_filter_location: {people_filter_location}")
            if people_filter_location:
                pyautogui.click(people_filter_location)
                logger.info("Clicked the 'People' filter.")
                countdown(10, "Waiting for filtered results to load...")
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
                    countdown(4, "Opening company filter...")

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
                            countdown(5, f"Searching for company '{company}'...")
                            pyautogui.click(
                                (add_company_input.x, add_company_input.y + 30)
                            )
                            logger.info(f"Added company: {company}")
                            countdown(5, "Waiting after adding company...")

                    show_results_button = pyautogui.locateCenterOnScreen(
                        "assets/show_results_button.png", confidence=0.8
                    )
                    logger.debug(f"show_results_button: {show_results_button}")
                    if show_results_button:
                        pyautogui.click(show_results_button)
                        logger.info("Clicked 'Show results' for company filters.")
                        countdown(5, "Applying company filters...")
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
                        countdown(5, f"Applying '{conn}' filter...")
                    else:
                        logger.warning(
                            f"Could not find '{conn}' connection filter button."
                        )

        except pyautogui.PyAutoGUIException as e:
            logger.error(f"A PyAutoGUI error occurred during filtering: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred during filtering: {e}")

        return state

    def identify_profiles(self, state):
        """
        Takes a long screenshot and uses Gemini to identify profiles to connect with.
        """
        logger.info("Identifying profiles to connect with...")

        try:
            # Define the region for the screenshot (adjust as needed)
            # This should be the main content area of the search results
            screen_width, screen_height = pyautogui.size()
            screenshot_rect = (
                int(screen_width * 0.2),
                150,
                int(screen_width * 0.6),
                screen_height - 200,
            )

            logger.debug(f"Taking a scrolling screenshot of region: {screenshot_rect}")
            full_page_image = scroll_screenshot(screenshot_rect)

            # Save the image for debugging
            full_page_image.save("full_page_screenshot.png")
            logger.info("Saved full page screenshot to 'full_page_screenshot.png'")

            # Convert image to base64
            with open("full_page_screenshot.png", "rb") as image_file:
                image_base64 = base64.b64encode(image_file.read()).decode("utf-8")

            # Prepare the prompt for the vision model
            prompt = [
                HumanMessage(
                    content=[
                        {
                            "type": "text",
                            "text": """
                        Analyze this screenshot of a LinkedIn search results page.
                        Identify all the "Connect" buttons for each person listed.
                        Return a JSON object with a key "connect_buttons" which is a list of dictionaries.
                        Each dictionary should contain the 'x' and 'y' coordinates of the center of a "Connect" button.
                        Example: {"connect_buttons": [{"x": 123, "y": 456}, {"x": 123, "y": 789}]}
                        """,
                        },
                        {
                            "type": "image_url",
                            "image_url": f"data:image/png;base64,{image_base64}",
                        },
                    ]
                )
            ]

            logger.info("Sending screenshot to Gemini for analysis...")
            response_content = smart_llm.invoke(prompt)

            # Clean the response to get valid JSON
            json_response_str = (
                response_content.strip().replace("```json", "").replace("```", "")
            )

            logger.debug(f"Cleaned JSON response string: {json_response_str}")

            response_data = json.loads(json_response_str)
            profiles = response_data.get("connect_buttons", [])
            logger.info(
                f"Identified {len(profiles)} potential profiles to connect with."
            )

            state["profiles_to_connect"] = profiles

        except Exception as e:
            logger.error(f"An error occurred in identify_profiles: {e}")
            state["profiles_to_connect"] = []

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
        workflow.add_node("identify_profiles", self.identify_profiles)

        workflow.set_entry_point("initial_search")

        workflow.add_conditional_edges(
            "initial_search",
            self.should_continue,
        )
        workflow.add_edge("filter_results", "identify_profiles")
        workflow.add_edge("identify_profiles", END)

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
            "initial_search_status": False,
            "profiles_to_connect": [],
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
        logger.warning(f"No search string provided. Using default: '{default_search}'.")
        search_string = default_search
    logger.debug(f"User input - search_string: {search_string}")

    companies_input = input(
        "Enter companies to filter by (comma-separated, e.g., Google,Microsoft): "
    )
    if not companies_input.strip():
        default_companies = "Google, Microsoft"
        logger.warning(f"No companies provided. Using default: '{default_companies}'.")
        companies_input = default_companies
    logger.debug(f"User input - companies_input raw: {companies_input}")
    companies = [c.strip() for c in companies_input.split(",") if c.strip()]

    connections_input = input(
        "Enter connection levels to filter by (e.g., 1st,2nd,3rd+): "
    )
    if not connections_input.strip():
        default_connections = ""
        logger.warning(
            f"No connections provided. Using default: '{default_connections}'."
        )
        connections_input = default_connections
    connections = [c.strip() for c in connections_input.split(",") if c.strip()]
    logger.debug(f"Parsed connections: {connections}")

    print("The Script will start in 5 seconds. Press Ctrl+C to cancel.")
    print("=" * 50)
    logger.info("Waiting 5 seconds before starting workflow.")
    countdown(5, "Bot starting...")

    logger.info("--- LinkedIn Connection Bot Starting ---")
    countdown(5, "Switch to your LinkedIn window...")

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
