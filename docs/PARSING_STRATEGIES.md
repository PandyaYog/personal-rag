# 📄 Document Parsing Strategies

Parsing is the "hidden mess" of RAG systems. Before we can chunk or embed anything, we must reliably extract clean text from a chaotic variety of file formats.

This project implements a **Robust Multi-Stage Parsing Engine** that handles everything from modern PDFs to legacy 90s Office files. It is designed to fail gracefully and try multiple extraction methods before giving up.

---

## 🏗️ The Complexity of Parsing

Why is this a separate module?
1.  **Encoding Hell:** Text isn't always UTF-8. It can be Latin-1, CP1252, or ASCII. We handle this automatically.
2.  **Binary vs. XML:** Modern Office files (`.docx`) are XML-based and easy to parse. Legacy files (`.doc`) are binary blobs requiring external tools.
3.  **Structure Preservation:** For CSVs and Excel, simply dumping text destroys the meaning. We preserve row/column relationships.

---

## 🛠️ Supported Formats & Strategies

### 1. PDF Documents (`.pdf`)
*   **Primary Tool:** `pdfplumber`
*   **Strategy:** Iterates through pages and extracts text layout-aware.
*   **Why:** Unlike simple text dumpers, `pdfplumber` is better at handling multi-column layouts.

### 2. Modern Office Files (`.docx`, `.pptx`)
*   **Primary Tool:** `unstructured` (The gold standard for document partitioning).
*   **Fallback:** `python-docx` / `python-pptx` (Native Python libraries).
*   **Strategy:** We try the heavy-duty `unstructured` library first. If it fails (e.g., missing system dependencies), we fall back to the lighter native libraries.

### 3. Legacy Office Files (`.doc`, `.ppt`)
*   **Challenge:** These are proprietary binary formats that Python cannot read natively.
*   **Strategy 1 (DOC):** `antiword` (A lightweight command-line utility).
*   **Strategy 2 (PPT):** `LibreOffice` (Headless mode). We spin up a temporary LibreOffice instance to convert the file to text/PDF, then extract from there.
*   **Note:** This requires `antiword` and `libreoffice` to be installed on the host system/container.

### 4. Structured Data (`.csv`, `.xlsx`)
*   **Challenge:** "Cell A1: Name, Cell B1: Age" becomes "Name Age" if blindly extracted, losing the connection.
*   **Strategy:**
    1.  Load into `pandas` DataFrame.
    2.  Convert each row into a JSON-like string: `Row 1: {'Name': 'Alice', 'Age': 30}`.
    3.  This preserves the key-value relationship for the LLM.

### 5. OpenDocument Formats (`.odt`, `.odp`)
*   **Strategy:** These are ZIP archives containing XML. We unzip them in memory and parse the `content.xml` directly using Python's `xml.etree`.
*   **Fallback:** LibreOffice conversion.

### 6. HTML & RTF
*   **HTML:** Uses `BeautifulSoup` to strip tags (`<script>`, `<style>`) and extract visible text.
*   **RTF:** Uses `striprtf` to convert Rich Text to plain text.

---

## 🛡️ Error Handling & Fallbacks

The parsing engine is built to be resilient:

1.  **Encoding Detection:** If UTF-8 fails, it tries `latin-1`, `cp1252`, and `ascii` sequentially.
2.  **Library Fallbacks:** If `unstructured` crashes on a weird DOCX, `python-docx` takes over instantly.
3.  **Graceful Degradation:** If a specific slide in a PPT fails, it skips that slide and logs a warning rather than crashing the entire process.

This ensures that your ingestion pipeline keeps running even when users upload "messy" real-world documents.

---

## ⚠️ Limitations: Handwritten Text

Please note that this parsing engine is optimized for **digital-native documents** (files where text is selectable).

*   **Handwritten Text:** The current system **does not** include a specialized Handwriting Recognition (HTR) model. PDFs containing handwritten notes or forms will likely yield poor results or fail to extract that specific content.
*   **Scanned Images:** While some basic OCR might work via `unstructured`, high-precision extraction from low-quality scans is not currently guaranteed.

I am actively looking into integrating advanced OCR solutions to handle handwritten documents in a future update.
