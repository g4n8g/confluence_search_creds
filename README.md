# Confluence Credential & Attachment Extractor

This Python script automates searching for sensitive information in a Confluence instance, converting found pages to PDF, and downloading all attachments from those pages.

> **Note:** You must manually set your Confluence `BASE_URL`, as well as valid `JSESSIONID` and `seraph.confluence` cookie values in the script before running.

---

## Table of Contents

- [Features](#features)  
- [Prerequisites](#prerequisites)  
---

## Features

- Reads a list of keywords (English & Russian) from `wordlist.txt`.
- For each keyword, performs a CQL search (`/rest/searchv3/1.0/cqlSearch`) on your Confluence instance.
- Converts the HTML content of each matching page into a PDF.
- Extracts all attachments (any file type) linked on those pages and downloads them.
- Prints all status messages and errors directly to the console.

---

## Prerequisites

1. **Python 3.6+**  
2. **Pip** (or another package manager for Python)  
3. **System packages for PDF rendering**  
   On Debian/Ubuntu:
   ```bash
   sudo apt update
   sudo apt install libpangocairo-1.0-0 libpangoft2-1.0-0 libgdk-pixbuf2.0-0 libcairo2
   pip install requests beautifulsoup4 weasyprint
