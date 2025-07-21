# LinkedIn Connection Automation

## ⚠️ Disclaimer

This project is for educational purposes only. Automating interactions on LinkedIn is against their Terms of Service and can lead to account restrictions or suspension. **Use at your own risk.**

## Description

A Python script that automates sending connection requests on LinkedIn based on a search query. It uses UI automation to mimic user behavior.

## Prerequisites

- Python 3.x installed.
- A modern web browser (e.g., Chrome, Firefox).
- An active, logged-in LinkedIn session in the browser.
- The browser window with LinkedIn must be open, maximized, and visible on the screen for the UI automation to work correctly.

## Installation

1. **Clone the repository:**

    ```bash
    git clone https://github.com/your-username/linkedin-connection-automation.git
    cd linkedin-connection-automation
    ```

2. **(Recommended) Create and activate a virtual environment:**

    ```bash
    # On Windows
    python -m venv .venv
    .venv\Scripts\activate

    # On macOS/Linux
    python -m venv .venv
    source .venv/bin/activate
    ```

3. **Install the required dependencies:**
    *(Note: You will need to create a `requirements.txt` file with libraries like `pyautogui` and `Pillow`).*

    ```bash
    pip install -r requirements.txt
    ```

## Detailed Plan & Workflow

The automation follows these steps:

1. **Initial Search:**
    - The script focuses on the browser window and navigates to the LinkedIn search bar.
    - It types a predefined search query (e.g., "Software Engineer in Test") and presses Enter.
    - It filters the search results for "People".

2. **Identify & Connect (Loop):**
    - The script takes a screenshot of the current view.
    - Using image recognition, it locates all "Connect" buttons on the page for profiles that are not 1st-degree connections.
    - For each "Connect" button found:
        - It clicks the "Connect" button.
        - It clicks the "Add a note" option in the confirmation pop-up.
        - It types a predefined, personalized connection message.
        - It clicks the final "Send" button to dispatch the request.
        - It waits for a short, randomized interval to appear more human-like.

3. **Pagination:**
    - After processing all visible "Connect" buttons on a page, the script scrolls down and clicks the "Next" button to load the next page of results.
    - The process repeats from Step 2 until a predefined page limit is reached or no "Next" button is found.
