"""Create illustrative local demo sources; never prescribed legal forms."""
from pathlib import Path
import json
import pymupdf

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "out" / "demo-bundle"
DISCLOSURE = "Demonstration document · illustrative information"
PARCEL = {
    "district": "Demo District", "dsDivision": "Demo Division",
    "gnDivision": "Demo GN Division", "village": "Demo Village",
    "assessmentNumber": "DEMO-ASSESS-21", "cadastralMapNo": "610021",
    "blockNo": "01", "sheetNo": "01", "parcelNo": "0021",
    "extent": "0.0159 hectares", "extentSubjectToTransfer": "0.0159 hectares",
    "placeOfRegistration": "Demo Registry Office", "titleCertificateNo": "DEMO-TITLE-0021",
    "classOfTitle": "FIRST_CLASS",
}
RECORDS = {
    "demo-title-information.pdf": {"kind": "title-certificate", "fields": {
        **{k: v for k, v in PARCEL.items() if k not in {"village", "assessmentNumber", "extentSubjectToTransfer"}},
        "ownerName": "Demo Seller",
    }},
    "demo-survey-information.pdf": {"kind": "survey-plan", "fields": {
        "surveyPlanNo": "DEMO-PLAN-0022", "surveyorName": "Demo Surveyor",
        "surveyorRegistration": "DEMO-SURVEYOR", "landName": "Demo Parcel",
        "lotNo": "0022", "extent": "0.0159 hectares", "boundaryNorth": "Demo road",
        "boundaryEast": "Demo lot A", "boundarySouth": "Demo stream", "boundaryWest": "Demo lot B",
    }},
    "demo-buyer-identity-information.pdf": {"kind": "identity-card", "fields": {
        "transfereeNic": "DEMO-ID-B", "holderNameEn": "Demo Buyer",
        "holderDateOfBirth": "1990-01-01", "holderAddress": "Demo Buyer Address",
    }},
    "demo-transfer-information.pdf": {"kind": "form8-instrument", "fields": {
        **PARCEL, "transferorName": "Demo Seller", "transferorNic": "DEMO-ID-A",
        "transferorAddress": "Demo Seller Address", "transfereeName": "Demo Buyer",
        "transfereeNic": "DEMO-ID-B", "transfereeAddress": "Demo Buyer Address",
        "consideration": "Rs. 1,000,000", "considerationWords": "Rupees one million",
        "notaryName": "Demo Reviewing Lawyer", "notaryCode": "DEMO-NP",
    }},
}
TITLES = {
    "title-certificate": "Title information fact sheet",
    "survey-plan": "Survey reference fact sheet",
    "identity-card": "Buyer identity information fact sheet",
    "form8-instrument": "Transfer particulars fact sheet",
}

def page_header(document, title, page_number):
    page = document.new_page(width=595, height=842)
    navy = (0.10, 0.20, 0.34)
    page.draw_rect(pymupdf.Rect(36, 32, 559, 91), color=None, fill=navy)
    page.insert_text((49, 55), "DRAFTLY DEMONSTRATION", fontname="hebo", fontsize=13, color=(1, 1, 1))
    page.insert_text((49, 76), DISCLOSURE, fontsize=10, color=(1, 1, 1))
    page.insert_text((40, 121), title, fontname="hebo", fontsize=20, color=navy)
    page.insert_text((40, 802), f"Illustrative fact sheet | Page {page_number} | No official document status", fontsize=9, color=navy)
    return page

def rows(page, values):
    y = 159
    for key, value in values.items():
        page.draw_line((40, y + 10), (555, y + 10), color=(0.86, 0.89, 0.93), width=0.5)
        page.insert_text((42, y), key, fontsize=9, color=(0.33, 0.39, 0.47))
        page.insert_text((205, y), value, fontsize=10, color=(0.06, 0.10, 0.18))
        y += 24

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    expected = {}
    for filename, record in RECORDS.items():
        doc = pymupdf.open()
        if record["kind"] == "form8-instrument":
            cover = page_header(doc, "Transfer information: demonstration cover", 1)
            rows(cover, {"seller": "Demo Seller", "buyer": "Demo Buyer", "parcel": "0021", "area": "0.0159 hectares"})
            cover.insert_textbox(pymupdf.Rect(42, 300, 550, 420),
                "This illustrative information sheet supplies demo particulars for interface review. "
                "It is not a prescribed transfer instrument and contains no attestation or approval wording. "
                "Structured demo fields are on page 2.", fontsize=12, lineheight=1.5)
        page = page_header(doc, TITLES[record["kind"]], len(doc) + 1)
        rows(page, record["fields"])
        doc.set_metadata({"title": TITLES[record["kind"]], "author": "Draftly demonstration", "subject": DISCLOSURE})
        doc.save(OUT / filename)
        doc.close()
        fields = dict(record["fields"])
        if record["kind"] == "title-certificate":
            fields["extent"] = "0.0158 hectares"
        expected[filename] = {"kind": record["kind"], "fields": fields,
            "preparation": "Prepared candidates for local UI recording; local English OCR supplies source text and geometry."}
    (OUT / "expected-fields.json").write_text(json.dumps(expected, indent=2) + "\n", encoding="utf-8")
    for filename in RECORDS:
        doc = pymupdf.open(OUT / filename)
        text = "\n".join(page.get_text() for page in doc)
        assert "synthetic" not in text.lower()
        assert all(DISCLOSURE in page.get_text() for page in doc)
        assert "0.0159 hectares" in text or RECORDS[filename]["kind"] == "identity-card"
        print(f"{filename}: {len(doc)} page(s), disclosure verified")
    doc = pymupdf.open(OUT / "demo-transfer-information.pdf")
    assert "transferorName" in doc[1].get_text()
    image = doc[1].get_pixmap(matrix=pymupdf.Matrix(1, 1))
    image.save(OUT / "transfer-page-2-review.png")

if __name__ == "__main__":
    main()
