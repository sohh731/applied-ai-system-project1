# 🎵 VibeFinder 2.0 — Music Recommender with Reliability Testing

## Title and Summary

VibeFinder 2.0 is a music recommendation system that suggests songs based on explicit user preferences and verifies its own reliability through integrated testing. It matters because it demonstrates how a practical AI system can deliver explainable recommendations while also measuring its consistency, accuracy, and robustness.

---

## Original Project and Scope

**Original Project:** VibeFinder 1.0 Music Recommender Simulation.

VibeFinder 1.0 was a rule-based music recommender that matched users to songs in a static catalog using explicit preference fields such as genre, mood, and energy. Its original goal was to simulate how a basic content-based recommender ranks songs and to provide transparent explanations for each recommendation.

---

## What This Project Does

This project extends that core recommender by adding a **Reliability and Testing System** as the AI feature. It still takes user preferences like genre, mood, energy, and acousticness, scores an 18-song catalog using weighted formulas, and returns ranked recommendations with human-readable explanations. The new feature also evaluates the recommender itself, checking consistency, edge case behavior, and performance.

---

## Architecture Overview

The system has three main layers:

- **Input Layer**: Users interact through either a command-line interface (`src/main.py`) or a web interface (`src/app.py`).
- **Processing Layer**: The recommender engine (`src/recommender.py`) scores and ranks songs based on preference matching and distance metrics.
- **Evaluation Layer**: The reliability harness (`tests/test_recommender.py`) validates the recommender with automated tests for consistency, accuracy, and edge cases.

The architecture shows data flowing from user preferences and song data into the recommender, producing recommendations, and then feeding the results into a testing and evaluation loop.

![System Architecture Diagram](assets/User%20Preference-2026-04-27-014827.png)

---

## Setup Instructions

1. Clone the repository or open the project folder.
2. Create and activate a Python virtual environment:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate      # Windows
   source .venv/bin/activate     # Mac/Linux
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Run the CLI version:

   ```bash
   python src/main.py
   ```

5. Run the web version:

   ```bash
   streamlit run src/app.py
   ```

6. Run tests:

   ```bash
   pytest
   ```

7. Run the standalone evaluation harness:

   ```bash
   python eval.py
   ```

8. Run the multi-step agent demo:

   ```bash
   python src/agent.py
   ```

9. Run the explanation styles demo (fine-tuning / specialization):

   ```bash
   python src/explainer.py
   ```

10. Run the RAG augmentation demo:

    ```bash
    python src/rag.py
    ```

---

## Sample Interactions

### Example 1: High-Energy Pop

**Input:**
- Genre: `pop`
- Mood: `happy`
- Energy: `0.85`
- Acoustic: `False`

**Output:**
- `Sunrise City` by `LoRoom` — score 8.6 — matches pop, happy, and high energy.
- `Gym Hero` by `Beat Pulse` — score 7.2 — matches pop and energy, but not mood.
- `Rooftop Lights` by `Skyline` — score 6.9 — matches mood and energy, but not exact genre.

### Example 2: Chill Study Lofi

**Input:**
- Genre: `lofi`
- Mood: `focused`
- Energy: `0.40`
- Acoustic: `True`

**Output:**
- `Focus Flow` by `LoRoom` — score 9.0 — matches lofi, chill, low energy, and acoustic feel.
- `Library Rain` by `Study Vibes` — score 8.1 — matches mood, energy, and high acousticness.
- `Night Drive Loop` by `Synth Path` — score 6.8 — matches low energy and chilled vibe.

### Example 3: Edge Case Behavior

**Input:**
- Genre: `metal`
- Mood: `intense`
- Energy: `0.95`
- Acoustic: `False`

**Output:**
- The system returns the closest available matches by mood and energy, while making it clear that no exact genre match exists.
- It still provides ranked results with explanations describing why each song was chosen.

---

## Stretch Features (+8 pts)

Four optional stretch features were implemented. All three interactive
features (Agent, RAG, Explanation Style) are integrated directly into the
Streamlit web UI (`src/app.py`) as sidebar toggles — not isolated demos.
Each also ships as a standalone CLI script for grading convenience.

**Web UI integration** — run `streamlit run src/app.py` and enable any
combination from the sidebar:
- **Agent Mode** toggle — activates the 7-step decision chain; the full
  decision log is shown below the results
- **Rich Explanations (RAG)** toggle — appends genre + artist KB context
  to every recommendation
- **Explanation Style** selector — switches between baseline, technical,
  casual, and DJ output for all results

All three can be active simultaneously. The agent selects the scoring mode,
RAG augments the explanations, and the style transformer reformats them.

---

### +2 — Test Harness / Evaluation Script (`eval.py`)

`eval.py` is a standalone evaluation harness distinct from `pytest`. Where
pytest checks code correctness, this script measures AI *quality*:

- **10 predefined test cases** — 8 with known expected answers, 2 adversarial
- **Confidence score** per result = `top_score / 13.0` (max possible)
- **Consistency check** — every case is run 3 times; titles must be identical
- **Accuracy** — how many ground-truth top songs were predicted correctly
- **Performance** — all runs must complete under 1 second

**Result:** 10/10 passed — 8/8 accuracy (100%) — avg confidence 0.41 — all
consistent — all under 1 ms. Edge cases (ghost genre, empty preferences) score
`LOW` confidence, flagging that the system had no useful signal.

```
python eval.py
```

---

### +2 — Agentic Workflow Enhancement (`src/agent.py`)

`MusicAgent` implements a 7-step planning and decision chain. Every step is
printed as it runs, making the agent's reasoning fully observable:

```
[STEP 1: analyze_intent]      Dominant signal: BALANCED
[STEP 2: select_strategy]     Chosen mode: BALANCED
[STEP 3: retrieve_candidates] Top: 'Focus Flow'  score=7.99
[STEP 4: check_quality]       Confidence: 0.61  -> PASS
[STEP 5: fallback]            Skipped -- confidence meets threshold.
[STEP 6: diversity_check]     No artist monopoly in top-3.
[STEP 7: final_output]        Returning 3 recommendations. confidence: 0.61
```

For the ghost-genre case ("metal"), Step 4 triggers a fallback: the agent
retries with `discovery` mode (genre/era zeroed out) and raises confidence
from 0.38 to 0.46 before returning results.

```
python src/agent.py
```

---

### +2 — Fine-Tuning / Specialization (`src/explainer.py`)

`explainer.py` specializes the explanation layer into three distinct output
styles. The scoring math does not change — only the presentation is adapted.

**Baseline** (raw scoring output):
```
genre match 'lofi' (+1.0); energy proximity 1.00 (+3.0); mood match 'focused' (+2.0)
```

**Technical** (precision-focused, numerical breakdown):
```
SCORE BREAKDOWN  Focus Flow [lofi / focused]
  genre match                 EXACT MATCH (lofi) ............... +1.00
  mood match                  EXACT MATCH (focused) ............ +2.00
  energy proximity            100% match  (delta=0.00) ......... +3.00
TOTAL: 6.00 / 13.00  confidence=0.46
```

**Casual** (conversational friend-style):
```
This one is a great fit -- same genre you wanted (lofi), the mood is exactly
right (focused), and the energy level is 100% matched to what you want.
```

**DJ** (high-energy, punchy):
```
LOCKED IN -- lofi confirmed | focused vibes locked | energy 100% dialed.
```

Output measurably differs across all three styles and the baseline.

```
python src/explainer.py
```

---

### +2 — RAG Enhancement (`src/rag.py` + `data/genre_kb.json` + `data/artist_kb.json`)

Retrieves from **three** data sources and combines them:

| Source | File | Content |
|---|---|---|
| Structured | `data/songs.csv` | 18 songs with quantitative audio features — used for scoring |
| Genre docs | `data/genre_kb.json` | 15 genre entries: descriptions, listening context, related genres |
| Artist docs | `data/artist_kb.json` | 16 artist profiles: style, influences, typical listener, catalog notes |

**Fuzzy nearest-neighbor retrieval** — genre lookup uses character-bigram
Jaccard similarity so unknown genres like `"metal"` resolve to the closest
KB entry (`"rock"`, similarity > 0) rather than silently returning nothing.
This is the core idea of retrieval: find the most relevant document even
when the query does not exactly match a key.

**Baseline explanation** (songs.csv only):
```
genre match 'lofi' (+1.0); energy proximity 1.00 (+3.0)
```

**RAG-augmented explanation** (songs.csv + genre_kb + artist_kb):
```
genre match 'lofi' (+1.0); energy proximity 1.00 (+3.0)
  [GENRE KB: 'lofi' -- exact match]
  Description : Lo-fi hip hop blends jazz samples with deliberate low-fidelity texture.
  Best for    : studying, reading, coding, late-night focus sessions
  Related     : jazz, ambient, chillhop, classical
  Key trait   : Lofi is defined by deliberate imperfection...
  [ARTIST KB: 'LoRoom']
  Style       : Classic lo-fi hip hop. Warm vinyl crackle, jazz-sampled loops.
  Influences  : Nujabes, J Dilla, Tomppabeats
  Listener    : Students, coders, remote workers who need non-distracting music.
```

For the ghost-genre `"metal"` case, the fuzzy retriever returns `"rock"` as
the nearest match, flags the substitution, and the rock entry's `related`
field lists `metal` — a concrete discovery nudge.

Integrated into `src/app.py` as the **Rich Explanations (RAG)** sidebar toggle.

```
python src/rag.py
```

---

## Design Decisions and Trade-offs

- **Explainability over complexity:** I chose a rule-based scoring system rather than a learned model so the behavior is transparent and easy to justify. This is important for a portfolio project where a future employer must understand the logic quickly.
- **Reliability harness as the AI feature:** Instead of relying on external APIs or trained models, I built an integrated testing system to show that the recommender is not only functional but also measurable.
- **Limited catalog for clarity:** The project uses an 18-song dataset, which is small but sufficient to demonstrate scoring, diversity, and edge case handling. The trade-off is that recommendation quality is not as rich as a production system with thousands of songs.
- **No external APIs:** This project is designed to run offline with no API keys needed, which improves reproducibility and makes the portfolio easier to evaluate.

---

## Testing Summary

**8 out of 8 tests passed** (run `pytest` to reproduce). The system performed well on all standard and adversarial cases. The only meaningful limitation surfaced by testing is the ghost-genre silent failure: when a user requests a genre not in the catalog (e.g., "metal"), no test catches this because the system still returns 3 results — but those results are wrong. A future guardrail should detect this and warn the user.

### Test results at a glance

| Test | What it checks | Result |
|---|---|---|
| `test_recommend_returns_songs_sorted_by_score` | Top song matches genre + mood preference | PASSED |
| `test_explain_recommendation_returns_non_empty_string` | Every recommendation includes a non-empty explanation | PASSED |
| `test_scoring_modes_produce_different_results` | `balanced` vs `genre_first` modes both return results | PASSED |
| `test_diversity_reranking_changes_order` | Diversity ON changes recommendation order vs OFF | PASSED |
| `test_consistency_same_input_same_output` | Identical inputs produce identical outputs across two calls | PASSED |
| `test_performance_under_load` | Full scoring run completes in under 1.0 second | PASSED |
| `test_edge_case_handling` | Invalid energy (1.5) and empty preferences still return 3 results | PASSED |
| `test_accuracy_against_ground_truth` | 3/3 ground-truth cases predict the correct top song (100% accuracy) | PASSED |

### Guardrail behavior — concrete examples

**Edge case: invalid energy value (energy = 1.5, above valid range)**
- Input: `{"genre": "pop", "target_energy": 1.5}`
- Expected: system should not crash; still return 3 recommendations
- Actual: system returns 3 results using the raw value in proximity math (graceful degradation)

**Edge case: empty preferences (no fields provided)**
- Input: `{}`
- Expected: system falls back to raw energy proximity across the full catalog
- Actual: system returns 3 results ranked by energy proximity to 0.0 (default)

**Consistency check**
- Input: `{"genre": "pop", "mood": "happy", "target_energy": 0.8}` — called twice
- Both calls return `["Sunrise City", "Gym Hero", "Rooftop Lights"]` in the same order
- Confirms deterministic behavior: no randomness or session state affects results

**Accuracy on ground truth**
- `pop / happy / 0.8` → top result: `Sunrise City` ✓
- `lofi / chill / 0.4` → top result: `Focus Flow` ✓
- `rock / intense / 0.9` → top result: `Storm Runner` ✓
- Accuracy: 3/3 = 100%

**What was challenging:** Balancing the weights for genre, mood, and energy required several iterations. Too much genre weight (original: 3.0) caused the model to rank Gym Hero (pop, intense) above Rooftop Lights (indie pop, happy) for a user who wanted happy music — because genre points overwhelmed the mood signal. Reducing genre to 1.0 and raising energy to 3.0 fixed this without breaking any tests.

---

## Reflection

### 1. Limitations and Biases

The most significant limitation is **catalog size**. With only 18 songs and one or two songs per genre, genre filtering produces a single result and then noise. Positions 2–5 in a genre-filtered list are often from completely unrelated genres — not because the user would enjoy them, but because no better match exists.

A second bias is **silent genre failure**. When a user requests a genre not in the catalog (like "metal"), the system earns zero genre points for every song and quietly falls back to mood and energy. It returns confident-looking results without ever telling the user their primary preference was ignored. This is a form of feedback loop bias: a user who keeps getting rock results might eventually start asking for rock, not knowing the system never found their metal preference.

A third bias is **no penalty for a wrong match**. The scoring formula rewards matches but never punishes mismatches. A song with the wrong mood still earns its genre and energy points. This caused Gym Hero (pop, but intense mood) to outscore Rooftop Lights (indie pop, correct happy mood) until the genre weight was reduced from 3.0 to 1.0.

Finally, the catalog is **culturally narrow** — almost entirely Western and English-language, with no representation of K-pop, Latin, Afrobeats, or classical Indian music. A user from any of those traditions would receive meaningless recommendations.

---

### 2. Could This AI Be Misused?

At its current scale — 18 made-up songs, no user accounts, no external APIs — the system has minimal misuse risk. However, the design patterns it demonstrates could become harmful at production scale:

- **Filter bubble amplification**: A real recommender using only explicit preferences and no feedback loop could reinforce narrow taste indefinitely. A user who asks for one genre would never discover anything outside it.
- **Confidence without accuracy**: The system presents ranked results with scores and explanations even when the match is poor (ghost genre, all-neutral preferences). At scale, users could mistake confident presentation for accurate recommendations.
- **Preference profiling**: A deployed version that logs preference inputs over time would accumulate sensitive behavioral data (mood states, energy preferences, listening times) without the user realizing it.

**Prevention measures I would add before deploying:**
- A genre-not-found warning before scoring, instead of silent fallback.
- A confidence label on recommendations when the top score is below a threshold (e.g., "low confidence — no songs matched your genre").
- Clear data handling disclosure if any inputs are logged.

---

### 3. What Surprised Me While Testing Reliability

The most surprising result was the **all-neutral profile** (every preference set to 0.5, genre = "any"). I expected this to be a boring but acceptable edge case. Instead, the top 5 results spanned a range of only 0.14 points — the system had essentially no signal to work with and returned an arbitrary list. What surprised me was how *confident* the output looked. Scores, explanations, and score bars appeared exactly as normal. There was no indication from the output that the recommendations were meaningless. The system's presentation layer is completely decoupled from its confidence level, which is a real reliability problem.

The second surprise was that **8 out of 8 tests passed on the first full run**, including the accuracy ground-truth test (3/3 correct top songs). I had expected at least one fragile test. The consistency test — calling the recommender twice with identical inputs and comparing the results — was the simplest test to write but also the most reassuring: it confirmed there is no hidden randomness or session state anywhere in the scoring pipeline.

---

### 4. AI Collaboration — One Helpful Suggestion and One Flawed Suggestion

**How I used AI during this project:**
I used Claude as a thinking partner throughout: drafting initial scoring formulas, generating the song catalog, reviewing test cases, and writing sections of this documentation. The workflow was iterative — I would describe what I wanted, review what it produced, test it against real outputs, and then correct course.

**One helpful suggestion:**
When I asked how to prevent all top results from going to the same artist, the AI suggested a **greedy diversity re-ranker** with a configurable artist penalty applied after scoring. The key insight was to apply the penalty during selection (not during scoring) so the raw scores are preserved and can be shown in the explanation. This was exactly right — it made the diversity fix transparent to the user. The explanation now shows `* diversity penalty applied (raw=6.72)` so the user can see the reranking happened. I would not have thought of separating the scoring step from the selection step on my own.

**One flawed suggestion:**
The AI initially recommended setting the genre weight to **3.0** with the reasoning that "genre mismatch is the most jarring failure in a music recommender." That sounded reasonable. But the AI did not know my catalog had only one or two songs per genre. With a 3.0 genre weight and a one-song-per-genre catalog, the top result was always determined entirely by genre — mood and energy had almost no effect. Worse, Gym Hero (pop, but wrong mood) kept outranking Rooftop Lights (indie pop, correct mood) because the 3.0 genre match overwhelmed the 2.0 mood signal. I had to run the actual experiments to discover this. Reducing the genre weight to 1.0 fixed the ranking without breaking any tests. The AI's suggestion was calibrated for a large catalog; it was wrong for mine.

---

## Portfolio

**GitHub Repository:** [https://github.com/sohh731/applied-ai-system-project1](https://github.com/sohh731/applied-ai-system-project1)

**Video Walkthrough (Loom):** *(add your Loom link here after recording)*

### What This Project Says About Me as an AI Engineer

I built VibeFinder 2.0 to prove something specific: that an AI system does not need to be a black box to be useful. Every decision this system makes — how a song is scored, why it ranks above another, when the agent falls back to a different mode — is visible, explainable, and testable. That design choice was deliberate, and it shaped every part of the project.

Most of my time went into measurement, not features. I wrote adversarial test profiles specifically designed to break the system, then studied why they broke it. When the genre weight was 3.0, the system looked confident but was wrong in ways I could only catch by reading the math. The fix — reducing genre weight from 3.0 to 1.0 — was not obvious until I ran the experiments, and I only had the tools to run those experiments because I had built the evaluation harness first.

That is what I want this project to say about me: I build systems I can question. A recommender that returns plausible-sounding answers is not hard to build. A recommender whose every output can be explained, challenged, and improved — with a test suite to prove it did not regress — is harder. That gap between plausible and verifiable is where I am trying to work.
