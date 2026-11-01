# Daily Pathology Report

A Streamlit app that turns pathology Excel workbooks into daily test summaries, downloadable reports, saved history, and date-filtered analytics.

## Run locally

From PowerShell in the project folder:

```powershell
.\.venv\Scripts\python.exe -m streamlit run excel_processor.py
```

Install dependencies first if needed:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Enable Gemini AI features

AI insights and automatic categorization use Gemini and require a `GEMINI_API_KEY` from Google AI Studio. Set it in the same environment that starts Streamlit. For a temporary PowerShell session:

```powershell
$env:GEMINI_API_KEY = "set-your-key-here"
.\.venv\Scripts\python.exe -m streamlit run excel_processor.py
```

Keep the key private; do not commit it to the repository. AI insights are generated only when requested and receive aggregate workload and derived financial summaries, including frequently used test counts and listed rates—not patient-level rows. Gemini API free-tier availability and usage limits depend on Google's current terms, model, and region; free usage is not guaranteed or unlimited.

## Financial analytics

The Analytics tab uses the laboratory price list columns `Test Id`, `Test Name`, `OPD Charge`, and `IPD Charge` to estimate charges for the selected reports. It matches tests by their test ID and shows the most frequently used tests and prices first. These are listed-rate estimates before discounts or adjustments, not actual collections or realized revenue. AI insight requests can include aggregate financial totals and the most frequently used tests with their listed rates; patient-level rows are not sent.

The app loads `price list.xls` automatically from beside `excel_processor.py`; there is no in-app price-list upload. Include the workbook in the deployed repository for Streamlit Cloud to use it. Repository collaborators—and anyone else with access to a public repository—can view the listed prices. The workbook is not copied into report storage.
