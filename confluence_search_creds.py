import os
import time
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from weasyprint import HTML

# === Configuration ===
BASE_URL = "http://<url>:8090"
COOKIES = {
    "JSESSIONID": "<enter_jsessionid>",
    "seraph.confluence": "<enter_seraph_confluence>"
}
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Host": urlparse(BASE_URL).netloc
}

LIMIT = 100
WORDLIST_PATH = "wordlist.txt"
OUTPUT_DIR = "confluence_pdfs"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def load_wordlist(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"[!] Error loading wordlist '{path}': {e}")
        return []

def search_confluence(word):
    start = 0
    urls = []
    cql = f'siteSearch ~ "{word}" AND type NOT IN ("user")'
    while True:
        try:
            response = requests.get(
                f"{BASE_URL}/rest/searchv3/1.0/cqlSearch",
                headers=HEADERS,
                cookies=COOKIES,
                params={
                    "cql": cql,
                    "start": start,
                    "limit": LIMIT,
                    "excerpt": "highlight",
                    "includeArchivedSpaces": "true"
                },
                verify=False
            )
        except Exception as e:
            print(f"[!] Connection error while searching for '{word}': {e}")
            break

        if response.status_code != 200:
            print(f"[HTTP {response.status_code}] CQL query error for word '{word}'")
            break

        try:
            data = response.json()
        except Exception as e:
            print(f"[!] JSON parse error for word '{word}': {e}")
            print("Server response:", response.text[:500])
            break

        results = data.get("results", [])
        if not results:
            break

        for result in results:
            content = result.get("content", {})
            webui = content.get("_links", {}).get("webui", "")
            title = content.get("title", "unknown").replace("/", "_")
            if webui:
                clean_path = webui.split("?")[0]
                full_url = urljoin(BASE_URL, clean_path)
                print(f"[+] Found page: {full_url} (title: '{title}')")
                urls.append((full_url, title))

        start += LIMIT
        time.sleep(0.5)

    return urls

def download_html_and_save_pdf(url, title):
    try:
        response = requests.get(url, headers=HEADERS, cookies=COOKIES, verify=False)
    except Exception as e:
        print(f"[!] Connection error while downloading {url}: {e}")
        return None

    if response.status_code != 200:
        print(f"[HTTP {response.status_code}] Failed to load page {url}")
        return None

    html_text = response.text
    try:
        soup = BeautifulSoup(html_text, "html.parser")
        pretty_html = soup.prettify()
        pdf_filename = os.path.join(OUTPUT_DIR, f"{title}.pdf")
        HTML(string=pretty_html, base_url=BASE_URL).write_pdf(pdf_filename)
        print(f"[+] PDF saved: {pdf_filename}")
    except Exception as e:
        print(f"[!] PDF conversion error for {url}: {e}")

    return html_text

def extract_attachments(html_text):
    attachments = []
    try:
        soup = BeautifulSoup(html_text, "html.parser")
        for link in soup.find_all("a", href=True):
            href = link["href"]
            if "/download/attachments/" in href:
                clean_href = href.split("?")[0]
                full_url = urljoin(BASE_URL, clean_href)
                filename = os.path.basename(clean_href)
                attachments.append((full_url, filename))
    except Exception as e:
        print(f"[!] Error parsing HTML for attachments: {e}")
    return attachments

def download_attachments(attachments, attachment_dir):
    os.makedirs(attachment_dir, exist_ok=True)
    for full_url, filename in attachments:
        try:
            response = requests.get(full_url, headers=HEADERS, cookies=COOKIES, verify=False)
        except Exception as e:
            print(f"[!] Connection error while downloading attachment {full_url}: {e}")
            continue

        if response.status_code == 200:
            save_path = os.path.join(attachment_dir, filename)
            try:
                with open(save_path, "wb") as f:
                    f.write(response.content)
                print(f"[+] Attachment saved: {save_path}")
            except Exception as e:
                print(f"[!] Failed to save attachment '{filename}': {e}")
        else:
            print(f"[HTTP {response.status_code}] Failed to download attachment {full_url}")

def main():
    print("[*] Loading wordlist...")
    words = load_wordlist(WORDLIST_PATH)
    if not words:
        print("[!] Wordlist is empty or failed to load. Exiting.")
        return

    seen_urls = set()

    for word in words:
        print(f"[*] Searching for word: '{word}'")
        found = search_confluence(word)
        for url, title in found:
            if url in seen_urls:
                continue
            seen_urls.add(url)

            html_text = download_html_and_save_pdf(url, title)
            if not html_text:
                continue

            attachments = extract_attachments(html_text)
            if attachments:
                safe_title = title.replace("/", "_")
                attach_dir = os.path.join(OUTPUT_DIR, "attachments", safe_title)
                print(f"[*] Found {len(attachments)} attachments on page '{title}'. Downloading to '{attach_dir}'")
                download_attachments(attachments, attach_dir)
            else:
                print(f"[*] No attachments found on page '{title}'")

    print(f"[*] Finished. All PDFs and attachments are in '{OUTPUT_DIR}'")

if __name__ == "__main__":
    main()
