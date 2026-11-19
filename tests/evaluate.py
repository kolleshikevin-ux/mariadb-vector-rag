"""Evaluate semantic retrieval with category-based Hit@k."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Iterable

# `python tests/evaluate.py` puts tests/ (not src/) at sys.path[0].
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from search import semantic_search  # noqa: E402

TESTS = [
    {
        "question": "How does a CPU execute instructions?",
        "expected_categories": {"Computer Architecture"},
    },
    {
        "question": "What is mutual exclusion?",
        "expected_categories": {"Operating Systems"},
    },
    {
        "question": "What is a relational database?",
        "expected_categories": {"Databases"},
    },
    {
        "question": "Explain TCP/IP",
        "expected_categories": {"Networking"},
    },
    {
        "question": "What is a hash table?",
        "expected_categories": {"Algorithms"},
    },
    {
        "question": "How does virtual memory work?",
        "expected_categories": {"Operating Systems"},
    },
    {
        "question": "What are SQL joins?",
        "expected_categories": {"Databases"},
    },
    {
        "question": "Explain instruction pipelining",
        "expected_categories": {"Computer Architecture"},
    },
]


def hit_at_k(rows: Iterable[tuple], expected_categories: set[str], k: int) -> bool:
    """A query is a hit when any expected category appears in the first k rows."""
    if type(k) is not int or k < 1:
        raise ValueError("k debe ser un entero mayor que cero.")
    return any(row[2] in expected_categories for row in list(rows)[:k])


def evaluate(max_k: int = 5, output: str | Path | None = "reports/evaluation.json") -> dict:
    if type(max_k) is not int or max_k < 1:
        raise ValueError("max_k debe ser un entero mayor que cero.")

    metric_ks = sorted({k for k in (1, 3, 5, max_k) if k <= max_k})
    hits = {k: 0 for k in metric_ks}
    detailed_results = []

    for test in TESTS:
        rows = semantic_search(test["question"], limit=max_k)
        expected = test["expected_categories"]
        for k in metric_ks:
            if hit_at_k(rows, expected, k):
                hits[k] += 1

        categories = [row[2] for row in rows]
        print(test["question"])
        print("Expected category:", ", ".join(sorted(expected)))
        print(f"Top categories (k={max_k}):", categories)
        print("Hit@k:", {k: hit_at_k(rows, expected, k) for k in metric_ks})
        print()

        detailed_results.append(
            {
                "question": test["question"],
                "expected_categories": sorted(expected),
                "retrieved": [
                    {
                        "id": row[0],
                        "title": row[1],
                        "category": row[2],
                        "distance": float(row[4]) if row[4] is not None else None,
                    }
                    for row in rows
                ],
                "hits": {f"hit_at_{k}": hit_at_k(rows, expected, k) for k in metric_ks},
            }
        )

    metrics = {
        f"Hit@{k}": {
            "hits": hits[k],
            "total": len(TESTS),
            "rate": hits[k] / len(TESTS),
        }
        for k in metric_ks
    }

    print("Evaluation summary:")
    for name, metric in metrics.items():
        print(f"{name}: {metric['hits']}/{metric['total']} = {metric['rate']:.2%}")

    report = {"metrics": metrics, "questions": detailed_results}
    if output:
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nSaved evaluation report to: {output_path}")

    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Evalúa semantic search con Hit@k.")
    parser.add_argument("--max-k", type=int, default=5, help="Cantidad máxima de resultados por pregunta.")
    parser.add_argument(
        "--output",
        default="reports/evaluation.json",
        help="Ruta del JSON de resultados; usa --output '' para no guardarlo.",
    )
    args = parser.parse_args()
    evaluate(max_k=args.max_k, output=args.output or None)


if __name__ == "__main__":
    main()
