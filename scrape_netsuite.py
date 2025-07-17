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
# Format: 'MainTitle|SubTitle' (e.g., 'SuiteCloud Platform|SuiteScript')
SUBJECT_TO_SCRAPE = 'SuiteCloud Platform|SuiteScript|SuiteScript 2.x API Reference|SuiteScript 2.x Modules|N/action Module'

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

def get_all_documentation_links(driver, base_url):
    """
    Traverses a path, expands sub-nodes, and uses a robust "Find, Scroll, Click"
    pattern to collect leaf node links, avoiding both stale and visibility issues.
    """
    print(f"Navigating to Help Center: {HELP_CENTER_URL}")
    driver.get(HELP_CENTER_URL)
    wait = WebDriverWait(driver, 10)

    path_parts = SUBJECT_TO_SCRAPE.split('|')
    print(f"Starting traversal for path: {path_parts}")

    try:
        # --- Path traversal logic remains the same, it is working well ---
        search_context = driver
        for i, part in enumerate(path_parts):
            print(f"  -> Traversing to: '{part}'")
            node_text_span = wait.until(EC.visibility_of_element_located(
                (By.XPATH, f".//span[@isfolder='1' and text()='{part}']")
            ))
            node_container = node_text_span.find_element(By.XPATH, "./ancestor::span[1]")
            node_id = node_container.get_attribute('id')
            try:
                expand_img = node_container.find_element(By.XPATH, ".//img[contains(@id, '_ti')]")
                if 'plus.png' in expand_img.get_attribute('src'):
                    print(f"     Expanding '{part}'...")
                    driver.execute_script("arguments[0].click();", expand_img)
                    child_container_locator = (By.ID, f"{node_id}_c")
                    wait.until(EC.presence_of_element_located(child_container_locator))
                    print(f"     Expansion of '{part}' confirmed.")
            except NoSuchElementException:
                print(f"     '{part}' has no expand icon. Continuing.")
            search_context = node_container
            print(f"     Set new search context to element with ID: {node_id}")

        print("\nTraversal complete. Force-expanding all nodes under the final target.")
        final_target_container = search_context
        while True:
            plus_icons = final_target_container.find_elements(By.XPATH, ".//img[contains(@src, 'plus.png')]")
            if not plus_icons:
                print("Expansion of sub-tree is complete.")
                break
            print(f"Found {len(plus_icons)} more nodes to expand. Clicking first one...")
            try:
                driver.execute_script("arguments[0].click();", plus_icons[0])
                time.sleep(0.5)
            except StaleElementReferenceException:
                print("Caught expected StaleElementReferenceException, re-scanning tree...")
                continue
        
        # --- START OF THE CRITICAL FIX ---
        
        # STAGE 1: Collect stable identifiers (IDs). This part is correct.
        print("Collecting all leaf node IDs from the target sub-tree...")
        leaf_node_spans = final_target_container.find_elements(By.XPATH, ".//span[@isfolder='0']")
        leaf_node_ids = [span.get_attribute('id') for span in leaf_node_spans if span.get_attribute('id')]
        total_leaves = len(leaf_node_ids)
        print(f"Found {total_leaves} leaf node IDs to scrape.")
        all_links = []
        
        # STAGE 2: Loop through the IDs and apply the "Find, Scroll, Click" pattern.
        for i, node_id in enumerate(leaf_node_ids):
            try:
                # STEP 1: FIND - Wait only for presence, not clickability.
                node = wait.until(EC.presence_of_element_located((By.ID, node_id)))

                # STEP 2: SCROLL - Use JavaScript to bring the element into view.
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", node)
                # Add a tiny pause to ensure scrolling is complete before the next action.
                time.sleep(0.2) 

                # Now that it's in view, we can safely get its text.
                title = node.text
                print(f"  ({i+1}/{total_leaves}) Processing: {title}")
                
                # STEP 3: CLICK - Use the reliable JavaScript click.
                driver.execute_script("arguments[0].click();", node)
                
                # Wait for the result of the click.
                wait.until(EC.presence_of_element_located((By.ID, 'helpcenter_content')))
                
                current_url = driver.current_url
                if current_url not in all_links:
                    all_links.append(current_url)

            except Exception as e:
                # The error message now uses the ID, which is more reliable.
                print(f"Could not process leaf node with ID '{node_id}'. Error: {e}")

        # --- END OF THE CRITICAL FIX ---

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