"""StorageDocker: high-performance Supabase object storage."""

from __future__ import annotations

import tempfile
from datetime import datetime
from html import escape
from pathlib import Path

import streamlit as st

from supabase_crud.config import ConfigurationError, Settings
from supabase_crud.helpers import human_size
from supabase_crud.service import FileService


st.set_page_config(
    page_title="StorageDocker",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom Design: StorageDocker Dark Minimalist Theme
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    :root {
        --canvas: #0B0C0E;
        --surface: #131418;
        --surface-soft: #181A20;
        --surface-hover: #1E2028;
        --border: #232630;
        --border-focus: #EF4444;
        --text-strong: #FFFFFF;
        --text-body: #B0B7C6;
        --text-dim: #717888;
        --text-subtle: #4B5262;
        --red: #E53E3E;
        --red-hover: #F56565;
        --red-subtle: rgba(229, 62, 62, 0.12);
        --red-border: rgba(229, 62, 62, 0.28);
        --supabase-green: #3ECF8E;
    }

    /* Reset & Base */
    html, body, .stApp {
        background-color: var(--canvas) !important;
        color: var(--text-strong) !important;
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
        margin: 0;
        padding: 0;
    }

    .stAppHeader,
    header[data-testid="stHeader"],
    .stApp > header {
        display: none !important;
        background: transparent !important;
        background-color: transparent !important;
        height: 0 !important;
        min-height: 0 !important;
    }

    [data-testid="stMainBlockContainer"],
    .main .block-container {
        max-width: 1340px !important;
        width: 95% !important;
        margin: 0 auto !important;
        padding: 2.2rem 2rem 5rem !important;
    }

    [data-testid="stVerticalBlock"] {
        gap: 1.15rem !important;
    }

    /* Header Masthead */
    .brand-masthead {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding-bottom: 1.4rem;
        border-bottom: 1px solid var(--border);
        margin-bottom: 0.25rem;
    }
    .brand-cluster {
        display: flex;
        align-items: center;
        gap: 1.1rem;
    }
    .supabase-logo-mark {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 44px;
        height: 44px;
        background: #14171F;
        border: 1px solid #282D3D;
        border-radius: 10px;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.4);
    }
    .brand-copy {
        display: flex;
        flex-direction: column;
    }
    .brand-title {
        font-size: 1.85rem;
        font-weight: 800;
        color: var(--text-strong);
        letter-spacing: -0.03em;
        line-height: 1.15;
    }
    .brand-title span {
        color: var(--red);
    }
    .brand-tagline {
        font-size: 0.82rem;
        font-weight: 600;
        color: var(--text-dim);
        margin-top: 0.15rem;
    }

    /* Stats Grid */
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1rem;
        margin-bottom: 0.25rem;
    }
    .stat-card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 1rem 1.3rem;
        display: flex;
        flex-direction: column;
        gap: 0.3rem;
    }
    .stat-label {
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--text-dim);
    }
    .stat-value {
        font-size: 1.3rem;
        font-weight: 800;
        color: var(--text-strong);
    }
    .stat-value small {
        font-size: 0.82rem;
        font-weight: 600;
        color: var(--text-dim);
        margin-left: 0.25rem;
    }

    /* Ingest Panel */
    .st-key-ingest_panel {
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
        padding: 1.3rem 1.6rem !important;
    }
    .ingest-heading {
        display: flex;
        align-items: center;
        font-size: 0.82rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: var(--text-strong);
        margin-bottom: 0.9rem !important;
    }
    .ingest-heading span {
        color: var(--red);
    }

    /* Streamlit File Uploader */
    [data-testid="stFileUploader"] {
        padding: 0 !important;
        margin: 0 !important;
    }
    [data-testid="stFileUploader"] section {
        min-height: 5.4rem !important;
        padding: 1.1rem 1.5rem !important;
        background: #141720 !important;
        border: 1.5px dashed #363C4E !important;
        border-radius: 10px !important;
        transition: all 0.2s ease;
    }
    [data-testid="stFileUploader"] section:hover {
        border-color: var(--red) !important;
        background: #181C26 !important;
    }
    [data-testid="stFileUploader"] section svg,
    [data-testid="stFileUploader"] section [data-testid="stIconMaterial"] {
        color: var(--red) !important;
        fill: var(--red) !important;
        width: 28px !important;
        height: 28px !important;
    }
    [data-testid="stFileUploader"] section [data-testid="stMarkdownContainer"] p,
    [data-testid="stFileUploader"] section [data-testid="stBaseButton-secondary"] + div p {
        color: #FFFFFF !important;
        font-size: 0.98rem !important;
        font-weight: 700 !important;
    }
    [data-testid="stFileUploader"] section [data-testid="stMarkdownContainer"] small,
    [data-testid="stFileUploader"] section small,
    [data-testid="stFileUploader"] section [data-testid="stMarkdownContainer"] span {
        color: #B5BDCC !important;
        font-size: 0.84rem !important;
        font-weight: 600 !important;
    }
    /* Streamlit nests the dropzone copy differently across versions. Keep
       both lines readable even when they are rendered as plain divs. */
    [data-testid="stFileUploader"] section [data-testid="stFileUploaderDropzoneInstructions"] * {
        color: #F8FAFC !important;
    }
    [data-testid="stFileUploader"] section [data-testid="stFileUploaderDropzoneInstructions"] > div:last-child,
    [data-testid="stFileUploader"] section [data-testid="stFileUploaderDropzoneInstructions"] > div:last-child * {
        color: #C5CDDA !important;
        font-size: 0.84rem !important;
        font-weight: 600 !important;
    }
    [data-testid="stFileUploader"] button {
        background: var(--surface-soft) !important;
        color: #FFFFFF !important;
        border: 1px solid #363C4E !important;
        border-radius: 6px !important;
        font-weight: 700 !important;
        font-size: 0.84rem !important;
        padding: 0.45rem 1.1rem !important;
        transition: all 0.15s ease !important;
    }
    [data-testid="stFileUploader"] button:hover {
        border-color: var(--red) !important;
        color: #FFFFFF !important;
        background: var(--red) !important;
    }

    /* Register Heading & Controls */
    .register-heading {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        font-size: 0.95rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--text-strong);
    }
    .register-heading span:first-child {
        color: var(--red);
    }
    .register-count-pill {
        padding: 0.18rem 0.6rem;
        background: var(--surface-soft);
        border: 1px solid var(--border);
        border-radius: 999px;
        font-size: 0.72rem;
        font-weight: 700;
        color: var(--text-body);
    }

    /* Search & Inputs */
    [data-testid="stInputInstructions"],
    .stInputInstructions,
    div[data-testid="stInputInstructions"] {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        height: 0 !important;
        width: 0 !important;
    }

    [data-testid="stTextInputRootElement"],
    .stTextInput input {
        border-radius: 8px !important;
        border: 1px solid #2F3546 !important;
        background: #161822 !important;
        font-size: 0.9rem !important;
        font-weight: 600 !important;
        color: #FFFFFF !important;
        box-shadow: none !important;
    }
    .stTextInput input:focus {
        border-color: var(--red) !important;
        box-shadow: 0 0 0 2px rgba(229, 62, 62, 0.2) !important;
    }
    [data-testid="stTextInputRootElement"] input {
        padding: 0.58rem 1rem !important;
    }
    .stTextInput input::placeholder,
    [data-testid="stTextInputRootElement"] input::placeholder {
        color: #8E97A8 !important;
        opacity: 1 !important;
        font-weight: 500 !important;
    }

    /* Table Container */
    .st-key-object_register {
        background: #111319 !important;
        border: 1px solid #232736 !important;
        border-radius: 14px !important;
        overflow: hidden !important;
        padding: 0.55rem !important;
        margin-top: 0.35rem !important;
    }
    .st-key-object_register > div > [data-testid="stVerticalBlock"] {
        gap: 0.35rem !important;
    }

    /* Table Rows */
    .st-key-object_register [data-testid="stHorizontalBlock"] {
        padding: 0.95rem 1.35rem !important;
        background-color: transparent !important;
        border-radius: 8px !important;
        border: none !important;
        align-items: center !important;
        transition: background-color 0.15s ease;
    }
    .st-key-object_register [data-testid="stHorizontalBlock"]:hover {
        background-color: var(--surface-hover) !important;
    }

    /* Table Header Strip - Spacious & Bold */
    .st-key-object_register [data-testid="stHorizontalBlock"]:first-child {
        background-color: #171A24 !important;
        padding: 1rem 1.35rem !important;
        min-height: 48px !important;
        border-radius: 9px !important;
        border: 1px solid #262C3E !important;
        margin-bottom: 0.35rem !important;
    }
    .st-key-object_register [data-testid="stHorizontalBlock"]:first-child:hover {
        background-color: #171A24 !important;
    }

    .header-cell {
        font-size: 0.8rem !important;
        font-weight: 800 !important;
        letter-spacing: 0.08em !important;
        text-transform: uppercase !important;
        color: #94A3B8 !important;
        line-height: 1.4 !important;
    }

    /* File Identity */
    .file-name-block {
        display: flex;
        align-items: center;
        gap: 0.9rem;
    }
    .file-ext-badge {
        font-size: 0.72rem;
        font-weight: 800;
        padding: 0.25rem 0.55rem;
        border-radius: 6px;
        background: var(--surface-soft);
        border: 1px solid var(--border);
        color: var(--red);
        text-transform: uppercase;
        flex-shrink: 0;
        min-width: 40px;
        text-align: center;
    }
    .file-info-block {
        display: flex;
        flex-direction: column;
        justify-content: center;
        overflow: hidden;
    }
    .file-name-text {
        font-size: 0.95rem;
        font-weight: 700;
        color: var(--text-strong);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        line-height: 1.3;
    }
    .file-desc-sub {
        font-size: 0.82rem;
        font-weight: 500;
        color: var(--text-body);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        line-height: 1.3;
        margin-top: 0.15rem;
    }

    .cell-data {
        font-size: 0.86rem;
        font-weight: 600;
        color: var(--text-body);
        line-height: 1.2;
    }

    /* Popover Action Button - Center aligned */
    .st-key-object_register div[data-testid="stPopover"] {
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        width: 100% !important;
        margin: 0 auto !important;
    }
    .st-key-object_register div[data-testid="stPopover"] button {
        min-height: 32px !important;
        height: 32px !important;
        width: 36px !important;
        min-width: 36px !important;
        padding: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        margin: 0 auto !important;
        background: var(--surface-soft) !important;
        border: 1px solid var(--border) !important;
        border-radius: 6px !important;
        color: var(--text-body) !important;
        box-shadow: none !important;
        cursor: pointer !important;
        transition: all 0.15s ease !important;
        position: relative !important;
    }
    .st-key-object_register div[data-testid="stPopover"] button:hover {
        background: var(--red) !important;
        border-color: var(--red) !important;
        color: #FFFFFF !important;
    }
    .st-key-object_register div[data-testid="stPopover"] [data-testid="stIconMaterial"],
    .st-key-object_register div[data-testid="stPopover"] svg {
        display: none !important;
    }
    .st-key-object_register div[data-testid="stPopover"] button p {
        font-size: 1.25rem !important;
        font-weight: 800 !important;
        line-height: 1 !important;
        margin: 0 !important;
        padding: 0 !important;
        text-align: center !important;
        position: absolute !important;
        inset: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    .st-key-object_register div[data-testid="stPopover"] button > div[data-testid="stMarkdownContainer"] {
        width: 100% !important;
        height: 100% !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }

    /* COMPACT CONTEXT MENU POPOVER */
    div[data-testid="stPopoverBody"],
    [data-testid="stPopoverBody"],
    div[data-testid="stPopoverBody"] > div {
        background: #14161F !important;
        background-color: #14161F !important;
        border: 1px solid #282E40 !important;
        border-radius: 10px !important;
        box-shadow: 0 12px 32px rgba(0, 0, 0, 0.85) !important;
        color: #FFFFFF !important;
    }
    div[data-testid="stPopoverBody"] {
        padding: 0.75rem !important;
        min-width: 175px !important;
        max-width: 220px !important;
    }
    div[data-testid="stPopoverBody"] [data-testid="stVerticalBlock"] {
        gap: 0.45rem !important;
    }
    div[data-testid="stPopoverBody"] button,
    div[data-testid="stPopoverBody"] a[data-testid="stLinkButton"],
    div[data-testid="stPopoverBody"] a[data-testid="stLinkButton"] > span,
    div[data-testid="stPopoverBody"] a[data-testid="stBaseButton-secondary"] {
        background: #1C202C !important;
        background-color: #1C202C !important;
        border: 1px solid #2F3548 !important;
        color: #FFFFFF !important;
        border-radius: 6px !important;
        font-weight: 700 !important;
        font-size: 0.82rem !important;
        padding: 0.4rem 0.6rem !important;
        text-align: center !important;
        display: block !important;
        width: 100% !important;
        transition: all 0.15s ease !important;
    }
    div[data-testid="stPopoverBody"] button:hover,
    div[data-testid="stPopoverBody"] a[data-testid="stLinkButton"]:hover {
        background: #272C3D !important;
        border-color: #434B64 !important;
        color: #FFFFFF !important;
    }
    div[data-testid="stPopoverBody"] button[kind="primary"] {
        background: rgba(229, 62, 62, 0.16) !important;
        border: 1px solid rgba(229, 62, 62, 0.4) !important;
        color: #FF5A5A !important;
    }
    div[data-testid="stPopoverBody"] button[kind="primary"]:hover {
        background: #E53E3E !important;
        border-color: #E53E3E !important;
        color: #FFFFFF !important;
    }

    /* Dialog Overlay & Backdrop - Translucent Frosted Glass */
    div[data-baseweb="modal"],
    div[data-baseweb="backdrop"],
    div[data-testid="stDialogOverlay"],
    div[data-testid="stBackdrop"],
    [data-testid="stDialog"],
    [data-testid="stModal"],
    section[data-testid="stModal"],
    dialog::backdrop {
        background: rgba(11, 12, 14, 0.65) !important;
        background-color: rgba(11, 12, 14, 0.65) !important;
        backdrop-filter: blur(8px) !important;
        -webkit-backdrop-filter: blur(8px) !important;
    }

    /* Intermediate full-screen modal containers - MUST BE TRANSPARENT */
    div[data-baseweb="modal"] > div,
    [data-testid="stDialog"] > div,
    [data-testid="stModal"] > div,
    section[data-testid="stModal"] > div {
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }

    /* Modal / Dialog Window Card */
    div[role="dialog"],
    [data-baseweb="modal-body"] {
        background: #13151D !important;
        background-color: #13151D !important;
        border: 1px solid #2F364A !important;
        border-radius: 14px !important;
        box-shadow: 0 24px 60px rgba(0, 0, 0, 0.95) !important;
        color: #FFFFFF !important;
    }
    div[role="dialog"] h2,
    div[role="dialog"] h1,
    div[role="dialog"] h3,
    div[role="dialog"] [data-testid="stHeadingWithActionElements"] *,
    [data-testid="stDialog"] h2,
    [data-testid="stDialog"] h1,
    [data-testid="stDialog"] [data-testid="stDialogTitle"] {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        font-size: 1.3rem !important;
        font-weight: 800 !important;
        letter-spacing: -0.01em !important;
        opacity: 1 !important;
    }
    div[role="dialog"] button[aria-label="Close"],
    [data-testid="stDialog"] button[aria-label="Close"],
    [data-testid="stDialog"] svg {
        color: #FFFFFF !important;
        fill: #FFFFFF !important;
        opacity: 0.8 !important;
    }
    div[role="dialog"] button[aria-label="Close"]:hover {
        opacity: 1 !important;
        color: #EF4444 !important;
    }
    div[role="dialog"] label,
    [data-testid="stDialog"] label,
    div[role="dialog"] label p,
    [data-testid="stDialog"] label p {
        color: #F8FAFC !important;
        font-size: 0.9rem !important;
        font-weight: 700 !important;
        opacity: 1 !important;
    }
    div[role="dialog"] textarea,
    div[role="dialog"] input,
    [data-testid="stDialog"] textarea,
    [data-testid="stDialog"] input {
        background: #181B26 !important;
        background-color: #181B26 !important;
        border: 1px solid #384158 !important;
        border-radius: 8px !important;
        color: #FFFFFF !important;
        font-size: 0.95rem !important;
        font-weight: 600 !important;
        padding: 0.62rem 0.85rem !important;
        height: 42px !important;
        min-height: 42px !important;
        box-sizing: border-box !important;
    }
    div[role="dialog"] textarea,
    [data-testid="stDialog"] textarea {
        height: 110px !important;
        min-height: 110px !important;
    }
    div[role="dialog"] textarea:focus,
    div[role="dialog"] input:focus,
    [data-testid="stDialog"] textarea:focus,
    [data-testid="stDialog"] input:focus {
        border-color: #EF4444 !important;
        box-shadow: 0 0 0 2px rgba(239, 68, 68, 0.25) !important;
        background: #1E2232 !important;
        color: #FFFFFF !important;
    }
    div[role="dialog"] textarea::placeholder,
    div[role="dialog"] input::placeholder,
    [data-testid="stDialog"] textarea::placeholder,
    [data-testid="stDialog"] input::placeholder {
        color: #A0ABC0 !important;
        opacity: 1 !important;
        font-weight: 500 !important;
    }
    [data-testid="stDialog"] [data-testid="stHorizontalBlock"],
    .st-key-ingest_panel [data-testid="stHorizontalBlock"] {
        align-items: center !important;
        gap: 0.5rem !important;
    }
    [data-testid="stDialog"] [data-testid="stColumn"],
    .st-key-ingest_panel [data-testid="stColumn"] {
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
    }
    [data-testid="stDialog"] [data-testid="stElementContainer"],
    .st-key-ingest_panel [data-testid="stElementContainer"] {
        margin: 0 !important;
        padding: 0 !important;
    }
    [data-testid="stDialog"] [data-testid="stTextInput"],
    .st-key-ingest_panel [data-testid="stTextInput"] {
        margin: 0 !important;
    }
    [data-testid="stDialog"] [data-testid="stMarkdownContainer"] p,
    .st-key-ingest_panel [data-testid="stMarkdownContainer"] p {
        margin: 0 !important;
        padding: 0 !important;
        line-height: 1 !important;
    }
    [data-testid="stDialog"] .stMarkdown,
    [data-testid="stDialog"] [data-testid="stMarkdownContainer"],
    .st-key-ingest_panel .stMarkdown,
    .st-key-ingest_panel [data-testid="stMarkdownContainer"] {
        margin: 0 !important;
        padding: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    .modal-locked-ext {
        background: #181B26 !important;
        border: 1px solid #384158 !important;
        border-radius: 8px !important;
        color: #EF4444 !important;
        font-weight: 800 !important;
        font-size: 0.88rem !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 0.35rem !important;
        height: 42px !important;
        min-height: 42px !important;
        max-height: 42px !important;
        padding: 0 0.85rem !important;
        text-transform: uppercase !important;
        user-select: none !important;
        box-sizing: border-box !important;
        margin: 0 !important;
        width: 100% !important;
    }

    /* Standard Buttons */
    .stButton > button {
        border-radius: 7px !important;
        font-weight: 700 !important;
        font-size: 0.84rem !important;
        border: 1px solid var(--border) !important;
        color: var(--text-strong) !important;
        background: var(--surface-soft) !important;
        transition: all 0.15s ease !important;
    }
    .stButton > button:hover {
        background: var(--surface-hover) !important;
        border-color: #3B4254 !important;
        color: #FFFFFF !important;
    }
    .stButton > button[kind="primary"] {
        background: var(--red) !important;
        border-color: var(--red) !important;
        color: white !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: var(--red-hover) !important;
        border-color: var(--red-hover) !important;
    }

    /* Pagination */
    .index-count {
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--text-dim);
    }

    .empty-notice {
        padding: 4rem 2rem;
        text-align: center;
        color: var(--text-dim);
        font-size: 0.95rem;
        font-weight: 600;
    }

    @media (max-width: 900px) {
        .stats-grid {
            grid-template-columns: repeat(2, 1fr);
        }
    }

    @media (max-width: 780px) {
        [data-testid="stMainBlockContainer"],
        .main .block-container {
            padding: 1.25rem 1rem 3rem !important;
            width: 100% !important;
        }
        .brand-title {
            font-size: 1.5rem;
        }
        .stats-grid {
            grid-template-columns: 1fr;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def get_service() -> FileService:
    return FileService(Settings.from_env())


def format_iso(iso_str: object) -> str:
    if not iso_str:
        return "—"
    try:
        dt = datetime.fromisoformat(str(iso_str).replace("Z", "+00:00"))
        return dt.strftime("%b %d, %Y · %H:%M")
    except Exception:
        return str(iso_str)[:16]


def upload_to_temp(uploaded_file) -> Path:
    suffix = Path(uploaded_file.name).suffix
    handle = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        handle.write(uploaded_file.getvalue())
        return Path(handle.name)
    finally:
        handle.close()


@st.dialog("Edit Object Details")
def edit_file_modal(service: FileService, record: dict[str, Any]) -> None:
    """Dialog modal for editing a file's name (extension locked) and custom field note."""
    rec_id = record["id"]
    current_full_name = record.get("original_name") or ""
    path_obj = Path(current_full_name)
    current_stem = path_obj.stem
    current_ext = path_obj.suffix  # e.g. ".webp"
    current_desc = record.get("description") or ""

    st.markdown(
        """
        <div style="font-size: 0.88rem; color: #CBD5E1; line-height: 1.5; font-weight: 500; margin-bottom: 1.15rem; margin-top: -0.25rem;">
            Rename the object or update its custom field note / metadata. The file extension is locked and preserved automatically.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div style="font-size: 0.88rem; font-weight: 700; color: #FFFFFF; margin-bottom: 0.4rem;">File Name</div>',
        unsafe_allow_html=True,
    )
    name_col, ext_col = st.columns([3.8, 1.2], vertical_alignment="center")
    with name_col:
        new_stem = st.text_input(
            "File Name Stem",
            value=current_stem,
            placeholder="Enter file name...",
            label_visibility="collapsed",
            key=f"modal_stem_{rec_id}",
        )
    with ext_col:
        ext_display = current_ext if current_ext else "—"
        st.markdown(
            f'<div class="modal-locked-ext" title="Extension locked: {escape(ext_display)}">🔒 {escape(ext_display)}</div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div style="font-size: 0.88rem; font-weight: 700; color: #FFFFFF; margin-top: 0.9rem; margin-bottom: 0.4rem;">Field Note / Description</div>',
        unsafe_allow_html=True,
    )
    new_desc = st.text_area(
        "Field Note / Description",
        value=current_desc,
        placeholder="Enter custom metadata, notes, or tags...",
        label_visibility="collapsed",
        key=f"modal_desc_{rec_id}",
        height=110,
    )

    btn_col1, btn_col2 = st.columns([1, 1])
    with btn_col1:
        if st.button("Save Changes", type="primary", use_container_width=True, key=f"modal_save_{rec_id}"):
            clean_stem = new_stem.strip()
            if not clean_stem:
                st.error("File name cannot be empty.")
                return
            # Automatically preserve and attach the locked extension
            full_filename = f"{clean_stem}{current_ext}"
            try:
                service.update_metadata(
                    rec_id,
                    original_name=full_filename,
                    description=new_desc.strip() or None,
                )
                st.toast("Object details updated successfully!", icon="⚡")
                st.rerun()
            except Exception as exc:
                st.error(f"Failed to update: {exc}")
    with btn_col2:
        if st.button("Cancel", use_container_width=True, key=f"modal_cancel_{rec_id}"):
            st.rerun()


def render_upload_panel(service: FileService) -> None:
    """Render a compact, always-visible ingest surface."""
    with st.container(key="ingest_panel"):
        st.markdown(
            """
            <div class="ingest-heading">
                <span>01 / Ingest Object</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        uploaded_file = st.file_uploader(
            "Drop a source file",
            type=["pdf", "png", "jpg", "jpeg", "webp", "gif", "txt", "csv", "json", "docx"],
            help="PDF, images, plaintext, CSV, or JSON up to 10 MB",
            label_visibility="collapsed",
        )

        if uploaded_file is None:
            return

        file_stem = Path(uploaded_file.name).stem
        file_ext = Path(uploaded_file.name).suffix

        name_col, ext_col, note_col, action_col = st.columns([2.3, 0.9, 3.2, 1.4], vertical_alignment="bottom")
        with name_col:
            file_name_stem = st.text_input(
                "File name stem",
                value=file_stem,
                placeholder="File name",
                label_visibility="collapsed",
            )
        with ext_col:
            ext_display = file_ext if file_ext else "—"
            st.markdown(
                f'<div class="modal-locked-ext" style="height: 38px; font-size: 0.82rem;" title="Extension locked: {escape(ext_display)}">🔒 {escape(ext_display)}</div>',
                unsafe_allow_html=True,
            )
        with note_col:
            file_note = st.text_input(
                "Field note",
                placeholder="Add description or field note (optional)",
                label_visibility="collapsed",
            )
        with action_col:
            archive_clicked = st.button("Ingest Object", type="primary", use_container_width=True)

        if archive_clicked:
            if uploaded_file.size > service.settings.max_file_size_bytes:
                st.error(f"File exceeds {human_size(service.settings.max_file_size_bytes)}.")
                return

            clean_stem = file_name_stem.strip() or file_stem
            custom_name = f"{clean_stem}{file_ext}"
            temp_path = upload_to_temp(uploaded_file)
            try:
                with st.spinner("Ingesting to Supabase Storage…"):
                    service.create_file(
                        str(temp_path),
                        description=file_note.strip() or None,
                        original_name=custom_name,
                    )
                st.toast("Object ingested successfully.", icon="⚡")
                st.rerun()
            except Exception as error:
                st.error(f"Upload rejected: {error}")
            finally:
                temp_path.unlink(missing_ok=True)


def main() -> None:
    # Official Supabase SVG logo + StorageDocker Masthead
    supabase_svg = """<svg width="24" height="24" viewBox="0 0 109 113" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M63.7076 110.284C60.848 113.885 55.0502 111.912 54.9813 107.314L53.9738 40.0667H97.3849C102.133 40.0667 104.887 45.4277 102.047 49.2222L63.7076 110.284Z" fill="url(#sb_gradient)"/>
<path d="M63.7076 110.284C60.848 113.885 55.0502 111.912 54.9813 107.314L53.9738 40.0667H97.3849C102.133 40.0667 104.887 45.4277 102.047 49.2222L63.7076 110.284Z" fill="black" fill-opacity="0.2"/>
<path d="M45.297 2.71556C48.1566 -0.885444 53.9544 1.08779 54.0233 5.68595L54.4442 72.9333H11.6151C6.8669 72.9333 4.11299 67.5723 6.95304 63.7778L45.297 2.71556Z" fill="#3ECF8E"/>
<defs>
<linearGradient id="sb_gradient" x1="53.9738" y1="54.9999" x2="94.4635" y2="73.8417" gradientUnits="userSpaceOnUse">
<stop stop-color="#249361"/>
<stop offset="1" stop-color="#3ECF8E"/>
</linearGradient>
</defs>
</svg>"""

    st.markdown(
        f"""
        <div class="brand-masthead">
            <div class="brand-cluster">
                <div class="supabase-logo-mark">
                    {supabase_svg}
                </div>
                <div class="brand-copy">
                    <div class="brand-title">Storage<span>Docker</span></div>
                    <div class="brand-tagline">
                        Enterprise Object Storage Registry
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    try:
        service = get_service()
    except ConfigurationError as exc:
        st.error(str(exc))
        st.info("Check .env credentials.")
        st.stop()

    records = service.list_files()

    # Metrics Summary
    total_bytes = sum(r.get("size_bytes") or 0 for r in records)
    total_count = len(records)
    latest_date = format_iso(records[0].get("created_at")) if records else "None"
    st.markdown(
        f"""
        <div class="stats-grid">
            <div class="stat-card">
                <span class="stat-label">Total Objects</span>
                <span class="stat-value">{total_count:02d} <small>files</small></span>
            </div>
            <div class="stat-card">
                <span class="stat-label">Total Storage</span>
                <span class="stat-value">{human_size(total_bytes)}</span>
            </div>
            <div class="stat-card">
                <span class="stat-label">Latest Upload</span>
                <span class="stat-value" style="font-size: 0.95rem; font-weight: 700;">{latest_date}</span>
            </div>
            <div class="stat-card">
                <span class="stat-label">Cloud Backend</span>
                <span class="stat-value" style="font-size: 0.95rem; font-weight: 700; color: #3ECF8E;">Supabase Storage</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_upload_panel(service)

    register_col, search_col = st.columns([5, 2.5], vertical_alignment="center")
    with register_col:
        st.markdown(
            f"""
            <div class="register-heading">
                <span>02 / Object Register</span>
                <span class="register-count-pill">{len(records):02d} OBJECTS</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with search_col:
        search = st.text_input(
            "Search",
            placeholder="Search by name, note, or format…",
            label_visibility="collapsed",
        ).strip().lower()

    filtered = sorted(records, key=lambda item: str(item.get("created_at") or ""), reverse=True)
    if search:
        filtered = [
            r for r in filtered
            if search in f"{r.get('original_name', '')} {r.get('description', '')} {r.get('content_type', '')}".lower()
        ]

    # Table Box Container
    table_box = st.container(key="object_register")

    if not filtered:
        table_box.markdown(
            """
            <div class="empty-notice">No objects match the current search query.</div>
            """,
            unsafe_allow_html=True,
        )
        return

    # Pagination calculation
    page_size = 6
    page_count = max(1, (len(filtered) + page_size - 1) // page_size)
    filter_fingerprint = search
    if st.session_state.get("archive_filter") != filter_fingerprint:
        st.session_state.archive_filter = filter_fingerprint
        st.session_state.archive_page = 0

    current_page = min(int(st.session_state.get("archive_page", 0)), page_count - 1)
    page_start = current_page * page_size
    page_records = filtered[page_start : page_start + page_size]
    page_end = page_start + len(page_records)

    # Column proportions: center action column
    col_weights = [5.6, 1.4, 2.2, 0.8]

    # Render Table Header (inside table_box)
    with table_box:
        hdr_cols = st.columns(col_weights, vertical_alignment="center")
        hdr_cols[0].markdown('<div class="header-cell">Document & Notes</div>', unsafe_allow_html=True)
        hdr_cols[1].markdown('<div class="header-cell">File Size</div>', unsafe_allow_html=True)
        hdr_cols[2].markdown('<div class="header-cell">Uploaded Date</div>', unsafe_allow_html=True)
        hdr_cols[3].markdown('<div class="header-cell" style="text-align: center;">Actions</div>', unsafe_allow_html=True)

        # Render Table Rows
        for r in page_records:
            rec_id = r["id"]
            orig_name = r.get("original_name") or "unnamed"
            ext = Path(orig_name).suffix.lstrip(".") or "txt"
            size_str = human_size(r.get("size_bytes"))
            date_str = format_iso(r.get("created_at"))
            desc = r.get("description")

            desc_html = (
                f'<div class="file-desc-sub">{escape(desc)}</div>'
                if desc
                else '<div class="file-desc-sub" style="color: var(--text-subtle);">No field note</div>'
            )

            cols = st.columns(col_weights, vertical_alignment="center")
            with cols[0]:
                st.markdown(
                    f"""
                    <div class="file-name-block">
                        <div class="file-ext-badge">{ext[:4]}</div>
                        <div class="file-info-block">
                            <div class="file-name-text" title="{escape(orig_name)}">{escape(orig_name)}</div>
                            {desc_html}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with cols[1]:
                st.markdown(f"<div class='cell-data'>{size_str}</div>", unsafe_allow_html=True)
            with cols[2]:
                st.markdown(f"<div class='cell-data'>{date_str}</div>", unsafe_allow_html=True)
            with cols[3]:
                action_popover = st.popover("⋮", use_container_width=True)
                with action_popover:
                    if st.button("Edit Details", key=f"edit_btn_{rec_id}", use_container_width=True):
                        edit_file_modal(service, r)

                    try:
                        signed_url = service.create_signed_url(rec_id)
                        st.link_button("Download", signed_url, use_container_width=True)
                    except Exception:
                        st.caption("Download unavailable")

                    if st.button("Delete", key=f"del_{rec_id}", type="primary", use_container_width=True):
                        try:
                            service.delete_file(rec_id)
                            st.toast("Object deleted.")
                            st.rerun()
                        except Exception as err:
                            st.error(str(err))

    # Pagination controls below table
    if page_count > 1:
        pag_col1, pag_col2, pag_col3 = st.columns([8, 1.2, 1.2], vertical_alignment="center")
        with pag_col1:
            st.markdown(
                f'<div class="index-count">{page_start + 1:02d}–{page_end:02d} of {len(filtered):02d} objects</div>',
                unsafe_allow_html=True,
            )
        with pag_col2:
            if st.button("← Previous", key="archive_previous", disabled=current_page == 0, use_container_width=True):
                st.session_state.archive_page = current_page - 1
                st.rerun()
        with pag_col3:
            if st.button("Next →", key="archive_next", disabled=current_page >= page_count - 1, use_container_width=True):
                st.session_state.archive_page = current_page + 1
                st.rerun()


if __name__ == "__main__":
    main()

