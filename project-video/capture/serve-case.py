"""Local film harness: real services and source bytes, prepared extraction only.

Never a production adapter. No remote OCR, no relaxed approval rules, no edits
to the product repository. Expected values are read from the approved bundle.
"""
from pathlib import Path
import asyncio
import hashlib
import json
import os
import sys
import subprocess
import csv
import io

ROOT = Path(__file__).resolve().parents[1]
PLATFORM = ROOT.parent.parent / 'draftly-platform'
BACKEND = PLATFORM / 'backend'
SOURCE = PLATFORM / 'inputs' / 'case-001'
os.chdir(BACKEND)
sys.path.insert(0, str(BACKEND))
os.environ.update({
    'DATABASE_URL': 'postgresql+psycopg://film@127.0.0.1:5439/draftly_film',
    'DATABASE_URL_DIRECT': 'postgresql+psycopg://film@127.0.0.1:5439/draftly_film',
    'ENVIRONMENT': 'test', 'USE_STUB_IDENTITY': 'true',
    # User approved local use of the owner's records. All remote keys are
    # disabled here; this approval covers local prepared processing only.
    'EXTRACTION_PROVIDER': 'vision-stub', 'PROVIDER_DATA_APPROVAL': 'true',
    'GEMINI_API_KEY': '', 'RETRIEVAL_BASE_URL': '',
    'DEMO_RELAXED_GATES': 'false', 'SOURCE_FILE_STORAGE': 'filesystem',
    'SOURCE_FILE_STORAGE_DIR': str(ROOT / 'out' / 'local-source-files'),
    'ALLOWED_ORIGINS': 'http://127.0.0.1:4311',
    'RESEND_OUTBOUND_ENABLED': 'false', 'EMAIL_SENDING_ENABLED': 'false',
    'MATTER_AGENT_ENABLED': 'false', 'RASTER_DPI': '160',
})

from src.modules.document.infrastructure import vision_stub_adapter as adapter
from src.modules.document.infrastructure.rasterizer_pypdfium import PypdfiumRasterizer
from src.modules.document.domain.v1 import OcrPage, OcrElement, Point, PageClassification, ExtractedCandidate, DetectedLanguage
from src.modules.document.infrastructure.matter_document_types import template_kind_for_class

expected = json.loads((SOURCE / 'expected-fields.json').read_text(encoding='utf-8'))
by_digest = {hashlib.sha256((SOURCE / filename).read_bytes()).hexdigest(): record for filename, record in expected.items()}
original_rasterize = PypdfiumRasterizer.rasterize

def prepared_rasterize(self, data, mime_type):
    pages = original_rasterize(self, data, mime_type)
    record = by_digest.get(hashlib.sha256(data).hexdigest(), {'kind': 'other', 'fields': {}})
    for page in pages:
        page.film_record = record
    return pages

PypdfiumRasterizer.rasterize = prepared_rasterize

class PreparedBundleAdapter:
    async def document_text_detection(self, page):
        record = page.film_record
        # Real local OCR geometry. Structured candidates below remain prepared.
        result = subprocess.run([r'C:/Program Files/Tesseract-OCR/tesseract.exe', 'stdin', 'stdout', '-l', 'eng', '--psm', '3', 'tsv'], input=page.png_bytes, capture_output=True, check=True)
        elements = []
        for row in csv.DictReader(io.StringIO(result.stdout.decode('utf-8')), delimiter='\t'):
            if row['level'] != '5' or not row['text'].strip():
                continue
            x,y,w,h = (float(row[k]) for k in ['left','top','width','height'])
            elements.append(OcrElement(level='word', text=row['text'], confidence=max(0,float(row['conf']))/100, detected_languages=(), polygon=(Point(x,y),Point(x+w,y),Point(x+w,y+h),Point(x,y+h)), reading_order=len(elements)))
        kind = record['kind']
        if kind == 'form8-instrument' and page.page_no != 2:
            kind = 'other'
        text = 'prepared-kind:' + kind + '\n' + ' '.join(e.text for e in elements)
        return OcrPage(text=text, detected_languages=(), elements=tuple(elements))

    async def classify_pages(self, pages, *, allowed_type_ids, text_limit):
        result = []
        previous = None
        for page in pages:
            kind = page.text.split('\n', 1)[0].removeprefix('prepared-kind:')
            type_id = next((i for i in allowed_type_ids if template_kind_for_class(i) == kind), 'other')
            result.append(PageClassification(page_no=page.page_no, type_id=type_id, suggested_name=None, starts_new_document=type_id != previous, model_reported_confidence=1.0))
            previous = type_id
        return result

    async def extract_document(self, *, type_id, text, page_numbers, fields):
        kind = template_kind_for_class(type_id)
        values = next((r['fields'] for r in expected.values() if r['kind'] == kind), {})
        page = 2 if kind == 'form8-instrument' and 2 in page_numbers else page_numbers[0]
        return tuple(ExtractedCandidate(key=f.key, value=values[f.key], page_no=page, model_reported_confidence=1.0) for f in fields if f.key in values)

adapter.VisionStubAdapter = PreparedBundleAdapter

from src.main import app
import uvicorn

if __name__ == '__main__':
    # Explicit selector runner is required by psycopg on Windows.
    config = uvicorn.Config(app, host='127.0.0.1', port=4321, log_level='warning', loop='asyncio')
    with asyncio.Runner(loop_factory=asyncio.SelectorEventLoop) as runner:
        runner.run(uvicorn.Server(config).serve())
