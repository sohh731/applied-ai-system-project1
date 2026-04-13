"""
Command line runner for the Music Recommender Simulation.

This file defines user taste profiles and runs the recommender.
You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

try:
    from recommender import load_songs, recommend_songs
except ModuleNotFoundError:
    from src.recommender import load_songs, recommend_songs


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

# Profile A: Late-night study session
# Wants quiet, wordless background music -- high instrumentalness is critical
study_user = {
    "genre": "lofi",
    "mood": "focused",
    "target_energy": 0.40,
    "target_valence": 0.58,
    "likes_acoustic": True,
    "target_instrumentalness": 0.88,
    "target_speechiness": 0.03,
}

# Profile B: Morning workout
# Wants loud, fast, aggressive tracks -- low acousticness and high energy are critical
workout_user = {
    "genre": "rock",
    "mood": "intense",
    "target_energy": 0.91,
    "target_valence": 0.50,
    "likes_acoustic": False,
    "target_instrumentalness": 0.02,
    "target_speechiness": 0.06,
}

# Profile C: Sunday afternoon (the "edge case" profile)
# Only specifies energy and mood -- deliberately narrow to expose system weaknesses
# CRITIQUE TEST: can this profile tell apart intense rock from chill lofi?
# Answer: NO -- see critique section below
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


def print_recommendations(label: str, user_prefs: dict, songs: list, k: int = 3) -> None:
    """Prints a clean, readable block of recommendations for one user profile."""
    recommendations = recommend_songs(user_prefs, songs, k=k)

    print(f"\n{'=' * 60}")
    print(f"  PROFILE : {label}")
    print(f"  GENRE   : {user_prefs.get('genre', 'any').upper():<10}  "
          f"MOOD: {user_prefs.get('mood', '—').upper():<10}  "
          f"ENERGY: {user_prefs.get('target_energy', '—')}")
    print(f"{'=' * 60}")

    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        # Score bar — 9.5 is the max possible score
        filled = int((score / 9.5) * 20)
        bar = "#" * filled + "-" * (20 - filled)

        print(f"\n  #{rank}  {song['title']}  -  {song['artist']}")
        print(f"       Genre: {song['genre']:<12}  Mood: {song['mood']:<10}  Energy: {song['energy']}")
        print(f"       Score: {score:>5.2f} / 9.50  [{bar}]")
        print(f"       Why:")
        for reason in explanation.split("; "):
            print(f"         * {reason}")

    print(f"\n{'-' * 60}")


def main() -> None:
    songs = load_songs("data/songs.csv")
    print(f"\nLoaded songs: {len(songs)}")

    profiles = {
        "Study Session (lofi focused)": study_user,
        "Morning Workout (rock intense)": workout_user,
        "Vague Chill Listener (edge case)": vague_user,
    }

    for label, user_prefs in profiles.items():
        print_recommendations(label, user_prefs, songs, k=3)


if __name__ == "__main__":
    main()
