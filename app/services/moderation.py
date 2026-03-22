"""Content moderation service.

Blocks sexual harassment, hate speech, threats, self-harm, and other
harmful content from both user inputs and bot outputs.
"""

from __future__ import annotations
import re
import logging
from dataclasses import dataclass
from app.config import settings

logger = logging.getLogger(__name__)

BLOCKED_MESSAGE = (
    "Your message was blocked by our safety filter. "
    "This platform does not allow harassment, hate speech, threats, "
    "sexually explicit content, or other harmful material. "
    "Please rephrase your message respectfully."
)

BLOCKED_OUTPUT_MESSAGE = (
    "The response was blocked by our safety filter. "
    "Please try rephrasing your question."
)


@dataclass
class ModerationResult:
    blocked: bool
    category: str  # which category triggered the block ("" if not blocked)
    matched: str   # the pattern/keyword that matched ("" if not blocked)


# ── Pattern categories ──
# Each category has a list of regex patterns (case-insensitive).
# Patterns are designed to catch harmful intent while minimizing false positives.

_PATTERNS: dict[str, list[str]] = {
    "sexual_harassment": [
        r"\b(send\s*(me\s*)?(nudes?|pics|naked|topless))\b",
        r"\b(show\s*(me\s*)?(your\s*)?(body|boobs|breasts|ass|butt|tits))\b",
        r"\b(wanna\s*(have\s*)?sex|let'?s\s*(have\s*)?sex|sex\s*with\s*(me|you))\b",
        r"\b(suck\s*my|blow\s*me|jerk\s*(me|off))\b",
        r"\b(i('?m|'?ll)\s*(gonna\s*)?(rape|grope|molest|touch\s*you))\b",
        r"\b(take\s*(off|your)\s*(clothes|pants|shirt|bra|underwear))\b",
        r"\b(sexual\s*favor|sleep\s*with\s*me)\b",
        r"\b(d[i1]ck\s*pic|c[o0]ck\s*pic)\b",
        r"\b(you('?re)?\s*(so\s*)?(hot|sexy|fuckable|bangable))\b",
        r"\b(sit\s*on\s*my\s*(face|lap|dick))\b",
    ],
    "sexually_explicit": [
        r"\b(porn(ography)?|hentai|xxx|nsfw\s*(content|image|video))\b",
        r"\b(write\s*(me\s*)?(erotica|smut|porn|sex\s*story))\b",
        r"\b(erotic\s*(story|fiction|roleplay))\b",
        r"\b(sexual\s*(roleplay|fantasy|scenario))\b",
        r"\b(masturbat(e|ion|ing))\b",
        r"\b(orgasm|cum\s*on|cumshot|creampie)\b",
        r"\b(f[u\*]ck\s*(me|her|him|them))\b",
    ],
    "hate_speech": [
        r"\b(kill\s*all\s*(jews|muslims|christians|blacks|whites|gays|trans))\b",
        r"\b(racial\s*superiority|white\s*power|master\s*race)\b",
        r"\b(ethnic\s*cleansing|genocide\s*(is\s*)?good)\b",
        r"\b(n[i1]gg[e3]r|f[a4]gg[o0]t|k[i1]ke|sp[i1]c|ch[i1]nk|wetback)\b",
        r"\b(subhuman|untermensch)\b",
        r"\b(gas\s*the\s*(jews|[a-z]+))\b",
        r"\b((all\s*)?(women|men|gays|trans)\s*(are|should)\s*(die|be\s*killed|burn))\b",
    ],
    "threats_violence": [
        r"\b(i('?m|'?ll|'?will)\s*(gonna\s*)?(kill|shoot|stab|murder|bomb)\s*(you|them|him|her|everyone))\b",
        r"\b(how\s*to\s*(make\s*a\s*)?bomb)\b",
        r"\b(how\s*to\s*(kill|poison|murder)\s*(someone|a\s*person|my))\b",
        r"\b(school\s*shoot(ing|er)?|mass\s*shoot(ing|er)?)\b",
        r"\b(i('?ll)?\s*find\s*(where\s*)?you\s*(live|are))\b",
        r"\b(death\s*threat|i('?ll)?\s*end\s*you)\b",
        r"\b(torture|dismember|behead)\b",
    ],
    "self_harm": [
        r"\b(how\s*to\s*(commit\s*)?suicide)\b",
        r"\b(best\s*way\s*to\s*(die|kill\s*myself))\b",
        r"\b(help\s*me\s*(die|end\s*(it|my\s*life)))\b",
        r"\b(cut\s*my(self|\s*wrists?))\b",
        r"\b(overdose\s*(on|instructions))\b",
    ],
    "child_exploitation": [
        r"\b(child\s*(porn|sex|nude|naked))\b",
        r"\b(cp\s*link|pedo\s*(content|material))\b",
        r"\b(sex\s*with\s*(a\s*)?(child|kid|minor|underage))\b",
        r"\b(loli|shota)\s*(porn|hentai|nsfw)\b",
    ],
    "doxxing_privacy": [
        r"\b(what('?s)?\s*(his|her|their)\s*(home\s*)?address)\b",
        r"\b(find\s*(someone'?s?|their)\s*(address|phone|ssn|social\s*security))\b",
        r"\b(dox(x)?(ing)?|swat(t)?(ing)?)\b",
        r"\b(leak\s*(their|someone'?s?)\s*(nudes?|photos?|info))\b",
    ],
}

# Compile all patterns once at import time
_COMPILED: dict[str, list[re.Pattern]] = {
    cat: [re.compile(p, re.IGNORECASE) for p in patterns]
    for cat, patterns in _PATTERNS.items()
}

# Optional: additional custom blocked words from .env
_custom_words: list[re.Pattern] = []


def _init_custom_words():
    global _custom_words
    raw = settings.moderation_custom_blocked.strip()
    if raw:
        words = [w.strip() for w in raw.split(",") if w.strip()]
        _custom_words = [re.compile(rf"\b{re.escape(w)}\b", re.IGNORECASE) for w in words]


def check(text: str) -> ModerationResult:
    """Check text against all moderation patterns. Returns result."""
    if not text or not settings.moderation_enabled:
        return ModerationResult(blocked=False, category="", matched="")

    # Init custom words on first call
    if settings.moderation_custom_blocked and not _custom_words:
        _init_custom_words()

    # Normalize text for matching
    normalized = text.lower().strip()

    # Check built-in categories
    for category, patterns in _COMPILED.items():
        for pattern in patterns:
            match = pattern.search(normalized)
            if match:
                logger.warning(f"Moderation blocked [{category}]: '{match.group()}'")
                return ModerationResult(
                    blocked=True,
                    category=category,
                    matched=match.group(),
                )

    # Check custom blocked words
    for pattern in _custom_words:
        match = pattern.search(normalized)
        if match:
            logger.warning(f"Moderation blocked [custom]: '{match.group()}'")
            return ModerationResult(
                blocked=True,
                category="custom_blocked",
                matched=match.group(),
            )

    return ModerationResult(blocked=False, category="", matched="")


async def log_violation(
    user_id: str,
    user_email: str,
    text: str,
    category: str,
    matched: str,
    direction: str,  # "input" or "output"
) -> None:
    """Log a moderation violation to PocketBase."""
    try:
        from app.services.pocketbase import pb
        token = await pb._admin_auth()
        import httpx
        async with httpx.AsyncClient() as client:
            data = {
                "user_email": user_email,
                "text_snippet": text[:500],
                "category": category,
                "matched_pattern": matched,
                "direction": direction,
            }
            if user_id:
                data["user"] = user_id
            await client.post(
                f"{pb.base_url}/api/collections/moderation_logs/records",
                json=data,
                headers={"Authorization": f"Bearer {token}"},
            )
    except Exception as e:
        logger.error(f"Failed to log moderation violation: {e}")
