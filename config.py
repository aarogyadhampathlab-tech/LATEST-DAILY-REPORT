import os
from datetime import datetime, timedelta

try:
    from google import genai
    from google.genai.errors import APIError as GeminiAPIError
    from google.genai.types import GenerateContentConfig
    GEMINI_AVAILABLE = True
except ImportError:
    genai = None
    GeminiAPIError = None
    GenerateContentConfig = None
    GEMINI_AVAILABLE = False


def get_gemini_client():
    if genai is None:
        raise RuntimeError("Install the Gemini dependency from requirements.txt to enable AI features.")

    api_key = get_gemini_api_key()
    if not api_key:
        raise RuntimeError(
            "Set GEMINI_API_KEY in the environment used to start Streamlit, "
            'or add GEMINI_API_KEY = "your-key" to Streamlit Cloud app secrets.'
        )

    return genai.Client(api_key=api_key)


def get_gemini_api_key():
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        return api_key.strip()

    try:
        import streamlit as st
        api_key = st.secrets.get("GEMINI_API_KEY")
    except FileNotFoundError:
        return None

    return api_key.strip() if isinstance(api_key, str) and api_key.strip() else None


def is_gemini_configured():
    return GEMINI_AVAILABLE and bool(get_gemini_api_key())


def default_dates():
    today = datetime.today()
    yesterday = today - timedelta(days=1)
    today_str = today.strftime('%d-%m-%Y')
    yesterday_str = yesterday.strftime('%d-%m-%Y')
    return today_str, yesterday_str


CATEGORY_RULES = {
    "Biochemistry": [
        "RENAL FUNCTION TEST", "LIVER FUNCTION TEST", "BLOOD GLUCOSE",
        "GLYCOSYLATED HB", "SGOT", "SGPT", "BLOOD UREA",
        "VIRAL MARKER", "PREOPERATIVE PROFILE", "SEROLOGY", "PT/INR"
    ],
    "Clinical": [
        "URINE ANALYSIS", "PLEURAL FLUID EXAMINATION",
        "Plural Fluid for R/E Biochemistry / ADA"
    ],
    "Hematology": [
        "COMPLETE BLOOD COUNTS [CBC]", "TOTAL LEUCOCYTE COUNT",
        "FLUID DLC", "COMPLETE HEMOGRAM WITH ESR", "BLOOD GROUP"
    ],
    "Immunology": [
        "Hormone Assays Report", "Serum IGE", "VDRL TITER", "HBsAg",
        "HCV ANTIBODY TEST", "CA-125", "THYROID FUNCTION TEST",
        "THYROID STIMULATING HORMONE", "TOTAL THYROID PROFILE",
        "IgG IgM S Typhe", "C-REACTIVE PROTEIN"
    ]
}
