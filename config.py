import os
from datetime import datetime, timedelta

try:
    from openai import APIError, OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    APIError = None
    OpenAI = None
    OPENAI_AVAILABLE = False


def get_openai_client():
    if OpenAI is None:
        raise RuntimeError("Install the OpenAI dependency from requirements.txt to enable AI insights.")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Set OPENAI_API_KEY in the environment used to start Streamlit.")

    return OpenAI(api_key=api_key)


def is_openai_configured():
    return OpenAI is not None and bool(os.getenv("OPENAI_API_KEY"))


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
