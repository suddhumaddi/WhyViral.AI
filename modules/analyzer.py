# No external dependencies required — standard library only.

# ---------------------------------------------------------------------------
# Keyword scoring tables
# ---------------------------------------------------------------------------

EMOTIONAL_WORDS = {
    # Struggle / hardship
    "can't", "cant", "hard", "fail", "failed", "failure", "struggle",
    "struggled", "struggling", "difficult", "impossible", "pain", "hurt",
    "fear", "afraid", "scared", "lost", "broken", "gave up", "quit",
    # Triumph / growth
    "success", "succeeded", "overcome", "overcame", "achieve", "achieved",
    "proud", "won", "victory", "breakthrough", "changed", "transformed",
    "grateful", "incredible", "amazing",
}

ADVICE_PHRASES = {
    "you should", "you need to", "you must", "you have to",
    "i learned", "i realised", "i realized", "i discovered", "i found out",
    "the key is", "the secret is", "the truth is", "the lesson is",
    "always", "never", "every time", "most people", "what nobody tells you",
    "here's what", "this is why", "that's when",
}

STORYTELLING_MARKERS = {
    "when i was", "i remember", "there was a time", "one day", "i used to",
    "i was", "i had", "it all started", "back then", "growing up",
    "i decided", "i chose", "i thought", "i realized",
}

IMPACT_WORDS = {
    "everything", "nothing", "completely", "totally", "literally",
    "honestly", "seriously", "absolutely", "forever", "life-changing",
    "life changing", "never forget", "turned my life",
}

# Weight each category contributes to the final score
WEIGHTS = {
    "emotional":     3,
    "advice":        3,
    "storytelling":  2,
    "impact":        2,
}

# Target window for a "viral" clip
MIN_DURATION = 20.0   # seconds
MAX_DURATION = 60.0   # seconds
TOP_N        = 3      # how many clips to return


# ---------------------------------------------------------------------------
# Scoring helpers
# ---------------------------------------------------------------------------

def _score_segment(text: str) -> dict:
    """
    Score a single segment's text against all keyword categories.
    Returns a breakdown dict and the total weighted score.
    """
    lowered = text.lower()
    breakdown = {}

    # Count matches per category (capped at 3 hits per category to avoid
    # a single very long segment dominating purely due to length)
    breakdown["emotional"]    = min(sum(1 for w in EMOTIONAL_WORDS    if w in lowered), 3)
    breakdown["advice"]       = min(sum(1 for p in ADVICE_PHRASES      if p in lowered), 3)
    breakdown["storytelling"] = min(sum(1 for m in STORYTELLING_MARKERS if m in lowered), 3)
    breakdown["impact"]       = min(sum(1 for w in IMPACT_WORDS        if w in lowered), 3)

    total = sum(breakdown[cat] * WEIGHTS[cat] for cat in breakdown)
    return {"breakdown": breakdown, "total": total}


# ---------------------------------------------------------------------------
# Segment expansion / merging
# ---------------------------------------------------------------------------

def _expand_segment(
    target: dict,
    all_segments: list[dict],
    min_dur: float = MIN_DURATION,
    max_dur: float = MAX_DURATION,
) -> dict:
    """
    Grow a single high-scoring segment by absorbing neighbouring segments
    until it meets `min_dur` seconds, without exceeding `max_dur` seconds.

    Strategy: alternate between pulling in the next segment to the right and
    the next to the left, preferring the side that adds the shorter gap first.
    """
    # Find the index of this segment in the full list
    try:
        idx = next(i for i, s in enumerate(all_segments) if s is target)
    except StopIteration:
        return {"start": target["start"], "end": target["end"]}

    lo, hi = idx, idx          # inclusive index range of the current window
    start  = target["start"]
    end    = target["end"]

    while (end - start) < min_dur:
        can_go_left  = lo > 0
        can_go_right = hi < len(all_segments) - 1

        if not can_go_left and not can_go_right:
            break   # no more neighbours

        # Decide which direction adds the smallest increment
        left_gap  = (start - all_segments[lo - 1]["start"]) if can_go_left  else float("inf")
        right_gap = (all_segments[hi + 1]["end"] - end)     if can_go_right else float("inf")

        if left_gap <= right_gap and can_go_left:
            candidate_start = all_segments[lo - 1]["start"]
            if (end - candidate_start) <= max_dur:
                lo    -= 1
                start  = candidate_start
            elif can_go_right:
                candidate_end = all_segments[hi + 1]["end"]
                if (candidate_end - start) <= max_dur:
                    hi   += 1
                    end   = candidate_end
                else:
                    break
            else:
                break
        elif can_go_right:
            candidate_end = all_segments[hi + 1]["end"]
            if (candidate_end - start) <= max_dur:
                hi   += 1
                end   = candidate_end
            elif can_go_left:
                candidate_start = all_segments[lo - 1]["start"]
                if (end - candidate_start) <= max_dur:
                    lo    -= 1
                    start  = candidate_start
                else:
                    break
            else:
                break
        else:
            break

    return {"start": round(start, 3), "end": round(end, 3)}


# ---------------------------------------------------------------------------
# Deduplication — drop clips that overlap significantly with a higher-ranked one
# ---------------------------------------------------------------------------

def _overlaps(a: dict, b: dict, threshold: float = 0.7) -> bool:
    """
    Return True if clips `a` and `b` share more than `threshold` of the
    shorter clip's duration (IoMin overlap).
    """
    overlap = max(0.0, min(a["end"], b["end"]) - max(a["start"], b["start"]))
    shorter = min(a["end"] - a["start"], b["end"] - b["start"])
    return shorter > 0 and (overlap / shorter) > threshold


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def analyze_transcript(transcript: list[dict]) -> list[dict]:
    """
    Identify the top 2–3 most viral-worthy segments from a transcript.

    Args:
        transcript: List of dicts with keys "start" (float), "end" (float),
                    and "text" (str) — as produced by transcribe.py.

    Returns:
        List of dicts with keys "start" and "end", sorted by start time,
        representing the best clip windows (20–60 s each).
    """
    if not transcript:
        return []

    # ── Step 1: score every segment ────────────────────────────────────────
    scored = []
    for seg in transcript:
        result = _score_segment(seg["text"])
        scored.append({
            "segment": seg,
            "score":   result["total"],
        })

    # ── Step 2: sort by score descending ───────────────────────────────────
    scored.sort(key=lambda x: x["score"], reverse=True)

    # ── Step 3: expand each top candidate & deduplicate ────────────────────
    clips   = []
    seen    = []   # already-selected (expanded) clips

    for item in scored:
        if len(clips) >= TOP_N:
            break

        expanded = _expand_segment(item["segment"], transcript)

        is_overlapping = False
        for kept in seen:
            overlap = max(0.0, min(expanded["end"], kept["end"]) - max(expanded["start"], kept["start"]))
            shorter = min(expanded["end"] - expanded["start"], kept["end"] - kept["start"])

            if shorter > 0 and (overlap / shorter) > 0.3:   # stricter threshold
                is_overlapping = True
                break

        if is_overlapping:
            continue

        clips.append(expanded)
        seen.append(expanded)

    # ── Step 4: return in chronological order ──────────────────────────────
    clips.sort(key=lambda c: c["start"])
    return clips


# ---------------------------------------------------------------------------
# Quick smoke-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import json

    sample_transcript = [
        {"start": 0.0,  "end": 6.6,  "text": "I had some tantrums of saying I can't do this."},
        {"start": 6.6,  "end": 14.8, "text": "When I was a kid comparing myself to others, I struggled so much."},
        {"start": 14.8, "end": 22.0, "text": "The weather today is quite nice and the sky is blue."},
        {"start": 22.0, "end": 30.5, "text": "I learned that failure is not the end — it's just the beginning."},
        {"start": 30.5, "end": 38.0, "text": "You should never give up on what you truly believe in."},
        {"start": 38.0, "end": 45.0, "text": "The coffee shop had really good lattes and pastries."},
        {"start": 45.0, "end": 55.0, "text": "That's when everything changed. I realized I had been afraid my whole life."},
        {"start": 55.0, "end": 63.0, "text": "Most people quit right before their breakthrough — I almost did too."},
    ]

    results = analyze_transcript(sample_transcript)
    print("Top viral segments:")
    print(json.dumps(results, indent=2))