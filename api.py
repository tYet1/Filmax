from __future__ import annotations

"""
api.py — External API integration for the Movie Recommendation System.

Data sources (NO web scraping):
    • TMDb API  → movie metadata (title, genre, poster, popularity)
    • OMDb API  → ratings from IMDb (/10), Rotten Tomatoes (%), Metacritic (/100)

All ratings are converted to a /10 scale.

Weighted aggregated rating formula:
    final_rating = 0.5 * imdb + 0.3 * rotten + 0.2 * metacritic
Missing values are handled by re-normalizing the available weights.
"""

import os
import time
from pathlib import Path
from typing import Optional

import requests
import streamlit as st
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ---------------------------------------------------------------------------
# Load environment variables from the project-level .env file
# ---------------------------------------------------------------------------
_ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=_ENV_PATH, override=False)


def _get_secret(name: str) -> Optional[str]:
    """Try Streamlit Cloud secrets first, then fall back to env vars."""
    try:
        return st.secrets.get(name)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# API keys & base URLs
# ---------------------------------------------------------------------------
TMDB_API_KEY = _get_secret("TMDB_API_KEY") or os.getenv("TMDB_API_KEY")
OMDB_API_KEY = _get_secret("OMDB_API_KEY") or os.getenv("OMDB_API_KEY")

TMDB_BASE_URL = "https://api.themoviedb.org/3"
OMDB_BASE_URL = "http://www.omdbapi.com/"
TMDB_POSTER_BASE_URL = "https://image.tmdb.org/t/p/w500"

# ---------------------------------------------------------------------------
# Resilient HTTP session with automatic retries
# ---------------------------------------------------------------------------

def _http_session() -> requests.Session:
    """Create a requests.Session with retry logic for transient errors."""
    session = requests.Session()
    retry = Retry(
        total=3,
        connect=3,
        read=3,
        backoff_factor=0.6,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update({
        "Accept": "application/json",
        "User-Agent": "movie-recommender/1.0",
    })
    return session


# ---------------------------------------------------------------------------
# TMDb endpoints
# ---------------------------------------------------------------------------

def get_trending_movies() -> list[dict]:
    """Fetch today's trending movies from TMDb (cached 1 hour in session)."""
    cache_key = "_tmdb_trending_v2"
    cached = st.session_state.get(cache_key)
    now = time.time()

    # Return cached data if fresh (< 1 hour)
    if cached and (now - cached.get("ts", 0)) < 3600 and cached.get("data"):
        return cached["data"]

    if not TMDB_API_KEY:
        return []

    try:
        resp = _http_session().get(
            f"{TMDB_BASE_URL}/trending/movie/day",
            params={"api_key": TMDB_API_KEY},
            timeout=(5, 20),
        )
        if resp.status_code == 200:
            data = resp.json().get("results", [])
            if data:
                st.session_state[cache_key] = {"ts": now, "data": data}
            return data
    except requests.exceptions.RequestException:
        # Return stale cache on network failure
        if cached and cached.get("data"):
            return cached["data"]
    return []


@st.cache_data(ttl=600)
def search_movie_tmdb(query: str) -> list[dict]:
    """Search TMDb for movies matching *query*."""
    if not TMDB_API_KEY or not query.strip():
        return []
    try:
        resp = _http_session().get(
            f"{TMDB_BASE_URL}/search/movie",
            params={"api_key": TMDB_API_KEY, "query": query},
            timeout=10,
        )
        if resp.status_code == 200:
            return resp.json().get("results", [])
    except requests.exceptions.RequestException:
        pass
    return []


@st.cache_data(ttl=86_400)
def get_movie_details_tmdb(movie_id: int) -> dict | None:
    """Fetch full movie details (including genres list) from TMDb."""
    if not TMDB_API_KEY:
        return None
    try:
        resp = _http_session().get(
            f"{TMDB_BASE_URL}/movie/{movie_id}",
            params={"api_key": TMDB_API_KEY},
            timeout=10,
        )
        if resp.status_code == 200:
            return resp.json()
    except requests.exceptions.RequestException:
        pass
    return None


# ---------------------------------------------------------------------------
# OMDb endpoints — ratings from IMDb, Rotten Tomatoes, Metacritic
# ---------------------------------------------------------------------------

@st.cache_data(ttl=86_400)
def get_omdb_ratings(title: str) -> dict | None:
    """
    Fetch ratings from OMDb and convert them all to a /10 scale.

    Returns dict with keys 'IMDb', 'Rotten Tomatoes', 'Metacritic'.
    Each value is a float on a 0–10 scale, or None if unavailable.
    """
    if not OMDB_API_KEY or not title.strip():
        return None
    try:
        resp = _http_session().get(
            OMDB_BASE_URL,
            params={"apikey": OMDB_API_KEY, "t": title},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("Response") == "True":
                return _parse_omdb_ratings(data.get("Ratings", []))
    except requests.exceptions.RequestException:
        pass
    return None


def _parse_omdb_ratings(ratings_list: list[dict]) -> dict:
    """
    Convert raw OMDb rating objects to a uniform /10 scale.

    Conversions:
        IMDb            → already X/10
        Rotten Tomatoes → X% → X/10
        Metacritic      → X/100 → X/10
    """
    result = {"IMDb": None, "Rotten Tomatoes": None, "Metacritic": None}

    for rating in ratings_list:
        source = rating.get("Source", "")
        value = rating.get("Value", "")

        try:
            if source == "Internet Movie Database":
                result["IMDb"] = float(value.split("/")[0])
            elif source == "Rotten Tomatoes":
                result["Rotten Tomatoes"] = float(value.replace("%", "")) / 10.0
            elif source == "Metacritic":
                result["Metacritic"] = float(value.split("/")[0]) / 10.0
        except (ValueError, IndexError):
            continue

    return result


# ---------------------------------------------------------------------------
# Aggregated weighted rating
# ---------------------------------------------------------------------------

def get_aggregated_rating(omdb_ratings: dict | None) -> float | None:
    """
    Compute a weighted average from available ratings.

    Formula:  final = 0.5 * IMDb + 0.3 * RT + 0.2 * Metacritic
    Missing values are handled by re-normalizing the remaining weights.

    Returns a float rounded to 1 decimal, or None if no ratings available.
    """
    if not omdb_ratings:
        return None

    weights = {"IMDb": 0.5, "Rotten Tomatoes": 0.3, "Metacritic": 0.2}
    weighted_sum = 0.0
    total_weight = 0.0

    for source, weight in weights.items():
        val = omdb_ratings.get(source)
        if val is not None:
            weighted_sum += val * weight
            total_weight += weight

    if total_weight == 0:
        return None

    # Re-normalize so the weights of available sources sum to 1
    return round(weighted_sum / total_weight, 1)
