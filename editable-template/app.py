"""
Draftly — Editable document templates (Streamlit)
=================================================

One engine, many documents.

Idea
----
A legal "template" here is NOT a Word file with holes in it. It is:

    schema  ->  the fixed definition of a document (labels, field types, table columns)
    data    ->  the values (from OCR extraction; the lawyer corrects them)
    render  ->  Streamlit widgets, pre-filled from data, so the lawyer edits in the browser
    export  ->  the corrected data + schema -> a Word (.docx) file

Because the document is stored as structured `data` (a plain dict), the lawyer
can only edit *values in fixed slots* — they cannot break the layout or drop a
required field. The corrected values stay structured, so downstream steps
(deed schedule, title report) reuse them directly, and each field can later
carry a pointer back to its source page for traceability.

Add a new document = add a new schema. Nothing else changes.

Run:  streamlit run app.py
Deps: streamlit, python-docx, pandas
"""

from __future__ import annotations
import io
import copy
import datetime as dt

import pandas as pd
import streamlit as st
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT


# ---------------------------------------------------------------------------
# 1. SCHEMAS  — the definition of each document.
#    label_si (Sinhala) is optional; confirm every field against a real sample.
#    Field types: "text", "number", "date", "textarea", "table".
# ---------------------------------------------------------------------------

ASSESSMENT_EXTRACT = {
    "id": "assessment_extract",
    "title_en": "Extract of the Assessment Register",
    "title_si": "තක්සේරු ලේඛනයේ පිටපත (පත්තිරු)",
    "sections": [
        {
            "name": "Issuing authority",
            "fields": [
                {"key": "local_authority", "label_en": "Local Authority",
                 "label_si": "පළාත් පාලන ආයතනය", "type": "text"},
                {"key": "extract_no", "label_en": "Extract / Reference No.",
                 "label_si": "පිටපත් අංකය", "type": "text"},
                {"key": "date_of_issue", "label_en": "Date of Issue",
                 "label_si": "නිකුත් කළ දිනය", "type": "date"},
            ],
        },
        {
            "name": "Property identification",
            "fields": [
                {"key": "assessment_no", "label_en": "Assessment No.",
                 "label_si": "තක්සේරු අංකය", "type": "text"},
                {"key": "ward", "label_en": "Ward No. / Name",
                 "label_si": "වට්ටම් අංකය / නම", "type": "text"},
                {"key": "street", "label_en": "Street / Road / Lane",
                 "label_si": "වීදිය / පාර", "type": "text"},
                {"key": "premises", "label_en": "Description of Premises",
                 "label_si": "පරිශ්‍රයේ විස්තරය", "type": "text"},
                {"key": "extent", "label_en": "Extent",
                 "label_si": "ප්‍රමාණය", "type": "text"},
            ],
        },
        {
            "name": "Parties",
            "fields": [
                {"key": "owner", "label_en": "Owner",
                 "label_si": "හිමිකරු", "type": "text"},
                {"key": "occupier", "label_en": "Occupier",
                 "label_si": "පදිංචිකරු", "type": "text"},
            ],
        },
        {
            "name": "Valuation",
            "fields": [
                {"key": "annual_value", "label_en": "Annual Value (Rs.)",
                 "label_si": "වාර්ෂික වටිනාකම (රු.)", "type": "number"},
                {"key": "rate_percent", "label_en": "Rate (%)",
                 "label_si": "අනුපාතය (%)", "type": "number"},
                {"key": "remarks", "label_en": "Remarks",
                 "label_si": "සටහන්", "type": "textarea"},
            ],
        },
    ],
}

RATES_AND_TAXES = {
    "id": "rates_and_taxes",
    "title_en": "Statement of Rates and Taxes",
    "title_si": "වාරිපනම් හා බදු පිළිබඳ ප්‍රකාශය (වාරිපනම්)",
    "sections": [
        {
            "name": "Property & owner",
            "fields": [
                {"key": "local_authority", "label_en": "Local Authority",
                 "label_si": "පළාත් පාලන ආයතනය", "type": "text"},
                {"key": "assessment_no", "label_en": "Assessment No.",
                 "label_si": "තක්සේරු අංකය", "type": "text"},
                {"key": "owner", "label_en": "Owner",
                 "label_si": "හිමිකරු", "type": "text"},
                {"key": "property", "label_en": "Property / Address",
                 "label_si": "දේපල / ලිපිනය", "type": "text"},
                {"key": "annual_value", "label_en": "Annual Value (Rs.)",
                 "label_si": "වාර්ෂික වටිනාකම (රු.)", "type": "number"},
                {"key": "rate_percent", "label_en": "Rate (%)",
                 "label_si": "අනුපාතය (%)", "type": "number"},
            ],
        },
        {
            "name": "Payment history",
            "fields": [
                {
                    "key": "payments",
                    "label_en": "Rates paid by period",
                    "type": "table",
                    "columns": [
                        {"key": "year", "label": "Year", "type": "number"},
                        {"key": "quarter", "label": "Quarter", "type": "text"},
                        {"key": "amount_due", "label": "Amount Due (Rs.)", "type": "number"},
                        {"key": "amount_paid", "label": "Amount Paid (Rs.)", "type": "number"},
                        {"key": "receipt_no", "label": "Receipt No.", "type": "text"},
                        {"key": "date_paid", "label": "Date Paid", "type": "text"},
                        {"key": "arrears", "label": "Arrears (Rs.)", "type": "number"},
                    ],
                },
            ],
        },
        {
            "name": "Certification",
            "fields": [
                {"key": "total_arrears", "label_en": "Total Arrears (Rs.)",
                 "label_si": "මුළු හිඟ මුදල (රු.)", "type": "number"},
                {"key": "certified_by", "label_en": "Certified By (Officer)",
                 "label_si": "සහතික කළ නිලධාරී", "type": "text"},
                {"key": "certified_date", "label_en": "Certified Date",
                 "label_si": "සහතික කළ දිනය", "type": "date"},
            ],
        },
    ],
}

SCHEMAS = {s["id"]: s for s in (ASSESSMENT_EXTRACT, RATES_AND_TAXES)}


# ---------------------------------------------------------------------------
# 2. SAMPLE DATA — in the real app this comes from the OCR / extraction stage.
#    Keys must match the schema field keys. Missing keys just render empty.
# ---------------------------------------------------------------------------

SAMPLE_DATA = {
    "assessment_extract": {
        "local_authority": "Colombo Municipal Council",
        "extract_no": "AE/2024/01187",
        "date_of_issue": "2024-11-03",
        "assessment_no": "142/7",
        "ward": "Ward 21 – Kollupitiya",
        "street": "Galle Road",
        "premises": "Two-storey dwelling house",
        "extent": "12.5 perches",
        "owner": "K. A. Perera",
        "occupier": "K. A. Perera",
        "annual_value": 480000,
        "rate_percent": 8.0,
        "remarks": "",
    },
    "rates_and_taxes": {
        "local_authority": "Colombo Municipal Council",
        "assessment_no": "142/7",
        "owner": "K. A. Perera",
        "property": "No. 142/7, Galle Road, Colombo 03",
        "annual_value": 480000,
        "rate_percent": 8.0,
        "payments": [
            {"year": 2024, "quarter": "Q1", "amount_due": 9600, "amount_paid": 9600,
             "receipt_no": "R-88123", "date_paid": "2024-02-10", "arrears": 0},
            {"year": 2024, "quarter": "Q2", "amount_due": 9600, "amount_paid": 9600,
             "receipt_no": "R-90411", "date_paid": "2024-05-08", "arrears": 0},
            {"year": 2024, "quarter": "Q3", "amount_due": 9600, "amount_paid": 0,
             "receipt_no": "", "date_paid": "", "arrears": 9600},
        ],
        "total_arrears": 9600,
        "certified_by": "",
        "certified_date": "",
    },
}


# ---------------------------------------------------------------------------
# 3. EXTRACT — stands in for the real OCR / field-extraction stage, which is
#    a separate piece of work owned by a teammate. This is a STUB: it ignores
#    the uploaded file's actual contents and returns hardcoded data whose keys
#    match the target schema, exactly like SAMPLE_DATA above.
#
#    When the real extractor is ready, ONLY this function's body changes —
#    render_editable_form() and build_docx() already consume whatever dict
#    comes back from here, so they don't need to know the data's origin.
# ---------------------------------------------------------------------------

def extract_fields(uploaded_file, doc_id: str) -> dict:
    """STUB. Real version: OCR `uploaded_file` (pdf/png/jpg) and map recognised
    text to this schema's field keys, optionally attaching a source pointer
    per field as {"value": ..., "source": {"page": n}} — see `_unwrap`/`_rewrap`
    below. For now it just hands back the fixture data for `doc_id`.
    """
    return copy.deepcopy(SAMPLE_DATA.get(doc_id, {}))


# ---------------------------------------------------------------------------
# 4. RENDER — turn a schema + data into an editable Streamlit form.
#    Returns the edited data dict.
# ---------------------------------------------------------------------------

def _parse_date(value):
    if isinstance(value, dt.date):
        return value
    if isinstance(value, str) and value.strip():
        try:
            return dt.datetime.strptime(value.strip(), "%Y-%m-%d").date()
        except ValueError:
            return None
    return None


def _unwrap(current):
    """Split a field's stored value from its optional traceability pointer.

    A scalar field's value in `data` is normally just the value itself
    (e.g. "K. A. Perera"). To support tracing a value back to where OCR
    read it from, a field MAY instead store
    `{"value": ..., "source": {"page": 3, ...}}`. This unwraps either shape
    to a plain (value, source) pair; `source` is None when there's no
    pointer. The extraction stub does not populate `source` yet — the hook
    just needs to exist so a future extractor can attach it per field.
    """
    if isinstance(current, dict) and "value" in current:
        return current.get("value"), current.get("source")
    return current, None


def _rewrap(value, source):
    """Re-attach a source pointer (if any) to an edited scalar value."""
    return {"value": value, "source": source} if source else value


def render_editable_form(schema: dict, data: dict) -> dict:
    """Render widgets for every field in the schema, pre-filled from `data`."""
    edited: dict = {}

    for section in schema["sections"]:
        st.subheader(section["name"])
        for field in section["fields"]:
            key = field["key"]
            wkey = f'{schema["id"]}__{key}'          # unique Streamlit widget key
            label = field["label_en"]
            if field.get("label_si"):
                label = f'{label}  ·  {field["label_si"]}'
            current, source = _unwrap(data.get(key, ""))
            ftype = field["type"]

            if ftype == "text":
                value = st.text_input(label, value=str(current or ""), key=wkey)
                edited[key] = _rewrap(value, source)

            elif ftype == "number":
                num = float(current) if current not in ("", None) else 0.0
                value = st.number_input(label, value=num, step=1.0, key=wkey)
                edited[key] = _rewrap(value, source)

            elif ftype == "textarea":
                value = st.text_area(label, value=str(current or ""), key=wkey)
                edited[key] = _rewrap(value, source)

            elif ftype == "date":
                d = _parse_date(current)
                picked = st.date_input(label, value=d, key=wkey)
                value = picked.strftime("%Y-%m-%d") if picked else ""
                edited[key] = _rewrap(value, source)

            elif ftype == "table":
                cols = field["columns"]
                rows = current if isinstance(current, list) else []
                df = pd.DataFrame(rows, columns=[c["key"] for c in cols])
                # friendly column headers
                df = df.rename(columns={c["key"]: c["label"] for c in cols})
                st.caption(field["label_en"])
                editeddf = st.data_editor(
                    df, num_rows="dynamic", use_container_width=True, key=wkey
                )
                # map headers back to keys
                back = {c["label"]: c["key"] for c in cols}
                editeddf = editeddf.rename(columns=back)
                edited[key] = editeddf.to_dict("records")

            if ftype != "table" and source:
                st.caption(f'📍 source: page {source.get("page", "?")}')

    return edited


# ---------------------------------------------------------------------------
# 5. EXPORT — schema + data -> a Word (.docx) file, returned as bytes.
# ---------------------------------------------------------------------------

def _shade_cell(cell, hex_fill):
    """Set a table cell background colour."""
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
    tcpr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:fill"), hex_fill)
    tcpr.append(shd)


def build_docx(schema: dict, data: dict) -> bytes:
    doc = Document()

    # Title (English + Sinhala)
    h = doc.add_paragraph()
    h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = h.add_run(schema["title_en"])
    run.bold = True
    run.font.size = Pt(15)
    if schema.get("title_si"):
        hs = doc.add_paragraph()
        hs.alignment = WD_ALIGN_PARAGRAPH.CENTER
        rs = hs.add_run(schema["title_si"])
        rs.font.size = Pt(12)
    doc.add_paragraph()  # spacer

    for section in schema["sections"]:
        sh = doc.add_paragraph()
        shr = sh.add_run(section["name"])
        shr.bold = True
        shr.font.color.rgb = RGBColor(0x33, 0x33, 0x33)

        table_fields = [f for f in section["fields"] if f["type"] == "table"]
        scalar_fields = [f for f in section["fields"] if f["type"] != "table"]

        # scalar fields -> a two-column label/value table
        if scalar_fields:
            t = doc.add_table(rows=0, cols=2)
            t.style = "Table Grid"
            t.alignment = WD_TABLE_ALIGNMENT.LEFT
            for f in scalar_fields:
                row = t.add_row().cells
                lbl = f["label_en"]
                if f.get("label_si"):
                    lbl = f'{lbl} / {f["label_si"]}'
                row[0].text = lbl
                val, _ = _unwrap(data.get(f["key"], ""))
                row[1].text = "" if val in (None, "") else str(val)
                _shade_cell(row[0], "F2F2F2")
                row[0].width = Pt(200)
                row[1].width = Pt(260)

        # table fields -> a full grid with column headers
        for f in table_fields:
            cols = f["columns"]
            rows = data.get(f["key"], []) or []
            gt = doc.add_table(rows=1, cols=len(cols))
            gt.style = "Table Grid"
            for i, c in enumerate(cols):
                cell = gt.rows[0].cells[i]
                cell.text = c["label"]
                for p in cell.paragraphs:
                    for r in p.runs:
                        r.bold = True
                _shade_cell(cell, "E8EEF7")
            for rec in rows:
                cells = gt.add_row().cells
                for i, c in enumerate(cols):
                    v = rec.get(c["key"], "")
                    cells[i].text = "" if v in (None, "") else str(v)

        doc.add_paragraph()  # spacer between sections

    # signature / approval line
    doc.add_paragraph()
    sig = doc.add_paragraph("Reviewed and approved: __________________________    Date: ____________")
    sig.runs[0].font.size = Pt(10)

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# 6. STREAMLIT UI
# ---------------------------------------------------------------------------

def main():
    st.set_page_config(page_title="Draftly — Document Templates", layout="centered")
    st.title("Draftly — Editable Document Templates")
    st.caption(
        "Extraction fills the fields · the lawyer verifies and edits · export to Word. "
        "The document stays structured, so nothing about the layout can be broken by editing."
    )

    labels = {
        "assessment_extract": "Assessment Extract (පත්තිරු)",
        "rates_and_taxes": "Rates & Taxes (වාරිපනම්)",
    }
    doc_id = st.selectbox(
        "Document",
        options=list(SCHEMAS.keys()),
        format_func=lambda k: labels.get(k, k),
    )
    schema = SCHEMAS[doc_id]

    # Keep edited data in session so it survives reruns / doc switches.
    store_key = f"data__{doc_id}"
    extracted_key = f"extracted_from__{doc_id}"   # signature of the last file we ran extract_fields on
    if store_key not in st.session_state:
        st.session_state[store_key] = {}

    st.subheader("1. Upload source document")
    uploaded_file = st.file_uploader(
        "Scanned assessment / rates document",
        type=["pdf", "png", "jpg", "jpeg"],
        key=f"upload__{doc_id}",
    )
    if uploaded_file is not None:
        signature = f"{uploaded_file.name}:{uploaded_file.size}"
        if st.session_state.get(extracted_key) != signature:
            st.session_state[store_key] = extract_fields(uploaded_file, doc_id)
            st.session_state[extracted_key] = signature
            st.rerun()

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Load sample extracted data"):
            st.session_state[store_key] = copy.deepcopy(SAMPLE_DATA.get(doc_id, {}))
            st.rerun()
    with col2:
        if st.button("Clear all fields"):
            st.session_state[store_key] = {}
            st.session_state.pop(extracted_key, None)
            st.rerun()

    st.divider()
    st.subheader("2. Verify and edit")

    edited = render_editable_form(schema, st.session_state[store_key])
    st.session_state[store_key] = edited   # persist edits

    st.divider()
    docx_bytes = build_docx(schema, edited)
    st.download_button(
        "⬇ Export to Word (.docx)",
        data=docx_bytes,
        file_name=f'{doc_id}.docx',
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        type="primary",
    )

    with st.expander("Show structured data (JSON)"):
        st.json(edited)


if __name__ == "__main__":
    main()