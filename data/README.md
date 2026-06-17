# data/

Put your **ESAI Harm-Bench-Legal Map** workbook export (`.xlsx`) in this folder. The tools pick up
the first `.xlsx` they find here automatically.

This folder is **git-ignored** , the workbook is shared data and should never be committed. Each
person downloads their own current export from the live Google Sheet (File -> Download -> .xlsx) and
drops it here.

You can also point the tools at a specific file:
```
python tools/workbook_health_check.py --workbook "/path/to/your export.xlsx"
# or
export ESAI_WORKBOOK="/path/to/your export.xlsx"
```
