# Official PaperBanana on this machine

The official [PaperBanana repository](https://github.com/dwzhu-pku/PaperBanana)
is checked out at `third_party/PaperBanana/`. The checkout and its Python 3.12
virtual environment are local and ignored by Draftly's Git repository. The
launcher reads `GEMINI_API_KEY` from the ignored root `.env` and supplies it to
PaperBanana as `GOOGLE_API_KEY` for that process. The key is not copied into
PaperBanana's config or the figures.

On 29 September 2026, the `check` command passed, the local Gradio page
returned HTTP 200, and an official `vanilla` pipeline call saved a 2752 x 1536
PNG at `tmp/paperbanana-smoke.png`. That image is a connectivity test in an
ignored scratch directory, not a reviewed paper figure. The planner, stylist,
and critic modes are installed but were not exercised in this smoke test.

From the `draftly-research` root, check the installation:

```powershell
third_party\PaperBanana\.venv\Scripts\python.exe scripts\paperbanana_local.py check
```

Launch the official Gradio interface at <http://127.0.0.1:7860>:

```powershell
third_party\PaperBanana\.venv\Scripts\python.exe scripts\paperbanana_local.py serve
```

For a one-image command-line run, put a figure specification in a UTF-8 text
file and run:

```powershell
third_party\PaperBanana\.venv\Scripts\python.exe scripts\paperbanana_local.py generate `
  --text-file figures\paperbanana-input.txt `
  --caption "Caption describing the figure" `
  --output figures\ai_generated\figure.png
```

The command uses PaperBanana's planner, stylist, and visualizer, with one
candidate and no reference dataset. `--mode dev_full` also enables the critic
loop. The official template's default models are `gemini-3.1-pro-preview` for
text planning and `gemini-3.1-flash-image-preview` for images; `--main-model`
and `--image-model` override them. API calls use the configured Gemini account
and may incur provider charges. Generated diagrams still need a human check for
labels, arrows, and factual accuracy before publication.

To rebuild the local installation if needed:

```powershell
git clone https://github.com/dwzhu-pku/PaperBanana.git third_party/PaperBanana
uv venv --python 3.12 third_party/PaperBanana/.venv
uv pip install -r third_party/PaperBanana/requirements.txt `
  --python third_party/PaperBanana/.venv/Scripts/python.exe
```
