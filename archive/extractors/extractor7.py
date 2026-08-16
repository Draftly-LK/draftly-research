import fitz  # PyMuPDF
import re
import json

def clean_text(text: str) -> str:
    """Remove newlines and normalize whitespace."""
    return re.sub(r"\s+", " ", text).strip()

def extract_metadata(page_text):
    title = None
    act_number = None
    year = None
    certification_date = None
    gazette_date = None
    summary = None
    preamble = None

    # Title (full formal name, remove "PARLIAMENT OF..." prefix if present)
    title_match = re.search(
        r"([A-Z\s\(\)]+ACT[, ]+No[.]?\s*\d+\s*OF\s*\d{4})",
        page_text, re.IGNORECASE
    )
    if title_match:
        raw_title = title_match.group(1).strip()
        title = re.sub(
            r"^PARLIAMENT OF THE DEMOCRATIC\s+SOCIALIST REPUBLIC OF\s+SRI LANKA\s*",
            "",
            raw_title,
            flags=re.IGNORECASE
        ).strip()

    # Act number and year
    act_match = re.search(r"No[.]?\s*(\d+)\s*OF\s*(\d{4})", page_text, re.IGNORECASE)
    if act_match:
        act_number = act_match.group(1).strip()
        year = act_match.group(2).strip()

    # Certification date
    cert_match = re.search(r"\[Certified on\s*([^\]]+)\]", page_text, re.IGNORECASE)
    if cert_match:
        certification_date = cert_match.group(1).strip()

    # Gazette date
    gaz_match = re.search(r"Gazette.*?(\w+\s+\d{1,2},?\s+\d{4})", page_text, re.IGNORECASE)
    if gaz_match:
        gazette_date = gaz_match.group(1).strip()

    # Summary (usually starts with AN ACT)
    summary_match = re.search(r"AN ACT.*?(?=WHEREAS|BE it enacted)", page_text, re.IGNORECASE | re.DOTALL)
    if summary_match:
        summary = summary_match.group(0).strip()

    # Preamble (robustly handle multiple WHEREAS / AND WHEREAS)
    preamble_match = re.search(
        r"(WHEREAS.*?)(?=BE it therefore enacted|BE it therefore enacted by Parliament|BE it enacted)",
        page_text,
        re.IGNORECASE | re.DOTALL
    )
    if preamble_match:
        preamble = preamble_match.group(0).strip()

    return {
        "title": clean_text(title) if title else "",
        "act_number": act_number or "",
        "year": year or "",
        "certification_date": clean_text(certification_date) if certification_date else "",
        "gazette_date": clean_text(gazette_date) if gazette_date else "",
        "summary": clean_text(summary) if summary else "",
        "preamble": clean_text(preamble) if preamble else ""
    }

def extract_sections(pdf_path, left_margin=200, right_margin=200):
    doc = fitz.open(pdf_path)

    # Combine text from first 2 pages to extract metadata, summary, and preamble
    first_pages_text = ""
    for i in range(min(2, len(doc))):
        first_pages_text += doc[i].get_text() + "\n"
    metadata = extract_metadata(first_pages_text)

    sections = []
    section_count = 0

    for page_num in range(len(doc)):
        page = doc[page_num]
        width = page.rect.width
        blocks = page.get_text("dict")["blocks"]

        margin_notes = []
        content_spans = []

        # Separate margin notes and main content
        for b in blocks:
            if "lines" not in b:
                continue
            x0, y0, x1, y1 = b.get("bbox", [0,0,0,0])
            text = " ".join(span["text"] for line in b["lines"] for span in line["spans"]).strip()
            if not text:
                continue

            if x1 < left_margin or x0 > (width - right_margin):
                margin_notes.append({'y': y0, 'text': clean_text(text)})
            else:
                for line in b["lines"]:
                    for span in line["spans"]:
                        content_spans.append({
                            "text": span["text"].strip(),
                            "bold": "Bold" in span["font"] or span["flags"] & 2,
                            "y": y0
                        })

        margin_notes.sort(key=lambda x: x['y'])
        content_spans.sort(key=lambda x: x['y'])

        current_section = None

        for i, span in enumerate(content_spans):
            # Check if span is a bold number (section start)
            if span["bold"] and re.match(r"^\d+\.$", span["text"]):
                # Save previous section
                if current_section:
                    current_section["content"] = clean_text(current_section["content"])
                    sections.append(current_section)
                    section_count += 1

                # Find nearest margin note for title
                nearest_margin = None
                nearest_distance = float("inf")
                for mn in margin_notes:
                    distance = abs(mn["y"] - span["y"])
                    if distance < nearest_distance:
                        nearest_distance = distance
                        nearest_margin = mn
                section_title = nearest_margin["text"] if nearest_margin else ""

                # Start new section
                current_section = {
                    "section_number": span["text"].strip("."),
                    "section_title": clean_text(section_title),
                    "content": ""
                }
            else:
                # Add text to current section
                if current_section:
                    current_section["content"] += " " + span["text"]

        # Add last section on page
        if current_section:
            current_section["content"] = clean_text(current_section["content"])
            sections.append(current_section)
            section_count += 1

    return {
        "metadata": metadata,
        "sections": sections,
        "total_sections": section_count
    }

if __name__ == "__main__":
    pdf_file = "10-2024_E.pdf"  # Change to your PDF path
    extracted_data = extract_sections(pdf_file)

    print(json.dumps(extracted_data, indent=4, ensure_ascii=False))
    with open("extracted_act_10-2024_E.json", "w", encoding="utf-8") as f:
         json.dump(extracted_data, f, ensure_ascii=False, indent=4)
