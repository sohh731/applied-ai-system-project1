import streamlit as st
import sys
import os
import time

sys.path.insert(0, os.path.dirname(__file__))

from recommender import load_songs, recommend_songs
from agent import MusicAgent
from explainer import explain_with_style
from rag import load_kbs, rag_recommend

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(page_title="VibeFinder 2.0", layout="wide")
st.title("VibeFinder 2.0 — AI Music Recommender")
st.markdown(
    "Recommends songs based on your preferences. "
    "Use the sidebar to activate the agent, RAG, and explanation-style features."
)

# ---------------------------------------------------------------------------
# Load data (cached so it only runs once)
# ---------------------------------------------------------------------------
@st.cache_data
def get_songs():
    return load_songs("data/songs.csv")

@st.cache_data
def get_kbs():
    try:
        return load_kbs("data/genre_kb.json", "data/artist_kb.json")
    except FileNotFoundError:
        return load_kbs("../data/genre_kb.json", "../data/artist_kb.json")

songs = get_songs()
genre_kb, artist_kb = get_kbs()

# ---------------------------------------------------------------------------
# Session state defaults (used by reset button)
# ---------------------------------------------------------------------------
DEFAULTS = {
    "genre":             "any",
    "mood":              "any",
    "energy":            0.5,
    "acoustic":          False,
    "k":                 5,
    "use_agent":         False,
    "use_rag":           False,
    "explanation_style": "casual",
}

for key, val in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = val

def reset_preferences():
    for key, val in DEFAULTS.items():
        st.session_state[key] = val

# ---------------------------------------------------------------------------
# Sidebar — stretch feature toggles
# ---------------------------------------------------------------------------
st.sidebar.header("Feature Settings")

st.sidebar.toggle(
    "Agent Mode",
    key="use_agent",
    help=(
        "Activates the multi-step MusicAgent. "
        "The agent analyzes your intent, selects the best scoring mode, "
        "checks confidence, and falls back to discovery mode if needed."
    ),
)

st.sidebar.toggle(
    "Rich Explanations (RAG)",
    key="use_rag",
    help=(
        "Retrieves from two knowledge bases — genre_kb.json and artist_kb.json — "
        "and appends genre description, listening context, artist style, and influences."
    ),
)

st.sidebar.selectbox(
    "Explanation Style",
    options=["baseline", "technical", "casual", "dj"],
    key="explanation_style",
    help=(
        "baseline: raw scoring reasons | "
        "technical: numerical delta breakdown | "
        "casual: conversational friend style | "
        "dj: punchy club-ready language"
    ),
)

st.sidebar.markdown("---")
active = []
if st.session_state.use_agent:
    active.append("Agent Mode")
if st.session_state.use_rag:
    active.append("RAG (genre + artist KB)")
if st.session_state.explanation_style != "baseline":
    active.append(f"Style: {st.session_state.explanation_style}")
st.sidebar.markdown("**Active:** " + (", ".join(active) if active else "none (baseline mode)"))

# ---------------------------------------------------------------------------
# Main tabs
# ---------------------------------------------------------------------------
tab_rec, tab_eval = st.tabs(["Recommendations", "Evaluation & Reliability"])

# ===========================================================================
# TAB 1 — RECOMMENDATIONS
# ===========================================================================
with tab_rec:
    st.header("Your Preferences")

    col1, col2 = st.columns(2)
    with col1:
        st.selectbox(
            "Preferred Genre",
            ["any", "pop", "lofi", "rock", "jazz", "ambient", "synthwave",
             "indie pop", "hip-hop", "r&b", "classical", "country", "edm",
             "folk", "reggae", "blues"],
            key="genre",
        )
        st.selectbox(
            "Preferred Mood",
            ["any", "happy", "chill", "intense", "relaxed", "focused", "moody",
             "motivated", "romantic", "melancholic", "nostalgic", "euphoric",
             "dreamy", "sad"],
            key="mood",
        )

    with col2:
        st.slider("Energy Level  (0.0 = calm, 1.0 = intense)", 0.0, 1.0, step=0.01, key="energy")
        st.checkbox("Prefer acoustic sounds", key="acoustic")
        st.slider("Number of recommendations", 1, 10, key="k")

    btn_col1, btn_col2 = st.columns([2, 1])
    with btn_col1:
        run = st.button("Get Recommendations", type="primary", use_container_width=True)
    with btn_col2:
        st.button("Reset", on_click=reset_preferences, use_container_width=True)

    if run:
        user_prefs = {
            "genre":          st.session_state.genre if st.session_state.genre != "any" else "",
            "mood":           st.session_state.mood  if st.session_state.mood  != "any" else "",
            "target_energy":  st.session_state.energy,
            "likes_acoustic": st.session_state.acoustic,
        }

        agent_log  = []
        use_agent  = st.session_state.use_agent
        use_rag    = st.session_state.use_rag
        style      = st.session_state.explanation_style
        k          = st.session_state.k

        # ------------------------------------------------------------------
        # Pipeline selection
        # ------------------------------------------------------------------
        if use_agent and use_rag:
            agent = MusicAgent(songs)
            _, agent_log = agent.run(user_prefs, k=k, verbose=False)
            agent_mode = "balanced"
            for entry in agent_log:
                if "select_strategy" in entry and "Chosen mode:" in entry:
                    agent_mode = entry.split("Chosen mode:")[-1].strip().lower()
            results = rag_recommend(
                user_prefs, songs, genre_kb, artist_kb,
                k=k, mode=agent_mode, diversity=True,
            )
        elif use_agent:
            agent = MusicAgent(songs)
            results, agent_log = agent.run(user_prefs, k=k, verbose=False)
        elif use_rag:
            results = rag_recommend(
                user_prefs, songs, genre_kb, artist_kb, k=k, diversity=True
            )
        else:
            results = recommend_songs(user_prefs, songs, k=k, diversity=True)

        # Apply explanation style
        if style != "baseline":
            results = [
                (song, score, explain_with_style(song, exp, score, style=style))
                for song, score, exp in results
            ]

        # ------------------------------------------------------------------
        # Display results
        # ------------------------------------------------------------------
        tags = []
        if use_agent:
            mode_label = "balanced"
            for entry in agent_log:
                if "select_strategy" in entry and "Chosen mode:" in entry:
                    mode_label = entry.split("Chosen mode:")[-1].strip()
                    break
            tags.append(f"Agent mode: {mode_label}")
        if use_rag:
            tags.append("RAG: genre + artist KB")
        if style != "baseline":
            tags.append(f"Style: {style}")

        st.header(f"Top {len(results)} Recommendations")
        if tags:
            st.caption("  |  ".join(tags))

        for i, (song, score, explanation) in enumerate(results, 1):
            with st.container(border=True):
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.subheader(f"#{i}  {song['title']}")
                    st.write(
                        f"**{song['artist']}**  |  "
                        f"Genre: {song['genre']}  |  "
                        f"Mood: {song['mood']}  |  "
                        f"Energy: {song['energy']:.2f}"
                    )
                with col_b:
                    conf = round(score / 13.0, 2)
                    st.metric("Score", f"{score:.2f}", delta=f"conf {conf:.2f}")
                with st.expander("Why this recommendation?"):
                    current_style = st.session_state.explanation_style
                    if current_style == "technical":
                        # Technical: monospace code block suits the numerical format
                        st.code(explanation, language=None)
                    elif "\n" in explanation and "[" in explanation:
                        # RAG augmented: split into scoring part and retrieved context
                        parts = explanation.split("\n", 1)
                        scoring = parts[0]
                        context = parts[1] if len(parts) > 1 else ""
                        st.markdown("**Scoring reasons:**")
                        for reason in scoring.split(";"):
                            reason = reason.strip()
                            if reason:
                                st.markdown(f"- {reason}")
                        if context:
                            st.markdown("**Retrieved context:**")
                            st.code(context, language=None)
                    elif ";" in explanation and current_style == "baseline":
                        # Baseline: convert semicolons to bullet points
                        st.markdown("**Why this song matched:**")
                        for reason in explanation.split(";"):
                            reason = reason.strip()
                            if reason:
                                st.markdown(f"- {reason}")
                    else:
                        # Casual / DJ: plain readable text
                        st.write(explanation)

        # Agent decision log
        if use_agent and agent_log:
            st.subheader("Agent Decision Chain")
            with st.expander("Show full decision log", expanded=True):
                st.code("\n".join(agent_log), language=None)


# ===========================================================================
# TAB 2 — EVALUATION & RELIABILITY
# ===========================================================================
with tab_eval:
    st.header("Evaluation & Reliability")
    st.markdown(
        "Runs the full evaluation harness on **10 predefined test cases** and "
        "reports accuracy, confidence, consistency, and performance — the same "
        "output as running `python eval.py` in the terminal."
    )

    # Static summary metrics (always visible)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Pytest tests",   "8 / 8",  "100% pass")
    col2.metric("Eval accuracy",  "8 / 8",  "100%")
    col3.metric("Avg confidence", "0.41",   "threshold 0.45")
    col4.metric("Consistency",    "10 / 10","deterministic")

    st.divider()

    if st.button("Run Full Evaluation", type="primary"):

        MAX_SCORE = 13.0
        CONFIDENCE_THRESHOLD = 0.45

        TEST_CASES = [
            ("Pop / happy / 0.8",
             {"genre": "pop",   "mood": "happy",     "target_energy": 0.80}, "Sunrise City"),
            ("Lofi / focused / 0.4",
             {"genre": "lofi",  "mood": "focused",   "target_energy": 0.40}, "Focus Flow"),
            ("Rock / intense / 0.9",
             {"genre": "rock",  "mood": "intense",   "target_energy": 0.90}, "Storm Runner"),
            ("Jazz / relaxed / 0.35",
             {"genre": "jazz",  "mood": "relaxed",   "target_energy": 0.35}, "Coffee Shop Stories"),
            ("Ambient / chill / 0.3",
             {"genre": "ambient","mood": "chill",    "target_energy": 0.30}, "Spacewalk Thoughts"),
            ("EDM / euphoric / 0.95",
             {"genre": "edm",   "mood": "euphoric",  "target_energy": 0.95}, "Drop Zone"),
            ("Hip-hop / motivated / 0.78",
             {"genre": "hip-hop","mood": "motivated","target_energy": 0.78}, "Block by Block"),
            ("Classical / melancholic / 0.2",
             {"genre": "classical","mood": "melancholic","target_energy": 0.20}, "Autumn Sonata"),
            ("EDGE: Ghost genre (metal)",
             {"genre": "metal", "mood": "intense",   "target_energy": 0.95}, None),
            ("EDGE: Empty preferences",
             {}, None),
        ]

        rows = []
        correct = 0
        accuracy_tested = 0
        all_consistent = True

        progress = st.progress(0, text="Running evaluation...")

        for idx, (label, prefs, expected) in enumerate(TEST_CASES):
            t0 = time.time()
            recs = recommend_songs(prefs, songs, k=3)
            elapsed_ms = round((time.time() - t0) * 1000, 1)

            top_song  = recs[0][0]["title"] if recs else "—"
            top_score = recs[0][1]          if recs else 0.0
            conf      = round(top_score / MAX_SCORE, 2)

            if expected is not None:
                accuracy_tested += 1
                passed = (top_song == expected)
                if passed:
                    correct += 1
                status = "PASS" if passed else "FAIL"
            else:
                status = "PASS" if recs else "FAIL"

            # Consistency: run 3 times
            r2 = recommend_songs(prefs, songs, k=3)
            r3 = recommend_songs(prefs, songs, k=3)
            t1 = [x[0]["title"] for x in recs]
            t2 = [x[0]["title"] for x in r2]
            t3 = [x[0]["title"] for x in r3]
            consistent = (t1 == t2 == t3)
            if not consistent:
                all_consistent = False

            conf_flag = "OK" if conf >= CONFIDENCE_THRESHOLD else "LOW"

            rows.append({
                "Test Case":   label,
                "Top Result":  top_song,
                "Expected":    expected or "—",
                "Pass / Fail": status,
                "Confidence":  f"{conf:.2f} [{conf_flag}]",
                "Consistent":  "YES" if consistent else "NO",
                "Time (ms)":   elapsed_ms,
            })

            progress.progress((idx + 1) / len(TEST_CASES),
                              text=f"Running: {label}")

        progress.empty()

        # ------------------------------------------------------------------
        # Results table
        # ------------------------------------------------------------------
        import pandas as pd
        df = pd.DataFrame(rows)

        def highlight_row(row):
            if row["Pass / Fail"] == "FAIL":
                return ["background-color: #ffcccc"] * len(row)
            elif "LOW" in str(row["Confidence"]):
                return ["background-color: #fff3cd"] * len(row)
            else:
                return ["background-color: #d4edda"] * len(row)

        st.dataframe(
            df.style.apply(highlight_row, axis=1),
            use_container_width=True,
            hide_index=True,
        )

        # ------------------------------------------------------------------
        # Summary
        # ------------------------------------------------------------------
        passed_count = sum(1 for r in rows if r["Pass / Fail"] == "PASS")
        avg_conf     = round(sum(
            float(r["Confidence"].split()[0]) for r in rows
        ) / len(rows), 2)
        accuracy_pct = round((correct / accuracy_tested) * 100) if accuracy_tested else 0

        st.divider()
        scol1, scol2, scol3, scol4 = st.columns(4)
        scol1.metric("Overall",     f"{passed_count}/{len(TEST_CASES)}", "passed")
        scol2.metric("Accuracy",    f"{correct}/{accuracy_tested}", f"{accuracy_pct}%")
        scol3.metric("Avg Confidence", f"{avg_conf:.2f}", f"threshold {CONFIDENCE_THRESHOLD}")
        scol4.metric("Consistency", "ALL consistent" if all_consistent else "INCONSISTENT")

        if accuracy_pct == 100 and all_consistent:
            st.success(
                f"All {passed_count} tests passed. "
                f"{correct}/{accuracy_tested} ground-truth cases correct (100%). "
                "System is fully deterministic across all inputs."
            )

        st.caption(
            "Green = PASS with OK confidence  |  "
            "Yellow = PASS but LOW confidence (system had weak signal)  |  "
            "Red = FAIL"
        )

    # Quick consistency check (always available without running full eval)
    st.divider()
    st.subheader("Quick Consistency Check")
    if st.button("Run Consistency Check"):
        prefs_test = {"genre": "pop", "mood": "happy", "target_energy": 0.8}
        r1 = recommend_songs(prefs_test, songs, k=3)
        r2 = recommend_songs(prefs_test, songs, k=3)
        consistent = all(a[0]["title"] == b[0]["title"] for a, b in zip(r1, r2))
        if consistent:
            st.success(
                f"Consistent — same input produces same output across 2 runs. "
                f"Top result: '{r1[0][0]['title']}' both times."
            )
        else:
            st.error("Inconsistency detected.")
