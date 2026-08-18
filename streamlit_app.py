"""The Quiet Index: a minimalist Streamlit front end for the CRUD service."""

from __future__ import annotations

import tempfile
from html import escape
from pathlib import Path

import streamlit as st

from supabase_crud.config import ConfigurationError, Settings
from supabase_crud.helpers import human_size
from supabase_crud.service import FileService


st.set_page_config(
    page_title="The Quiet Index",
    page_icon="⌁",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700&display=swap');

    :root {
        --ink: #242522;
        --muted: #77766f;
        --paper: #f4f1e9;
        --card: #fbfaf6;
        --line: #dad6cb;
        --moss: #61715c;
        --clay: #a85e46;
    }

    .stApp { background: var(--paper); color: var(--ink); }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stSidebar"] { background: #ebe7dc; border-right: 1px solid var(--line); }
    [data-testid="stSidebar"] > div:first-child { padding-top: 2rem; }
    .block-container { max-width: 1180px; padding-top: 3rem; padding-bottom: 4rem; }
    h1, h2, h3, p, label, button { font-family: 'Manrope', sans-serif; }
    h1 { letter-spacing: -0.055em; font-size: clamp(2.6rem, 6vw, 5.5rem); line-height: .95; margin-bottom: .8rem; }
    h2 { letter-spacing: -0.04em; font-size: 1.55rem; }
    h3 { letter-spacing: -0.025em; }
    .eyebrow, .mono, [data-testid="stMetricLabel"], [data-testid="stMetricValue"] {
        font-family: 'DM Mono', monospace !important;
    }
    .eyebrow { color: var(--clay); font-size: .72rem; letter-spacing: .16em; text-transform: uppercase; }
    .lede { color: var(--muted); font-size: 1.06rem; max-width: 620px; line-height: 1.6; }
    .rule { height: 1px; background: var(--line); margin: 2.2rem 0 1.4rem; }
    .record-card {
        background: var(--card); border: 1px solid var(--line); border-radius: 3px;
        padding: 1.1rem 1.25rem .6rem; margin: .65rem 0 1rem;
        box-shadow: 0 5px 20px rgba(47, 44, 34, .035);
    }
    .record-name { font-size: 1.1rem; font-weight: 700; letter-spacing: -.02em; overflow-wrap: anywhere; }
    .record-description { color: var(--muted); font-size: .88rem; margin-top: .35rem; min-height: 1.25rem; }
    .record-meta { color: var(--muted); font-family: 'DM Mono', monospace; font-size: .7rem; line-height: 1.7; }
    .status {
        border-radius: 99px; display: inline-block; font-family: 'DM Mono', monospace;
        font-size: .64rem; letter-spacing: .08em; padding: .32rem .55rem; text-transform: uppercase;
    }
    .status-active { background: #e2eadc; color: #4c6349; }
    .status-pending { background: #f4ead0; color: #8b6a2e; }
    .status-rejected { background: #f0ddd7; color: #914e3c; }
    .empty {
        border: 1px dashed #c5c0b4; color: var(--muted); padding: 3.5rem 2rem;
        text-align: center; margin-top: 1rem;
    }
    div[data-testid="stMetric"] { background: transparent; border-left: 1px solid var(--line); padding-left: 1rem; }
    div[data-testid="stMetricValue"] { font-size: 1.35rem; }
    .stButton button, .stDownloadButton button { border-radius: 2px; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def get_service() -> FileService:
    return FileService(Settings.from_env())


def format_date(value: object) -> str:
    text = str(value or "")
    return text.replace("T", " ").replace("+00:00", " UTC")[:19]


def upload_to_temp(uploaded_file) -> Path:
    suffix = Path(uploaded_file.name).suffix
    handle = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        handle.write(uploaded_file.getvalue())
        return Path(handle.name)
    finally:
        handle.close()


def render_sidebar(service: FileService) -> None:
    with st.sidebar:
        st.markdown('<div class="eyebrow">New specimen</div>', unsafe_allow_html=True)
        st.markdown("### Add to the index")
        st.caption("A document enters the archive only after the server-side validator signs off.")
        with st.form("new_upload", clear_on_submit=True):
            uploaded = st.file_uploader(
                "Choose a source file",
                type=["pdf", "jpg", "jpeg", "png", "gif", "webp", "txt", "csv", "json"],
                label_visibility="collapsed",
            )
            description = st.text_area(
                "Context note",
                placeholder="Why does this belong in the archive?",
                height=90,
            )
            submitted = st.form_submit_button("Archive file", use_container_width=True)
        if submitted:
            if uploaded is None:
                st.warning("Choose a file first.")
                return
            if uploaded.size > service.settings.max_file_size_bytes:
                st.error(
                    f"That file is {human_size(uploaded.size)}; limit is "
                    f"{human_size(service.settings.max_file_size_bytes)}."
                )
                return
            temp_path = upload_to_temp(uploaded)
            try:
                with st.spinner("Indexing and validating…"):
                    service.create_file(str(temp_path), description.strip() or None)
                st.success("Archived and validated.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
            finally:
                temp_path.unlink(missing_ok=True)

        st.markdown('<div class="rule"></div>', unsafe_allow_html=True)
        st.markdown('<div class="eyebrow">Collection note</div>', unsafe_allow_html=True)
        st.caption(
            "The Quiet Index is intentionally private. Files stay in Supabase Storage; "
            "this local interface requests bytes only when you download them."
        )


def render_record(service: FileService, record: dict) -> None:
    record_id = record["id"]
    status = record.get("status", "pending")
    status_class = status if status in {"active", "pending", "rejected"} else "pending"
    description = escape(str(record.get("description") or "No context note yet."))
    original_name = escape(str(record["original_name"]))
    size = human_size(record.get("size_bytes"))
    content_type = record.get("content_type") or "unknown type"
    checksum = (record.get("checksum_sha256") or "not generated")[:16]

    st.markdown('<div class="record-card">', unsafe_allow_html=True)
    top_left, top_right = st.columns([5, 1])
    with top_left:
        st.markdown(f'<div class="record-name">{original_name}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="record-description">{description}</div>', unsafe_allow_html=True)
    with top_right:
        st.markdown(
            f'<span class="status status-{status_class}">{status}</span>',
            unsafe_allow_html=True,
        )
    st.markdown(
        f'<div class="record-meta">{content_type} &nbsp;·&nbsp; {size} &nbsp;·&nbsp; '
        f'added {format_date(record.get("created_at"))} &nbsp;·&nbsp; sha {checksum}</div>',
        unsafe_allow_html=True,
    )

    actions = st.columns([1.1, 1.1, 1.1, 1.1, 3.6])
    with actions[0]:
        try:
            signed_url = service.create_signed_url(record_id)
            st.link_button(
                "Download",
                signed_url,
                use_container_width=True,
            )
        except Exception:
            st.caption("File unavailable")
    with actions[1]:
        edit_open = st.popover("Edit note", use_container_width=True)
        with edit_open:
            with st.form(f"edit-{record_id}"):
                new_description = st.text_area(
                    "Context note",
                    value=record.get("description") or "",
                    key=f"description-{record_id}",
                )
                save_edit = st.form_submit_button("Save", use_container_width=True)
            if save_edit:
                try:
                    service.update_metadata(record_id, description=new_description.strip())
                    st.success("Saved")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
    with actions[2]:
        replace_open = st.popover("Replace", use_container_width=True)
        with replace_open:
            replacement = st.file_uploader(
                "New version",
                type=["pdf", "jpg", "jpeg", "png", "gif", "webp", "txt", "csv", "json"],
                key=f"replace-file-{record_id}",
            )
            replace_description = st.text_input(
                "Context note",
                value=record.get("description") or "",
                key=f"replace-description-{record_id}",
            )
            replace_submit = st.button("Validate replacement", key=f"replace-submit-{record_id}")
            if replace_submit:
                if replacement is None:
                    st.warning("Choose a replacement file first.")
                elif replacement.size > service.settings.max_file_size_bytes:
                    st.error("Replacement exceeds the configured size limit.")
                else:
                    temp_path = upload_to_temp(replacement)
                    try:
                        with st.spinner("Validating replacement…"):
                            service.replace_file(
                                record_id,
                                str(temp_path),
                                description=replace_description.strip() or None,
                            )
                        st.success("Version replaced.")
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))
                    finally:
                        temp_path.unlink(missing_ok=True)
    with actions[3]:
        if st.button("Remove", key=f"delete-{record_id}", use_container_width=True):
            try:
                service.delete_file(record_id)
                st.toast("Removed from the index.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))
    st.markdown("</div>", unsafe_allow_html=True)


def main() -> None:
    st.markdown('<div class="eyebrow">Private field archive · v1</div>', unsafe_allow_html=True)
    st.title("The Quiet Index")
    st.markdown(
        '<p class="lede">A calm, searchable shelf for the source material behind your thinking. '
        "Upload a document, leave a trace of context, and let Supabase verify the object before it settles in.</p>",
        unsafe_allow_html=True,
    )

    try:
        service = get_service()
    except ConfigurationError as exc:
        st.error(str(exc))
        st.info("Copy .env.example to .env, add your Supabase URL, server-side key, and Edge Function secret, then reload.")
        st.stop()

    render_sidebar(service)
    records = service.list_files()
    active = [row for row in records if row.get("status") == "active"]
    total_bytes = sum(row.get("size_bytes") or 0 for row in records)

    metric_cols = st.columns(4)
    metric_cols[0].metric("Indexed", len(records))
    metric_cols[1].metric("Validated", len(active))
    metric_cols[2].metric("Pending", len(records) - len(active))
    metric_cols[3].metric("Footprint", human_size(total_bytes))

    st.markdown('<div class="rule"></div>', unsafe_allow_html=True)
    controls = st.columns([3.5, 1.3])
    with controls[0]:
        search = st.text_input(
            "Search the index",
            placeholder="filename, context, or MIME type",
            label_visibility="collapsed",
        ).strip().lower()
    with controls[1]:
        filter_status = st.selectbox(
            "Status",
            ["All statuses", "active", "pending", "rejected"],
            label_visibility="collapsed",
        )

    filtered = records
    if search:
        filtered = [
            row
            for row in filtered
            if search in " ".join(
                str(row.get(field) or "")
                for field in ("original_name", "description", "content_type")
            ).lower()
        ]
    if filter_status != "All statuses":
        filtered = [row for row in filtered if row.get("status") == filter_status]

    st.markdown(
        f'<div class="eyebrow">{len(filtered):02d} records on shelf</div>',
        unsafe_allow_html=True,
    )
    if not filtered:
        st.markdown(
            '<div class="empty"><strong>The shelf is quiet.</strong><br>'
            'Upload a source from the sidebar to begin a new trail.</div>',
            unsafe_allow_html=True,
        )
    else:
        for record in filtered:
            render_record(service, record)


if __name__ == "__main__":
    main()
