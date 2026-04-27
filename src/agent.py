"""
agent.py — Multi-Step Music Recommendation Agent

Implements a planning and decision-making chain where every step is printed
as a visible action with its reasoning. The agent does not just score and
return — it analyzes intent, selects a strategy, runs retrieval, checks
quality, decides whether to fall back to a different mode, verifies
diversity, and produces a final result along with a complete decision log.

Observable steps (tool calls):
  [STEP 1: analyze_intent]      Detect which preference dimensions are strong
  [STEP 2: select_strategy]     Choose the best scoring mode from intent
  [STEP 3: retrieve_candidates] Run the recommender with the chosen mode
  [STEP 4: check_quality]       Evaluate top-result confidence vs threshold
  [STEP 5: fallback]            Retry with discovery mode if quality is low
                                (skipped when quality is already acceptable)
  [STEP 6: diversity_check]     Confirm no single artist dominates the top-3
  [STEP 7: final_output]        Summarise decisions and return results

Usage (CLI demo):
    python src/agent.py

Usage (import):
    from src.agent import MusicAgent
    agent = MusicAgent(songs)
    results, log = agent.run(user_prefs, k=5, verbose=True)
    # results: list of (song_dict, score, explanation)
    # log:     list of strings, one per step
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

try:
    from recommender import load_songs, recommend_songs
except ModuleNotFoundError:
    from src.recommender import load_songs, recommend_songs

# Maximum score possible when all advanced features are active.
MAX_SCORE = 13.0

# If top confidence falls below this, the agent triggers a fallback.
CONFIDENCE_THRESHOLD = 0.40


class MusicAgent:
    """
    Multi-step recommendation agent with an observable decision chain.

    Each 'tool call' (step) is a discrete method that can be inspected,
    tested, or replaced independently. The run() method sequences them
    and records every decision in a log.
    """

    def __init__(self, songs: list):
        self.songs = songs

    # ------------------------------------------------------------------
    # TOOL FUNCTIONS
    # Each represents one observable step in the agent's reasoning chain.
    # ------------------------------------------------------------------

    def analyze_intent(self, prefs: dict) -> dict:
        """
        Tool: analyze_intent
        Reads the user's preferences and identifies which dimensions carry
        the strongest signal. Returns a structured intent summary that
        select_strategy uses to pick a scoring mode.
        """
        genre  = prefs.get("genre", "")
        mood   = prefs.get("mood", "")
        energy = prefs.get("target_energy")

        has_genre  = bool(genre and genre not in ("any", ""))
        has_mood   = bool(mood and mood not in ("any", ""))
        has_energy = energy is not None

        # Determine the dominant signal
        if has_genre and has_mood:
            dominant = "balanced"
        elif has_genre and not has_mood:
            dominant = "genre"
        elif has_mood and not has_genre:
            dominant = "mood"
        elif has_energy and not has_genre and not has_mood:
            dominant = "energy"
        else:
            dominant = "weak"

        return {
            "has_genre":  has_genre,
            "has_mood":   has_mood,
            "has_energy": has_energy,
            "dominant":   dominant,
            "genre":      genre or "any",
            "mood":       mood  or "—",
            "energy":     energy,
        }

    def select_strategy(self, intent: dict) -> str:
        """
        Tool: select_strategy
        Maps the dominant intent dimension to the scoring mode most likely
        to produce high-quality results for that user type.

        Mapping:
          genre   → genre_first    (genre lock is the user's primary gate)
          mood    → mood_first     (vibe matters more than genre label)
          energy  → energy_focused (intensity matching is all that matters)
          weak    → discovery      (no strong signal, open exploration)
          balanced→ balanced       (both genre and mood present; use defaults)
        """
        mapping = {
            "genre":    "genre_first",
            "mood":     "mood_first",
            "energy":   "energy_focused",
            "weak":     "discovery",
            "balanced": "balanced",
        }
        return mapping.get(intent["dominant"], "balanced")

    def retrieve_candidates(self, prefs: dict, mode: str, k: int) -> list:
        """
        Tool: retrieve_candidates
        Runs the full recommender pipeline (scoring + diversity re-ranking)
        with the given mode and returns top-k results.
        """
        return recommend_songs(prefs, self.songs, k=k, mode=mode, diversity=True)

    def check_quality(self, results: list) -> tuple:
        """
        Tool: check_quality
        Computes the confidence of the top result and decides whether it
        meets the threshold for reliable output.

        Returns:
            (confidence, meets_threshold)
        """
        if not results:
            return 0.0, False
        conf = round(results[0][1] / MAX_SCORE, 2)
        return conf, conf >= CONFIDENCE_THRESHOLD

    def detect_artist_monopoly(self, results: list, top_n: int = 3) -> bool:
        """
        Tool: detect_artist_monopoly
        Returns True if any artist appears more than once in the top-n
        slots, indicating the diversity re-ranker may not have fired or
        the catalog is too small to diversify.
        """
        artists = [r[0].get("artist", "") for r in results[:top_n]]
        return len(set(artists)) < len(artists)

    # ------------------------------------------------------------------
    # MAIN AGENT LOOP
    # ------------------------------------------------------------------

    def run(self, prefs: dict, k: int = 5, verbose: bool = True) -> tuple:
        """
        Executes the full multi-step agent chain.

        Args:
            prefs:   user preference dict (same format as recommend_songs)
            k:       number of recommendations to return
            verbose: if True, each step is printed to stdout as it runs

        Returns:
            (results, log)
            results: list of (song_dict, score, explanation) tuples
            log:     list of strings capturing every step and decision
        """
        log = []

        def emit(step_n: int, tool: str, headline: str, detail: str = ""):
            """Formats and records one agent step."""
            line = f"[STEP {step_n}: {tool}] {headline}"
            log.append(line)
            if verbose:
                print(line)
            if detail:
                detail_line = f"           -> {detail}"
                log.append(detail_line)
                if verbose:
                    print(detail_line)

        # ---- STEP 1: Analyze intent ----
        intent = self.analyze_intent(prefs)
        emit(1, "analyze_intent",
             f"Dominant signal: {intent['dominant'].upper()}",
             f"genre='{intent['genre']}'  mood='{intent['mood']}'  "
             f"energy={intent['energy']}  "
             f"(has_genre={intent['has_genre']}, has_mood={intent['has_mood']}, "
             f"has_energy={intent['has_energy']})")

        # ---- STEP 2: Select strategy ----
        mode = self.select_strategy(intent)
        emit(2, "select_strategy",
             f"Chosen mode: {mode.upper()}",
             f"dominant='{intent['dominant']}' maps to mode='{mode}'")

        # ---- STEP 3: Retrieve candidates ----
        results = self.retrieve_candidates(prefs, mode, k)
        if results:
            top = results[0]
            emit(3, "retrieve_candidates",
                 f"Retrieved {len(results)} candidates  (mode={mode})",
                 f"Top: '{top[0]['title']}' by {top[0]['artist']}  "
                 f"genre={top[0]['genre']}  score={top[1]:.2f}")
        else:
            emit(3, "retrieve_candidates", "No candidates returned — empty catalog?")

        # ---- STEP 4: Quality gate ----
        conf, meets = self.check_quality(results)
        emit(4, "check_quality",
             f"Confidence: {conf:.2f} / 1.00  "
             f"(threshold={CONFIDENCE_THRESHOLD})  "
             f"-> {'PASS' if meets else 'BELOW THRESHOLD'}",
             f"top_score={results[0][1]:.2f} / {MAX_SCORE}  =  {conf:.2f}")

        # ---- STEP 5: Fallback (conditional) ----
        if not meets:
            emit(5, "fallback",
                 f"Confidence {conf:.2f} is below {CONFIDENCE_THRESHOLD}. "
                 f"Retrying with DISCOVERY mode (genre/era zeroed out).")
            fallback = self.retrieve_candidates(prefs, "discovery", k)
            f_conf, _ = self.check_quality(fallback)
            if f_conf > conf:
                results = fallback
                conf    = f_conf
                mode    = "discovery"
                emit(5, "fallback",
                     f"Discovery mode raised confidence to {conf:.2f}. "
                     f"Switching to fallback results.",
                     f"New top: '{results[0][0]['title']}'  score={results[0][1]:.2f}")
            else:
                emit(5, "fallback",
                     f"Discovery mode did not improve results "
                     f"({f_conf:.2f} <= {conf:.2f}). Keeping original results.")
        else:
            emit(5, "fallback",
                 "Skipped — confidence meets threshold, no fallback needed.")

        # ---- STEP 6: Diversity check ----
        monopoly = self.detect_artist_monopoly(results, top_n=min(3, len(results)))
        if monopoly:
            emit(6, "diversity_check",
                 "Artist monopoly detected in top-3.",
                 "Diversity re-ranking was applied in Step 3. "
                 "Catalog may be too small to fully diversify this genre.")
        else:
            emit(6, "diversity_check",
                 "No artist monopoly in top-3 — diverse results confirmed.")

        # ---- STEP 7: Final output ----
        emit(7, "final_output",
             f"Returning {len(results)} recommendations. "
             f"Final mode: {mode.upper()}  confidence: {conf:.2f}",
             "Decision chain complete.")

        return results, log


# ---------------------------------------------------------------------------
# CLI DEMO  (python src/agent.py)
# ---------------------------------------------------------------------------

def _print_results(results: list, label: str = "") -> None:
    if label:
        print(f"\n  Results for: {label}")
    print(f"  {'#':<4} {'Title':<24} {'Artist':<18} "
          f"{'Genre':<12} {'Mood':<10} {'Score'}")
    print("  " + "-" * 82)
    for i, (song, score, _explanation) in enumerate(results, 1):
        print(f"  #{i:<3} {song['title']:<24} {song['artist']:<18} "
              f"{song['genre']:<12} {song['mood']:<10} {score:.2f}")
    print()


def main() -> None:
    try:
        songs = load_songs("data/songs.csv")
    except FileNotFoundError:
        songs = load_songs("../data/songs.csv")

    demo_cases = [
        (
            "Standard: Chill Lofi study session",
            {
                "genre": "lofi",
                "mood": "focused",
                "target_energy": 0.40,
                "target_instrumentalness": 0.88,
                "target_acousticness": 0.78,
            },
        ),
        (
            "Mood-only: user says 'euphoric', no genre",
            {
                "mood": "euphoric",
                "target_energy": 0.90,
            },
        ),
        (
            "Edge case: ghost genre (metal not in catalog)",
            {
                "genre": "metal",
                "mood": "intense",
                "target_energy": 0.95,
            },
        ),
        (
            "Edge case: no preferences at all",
            {},
        ),
    ]

    for label, prefs in demo_cases:
        print("\n" + "#" * 70)
        print(f"  AGENT RUN — {label}")
        print("#" * 70)
        agent   = MusicAgent(songs)
        results, _log = agent.run(prefs, k=3, verbose=True)
        _print_results(results)


if __name__ == "__main__":
    main()
