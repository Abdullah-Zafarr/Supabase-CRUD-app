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
        background:
            radial-gradient(circle at 88% 8%, rgba(46, 116, 109, 0.10), transparent 23rem),
            linear-gradient(rgba(21, 49, 58, 0.025) 1px, transparent 1px),
            linear-gradient(90deg, rgba(21, 49, 58, 0.025) 1px, transparent 1px),
            var(--canvas) !important;
        background-size: auto, 32px 32px, 32px 32px, auto !important;
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
        width: 31px;
        height: 31px;
        background: var(--ocean);
        color: #F8F5EB;
        border-radius: 50% 50% 50% 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-family: 'DM Mono', monospace;
        font-size: 0.72rem;
        transform: rotate(-8deg);
        box-shadow: 3px 3px 0 var(--sand);
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
        display: grid;
        grid-template-columns: minmax(0, 2.2fr) minmax(220px, 1fr);
        gap: 2rem;
        align-items: end;
        padding: 3.4rem 0 2.4rem;
        border-bottom: 1px solid var(--border-focus);
        margin-bottom: 1.35rem;
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
        font-size: clamp(2.6rem, 6vw, 5.2rem);
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
        background: var(--surface);
        border: 1px solid var(--border-focus);
        border-radius: 2px 14px 2px 2px;
        overflow: hidden;
        box-shadow: 5px 5px 0 rgba(23, 63, 73, 0.07);
    }
    .list-header {
        display: grid;
        grid-template-columns: 3.2fr 0.9fr 0.8fr 1.3fr 1.6fr 1fr 0.7fr;
        padding: 0.75rem 1.25rem;
        background: var(--ocean);
        border-bottom: 1px solid var(--border);
        font-family: 'DM Mono', monospace;
        font-size: 0.61rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #DDE8E4;
        align-items: center;
    }
    .file-row {
        display: grid;
        grid-template-columns: 3.2fr 0.9fr 0.8fr 1.3fr 1.6fr 1fr 0.7fr;
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
        height: 28px;
        border-radius: 50% 50% 50% 4px;
        display: flex;
        align-items: center;
        justify-content: center;
        text-transform: uppercase;
        flex-shrink: 0;
        border: 1px solid var(--border);
        background: var(--sea-glass-bg);
        color: var(--sea-glass);
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
        background: var(--surface) !important;
        background-color: var(--surface) !important;
        background-image: none !important;
        border: 1px solid var(--border-focus) !important;
        color: var(--ocean) !important;
        -webkit-text-fill-color: var(--ocean) !important;
        border-radius: 3px 10px 3px 3px !important;
        font-family: 'DM Mono', monospace !important;
        font-size: 0.68rem !important;
        font-weight: 500 !important;
        padding: 0.32rem 0.65rem !important;
        box-shadow: none !important;
        min-height: 2.1rem !important;
    }
    div[data-testid="stPopover"] button:hover,
    div[data-testid="stPopover"] button[data-testid="stBaseButton-secondary"]:hover {
        background: #E8E3D8 !important;
        background-color: #E8E3D8 !important;
        border-color: var(--ocean) !important;
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
        padding: 3.5rem 1.5rem;
        text-align: center;
        color: var(--text-dim);
        font-size: 0.85rem;
    }

    @media (max-width: 780px) {
        .masthead { grid-template-columns: 1fr; gap: 1.25rem; padding-top: 2.5rem; }
        .masthead-note { max-width: none; }
        .brand-meta { display: none; }
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


def main() -> None:
    # Top Bar
    top_c1, top_c2 = st.columns([5, 1.2])
    with top_c1:
        st.markdown(
            """
            <div class="brand-cluster">
                <div class="brand-mark">TF</div>
                <span class="brand-title">Tideframe</span>
                <span class="brand-meta">private object archive · documents</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with top_c2:
        if st.button("Refresh index", use_container_width=True):
            st.rerun()

    try:
        service = get_service()
    except ConfigurationError as exc:
        st.error(str(exc))
        st.info("Check .env credentials.")
        st.stop()

    st.markdown(
        """
        <section class="masthead">
            <div>
                <div class="masthead-kicker">Supabase · field storage</div>
                <div class="masthead-title">Keep every signal.</div>
            </div>
            <div class="masthead-note">
                A small, private registry for source files, evidence, and the notes
                that make them useful later.
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    # Ingest Accordion / Uploader
    with st.expander("+ Add an object to the archive", expanded=False):
        col_up1, col_up2 = st.columns([3, 2])
        with col_up1:
            uploaded_file = st.file_uploader(
                "Upload file",
                type=["pdf", "png", "jpg", "jpeg", "webp", "gif", "txt", "csv", "json", "docx"],
                help="Allowed: PDF, Images, Plaintext, CSV, JSON (up to 10 MB)",
            )
        with col_up2:
            uploader_name = st.text_input("Uploader tag", value=service.settings.app_user)
            file_note = st.text_area("Context note (optional)", placeholder="Add context or notes...", height=72)

        if uploaded_file is not None:
            if st.button("Validate & archive", type="primary"):
                if uploaded_file.size > service.settings.max_file_size_bytes:
                    st.error(f"File exceeds {human_size(service.settings.max_file_size_bytes)}.")
                else:
                    t_path = upload_to_temp(uploaded_file)
                    try:
                        with st.spinner("Uploading and validating with Edge Function..."):
                            service.create_file(str(t_path), description=file_note.strip() or None)
                        st.toast("File validated and archived.", icon="✓")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Upload rejected: {e}")
                    finally:
                        t_path.unlink(missing_ok=True)

    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)

    # Data & Filters
    records = service.list_files()

    # Search & Filter bar
    f1, f2, f3 = st.columns([4, 1.8, 1.8])
    with f1:
        search = st.text_input("Search", placeholder="Search filename, note, type...", label_visibility="collapsed").strip().lower()
    with f2:
        filter_status = st.selectbox("Status", ["All statuses", "active", "pending", "rejected"], label_visibility="collapsed")
    with f3:
        sort_order = st.selectbox("Sort", ["Newest first", "Oldest first", "Largest size", "Name A-Z"], label_visibility="collapsed")

    filtered = records
    if search:
        filtered = [
            r for r in filtered
            if search in f"{r.get('original_name', '')} {r.get('description', '')} {r.get('content_type', '')}".lower()
        ]
    if filter_status != "All statuses":
        filtered = [r for r in filtered if (r.get("status") or "").lower() == filter_status]

    if sort_order == "Newest first":
        filtered = sorted(filtered, key=lambda x: str(x.get("created_at") or ""), reverse=True)
    elif sort_order == "Oldest first":
        filtered = sorted(filtered, key=lambda x: str(x.get("created_at") or ""))
    elif sort_order == "Largest size":
        filtered = sorted(filtered, key=lambda x: int(x.get("size_bytes") or 0), reverse=True)
    elif sort_order == "Name A-Z":
        filtered = sorted(filtered, key=lambda x: str(x.get("original_name") or "").lower())

    st.markdown(
        f"""
        <div style="display: flex; justify-content: space-between; align-items: center; margin: 1rem 0 0.5rem 0.25rem;">
            <div style="font-family: 'DM Mono', monospace; font-size: 0.66rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.1em; color: var(--sea-glass);">
                Objects in view / {len(filtered):02d}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

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

    # Table Header
    st.markdown(
        """
        <div class="list-wrapper">
            <div class="list-header">
                <div>Document</div>
                <div>Size</div>
                <div>Format</div>
                <div>Uploader</div>
                <div>Timestamp</div>
                <div>Status</div>
                <div style="text-align: right;">Action</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Table Rows
    for r in filtered:
        rec_id = r["id"]
        orig_name = r.get("original_name") or "unnamed"
        ext = Path(orig_name).suffix.lstrip(".") or "txt"
        size_str = human_size(r.get("size_bytes"))
        uploader_str = r.get("uploaded_by") or "service-app"
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

        cols = st.columns([3.2, 0.9, 0.8, 1.3, 1.6, 1.0, 0.7])
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
            st.markdown(f"<div style='padding-top: 0.45rem;' class='cell-mono'>.{ext.lower()}</div>", unsafe_allow_html=True)
        with cols[3]:
            st.markdown(f"<div style='padding-top: 0.45rem;' class='cell-data'>{escape(uploader_str)}</div>", unsafe_allow_html=True)
        with cols[4]:
            st.markdown(f"<div style='padding-top: 0.45rem;' class='cell-mono'>{date_str}</div>", unsafe_allow_html=True)
        with cols[5]:
            st.markdown(f"<div style='padding-top: 0.45rem;'>{status_html}</div>", unsafe_allow_html=True)
        with cols[6]:
            action_popover = st.popover("Details", use_container_width=True)
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
