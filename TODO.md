# Project TODO List

The following tasks are planned for future improvements or bug‑fixes in the ACMA Bandplan extraction project.

- [ ] **Split `frequency_range` into separate `start_mhz` and `stop_mhz` columns** – makes numeric queries easier.
- [ ] **Standardise frequency units** – convert all ranges to a single unit (e.g. MHz) before storing.
- [ ] **Provide a lookup example that includes footnote references** – demonstrate how to join the `allocations` table with the appropriate footnotes.
- [ ] **Clean up the database of messy region data** – remove duplicate or malformed entries and normalise region names.
- [ ] **Prevent page numbers from creating duplicate rows in `international_footnotes`** – ensure each footnote is inserted only once.
- [ ] Add unit tests for the extraction logic (e.g., verify row counts, footnote mapping).
- [ ] Improve error handling when PDF parsing fails or tables are missing.
- [ ] Allow specifying an output database path via command‑line argument.
- [ ] Document the schema and provide example SQL queries in the README.
- [ ] Add a script to export the SQLite data to CSV for easier consumption by other tools.
- [ ] Consider adding support for newer ACMA band‑plan PDFs (e.g., 2025/6 version).
