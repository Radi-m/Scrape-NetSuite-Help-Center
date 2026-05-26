import time
import secret
import traceback
from datetime import datetime
from bs4 import BeautifulSoup
from tqdm import tqdm

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException

# --- LOCATORS ---
SECURITY_QUESTION_LABEL_LOCATOR = (By.XPATH, "//td[normalize-space()='Question:']/following-sibling::td")
SECURITY_ANSWER_INPUT_LOCATOR = (By.NAME, 'answer')
SECURITY_SUBMIT_BUTTON_LOCATOR = (By.NAME, 'submitter')

OUTPUT_FILE = './out/Order Management.html'
DRIVER_PATH = './chromedriver.exe'

# Toggle to also generate a Markdown version of the scraped content.
# When True, a .md file (same basename as OUTPUT_FILE) will be produced.
GENERATE_MD = True

# --- SCRAPE SUBJECT ---
# Format: 'MainTitle|SubTitle' (e.g., 'SuiteCloud Platform|SuiteScript')
SUBJECT_TO_SCRAPE = 'Order Management'

# --- MARKDOWN CONVERSION (lightweight) ---
def _html_to_markdown(html: str) -> str:
    """Convert a subset of HTML produced by the Help Center into Markdown.

    This is intentionally lightweight to avoid adding external dependencies.
    If you need fuller fidelity, consider installing a library such as
    `markdownify` and replacing this function's implementation.
    """
    soup = BeautifulSoup(html, 'html.parser')  # type: ignore

    lines: list[str] = []

    def handle(el, depth=0):  # recursive
        name = getattr(el, 'name', None)
        if name is None:  # NavigableString
            text = str(el)
            if text.strip():
                lines.append(text)
            return

        # Heading tags
        if name in [f'h{i}' for i in range(1, 7)]:
            level = int(name[1])
            heading_text = el.get_text(strip=True)
            if heading_text:
                lines.append('#' * level + ' ' + heading_text)
                lines.append('')
            return

        if name == 'p':
            para = el.get_text(' ', strip=True)
            if para:
                lines.append(para)
                lines.append('')
            return

        if name == 'pre':
            code_text = el.get_text('', strip=False)
            lines.append('```')
            lines.append(code_text.rstrip())
            lines.append('```')
            lines.append('')
            return

        if name == 'code' and el.parent and el.parent.name != 'pre':
            code_inline = el.get_text(strip=True)
            if code_inline:
                lines.append(f'`{code_inline}`')
            return

        if name in ('ul', 'ol'):
            for idx, li in enumerate([c for c in el.children if getattr(c, 'name', None) == 'li']):
                bullet = f"{idx+1}." if name == 'ol' else '*'
                li_text = li.get_text(' ', strip=True)
                if li_text:
                    lines.append(('  ' * depth) + f"{bullet} {li_text}")
            lines.append('')
            return

        if name == 'table':
            rows = el.find_all('tr', recursive=False)
            if rows:
                header_cells = rows[0].find_all(['th', 'td'])
                headers = [c.get_text(' ', strip=True) for c in header_cells]
                if headers:
                    lines.append('| ' + ' | '.join(headers) + ' |')
                    lines.append('| ' + ' | '.join(['---'] * len(headers)) + ' |')
                    for r in rows[1:]:
                        cells = r.find_all(['td', 'th'])
                        row_vals = [c.get_text(' ', strip=True) for c in cells]
                        lines.append('| ' + ' | '.join(row_vals) + ' |')
                    lines.append('')
            return

        # Generic container: recurse into children
        for child in el.children:
            handle(child, depth=depth + (1 if name in ('ul', 'ol') else 0))

    for child in soup.children:
        handle(child)

    # Collapse excessive blank lines
    cleaned = []
    prev_blank = False
    for ln in lines:
        if ln.strip() == '':
            if not prev_blank:
                cleaned.append('')
            prev_blank = True
        else:
            cleaned.append(ln.rstrip())
            prev_blank = False
    return '\n'.join(cleaned).strip() + '\n'

def login_and_get_session(driver):
    """Logs into NetSuite, handling the security question page if it appears."""
    print(f"Navigating to login page: {secret.NETSUITE_LOGIN_PAGE}")
    driver.get(secret.NETSUITE_LOGIN_PAGE)
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
    driver.get(secret.HELP_CENTER_URL)

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
            expand_img = node_container.find_element(By.XPATH, f".//img[contains(@id, '{node_id}_ti')]")
            if 'plus.png' in expand_img.get_attribute('src'):
                driver.execute_script("arguments[0].click();", expand_img)
                wait.until(EC.presence_of_element_located((By.ID, f"{node_id}_c")))
        except NoSuchElementException: pass
        search_context = node_container

    final_target_container = search_context

    # 2. Fully Expand Sub-Tree
    print("Force-expanding entire sub-tree...")
    attempts = 0
    while attempts < 30:
        plus_icons = final_target_container.find_elements(By.XPATH, ".//img[contains(@src, 'plus.png')]")
        if not plus_icons:
            print("Expansion complete.")
            break

        print(f"  Found {len(plus_icons)} more nodes to expand...")
        for icon in list(plus_icons):
            try:
                # --- FIX: Changed {{...}} to {...} ---
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", icon)
                driver.execute_script("arguments[0].click();", icon)
                time.sleep(0.2)
            except StaleElementReferenceException:
                print("  (Stale element, re-scanning tree...)")
                break
        attempts += 1

    # 3. Collect IDs
    print("Collecting leaf node IDs...")
    leaf_node_spans = final_target_container.find_elements(By.XPATH, ".//span[@isfolder='0']")
    leaf_node_ids = [span.get_attribute('id') for span in leaf_node_spans if span.get_attribute('id')]
    print(f"Found {len(leaf_node_ids)} total leaf nodes to process.")
    return leaf_node_ids

def scrape_single_page(driver, wait, node_id, file_handle, progress_bar, md_handle=None):
    """
    Navigates to the help center, finds a specific node by ID, clicks it,
    and scrapes its content. This is the "atomic" operation.
    """
    driver.get(secret.HELP_CENTER_URL)

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
            return

        title = node.text
        # Update progress bar with the name of the current item
        progress_bar.set_description(f"Processing: {title}")

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
            # First, remove unwanted elements like footers and feedback forms
            for el in content_container.find_all(id=["nshelp_footer", "helpcenter_feedback"], class_=["nshelp_navheader"]): # type: ignore
                el.decompose()

            # Find and remove all "Related Topics" divs
            for related_topics_div in content_container.find_all('div', class_='nshelp_relatedtopics'): # type: ignore
                related_topics_div.decompose()

            # Find and remove all "Important" divs
            for important_div in content_container.find_all('div', class_='nshelp_imp'): # type: ignore
                important_div.decompose()

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

        # --- Markdown output (optional) ---
        if md_handle is not None:
            md_handle.write(f"# {title}\n\n")
            md_handle.write(f"**Source URL:** {current_url}\n\n")
            if path_text:
                md_handle.write(f"**Path:** `{path_text}`\n\n")
            if content_html:
                md_handle.write(_html_to_markdown(str(content_html)))
            md_handle.write('\n---\n\n')
        return True

    except Exception as e:
        # Update progress bar with warning message
        progress_bar.set_description(f"WARNING on node {node_id}. Skipping.")
        print(f"  WARNING: Could not process node with ID '{node_id}'. Skipping. Error: {type(e).__name__}")
        return False


if __name__ == '__main__':
    from selenium.webdriver.chrome.options import Options
    chrome_options = Options()
    chrome_options.add_argument('--log-level=3') # Suppresses most console messages
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])    
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 10)

    # HTML Boilerplate with improved styling
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
        pre[class*="language-"] span, pre code span {{
            background: none !important; /* Remove any background color from tokens */
            color: inherit !important; /* Make text color inherit from the <pre> tag */
            text-shadow: none !important;
        }}
    </style>
</head>
<body>
    <h1>Scraped NetSuite Documentation</h1>
    <h2 class="page-subtitle">{subject}</h2>
    <p>Generated on: {now}</p>
"""
    html_footer = "</body>\n</html>"

    if login_and_get_session(driver):
        try:
            # Phase 1: Get all the target IDs once
            all_ids = get_all_leaf_node_ids(driver, wait)
            total_leaves = len(all_ids)

            # Phase 2: Open the file and process each ID atomically
            output_filename = OUTPUT_FILE
            with open(output_filename, 'w', encoding='utf-8') as f:
                f.write(html_header.format(
                    subject=SUBJECT_TO_SCRAPE.replace('|', ' > '),
                    now=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))

                print("\n--- Phase 2: Scraping each page individually ---")
                progress_bar = tqdm(all_ids, unit="page", desc="Starting scrape")

                md_output_filename = None
                md_handle = None
                if GENERATE_MD:
                    base_no_ext = OUTPUT_FILE.rsplit('.', 1)[0]
                    md_output_filename = base_no_ext + '.md'
                    md_handle = open(md_output_filename, 'w', encoding='utf-8')
                    md_handle.write(f"# Scraped NetSuite Documentation\n\n")
                    md_handle.write(f"## {SUBJECT_TO_SCRAPE.replace('|', ' > ')}\n\n")
                    md_handle.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    md_handle.write('---\n\n')

                for node_id in progress_bar:
                    scrape_single_page(driver, wait, node_id, f, progress_bar, md_handle=md_handle)

                f.write(html_footer)
                if md_handle:
                    md_handle.close()
                print(f"\nScraping complete. HTML saved to '{output_filename}'" + (f" and Markdown saved to '{md_output_filename}'" if md_output_filename else ''))

        except Exception as e:
            print(f"A fatal error occurred: {e}")
            traceback.print_exc()

    print("Closing browser.")
    driver.quit()