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

def get_all_documentation_links(driver, base_url):
    """
    Traverses a path, expands all sub-nodes, and uses a robust "Find, Scroll, Click"
    pattern to collect leaf node links, gracefully skipping non-clickable labels.
    """
    print(f"Navigating to Help Center: {HELP_CENTER_URL}")
    driver.get(HELP_CENTER_URL)
    wait = WebDriverWait(driver, 10)

    path_parts = SUBJECT_TO_SCRAPE.split('|')
    print(f"Starting traversal for path: {path_parts}")

    try:
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
                if 'plus.png' in expand_img.get_attribute('src'): # type: ignore
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
        
        print("Collecting all leaf node IDs from the target sub-tree...")
        leaf_node_spans = final_target_container.find_elements(By.XPATH, ".//span[@isfolder='0']")
        leaf_node_ids = [span.get_attribute('id') for span in leaf_node_spans if span.get_attribute('id')]
        total_leaves = len(leaf_node_ids)
        print(f"Found {total_leaves} leaf node IDs to process.")
        all_links = []
        
        for i, node_id in enumerate(leaf_node_ids):
            try:
                node = wait.until(EC.presence_of_element_located((By.ID, node_id))) # type: ignore
                if not node.get_attribute('onclick'):
                    print(f"  ({i+1}/{total_leaves}) Skipping '{node.text}' (not a clickable link).")
                    continue
                
                title = node.text
                print(f"  ({i+1}/{total_leaves}) Processing: {title}")

                driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", node)
                time.sleep(0.2)
                
                driver.execute_script("arguments[0].click();", node)
                wait.until(EC.presence_of_element_located((By.ID, 'helpcenter_content')))
                
                current_url = driver.current_url
                if current_url not in all_links:
                    all_links.append(current_url)

            except Exception as e:
                try:
                    node_text = driver.find_element(By.ID, node_id).text
                    print(f"  WARNING: Could not process node '{node_text}' with ID '{node_id}'. It might be a text label. Skipping. Error: {type(e).__name__}")
                except:
                     print(f"  WARNING: Could not process node with ID '{node_id}'. Skipping. Error: {type(e).__name__}")

        print(f"\nCollected {len(all_links)} unique documentation pages from '{SUBJECT_TO_SCRAPE}'.")
        return all_links

    except Exception as e:
        print(f"An unexpected error occurred during link extraction: {e}")
        traceback.print_exc()
        return []

def scrape_content_and_save(driver, links, subject_to_scrape):
    """
    Visits each link, extracts its clean HTML content, and appends it as a
    semantically distinct <article> to a single, well-structured HTML file.
    Includes a CSS reset to fix code snippet rendering and removes unwanted sections.
    """
    if not links:
        print("No links were found to scrape.")
        return

    print(f"Starting to build single HTML output from {len(links)} pages...")
    
    html_header = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NetSuite SuiteScript Documentation</title>
    <style>
        /* General Body Styles */
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; max-width: 1200px; margin: 0 auto; padding: 20px; }}
        
        /* Scraped Content Containers */
        .scraped-page {{ border: 1px solid #ddd; border-radius: 8px; margin-bottom: 40px; padding: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }}
        .scraped-page.error {{ border-color: #d9534f; background-color: #f2dede; }}
        .metadata {{ background-color: #f7f7f7; border: 1px solid #eee; padding: 10px; margin-bottom: 20px; border-radius: 4px; }}
        .metadata p {{ margin: 5px 0; }}
        .content-snippet {{ margin-top: 20px; }}

        /* Typography */
        h1 {{ color: #1a0dab; border-bottom: 2px solid #eee; padding-bottom: 10px; margin-bottom: 5px; }}
        .page-subtitle {{ color: #555; font-weight: 400; font-size: 1.3rem; margin-top: 0; margin-bottom: 25px; }}
        
        /* Tables */
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; vertical-align: top; }}
        th {{ background-color: #f2f2f2; }}

        /* --- START OF THE FIX for Code Snippets --- */
        /* General code styles */
        code {{ font-family: "Courier New", Courier, monospace; }}

        /* Style for <pre> blocks (the whole code box) */
        pre, pre[class*="language-"] {{
            background-color: #f5f2f0 !important; /* A light, readable background */
            color: #333; /* Dark text for readability */
            padding: 15px;
            margin: 20px 0;
            border-radius: 5px;
            overflow-x: auto;
            border: 1px solid #ddd;
        }}

        /* CSS Reset for SPANs inside code blocks */
        /* This forces the syntax highlighting spans to inherit our desired text color */
        pre[class*="language-"] span, pre code span {{
            background: none !important; /* Remove any background color from tokens */
            color: inherit !important; /* Make text color inherit from the <pre> tag */
            text-shadow: none !important;
        }}
        /* --- END OF THE FIX --- */
    </style>
</head>
<body>
    <h1>Scraped NetSuite Documentation</h1>
    <h2 class="page-subtitle">{subtitle}</h2>
    <p>Generated on: {now}</p>
"""

    html_footer = """
</body>
</html>
"""

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        from datetime import datetime
        subtitle_text = subject_to_scrape.replace('|', ' > ')
        f.write(html_header.format(
            now=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            subtitle=subtitle_text
        ))

        for i, link in enumerate(links):
            print(f"Scraping ({i+1}/{len(links)}): {link}")
            try:
                driver.get(link)
                wait = WebDriverWait(driver, 20)
                wait.until(EC.presence_of_element_located((By.ID, 'helpcenter_content')))
                
                soup = BeautifulSoup(driver.page_source, 'html.parser')

                title_element = soup.find('h1', class_='nshelp_title')
                title = title_element.get_text(strip=True) if title_element else "Untitled"
                
                path_text = ""
                try:
                    nav_div = soup.find(id='ns_navigation')
                    if nav_div:
                        path_text = nav_div.get_text(separator=' > ', strip=True)
                except Exception:
                    print("  (Info: No navigation breadcrumbs found.)")

                content_html = ""
                content_div = soup.find('div', class_='nshelp_page')
                if not content_div:
                    content_div = soup.find('div', class_='nshelp_content')
                
                if content_div:
                    # CORRECTED: Use a CSS selector to find and remove all unwanted elements
                    unwanted_selector = "#nshelp_footer, #helpcenter_feedback, .nshelp_navheader, .nshelp_relatedtopics"
                    for element in content_div.select(unwanted_selector): # type: ignore
                        element.decompose()
                    content_html = content_div.prettify() # type: ignore
                else:
                    content_html = "<p>Error: Could not find main content div.</p>"

                f.write('<article class="scraped-page">\n')
                f.write(f'<h1>{title}</h1>\n')
                f.write('<div class="metadata">\n')
                f.write(f'<p><strong>Source URL:</strong> <a href="{link}" target="_blank">{link}</a></p>\n')
                if path_text:
                    f.write(f'<p><strong>Path:</strong> <code>{path_text}</code></p>\n')
                f.write('</div>\n<hr>\n')
                f.write('<div class="content-snippet">\n')
                f.write(content_html) # type: ignore
                f.write('</div>\n')
                f.write('</article>\n\n')
            
            except Exception as e:
                print(f"  ERROR: Could not process page {link}. Writing error to file.")
                traceback.print_exc()
                f.write(f'<article class="scraped-page error"><h1>Failed to scrape: {link}</h1><p>Error: {e}</p></article>\n')
                
        f.write(html_footer)

    print(f"\nScraping complete. All content saved to '{OUTPUT_FILE}'")    
        
if __name__ == '__main__':
    service = webdriver.ChromeService(executable_path=DRIVER_PATH)
    driver = webdriver.Chrome(service=service)
    
    if login_and_get_session(driver):
        current_url = driver.current_url
        base_url = f"{current_url.split('/app/')[0]}"
        
        doc_links = get_all_documentation_links(driver, base_url)
        
        if doc_links:
            scrape_content_and_save(driver, doc_links, SUBJECT_TO_SCRAPE)
            
    print("Closing browser.")
    driver.quit()