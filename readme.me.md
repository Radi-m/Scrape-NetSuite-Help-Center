
# NetSuite Documentation Scraper

This Python script uses Selenium to automate logging into a NetSuite account, navigating to the Help Center, and recursively scraping a specified documentation section. The final output is a single, clean, and styled HTML file for easy offline viewing and searching.

## Key Features

-   **Automated Login:** Logs into NetSuite using your provided credentials.
-   **Security Question Handling:** Automatically detects and answers security questions if they appear during login.
-   **Targeted Scraping:** You can specify the exact documentation path you want to scrape (e.g., `SuiteCloud Platform|SuiteScript|SuiteScript 2.x API Reference`).
-   **Recursive Tree Expansion:** Intelligently expands all nested topics within your target section to find every single documentation page.
-   **Single HTML Output:** Combines all scraped pages into one `netsuite_suitescript_docs.html` file.
-   **Clean & Styled Content:**
    -   Removes unnecessary elements like headers, footers, and feedback forms.
    -   Applies clean, readable CSS for a better user experience.
    -   **Includes a crucial CSS fix** to ensure code snippets are rendered correctly, which is often a problem with web scraping.
-   **Offline Access:** Once generated, the HTML file provides fast, offline access to the documentation you need.

## Prerequisites

Before you begin, ensure you have the following installed:

1.  **Python 3.x:** [Download Python](https://www.python.org/downloads/)
2.  **Google Chrome:** The script is configured to use Chrome. [Download Chrome](https://www.google.com/chrome/).
3.  **ChromeDriver:** This is required for Selenium to control the Chrome browser.
    -   **Important:** The version of ChromeDriver **must** match your version of Google Chrome.
    -   Check your Chrome version by going to `chrome://settings/help`.
    -   [Download the matching ChromeDriver](https://googlechromelabs.github.io/chrome-for-testing/) and place the `chromedriver.exe` (or `chromedriver` on Linux/macOS) file in the project's root directory.

## Setup and Installation

1.  **Clone the Repository**
    ```bash
    git clone <your-repository-url>
    cd <your-repository-directory>
    ```

2.  **Install Python Dependencies**
    It's recommended to use a virtual environment.
    ```bash
    # Create and activate a virtual environment (optional but recommended)
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`

    # Install the required packages
    pip install selenium beautifulsoup4
    ```

3.  **Configure Credentials**

    This is the most important step. You must provide your NetSuite credentials in a `secret.py` file. A template is provided.

    **Rename the template file:**
    ```bash
    # On Linux/macOS
    mv secret_template.py secret.py

    # On Windows
    copy secret_template.py secret.py
    ```

    **Edit `secret.py` and fill in your details:**

    ```python
    # secret.py

    # These URLs are typically not needed for the scraper to work,
    # but are kept here for reference.
    NETSUITE_BASE_URL = 'https://<1234567>.app.netsuite.com'
    NETSUITE_LOGIN_PAGE = 'https://system.netsuite.com/pages/customerlogin.jsp?country=US'
    HELP_CENTER_URL = 'https://<1234567>.app.netsuite.com/app/help/helpcenter.nl'

    # --- REQUIRED FIELDS ---
    EMAIL = 'your-netsuite-email@example.com'
    PASSWORD = 'YourNetSuitePassword'

    # The 'key' must be the EXACT text of the question from the page.
    # The 'value' is the answer. Add all your possible questions.
    SECURITY_QUESTIONS = {
        "What was your childhood nickname?": "YourAnswerHere",
        "In what city or town was your first job?": "AnotherAnswer",
        "What is the name of your favorite pet?": "Fido",
        # Add all other possible security questions and answers here
    }
    ```
    > **Security Note:** The `secret.py` file contains sensitive information. Ensure it is included in your `.gitignore` file to prevent it from being committed to version control.

## How to Use

1.  **Configure the Scrape Target**

    Open the `scrape_netsuite.py` file and modify the `SUBJECT_TO_SCRAPE` constant. This variable defines the documentation path you want to download. The format is a string with topics separated by `|`.

    For example, to scrape the `N/action` module documentation:
    ```python
    # scrape_netsuite.py

    SUBJECT_TO_SCRAPE = 'SuiteCloud Platform|SuiteScript|SuiteScript 2.x API Reference|SuiteScript 2.x Modules|N/action Module'
    ```

2.  **Run the Scraper**

    Execute the script from your terminal:
    ```bash
    python scrape_netsuite.py
    ```

    The script will print its progress to the console, including login status, tree traversal, and the scraping of each page.

3.  **View the Output**

    Once the script is finished, an HTML file named `netsuite_suitescript_docs.html` will be created in the project directory. Open this file in any web browser to view the scraped documentation.

## Customization

You can modify the following constants at the top of `scrape_netsuite.py` to change the script's behavior:

-   `OUTPUT_FILE`: Change the name of the final generated HTML file.
-   `DRIVER_PATH`: If you placed `chromedriver.exe` somewhere other than the root directory, update this path.

## Disclaimer

This script is intended for personal use to create an offline backup of documentation for easier access. Be mindful of NetSuite's terms of service. The authors are not responsible for any misuse of this script or any issues with your NetSuite account that may arise from its use.