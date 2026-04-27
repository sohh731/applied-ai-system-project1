# Model Card: AI Music Recommender with Reliability & Testing System

## 1. Model Name

**VibeFinder 2.0**

---

## 2. Goal / Task

VibeFinder 2.0 is an AI-powered music recommender that uses a comprehensive reliability and testing system to ensure consistent, accurate recommendations. The system evaluates its own performance through automated metrics and validation.

Unlike the original rule-based version, this system includes built-in quality assurance that measures accuracy, consistency, and performance - treating the recommender itself as an AI system that can be tested and improved.

---

## 3. Data Used

The catalog has 18 songs.

Each song has 17 features total: 12 original features plus 5 advanced features added during development.

**Original features:** genre, mood, energy, tempo, valence, danceability, acousticness, speechiness, instrumentalness, id, title, artist.

**Advanced features added (Challenge 1):**
- `popularity` (0–100) — mainstream appeal score
- `release_decade` (1970–2020) — era of the song
- `detail_mood` — granular mood tag (e.g. euphoric, aggressive, peaceful, nostalgic, melancholic)
- `liveness` (0–1) — studio clean (0) vs. live concert feel (1)
- `loudness` (0–1) — quiet/gentle (0) vs. loud/dynamic (1)

Genres in the catalog: pop, lofi, rock, ambient, jazz, synthwave, indie pop, hip-hop, R&B, classical, country, EDM, folk, reggae, and blues.

Moods in the catalog: happy, chill, intense, relaxed, focused, moody, motivated, romantic, melancholic, nostalgic, euphoric, dreamy, and sad.

The catalog only has one or two songs per genre. That is a big limitation. With so few songs, the recommendations can feel repetitive.

The songs are made up for this simulation. They do not reflect real listening data. Genres like K-pop, Latin, Afrobeats, and classical Indian music are not represented at all.

**Testing Component:** Uses automated test cases with ground truth expectations to evaluate system performance.

---

## 4. Algorithm Summary

The system combines rule-based scoring with comprehensive reliability testing.

**Rule-Based Scoring:** Every song gets a score by comparing it to user preferences. Higher score = better match.

The score has two types of checks:

**Categorical checks (yes or no):**
- If the song's genre matches the user's preferred genre, it earns full genre points.
- If the song's mood matches the user's preferred mood, it earns full mood points.
- If the song does not match, it earns zero — there is no penalty, just no reward.

**Proximity checks (how close is close enough):**
- For features like energy, acousticness, and instrumentalness, the system measures the gap between the song's value and the user's target.
- The closer the match, the more points the song earns. A perfect match earns the full weight. A gap of 1.0 earns zero.
- Formula: `points = weight × (1.0 - |target - actual|)`

**Weights — original features:**

| Feature | Max Points |
|---|---|
| Genre match | 1.0 |
| Mood match | 2.0 |
| Energy proximity | 3.0 |
| Acousticness proximity | 1.0 |
| Instrumentalness proximity | 1.0 |
| Valence proximity | 0.5 |
| Speechiness proximity | 0.5 |

**Weights — advanced features (optional; only active when user specifies them):**

| Feature | Max Points | Scoring rule |
|---|---|---|
| Popularity proximity | 0.5 | Normalized 0–1 before proximity formula |
| Decade preference | 0.5 | Exact match = 1.0; loses 0.25 pts per decade away |
| Detail mood match | 1.5 | Exact tag match only; no partial credit |
| Liveness proximity | 0.5 | Proximity formula |
| Loudness proximity | 0.5 | Proximity formula |

**Reliability Testing System:**
- **Consistency Checks:** Validates that identical inputs produce identical outputs
- **Accuracy Metrics:** Compares recommendations against expected ground truth
- **Performance Monitoring:** Measures execution time and resource usage
- **Edge Case Validation:** Tests system behavior with invalid or extreme inputs
- **Mode Comparison:** Ensures different scoring strategies produce meaningful variations
| Liveness proximity | 0.5 | Standard proximity formula |
| Loudness proximity | 0.5 | Standard proximity formula |

**Maximum possible score: 13.0 points** (all optional features active).
**Baseline score (no advanced features): 9.0 points.**

**Scoring modes (Challenge 2 — Strategy pattern):**
The system supports four interchangeable ranking strategies. Each mode is a partial weight override merged onto the baseline at score time — no duplicated logic.

| Mode | Key change | Best for |
|---|---|---|
| `balanced` | baseline weights | general use (default) |
| `genre_first` | genre boosted to 4.0 | strict genre purists |
| `mood_first` | mood boosted to 4.0, detail_mood to 3.0 | vibe seekers who don't care about genre |
| `energy_focused` | energy boosted to 6.0 | intensity matching (workout vs. study) |
| `discovery` | genre and decade zeroed out | open exploration across all genres |

**Diversity re-ranking (Challenge 3):**
After scoring, a greedy re-ranking pass applies an artist penalty (default 0.5×) and genre penalty (default 0.8×) for each repeat in the top-k. This prevents all slots from being filled by the same artist or genre. The penalty is shown in the explanation string so it is transparent.

After every song is scored, they are sorted from highest to lowest. The top results are returned with an explanation of which features contributed points.

---

## 5. Observed Behavior / Biases

**Filter bubble from small catalog.**
With only one rock song in the catalog, a rock fan gets Storm Runner as #1 and then falls off a cliff. Songs from completely unrelated genres fill spots #2 through #5. The system looks confident but positions #3–#5 are basically random noise.

**No penalty for a bad mood match.**
The system rewards a genre match but never punishes a mood mismatch. A pop song with the wrong mood (intense instead of happy) still earns its genre points and energy points. This caused Gym Hero (pop, intense) to outrank Rooftop Lights (indie pop, happy) for a user who wanted happy music — until the genre weight was reduced from 3.0 to 1.0.

**Ghost genre — silent failure.**
If the user asks for a genre that does not exist in the catalog (like "metal"), every song scores zero genre points. The system quietly falls back to mood and energy and returns confident-looking results. It never tells the user their genre preference was completely ignored.

**Calm preferences are penalized more.**
A user who wants energy 0.10 loses a lot more points on high-energy songs than a user who wants energy 0.50. The proximity formula treats the gap as linear, but for very extreme preferences, the system consistently struggles to find a good match.

**Artist repeat problem — identified and fixed.**
Without diversity enforcement, all top slots can go to the same artist. For the Chill Lofi profile, the top three results were all LoRoom songs. This was fixed in Challenge 3 with a greedy diversity re-ranker: each additional song by the same artist has its effective score halved (artist_penalty=0.5). The fix works — with diversity ON, the top 5 Chill Lofi results span jazz, ambient, folk, and classical rather than three identical lofi tracks.

---

## 6. Evaluation Process

Seven profiles were tested: three standard and four adversarial.

| Profile | Top Result | Score | Matched Intuition? |
|---|---|---|---|
| High-Energy Pop (pop, happy, 0.85) | Sunrise City | 8.86 | Yes |
| Chill Lofi (lofi, focused, 0.40) | Focus Flow | 9.48 | Yes |
| Deep Intense Rock (rock, intense, 0.91) | Storm Runner | 8.98 | Yes |
| Conflicting energy + sad mood | 3 AM Diner | 6.79 | Partially |
| Ghost genre (metal) | Storm Runner (rock) | 7.68 | No |
| EDM + fully instrumental | Drop Zone | 8.71 | Partially |
| All-neutral preferences | Gravel Road Home | 5.16 | No |

**What surprised me most:**
The High-Energy Pop profile kept putting Gym Hero (pop, intense) at #2 even though the user wanted *happy* music. Gym Hero earned its genre points (pop == pop) and strong energy proximity points. The system does not penalize a mood mismatch — it just gives zero mood points. So Gym Hero and Rooftop Lights competed on genre + energy alone, and Gym Hero won because genre used to carry 3.0 points.

**Weight experiment:**
Reducing genre weight from 3.0 to 1.0 and increasing energy weight from 1.5 to 3.0 caused Rooftop Lights (indie pop, happy) to jump to #2. That felt more musically correct. Both automated tests still passed after the change.

**Most revealing adversarial test:**
The all-neutral profile (every preference at 0.5, no genre set) returned five songs within 0.14 points of each other. The system had no meaningful signal to work with and returned an essentially arbitrary result.

**Scoring mode comparison (Challenge 2):**
Running the same High-Energy Pop profile under all four modes showed clear differences. `genre_first` immediately pushed Gym Hero back to #2 (genre dominates). `mood_first` surfaced all three happy-mood songs in the top 3. `energy_focused` ranked by intensity alone — Gym Hero (0.93) and Storm Runner (0.91) climbed because their energy was closest to 0.85. `discovery` (genre=0) produced the most surprising results: songs from reggae and ambient appeared that would never surface under normal genre filtering.

**Diversity re-ranking (Challenge 3):**
Before diversity enforcement: Chill Lofi top-2 were both LoRoom. After: LoRoom gets slot #1, then Coffee Shop Stories (jazz), Spacewalk Thoughts (ambient), Library Rain (paper lanterns — penalized, raw=6.72), and Autumn Sonata (classical) fill the rest. Four different artists and four different genres in five slots.

---

## 7. Intended Use and Non-Intended Use

**Intended use:**
This system is for classroom exploration of how content-based recommender systems work. It is designed to show students how weighted scoring, feature matching, scoring modes, diversity enforcement, and catalog limitations affect the results a system returns.

It works best when a user has clear, specific preferences and their preferred genre exists in the catalog.

**Not intended for:**
- Real music discovery. The catalog is 18 made-up songs.
- Production use of any kind.
- Personalization over time. The system has no memory between sessions.
- Users who cannot or do not want to state their preferences explicitly.
- Representing diverse global music taste. The catalog is almost entirely Western and English-language.

---

## 8. Ideas for Improvement

**1. Expand the catalog.**
The most important fix is adding more songs — at least 10 per genre. Right now, genre filtering produces one result and then noise. With a bigger catalog, genre filtering would produce a meaningful shortlist that mood and energy could refine.

**2. Diversity enforcement — implemented, but tuning needed.**
The artist and genre diversity re-ranker was built (Challenge 3). It works — it breaks up the LoRoom monopoly in the Chill Lofi profile. But the default penalties (artist=0.5, genre=0.8) were chosen by intuition, not by testing. A better version would let users control these values, or learn them from feedback.

**3. Warn the user when their genre has no matches.**
Before scoring, check whether the user's genre exists in the catalog. If it does not, tell the user instead of silently falling back. Something like "No songs found for genre: metal — showing closest matches by mood and energy instead" would be far more honest than returning confident-looking wrong results.

**4. Replace single energy target with a range.**
Let users say "energy between 0.6 and 0.9" instead of a single point. This would reduce the penalty for extreme preferences and let users express "somewhere in this zone" rather than a precise number.

**5. Add a mood-mismatch penalty.**
Right now the system only rewards correct matches — it never punishes wrong ones. Adding a small negative score for a mood mismatch would push songs like Gym Hero (wrong mood) down the list without having to reduce the genre weight as a workaround.

---

## 9. Personal Reflection

**Biggest learning moment:**
The biggest learning moment was the Gym Hero problem. The system kept recommending Gym Hero (pop, intense) to a user who wanted happy music. At first that felt like a bug. But when I traced the math, it made complete sense: genre match earns points, missing mood earns zero, and there is no penalty for the wrong mood. Gym Hero earned enough genre and energy points to win. The system was not broken — my assumptions about how it should behave were just wrong. That moment changed how I think about all scoring systems: they do exactly what the math says, not what you intended.

**How AI tools helped, and when I had to double-check:**
AI tools helped me move fast. They suggested the proximity formula, helped generate the expanded song catalog, and drafted sections of this model card. But I had to double-check several things. The original genre weight (3.0) came from the AI suggestion that "genre mismatch is the most jarring failure." That sounded right, but testing showed it was too high for a small catalog. The AI did not know my catalog only had one rock song. I had to run the actual experiments to discover that the weight needed to come down to 1.0. The AI gave me a reasonable starting point, but the evaluation work was still mine to do.

**What surprised me about simple algorithms still feeling like recommendations:**
What surprised me most is that the output actually feels like a recommendation even though the algorithm is just arithmetic. When the Chill Lofi profile returned Focus Flow with a score of 9.48 and a clear explanation ("energy proximity 1.00, instrumentalness proximity 1.00"), it felt right — not because of anything clever, but because the numbers happened to align with musical intuition. The explanation feature made the biggest difference. Seeing exactly why a song was chosen made the result feel trustworthy instead of arbitrary. A black-box answer of "here is your recommendation" would not have felt that way. Transparency is doing a lot of work to make a simple formula feel intelligent.

**What I would try next:**
First, I would expand the catalog to at least 10 songs per genre so that genre filtering actually narrows down a real shortlist instead of producing one song and then noise. Second, I would add a warning when the user's genre is not in the catalog, instead of silently falling back. Third, I would replace the single energy target with a range (min and max) so users can say "somewhere between 0.6 and 0.9" instead of picking an exact number. Those three changes would make the system far more honest about what it knows and what it is guessing at.
