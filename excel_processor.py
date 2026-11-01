import hashlib
import json
import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
from datetime import datetime

import config
from helpers import build_test_counts, build_category_counts, generate_ai_insights, get_report_date, style_excel
from data_persistence import save_processed_data, load_processed_data, delete_processed_data, get_saved_dates, load_daily_report_series, compute_cumulative

st.set_page_config(page_title="Pathology Report", page_icon="🧪", layout="wide")

theme_mode = st.sidebar.radio(
    "Appearance",
    options=["Day", "Night"],
    horizontal=True,
    key="theme_mode"
)

# ============================================================================
# APP STYLING
# ============================================================================
st.markdown("""
<style>
* {
    margin: 0;
    padding: 0;
}

html, body, [data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #0f0f0f 0%, #1a1a1a 100%);
    min-height: 100vh;
}

[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #0f0f0f 0%, #1a1a1a 100%);
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1a1a1a 0%, #2d2d2d 100%);
    border-right: 2px solid #333;
}

.main {
    background: transparent;
}

.block-container {
    padding: 2rem 1rem;
    max-width: 1400px;
}

/* Card Styling */
.glossy-card {
    background: rgba(255, 255, 255, 0.08);
    border-radius: 20px;
    padding: 25px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.12);
    margin-bottom: 20px;
    transition: transform 0.3s ease, box-shadow 0.3s ease, border 0.3s ease;
}

.glossy-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 12px 40px rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
}

/* Header Styling */
.header-title {
    background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
    color: white;
    padding: 50px;
    border-radius: 25px;
    text-align: center;
    margin-bottom: 30px;
    box-shadow: 0 15px 50px rgba(0, 0, 0, 0.4);
    border: 2px solid rgba(255, 255, 255, 0.1);
}

.header-title h1 {
    font-size: 3.5em;
    font-weight: 800;
    margin-bottom: 10px;
    background: linear-gradient(135deg, #ffffff 0%, #c0c0c0 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.header-title p {
    font-size: 1.2em;
    opacity: 0.85;
    color: rgba(255, 255, 255, 0.8);
}

/* Metric Cards */
[data-testid="stMetric"] {
    background: rgba(255, 255, 255, 0.08);
    padding: 25px;
    border-radius: 15px;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
    border: 1px solid rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
}

[data-testid="stMetricValue"] {
    color: #ffffff;
    font-size: 2.5em !important;
    font-weight: 800;
}

[data-testid="stMetricLabel"] {
    color: rgba(255, 255, 255, 0.7) !important;
}

/* Button Styling */
.stButton > button {
    background: linear-gradient(135deg, #ffffff 0%, #e8e8e8 100%);
    color: #1a1a1a;
    border: none;
    border-radius: 12px;
    padding: 12px 30px;
    font-weight: 700;
    font-size: 1em;
    box-shadow: 0 4px 15px rgba(255, 255, 255, 0.2);
    transition: all 0.3s ease;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 25px rgba(255, 255, 255, 0.3);
    background: linear-gradient(135deg, #f0f0f0 0%, #d0d0d0 100%);
}

/* Upload Button */
.stFileUploader > button {
    background: linear-gradient(135deg, #ffffff 0%, #e8e8e8 100%) !important;
    color: #1a1a1a !important;
    font-weight: 700 !important;
}

/* Tab Styling */
[data-testid="stTabs"] [role="tablist"] {
    background: transparent;
    border: none;
    border-bottom: 2px solid rgba(255, 255, 255, 0.1);
}

[data-testid="stTabs"] [role="tab"] {
    background: transparent;
    color: rgba(255, 255, 255, 0.6);
    border: none;
    padding: 12px 20px;
    font-weight: 600;
    border-bottom: 3px solid transparent;
    transition: all 0.3s ease;
}

[data-testid="stTabs"] [role="tab"]:hover {
    color: rgba(255, 255, 255, 0.9);
}

[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    background: transparent;
    color: white;
    border-bottom: 3px solid #ffffff;
}

/* Selectbox Styling */
[data-testid="stSelectbox"] {
    border-radius: 12px;
}

.stSelectbox {
    margin-bottom: 20px;
}

/* Section Header */
.section-header {
    font-size: 1.8em;
    font-weight: 700;
    color: #ffffff;
    margin: 30px 0 20px 0;
    padding-bottom: 10px;
    border-bottom: 3px solid rgba(255, 255, 255, 0.2);
}

/* Table Styling */
[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
    background: rgba(255, 255, 255, 0.05);
}

/* Download Button */
.stDownloadButton > button {
    background: linear-gradient(135deg, #ffffff 0%, #e8e8e8 100%);
    color: #1a1a1a;
    font-weight: 700;
}

.stDownloadButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(255, 255, 255, 0.3);
}

/* Success/Error Messages */
.stSuccess {
    background: rgba(76, 175, 80, 0.15);
    border-left: 5px solid #4CAF50;
    border-radius: 8px;
    color: rgba(255, 255, 255, 0.9);
}

.stError {
    background: rgba(244, 67, 54, 0.15);
    border-left: 5px solid #f44336;
    border-radius: 8px;
    color: rgba(255, 255, 255, 0.9);
}

.stInfo {
    background: rgba(33, 150, 243, 0.15);
    border-left: 5px solid #2196F3;
    border-radius: 8px;
    color: rgba(255, 255, 255, 0.9);
}

.stWarning {
    background: rgba(255, 152, 0, 0.15);
    border-left: 5px solid #FF9800;
    border-radius: 8px;
    color: rgba(255, 255, 255, 0.9);
}

/* Divider */
hr {
    border: none;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
    margin: 30px 0;
}

/* Text Colors */
h1, h2, h3, h4, h5, h6 {
    color: #ffffff !important;
}

p, span, label {
    color: rgba(255, 255, 255, 0.85) !important;
}

/* Input Fields */
input {
    background: rgba(255, 255, 255, 0.08) !important;
    color: #ffffff !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 8px !important;
}

input::placeholder {
    color: rgba(255, 255, 255, 0.4) !important;
}

/* Checkbox */
[data-testid="stCheckbox"] {
    color: rgba(255, 255, 255, 0.9) !important;
}

/* Keep interactive text readable in every button state. */
.stButton > button,
.stDownloadButton > button {
    color: #171717 !important;
    background: #f3f4f6 !important;
    border: 1px solid #d1d5db !important;
    box-shadow: none;
}

.stButton > button:hover,
.stButton > button:focus,
.stButton > button:active,
.stDownloadButton > button:hover,
.stDownloadButton > button:focus,
.stDownloadButton > button:active {
    color: #111827 !important;
    background: #e5e7eb !important;
    border-color: #9ca3af !important;
}

.stButton > button *,
.stDownloadButton > button * {
    color: inherit !important;
}

html, body, [data-testid="stAppViewContainer"] {
    background: #111827;
}

[data-testid="stSidebar"] {
    background: #172033;
    border-right: 1px solid #273449;
}

.block-container {
    max-width: 1200px;
    padding: 1.5rem 1.25rem;
}

.glossy-card {
    background: #182234;
    border: 1px solid #2b374a;
    border-radius: 12px;
    box-shadow: none;
    backdrop-filter: none;
    padding: 18px;
    transition: none;
}

.glossy-card:hover {
    transform: none;
    box-shadow: none;
    border-color: #2b374a;
}

.header-title {
    background: #182234;
    padding: 24px;
    border: 1px solid #2b374a;
    border-radius: 12px;
    box-shadow: none;
    margin-bottom: 20px;
}

.header-title h1 {
    font-size: 2rem;
}

[data-testid="stMetric"] {
    background: #182234;
    border: 1px solid #2b374a;
    border-radius: 12px;
    box-shadow: none;
    backdrop-filter: none;
    padding: 16px;
}

[data-testid="stTabs"] [role="tab"] {
    padding: 10px 14px;
}

[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color: #ffffff;
    border-bottom-color: #60a5fa;
}

[data-testid="stFileUploader"] section {
    background: #182234;
    border: 1px dashed #52627a;
    border-radius: 10px;
}

html, body, [data-testid="stAppViewContainer"] {
    background:
        radial-gradient(ellipse at 12% 0%, rgba(186, 230, 253, 0.45), transparent 36%),
        linear-gradient(135deg, #f5f8ff 0%, #eef4fb 55%, #f8fafc 100%);
    color: #172033;
}

[data-testid="stAppViewContainer"] > .main {
    background: transparent;
}

[data-testid="stSidebar"] {
    background: rgba(255, 255, 255, 0.78);
    border-right: 1px solid rgba(148, 163, 184, 0.24);
}

.block-container {
    max-width: 1280px;
    padding: 1.5rem 1.5rem 3rem;
}

h1, h2, h3, h4, h5, h6,
p, span, label, [data-testid="stMarkdownContainer"] {
    color: #172033 !important;
}

.header-title {
    background: linear-gradient(120deg, rgba(255,255,255,.86), rgba(239,246,255,.76));
    border: 1px solid rgba(148, 163, 184, 0.26);
    box-shadow: 0 18px 48px rgba(51, 65, 85, 0.08);
    backdrop-filter: blur(18px);
    animation: fade-up .55s ease both;
}

.header-title h1 {
    background: linear-gradient(100deg, #172554, #2563eb 55%, #0f766e);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.header-title p {
    color: #52627a !important;
}

.glossy-card,
[data-testid="stMetric"] {
    background: rgba(255, 255, 255, 0.72);
    border: 1px solid rgba(148, 163, 184, 0.22);
    box-shadow: 0 12px 30px rgba(51, 65, 85, 0.06);
    backdrop-filter: blur(16px);
    animation: fade-up .45s ease both;
}

.glossy-card:hover {
    transform: translateY(-2px);
    border-color: rgba(96, 165, 250, 0.45);
    box-shadow: 0 16px 36px rgba(51, 65, 85, 0.1);
}

[data-testid="stMetricValue"] {
    color: #1d4ed8 !important;
}

[data-testid="stMetricLabel"] {
    color: #64748b !important;
}

[data-testid="stTabs"] [role="tablist"] {
    border-bottom-color: rgba(148, 163, 184, 0.3);
}

[data-testid="stTabs"] [role="tab"] {
    color: #64748b !important;
}

[data-testid="stTabs"] [role="tab"]:hover,
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color: #1d4ed8 !important;
}

[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    border-bottom-color: #3b82f6;
}

[data-testid="stFileUploader"] section {
    background: rgba(255, 255, 255, 0.72);
    border: 1px dashed #93a4bd;
    transition: border-color .2s ease, background .2s ease;
}

[data-testid="stFileUploader"] section:hover {
    background: rgba(239, 246, 255, 0.92);
    border-color: #3b82f6;
}

[data-testid="stFileUploader"] button {
    color: #1e3a8a !important;
    background: #eff6ff !important;
    border: 1px solid #bfdbfe !important;
}

[data-testid="stFileUploader"] button:hover,
[data-testid="stFileUploader"] button:focus {
    color: #1e40af !important;
    background: #dbeafe !important;
    border-color: #60a5fa !important;
}

[data-testid="stFileUploader"] button * {
    color: inherit !important;
}

.stButton > button,
.stDownloadButton > button {
    min-height: 2.75rem;
    border-radius: 10px;
    transition: transform .18s ease, box-shadow .18s ease, background .18s ease;
}

.stButton > button:hover,
.stDownloadButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 8px 18px rgba(37, 99, 235, 0.14);
}

[data-testid="stDownloadButton"] > button {
    width: 100%;
    min-height: 3.25rem;
    color: #ffffff !important;
    background: linear-gradient(100deg, #2563eb, #4f46e5) !important;
    border: none !important;
    font-size: 1.05rem;
    font-weight: 700;
    box-shadow: 0 10px 22px rgba(37, 99, 235, 0.22);
}

[data-testid="stDownloadButton"] > button:hover,
[data-testid="stDownloadButton"] > button:focus,
[data-testid="stDownloadButton"] > button:active {
    color: #ffffff !important;
    background: linear-gradient(100deg, #1d4ed8, #4338ca) !important;
}

[data-testid="stDownloadButton"] > button * {
    color: inherit !important;
}

input {
    color: #172033 !important;
    background: rgba(255, 255, 255, 0.82) !important;
    border-color: #cbd5e1 !important;
}

input::placeholder {
    color: #94a3b8 !important;
}

[data-testid="stDateInputField"] {
    color: #172033 !important;
    background: rgba(255, 255, 255, 0.94) !important;
    border-color: #cbd5e1 !important;
}

[data-testid="stDateInputField"] [role="spinbutton"] {
    color: #172033 !important;
}

[data-testid="stDateInput"] [data-baseweb="input"],
[data-testid="stDateInput"] [data-baseweb="base-input"],
[data-testid="stDateInput"] input {
    color: #172033 !important;
    background: rgba(255, 255, 255, 0.94) !important;
    border-color: #cbd5e1 !important;
}

[data-testid="stButton"] > button:not([kind="primary"]) {
    color: #1e3a8a !important;
    background: #eff6ff !important;
    border: 1px solid #bfdbfe !important;
}

[data-testid="stButton"] > button:not([kind="primary"]):hover,
[data-testid="stButton"] > button:not([kind="primary"]):focus {
    color: #1e40af !important;
    background: #dbeafe !important;
    border-color: #60a5fa !important;
}

.stSuccess, .stInfo, .stWarning, .stError {
    color: #172033 !important;
    border-radius: 10px;
}

hr {
    background: #dbe4f0;
}

@keyframes fade-up {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
}

@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation-duration: .01ms !important;
        animation-iteration-count: 1 !important;
        scroll-behavior: auto !important;
        transition-duration: .01ms !important;
    }
}
</style>
""", unsafe_allow_html=True)

if theme_mode == "Night":
    st.markdown("""
    <style>
    html, body, [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(ellipse at 12% 0%, rgba(30, 64, 175, .18), transparent 38%),
            linear-gradient(135deg, #0b1220 0%, #111827 60%, #0f172a 100%);
        color: #e5edf8;
    }
    [data-testid="stSidebar"] {
        background: rgba(15, 23, 42, .94);
        border-right-color: #263247;
    }
    h1, h2, h3, h4, h5, h6, p, span, label,
    [data-testid="stMarkdownContainer"] {
        color: #e5edf8 !important;
    }
    .header-title, .glossy-card, [data-testid="stMetric"] {
        background: rgba(24, 34, 52, .78);
        border-color: rgba(100, 116, 139, .3);
        box-shadow: 0 14px 36px rgba(0, 0, 0, .18);
    }
    .header-title h1 {
        background: linear-gradient(100deg, #e0f2fe, #93c5fd 55%, #5eead4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .header-title p, [data-testid="stMetricLabel"] {
        color: #a9b8cb !important;
    }
    [data-testid="stMetricValue"] {
        color: #93c5fd !important;
    }
    [data-testid="stTabs"] [role="tab"] {
        color: #a9b8cb !important;
    }
    [data-testid="stTabs"] [role="tab"]:hover,
    [data-testid="stTabs"] [role="tab"][aria-selected="true"] {
        color: #bfdbfe !important;
    }
    [data-testid="stTabs"] [role="tab"][aria-selected="true"] {
        border-bottom-color: #60a5fa;
    }
    [data-testid="stFileUploader"] section {
        background: rgba(24, 34, 52, .74);
        border-color: #52627a;
    }
    [data-testid="stFileUploader"] button {
        color: #dbeafe !important;
        background: #1e3a5f !important;
        border-color: #345477 !important;
    }
    [data-testid="stFileUploader"] button:hover,
    [data-testid="stFileUploader"] button:focus {
        color: #ffffff !important;
        background: #254c78 !important;
    }
    .stButton > button {
        color: #e5edf8 !important;
        background: #253248 !important;
        border-color: #3b4a61 !important;
    }
    .stButton > button:hover,
    .stButton > button:focus,
    .stButton > button:active {
        color: #ffffff !important;
        background: #334765 !important;
        border-color: #5d7597 !important;
    }
    input {
        color: #e5edf8 !important;
        background: rgba(15, 23, 42, .86) !important;
        border-color: #3b4a61 !important;
    }
    input::placeholder {
        color: #94a3b8 !important;
    }
    [data-testid="stDateInput"] [data-baseweb="input"],
    [data-testid="stDateInput"] [data-baseweb="base-input"],
    [data-testid="stDateInput"] input {
        color: #e5edf8 !important;
        background: rgba(15, 23, 42, .86) !important;
        border-color: #3b4a61 !important;
    }
    [data-testid="stDateInputField"] {
        color: #e5edf8 !important;
        background: rgba(15, 23, 42, .86) !important;
        border-color: #3b4a61 !important;
    }
    [data-testid="stDateInputField"] [role="spinbutton"] {
        color: #e5edf8 !important;
    }
    [data-testid="stAlert"] p,
    [data-testid="stAlert"] span {
        color: #e5edf8 !important;
    }
    [data-testid="stButton"] > button:not([kind="primary"]) {
        color: #dbeafe !important;
        background: #253248 !important;
        border-color: #3b4a61 !important;
    }
    [data-testid="stButton"] > button:not([kind="primary"]):hover,
    [data-testid="stButton"] > button:not([kind="primary"]):focus {
        color: #ffffff !important;
        background: #334765 !important;
        border-color: #5d7597 !important;
    }
    </style>
    """, unsafe_allow_html=True)


def render_ai_insights(summary, key):
    summary_id = hashlib.sha256(
        json.dumps(summary, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()[:16]
    result_key = f"ai_insights_{key}_{summary_id}"

    if not config.GEMINI_AVAILABLE:
        st.caption(
            "Install the Gemini dependency from requirements.txt to enable AI insights. "
            "Only aggregate counts are sent."
        )
    elif not config.is_gemini_configured():
        st.caption(
            "Set GEMINI_API_KEY in the environment used to start Streamlit to enable AI insights. "
            "Only aggregate counts are sent."
        )
    else:
        st.caption("AI receives aggregate counts only; patient-level rows are not sent.")
    if st.button("✨ Generate AI insights", key=f"generate_{result_key}"):
        with st.spinner("Reviewing the aggregate report data..."):
            try:
                st.session_state[result_key] = generate_ai_insights(summary)
            except RuntimeError as exc:
                st.warning(str(exc))

    if result_key in st.session_state:
        st.markdown(st.session_state[result_key])


# ============================================================================
# HEADER
# ============================================================================
st.markdown("""
<div class="header-title">
    <h1>🧪 Pathology Report Dashboard</h1>
    <p>Aarogyadham Hospital - Professional Report Management System</p>
</div>
""", unsafe_allow_html=True)

# Initialize session state for tabs
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = 0

# Create main tabs
tab1, tab2, tab3 = st.tabs(["📊 Daily Report", "📁 Saved Reports", "📈 Analytics"])

# ============================================================================
# TAB 1: DAILY REPORT
# ============================================================================
with tab1:
    st.markdown("### Upload daily Excel report")
    st.caption("Choose an .xlsx file to generate the daily pathology summary.")
    uploaded_file = st.file_uploader(
        "Excel file",
        type=["xlsx"],
        key="upload_daily",
        help="The workbook must include TestName, subgroup, and CollectionDate columns."
    )
    
    if uploaded_file:
        try:
            source_file = uploaded_file.getvalue()
            df = pd.read_excel(BytesIO(source_file))
            
            # Validate required columns
            required_columns = ['TestName', 'subgroup', 'CollectionDate']
            missing = [col for col in required_columns if col not in df.columns]
            if missing:
                st.error(f"❌ Missing columns: {', '.join(missing)}")
                st.stop()
            
            # Use the most frequent CollectionDate to identify the daily report.
            report_date_str = get_report_date(df)
            upload_fingerprint = hashlib.sha256(source_file).hexdigest()
            same_upload_processed = (
                st.session_state.get("last_upload_fingerprint") == upload_fingerprint
            )
            
            test_counts = build_test_counts(df)
            cat_counts, categorized_df = build_category_counts(df)
            
            if report_date_str in get_saved_dates():
                if same_upload_processed:
                    upload_result = st.session_state.get("last_upload_result")
                    if upload_result == "cancelled":
                        st.info("Upload cancelled. The existing report was kept.")
                        st.stop()
                    elif upload_result == "replaced":
                        st.success(f"Report for {report_date_str} was replaced.")
                    else:
                        st.info(f"This workbook is already processed for {report_date_str}.")
                else:
                    st.warning(
                        f"A report for {report_date_str} already exists. "
                        "Replace it with this upload, or cancel to keep the saved report?"
                    )
                    replace_col, cancel_col = st.columns(2)
                    with replace_col:
                        replace_report = st.button(
                            "Replace existing report",
                            type="primary",
                            width="stretch",
                            key=f"replace_report_{report_date_str}"
                        )
                    with cancel_col:
                        cancel_upload = st.button(
                            "Cancel upload",
                            width="stretch",
                            key=f"cancel_upload_{report_date_str}"
                        )

                    if replace_report:
                        save_processed_data(
                            report_date_str, df, test_counts, cat_counts, source_file
                        )
                        st.session_state["last_upload_fingerprint"] = upload_fingerprint
                        st.session_state["last_upload_result"] = "replaced"
                        st.success(f"Report for {report_date_str} was replaced.")
                    elif cancel_upload:
                        st.session_state["last_upload_fingerprint"] = upload_fingerprint
                        st.session_state["last_upload_result"] = "cancelled"
                        st.info("Upload cancelled. The existing report was kept.")
                        st.stop()
                    else:
                        st.stop()
            else:
                save_processed_data(
                    report_date_str, df, test_counts, cat_counts, source_file
                )
                st.session_state["last_upload_fingerprint"] = upload_fingerprint
                st.session_state["last_upload_result"] = "saved"
                st.success(f"✅ Report for {report_date_str} processed and saved successfully!")

            excel_report = style_excel(test_counts, cat_counts, report_date_str)
            st.download_button(
                label="⬇️ Download daily report",
                data=excel_report.getvalue(),
                file_name=f"Report_{report_date_str}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                width="stretch",
                key="download_daily_report"
            )
            
            # ================================================================
            # REPORT DETAILS
            # ================================================================
            st.markdown('<div class="glossy-card">', unsafe_allow_html=True)
            
            col1, col2 = st.columns([2, 2])
            with col1:
                st.markdown(f"### 📅 Report Date: **{report_date_str}**")
            with col2:
                st.markdown(f"### 🏥 Hospital: Aarogyadham")
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # ================================================================
            # KEY METRICS
            # ================================================================
            st.markdown("### 📊 Quick Metrics")
            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric("📋 Total Tests", len(df), delta=None)
            with m2:
                ipd_count = int(test_counts.iloc[-1]["IPD"]) if not test_counts.empty else 0
                st.metric("🛏️ IPD", ipd_count)
            with m3:
                opd_count = int(test_counts.iloc[-1]["OPD"]) if not test_counts.empty else 0
                st.metric("🚶 OPD", opd_count)

            daily_test_data = test_counts[test_counts["TestName"] != "Grand Total"]
            daily_category_data = cat_counts[cat_counts["Category"] != "Grand Total"]
            daily_ai_summary = {
                "report_date": report_date_str,
                "total_tests": int(test_counts.iloc[-1]["Total"]),
                "booking_mode_counts": {"IPD": ipd_count, "OPD": opd_count},
                "category_counts": daily_category_data[
                    ["Category", "Count"]
                ].to_dict(orient="records"),
                "most_requested_tests": daily_test_data.nlargest(
                    min(8, len(daily_test_data)), "Total"
                )[["TestName", "IPD", "OPD", "Total"]].to_dict(orient="records")
            }
            with st.expander("✨ AI workload insights", expanded=False):
                render_ai_insights(daily_ai_summary, "daily")
            
            # ================================================================
            # DETAILED TABLES
            # ================================================================
            st.markdown('<div class="glossy-card">', unsafe_allow_html=True)
            
            col_t1, col_t2 = st.columns(2)
            
            with col_t1:
                st.markdown("#### 🧬 Test-wise Breakdown")
                st.dataframe(test_counts, width="stretch", hide_index=True)
            
            with col_t2:
                st.markdown("#### 📂 Category Summary")
                st.dataframe(cat_counts, width="stretch", hide_index=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
        except Exception as e:
            st.error(f"❌ Error processing file: {str(e)}")
    else:
        st.session_state.pop("last_upload_fingerprint", None)
        st.session_state.pop("last_upload_result", None)
        st.info("Upload an Excel workbook to view its summary and download the report.")

# ============================================================================
# TAB 2: SAVED REPORTS MANAGEMENT
# ============================================================================
with tab2:
    st.markdown("### 📁 Saved daily reports")
    st.caption("Download any day’s formatted Excel report or expand a row to review its summaries.")
    
    saved_dates = get_saved_dates()
    
    if saved_dates:
        saved_dates_sorted = list(reversed(saved_dates))
        for date_str in saved_dates_sorted:
            df_loaded, test_counts, cat_counts = load_processed_data(date_str)
            if df_loaded is None or test_counts is None or cat_counts is None:
                st.warning(f"Saved data for {date_str} is incomplete.")
                continue

            grand_total = test_counts[test_counts["TestName"] == "Grand Total"]
            if grand_total.empty:
                st.warning(f"Saved test totals for {date_str} are missing.")
                continue

            totals = grand_total.iloc[0]
            with st.container(border=True):
                col_date, col_summary, col_download, col_details, col_delete = st.columns(
                    [1.45, 3, 1.45, 0.9, 0.7], vertical_alignment="center"
                )
                with col_date:
                    st.markdown(f"**📅 {date_str}**")
                with col_summary:
                    st.caption(
                        f"📋 {int(totals['Total']):,} tests  ·  "
                        f"🛏️ {int(totals['IPD']):,} IPD  ·  "
                        f"🚶 {int(totals['OPD']):,} OPD"
                    )
                with col_download:
                    saved_report = style_excel(test_counts, cat_counts, date_str)
                    st.download_button(
                        "⬇️ Download",
                        data=saved_report.getvalue(),
                        file_name=f"Report_{date_str}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        width="stretch",
                        key=f"download_saved_{date_str}"
                    )
                with col_details:
                    with st.popover("View"):
                        st.dataframe(test_counts, width="stretch", hide_index=True)
                        st.dataframe(cat_counts, width="stretch", hide_index=True)
                with col_delete:
                    if st.button(
                        "🗑️",
                        help=f"Delete report for {date_str}",
                        key=f"del_{date_str}",
                        width="stretch"
                    ):
                        delete_processed_data(date_str)
                        st.success(f"Deleted report for {date_str}.")
                        st.rerun()
    else:
        st.info("📂 No saved reports yet. Upload a file in the Daily Report tab to save it.")

# ============================================================================
# TAB 3: CUMULATIVE ANALYTICS
# ============================================================================
with tab3:
    st.markdown("### 📈 Lab activity at a glance")
    st.caption("Select a reporting period to explore workload trends and category mix.")

    saved_dates = get_saved_dates()
    if saved_dates:
        saved_date_values = [
            (value, datetime.strptime(value, "%d-%m-%Y").date())
            for value in saved_dates
        ]
        first_date = saved_date_values[0][1]
        last_date = saved_date_values[-1][1]
        selected_range = st.date_input(
            "Report date range",
            value=(first_date, last_date),
            min_value=first_date,
            max_value=last_date,
            key="analytics_date_range"
        )
        if isinstance(selected_range, tuple):
            range_start = selected_range[0]
            range_end = selected_range[-1]
        else:
            range_start = range_end = selected_range

        selected_dates = [
            value for value, parsed in saved_date_values
            if range_start <= parsed <= range_end
        ]
        daily_series = load_daily_report_series(selected_dates)
        cum_tc, cum_cc = compute_cumulative(selected_dates)

        if cum_tc is not None and not cum_tc.empty and not daily_series.empty:
            tc_data = cum_tc[cum_tc["TestName"] != "Grand Total"].copy()
            cc_data = cum_cc[cum_cc["Category"] != "Grand Total"].copy()
            grand_total = cum_tc[cum_tc["TestName"] == "Grand Total"].iloc[0]
            total_tests = int(grand_total["Total"])
            total_ipd = int(grand_total["IPD"])
            total_opd = int(grand_total["OPD"])
            report_days = len(daily_series)
            top_test = tc_data.loc[tc_data["Total"].idxmax()] if not tc_data.empty else None
            top_category = cc_data.loc[cc_data["Count"].idxmax()] if not cc_data.empty else None

            st.caption(
                f"Showing {range_start.strftime('%d %b %Y')} – "
                f"{range_end.strftime('%d %b %Y')} · {report_days} report days"
            )

            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.metric("🧪 Tests processed", f"{total_tests:,}")
            with m2:
                st.metric("🛏️ IPD tests", f"{total_ipd:,}")
            with m3:
                st.metric("🚶 OPD tests", f"{total_opd:,}")
            with m4:
                st.metric("📅 Report days", report_days)

            if top_test is not None and top_category is not None:
                st.info(
                    f"💡 **At a glance:** {top_test['TestName']} is the most frequent test "
                    f"({int(top_test['Total']):,} total). {top_category['Category']} "
                    f"leads by category with {int(top_category['Count']):,} tests."
                )

            with st.expander("✨ AI analytics insights", expanded=False):
                analytics_ai_summary = {
                    "reporting_period": {
                        "start": range_start.strftime("%Y-%m-%d"),
                        "end": range_end.strftime("%Y-%m-%d"),
                        "days_with_reports": report_days
                    },
                    "daily_workload": [
                        {
                            "date": row.Date.strftime("%Y-%m-%d"),
                            "total": int(row.Total),
                            "ipd": int(row.IPD),
                            "opd": int(row.OPD)
                        }
                        for row in daily_series.itertuples(index=False)
                    ],
                    "most_requested_tests": tc_data.nlargest(
                        min(10, len(tc_data)), "Total"
                    )[["TestName", "IPD", "OPD", "Total"]].to_dict(orient="records"),
                    "category_counts": cc_data[
                        ["Category", "Count"]
                    ].to_dict(orient="records")
                }
                render_ai_insights(analytics_ai_summary, "analytics")

            st.markdown("#### 📆 Daily test volume")
            chart_template = "plotly_dark" if theme_mode == "Night" else "plotly_white"
            chart_font = "#e5edf8" if theme_mode == "Night" else "#334155"
            grid_color = "#334155" if theme_mode == "Night" else "#e8edf5"
            fig_timeline = px.line(
                daily_series,
                x="Date",
                y=["Total", "IPD", "OPD"],
                markers=True,
                color_discrete_map={
                    "Total": "#8b5cf6",
                    "IPD": "#3b82f6",
                    "OPD": "#f59e0b"
                },
                labels={"value": "Test count", "Date": "Collection date", "variable": "Volume"}
            )
            fig_timeline.update_layout(
                height=370,
                template=chart_template,
                hovermode="x unified",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font={"color": chart_font},
                margin={"l": 10, "r": 15, "t": 20, "b": 20},
                legend={"orientation": "h", "y": 1.12, "x": 0}
            )
            fig_timeline.update_xaxes(showgrid=False)
            fig_timeline.update_yaxes(showgrid=True, gridcolor=grid_color, zeroline=False)
            st.plotly_chart(fig_timeline, width="stretch")

            col1, col2 = st.columns([1.4, 1])
            with col1:
                st.markdown("#### 🧬 Most requested tests")
                top_tests = tc_data.nlargest(min(12, len(tc_data)), "Total").sort_values("Total")
                fig_tc = px.bar(
                    top_tests,
                    x=["IPD", "OPD"],
                    y="TestName",
                    orientation="h",
                    barmode="group",
                    color_discrete_map={"IPD": "#3b82f6", "OPD": "#f59e0b"},
                    labels={"value": "Tests", "TestName": "Test", "variable": "Booking type"}
                )
                fig_tc.update_layout(
                    hovermode="y unified",
                    showlegend=True,
                    height=460,
                    template=chart_template,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font={"color": chart_font},
                    margin={"l": 10, "r": 15, "t": 20, "b": 20},
                    legend={"orientation": "h", "y": 1.08, "x": 0}
                )
                fig_tc.update_xaxes(showgrid=True, gridcolor=grid_color, zeroline=False)
                fig_tc.update_yaxes(showgrid=False)
                st.plotly_chart(fig_tc, width="stretch")

            with col2:
                st.markdown("#### 🧩 Test category mix")
                fig_cc = px.pie(
                    cc_data,
                    values="Count",
                    names="Category",
                    hole=0.58,
                    color_discrete_sequence=["#3b82f6", "#14b8a6", "#f59e0b", "#8b5cf6"]
                )
                fig_cc.update_layout(
                    height=460,
                    template=chart_template,
                    paper_bgcolor="rgba(0,0,0,0)",
                    font={"color": chart_font},
                    margin={"l": 10, "r": 10, "t": 20, "b": 15},
                    legend={"orientation": "h", "y": -0.08, "x": 0}
                )
                fig_cc.update_traces(textposition="inside", textinfo="percent")
                st.plotly_chart(fig_cc, width="stretch")

            st.markdown("#### 📋 Detailed totals")
            tab_test, tab_cat = st.tabs(["🧬 Test Counts", "📂 Category Counts"])
            with tab_test:
                st.dataframe(cum_tc, width="stretch", hide_index=True)
            with tab_cat:
                st.dataframe(cum_cc, width="stretch", hide_index=True)
        else:
            st.info("No saved reports fall within this date range.")
    else:
        st.info("📊 No saved reports yet. Upload a daily workbook to start building your analytics.")
