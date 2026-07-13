from pathlib import Path
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

opts = PdfPipelineOptions()
opts.do_ocr = False               # born-digital text layer; OCR was the OOM culprit
opts.generate_page_images = False # don't rasterize full pages
opts.generate_picture_images = False
opts.images_scale = 1.0

conv = DocumentConverter(
    format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)}
)
src = Path("papers/bookrag-2512.03413.pdf")
res = conv.convert(src)
out = Path("papers/markdown/bookrag-2512.03413.md")
out.write_text(res.document.export_to_markdown(), encoding="utf-8")
print("OK ->", out, out.stat().st_size, "bytes")
