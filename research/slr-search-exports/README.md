# Database search exports

The raw exports from the database searches run on 13 October 2026 belong in this folder. **They are not in the repository**: the databases' licence terms restrict redistributing bulk records, and the Scopus file is 21 MB. Only this README is tracked.

| File (local only) | Database | Records | Abstracts |
|---|---|---|---|
| `export_c73713db-…_2026-10-13T093908….csv` | Scopus | 8,663 | Yes |
| `export2026.10.13-05.59.12.csv` | IEEE Xplore | 1,000 (the site reported 4,343; 1,000 appears to be the export limit) | Yes |
| `acm (2).bib` | ACM Digital Library | 744 | Yes |
| `Springlinker.csv` | SpringerLink | 284 | **No** (titles and metadata only) |
| `SIAM search.txt` | SIAM (RSS/XML feed of the search) | See file | — |

The search strings are recorded in the systematic review protocol and in the methodology. To reproduce the exports, run the same strings with the same filters on each site and save the files here.
