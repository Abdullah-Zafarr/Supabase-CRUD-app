"""Tideframe: a quiet coastal-inspired Supabase object archive."""

from __future__ import annotations

import tempfile
from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any

import streamlit as st

from supabase_crud.config import ConfigurationError, Settings
from supabase_crud.helpers import human_size
from supabase_crud.service import FileService


st.set_page_config(
    page_title="Tideframe Archive",
    page_icon="◒",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom design system: coastal field archive
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Instrument+Sans:wdth,wght@75..100,400..700&display=swap');

    :root {
        --canvas: #F2F0E8;
        --surface: #FCFBF7;
        --surface-hover: #E9F0EC;
        --border: #CBD2CC;
        --border-focus: #5B827C;
        --text-strong: #15313A;
        --text-body: #405B61;
        --text-dim: #6F8180;
        --text-subtle: #93A19E;
        --ocean: #173F49;
        --sea-glass: #2E746D;
        --sea-glass-bg: #DCEAE4;
        --signal: #E36A45;
        --signal-bg: #FBE3D8;
        --sand: #D9B977;
        --sand-bg: #F4EACF;
    }

    /* Reset & Base */
    .stApp {
        background: var(--canvas) !important;
        color: var(--text-strong) !important;
        font-family: 'Instrument Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    [data-testid="stHeader"] {
        background: transparent !important;
    }

    .main .block-container {
        max-width: 1120px !important;
        padding: 2.25rem 1.5rem 6rem !important;
    }

    /* Top Bar */
    .top-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding-bottom: 1.5rem;
        border-bottom: 1px solid var(--border);
        margin-bottom: 1.75rem;
    }
    .brand-cluster {
        display: flex;
        align-items: center;
        gap: 0.8rem;
    }
    .brand-mark {
        width: 24px;
        height: 24px;
        background: var(--ocean);
        color: #F8F5EB;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-family: 'DM Mono', monospace;
        font-size: 0.58rem;
    }
    .brand-title {
        font-size: 1rem;
        font-weight: 650;
        color: var(--text-strong);
        letter-spacing: -0.015em;
    }
    .brand-meta {
        font-family: 'DM Mono', monospace;
        font-size: 0.63rem;
        color: var(--text-dim);
        padding-left: 0.8rem;
        border-left: 1px solid var(--border-focus);
    }

    .masthead {
        padding: 0.65rem 0 0.45rem;
        border-bottom: 0;
        margin-bottom: 0.2rem;
    }
    .masthead-kicker {
        font-family: 'DM Mono', monospace;
        color: var(--signal);
        font-size: 0.68rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.14em;
        margin-bottom: 0.8rem;
    }
    .masthead-title {
        color: var(--ocean);
        font-size: clamp(2rem, 4vw, 3rem);
        line-height: 0.9;
        letter-spacing: -0.065em;
        font-weight: 580;
        max-width: 720px;
    }
    .masthead-note {
        font-size: 0.92rem;
        line-height: 1.55;
        color: var(--text-dim);
        max-width: 300px;
        padding-left: 1rem;
        border-left: 2px solid var(--signal);
    }

    /* Upload Panel */
    .upload-container {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 1.25rem 1.5rem;
        margin-bottom: 2rem;
    }
    .upload-title-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.85rem;
    }
    .upload-heading {
        font-size: 0.82rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--text-body);
    }
    .upload-constraints {
        font-family: 'DM Mono', monospace;
        font-size: 0.68rem;
        color: var(--text-dim);
    }

    /* List & Table Styling */
    .list-wrapper {
        background: transparent;
        border: 0;
        border-radius: 0;
        overflow: hidden;
        box-shadow: none;
    }
    .list-header {
        display: grid;
        grid-template-columns: 5.2fr 0.8fr 1.8fr 0.8fr 0.35fr;
        padding: 0.55rem 0.4rem;
        background: transparent;
        border-top: 1px solid var(--border);
        border-bottom: 1px solid var(--border);
        font-family: 'DM Mono', monospace;
        font-size: 0.61rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--text-dim);
        align-items: center;
    }
    .file-row {
        display: grid;
        grid-template-columns: 5.2fr 0.8fr 1.8fr 0.8fr 0.35fr;
        padding: 0.95rem 1.25rem;
        border-bottom: 1px solid var(--border);
        align-items: center;
        background: var(--surface);
        transition: background 0.15s ease;
    }
    .file-row:last-child {
        border-bottom: none;
    }
    .file-row:hover {
        background: var(--surface-hover);
    }

    /* File identity */
    .file-name-block {
        display: flex;
        align-items: center;
        gap: 0.65rem;
        overflow: hidden;
    }
    .file-ext-icon {
        font-family: 'DM Mono', monospace;
        font-size: 0.62rem;
        font-weight: 500;
        width: 34px;
        height: auto;
        border-radius: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        text-transform: uppercase;
        flex-shrink: 0;
        border: 0;
        background: transparent;
        color: var(--text-dim);
    }
    .file-name-text {
        font-size: 0.85rem;
        font-weight: 600;
        color: var(--text-strong);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .file-desc-sub {
        font-size: 0.73rem;
        color: var(--text-dim);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        margin-top: 0.1rem;
    }

    .cell-data {
        font-size: 0.8rem;
        color: var(--text-body);
    }
    .cell-mono {
        font-family: 'DM Mono', monospace;
        font-size: 0.71rem;
        color: var(--text-dim);
    }

    /* Restrained text-only status treatment */
    .status-label {
        display: inline-block;
        font-family: 'DM Mono', monospace;
        font-size: 0.66rem;
        font-weight: 500;
        letter-spacing: 0.06em;
        text-transform: uppercase;
    }
    .status-active {
        color: var(--text-body);
    }
    .status-pending {
        color: #80662D;
    }
    .status-rejected {
        color: #A33D23;
    }

    /* Clean Streamlit Overrides */
    div[data-testid="stPopover"] button,
    div[data-testid="stPopover"] button[data-testid="stBaseButton-secondary"] {
        background: transparent !important;
        background-color: transparent !important;
        background-image: none !important;
        border: 0 !important;
        color: var(--ocean) !important;
        -webkit-text-fill-color: var(--ocean) !important;
        border-radius: 3px !important;
        font-family: 'DM Mono', monospace !important;
        font-size: 0.68rem !important;
        font-weight: 500 !important;
        padding: 0.22rem 0.35rem !important;
        box-shadow: none !important;
        min-height: 1.9rem !important;
    }
    div[data-testid="stPopover"] button:hover,
    div[data-testid="stPopover"] button[data-testid="stBaseButton-secondary"]:hover {
        background: rgba(21, 49, 58, 0.06) !important;
        background-color: rgba(21, 49, 58, 0.06) !important;
        border-color: transparent !important;
        color: var(--ocean) !important;
        -webkit-text-fill-color: var(--ocean) !important;
    }
    div[data-testid="stPopover"] button svg {
        color: var(--ocean) !important;
        fill: var(--ocean) !important;
    }

    .stButton > button {
        border-radius: 999px !important;
        font-weight: 500 !important;
        font-size: 0.8rem !important;
        border-color: var(--border-focus) !important;
        color: var(--ocean) !important;
        background: var(--surface) !important;
    }
    .stButton > button[kind="primary"] {
        background: var(--signal) !important;
        border-color: var(--signal) !important;
        color: white !important;
    }
    .stButton > button:hover {
        border-color: var(--signal) !important;
        color: var(--signal) !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: #C95132 !important;
        border-color: #C95132 !important;
        color: white !important;
    }

    .stTextInput input, .stTextArea textarea, .stSelectbox select {
        border-radius: 3px 12px 3px 3px !important;
        border: 1px solid var(--border-focus) !important;
        background: var(--surface) !important;
        font-size: 0.82rem !important;
        color: var(--text-strong) !important;
    }

    [data-testid="stFileUploader"] {
        padding: 0 !important;
    }
    [data-testid="stFileUploader"] section {
        border: 1px dashed var(--border-focus) !important;
        border-radius: 3px 18px 3px 3px !important;
        background: #F7F5ED !important;
        padding: 1.25rem 1rem !important;
    }
    [data-testid="stFileUploader"] section:hover {
        border-color: var(--signal) !important;
    }

    [data-testid="stExpander"] {
        border: 1px solid var(--border-focus) !important;
        border-radius: 2px 14px 2px 2px !important;
        background: rgba(252, 251, 247, 0.78) !important;
    }
    [data-testid="stExpander"] summary {
        font-family: 'DM Mono', monospace !important;
        font-size: 0.72rem !important;
        color: var(--ocean) !important;
    }

    .empty-notice {
        padding: 2rem 1.5rem;
        text-align: center;
        color: var(--text-dim);
        font-size: 0.85rem;
    }

    .index-count {
        font-family: 'DM Mono', monospace;
        font-size: 0.61rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--text-dim);
        padding: 0.15rem 0 0.1rem;
    }

    /* Single-viewport shell */
    html,
    body,
    [data-testid="stAppViewContainer"],
    .stApp,
    .main {
        height: 100vh !important;
        max-height: 100vh !important;
        overflow: hidden !important;
    }
    [data-testid="stHeader"] {
        height: 0 !important;
        min-height: 0 !important;
    }
    .main .block-container {
        height: 100vh !important;
        max-height: 100vh !important;
        padding: 0.7rem 1.5rem 0.45rem !important;
        overflow: hidden !important;
    }
    [data-testid="stVerticalBlock"] {
        gap: 0.35rem !important;
    }
    .masthead {
        padding: 0.45rem 0 0.25rem !important;
        margin: 0 !important;
    }
    .masthead-title {
        font-size: clamp(1.8rem, 4vh, 2.6rem) !important;
        line-height: 1 !important;
    }
    [data-testid="stExpander"] summary {
        min-height: 2.1rem !important;
        padding-top: 0.25rem !important;
        padding-bottom: 0.25rem !important;
    }
    .list-header {
        padding-top: 0.52rem !important;
        padding-bottom: 0.52rem !important;
    }
    .file-name-block {
        min-height: 2.15rem;
    }
    .file-desc-sub {
        margin-top: 0 !important;
    }
    div[data-testid="stTextInputRootElement"],
    div[data-testid="stSelectbox"] > div > div {
        min-height: 2.15rem !important;
    }

    @media (max-width: 780px) {
        .masthead { grid-template-columns: 1fr; }
        .masthead-note { display: none; }
        .brand-meta { display: none; }
        .main .block-container { padding-left: 0.65rem !important; padding-right: 0.65rem !important; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Final layout layer: centered, calm, and deliberately sparse.
st.markdown(
    """
    <style>
    :root {
        --canvas: #F5F3ED;
        --surface: #FCFBF7;
        --border: #D6D8D2;
        --text-strong: #17363D;
        --text-body: #52686C;
        --text-dim: #829092;
        --ocean: #173F49;
        --signal: #D96845;
    }

    .stApp { background: var(--canvas) !important; }

    [data-testid="stMainBlockContainer"],
    .main .block-container {
        width: calc(100% - 3rem) !important;
        max-width: 1180px !important;
        margin: 0 auto !important;
        padding: 1.65rem 0 0.75rem !important;
    }

    [data-testid="stVerticalBlock"] { gap: 0.7rem !important; }

    .brand-cluster { gap: 0.65rem; }
    .brand-mark {
        width: 25px;
        height: 25px;
        font-size: 0.57rem;
        background: var(--ocean);
    }
    .brand-title { font-size: 0.92rem; font-weight: 650; }

    .masthead {
        padding: 1.15rem 0 0.15rem !important;
        margin: 0 !important;
    }
    .masthead-title {
        font-size: 2.5rem !important;
        line-height: 1 !important;
        letter-spacing: -0.055em !important;
        font-weight: 580 !important;
    }

    [data-testid="stTextInputRootElement"] {
        min-height: 2.55rem !important;
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        box-shadow: 0 1px 0 rgba(23, 63, 73, 0.02) !important;
    }
    [data-testid="stTextInputRootElement"] input {
        padding-left: 0.85rem !important;
        font-size: 0.8rem !important;
    }

    div[data-testid="stPopover"] button,
    div[data-testid="stPopover"] button[data-testid="stBaseButton-secondary"] {
        min-height: 2rem !important;
        background: transparent !important;
        border: 0 !important;
        border-radius: 6px !important;
        color: var(--text-body) !important;
        -webkit-text-fill-color: var(--text-body) !important;
        box-shadow: none !important;
        padding: 0.2rem 0.35rem !important;
    }
    div[data-testid="stPopover"] button svg { display: none !important; }

    .st-key-new_file_control div[data-testid="stPopover"] button,
    .st-key-new_file_control div[data-testid="stPopover"] button[data-testid="stBaseButton-secondary"] {
        width: 100% !important;
        min-height: 2.55rem !important;
        background: var(--ocean) !important;
        border: 1px solid var(--ocean) !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        font-family: 'Instrument Sans', sans-serif !important;
        font-size: 0.78rem !important;
        font-weight: 600 !important;
    }
    .st-key-new_file_control div[data-testid="stPopover"] button:hover {
        background: #24545D !important;
        border-color: #24545D !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }

    .index-count {
        padding: 0.3rem 0 0.15rem !important;
        font-size: 0.58rem !important;
        color: var(--text-dim) !important;
    }

    .list-wrapper { overflow: visible; }
    .list-header {
        grid-template-columns: 5.2fr 0.8fr 1.8fr 0.8fr 0.35fr;
        padding: 0.58rem 0.65rem !important;
        border-top: 1px solid var(--border) !important;
        border-bottom: 1px solid var(--border) !important;
        background: rgba(255, 255, 255, 0.28) !important;
        color: var(--text-dim) !important;
        font-size: 0.57rem !important;
    }

    .file-name-block { padding-left: 0.55rem; min-height: 2.55rem; }
    .file-ext-icon {
        width: 31px;
        color: var(--text-dim);
        font-size: 0.55rem;
    }
    .file-name-text { font-size: 0.8rem; font-weight: 600; }
    .file-desc-sub { font-size: 0.67rem; }
    .cell-mono { font-size: 0.64rem; }
    .status-label { font-size: 0.59rem; }

    @media (max-width: 780px) {
        [data-testid="stMainBlockContainer"], .main .block-container {
            width: calc(100% - 1.25rem) !important;
        }
        .masthead-title { font-size: 2rem !important; }
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


def render_upload_popover(service: FileService) -> None:
    """Render the complete create flow behind one quiet control."""
    with st.popover("New file"):
        uploaded_file = st.file_uploader(
            "File",
            type=["pdf", "png", "jpg", "jpeg", "webp", "gif", "txt", "csv", "json", "docx"],
            help="PDF, images, plaintext, CSV, or JSON up to 10 MB",
        )
        file_note = st.text_area("Field note", placeholder="Optional context", height=72)

        if uploaded_file is not None and st.button("Archive", type="primary", use_container_width=True):
            if uploaded_file.size > service.settings.max_file_size_bytes:
                st.error(f"File exceeds {human_size(service.settings.max_file_size_bytes)}.")
                return

            temp_path = upload_to_temp(uploaded_file)
            try:
                with st.spinner("Validating…"):
                    service.create_file(str(temp_path), description=file_note.strip() or None)
                st.toast("Archived.", icon="✓")
                st.rerun()
            except Exception as error:
                st.error(f"Upload rejected: {error}")
            finally:
                temp_path.unlink(missing_ok=True)


def main() -> None:
    st.markdown(
        """
        <div class="brand-cluster">
            <div class="brand-mark">TF</div>
            <span class="brand-title">Tideframe</span>
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

    st.markdown(
        """
        <section class="masthead">
            <div class="masthead-title">Files</div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    records = service.list_files()

    search_col, _, add_col = st.columns([4, 3, 1.15], vertical_alignment="center")
    with search_col:
        search = st.text_input(
            "Search",
            placeholder="Search the archive",
            label_visibility="collapsed",
        ).strip().lower()
    with add_col:
        with st.container(key="new_file_control"):
            render_upload_popover(service)

    filtered = sorted(records, key=lambda item: str(item.get("created_at") or ""), reverse=True)
    if search:
        filtered = [
            r for r in filtered
            if search in f"{r.get('original_name', '')} {r.get('description', '')} {r.get('content_type', '')}".lower()
        ]

    if not filtered:
        st.markdown(
            """
            <div class="list-wrapper">
                <div class="empty-notice">No records match the current filter.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # Keep the shell within one viewport by paging instead of growing vertically.
    page_size = 5
    page_count = max(1, (len(filtered) + page_size - 1) // page_size)
    filter_fingerprint = search
    if st.session_state.get("archive_filter") != filter_fingerprint:
        st.session_state.archive_filter = filter_fingerprint
        st.session_state.archive_page = 0

    current_page = min(int(st.session_state.get("archive_page", 0)), page_count - 1)
    page_start = current_page * page_size
    page_records = filtered[page_start : page_start + page_size]
    page_end = page_start + len(page_records)

    if page_count == 1:
        st.markdown(
            f"""
            <div class="index-count">
                {len(filtered):02d} objects
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        index_col, previous_col, next_col = st.columns([10, 0.5, 0.5], vertical_alignment="center")
        with index_col:
            st.markdown(
                f'<div class="index-count">{page_start + 1:02d}–{page_end:02d} / {len(filtered):02d}</div>',
                unsafe_allow_html=True,
            )
        with previous_col:
            if st.button("←", key="archive_previous", disabled=current_page == 0, use_container_width=True):
                st.session_state.archive_page = current_page - 1
                st.rerun()
        with next_col:
            if st.button("→", key="archive_next", disabled=current_page >= page_count - 1, use_container_width=True):
                st.session_state.archive_page = current_page + 1
                st.rerun()

    # Table Header
    st.markdown(
        """
        <div class="list-wrapper">
            <div class="list-header">
                <div>Document</div>
                <div>Size</div>
                <div>Added</div>
                <div>Status</div>
                <div></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Table Rows
    for r in page_records:
        rec_id = r["id"]
        orig_name = r.get("original_name") or "unnamed"
        ext = Path(orig_name).suffix.lstrip(".") or "txt"
        size_str = human_size(r.get("size_bytes"))
        date_str = format_iso(r.get("created_at"))
        status_val = (r.get("status") or "pending").lower()
        desc = r.get("description")

        if status_val == "active":
            status_html = '<span class="status-label status-active">Active</span>'
        elif status_val == "rejected":
            status_html = '<span class="status-label status-rejected">Rejected</span>'
        else:
            status_html = '<span class="status-label status-pending">Pending</span>'

        desc_html = f'<div class="file-desc-sub">{escape(desc)}</div>' if desc else '<div class="file-desc-sub" style="color: var(--text-subtle);">No field note</div>'

        cols = st.columns([5.2, 0.8, 1.8, 0.8, 0.35])
        with cols[0]:
            st.markdown(
                f"""
                <div class="file-name-block">
                    <div class="file-ext-icon">{ext[:4]}</div>
                    <div style="overflow: hidden;">
                        <div class="file-name-text">{escape(orig_name)}</div>
                        {desc_html}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with cols[1]:
            st.markdown(f"<div style='padding-top: 0.45rem;' class='cell-mono'>{size_str}</div>", unsafe_allow_html=True)
        with cols[2]:
            st.markdown(f"<div style='padding-top: 0.45rem;' class='cell-mono'>{date_str}</div>", unsafe_allow_html=True)
        with cols[3]:
            st.markdown(f"<div style='padding-top: 0.45rem;'>{status_html}</div>", unsafe_allow_html=True)
        with cols[4]:
            action_popover = st.popover("···", use_container_width=True)
            with action_popover:
                st.markdown(f"**{escape(orig_name)}**")
                try:
                    signed_url = service.create_signed_url(rec_id)
                    st.link_button("Download object", signed_url, use_container_width=True)
                except Exception:
                    st.caption("Download link unavailable")

                st.divider()

                with st.form(f"note_form_{rec_id}"):
                    st.caption("Edit label and field note")
                    new_n = st.text_input("Name", value=orig_name, key=f"nm_{rec_id}")
                    new_d = st.text_area("Note", value=desc or "", height=60, key=f"nt_{rec_id}")
                    if st.form_submit_button("Save Updates", use_container_width=True):
                        try:
                            service.update_metadata(rec_id, description=new_d.strip() or None, original_name=new_n.strip() or None)
                            st.toast("Record updated.", icon="✓")
                            st.rerun()
                        except Exception as err:
                            st.error(str(err))

                st.divider()

                with st.expander("Replace payload"):
                    rf = st.file_uploader("Candidate file", type=["pdf", "png", "jpg", "jpeg", "webp", "gif", "txt", "csv", "json", "docx"], key=f"rf_{rec_id}")
                    if st.button("Swap & Revalidate", key=f"rbtn_{rec_id}", use_container_width=True):
                        if rf:
                            tp = upload_to_temp(rf)
                            try:
                                service.replace_file(rec_id, str(tp))
                                st.toast("Replacement validated.", icon="✓")
                                st.rerun()
                            except Exception as err:
                                st.error(str(err))
                            finally:
                                tp.unlink(missing_ok=True)

                st.divider()

                if st.button("Delete Permanently", key=f"del_{rec_id}", type="primary", use_container_width=True):
                    try:
                        service.delete_file(rec_id)
                        st.toast("Object removed.")
                        st.rerun()
                    except Exception as err:
                        st.error(str(err))

        st.markdown("<div style='height: 1px; background: var(--border); margin: 0.15rem 0;'></div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
