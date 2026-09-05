from __future__ import annotations

import argparse
import json
from pathlib import Path

from .answering import answer
from .evaluation import run_evaluation
from .index import build_index
from .lsr_evaluation import run_lsr_evaluation
from .models import StatuteQuery
from .qa_evaluation import run_qa_evaluation
from .question_analysis import parse_question_file
from .search import search


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m draftly.retrieval")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build", help="Build or refresh the statutes-only BM25 index.")
    build_parser.add_argument("--force", action="store_true", help="Rebuild even if the corpus fingerprint matches.")

    search_parser = subparsers.add_parser("search", help="Search statutes and amendments.")
    search_parser.add_argument("query", help="Question or legal lookup query.")
    search_parser.add_argument("--topic", dest="topic_slug", help="Hard filter to a curriculum topic slug.")
    search_parser.add_argument("--kind", choices=["statute", "amendment"], action="append", help="Filter by document type.")
    search_parser.add_argument("--source-id", help="Filter to one source ID, e.g. SRC001.")
    search_parser.add_argument("--limit", type=int, default=8)

    ask_parser = subparsers.add_parser("ask", help="Generate a bounded, cited statutes-only answer.")
    ask_parser.add_argument("query", help="Question, including a complete multi-part exam question if needed.")
    ask_parser.add_argument("--limit", type=int, default=12)

    subparsers.add_parser("evaluate", help="Run development retrieval evaluation.")

    lsr_parser = subparsers.add_parser(
        "evaluate-lsr",
        help="Run the IL-PCSR-derived legal statute retrieval (LSR) evaluation.",
    )
    lsr_parser.add_argument(
        "--rerank",
        action="store_true",
        help="Add a bounded Gemini re-rank pass over each query's retrieved candidates.",
    )

    serve_parser = subparsers.add_parser("serve", help="Run the statute retrieval FastAPI service.")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8000)
    serve_parser.add_argument("--reload", action="store_true")

    questions_parser = subparsers.add_parser(
        "evaluate-questions",
        help="Run the questions.md robustness harness without claiming legal correctness.",
    )
    questions_parser.add_argument("--questions", default="src/questions.md")
    questions_parser.add_argument("--output", default="evaluation/runs/statute-qa-v2")
    questions_parser.add_argument("--with-answers", action="store_true")
    questions_parser.add_argument("--resume", action="store_true", help="Resume from results.partial.jsonl.")
    questions_parser.add_argument(
        "--question-id",
        action="append",
        help="Evaluate only a matching question ID; repeat for multiple IDs.",
    )

    args = parser.parse_args()
    if args.command == "build":
        print(json.dumps(build_index(force=args.force).to_dict(), indent=2))
    elif args.command == "search":
        hits = search(
            StatuteQuery(
                text=args.query,
                topic_slug=args.topic_slug,
                kinds=tuple(args.kind) if args.kind else None,
                source_id=args.source_id,
                limit=args.limit,
            )
        )
        print(json.dumps([hit.to_dict(include_text=False) for hit in hits], indent=2))
    elif args.command == "ask":
        response = answer(StatuteQuery(text=args.query, limit=args.limit))
        print(json.dumps(response.to_dict(), indent=2, ensure_ascii=False))
    elif args.command == "evaluate":
        print(json.dumps(run_evaluation(), indent=2))
    elif args.command == "evaluate-lsr":
        print(json.dumps(run_lsr_evaluation(rerank=args.rerank), indent=2))
    elif args.command == "serve":
        import uvicorn

        uvicorn.run("draftly.retrieval.api:app", host=args.host, port=args.port, reload=args.reload)
    elif args.command == "evaluate-questions":
        questions = parse_question_file(Path(args.questions))
        if args.question_id:
            selected_ids = set(args.question_id)
            questions = tuple(question for question in questions if question.question_id in selected_ids)
            missing_ids = selected_ids - {question.question_id for question in questions}
            if missing_ids:
                parser.error(f"Unknown question IDs: {', '.join(sorted(missing_ids))}")
        metrics = run_qa_evaluation(
            questions,
            Path(args.output),
            retrieve=lambda text: search(StatuteQuery(text=text, limit=10)),
            answer=answer if args.with_answers else None,
            mode="full_answer" if args.with_answers else "retrieval_only",
            config={"corpus": "statutes-and-amendments-only", "gold_status": "unverified"},
            resume=args.resume,
        )
        print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
