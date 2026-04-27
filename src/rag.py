"""
rag.py — Dual-Source Retrieval-Augmented Recommendation for VibeFinder 2.0

Retrieves from TWO separate document sources and combines them to produce
explanations that are measurably richer than the baseline CSV-only output.

  Source 1 (structured):    data/songs.csv
                            18 songs with quantitative audio features.
                            Used by the scoring engine for numeric matching.

  Source 2 (genre docs):    data/genre_kb.json
                            15 genre knowledge-base entries.
                            Retrieved by genre string (fuzzy-matched so that
                            unknown genres like 'metal' resolve to the nearest
                            known genre, e.g. 'rock').

  Source 3 (artist docs):   data/artist_kb.json
                            16 artist profiles: style, influences, listener
                            type, and catalog notes.
                            Retrieved by artist name exact match.

Retrieval strategy:
  For each recommended song the RAG pipeline:
    1. Looks up the song's genre in Source 2 via fuzzy nearest-neighbor
       (character overlap ratio). If the exact genre is absent — e.g.
       user requests 'metal' and gets a 'rock' song — the closest KB entry
       is returned with a note explaining the substitution.
    2. Looks up the song's artist in Source 3 by exact name.
    3. Appends both retrieved context blocks to the baseline explanation.

Impact on output quality:
  Baseline:   "genre match 'lofi' (+1.0); energy proximity 1.00 (+3.0)"
  Augmented:  same scores PLUS --
              [GENRE: Lo-fi hip hop blends jazz samples ... Ideal for: studying]
              [ARTIST: LoRoom — Classic lo-fi hip hop. Influences: Nujabes...]

Usage:
    python src/rag.py                       # demo with before/after output

    from src.rag import load_kbs, rag_recommend
    genre_kb, artist_kb = load_kbs()
    results = rag_recommend(user_prefs, songs, genre_kb, artist_kb, k=3)
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(__file__))

try:
    from recommender import load_songs, recommend_songs
except ModuleNotFoundError:
    from src.recommender import load_songs, recommend_songs


# ---------------------------------------------------------------------------
# LOADERS
# ---------------------------------------------------------------------------

def load_genre_kb(path: str) -> dict:
    """Loads the genre knowledge base from a JSON file."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_artist_kb(path: str) -> dict:
    """Loads the artist knowledge base from a JSON file."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_kbs(
    genre_path: str = "data/genre_kb.json",
    artist_path: str = "data/artist_kb.json",
) -> tuple:
    """
    Convenience loader: returns (genre_kb, artist_kb).
    Tries the given paths; falls back to ../data/ if running from src/.
    """
    for base in ("", "../"):
        try:
            gkb = load_genre_kb(base + genre_path)
            akb = load_artist_kb(base + artist_path)
            return gkb, akb
        except FileNotFoundError:
            continue
    raise FileNotFoundError(
        f"Could not find knowledge base files at '{genre_path}' or '../{genre_path}'"
    )


# ---------------------------------------------------------------------------
# FUZZY GENRE RETRIEVAL
#
# Standard dict lookup fails silently when the user's genre is not in the KB
# (e.g. 'metal', 'k-pop', 'trap').  Instead of returning None, the fuzzy
# retriever computes a character-overlap similarity score between the
# requested genre and every KB key, then returns the closest match.
#
# This turns an exact-match lookup into a nearest-neighbor retrieval step,
# which is the core idea of retrieval-augmented systems: find the most
# relevant document even when the query doesn't exactly match a key.
# ---------------------------------------------------------------------------

def _char_overlap_ratio(a: str, b: str) -> float:
    """
    Simple character-level overlap similarity between two strings.
    Returns a float in [0.0, 1.0].  Higher = more similar.

    Uses the Jaccard coefficient on character bigrams so that
    'metal' -> 'rock' scores lower than 'indie pop' -> 'pop'.
    """
    def bigrams(s: str) -> set:
        s = s.lower().strip()
        return {s[i:i+2] for i in range(len(s) - 1)} if len(s) > 1 else {s}

    ba, bb = bigrams(a), bigrams(b)
    if not ba and not bb:
        return 1.0
    if not ba or not bb:
        return 0.0
    return len(ba & bb) / len(ba | bb)


def retrieve_genre_context(genre: str, kb: dict) -> tuple:
    """
    Retrieves the best-matching genre KB entry for the given genre string.

    Returns:
        (entry_dict, matched_key, is_exact)
        entry_dict:  the KB entry (never None — falls back to closest)
        matched_key: the key that was actually used
        is_exact:    True if genre matched a KB key exactly
    """
    key = genre.lower().strip()

    # Exact match first
    if key in kb:
        return kb[key], key, True

    # Nearest-neighbor fallback
    best_key   = max(kb.keys(), key=lambda k: _char_overlap_ratio(key, k))
    best_score = _char_overlap_ratio(key, best_key)

    # Even the best match might be terrible (score near 0) — flag that
    return kb[best_key], best_key, False


def retrieve_artist_context(artist: str, kb: dict) -> dict | None:
    """
    Retrieves the artist KB entry by exact name.
    Returns None if the artist is not in the knowledge base.
    """
    return kb.get(artist)


# ---------------------------------------------------------------------------
# AUGMENTATION
# ---------------------------------------------------------------------------

def augment_explanation(
    song: dict,
    base_explanation: str,
    genre_context: tuple,
    artist_context: dict | None,
    user_genre: str = "",
) -> str:
    """
    Appends retrieved genre and artist context to the base explanation.

    Args:
        song:             song dict
        base_explanation: semicolon-separated reason string from recommend_songs
        genre_context:    (entry, matched_key, is_exact) from retrieve_genre_context
        artist_context:   artist KB entry dict, or None
        user_genre:       genre the user originally requested
    """
    lines = [base_explanation]

    entry, matched_key, is_exact = genre_context
    song_genre = song.get("genre", "?")

    # --- Genre block ---
    if is_exact:
        lines.append(f"  [GENRE KB: '{song_genre}' — exact match]")
    else:
        lines.append(
            f"  [GENRE KB: '{song_genre}' not in knowledge base — "
            f"nearest match is '{matched_key}' (fuzzy retrieval)]"
        )
    lines.append(f"  Description : {entry.get('description', '')}")
    lines.append(f"  Best for    : {entry.get('listening_context', '')}")
    related = ", ".join(entry.get("related_genres", []))
    if related:
        lines.append(f"  Related     : {related}")
    distinguishes = entry.get("what_distinguishes", "")
    if distinguishes:
        lines.append(f"  Key trait   : {distinguishes}")

    # Warn when the song's genre differs from what the user asked for
    if user_genre and user_genre not in ("any", "") and user_genre != song_genre:
        lines.append(
            f"  [NOTE: you asked for '{user_genre}' — this song is '{song_genre}'. "
            f"See 'Related' above for closer options.]"
        )

    # --- Artist block ---
    if artist_context:
        artist = song.get("artist", "?")
        lines.append(f"  [ARTIST KB: '{artist}']")
        lines.append(f"  Style       : {artist_context.get('style', '')}")
        influences = ", ".join(artist_context.get("influences", []))
        if influences:
            lines.append(f"  Influences  : {influences}")
        listener = artist_context.get("typical_listener", "")
        if listener:
            lines.append(f"  Listener    : {listener}")
        notes = artist_context.get("catalog_notes", "")
        if notes:
            lines.append(f"  Note        : {notes}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# RAG RECOMMEND — main public function
# ---------------------------------------------------------------------------

def rag_recommend(
    user_prefs: dict,
    songs: list,
    genre_kb: dict,
    artist_kb: dict,
    k: int = 5,
    mode: str = "balanced",
    diversity: bool = True,
) -> list:
    """
    Runs the recommender then augments each explanation with retrieved
    context from two knowledge bases (genre + artist).

    Returns:
        list of (song_dict, score, augmented_explanation) tuples
    """
    base_results = recommend_songs(
        user_prefs, songs, k=k, mode=mode, diversity=diversity
    )
    user_genre = user_prefs.get("genre", "")

    augmented = []
    for song, score, base_exp in base_results:
        genre_ctx  = retrieve_genre_context(song.get("genre", ""), genre_kb)
        artist_ctx = retrieve_artist_context(song.get("artist", ""), artist_kb)
        aug_exp    = augment_explanation(
            song, base_exp, genre_ctx, artist_ctx, user_genre
        )
        augmented.append((song, score, aug_exp))
    return augmented


# ---------------------------------------------------------------------------
# DEMO
# ---------------------------------------------------------------------------

def main() -> None:
    try:
        songs = load_songs("data/songs.csv")
        genre_kb, artist_kb = load_kbs()
    except FileNotFoundError:
        songs = load_songs("../data/songs.csv")
        genre_kb, artist_kb = load_kbs("../data/genre_kb.json", "../data/artist_kb.json")

    cases = [
        (
            "Lofi / focused  (standard case — all sources hit)",
            {"genre": "lofi", "mood": "focused", "target_energy": 0.40,
             "target_instrumentalness": 0.88, "target_acousticness": 0.78},
        ),
        (
            "Metal / intense  (ghost genre — fuzzy retrieval fires)",
            {"genre": "metal", "mood": "intense", "target_energy": 0.95},
        ),
    ]

    for label, prefs in cases:
        print("\n" + "=" * 72)
        print(f"  DEMO: {label}")
        print("=" * 72)

        base_results = recommend_songs(prefs, songs, k=2, diversity=True)
        rag_results  = rag_recommend(prefs, songs, genre_kb, artist_kb,
                                     k=2, diversity=True)

        for i, ((b_song, b_score, b_exp), (_r_song, _r_score, r_exp)) in enumerate(
            zip(base_results, rag_results), 1
        ):
            print(f"\n  #{i}  {b_song['title']} - {b_song['artist']}  "
                  f"(score={b_score:.2f})")

            print("\n  -- BASELINE (data/songs.csv only) --")
            for part in b_exp.split(";"):
                print(f"  {part.strip()}")

            print("\n  -- RAG AUGMENTED (songs.csv + genre_kb.json + artist_kb.json) --")
            for line in r_exp.splitlines():
                print(f"  {line}")
            print()


if __name__ == "__main__":
    main()
