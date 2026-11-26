FLOWFORGE BG-00 PACKAGE

1. Overlay this package at the FlowForge repository root.
2. Copy the three authoritative PDFs into specs/source, or pass their paths to Invoke-FlowForgeBG00.ps1.
3. Ensure Python packages pypdf and PyYAML are installed in .venv.
4. Run:
   .\scripts\requirements\Invoke-FlowForgeBG00.ps1
5. Run:
   .\.venv\Scripts\python.exe -m pytest -q .\tests\requirements
6. Review generated candidates, duplicates, crosswalk, and backlog before using them as implementation truth.

The tooling does not change application runtime code or the database.
