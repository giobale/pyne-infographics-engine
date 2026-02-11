"""SalesBanana CLI entry point."""

import argparse
import sys

from src.pipeline import generate_diagram


def main() -> None:
    parser = argparse.ArgumentParser(
        description="SalesBanana: AI-powered diagram generation pipeline",
    )
    parser.add_argument(
        "brief",
        nargs="?",
        help="Diagram brief (natural language). If omitted, reads from stdin.",
    )
    parser.add_argument(
        "--rounds",
        type=int,
        default=None,
        help="Override max refinement rounds (default: from .env)",
    )

    args = parser.parse_args()

    # Get brief from argument or stdin
    if args.brief:
        brief = args.brief
    elif not sys.stdin.isatty():
        brief = sys.stdin.read().strip()
    else:
        parser.error("Please provide a brief as an argument or pipe it via stdin.")

    if not brief:
        parser.error("Brief cannot be empty.")

    # Run pipeline
    result = generate_diagram(brief, max_rounds=args.rounds)

    # Output summary
    print(f"\nDiagram generated successfully!")
    print(f"  Output:    {result.image_path}")
    print(f"  Rounds:    {result.rounds_taken}")
    print(f"  Approved:  {result.approved}")
    print(f"  Run dir:   {result.run_dir}")


if __name__ == "__main__":
    main()
