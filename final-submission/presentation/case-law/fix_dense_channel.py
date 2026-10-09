"""Apply a precise dense-channel correction while preserving the v3 artwork."""
from pathlib import Path
import shutil

from PIL import Image, ImageDraw, ImageFont, ImageOps

HERE = Path(__file__).resolve().parent
TARGET = HERE / 'Draftly-Case-Law-Retrieval-PaperBanana-v3.png'
ORIGINAL = HERE / 'Draftly-Case-Law-Retrieval-PaperBanana-v3-before-dense-fix.png'
if not ORIGINAL.exists():
    shutil.copyfile(TARGET, ORIGINAL)
im = Image.open(ORIGINAL).convert('RGB')
scale = im.width / 2048
d = ImageDraw.Draw(im)


def box(coords):
    return tuple(round(v * scale) for v in coords)


def path(points, color, width):
    d.line([box(p) for p in points], fill=color,
           width=round(width * scale), joint='curve')


navy = '#183B63'
# Remove the optional-channel card, legend, and dashed connecting paths.
d.rectangle(box((640, 672, 1028, 832)), fill='white')
d.rectangle(box((67, 786, 470, 824)), fill='white')
path([(467, 649), (467, 750), (648, 750)], 'white', 14)
path([(1019, 750), (1208, 750), (1208, 649)], 'white', 16)
d.polygon([box(p) for p in [(1193, 649), (1223, 649), (1223, 676), (1193, 676)]], fill='white')

# Dense retrieval is a normal architecture branch.
d.rounded_rectangle(box((650, 680, 1018, 819)), radius=round(16 * scale),
                    fill='#E2EEFA', outline=navy, width=round(2 * scale))
path([(467, 646), (467, 750), (626, 750)], navy, 4)
d.polygon([box(p) for p in [(650, 750), (625, 737), (625, 763)]], fill=navy)
path([(1018, 750), (1208, 750), (1208, 675)], navy, 4)
d.polygon([box(p) for p in [(1208, 646), (1194, 675), (1222, 675)]], fill=navy)

bold = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', round(34 * scale))
regular = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', round(29 * scale))
d.text(box((834, 723)), 'Dense embeddings', fill='#101010', font=bold, anchor='mm')
d.text(box((834, 774)), 'Semantic similarity', fill='#101010', font=regular, anchor='mm')
im.save(TARGET)
ImageOps.grayscale(im).resize((1440, 804)).save(HERE / 'case-law-v3-grayscale-preview.png')
im.save(HERE.parents[1] / 'figures/research-case-law-retrieval-v3.png')
print('Corrected dense card, solid arrows, grayscale preview and library copy.')
