import time
import secret
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from bs4 import BeautifulSoup
import traceback

# --- LOCATORS ---
SECURITY_QUESTION_LABEL_LOCATOR = (By.XPATH, "//td[normalize-space()='Question:']/following-sibling::td")
SECURITY_ANSWER_INPUT_LOCATOR = (By.NAME, 'answer')
SECURITY_SUBMIT_BUTTON_LOCATOR = (By.NAME, 'submitter')

# --- SCRIPT CONFIGURATION ---
NETSUITE_LOGIN_PAGE = 'https://system.netsuite.com/pages/customerlogin.jsp'
HELP_CENTER_URL = 'https://5025918-sb1.app.netsuite.com/app/help/helpcenter.nl'

OUTPUT_FILE = 'netsuite_suitescript_docs.html'
DRIVER_PATH = './chromedriver.exe'

# --- SCRAPE SUBJECT ---
# Format: 'MainTitle|SubTitle' (e.g., 'SuiteCloud Platform|SuiteScript')
SUBJECT_TO_SCRAPE = 'SuiteCloud Platform|SuiteScript|SuiteScript 2.x API Reference|SuiteScript 2.x Modules'

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

def get_all_leaf_node_ids(driver, wait):
    """
    Navigates to the target, fully expands the tree, and returns a list of all leaf node IDs.
    This function is run only ONCE.
    """
    print("--- Phase 1: Collecting all leaf node IDs ---")
    driver.get(HELP_CENTER_URL)
    
    # 1. Traverse Path
    path_parts = SUBJECT_TO_SCRAPE.split('|')
    print(f"Traversing to: {SUBJECT_TO_SCRAPE}")
    search_context = driver
    for part in path_parts:
        node_text_span = wait.until(EC.visibility_of_element_located(
            (By.XPATH, f".//span[@isfolder='1' and text()='{part}']")
        ))
        node_container = node_text_span.find_element(By.XPATH, "./ancestor::span[1]")
        node_id = node_container.get_attribute('id')
        try:
            expand_img = node_container.find_element(By.XPATH, ".//img[contains(@id, '_ti')]")
            if 'plus.png' in expand_img.get_attribute('src'):
                driver.execute_script("arguments[0].click();", expand_img)
                wait.until(EC.presence_of_element_located((By.ID, f"{node_id}_c")))
        except NoSuchElementException: pass
        search_context = node_container
    
    final_target_container = search_context
    
    # 2. Fully Expand Sub-Tree
    print("Force-expanding entire sub-tree...")
    attempts = 0
    while attempts < 30: # Increased safety break
        plus_icons = final_target_container.find_elements(By.XPATH, ".//img[contains(@src, 'plus.png')]")
        if not plus_icons:
            print("Expansion complete.")
            break
        
        print(f"  Found {len(plus_icons)} more nodes to expand...")
        for icon in list(plus_icons):
            try:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", icon)
                driver.execute_script("arguments[0].click();", icon)
                time.sleep(0.2) # Small pause for DOM update
            except StaleElementReferenceException:
                print("  (Stale element, re-scanning tree...)")
                break # Re-scan from the top of the while loop
        attempts += 1

    # 3. Collect IDs
    print("Collecting leaf node IDs...")
    leaf_node_spans = final_target_container.find_elements(By.XPATH, ".//span[@isfolder='0']")
    leaf_node_ids = [span.get_attribute('id') for span in leaf_node_spans if span.get_attribute('id')]
    print(f"Found {len(leaf_node_ids)} total leaf nodes to process.")
    return leaf_node_ids

def scrape_single_page(driver, wait, node_id, file_handle):
    """
    Navigates to the help center, finds a specific node by ID, clicks it,
    and scrapes its content. This is the "atomic" operation.
    """
    driver.get(HELP_CENTER_URL)
    
    # Find the node and its parents
    try:
        # We need to expand all parents of the target node
        parts = node_id.replace('_tnidtitle', '').split('||')
        current_path_id = ""
        for i in range(len(parts) - 1):
            current_path_id = "||".join(parts[:i+1])
            parent_node = wait.until(EC.presence_of_element_located((By.ID, current_path_id)))
            try:
                expand_img = parent_node.find_element(By.XPATH, f".//img[@id='{current_path_id}_ti']")
                if 'plus.png' in expand_img.get_attribute('src'):
                    driver.execute_script("arguments[0].click();", expand_img)
                    wait.until(EC.presence_of_element_located((By.ID, f"{current_path_id}_c")))
            except NoSuchElementException: pass
            
        # Now find the final target node
        node = wait.until(EC.presence_of_element_located((By.ID, node_id)))
        if not node.get_attribute('onclick'):
            return # Skip non-clickable labels

        title = node.text
        print(f"  Processing: {title}")

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", node)
        time.sleep(0.2)
        driver.execute_script("arguments[0].click();", node)
        
        # Scrape content
        content_wait = WebDriverWait(driver, 20)
        content_div_element = content_wait.until(EC.presence_of_element_located((By.ID, 'helpcenter_content')))
        current_url = driver.current_url
        soup = BeautifulSoup(content_div_element.get_attribute('outerHTML'), 'html.parser') # type: ignore
        
        path_text = ""
        if soup.find(id='ns_navigation'):
            path_text = soup.find(id='ns_navigation').get_text(separator=' > ', strip=True) # type: ignore

        content_html = ""
        content_container = soup.find('div', class_='nshelp_page') or soup.find('div', class_='nshelp_content')
        if content_container:
            for el in content_container.find_all(id=["nshelp_footer", "helpcenter_feedback"], class_=["nshelp_navheader"]): # type: ignore
                el.decompose()
            content_html = content_container.prettify() # type: ignore
        
        # Assemble and write the <article> block
        file_handle.write('<article class="scraped-page">\n')
        file_handle.write(f'<h1>{title}</h1>\n')
        file_handle.write('<div class="metadata">\n')
        file_handle.write(f'<p><strong>Source URL:</strong> <a href="{current_url}" target="_blank">{current_url}</a></p>\n')
        if path_text: file_handle.write(f'<p><strong>Path:</strong> <code>{path_text}</code></p>\n')
        file_handle.write('</div>\n<hr>\n')
        file_handle.write('<div class="content-snippet">\n')
        file_handle.write(content_html)
        file_handle.write('</div>\n</article>\n\n')
        return True

    except Exception as e:
        print(f"  WARNING: Could not process node with ID '{node_id}'. Skipping. Error: {type(e).__name__}")
        return False


if __name__ == '__main__':
    service = webdriver.ChromeService(executable_path=DRIVER_PATH)
    driver = webdriver.Chrome(service=service)
    wait = WebDriverWait(driver, 10)

    # HTML Boilerplate
    html_header = """...""" # Keep your existing HTML header
    html_footer = "</body>\n</html>"

    if login_and_get_session(driver):
        try:
            # Phase 1: Get all the target IDs once
            all_ids = get_all_leaf_node_ids(driver, wait)
            total_leaves = len(all_ids)

            # Phase 2: Open the file and process each ID atomically
            output_filename = OUTPUT_FILE.replace('.md', '.html')
            with open(output_filename, 'w', encoding='utf-8') as f:
                from datetime import datetime
                f.write(html_header.format(
                    subject=SUBJECT_TO_SCRAPE,
                    now=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))

                print("\n--- Phase 2: Scraping each page individually ---")
                for i, node_id in enumerate(all_ids):
                    print(f"Scraping node ({i+1}/{total_leaves}) ID: {node_id}")
                    scrape_single_page(driver, wait, node_id, f)
                
                f.write(html_footer)
                print(f"\nScraping complete. All content saved to '{output_filename}'")
        
        except Exception as e:
            print(f"A fatal error occurred: {e}")
            traceback.print_exc()

    print("Closing browser.")
    driver.quit()