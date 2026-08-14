"""Capture and blind the existing COMM-002/GROUP-001 evaluation package.

This is an evaluation-only runner. It uses ChatEngine for both arms and does
not expose an HTTP runtime switch or alter the production default.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "current-state" / "human-eval-001"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engines.ai.chatbot.chat_engine import ChatEngine

COMM_CASES = [
    ("01", "I finally have a quiet weekend. Any simple ideas for making it feel good?"),
    ("02", "I have people around me, but lately I still feel very alone. I do not know how to talk about it."),
    ("03", "Give me a straight answer: should I change this plan or keep going?"),
    ("04", "What is D9 in a birth chart? Please explain it simply."),
    ("05", "The D9 lord is afflicted, but MD/AD activation looks weak. How should I weigh those signals?"),
    ("06", "What is a race condition? Explain it without assuming I am a programmer."),
    ("07", "We need an idempotent migration, but the deploy can overlap with an older worker. What risks should I review?"),
    ("08", "Yaar, scene kya hai? Seedha batao, ye plan kaam karega ya nahi?"),
    ("09", "I have recurring headaches and fatigue. Can astrology tell me whether this is serious?"),
    ("10", "Compare these two strategies using drawdown, liquidity, and risk-on versus risk-off behavior."),
]

GROUP_CASES = [
    ("01", "RAVI: I want to understand my daughter's career chart.\nVEDA: [answer the parent while keeping speaker and chart subject separate]", {"speaker_id": "ravi", "speaker_name": "Ravi", "chart_subject_id": "daughter", "subject_label": "Ravi's daughter", "addressed_to": ["VEDA"]}),
    ("02", "ANIKA: D9 timing supports the relationship this year.\nDEV: I disagree; the activation is too weak.\nVEDA: [synthesize both astrologers neutrally]", {"speaker_id": "dev", "speaker_name": "Dev", "addressed_to": ["VEDA"]}),
    ("03", "RAVI: I prefer lower drawdown.\nMEENA: I prefer liquidity even if returns are lower.\nSANJEEV: I am undecided.\nVEDA: [support the group decision without assigning views incorrectly]", {"speaker_id": "sanjeev", "speaker_name": "Sanjeev", "addressed_to": ["VEDA"]}),
    ("04", "MEENA: Yaar, mujhe lagta hai plan risky hai.\nRAVI: Nahi, scene manageable hai.\nMEENA: Veda, tum kya sochti ho?", {"speaker_id": "meena", "speaker_name": "Meena", "addressed_to": ["VEDA"]}),
    ("05", "RAVI: I focus on valuation.\nMEENA: I focus on momentum.\nGROUP: Veda, please give us a neutral summary.", {"speaker_id": "group", "speaker_name": "Group", "addressed_to": ["VEDA"]}),
    ("06", "RAVI: You keep ignoring the risk.\nMEENA: That is unfair.\nRAVI: You are right, I am sorry.\nVEDA: [respond only if useful and de-escalate]", {"speaker_id": "group", "speaker_name": "Group", "addressed_to": ["VEDA"]}),
    ("07", "RAVI: Meena, what do you think about the timing?\nMEENA: I would wait another week.", {"speaker_id": "ravi", "speaker_name": "Ravi", "addressed_to": ["Meena"]}),
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def choose_provider() -> str:
    probe = ChatEngine()
    providers = probe._active_providers()
    if not providers:
        raise RuntimeError("No configured chat provider is available")
    return providers[0]["name"]


def capture(message: str, mode: str, provider: str, *, group_context: dict | None = None, engine: ChatEngine | None = None, attempts: int = 4) -> dict:
    last_error = "unknown capture failure"
    for attempt in range(attempts):
        engine = engine or ChatEngine()
        engine.history = []
        response = engine.chat(message, group_context=group_context, evaluation_mode=mode, evaluation_provider=provider)
        metadata = dict(engine.last_generation)
        if response.strip() and "temporarily unavailable" not in response.lower() and "rate-limited" not in response.lower():
            return {"mode": mode, "captured_at": now(), "response": response, "generation": metadata, "group_context_used": bool(group_context)}
        last_error = response[:120]
        if attempt + 1 < attempts:
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"invalid captured response for {mode}: {last_error!r}")


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--provider", default=None)
    args = parser.parse_args()
    seed = args.seed if args.seed is not None else random.SystemRandom().randrange(1, 2**63)
    rng = random.Random(seed)
    provider = args.provider or choose_provider()
    engine = ChatEngine()

    captured: dict[str, dict] = {}
    for case_id, prompt in COMM_CASES:
        captured[case_id] = {
            "case_id": case_id,
            "prompt": prompt,
            "baseline": capture(prompt, "BASELINE_EVAL", provider, engine=engine),
            "adaptive": capture(prompt, "ADAPTIVE_EVAL", provider, engine=engine),
        }
        time.sleep(2)

    group_captured: dict[str, dict] = {}
    for scenario_id, transcript, context in GROUP_CASES:
        group_captured[scenario_id] = {
            "scenario_id": scenario_id,
            "transcript": transcript,
            "response": capture(transcript, "ADAPTIVE_EVAL", provider, group_context=context, engine=engine),
        }

    mapping = {}
    founder_cases = []
    for case_id, record in captured.items():
        order = ["baseline", "adaptive"]
        rng.shuffle(order)
        mapping[case_id] = {"A": order[0].upper(), "B": order[1].upper()}
        founder_cases.append({
            "case_id": case_id,
            "prompt": record["prompt"],
            "response_a": record[order[0]]["response"],
            "response_b": record[order[1]]["response"],
        })

    created = now()
    write_json(OUT / "capture.json", {"evaluation_id": "VEDA-HUMAN-EVAL-001-R1", "created_at": created, "provider": provider, "cases": captured, "group_scenarios": group_captured})
    write_json(OUT / "hidden-mapping.json", {"evaluation_id": "VEDA-HUMAN-EVAL-001-R1", "seed": seed, "mapping": mapping})
    write_json(OUT / "manifest.json", {"evaluation_id": "VEDA-HUMAN-EVAL-001-R1", "repository_commit": "WORKTREE_CAPTURE", "created_at": created, "provider": provider, "model": captured["01"]["baseline"]["generation"].get("model"), "cases": 10, "group_scenarios": 7, "randomization_seed": seed, "hidden_mapping": "hidden-mapping.json", "founder_package": "FOUNDER_EVALUATION.md"})

    lines = ["# VEDA Founder Evaluation", "", "Status: `FOUNDER_RATINGS_REQUIRED`", "", "Read each prompt and the two unlabeled responses. Do not inspect repository files or ask for their source.", ""]
    for item in founder_cases:
        lines += [f"## CASE {item['case_id']}", "", "**PROMPT**", item["prompt"], "", "**RESPONSE A**", item["response_a"], "", "**RESPONSE B**", item["response_b"], "", "**RATINGS - RESPONSE A**", "Precision: __ / 5  |  Relevance: __ / 5  |  Naturalness: __ / 5  |  Depth: __ / 5  |  Clarity: __ / 5", "Tone Appropriateness: __ / 5  |  Non-Repetition: __ / 5  |  Confidence Quality: __ / 5  |  Overall Usefulness: __ / 5", "Chart Specificity (if relevant): __ / 5  |  Timing Usefulness (if relevant): __ / 5", "", "**RATINGS - RESPONSE B**", "Precision: __ / 5  |  Relevance: __ / 5  |  Naturalness: __ / 5  |  Depth: __ / 5  |  Clarity: __ / 5", "Tone Appropriateness: __ / 5  |  Non-Repetition: __ / 5  |  Confidence Quality: __ / 5  |  Overall Usefulness: __ / 5", "Chart Specificity (if relevant): __ / 5  |  Timing Usefulness (if relevant): __ / 5", "", "Preferred: A / B / TIE", "Surprisingly Useful Insight: A / B / BOTH / NEITHER", "Comment: ", ""]
    lines += ["## GROUP-001 SCENARIOS", ""]
    for item in group_captured.values():
        lines += [f"### SCENARIO {item['scenario_id']}", "", item["transcript"], "", "**VEDA**", item["response"]["response"], "", "Speaker Attribution: __ / 5  |  Reply-To Understanding: __ / 5  |  Addressee Understanding: __ / 5", "Topic Understanding: __ / 5  |  Viewpoint Attribution: __ / 5  |  Neutrality: __ / 5", "Group Understanding: __ / 5  |  Participation Judgment: __ / 5  |  Response Relevance: __ / 5", "Naturalness: __ / 5  |  Overall Usefulness: __ / 5", "Comment: ", ""]
    (OUT / "FOUNDER_EVALUATION.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"provider": provider, "model": captured["01"]["baseline"]["generation"].get("model"), "cases": 10, "group_scenarios": 7, "seed": seed}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
