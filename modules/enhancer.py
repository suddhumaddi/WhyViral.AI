# No external dependencies required — standard library only.

import random
import re

# ---------------------------------------------------------------------------
# Keyword banks (reuse same philosophy as analyzer.py)
# ---------------------------------------------------------------------------

EMOTIONAL_WORDS = {
    "can't", "cant", "couldn't", "hard", "fail", "failed", "failure",
    "struggle", "struggled", "struggling", "difficult", "impossible",
    "pain", "hurt", "fear", "afraid", "scared", "lost", "broken",
    "gave up", "quit", "alone", "hopeless", "desperate",
    "success", "overcome", "overcame", "achieve", "achieved", "proud",
    "victory", "breakthrough", "changed", "transformed", "grateful",
    "incredible", "amazing", "unstoppable",
}

ADVICE_WORDS = {
    "you should", "you need to", "you must", "you have to",
    "i learned", "i realised", "i realized", "i discovered",
    "the key is", "the secret is", "the truth is", "the lesson is",
    "always", "never", "every time", "most people",
    "what nobody tells you", "here's what", "this is why",
}

STORYTELLING_WORDS = {
    "when i was", "i remember", "there was a time", "one day",
    "i used to", "i was", "i had", "it all started", "back then",
    "growing up", "i decided", "i thought", "i realized", "that's when",
}

RELATABLE_WORDS = {
    "we all", "everyone", "nobody", "no one", "most people",
    "you know that feeling", "happens to all", "you've been there",
    "i'm not alone", "so many people", "just like you",
    "comparing", "doubt", "overthinking", "imposter",
}

IMPACT_WORDS = {
    "everything", "nothing", "completely", "totally", "literally",
    "honestly", "seriously", "absolutely", "forever",
    "life-changing", "life changing", "never forget",
    "turned my life", "shifted", "mindset",
}

# Score contribution per category (max 3 hits each)
SCORE_WEIGHTS = {
    "emotional":     2.0,
    "advice":        2.0,
    "storytelling":  1.5,
    "relatable":     1.5,
    "impact":        1.0,
}
MAX_RAW_SCORE = sum(w * 3 for w in SCORE_WEIGHTS.values())   # 24.0

# ---------------------------------------------------------------------------
# Hook templates keyed by dominant detected theme
# ---------------------------------------------------------------------------

HOOKS = {
    "emotional": [
        "This hit harder than expected.",
        "This will make you feel seen.",
        "Nobody talks about this feeling.",
        "This is the raw truth.",
    ],
    "advice": [
        "I wish someone told me this earlier.",
        "Nobody tells you this — until now.",
        "This one lesson changes everything.",
        "Write this down.",
    ],
    "storytelling": [
        "This story will stay with you.",
        "Everything changed after this moment.",
        "This is where it all turned around.",
        "I had no idea this would happen.",
    ],
    "relatable": [
        "If this is you, watch till the end.",
        "You are not alone in this.",
        "More people need to hear this.",
        "This is why you feel stuck.",
    ],
    "impact": [
        "This mindset shift changes everything.",
        "One decision. Infinite impact.",
        "This is why most people never succeed.",
        "This is the wake-up call you needed.",
    ],
    "default": [
        "This is worth your full attention.",
        "Stop scrolling — this matters.",
        "You need to hear this.",
        "Pay close attention to this part.",
    ],
}

# ---------------------------------------------------------------------------
# Caption fragments keyed by theme
# ---------------------------------------------------------------------------

CAPTIONS = {
    "emotional": [
        "Pain is temporary. Growth is permanent.",
        "Failure is not the end — it's the beginning.",
        "Feel it. Face it. Rise from it.",
        "Your struggle is your strength in disguise.",
    ],
    "advice": [
        "The lesson you needed right now.",
        "Advice they don't teach in school.",
        "Write this down. Live by it.",
        "Simple truth. Massive impact.",
    ],
    "storytelling": [
        "One moment. One shift. Everything changed.",
        "Real stories hit different.",
        "This is where the story turns.",
        "The moment that rewrote everything.",
    ],
    "relatable": [
        "You are not behind. You are becoming.",
        "More people feel this than admit it.",
        "Shared struggles, shared strength.",
        "You're not alone in this journey.",
    ],
    "impact": [
        "Big results start with small mindset shifts.",
        "One decision changes the entire trajectory.",
        "This is what separates the 1% from the rest.",
        "Perspective changes everything.",
    ],
    "default": [
        "Worth every second of your attention.",
        "Some content just hits different.",
        "This one stays with you.",
        "Quality over quantity. Always.",
    ],
}

# ---------------------------------------------------------------------------
# Editing tip pool, tagged by what they enhance
# ---------------------------------------------------------------------------

ALL_TIPS = {
    "emphasis": [
        "Add a slow zoom on the most powerful sentence.",
        "Use bold captions to highlight the key phrase.",
        "Pause for 1–2 seconds before the final line for impact.",
        "Emphasize emotion with a subtle background music swell.",
    ],
    "pacing": [
        "Cut any silence longer than 0.5 seconds to maintain energy.",
        "Speed-ramp into the climax for dramatic effect.",
        "Use jump cuts to keep the pacing tight.",
    ],
    "visual": [
        "Flash the caption on screen at the emotional peak.",
        "Add a soft vignette to draw focus to the speaker.",
        "Use a black-and-white filter briefly to signal a past memory.",
        "Overlay subtle particle effects to enhance the mood.",
    ],
    "audio": [
        "Lower background music volume at the key sentence.",
        "Add a soft reverb on the last word for resonance.",
        "Layer a heartbeat or tension sound under the struggle moment.",
    ],
}

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _count_hits(text: str, keyword_set: set) -> int:
    """Count how many keywords from the set appear in lowercased text (capped at 3)."""
    lowered = text.lower()
    return min(sum(1 for kw in keyword_set if kw in lowered), 3)


def _detect_themes(text: str) -> dict:
    """Return a hit-count dict per theme."""
    return {
        "emotional":    _count_hits(text, EMOTIONAL_WORDS),
        "advice":       _count_hits(text, ADVICE_WORDS),
        "storytelling": _count_hits(text, STORYTELLING_WORDS),
        "relatable":    _count_hits(text, RELATABLE_WORDS),
        "impact":       _count_hits(text, IMPACT_WORDS),
    }


def _dominant_theme(themes: dict) -> str:
    """Return the theme with the highest hit count, or 'default'."""
    best = max(themes, key=themes.get)
    return best if themes[best] > 0 else "default"


def _compute_score(themes: dict) -> float:
    """
    Normalise raw weighted score to a 0–10 scale.
    Adds a small length bonus for scores in the mid range.
    """
    raw = sum(themes[cat] * SCORE_WEIGHTS[cat] for cat in themes)
    normalised = ((raw / MAX_RAW_SCORE) * 10) + 2.5 * (0.5 - abs(raw / MAX_RAW_SCORE - 0.5))   # bonus for mid-range scores
    return round(min(normalised, 10.0), 1)


def _build_reasons(themes: dict) -> list[str]:
    """Convert theme hits into human-readable reason strings."""
    label_map = {
        "emotional":    "Emotional resonance",
        "advice":       "Actionable insight or life lesson",
        "storytelling": "Personal storytelling",
        "relatable":    "Highly relatable content",
        "impact":       "Strong, impactful language",
    }
    # Include a reason for every theme that scored at least 1 hit
    reasons = [label_map[t] for t in themes if themes[t] > 0]

    # Guarantee at least one reason so output is never empty
    if not reasons:
        reasons = ["Engaging standalone moment"]

    return reasons


def _pick(pool: list, seed_text: str) -> str:
    """Deterministically pick from a list based on a hash of the input text."""
    return pool[hash(seed_text) % len(pool)]


def _build_tips(themes: dict, text: str) -> list[str]:
    """Select 2–3 contextually relevant editing tips."""
    tips = []

    # Always include one emphasis tip
    tips.append(_pick(ALL_TIPS["emphasis"], text))

    # Add a pacing tip if the text is longer (likely multi-sentence)
    if len(text.split()) > 15:
        tips.append(_pick(ALL_TIPS["pacing"], text + "pacing"))

    # Add a visual tip for emotional or storytelling content
    if themes.get("emotional", 0) > 0 or themes.get("storytelling", 0) > 0:
        tips.append(_pick(ALL_TIPS["visual"], text + "visual"))
    elif themes.get("advice", 0) > 0:
        tips.append(_pick(ALL_TIPS["audio"], text + "audio"))

    # Return exactly 2–3 unique tips
    seen, unique = set(), []
    for tip in tips:
        if tip not in seen:
            seen.add(tip)
            unique.append(tip)

    return unique[:3]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def enhance_clip(text: str) -> dict:
    """
    Analyse a short transcript clip and generate viral content enhancements.

    Args:
        text: The transcribed text of the clip.

    Returns:
        A dict with keys:
            - "score"   (float):      Virality score from 0–10.
            - "reason"  (list[str]):  Why this clip is engaging.
            - "hook"    (str):        Attention-grabbing opening line.
            - "caption" (str):        Short punchy social media caption.
            - "tips"    (list[str]):  Editing suggestions for maximum impact.
    """
    if not text or not text.strip():
        return {
            "score":   0.0,
            "reason":  ["No content to analyse"],
            "hook":    "Add content to unlock insights.",
            "caption": "",
            "tips":    [],
        }

    themes  = _detect_themes(text)
    score   = _compute_score(themes)
    theme   = _dominant_theme(themes)
    reasons = _build_reasons(themes)
    hook    = _pick(HOOKS.get(theme, HOOKS["default"]), text)
    caption = _pick(CAPTIONS.get(theme, CAPTIONS["default"]), text + "cap")
    tips    = _build_tips(themes, text)

    return {
        "score":   score,
        "reason":  reasons,
        "hook":    hook,
        "caption": caption,
        "tips":    tips,
    }


# ---------------------------------------------------------------------------
# Quick smoke-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import json

    samples = [
        "I used to think I couldn't do anything, but then I realized failure is part of growth.",
        "The weather today is really nice, perfect for a walk in the park.",
        "You should never compare your chapter one to someone else's chapter twenty. I learned this the hard way.",
        "Most people quit right before their breakthrough. I almost did too — and it would have been the biggest mistake of my life.",
    ]

    for sample in samples:
        print(f"\nInput : {sample}")
        result = enhance_clip(sample)
        print(f"Output: {json.dumps(result, indent=2)}")
        print("-" * 60)