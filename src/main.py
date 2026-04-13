"""
Command line runner for the Music Recommender Simulation.

This file defines user taste profiles and runs the recommender.
You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

try:
    from recommender import load_songs, recommend_songs, SCORING_MODES
except ModuleNotFoundError:
    from src.recommender import load_songs, recommend_songs, SCORING_MODES

try:
    from tabulate import tabulate
    _TABULATE_AVAILABLE = True
except ImportError:
    _TABULATE_AVAILABLE = False


# ---------------------------------------------------------------------------
# USER TASTE PROFILES
# Each profile is a dictionary of preference signals your score_song function
# will compare against every song in the catalog.
#
# Features used:
#   genre              (str)   -- preferred genre label
#   mood               (str)   -- preferred mood label
#   target_energy      (float) -- ideal energy level, 0.0 (calm) to 1.0 (intense)
#   target_valence     (float) -- ideal emotional brightness, 0.0 (dark) to 1.0 (upbeat)
#   likes_acoustic     (bool)  -- True = prefers organic/acoustic sound
#   target_instrumentalness (float) -- 1.0 = wants fully instrumental (no vocals)
#   target_speechiness (float) -- 1.0 = wants rap/spoken word style
# ---------------------------------------------------------------------------

# Profile 1: High-Energy Pop
# Upbeat, danceable pop -- high energy, high valence, very low instrumentalness
high_energy_pop = {
    "genre": "pop",
    "mood": "happy",
    "target_energy": 0.85,
    "target_valence": 0.82,
    "likes_acoustic": False,
    "target_acousticness": 0.15,
    "target_instrumentalness": 0.00,
    "target_speechiness": 0.06,
}

# Profile 2: Chill Lofi
# Quiet, wordless background music for studying -- high instrumentalness is critical
chill_lofi = {
    "genre": "lofi",
    "mood": "focused",
    "target_energy": 0.40,
    "target_valence": 0.58,
    "likes_acoustic": True,
    "target_acousticness": 0.78,
    "target_instrumentalness": 0.88,
    "target_speechiness": 0.03,
}

# Profile 3: Deep Intense Rock
# Heavy, aggressive tracks -- high energy, low valence, loud and electric
deep_intense_rock = {
    "genre": "rock",
    "mood": "intense",
    "target_energy": 0.91,
    "target_valence": 0.48,
    "likes_acoustic": False,
    "target_acousticness": 0.10,
    "target_instrumentalness": 0.02,
    "target_speechiness": 0.06,
}

# Profile 4: Late-night study session (kept for edge case critique)
study_user = chill_lofi

# Profile 5: Morning workout (kept for backwards compatibility)
workout_user = deep_intense_rock

# Profile 6: Vague chill listener (edge case -- no genre set)
vague_user = {
    "genre": "any",
    "mood": "chill",
    "target_energy": 0.40,
    "target_valence": 0.60,
    "likes_acoustic": False,
    "target_instrumentalness": 0.50,
    "target_speechiness": 0.05,
}

# ---------------------------------------------------------------------------
# CRITIQUE: Does the profile differentiate "intense rock" vs "chill lofi"?
#
# Song: Storm Runner (rock, intense)
#   energy=0.91, valence=0.48, acousticness=0.10, instrumentalness=0.00
#
# Song: Library Rain (lofi, chill)
#   energy=0.35, valence=0.60, acousticness=0.86, instrumentalness=0.92
#
# FULL PROFILE (study_user / workout_user):
#   energy alone separates them (0.91 vs 0.35) -- score gap is wide
#   instrumentalness adds a second axis: 0.00 vs 0.92 -- rock is penalized hard
#   genre + mood add a third lock -- three independent dimensions all point correctly
#   Verdict: DIFFERENTIATED cleanly
#
# NARROW PROFILE (vague_user, genre="any"):
#   energy still separates them, so basic ranking works
#   BUT: a classical song (energy=0.22) now scores HIGHER than lofi (energy=0.35)
#   because it is also closer to target_energy=0.40 -- wrong result
#   mood="chill" has no match in the catalog for classical, which saves it --
#   but only by accident, not by design
#   Verdict: FRAGILE -- correct output for the wrong reasons
#
# MISSING DIMENSION problem:
#   If a user wants "chill but electronic" (low energy, no acousticness),
#   no profile above captures that. synthwave Night Drive Loop (energy=0.75)
#   would score low on energy proximity but there is no way to reward its
#   electronic texture without a target_acousticness preference in the profile.
#   Adding "target_acousticness" to every profile would close this gap.
# ---------------------------------------------------------------------------


def print_recommendations(label: str, user_prefs: dict, songs: list,
                          k: int = 3, mode: str = "balanced",
                          diversity: bool = True) -> None:
    """Prints a clean, readable block of recommendations for one user profile."""
    recommendations = recommend_songs(user_prefs, songs, k=k, mode=mode,
                                      diversity=diversity)

    diversity_label = "ON" if diversity else "OFF"
    print(f"\n{'=' * 60}")
    print(f"  PROFILE : {label}")
    print(f"  MODE    : {mode.upper():<16}  DIVERSITY: {diversity_label}")
    print(f"  GENRE   : {user_prefs.get('genre', 'any').upper():<10}  "
          f"MOOD: {user_prefs.get('mood', '-').upper():<10}  "
          f"ENERGY: {user_prefs.get('target_energy', '-')}")
    print(f"{'=' * 60}")

    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        filled = int((score / 13.0) * 20)   # 13.0 = max with all advanced features
        bar = "#" * filled + "-" * (20 - filled)

        print(f"\n  #{rank}  {song['title']}  -  {song['artist']}")
        print(f"       Genre: {song['genre']:<12}  Mood: {song['mood']:<10}  Energy: {song['energy']}")
        print(f"       Score: {score:>5.2f}  [{bar}]")
        print(f"       Why:")
        for reason in explanation.split("; "):
            print(f"         * {reason}")

    print(f"\n{'-' * 60}")


def print_mode_comparison(label: str, user_prefs: dict, songs: list, k: int = 3) -> None:
    """Runs the same profile under all four scoring modes and prints results side by side."""
    modes = ["balanced", "genre_first", "mood_first", "energy_focused", "discovery"]
    print(f"\n{'#' * 60}")
    print(f"  MODE COMPARISON: {label}")
    print(f"{'#' * 60}")
    for mode in modes:
        print_recommendations(label, user_prefs, songs, k=k, mode=mode)


# ---------------------------------------------------------------------------
# VISUAL SUMMARY TABLE
#
# Copilot prompt that inspired this design:
#   "Using tabulate with tablefmt='grid', build a summary table for the top-k
#    recommendations. Each row must show: rank, song title and artist (stacked),
#    genre / mood / energy (stacked), a 10-char score bar with numeric score,
#    and all scoring reasons as a bulleted multi-line cell. Use \n inside each
#    cell string so tabulate renders them as wrapped lines within the grid."
#
# tabulate's 'grid' format is the key: it draws box-drawing borders around
# every cell and honours \n as a line break inside the cell, which lets the
# reasons column expand vertically without truncating any explanation.
# ---------------------------------------------------------------------------

def _make_score_bar(score: float, max_score: float = 13.0, width: int = 10) -> str:
    """Returns a compact ASCII score bar, e.g. '|######----|  8.86'."""
    filled = min(width, int((score / max_score) * width))
    bar = "#" * filled + "-" * (width - filled)
    return f"|{bar}| {score:>5.2f}"


def print_summary_table(
    label: str,
    user_prefs: dict,
    songs: list,
    k: int = 5,
    mode: str = "balanced",
    diversity: bool = True,
) -> None:
    """Prints a formatted tabulate grid table of the top-k recommendations.

    Each row contains: rank, song/artist, genre/mood/energy, score bar, and
    all scoring reasons as a multi-line bulleted cell. Falls back to the
    plain print_recommendations() output if tabulate is not installed.
    """
    if not _TABULATE_AVAILABLE:
        print("  [tabulate not installed — falling back to plain output]")
        print_recommendations(label, user_prefs, songs, k=k, mode=mode,
                              diversity=diversity)
        return

    results = recommend_songs(user_prefs, songs, k=k, mode=mode,
                              diversity=diversity)

    headers = ["#", "Song / Artist", "Genre / Mood / Energy", "Score", "Why (scoring reasons)"]
    rows = []
    for rank, (song, score, explanation) in enumerate(results, start=1):
        # Column 1 — rank
        rank_cell = str(rank)

        # Column 2 — title stacked above artist
        song_cell = f"{song['title']}\n{song['artist']}"

        # Column 3 — genre / mood / energy stacked
        info_cell = (
            f"genre : {song['genre']}\n"
            f"mood  : {song['mood']}\n"
            f"energy: {song['energy']}"
        )

        # Column 4 — score bar + numeric score
        score_cell = _make_score_bar(score)

        # Column 5 — reasons, one bullet per line
        reasons = [r.strip() for r in explanation.split(";") if r.strip()]
        reasons_cell = "\n".join(f"* {r}" for r in reasons)

        rows.append([rank_cell, song_cell, info_cell, score_cell, reasons_cell])

    diversity_label = "ON" if diversity else "OFF"
    print(f"\n{'=' * 80}")
    print(f"  SUMMARY TABLE  |  {label}")
    print(f"  Mode: {mode.upper():<18} Diversity: {diversity_label:<6} "
          f"Genre: {user_prefs.get('genre','any').upper():<10} "
          f"Mood: {user_prefs.get('mood','-').upper():<10} "
          f"Energy: {user_prefs.get('target_energy','-')}")
    print(f"{'=' * 80}")
    print(tabulate(rows, headers=headers, tablefmt="grid"))
    print()


def main() -> None:
    songs = load_songs("data/songs.csv")
    print(f"\nLoaded songs: {len(songs)}")

    # --- Standard profiles ---
    standard_profiles = {
        "High-Energy Pop": high_energy_pop,
        "Chill Lofi": chill_lofi,
        "Deep Intense Rock": deep_intense_rock,
    }

    # --- Adversarial / edge case profiles ---
    # Each one is designed to expose a specific weakness in the scoring logic.

    # EDGE CASE 1: Conflicting energy + mood
    # energy=0.9 screams "intense" but mood="sad" — no song in the catalog is both.
    # Expected failure: system is forced to choose between high energy OR sad mood,
    # it cannot satisfy both. Watch which dimension wins.
    conflicting_energy_mood = {
        "genre": "blues",
        "mood": "sad",
        "target_energy": 0.90,
        "target_valence": 0.20,
        "likes_acoustic": False,
        "target_acousticness": 0.10,
        "target_instrumentalness": 0.10,
        "target_speechiness": 0.05,
    }

    # EDGE CASE 2: Ghost genre (not in catalog)
    # Genre "metal" does not exist in the 18-song catalog.
    # Expected failure: zero genre points for every song — system falls back to
    # mood and energy only, recommending songs the user almost certainly doesn't want.
    ghost_genre = {
        "genre": "metal",
        "mood": "intense",
        "target_energy": 0.95,
        "target_valence": 0.30,
        "likes_acoustic": False,
        "target_acousticness": 0.05,
        "target_instrumentalness": 0.05,
        "target_speechiness": 0.05,
    }

    # EDGE CASE 3: Contradictory acousticness + instrumentalness
    # Wants fully instrumental (instrumentalness=1.0) but also fully electronic
    # (acousticness=0.0). In the catalog, instrumental songs are almost always
    # acoustic (lofi, classical, ambient). This profile wants something that
    # doesn't exist: a silent EDM track with no vocals.
    impossible_combo = {
        "genre": "edm",
        "mood": "euphoric",
        "target_energy": 0.97,
        "target_valence": 0.83,
        "likes_acoustic": False,
        "target_acousticness": 0.02,
        "target_instrumentalness": 1.00,
        "target_speechiness": 0.02,
    }

    # EDGE CASE 4: The "Middle of Everything" user
    # Every preference is set to the midpoint (0.5).
    # Expected failure: no song scores badly, but no song scores well either.
    # The system returns whoever happened to land closest to dead-center —
    # revealing that "average" preferences produce meaningless recommendations.
    middle_of_everything = {
        "genre": "any",
        "mood": "",
        "target_energy": 0.50,
        "target_valence": 0.50,
        "likes_acoustic": False,
        "target_acousticness": 0.50,
        "target_instrumentalness": 0.50,
        "target_speechiness": 0.05,
    }

    adversarial_profiles = {
        "EDGE 1 — Conflicting Energy + Sad Mood": conflicting_energy_mood,
        "EDGE 2 — Ghost Genre (metal, not in catalog)": ghost_genre,
        "EDGE 3 — Impossible Combo (EDM + fully instrumental)": impossible_combo,
        "EDGE 4 — Middle of Everything (all 0.5)": middle_of_everything,
    }

    # -----------------------------------------------------------------------
    # ADVANCED FEATURE PROFILES
    # Each profile uses one or more of the five new attributes:
    #   target_popularity, preferred_decade, preferred_detail_mood,
    #   target_liveness, target_loudness
    # -----------------------------------------------------------------------

    # ADVANCED 1: Y2K Nostalgic Jazz Listener
    # Wants 2000s-era jazz with a nostalgic granular tag and a live-room feel.
    # preferred_decade=2000 rewards Coffee Shop Stories (jazz, 2000, nostalgic)
    # and penalizes 2020s releases by 0.5 points.
    # target_liveness=0.4 rewards the slight live feel of Coffee Shop Stories (0.45).
    y2k_jazz = {
        "genre": "jazz",
        "mood": "relaxed",
        "target_energy": 0.35,
        "target_valence": 0.70,
        "likes_acoustic": True,
        "target_acousticness": 0.85,
        "target_instrumentalness": 0.70,
        "target_speechiness": 0.04,
        "preferred_decade": 2000,
        "preferred_detail_mood": "nostalgic",
        "target_liveness": 0.40,
        "target_loudness": 0.40,
    }

    # ADVANCED 2: Underground Aggressive Hip-Hop
    # Wants low-popularity (underground) tracks with an aggressive detail mood
    # and loud/dynamic sound. target_popularity=30 penalizes mainstream songs
    # like Gym Hero (81) and rewards less-known catalog entries.
    # preferred_detail_mood="aggressive" adds +1.5 for Block by Block and Storm Runner.
    underground_hiphop = {
        "genre": "hip-hop",
        "mood": "motivated",
        "target_energy": 0.80,
        "target_valence": 0.65,
        "likes_acoustic": False,
        "target_acousticness": 0.10,
        "target_instrumentalness": 0.05,
        "target_speechiness": 0.25,
        "target_popularity": 30,
        "preferred_decade": 2010,
        "preferred_detail_mood": "aggressive",
        "target_liveness": 0.10,
        "target_loudness": 0.85,
    }

    advanced_profiles = {
        "ADVANCED 1 — Y2K Nostalgic Jazz (2000s era, live feel)": y2k_jazz,
        "ADVANCED 2 — Underground Aggressive Hip-Hop (low popularity)": underground_hiphop,
    }

    print("\n" + "#" * 60)
    print("  STANDARD PROFILES")
    print("#" * 60)
    for label, user_prefs in standard_profiles.items():
        print_recommendations(label, user_prefs, songs, k=5)

    print("\n" + "#" * 60)
    print("  ADVERSARIAL / EDGE CASE PROFILES")
    print("#" * 60)
    for label, user_prefs in adversarial_profiles.items():
        print_recommendations(label, user_prefs, songs, k=5)

    print("\n" + "#" * 60)
    print("  ADVANCED FEATURE PROFILES")
    print("#" * 60)
    for label, user_prefs in advanced_profiles.items():
        print_recommendations(label, user_prefs, songs, k=5)

    # -----------------------------------------------------------------------
    # SCORING MODE COMPARISON
    # Run the High-Energy Pop profile under all four modes so the effect of
    # each strategy is visible side by side in the terminal output.
    # -----------------------------------------------------------------------
    # -----------------------------------------------------------------------
    # DIVERSITY PENALTY COMPARISON
    # The Chill Lofi profile is the clearest demonstration: without diversity
    # enforcement all three top slots go to LoRoom (same artist). With
    # diversity ON, the artist_penalty=0.5 halves the effective score for
    # each additional LoRoom song, pulling in songs from other artists.
    # -----------------------------------------------------------------------
    print("\n" + "#" * 60)
    print("  DIVERSITY PENALTY — before / after")
    print("  Profile: Chill Lofi (exposes the LoRoom repeat problem)")
    print("#" * 60)
    print_recommendations("Chill Lofi", chill_lofi, songs, k=5, diversity=False)
    print_recommendations("Chill Lofi", chill_lofi, songs, k=5, diversity=True)

    print("\n" + "#" * 60)
    print("  SCORING MODE COMPARISON")
    print("  Same profile (High-Energy Pop) — four different strategies")
    print("#" * 60)
    print(f"\n  Available modes: {', '.join(SCORING_MODES.keys())}")
    print("  Switching modes changes the weight table inside the scorer.")
    print("  The same 18 songs are scored every time — only the math changes.")
    print_mode_comparison("High-Energy Pop", high_energy_pop, songs, k=3)

    # -----------------------------------------------------------------------
    # VISUAL SUMMARY TABLES
    # Each table shows the same information as the plain output but in a
    # tabulate 'grid' format: every cell has a border, and the reasons column
    # expands vertically so no explanation is truncated or hidden.
    # Three representative profiles are shown — one standard, one adversarial,
    # one advanced — so the table format is demonstrated across different
    # scoring densities (few reasons vs many reasons per row).
    # -----------------------------------------------------------------------
    print("\n" + "#" * 80)
    print("  VISUAL SUMMARY TABLES  (tabulate grid format)")
    print("  Reasons column expands vertically — no explanations are truncated.")
    print("#" * 80)
    print_summary_table("High-Energy Pop", high_energy_pop, songs, k=5,
                        mode="balanced", diversity=True)
    print_summary_table("Chill Lofi — diversity ON", chill_lofi, songs, k=5,
                        mode="balanced", diversity=True)
    print_summary_table("Ghost Genre (metal)", ghost_genre, songs, k=5,
                        mode="balanced", diversity=True)


if __name__ == "__main__":
    main()
