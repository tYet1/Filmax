from __future__ import annotations

"""
recommender.py — Recommendation engine for the Filmax Movie Recommendation System.
"""

import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from database import get_all_movies, get_all_ratings, get_user_favorite_genres
from static_data import get_preloaded_recommendations

def get_content_based_recommendations(user_id: int, n: int = 5) -> list[pd.Series]:
    all_movies = get_all_movies()
    all_ratings = get_all_ratings()

    if all_movies.empty or all_ratings.empty:
        return []

    user_rated_ids = set(all_ratings.loc[all_ratings["user_id"] == user_id, "movie_id"])
    
    # Calculate user's average rating or use a default threshold
    user_avg = all_ratings.loc[all_ratings["user_id"] == user_id, "rating"].mean()
    threshold = min(7.0, user_avg) if pd.notna(user_avg) else 7.0
    
    high_rated_ids = set(all_ratings.loc[(all_ratings["user_id"] == user_id) & (all_ratings["rating"] >= threshold), "movie_id"])

    if not high_rated_ids:
        high_rated_ids = user_rated_ids
        if not high_rated_ids:
            return []

    cv = CountVectorizer(stop_words="english")
    genre_matrix = cv.fit_transform(all_movies["genre"].fillna(""))
    sim_matrix = cosine_similarity(genre_matrix)

    indices = [idx for idx, mid in enumerate(all_movies["movie_id"]) if mid in high_rated_ids]
    if not indices: return []

    avg_sim_scores = sim_matrix[indices].mean(axis=0)
    ranked_indices = avg_sim_scores.argsort()[::-1]
    
    recommendations = []
    for idx in ranked_indices:
        movie = all_movies.iloc[idx]
        if movie["movie_id"] not in user_rated_ids:
            recommendations.append(movie)
        if len(recommendations) >= n:
            break
    return recommendations

def get_collaborative_recommendations(user_id: int, n: int = 5) -> list[pd.Series]:
    all_ratings = get_all_ratings()
    all_movies = get_all_movies()

    if all_ratings.empty or all_ratings["user_id"].nunique() < 2:
        return []

    pivot = all_ratings.pivot_table(index="user_id", columns="movie_id", values="rating").fillna(0)
    if user_id not in pivot.index: return []

    user_sim = cosine_similarity(pivot)
    user_sim_df = pd.DataFrame(user_sim, index=pivot.index, columns=pivot.index)
    similar_users = user_sim_df[user_id].drop(user_id, errors="ignore").sort_values(ascending=False).index

    if len(similar_users) == 0: return []

    user_vector = pivot.loc[user_id]
    unrated_movies = user_vector[user_vector == 0].index

    movie_scores = {}
    for mid in unrated_movies:
        scores, sims = [], []
        for other in similar_users:
            other_rating = pivot.loc[other, mid]
            if other_rating > 0:
                sim = user_sim_df.loc[user_id, other]
                scores.append(other_rating * sim)
                sims.append(sim)
        if sims and sum(sims) > 0:
            movie_scores[mid] = sum(scores) / sum(sims)

    top_movie_ids = sorted(movie_scores, key=movie_scores.get, reverse=True)[:n]
    recommendations = []
    for mid in top_movie_ids:
        match = all_movies[all_movies["movie_id"] == mid]
        if not match.empty:
            recommendations.append(match.iloc[0])
    return recommendations

def get_hybrid_recommendations(user_id: int, n: int = 10) -> list[pd.Series] | list[dict]:
    """
    Get recommendations. If user has no ratings, return preloaded favorites.
    """
    all_ratings = get_all_ratings()
    user_ratings = all_ratings[all_ratings["user_id"] == user_id]
    
    if user_ratings.empty:
        # Cold start: Use favorite genres
        fav_genres = get_user_favorite_genres(user_id)
        return get_preloaded_recommendations(fav_genres, limit=n)

    cb = []
    cf = []
    if not user_ratings.empty:
        cb = get_content_based_recommendations(user_id, n)
        cf = get_collaborative_recommendations(user_id, n)

    seen = set()
    merged = []
    for movie in cb + cf:
        mid = movie["movie_id"]
        if mid not in seen:
            seen.add(mid)
            merged.append(movie)

    if len(merged) < n:
        # Fallback to genre-based recommendations
        fav_genres = get_user_favorite_genres(user_id)
        rated_ids = set(user_ratings["movie_id"]) if not user_ratings.empty else set()
        preloaded = get_preloaded_recommendations(fav_genres, limit=n * 2)
        
        for movie in preloaded:
            mid = movie.get("id") or movie.get("movie_id")
            if mid not in seen and mid not in rated_ids:
                seen.add(mid)
                merged.append(movie)
                if len(merged) >= n:
                    break

    return merged[:n]
