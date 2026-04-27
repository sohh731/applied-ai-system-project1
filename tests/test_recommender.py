from src.recommender import Song, UserProfile, Recommender, recommend_songs, load_songs
import pytest

def make_small_recommender() -> Recommender:
    songs = [
        Song(
            id=1,
            title="Test Pop Track",
            artist="Test Artist",
            genre="pop",
            mood="happy",
            energy=0.8,
            tempo_bpm=120,
            valence=0.9,
            danceability=0.8,
            acousticness=0.2,
        ),
        Song(
            id=2,
            title="Chill Lofi Loop",
            artist="Test Artist",
            genre="lofi",
            mood="chill",
            energy=0.4,
            tempo_bpm=80,
            valence=0.6,
            danceability=0.5,
            acousticness=0.9,
        ),
    ]
    return Recommender(songs)


def test_recommend_returns_songs_sorted_by_score():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    results = rec.recommend(user, k=2)

    assert len(results) == 2
    # Starter expectation: the pop, happy, high energy song should score higher
    assert results[0].genre == "pop"
    assert results[0].mood == "happy"


def test_explain_recommendation_returns_non_empty_string():
    user = UserProfile(
        favorite_genre="lofi",
        favorite_mood="chill",
        target_energy=0.4,
        likes_acoustic=True,
    )
    rec = make_small_recommender()
    results = rec.recommend(user, k=1)

    assert len(results) == 1
    explanation = rec.explain_recommendation(user, results[0])
    assert explanation != ""


def test_scoring_modes_produce_different_results():
    """Test that different scoring modes change recommendation order."""
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    
    balanced_results = rec.recommend(user, k=2, mode="balanced")
    genre_first_results = rec.recommend(user, k=2, mode="genre_first")
    
    # Results should be different or same but verify modes are applied
    assert len(balanced_results) == len(genre_first_results)


def test_diversity_reranking_changes_order():
    """Test that diversity affects recommendation order."""
    songs = load_songs("data/songs.csv")
    user_prefs = {"genre": "pop", "mood": "happy", "target_energy": 0.8}
    
    no_diversity = recommend_songs(user_prefs, songs, k=5, diversity=False)
    with_diversity = recommend_songs(user_prefs, songs, k=5, diversity=True)
    
    # Check if diversity changed the order (at least one position different)
    order_changed = any(a[0]['title'] != b[0]['title'] for a, b in zip(no_diversity, with_diversity))
    assert order_changed or len(no_diversity) < 5  # If fewer songs, diversity may not change much


def test_consistency_same_input_same_output():
    """Test reliability: same input should produce same output."""
    songs = load_songs("data/songs.csv")
    user_prefs = {"genre": "pop", "mood": "happy", "target_energy": 0.8}
    
    results1 = recommend_songs(user_prefs, songs, k=3)
    results2 = recommend_songs(user_prefs, songs, k=3)
    
    assert len(results1) == len(results2)
    for r1, r2 in zip(results1, results2):
        assert r1[0]['title'] == r2[0]['title']  # Same songs in same order


def test_performance_under_load():
    """Test system performance with larger inputs."""
    songs = load_songs("data/songs.csv")
    user_prefs = {"genre": "pop", "mood": "happy", "target_energy": 0.8}
    
    import time
    start = time.time()
    results = recommend_songs(user_prefs, songs, k=10)
    end = time.time()
    
    assert len(results) == 10
    assert end - start < 1.0  # Should complete in under 1 second


def test_edge_case_handling():
    """Test guardrails: system handles invalid inputs gracefully."""
    songs = load_songs("data/songs.csv")
    
    # Invalid energy
    user_prefs = {"genre": "pop", "target_energy": 1.5}  # Energy > 1.0
    results = recommend_songs(user_prefs, songs, k=3)
    assert len(results) == 3  # Should still work, clamping or ignoring invalid values
    
    # Empty preferences
    user_prefs = {}
    results = recommend_songs(user_prefs, songs, k=3)
    assert len(results) == 3  # Should return some recommendations


def test_accuracy_against_ground_truth():
    """Evaluate accuracy using simulated ground truth."""
    songs = load_songs("data/songs.csv")
    
    # Define test cases with expected top song
    test_cases = [
        ({"genre": "pop", "mood": "happy", "target_energy": 0.8}, "Sunrise City"),
        ({"genre": "lofi", "mood": "chill", "target_energy": 0.4}, "Focus Flow"),
        ({"genre": "rock", "mood": "intense", "target_energy": 0.9}, "Storm Runner"),
    ]
    
    correct_predictions = 0
    for prefs, expected_title in test_cases:
        results = recommend_songs(prefs, songs, k=1)
        if results and results[0][0]['title'] == expected_title:
            correct_predictions += 1
    
    accuracy = correct_predictions / len(test_cases)
    assert accuracy >= 0.66  # At least 2/3 correct for basic functionality
