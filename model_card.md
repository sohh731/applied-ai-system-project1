# Model Card: Music Recommender Simulation

## 1. Model Name

**VibeFinder 1.0**

---

## 2. Goal / Task

VibeFinder 1.0 suggests songs from a small catalog based on what a user tells it they want to hear.

The user gives it a genre, a mood, and a target energy level. The system finds the songs that match those preferences most closely and returns the top results ranked from best to worst.

It is not trying to learn from behavior or listening history. It only works with what the user explicitly tells it.

---

## 3. Data Used

The catalog has 18 songs.

Each song has 10 features: genre, mood, energy, tempo, valence, danceability, acousticness, speechiness, and instrumentalness.

Genres in the catalog: pop, lofi, rock, ambient, jazz, synthwave, indie pop, hip-hop, R&B, classical, country, EDM, folk, reggae, and blues.

Moods in the catalog: happy, chill, intense, relaxed, focused, moody, motivated, romantic, melancholic, nostalgic, euphoric, dreamy, and sad.

The catalog only has one or two songs per genre. That is a big limitation. With so few songs, the recommendations can feel repetitive.

The songs are made up for this simulation. They do not reflect real listening data. Genres like K-pop, Latin, Afrobeats, and classical Indian music are not represented at all.

---

## 4. Algorithm Summary

Every song gets a score by comparing it to what the user wants. Higher score = better match.

The score has two types of checks:

**Categorical checks (yes or no):**
- If the song's genre matches the user's preferred genre, it earns full genre points.
- If the song's mood matches the user's preferred mood, it earns full mood points.
- If the song does not match, it earns zero — there is no penalty, just no reward.

**Proximity checks (how close is close enough):**
- For features like energy, acousticness, and instrumentalness, the system measures the gap between the song's value and the user's target.
- The closer the match, the more points the song earns. A perfect match earns the full weight. A gap of 1.0 earns zero.
- Formula: `points = weight × (1.0 - |target - actual|)`

**Weights (how much each feature is worth):**

| Feature | Max Points |
|---|---|
| Genre match | 1.0 |
| Mood match | 2.0 |
| Energy proximity | 3.0 |
| Acousticness proximity | 1.0 |
| Instrumentalness proximity | 1.0 |
| Valence proximity | 0.5 |
| Speechiness proximity | 0.5 |

**Maximum possible score: 9.0 points.**

After every song is scored, they are sorted from highest to lowest. The top results are returned with an explanation of which features contributed points.

---

## 5. Observed Behavior / Biases

**Filter bubble from small catalog.**
With only one rock song in the catalog, a rock fan gets Storm Runner as #1 and then falls off a cliff. Songs from completely unrelated genres fill spots #2 through #5. The system looks confident but positions #3–#5 are basically random noise.

**No penalty for a bad mood match.**
The system rewards a genre match but never punishes a mood mismatch. A pop song with the wrong mood (intense instead of happy) still earns its genre points and energy points. This caused Gym Hero (pop, intense) to outrank Rooftop Lights (indie pop, happy) for a user who wanted happy music — until the genre weight was reduced.

**Ghost genre — silent failure.**
If the user asks for a genre that does not exist in the catalog (like "metal"), every song scores zero genre points. The system quietly falls back to mood and energy and returns confident-looking results. It never tells the user their genre preference was completely ignored.

**Calm preferences are penalized more.**
A user who wants energy 0.10 loses a lot more points on high-energy songs than a user who wants energy 0.50. The proximity formula treats the gap as linear, but for very extreme preferences, the system consistently struggles to find a good match.

**No variety enforcement.**
The ranking rule just picks the top-k highest-scoring songs. For the Chill Lofi profile, all three top results are lofi songs by the same artist (LoRoom). A real recommender would try to avoid repeating the same artist.

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

---

## 7. Intended Use and Non-Intended Use

**Intended use:**
This system is for classroom exploration of how content-based recommender systems work. It is designed to show students how weighted scoring, feature matching, and catalog limitations affect the results a system returns.

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

**2. Add a diversity enforcement step.**
The ranking rule should limit how many times the same artist can appear in the top 5. Right now, all three lofi recommendations are by LoRoom. A simple "no more than one song per artist" rule would fix this.

**3. Warn the user when their genre has no matches.**
Before scoring, check whether the user's genre exists in the catalog. If it does not, tell the user instead of silently falling back. Something like "No songs found for genre: metal — showing closest matches by mood and energy instead" would be far more honest than returning confident-looking wrong results.

**4. Replace single energy target with a range.**
Let users say "energy between 0.6 and 0.9" instead of a single point. This would reduce the penalty for extreme preferences and let users express "somewhere in this zone" rather than a precise number.

---

## 9. Personal Reflection

Building this recommender made clear how much hidden work the genre label is doing. Before running the weight experiments, it felt natural to give genre a heavy weight — after all, a jazz fan does not want rock recommendations. But with only 18 songs, that heavy weight creates a situation where one or two songs dominate every profile and the rest of the results are filler.

The most interesting moment was watching the High-Energy Pop results change when genre weight dropped from 3.0 to 1.0. Rooftop Lights jumped to #2 purely because its mood ("happy") matched the user better than Gym Hero's ("intense"). That result felt more human and more correct. This changed how I think about real apps like Spotify: their recommendations likely feel good not because the algorithm is smarter, but because their catalog is large enough that genre filtering has thousands of songs to choose from — making the heavy genre weight invisible.
