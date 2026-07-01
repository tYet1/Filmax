from __future__ import annotations

"""
utils.py — Helper / utility functions for the Filmax Movie Recommendation System.
"""

import pandas as pd
from database import get_user_ratings, get_user_genre_average

def normalize_user_ratings(user_id: int) -> pd.DataFrame:
    ratings = get_user_ratings(user_id)
    if ratings.empty:
        return pd.DataFrame()
    user_avg = ratings["rating"].mean()
    user_std = ratings["rating"].std()
    ratings["user_avg"] = round(user_avg, 2)
    ratings["normalized_rating"] = round(ratings["rating"] - user_avg, 2)
    
    if pd.isna(user_std) or user_std == 0:
        ratings["z_score"] = 0.0
    else:
        ratings["z_score"] = round(ratings["normalized_rating"] / user_std, 2)
        
    ratings["genre_avg"] = ratings["genre"].apply(
        lambda g: round(get_user_genre_average(user_id, g), 2) if get_user_genre_average(user_id, g) is not None else None
    )
    
    return ratings

def calculate_user_specific_rating(omdb_ratings: dict | None, user_genre_avg: float | None) -> dict:
    """
    Calculate a personalized rating blending global scores and user genre history.
    Formula: 0.7 * Global Weighted + 0.3 * User Genre Avg.
    """
    weights = {"IMDb": 0.5, "Rotten Tomatoes": 0.3, "Metacritic": 0.2}
    weighted_sum = 0.0
    total_weight = 0.0
    
    breakdown = {
        "global_scores": {},
        "weighted_global": None,
        "user_genre_avg": user_genre_avg,
        "final_score": None
    }
    
    if omdb_ratings:
        for source, weight in weights.items():
            val = omdb_ratings.get(source)
            if val is not None:
                weighted_sum += val * weight
                total_weight += weight
                breakdown["global_scores"][source] = val
        
        if total_weight > 0:
            breakdown["weighted_global"] = round(weighted_sum / total_weight, 2)
            
    # Combine with user genre history
    if breakdown["weighted_global"] is not None:
        if user_genre_avg is not None:
            # 70% Global, 30% Personal
            final = (0.7 * breakdown["weighted_global"]) + (0.3 * user_genre_avg)
            breakdown["final_score"] = round(final, 2)
        else:
            # Fallback to global if no genre history
            breakdown["final_score"] = breakdown["weighted_global"]
    elif user_genre_avg is not None:
        # Fallback to personal if no global
        breakdown["final_score"] = round(user_genre_avg, 2)
        
    return breakdown

def format_movie_data(tmdb_movie: dict) -> dict:
    genres_raw = tmdb_movie.get("genres", [])
    genre_str = ", ".join(g.get("name", "") for g in genres_raw) if genres_raw else ""
    return {
        "movie_id": tmdb_movie.get("id"),
        "title": tmdb_movie.get("title"),
        "genre": genre_str,
        "tmdb_rating": tmdb_movie.get("vote_average"),
        "poster_path": tmdb_movie.get("poster_path"),
    }

def safe_float(value, default=None) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

def rating_color(rating: float) -> str:
    if rating >= 7.5: return "#4CAF50"
    elif rating >= 6.0: return "#FFC107"
    else: return "#F44336"
