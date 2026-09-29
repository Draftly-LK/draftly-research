"""Run the official PaperBanana checkout with Draftly's local Gemini key.

The key stays in the repository's ignored .env and is passed through the
process environment. No credential is written into PaperBanana's config.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import runpy
import sys
from pathlib import Path

from dotenv import dotenv_values


ROOT = Path(__file__).resolve().parents[1]
PAPERBANANA = ROOT / "third_party" / "PaperBanana"
DEFAULT_IMAGE_MODEL = "gemini-3.1-flash-image-preview"
DEFAULT_MAIN_MODEL = "gemini-3.1-pro-preview"


def prepare() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    if not (PAPERBANANA / "app.py").is_file():
        raise SystemExit(
            "Official PaperBanana checkout missing. See docs/paperbanana-local.md."
        )
    key = dotenv_values(ROOT / ".env").get("GEMINI_API_KEY")
    if not key:
        raise SystemExit("GEMINI_API_KEY is missing from the ignored root .env file.")
    for provider_key in ("OPENROUTER_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"):
        os.environ.pop(provider_key, None)
    os.environ["GOOGLE_API_KEY"] = key
    os.chdir(PAPERBANANA)
    sys.path.insert(0, str(PAPERBANANA))


async def generate(args: argparse.Namespace) -> None:
    from app import create_sample_inputs, get_final_image, process_parallel_candidates

    content = args.text_file.read_text(encoding="utf-8")
    if not content.strip():
        raise SystemExit("The input text file is empty.")
    inputs = create_sample_inputs(
        content,
        args.caption,
        aspect_ratio=args.aspect_ratio,
        figure_size=args.figure_size,
        num_copies=1,
        max_critic_rounds=args.critic_rounds,
    )
    results = await process_parallel_candidates(
        inputs,
        exp_mode=args.mode,
        retrieval_setting="none",
        main_model_name=args.main_model,
        image_gen_model_name=args.image_model,
    )
    if not results:
        raise SystemExit("PaperBanana returned no results.")
    image, _ = get_final_image(results[0], args.mode)
    if image is None:
        raise SystemExit("PaperBanana returned no image. Check the provider error above.")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    image.save(args.output, format="PNG")
    print(f"Saved image: {args.output} ({image.width} x {image.height})")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check", help="Check the checkout, key and dependencies locally")
    sub.add_parser("serve", help="Start the official Gradio app on localhost:7860")
    generation = sub.add_parser("generate", help="Generate one image through PaperBanana")
    generation.add_argument("--text-file", type=Path, required=True)
    generation.add_argument("--caption", required=True)
    generation.add_argument("--output", type=Path, required=True)
    generation.add_argument("--mode", default="dev_planner_stylist", choices=[
        "vanilla", "dev_planner", "dev_planner_stylist", "dev_planner_critic",
        "dev_full", "demo_planner_critic", "demo_full",
    ])
    generation.add_argument("--main-model", default=DEFAULT_MAIN_MODEL)
    generation.add_argument("--image-model", default=DEFAULT_IMAGE_MODEL)
    generation.add_argument("--aspect-ratio", default="16:9")
    generation.add_argument("--figure-size", default="7-9cm")
    generation.add_argument("--critic-rounds", type=int, default=1)
    args = parser.parse_args()
    if args.command == "generate":
        args.text_file = args.text_file.resolve()
        args.output = args.output.resolve()
    prepare()
    if args.command == "check":
        import app  # noqa: F401 - imports the official app and all dependencies

        print("PaperBanana checkout, dependencies and Gemini key are ready.")
    elif args.command == "serve":
        runpy.run_path(str(PAPERBANANA / "app.py"), run_name="__main__")
    else:
        asyncio.run(generate(args))


if __name__ == "__main__":
    main()
