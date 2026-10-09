"""Draw the four synthetic demo documents with the stub's invented values.

Each PNG carries the vision-stub marker in a tEXt "Comment" chunk
(STUB-KIND:<kind>), exactly like the originals in draftly-synthetic-docs.
Every value is invented; nothing here comes from a real record.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from PIL.PngImagePlugin import PngInfo

OUT = Path(__file__).parent / "docs"
OUT.mkdir(exist_ok=True)
W, H = 1600, 1000
F = "C:/Windows/Fonts/"
reg = lambda s: ImageFont.truetype(F + "arial.ttf", s)
bold = lambda s: ImageFont.truetype(F + "arialbd.ttf", s)
mono = lambda s: ImageFont.truetype(F + "consola.ttf", s)
INK = (25, 30, 40)
RED = (176, 58, 46)
GREY = (120, 128, 140)


def page(kind: str, title: str, subtitle: str, rows: list[tuple[str, str]], extra=None) -> None:
    im = Image.new("RGB", (W, H), (252, 251, 246))
    d = ImageDraw.Draw(im)
    d.rectangle([18, 18, W - 18, H - 18], outline=INK, width=4)
    d.rectangle([18, 18, W - 18, 78], fill=(248, 215, 210))
    d.text((40, 32), "SYNTHETIC DEMO DOCUMENT  -  NOT A REAL RECORD  -  INVENTED VALUES ONLY", font=bold(26), fill=RED)
    d.text((60, 120), title, font=bold(46), fill=INK)
    d.text((60, 180), subtitle, font=reg(26), fill=GREY)
    d.line([60, 230, W - 60, 230], fill=(200, 205, 212), width=2)
    y = 262
    col_w = 560 if extra else 700
    for label, value in rows:
        d.text((60, y), label, font=reg(28), fill=GREY)
        d.text((60 + col_w - 120, y), value, font=mono(30), fill=INK)
        y += 52
    if extra:
        extra(d)
    info = PngInfo()
    info.add_text("Comment", f"STUB-KIND:{kind}\n")
    im.save(OUT / f"synthetic-{'form8-instrument' if kind == 'form8-instrument' else kind}.png", pnginfo=info)


PARCEL = [
    ("District", "Colombo"),
    ("Divisional Secretary's Division", "Synthetic DS Division"),
    ("Grama Niladhari Division", "Synthetic GN Division 000"),
    ("Village", "Synthetic Village"),
    ("Cadastral map no.", "900001"),
    ("Block no. / Sheet no.", "09 / 01"),
    ("Parcel no.", "0099"),
    ("Extent", "0.0250 hectares"),
]

page(
    "title-certificate",
    "Certificate of Title (Bim Saviya)  -  SYNTHETIC",
    "Registration of Title Act, No. 21 of 1998, section 37  -  demonstration copy",
    [("Title certificate no.", "00099900001"), ("Class of title", "First class"), *PARCEL,
     ("Registered owner", "Synthetic Transferor One"), ("Place of registration", "Synthetic Land Registry")],
)

page(
    "identity-card",
    "National Identity Card  -  SYNTHETIC",
    "Demonstration card for a synthetic party",
    [("Name", "Synthetic Transferee Two"), ("NIC no.", "900010002V"), ("Date of birth", "1990-01-01"),
     ("Address", "1 Synthetic Lane, Synthetic Town")],
    extra=lambda d: (d.rectangle([1150, 262, 1480, 640], outline=GREY, width=3),
                     d.ellipse([1230, 320, 1400, 490], outline=GREY, width=3),
                     d.text((1235, 560), "PHOTO (none)", font=reg(26), fill=GREY)),
)

page(
    "form8-instrument",
    "Form 8  -  Instrument of Transfer  -  SYNTHETIC",
    "Registration of Title Act, section 43  -  demonstration particulars",
    [*PARCEL[:2], *PARCEL[4:],
     ("Title certificate no.", "00099900001"),
     ("Transferor  /  NIC", "Synthetic Transferor One  /  800000001V"),
     ("Transferee  /  NIC", "Synthetic Transferee Two  /  900010002V"),
     ("Consideration", "Rs. 1,000,000 (Rupees one million)"),
     ("Notary  /  code", "Synthetic Notary Public  /  SYN-NP-0001")],
)


def plan_drawing(d: ImageDraw.ImageDraw) -> None:
    pts = [(1060, 330), (1470, 300), (1500, 700), (1090, 740)]
    d.polygon(pts, outline=INK, width=4)
    d.text((1210, 500), "LOT 7", font=bold(36), fill=INK)
    d.text((1180, 260), "N: Synthetic road", font=reg(22), fill=GREY)
    d.text((1180, 760), "S: Synthetic stream", font=reg(22), fill=GREY)
    d.text((1515, 480), "E", font=reg(22), fill=GREY)
    d.text((1030, 520), "W", font=reg(22), fill=GREY)


page(
    "survey-plan",
    "Survey Plan No. 9001  -  SYNTHETIC",
    "Licensed surveyor's plan, scale 1:1000  -  demonstration drawing",
    [("Plan no.  /  Lot", "9001  /  7"), ("Land name", "Synthetic Land"), ("Extent", "0.0250 hectares"),
     ("Surveyor", "Synthetic Licensed Surveyor"), ("North", "Synthetic road"), ("East", "Synthetic lot 8"),
     ("South", "Synthetic stream"), ("West", "Synthetic lot 6")],
    extra=plan_drawing,
)


def extra(name: str, title: str, subtitle: str, rows: list[tuple[str, str]]) -> None:
    """Supporting records shown in the video only; never uploaded to the app."""
    im = Image.new("RGB", (W, H), (252, 251, 246))
    d = ImageDraw.Draw(im)
    d.rectangle([18, 18, W - 18, H - 18], outline=INK, width=4)
    d.rectangle([18, 18, W - 18, 78], fill=(248, 215, 210))
    d.text((40, 32), "SYNTHETIC DEMO DOCUMENT  -  NOT A REAL RECORD  -  INVENTED VALUES ONLY", font=bold(26), fill=RED)
    d.text((60, 120), title, font=bold(46), fill=INK)
    d.text((60, 180), subtitle, font=reg(26), fill=GREY)
    d.line([60, 230, W - 60, 230], fill=(200, 205, 212), width=2)
    y = 262
    for label, value in rows:
        d.text((60, y), label, font=reg(28), fill=GREY)
        d.text((560, y), value, font=mono(30), fill=INK)
        y += 56
    im.save(OUT / name)


extra(
    "synthetic-company-resolution.png",
    "Board Resolution (extract)  -  SYNTHETIC",
    "Certified extract  -  demonstration copy",
    [("Company", "Synthetic Developments (Pvt) Ltd"), ("Resolved", "To sell Lot 7 of Plan 9001"),
     ("To", "Synthetic Transferee Two"), ("Consideration", "Rs. 1,000,000"),
     ("Authorised signatory", "Synthetic Director One"), ("Date of resolution", "2026-01-01")],
)
extra(
    "synthetic-payment-record.png",
    "Payment Record  -  SYNTHETIC",
    "Bank cheque copy  -  demonstration copy",
    [("Payee", "Synthetic Developments (Pvt) Ltd"), ("Payer", "Synthetic Transferee Two"),
     ("Amount", "Rs. 400,000 (part payment)"), ("Cheque no.", "SYN-000123"),
     ("Date", "2026-01-15"), ("Bank", "Synthetic Bank, Synthetic Branch")],
)
print(sorted(p.name for p in OUT.glob("*.png")))
