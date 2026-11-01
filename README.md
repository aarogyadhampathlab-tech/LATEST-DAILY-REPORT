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

Keep the key private; do not commit it to the repository. AI insights are generated only when requested and receive aggregate test counts, not patient-level rows. Gemini API free-tier availability and usage limits depend on Google's current terms, model, and region; free usage is not guaranteed or unlimited.
