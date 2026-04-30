"""
explainer.py — Specialized Explanation Styles for VibeFinder 2.0

Demonstrates fine-tuning / specialization behavior by reformatting the
recommender's raw scoring reasons into three distinct tones. The scoring
math does not change — only the presentation layer is specialized.

Three styles:
  'technical'  Precision-focused. Shows numerical deltas, percentage matches,
               and a score breakdown in tabular form. Target audience: engineers
               or users who want to verify the math.

  'casual'     Conversational friend-style. Translates the score breakdown into
               natural language without numbers. Target audience: general users
               who want a quick, friendly explanation.

  'dj'         High-energy club/DJ language. Short, punchy, hype-oriented.
               Treats every match as a crowd-ready endorsement. Target audience:
               party / workout playlist builders.

Output measurably differs from the baseline (raw reason string):

  Baseline:  energy proximity 0.97 (+2.91); genre match 'pop' (+1.0);
             mood match 'happy' (+2.0)

  Technical: SCORE BREAKDOWN  Sunrise City [pop / happy]
               genre   : EXACT MATCH (pop=pop) ............. +1.00
               mood    : EXACT MATCH (happy=happy) ......... +2.00
               energy  : 97% match (delta=0.03) ............ +2.91
             TOTAL: 5.91 / 13.00  confidence=0.45

  Casual:    This one's a great fit — same genre you wanted (pop), the mood
             is exactly right (happy), and the energy level is nearly perfect.
             Strong match overall.

  DJ:        LOCKED IN — pop confirmed, happy vibes on point, energy
             99% dialed. This one hits.

Usage:
    python src/explainer.py          # side-by-side comparison demo

    from src.explainer import explain_with_style
    styled = explain_with_style(song, raw_explanation, total_score, style="casual")
"""

import sys
import os
import re

sys.path.insert(0, os.path.dirname(__file__))

try:
    from recommender import load_songs, recommend_songs
except ModuleNotFoundError:
    from src.recommender import load_songs, recommend_songs

MAX_SCORE = 13.0


def _safe_float(value):
    """Safely convert a value to float, returning 0 if conversion fails."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0


# ---------------------------------------------------------------------------
# PARSER
# Converts the semicolon-separated reason string produced by _score_core
# into a structured list of (feature, value, points) tuples that each
# style function can render differently.
# ---------------------------------------------------------------------------

def _parse_reasons(raw: str) -> list:
    """
    Parses a raw reason string into structured records.

    Input:  "energy proximity 0.97 (+2.91); genre match 'pop' (+1.0)"
    Output: [
        {"feature": "energy proximity", "value": "0.97", "points": 2.91},
        {"feature": "genre match",      "value": "pop",  "points": 1.0},
    ]
    """
    records = []
    for part in raw.split(";"):
        part = part.strip()
        if not part or part == "no matching features":
            continue

        # Extract points from (+N.NN) at end of token
        pts_match = re.search(r"\(\+([0-9.]+)\)$", part)
        points = float(pts_match.group(1)) if pts_match else 0.0
        body   = part[: pts_match.start()].strip() if pts_match else part

        # Extract quoted value  e.g.  genre match 'pop'
        q_match = re.search(r"'([^']+)'", body)
        # Extract last bare number  e.g.  energy proximity 0.97
        n_match = re.search(r"([0-9.]+)\s*$", body)

        if q_match:
            value   = q_match.group(1)
            feature = body[: q_match.start()].strip()
        elif n_match:
            value   = n_match.group(1)
            feature = body[: n_match.start()].strip()
        else:
            value   = ""
            feature = body

        # Normalise feature label (strip trailing whitespace/punctuation)
        feature = feature.rstrip(": ").strip()
        records.append({"feature": feature, "value": value, "points": points})

    return records


# ---------------------------------------------------------------------------
# STYLE RENDERERS
# ---------------------------------------------------------------------------

def _render_technical(song: dict, records: list, total: float) -> str:
    """Renders a precision-focused score breakdown with numerical deltas."""
    lines = []
    tag = f"{song.get('title', '?')} [{song.get('genre', '?')} / {song.get('mood', '?')}]"
    lines.append(f"SCORE BREAKDOWN  {tag}")

    max_feat_len = max((len(r["feature"]) for r in records), default=10)
    for r in records:
        feat  = r["feature"].ljust(max_feat_len + 2)
        pts   = f"+{r['points']:.2f}"

        # For proximity features, show percentage
        if "proximity" in r["feature"] and r["value"]:
            float_val = _safe_float(r["value"])
            pct = round(float_val * 100)
            detail = f"{pct}% match"
            delta  = round(1.0 - float_val, 2)
            detail += f"  (delta={delta:.2f})"
        elif "match" in r["feature"] and r["value"]:
            detail = f"EXACT MATCH ({r['value']})"
        elif "bonus" in r["feature"]:
            detail = "acoustic preference bonus"
        elif "penalty" in r["feature"]:
            detail = f"diversity penalty applied  raw={r['value']}"
        elif "decade" in r["feature"]:
            detail = f"era score  ({r['value']}s)"
        else:
            detail = r["value"] or ""

        dots = "." * max(0, 40 - len(feat) - len(detail))
        lines.append(f"  {feat}{detail} {dots} {pts}")

    conf = round(total / MAX_SCORE, 2)
    lines.append(f"TOTAL: {total:.2f} / {MAX_SCORE:.2f}  confidence={conf:.2f}")
    return "\n".join(lines)


# Casual-style sentence fragments for each feature type.
_CASUAL_TEMPLATES = {
    "genre match":              "same genre you wanted ({value})",
    "mood match":               "the mood is exactly right ({value})",
    "energy proximity":         "the energy level is {pct}% matched to what you want",
    "acousticness proximity":   "acoustic texture is {pct}% matched",
    "instrumentalness proximity": "vocal/instrumental balance is {pct}% matched",
    "valence proximity":        "emotional brightness is {pct}% matched",
    "speechiness proximity":    "vocal style is {pct}% matched",
    "acoustic bonus":           "has the acoustic sound you prefer",
    "popularity proximity":     "popularity level is {pct}% matched to your preference",
    "decade score":             "from the {value}s era you were looking for",
    "detail mood match":        "has the exact detailed mood you wanted ({value})",
    "liveness proximity":       "live/studio feel is {pct}% matched",
    "loudness proximity":       "loudness level is {pct}% matched",
    "diversity penalty applied":"(moved down slightly for playlist variety)",
}


def _render_casual(song: dict, records: list, total: float) -> str:
    """Renders a conversational friend-style explanation."""
    phrases = []
    for r in records:
        feat  = r["feature"]
        value = r["value"]
        pct   = round(_safe_float(value) * 100) if value and "proximity" in feat else 0

        tmpl = None
        for key, template in _CASUAL_TEMPLATES.items():
            if key in feat:
                tmpl = template
                break

        if tmpl:
            phrase = tmpl.format(value=value, pct=pct)
            phrases.append(phrase)

    if not phrases:
        return "No strong matches — this is the best available option given your preferences."

    conf = round(total / MAX_SCORE, 2)
    if conf >= 0.6:
        opener = "This one is a great fit —"
    elif conf >= 0.4:
        opener = "Decent match —"
    else:
        opener = "Closest available option —"

    body  = ", ".join(phrases[:-1])
    if len(phrases) > 1:
        body += f", and {phrases[-1]}"
    else:
        body = phrases[0]

    return f"{opener} {body}."


# DJ-style short labels for each feature type.
_DJ_TEMPLATES = {
    "genre match":              "{value} confirmed",
    "mood match":               "{value} vibes locked",
    "energy proximity":         "energy {pct}% dialed",
    "acousticness proximity":   "texture {pct}% dialed",
    "instrumentalness proximity": "instrumental balance {pct}%",
    "valence proximity":        "emotional tone {pct}%",
    "speechiness proximity":    "vocal ratio {pct}%",
    "acoustic bonus":           "acoustic sound: present",
    "popularity proximity":     "crowd factor {pct}%",
    "decade score":             "{value}s era: in range",
    "detail mood match":        "{value} detail mood: EXACT",
    "liveness proximity":       "live feel {pct}%",
    "loudness proximity":       "volume {pct}%",
    "diversity penalty applied":"(rotated for set variety)",
}


def _render_dj(song: dict, records: list, total: float) -> str:
    """Renders a high-energy club/DJ style explanation."""
    tags = []
    for r in records:
        feat  = r["feature"]
        value = r["value"]
        pct   = round(_safe_float(value) * 100) if value and "proximity" in feat else 0

        tmpl = None
        for key, template in _DJ_TEMPLATES.items():
            if key in feat:
                tmpl = template
                break

        if tmpl:
            tags.append(tmpl.format(value=value, pct=pct))

    if not tags:
        return "Closest available — no perfect lock."

    conf = round(total / MAX_SCORE, 2)
    if conf >= 0.6:
        opener = "LOCKED IN —"
    elif conf >= 0.4:
        opener = "ON DECK —"
    else:
        opener = "BEST AVAILABLE —"

    return f"{opener} {' | '.join(tags)}."


# ---------------------------------------------------------------------------
# PUBLIC API
# ---------------------------------------------------------------------------

def explain_with_style(
    song: dict,
    raw_explanation: str,
    total_score: float,
    style: str = "casual",
) -> str:
    """
    Reformats a raw explanation string into the requested style.

    Args:
        song:            song dict (needs 'title', 'genre', 'mood')
        raw_explanation: semicolon-separated reason string from recommend_songs
        total_score:     the song's total numeric score
        style:           one of 'technical', 'casual', 'dj'
                         (defaults to 'casual'; unknown styles return raw)

    Returns:
        A single string in the requested style.
    """
    records = _parse_reasons(raw_explanation)

    if style == "technical":
        return _render_technical(song, records, total_score)
    elif style == "casual":
        return _render_casual(song, records, total_score)
    elif style == "dj":
        return _render_dj(song, records, total_score)
    else:
        return raw_explanation   # unknown style: fall back to baseline


def recommend_with_style(
    user_prefs: dict,
    songs: list,
    k: int = 3,
    mode: str = "balanced",
    style: str = "casual",
) -> list:
    """
    Convenience wrapper: runs recommend_songs then reformats all explanations
    in the given style.

    Returns:
        list of (song_dict, score, styled_explanation)
    """
    raw_results = recommend_songs(user_prefs, songs, k=k, mode=mode, diversity=True)
    styled = []
    for song, score, raw_exp in raw_results:
        styled_exp = explain_with_style(song, raw_exp, score, style=style)
        styled.append((song, score, styled_exp))
    return styled


# ---------------------------------------------------------------------------
# DEMO  (python src/explainer.py)
# Shows a side-by-side comparison of all three styles for the same song.
# ---------------------------------------------------------------------------

def main() -> None:
    try:
        songs = load_songs("data/songs.csv")
    except FileNotFoundError:
        songs = load_songs("../data/songs.csv")

    demo_prefs = {
        "genre": "pop",
        "mood": "happy",
        "target_energy": 0.82,
        "target_acousticness": 0.18,
        "target_instrumentalness": 0.00,
        "target_valence": 0.84,
    }

    # Get raw results once
    raw_results = recommend_songs(demo_prefs, songs, k=3, mode="balanced", diversity=True)

    styles = ["technical", "casual", "dj"]

    print("\n" + "=" * 80)
    print("  EXPLAINER DEMO — same song, three different styles")
    print("  Profile: pop / happy / energy=0.82")
    print("=" * 80)

    for song, score, raw_exp in raw_results[:2]:   # show top 2 songs
        title = song['title']
        print(f"\n  Song: {title} - {song['artist']}  (score={score:.2f})")
        print(f"  {'-' * 60}")

        print(f"\n  [BASELINE — raw reason string]")
        print(f"  {raw_exp}")

        for style in styles:
            styled = explain_with_style(song, raw_exp, score, style=style)
            print(f"\n  [{style.upper()}]")
            # Indent multi-line output
            for line in styled.splitlines():
                print(f"  {line}")

        print()


if __name__ == "__main__":
    main()
