# ACMA Bandplan Database

This repository contains a small Python utility that extracts the frequency allocation tables from the **Australian Radiofrequency Spectrum Plan 2021** (the *band‑plan*). The extracted data is stored in an SQLite database for easy querying and analysis.

> ⚙️ This project was vibcoded on Opencode using **OpenAI GPT‑4** and the Aurafriday MCP stack.

---
## 📥 Getting the Original PDF
The extraction script expects the official ACMA band‑plan PDF. You can download it directly from the ACMA website:

```text
https://www.acma.gov.au/sites/default/files/2021-07/Australian%20Radiofrequency%20Spectrum%20Plan%202021_Including%20general%20information.pdf
```

Save the file to a convenient location, e.g. `bandplan.pdf`.

---
## ⚙️ Prerequisites
* Python 3.10+ (the script has been tested with 3.11)
* pip

No external database server is required – SQLite comes bundled with Python.

---
## 📦 Installation
```bash
# Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate   # On Windows use `.venv\Scripts\activate`

# Install the dependencies
pip install PyPDF2 pandas
```

---
## 🚀 Running the Extraction
```bash
python extract_to_sqlite.py path/to/bandplan.pdf
```
The script will:
1. Parse the PDF and locate the frequency allocation tables.
2. Extract each row into a structured format.
3. Store the data in `frequency_allocations.db` in the current directory.
4. Create two additional tables – `australian_footnotes` (pages 112‑119) and `international_footnotes` (pages 120‑214).

---
## 📊 Database Schema
| Table | Columns |
|-------|---------|
| `allocations` | `id`, `unit`, `frequency_range`, `region1`, `region2`, `region3`, `common`, `footnote_ref` |
| `australian_footnotes` | `id`, `page_number`, `text` |
| `international_footnotes` | `id`, `page_number`, `text` |

The `frequency_range` column stores the range as a string (e.g. `"535–1606.5"`). The `common` column contains any text that was merged across multiple region columns in the original PDF.

---
## 🔎 Querying the Data
```python
import sqlite3
conn = sqlite3.connect('frequency_allocations.db')
cur = conn.cursor()
# Example: fetch all allocations for the 2 MHz band (2000–2100 MHz)
cur.execute("SELECT * FROM allocations WHERE frequency_range LIKE '%2000%'")
print(cur.fetchall())
```

---
## 📄 License
This project is licensed under the MIT License – see [LICENSE](LICENSE) for details.

---
## 🤝 Contributing
Feel free to open issues or pull requests. If you add new features, please include tests and update the documentation accordingly.
