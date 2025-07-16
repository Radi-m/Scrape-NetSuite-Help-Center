import time
import secret
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import traceback

# --- LOCATORS ---
SECURITY_QUESTION_LABEL_LOCATOR = (By.XPATH, "//td[normalize-space()='Question:']/following-sibling::td")
SECURITY_ANSWER_INPUT_LOCATOR = (By.NAME, 'answer')
SECURITY_SUBMIT_BUTTON_LOCATOR = (By.NAME, 'submitter')

# --- SCRIPT CONFIGURATION ---
NETSUITE_LOGIN_PAGE = 'https://system.netsuite.com/pages/customerlogin.jsp'
HELP_CENTER_URL = 'https://5025918-sb1.app.netsuite.com/app/help/helpcenter.nl'

OUTPUT_FILE = 'netsuite_suitescript_docs.md'
DRIVER_PATH = './chromedriver.exe'

# --- SCRAPE SUBJECT ---
# Format: 'MainTitle/SubTitle' (e.g., 'SuiteCloud Platform/SuiteScript')
SUBJECT_TO_SCRAPE = 'SuiteCloud Platform/SuiteScript'

def login_and_get_session(driver):
    """Logs into NetSuite, handling the security question page if it appears."""
    print(f"Navigating to login page: {NETSUITE_LOGIN_PAGE}")
    driver.get(NETSUITE_LOGIN_PAGE)
    wait = WebDriverWait(driver, 30)
    try:
        wait.until(EC.presence_of_element_located((By.ID, 'email'))).send_keys(secret.EMAIL)
        driver.find_element(By.ID, 'password').send_keys(secret.PASSWORD)
        driver.find_element(By.ID, 'login-submit').click()
        print("Credentials submitted. Checking for dashboard or security question...")

        wait.until(EC.any_of(
            EC.presence_of_element_located(SECURITY_ANSWER_INPUT_LOCATOR),
            EC.url_contains('/app/center/card.nl')
        ))
        try:
            answer_input = driver.find_element(*SECURITY_ANSWER_INPUT_LOCATOR)
            print("Security question page detected.")
            question_element = driver.find_element(*SECURITY_QUESTION_LABEL_LOCATOR)
            question_text = question_element.text.strip()
            print(f"Question asked: '{question_text}'")

            if question_text in secret.SECURITY_QUESTIONS:
                answer = secret.SECURITY_QUESTIONS[question_text]
                print("Found matching question. Submitting answer.")
                answer_input.send_keys(answer)
                driver.find_element(*SECURITY_SUBMIT_BUTTON_LOCATOR).click()
                print("Answer submitted. Waiting for dashboard to load...")
                wait.until(EC.url_contains('/app/center/card.nl'))
                print("Dashboard loaded after security question. Login successful!")
                return True
            else:
                print(f"ERROR: The security question '{question_text}' was not found in your secret.py file.")
                return False
        except NoSuchElementException:
            print("Direct login to dashboard detected. Login successful!")
            return True
    except TimeoutException:
        print("Login failed. Neither the security question page nor the dashboard loaded in time.")
        return False
    except Exception as e:
        print(f"An unexpected error occurred during login: {e}")
        return False

# --- REVISED AND TARGETED FUNCTION ---

def get_all_documentation_links(driver, base_url):
    """
    Traverses a specific path (e.g., 'A/B/C'), then expands all sub-nodes
    under the final node 'C' and collects all of its leaf node links.
    """
    print(f"Navigating to Help Center: {HELP_CENTER_URL}")
    driver.get(HELP_CENTER_URL)
    wait = WebDriverWait(driver, 30)

    # You can now use deeper paths, for example:
    # SUBJECT_TO_SCRAPE = 'SuiteCloud Platform/SuiteScript/SuiteScript 2.x API Reference'
    path_parts = SUBJECT_TO_SCRAPE.split('/')
    print(f"Starting traversal for path: {path_parts}")

    try:
        # Start the search from the top of the document
        search_context = driver

        # Step 1: Traverse the provided path, expanding as we go
        for i, part in enumerate(path_parts):
            print(f"  -> Traversing to: '{part}'")

            # Find the text span for the current part of the path within the current context.
            # The .// is crucial: it means "search within the current context's descendants".
            # We wait for it to be visible before proceeding.
            node_text_span = wait.until(EC.visibility_of_element_located(
                (By.XPATH, f".//span[@isfolder='1' and text()='{part}']")
            ))

            # Find the container of this node. This will be our new search context.
            node_container = node_text_span.find_element(By.XPATH, "./ancestor::span[1]")

            # Now, check if this node needs to be expanded.
            try:
                # Find the expand/collapse image within this node's row
                expand_img = node_container.find_element(By.XPATH, ".//img[contains(@id, '_ti')]")
                if 'plus.png' in expand_img.get_attribute('src'):
                    print(f"     Expanding '{part}'...")
                    driver.execute_script("arguments[0].click();", expand_img)
                    time.sleep(2) # Wait for children to be loaded into the DOM
            except NoSuchElementException:
                # This node might be a leaf or doesn't have an expand icon. We can ignore it.
                print(f"     '{part}' has no expand icon. Continuing.")
                pass

            # Update the search context to the container of the node we just found.
            # The next iteration will only search inside this container.
            search_context = node_container
            print(f"     Set new search context to element with ID: {search_context.get_attribute('id')}")

        # Step 2: Now that we are at our target, expand all of its children
        print("\nTraversal complete. Force-expanding all nodes under the final target.")
        final_target_container = search_context
        
        while True:
            # Find all visible "plus" icons WITHIN our final target container
            plus_icons = final_target_container.find_elements(By.XPATH, ".//img[contains(@src, 'plus.png')]")

            if not plus_icons:
                print("Expansion of sub-tree is complete.")
                break

            print(f"Found {len(plus_icons)} more nodes to expand. Clicking first one...")
            try:
                # Click the first available icon. The loop will restart and find new ones.
                driver.execute_script("arguments[0].click();", plus_icons[0])
                time.sleep(1) # Wait for UI to update
            except StaleElementReferenceException:
                print("Caught expected StaleElementReferenceException, re-scanning tree...")
                continue
        
        # Step 3: Collect all leaf nodes (isfolder="0") from the final container
        print("Collecting all leaf node links from the target sub-tree...")
        leaf_nodes = final_target_container.find_elements(By.XPATH, ".//span[@isfolder='0']")
        total_leaves = len(leaf_nodes)
        print(f"Found {total_leaves} leaf nodes to scrape.")
        all_links = []
        
        for i, node in enumerate(leaf_nodes):
            try:
                title = node.text
                print(f"  ({i+1}/{total_leaves}) Processing: {title}")
                driver.execute_script("arguments[0].click();", node)
                wait.until(EC.presence_of_element_located((By.ID, 'helpcenter_content')))
                
                current_url = driver.current_url
                if current_url not in all_links:
                    all_links.append(current_url)

            except Exception as e:
                print(f"Could not process leaf node '{node.text if node else 'UNKNOWN'}'. Error: {e}")

        print(f"\nCollected {len(all_links)} unique documentation pages from '{SUBJECT_TO_SCRAPE}'.")
        return all_links

    except Exception as e:
        print(f"An unexpected error occurred during link extraction: {e}")
        traceback.print_exc()
        return []

def scrape_content_and_save(driver, links):
    """Visits each link from the provided list, scrapes its content, and saves it to a markdown file."""
    if not links:
        print("No links were found to scrape.")
        return

    print(f"Starting to scrape {len(links)} pages...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for i, link in enumerate(links):
            print(f"Scraping ({i+1}/{len(links)}): {link}")
            try:
                driver.get(link)
                content_div = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.ID, 'helpcenter_content'))
                )
                soup = BeautifulSoup(content_div.get_attribute('outerHTML'), 'html.parser') # type: ignore
                
                title_element = soup.find('h1', class_='nshelp_title')
                title = title_element.get_text(strip=True) if title_element else driver.title.replace('NetSuite Help Center - ', '')
                content_text = soup.get_text(separator='\n', strip=True)
                
                f.write(f"# {title}\n\n")
                f.write(f"**Source URL:** <{link}>\n\n")
                f.write(f"{content_text}\n\n---\n\n")
            except Exception as e:
                print(f"Could not scrape page {link}. Error: {e}")
                f.write(f"# Failed to scrape content from {link}\n\n---\n\n")
                
    print(f"Scraping complete. Content saved to '{OUTPUT_FILE}'.")


if __name__ == '__main__':
    service = webdriver.ChromeService(executable_path=DRIVER_PATH)
    driver = webdriver.Chrome(service=service)
    
    if login_and_get_session(driver):
        current_url = driver.current_url
        base_url = f"{current_url.split('/app/')[0]}"
        
        doc_links = get_all_documentation_links(driver, base_url)
        
        if doc_links:
            scrape_content_and_save(driver, doc_links)
            
    print("Closing browser.")
    driver.quit()