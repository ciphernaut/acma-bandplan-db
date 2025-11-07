import pathlib
import sqlite3
import pdfplumber
import re

# Path for the SQLite database
DB_PATH = pathlib.Path('/projects/ACMA/frequency_allocations.db')

# Create or replace the database and tables
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

c.execute('DROP TABLE IF EXISTS allocations')
c.execute('DROP TABLE IF EXISTS australian_footnotes')
c.execute('DROP TABLE IF EXISTS international_footnotes')

c.execute(
    '''CREATE TABLE allocations(
        frequency_range TEXT PRIMARY KEY,
        unit TEXT,
        region1 TEXT,
        region2 TEXT,
        region3 TEXT,
        australian_table_of_allocations TEXT,
        common TEXT,
        footnote_ref TEXT
    )'''
)

c.execute(
    '''CREATE TABLE australian_footnotes(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ref TEXT UNIQUE,
        text TEXT
    )'''
)

c.execute(
    '''CREATE TABLE international_footnotes(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ref TEXT UNIQUE,
        text TEXT
    )'''
)

conn.commit()

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def get_unit_from_page(page):
    """Return the unit header (kHz, MHz or GHz) from a page.
    The unit is expected to appear in one of the first five lines of text.
    """
    txt = page.extract_text()
    if not txt:
        return None
    for line in txt.splitlines()[:5]:
        lc = line.strip().lower()
        if lc in ['khz', 'mhz', 'ghz']:
            return lc.upper()
    return None


def process_table(table, unit):
    """
    Convert a pdfplumber table into rows for the allocations table.

    The PDF layout is:
    * Column 1 contains the frequency range followed by a description and sometimes region values.
    * Columns 2‑3 are usually empty but may contain merged cells.
    * Column 4 repeats the information from column 1 but split into lines:
          line 0 – frequency range (e.g. "8.3 – 9").
          line 1 – description (e.g. "METEOROLOGICAL AIDS")
          line 2‑… – region values for Region 1, 2, 3.

    The function extracts:
      * ``frequency_range`` – the numeric range extracted from line 0.
      * ``unit`` – passed from the page header.
      * ``region1``–``region3`` – individual region values; if a value is missing it is set to ``'COMMON'``.
      * ``australian_table_of_allocations`` – the description part (line 1).
      * ``common`` – the common content when any region cell is merged. The frequency range portion of that content is omitted.
      * ``footnote_ref`` – comma‑separated list of references found in any field.
    """
    rows = []
    for row in table[2:]:  # skip header rows
        if not any(row):
            continue
        raw_cell = row[-1] or ''
        parts = [p.strip() for p in raw_cell.split('\n') if p.strip()]
        if not parts:
            continue
        # Extract numeric range from first line – allow any dash-like character
        # Clean the line by removing all whitespace so stray spaces inside numbers are ignored
        cleaned_line = re.sub(r'\s+', '', parts[0])
        # Extract numeric range from the cleaned line
        m = re.search(r'(\d+(?:\.\d+)?[–-—]\d+(?:\.\d+)?)', cleaned_line)
        frequency_range = m.group(1) if m else ''
        common_content = parts[0].replace(frequency_range, '', 1).strip()
        description = parts[1] if len(parts) > 1 else ''
        region_values = parts[2:] if len(parts) > 2 else []

        # Helper to split a cell into content and any footnote refs
        def split_cell(cell):
            refs = re.findall(r'\b(?:AUS\d+[A-Z]*|\d{1,3}[A-Z]{0,2})\b', cell)
            # Remove refs from the cell text
            cleaned = re.sub(r'\b(?:AUS\d+[A-Z]*|\d{1,3}[A-Z]{0,2})\b', '', cell).strip()
            return cleaned if cleaned else None, refs

        foot_refs = []
        # Process each region value (may be less than 3)
        r_vals = []
        for val in region_values:
            content, refs = split_cell(val)
            if refs:
                foot_refs.extend(refs)
            r_vals.append(content or 'COMMON')

        # Pad to three regions
        while len(r_vals) < 3:
            r_vals.append('COMMON')
        r1, r2, r3 = r_vals[:3]

        # Detect merged cells: if two or more region columns contain identical non‑empty text
        common_text = None
        for txt in (r1, r2, r3):
            if txt and txt not in ('COMMON', ''):
                if common_text is None:
                    common_text = txt
                elif txt == common_text:
                    continue
                else:
                    common_text = None
                    break
        if common_text:
            r1 = r2 = r3 = 'COMMON'
            common_col = common_text
        else:
            # If no merged text, use the extracted common_content or description as common
            common_col = common_content or description

        footnote_ref = ','.join(sorted(set(foot_refs))) if foot_refs else None
        rows.append((frequency_range, unit, r1, r2, r3, description, common_col, footnote_ref))
    return rows

# ---------------------------------------------------------------------------
# Footnote extraction helpers
# ---------------------------------------------------------------------------

def extract_footnotes(pdf_obj, start_page, end_page, is_australian):
    """Extract footnotes between start_page and end_page (inclusive). Pages are 0-indexed.
    Inserts into australian_footnotes or international_footnotes tables. Handles multi‑line
    footnote text and strips any leading page numbers that may appear before the reference."""
    for page_num in range(start_page, end_page + 1):
        page = pdf_obj.pages[page_num]
        raw_text = page.extract_text() or ''
        lines = [l.rstrip() for l in raw_text.splitlines() if l.strip()]
        current_ref = None
        buffer = []
        for line in lines:
            # Strip any leading page number or whitespace before attempting to match a reference.
            cleaned = re.sub(r'^\s*\d+\s+', '', line)
            # Detect a new reference.  Allow an optional leading page number that has been removed.
            if is_australian:
                m = re.match(r'^(AUS\d+[A-Z]*)(.*)$', cleaned)
            else:
                m = re.match(r'^(\d{1,3}[A-Z]{0,2})(.*)$', cleaned)
            if m:
                # Save previous footnote
                if current_ref is not None:
                    txt = ' '.join(buffer).strip()
                    if is_australian:
                        c.execute('INSERT OR IGNORE INTO australian_footnotes(ref,text) VALUES (?,?)', (current_ref, txt))
                    else:
                        c.execute('INSERT OR IGNORE INTO international_footnotes(ref,text) VALUES (?,?)', (current_ref, txt))
                current_ref = m.group(1)
                buffer = [m.group(2).strip()]
            else:
                # Continuation of the current footnote – ignore lines that are just page numbers.
                if current_ref is not None and cleaned.strip():
                    buffer.append(cleaned.strip())
        # Flush last footnote on page
        if current_ref is not None:
            txt = ' '.join(buffer).strip()
            if is_australian:
                c.execute('INSERT OR IGNORE INTO australian_footnotes(ref,text) VALUES (?,?)', (current_ref, txt))
            else:
                c.execute('INSERT OR IGNORE INTO international_footnotes(ref,text) VALUES (?,?)', (current_ref, txt))
    conn.commit()

# ---------------------------------------------------------------------------
# Main extraction loop
# ---------------------------------------------------------------------------
pdf_path = pathlib.Path('/projects/ACMA/Australian Radiofrequency Spectrum Plan 2021_Including general information.pdf')
with pdfplumber.open(pdf_path) as pdf:
    # Extract footnotes first (pages 112‑119 and 120‑214 in physical numbering)
    extract_footnotes(pdf, 111, 118, True)   # 0-indexed: pages 112-119
    extract_footnotes(pdf, 119, 213, False)  # 0-indexed: pages 120-214

    for page_num in range(30, 112):  # physical pages 31‑112 inclusive (0-indexed)
        page = pdf.pages[page_num]
        unit = get_unit_from_page(page)
        if not unit:
            continue
        tables = page.extract_tables()
        for tbl in tables:
            rows = process_table(tbl, unit)
            c.executemany(
                '''INSERT OR IGNORE INTO allocations (
                    frequency_range, unit, region1, region2, region3,
                    australian_table_of_allocations, common, footnote_ref
                ) VALUES (?,?,?,?,?,?,?,?)''',
                rows,
            )
    conn.commit()
print('Extraction complete. Database at', DB_PATH)
