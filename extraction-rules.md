# Extraction Rules for ACMA Frequency Allocation Tables

The PDF layout is irregular and requires a set of rules to transform the raw table data into the SQLite schema.

## 1. Page Selection
* Only physical pages **31‑112** (inclusive) contain Part 2 tables.
* Each page starts with a *Unit* header (`kHz`, `MHz` or `GHz`).

## 2. Table Structure
| Column | Description |
|--------|-------------|
| **Column 1** | Contains the frequency range followed by a description and, on some rows, region values.
| **Columns 2‑3** | Empty in the PDF.
| **Column 4** | Repeats the information from column 1 but split into lines:
  * line 0 – frequency range (e.g. `8.3 – 9`).
  * line 1 – description (e.g. `METEOROLOGICAL AIDS`).
  * line 2‑… – region values for Region 1, 2, 3.

## 3. Frequency Range Extraction
* Prefer the value from **line 0** of column 4.
* If it starts with `Below X`, convert to `0 - X` (e.g. `Below 8.3` → `0 - 8.3`).
* Otherwise, use a regex that matches a numeric range (`\d+(\.\d+)?\s*[–-]\s*\d+(\.\d+)?`).

## 4. Description / Australian Table of Allocations
* The description is **line 1** of column 4.
* Store this string in the `australian_table_of_allocations` column.

## 5. Region Values & Common Column
| Scenario | Action |
|----------|--------|
| Three distinct values present (lines 2‑4) | Assign to `region1`, `region2`, `region3`. Set `common` empty. |
| Two values present (lines 2‑3) | Assign first to `region1`, second to `region2`; set `region3 = 'COMMON'`. Set `common` to the description. |
| One value present (line 2) | Assign to `region1`; set `region2 = region3 = 'COMMON'`. Set `common` to the description. |
| No values present | All three regions are `'COMMON'`. Set `common` to the description.

## 6. SQLite Schema
```sql
CREATE TABLE allocations(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    frequency_range TEXT,
    unit TEXT,
    region1 TEXT,
    region2 TEXT,
    region3 TEXT,
    australian_table_of_allocations TEXT,
    common TEXT,
    footnote_ref TEXT
);
```

## 7. Footnotes Extraction
* **Australian footnotes** – pages 112‑119 (physical). Each line starts with a reference such as `AUS1A` or `AUS3`. The rest of the line is the note text.
* **International footnotes** – pages 120‑214. References follow patterns like `556B`, `532AB`, or simple numbers (`53`).

Both sets are stored in separate tables:
```sql
CREATE TABLE australian_footnotes(ref TEXT UNIQUE, text TEXT);
CREATE TABLE international_footnotes(ref TEXT UNIQUE, text TEXT);
```
The script extracts the reference and note text, inserts them into these tables, and links any matching reference found in `allocations.footnote_ref`.

* **Australian footnotes** – pages 112‑119 (physical). Each line starts with a reference such as `AUS1A` or `AUS3`. The rest of the line is the note text.
* **International footnotes** – pages 120‑214. References follow patterns like `556B`, `532AB`, or simple numbers (`53`).

Both sets are stored in separate tables:
```sql
CREATE TABLE australian_footnotes(ref TEXT UNIQUE, text TEXT);
CREATE TABLE international_footnotes(ref TEXT UNIQUE, text TEXT);
```
The script extracts the reference and note text, inserts them into these tables, and links any matching reference found in `allocations.footnote_ref`.
```
## 7. Implementation Notes
* The extraction script uses `pdfplumber` to read tables.
* The script follows the rules above and inserts rows into the SQLite database.
* The first row (`Below 8.3`) is handled by rule 3.
* All other rows are processed automatically based on the number of region values found.

---

Feel free to refer to this document when modifying or debugging the extraction logic.
