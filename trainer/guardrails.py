"""Rule-based guardrails for the trainer agent.

Input checks run before the model sees a message. Output checks run on the
model's reply before it goes back to the member. Everything here is
deterministic, so it is cheap, fast and easy to test without model calls.
"""
import re
from dataclasses import dataclass

EMERGENCY_REPLY = (
    "That sounds serious. Stop training now and contact a doctor or local "
    "emergency services. I can help with your plan once you are cleared."
)
MEDICAL_REPLY = (
    "I can't diagnose conditions or advise on medication or supplements. "
    "Please check with a doctor or pharmacist. I can adjust your training "
    "around what they tell you."
)
EXTREME_DIET_REPLY = (
    "I can't recommend extreme dieting or fasting plans. A registered "
    "dietitian can set safe targets, and I can build your training around them."
)
INJECTION_REPLY = (
    "I can't change my instructions or share them. I'm happy to help with "
    "your training, workouts or fitness questions."
)
OUTPUT_DISCLAIMER = (
    "\n\nNote: if pain continues or gets worse, stop and see a medical professional."
)
LEAK_REPLY = "I can't share that. What would you like to work on in your training?"

# Fragments that only appear in the system prompt. If one shows up in a reply, it leaked.
PROMPT_MARKERS = ("CRITICAL INSTRUCTION", "## Your Tools", "## Your Behavior Rules")

_EMERGENCY = re.compile(
    r"chest (pain|pressure|tightness)|can'?t breathe|cannot breathe|short(ness)? of breath"
    r"|heart attack|faint(ed|ing)?|passed out|blacking out|numb(ness)? (in|down)"
    r"|severe (pain|bleeding)|coughing (up )?blood|suicid|want to die",
    re.I,
)
_MEDICAL = re.compile(
    r"\bdiagnos(e|is)\b|\bprescri(be|ption)\b|\bdosage\b|\bsteroids?\b|\banabolic\b"
    r"|\b(sarms?|clenbuterol|trenbolone|testosterone (shot|injection|cycle))\b"
    r"|what medication|should i take (a )?(pill|medic)",
    re.I,
)
_EXTREME_DIET = re.compile(
    r"\bstarv(e|ing)\b|(eat|consume) (only )?(under |less than )?[1-7]\d\d (cal|kcal)"
    r"|(water|juice) fast for \d+ days|purge|laxatives? (to|for) (lose|weight)",
    re.I,
)
_INJECTION = re.compile(
    r"ignore (all |your |the )?(previous|prior|above|earlier) (instructions|rules|prompt)"
    r"|disregard (all |your |the )?(previous|prior|above) (instructions|rules)"
    r"|(reveal|show|print|repeat|tell me) (me )?(your|the) (system )?(prompt|instructions)"
    r"|you are now (a|an|in)\b|developer mode|jailbreak",
    re.I,
)
_PAIN_WORDS = re.compile(r"\b(pain|painful|injur(y|ed)|sprain|strain|torn|swelling|dizz(y|iness))\b", re.I)


@dataclass
class GuardResult:
    allowed: bool
    category: str = "ok"
    reply: str = ""


def check_input(message: str) -> GuardResult:
    """Return allowed=False with a canned reply when a message should not reach the model."""
    text = message or ""
    # Order matters: an emergency outranks everything else.
    if _EMERGENCY.search(text):
        return GuardResult(False, "emergency", EMERGENCY_REPLY)
    if _INJECTION.search(text):
        return GuardResult(False, "prompt_injection", INJECTION_REPLY)
    if _EXTREME_DIET.search(text):
        return GuardResult(False, "extreme_diet", EXTREME_DIET_REPLY)
    if _MEDICAL.search(text):
        return GuardResult(False, "medical", MEDICAL_REPLY)
    return GuardResult(True)


def check_output(reply: str) -> GuardResult:
    """Return the reply to send. allowed=False means it was replaced or changed."""
    text = reply or ""
    if any(marker in text for marker in PROMPT_MARKERS):
        return GuardResult(False, "prompt_leak", LEAK_REPLY)
    if _PAIN_WORDS.search(text) and OUTPUT_DISCLAIMER.strip() not in text:
        return GuardResult(False, "disclaimer_added", text + OUTPUT_DISCLAIMER)
    return GuardResult(True, "ok", text)


def text_of(content) -> str:
    """Claude replies can be a string or a list of content blocks. Return the text."""
    if isinstance(content, str):
        return content
    parts = []
    for block in content or []:
        if isinstance(block, dict) and block.get("type") == "text":
            parts.append(block.get("text", ""))
        elif isinstance(block, str):
            parts.append(block)
    return "".join(parts)
