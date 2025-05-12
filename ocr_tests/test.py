from pathlib import Path
from typing import Any, Mapping
import json
import logging
import sys

from configuration import Configuration
from text_extractor import TextExtractor
from message_builder import MessageBuilder
from logger import logger


NUM_RUNS = 1  # Number of times to process each image


def main() -> None:
    """Run OCR entity‑matching test NUM_RUNS times per image and summarise results."""
    logger.setLevel(logging.DEBUG)

    cfg = Configuration()
    extractor = TextExtractor(cfg, logger)
    message_builder = MessageBuilder(cfg, logger)

    # ── Load the expected entity map ──────────────────────────────────────────
    map_path = Path(cfg.system_path / "ocr_tests" / "map.json")
    with map_path.open("r", encoding="utf-8") as fp:
        entity_map: Mapping[str, Any] = json.load(fp)

    # Prepare result counters: {img_name: {"success": int, "failure": int}}
    results: dict[str, dict[str, int]] = {
        img_name: {"success": 0, "failure": 0} for img_name in entity_map
    }

    # ── Run the tests ────────────────────────────────────────────────────────
    for run in range(1, NUM_RUNS + 1):
        logger.info("▶️  Run %d/%d", run, NUM_RUNS)

        for img_name, expected in entity_map.items():
            img_path = Path(cfg.system_path / "ocr_tests" / img_name)

            # Extract text from the image and attempt entity match
            text = extractor.extract_text_from_file(img_path)
            matched_entity = message_builder.match_entity(text)

            # Determine pass/fail
            passed: bool
            if expected is None:
                passed = matched_entity is None
            else:
                passed = matched_entity is not None and matched_entity.get("name") == expected

            # Update counters
            if passed:
                results[img_name]["success"] += 1
                logger.debug(
                    "✅ PASS | file=%s run=%d matched=%s", img_name, run, getattr(matched_entity, "name", None)
                )
            else:
                results[img_name]["failure"] += 1
                logger.error(
                    "❌ FAIL | file=%s run=%d expected=%s got=%s",
                    img_name,
                    run,
                    expected,
                    getattr(matched_entity, "name", None),
                )

    # ── Print summary ────────────────────────────────────────────────────────
    total_success = total_failure = 0
    print("\n\n📊 Test Summary (each file processed", NUM_RUNS, "times):")
    print("─" * 72)
    for img_name, counts in results.items():
        success, failure = counts["success"], counts["failure"]
        total_success += success
        total_failure += failure
        rate = success / NUM_RUNS * 100
        print(f"{img_name:30s}  ✅ {success:2d}  ❌ {failure:2d}  ({rate:5.1f}%)")

    overall_runs = NUM_RUNS * len(entity_map)
    overall_rate = total_success / overall_runs * 100 if overall_runs else 0.0

    print("─" * 72)
    print(f"OVERALL: ✅ {total_success}/{overall_runs}  ({overall_rate:.1f}% passed)")

    # Exit with non‑zero status if any failures occurred
    if total_failure:
        logger.warning("Some tests failed → exiting with status 1")
        sys.exit(1)

    print("\n✅ All checks passed across all runs!")


if __name__ == "__main__":
    main()
