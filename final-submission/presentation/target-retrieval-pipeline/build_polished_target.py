"""Build the editable, deterministic target retrieval figure."""
import importlib.util
import json
from pathlib import Path

import cairosvg
from PIL import Image, ImageOps

HERE = Path(__file__).resolve().parent
RENDERER = Path.home() / '.codex/skills/figure-spec/scripts/figure_renderer.py'
NAME = 'Draftly-Target-Hybrid-Retrieval-Polished-v4'
NAVY, BLUE, SLATE = '#183B63', '#EAF2FC', '#52677D'
AMBER, GREEN, ROSE = '#FFF4DF', '#E8F5EE', '#FCF0EC'


def card(id, label, x, y, w, h, fill=BLUE, fs=34, sub=None):
    result = dict(id=id, label=label, x=x, y=y, width=w, height=h,
                  shape='rounded', fill=fill, stroke='#B7C9DF',
                  text_color=NAVY, font_size=fs)
    if sub:
        result['sublabel'] = sub
    return result


nodes = [
    card('question', 'Lawyer\nquestion', 145, 560, 210, 140, '#FFFFFF'),
    card('original', 'Original query', 500, 330, 285, 110),
    card('rewrite', 'Bounded query\nrewrite', 270, 850, 235, 140, fs=30),
    card('sanitized', 'Sanitized\nrewrite', 540, 850, 220, 140),
    card('bm25-original', 'BM25\nlexical search', 850, 235, 250, 130),
    card('dense-original', 'Dense\nembedding\nsearch', 850, 425, 250, 130, fs=30),
    card('bm25-rewrite', 'BM25\nlexical search', 850, 755, 250, 130),
    card('dense-rewrite', 'Dense\nembedding\nsearch', 850, 945, 250, 130, fs=30),
    card('fusion', 'Initial RRF\nfusion', 1240, 590, 210, 150),
    card('graph', 'Typed graph\nexpansion', 1400, 880, 270, 160, AMBER),
    card('final', 'Final RRF\nfusion', 1500, 590, 190, 150),
    card('evidence', 'Retrieved\nsections', 1770, 590, 220, 150),
    card('gate', 'Answer generation\n+ evidence gate', 2050, 590, 255, 170,
         AMBER, 26, sub='Citations + claim checks'),
    card('answer', 'Grounded\nanswer', 2255, 305, 230, 130, GREEN),
    card('insufficient', 'Not enough\nlegal evidence', 2255, 815, 230, 130, ROSE, 30),
    card('status', 'TARGET INTEGRATION  ·  IN PROGRESS', 1200, 1220, 700, 64,
         '#F0F4F9', 26),
]
pairs = [('question', 'original'), ('question', 'rewrite'), ('rewrite', 'sanitized'),
         ('original', 'bm25-original'), ('original', 'dense-original'),
         ('sanitized', 'bm25-rewrite'), ('sanitized', 'dense-rewrite'),
         ('bm25-original', 'fusion'), ('dense-original', 'fusion'),
         ('bm25-rewrite', 'fusion'), ('dense-rewrite', 'fusion'),
         ('fusion', 'final'), ('fusion', 'graph'), ('graph', 'final'),
         ('final', 'evidence'), ('evidence', 'gate'),
         ('gate', 'answer'), ('gate', 'insufficient')]
edges = [dict(**{'from': a, 'to': b}, color=NAVY, thickness=2.5) for a, b in pairs]


def label(text, x, y, fs=27, anchor='middle', color=SLATE):
    return dict(text=text, x=x, y=y, font_size=fs, color=color, anchor=anchor)


spec = dict(
    title='Draftly target hybrid retrieval: core query channels',
    canvas=dict(width=2400, height=1350),
    style=dict(font_family='Arial, Helvetica, sans-serif', font_size=34,
               bg_color='#FFFFFF', palette=[NAVY, BLUE, AMBER, GREEN, ROSE]),
    nodes=nodes, edges=edges,
    labels=[
        label('01  QUERY PREPARATION', 400, 100, 28, color=NAVY),
        label('02  PARALLEL SEARCH', 850, 100, 28, color=NAVY),
        label('03  FUSION & EXPANSION', 1360, 100, 28, color=NAVY),
        label('04  EVIDENCE & ANSWER', 2050, 100, 28, color=NAVY),
        label('ORIGINAL QUERY', 850, 150, 23),
        label('REWRITTEN QUERY', 850, 670, 23),
        label('Search terms only', 540, 960, 26),
        label('No new citations', 540, 995, 26),
        label('Fused results', 1375, 490, 24),
        label('Fused statutory-section seeds', 1380, 1000, 26),
        label('Graph candidates', 1540, 750, 23),
        label('Source-linked evidence', 1770, 715, 25),
        label('Core query channels shown · Original query retained if rewriting is unavailable',
              1200, 1130, 28),
    ])


def main():
    spec_dir = HERE / 'figures/specs'
    spec_dir.mkdir(parents=True, exist_ok=True)
    (spec_dir / f'{NAME}.json').write_text(json.dumps(spec, indent=2), encoding='utf-8')
    module_spec = importlib.util.spec_from_file_location('figure_renderer', RENDERER)
    renderer = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(renderer)
    issues = renderer.validate_spec(spec)
    if issues:
        raise ValueError('\n'.join(issues))
    svg = HERE / f'{NAME}.svg'
    svg.write_text(renderer.render_svg(spec), encoding='utf-8')
    cairosvg.svg2png(url=str(svg), write_to=str(HERE / f'{NAME}.png'),
                    output_width=4800, output_height=2700)
    cairosvg.svg2pdf(url=str(svg), write_to=str(HERE / f'{NAME}.pdf'))
    im = Image.open(HERE / f'{NAME}.png')
    ImageOps.grayscale(im).resize((1600, 900)).save(HERE / f'{NAME}-grayscale-preview.png')
    library = HERE.parents[1] / 'figures'
    im.save(library / 'research-target-hybrid-retrieval-polished-v4.png')
    print('Validated FigureSpec; exported PNG, SVG, PDF and grayscale preview.')


if __name__ == '__main__':
    main()
