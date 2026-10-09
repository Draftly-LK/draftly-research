"""Local actual-service demo harness with disclosed prepared extraction."""
from pathlib import Path
import asyncio
import csv
import hashlib
import io
import json
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PLATFORM = ROOT.parent.parent / "draftly-platform"
BACKEND = PLATFORM / "backend"
SOURCE = ROOT / "out" / "demo-bundle"
DATABASE = "postgresql+psycopg://film@127.0.0.1:15439/draftly_video_workflow_v2"
os.chdir(BACKEND)
sys.path.insert(0, str(BACKEND))
os.environ.update({
    "DATABASE_URL": DATABASE, "DATABASE_URL_DIRECT": DATABASE,
    "ENVIRONMENT": "test", "USE_STUB_IDENTITY": "true",
    "EXTRACTION_PROVIDER": "vision-stub", "PROVIDER_DATA_APPROVAL": "true",
    "GEMINI_API_KEY": "", "RETRIEVAL_BASE_URL": "",
    "SUPERMEMORY_ENABLED": "false", "SUPERMEMORY_API_KEY": "",
    "DEMO_RELAXED_GATES": "false", "SOURCE_FILE_STORAGE": "filesystem",
    "SOURCE_FILE_STORAGE_DIR": str(ROOT / "out" / "demo-source-files"),
    "ALLOWED_ORIGINS": "http://127.0.0.1:4315",
    "RESEND_API_KEY": "", "RESEND_OUTBOUND_ENABLED": "false",
    "EMAIL_SENDING_ENABLED": "false", "MATTER_AGENT_ENABLED": "false",
    "CLERK_SECRET_KEY": "", "PAYHERE_MERCHANT_SECRET": "", "USE_STUB_BILLING": "true",
    "RASTER_DPI": "160",
})

from src.modules.document.infrastructure import vision_stub_adapter as adapter
from src.modules.document.infrastructure.rasterizer_pypdfium import PypdfiumRasterizer
from src.modules.document.domain.v1 import OcrPage, OcrElement, Point, PageClassification, ExtractedCandidate
from src.modules.document.infrastructure.matter_document_types import template_kind_for_class

expected = json.loads((SOURCE / "expected-fields.json").read_text(encoding="utf-8"))
by_digest = {hashlib.sha256((SOURCE / filename).read_bytes()).hexdigest(): filename for filename in expected}
original_rasterize = PypdfiumRasterizer.rasterize

def prepared_rasterize(self, data, mime_type):
    pages = original_rasterize(self, data, mime_type)
    filename = by_digest.get(hashlib.sha256(data).hexdigest())
    for page in pages:
        page.film_filename = filename
    return pages

PypdfiumRasterizer.rasterize = prepared_rasterize

class PreparedDemoAdapter:
    async def document_text_detection(self, page):
        filename = page.film_filename
        record = expected.get(filename, {"kind": "other", "fields": {}})
        result = subprocess.run([
            r"C:/Program Files/Tesseract-OCR/tesseract.exe", "stdin", "stdout", "-l", "eng", "--psm", "3", "tsv"
        ], input=page.png_bytes, capture_output=True, check=True)
        elements = []
        for row in csv.DictReader(io.StringIO(result.stdout.decode("utf-8")), delimiter="\t"):
            if row["level"] != "5" or not row["text"].strip():
                continue
            x, y, w, h = (float(row[k]) for k in ("left", "top", "width", "height"))
            elements.append(OcrElement(level="word", text=row["text"], confidence=max(0, float(row["conf"])) / 100,
                detected_languages=(), polygon=(Point(x, y), Point(x + w, y), Point(x + w, y + h), Point(x, y + h)),
                reading_order=len(elements)))
        kind = record["kind"]
        if kind == "form8-instrument" and page.page_no != 2:
            kind = "other"
        text = f"prepared-kind:{kind}\nprepared-record:{filename or 'unknown'}\n" + " ".join(e.text for e in elements)
        return OcrPage(text=text, detected_languages=(), elements=tuple(elements))

    async def classify_pages(self, pages, *, allowed_type_ids, text_limit):
        results = []
        previous = None
        for page in pages:
            kind = page.text.split("\n", 1)[0].removeprefix("prepared-kind:")
            type_id = next((i for i in allowed_type_ids if template_kind_for_class(i) == kind), "other")
            results.append(PageClassification(page_no=page.page_no, type_id=type_id, suggested_name=None,
                starts_new_document=type_id != previous, model_reported_confidence=1.0))
            previous = type_id
        return results

    async def extract_document(self, *, type_id, text, page_numbers, fields):
        filename = next((line.split("prepared-record:", 1)[1].strip() for line in text.splitlines()
                         if "prepared-record:" in line), None)
        values = expected.get(filename, {}).get("fields", {})
        kind = template_kind_for_class(type_id)
        page = 2 if kind == "form8-instrument" and 2 in page_numbers else page_numbers[0]
        return tuple(ExtractedCandidate(key=f.key, value=values[f.key], page_no=page,
            model_reported_confidence=1.0) for f in fields if f.key in values)

adapter.VisionStubAdapter = PreparedDemoAdapter
from src.main import app
import uvicorn

if __name__ == "__main__":
    config = uvicorn.Config(app, host="127.0.0.1", port=4325, log_level="warning", loop="asyncio")
    with asyncio.Runner(loop_factory=asyncio.SelectorEventLoop) as runner:
        runner.run(uvicorn.Server(config).serve())
