# 🎵 Music Recommender Simulation

## Project Summary

VibeFinder 1.0 is a content-based music recommender. It takes a user's stated preferences — genre, mood, and target energy level — and scores every song in an 18-song catalog against those preferences using a weighted formula. Songs are then ranked from best match to worst, and the top results are returned with a plain-language explanation of exactly why each song was chosen.

The system was built to make the inner workings of a recommender fully visible. Every score can be traced back to specific feature matches. This makes it easy to see where the algorithm succeeds, where it fails, and why — which is the main point of the project.

---

## How The System Works

Real-world recommenders like Spotify or YouTube analyze patterns across millions of users and songs — tracking what you skip, replay, or save — to build a detailed model of your taste. They use collaborative filtering (what people like you enjoyed) and content-based filtering (matching audio features of songs you liked to new ones). This simulation focuses on the content-based side: it takes a user's stated preferences and compares them directly against each song's features using a weighted scoring formula. Rather than learning from behavior over time, the system prioritizes explicit taste signals — genre match first, then mood, then how close a song's energy level is to what the user wants. The goal is a transparent, explainable recommender where you can see exactly why each song was chosen.

### Song Features

Each `Song` object stores the following attributes:

| Feature | Type | Description |
|---|---|---|
| `id` | int | Unique identifier |
| `title` | str | Song title |
| `artist` | str | Artist name |
| `genre` | str | Genre label (e.g. pop, lofi, rock) |
| `mood` | str | Mood label (e.g. happy, chill, intense) |
| `energy` | float (0–1) | How energetic the track feels |
| `tempo_bpm` | float | Beats per minute |
| `valence` | float (0–1) | Musical positivity (high = upbeat) |
| `danceability` | float (0–1) | How suitable the track is for dancing |
| `acousticness` | float (0–1) | How acoustic (vs. electronic) the track sounds |

### UserProfile Features

Each `UserProfile` stores what the user has told the system about their taste:

| Feature | Type | Description |
|---|---|---|
| `favorite_genre` | str | The genre they want to hear |
| `favorite_mood` | str | The mood they are looking for |
| `target_energy` | float (0–1) | Their preferred energy level |
| `likes_acoustic` | bool | Whether they prefer acoustic over electronic sounds |

### Algorithm Recipe

The scoring formula is the core decision engine. Every song is judged by the same seven rules in order, and the results are summed into a single score:

| Rule | Feature | Max Points | How it works |
|---|---|---|---|
| 1 | Genre match | **+1.0** | Full points if `song.genre == user.favorite_genre`, zero otherwise |
| 2 | Mood match | **+2.0** | Full points if `song.mood == user.favorite_mood`, zero otherwise |
| 3 | Energy proximity | **up to +3.0** | `3.0 × (1 - \|target_energy - song.energy\|)` — closer = more points |
| 4 | Acousticness proximity | **up to +1.0** | `1.0 × (1 - \|target_acousticness - song.acousticness\|)` |
| 5 | Instrumentalness proximity | **up to +1.0** | `1.0 × (1 - \|target_instrumentalness - song.instrumentalness\|)` |
| 6 | Valence proximity | **up to +0.5** | `0.5 × (1 - \|target_valence - song.valence\|)` |
| 7 | Speechiness proximity | **up to +0.5** | `0.5 × (1 - \|target_speechiness - song.speechiness\|)` |

**Maximum possible score: 9.0 points.**
All songs are then sorted by total score (highest first) and the top-k are returned as recommendations.

**Why these weights?** These are the final weights after a sensitivity experiment. Genre started at 3.0 but was reduced to 1.0 because with only 18 songs in the catalog, a heavy genre weight caused one song to dominate every profile and left positions #2–#5 as noise. Energy was raised to 3.0 because it is the strongest single numerical signal for "vibe" — the gap between a calm study song and a high-intensity workout song is almost entirely captured by energy alone. Mood (2.0) sets the listening context. The remaining features act as fine-tuning.

### Data Flow Diagram

The diagram below shows how a single song travels from the CSV file to a ranked result:

![Data Flow Diagram](mermaid-diagram.png)

```mermaid
flowchart TD
    PREFS[/"User Preferences\ngenre · mood · target_energy\ntarget_acousticness · target_instrumentalness · ..."/]
    CSV[("data/songs.csv\n18 songs")]

    CSV --> LOAD["load_songs()\nparse CSV rows into list of dicts"]
    PREFS --> RECS
    LOAD --> RECS["recommend_songs(user_prefs, songs, k)"]

    RECS --> LOOP["For each song in the catalog"]
    LOOP --> SCORE["score_song(user_prefs, song)"]

    SCORE --> G["Genre match?    → +3.0"]
    G     --> M["Mood match?     → +2.0"]
    M     --> EN["Energy proximity    → up to +1.5"]
    EN    --> AC["Acousticness proximity  → up to +1.0"]
    AC    --> IN["Instrumentalness proximity → up to +1.0"]
    IN    --> VA["Valence proximity   → up to +0.5"]
    VA    --> SP["Speechiness proximity   → up to +0.5"]
    SP    --> SUM(["Total score + reasons list"])

    SUM -->|"next song"| LOOP
    LOOP -->|"all 18 songs scored"| RANK["Ranking Rule\nSort all scores descending"]
    RANK --> OUT[/"Top-k results\nsong · score · explanation string"/]
```

**Reading the diagram:**
- The two inputs — user preferences and the CSV — feed into `recommend_songs()` at the top
- The loop node represents `recommend_songs()` iterating; each pass calls `score_song()` once
- Inside `score_song()` the seven scoring steps run in order and accumulate a total
- After all songs are scored the loop exits into the Ranking Rule (a single `sorted()` call)
- The output is a list of `(song, score, explanation)` tuples, sliced to the top-k

---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python -m src.main
```

### Running Tests

Run the starter tests with:

```bash
pytest
```

You can add more tests in `tests/test_recommender.py`.

---

## Experiments You Tried

### Standard Profiles — Top 5 Results

The screenshots below show terminal output for the three main user profiles (High-Energy Pop, Chill Lofi, Deep Intense Rock) run with `python src/main.py`.

![Terminal Output 1](Screenshot1.png)
![Terminal Output 2](Screenshot 2.png)
![Terminal Output 3](Screenshot3.png)
![Terminal Output 4](Screenshot4.png)
![Terminal Output 5](Screenshot5.png)

### Adversarial / Edge Case Stress Tests

These screenshots show the four adversarial profiles designed to expose weaknesses in the scoring logic — conflicting preferences, ghost genres, impossible feature combinations, and all-neutral preferences.

![Stress Test 1](Screenshot stress test 1.png)
![Stress Test 2](Screenshot stress test 2.png)
![Stress Test 3](Screenshot stress test 3.png)
![Stress Test 4](Screenshot stress test 4.png)
![Stress Test 5](Screenshot stress test 5.png)
![Stress Test 6](Screenshot stress test 6.png)
![Stress Test 7](Screenshot stress test 7.png)
![Stress Test 8](Screenshot stress test 8.png)
![Stress Test 9](Screenshot stress test 9.png)

---

## Limitations and Risks

### Potential Biases

**Genre over-prioritization.** Genre carries 3.0 points — more than mood, energy, acousticness, instrumentalness, valence, and speechiness combined (max 5.5 pts). This means a mediocre pop song that matches the user's genre will almost always outscore a genuinely great lofi song that matches every numerical preference. The system might over-prioritize genre, ignoring great songs that fit the user's mood and energy perfectly but sit in the "wrong" genre bucket.

**Catalog representation bias.** The 18-song catalog skews toward Western genres and mostly reflects a young, English-speaking listener's taste. Genres like K-pop, Latin, Afrobeats, or classical Indian music are absent. A user whose preferred genre is not in the catalog will get zero genre-match points for every song, making the recommender fall back on mood and energy alone — a much weaker signal.

**Mood label subjectivity.** Mood labels like "chill" or "intense" were assigned manually and reflect one person's interpretation. Two people might describe the same song differently. The system treats these labels as objective facts, which means it will confidently match or mismatch based on labels that could be wrong.

**No diversity enforcement.** The ranking rule returns the top-k highest-scoring songs with no diversity check. For a lofi-focused user, all 5 recommendations could be lofi tracks — technically correct but offering no discovery or variety.

**Cold start problem.** The system only knows what the user explicitly tells it. A new user who says `genre: lofi` but does not specify `target_energy` or `target_instrumentalness` will get weaker, less personalized results because optional features default to neutral values rather than learned preferences.

### Other Limitations

- Works on a catalog of only 18 songs — real recommenders use millions
- Does not understand lyrics, language, cultural context, or artist relationships
- Scores are not normalized, so adding or removing features changes the scale and breaks comparability across experiments

---

## Reflection

[**Full Model Card**](model_card.md)

**What I learned about how recommenders turn data into predictions:**
The scoring formula is just arithmetic — multiply a weight by a proximity ratio and add it up. But the output actually feels like a recommendation because the weights encode real musical intuition. Energy is weighted heaviest (3.0) because the gap between a calm study session and an intense workout is almost entirely captured by a single number. Mood and genre add categorical context. What surprised me is that this simple chain of additions, when tuned correctly, produces results that feel right most of the time — not because the system understands music, but because the features were chosen to reflect things humans actually care about.

**What I learned about where bias or unfairness shows up:**
The most important bias I found was the ghost genre problem: if a user asks for a genre that does not exist in the catalog, the system silently ignores that preference and returns confident-looking results anyway. A user who asks for metal and gets rock might never realize their request was never honored. That is a real form of unfairness — the system appears to be helping when it is not. The other major bias is the small catalog: with only one or two songs per genre, the system creates a filter bubble where users never discover anything outside the single best match for their genre. Both problems would be invisible to a user who did not look closely at the scores.
