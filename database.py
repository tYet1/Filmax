from __future__ import annotations

"""
database.py — SQLite database layer for the Filmax Movie Recommendation System.

Tables:
    users     (user_id, name, favorite_genres)
    movies    (movie_id, title, genre, tmdb_rating, poster_path)
    ratings   (user_id, movie_id, rating)
    watchlist (user_id, movie_id)
"""

import sqlite3
import pandas as pd

DB_NAME = "movie_recommender.db"

def init_db():
    """Create all tables if they do not already exist."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Updated users table with favorite_genres
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL UNIQUE,
            favorite_genres TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movies (
            movie_id    INTEGER PRIMARY KEY,
            title       TEXT NOT NULL,
            genre       TEXT,
            tmdb_rating REAL,
            poster_path TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ratings (
            user_id  INTEGER,
            movie_id INTEGER,
            rating   REAL,
            PRIMARY KEY (user_id, movie_id),
            FOREIGN KEY (user_id)  REFERENCES users(user_id),
            FOREIGN KEY (movie_id) REFERENCES movies(movie_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS watchlist (
            user_id  INTEGER,
            movie_id INTEGER,
            PRIMARY KEY (user_id, movie_id),
            FOREIGN KEY (user_id)  REFERENCES users(user_id),
            FOREIGN KEY (movie_id) REFERENCES movies(movie_id)
        )
    """)

    conn.commit()
    conn.close()

def _conn():
    return sqlite3.connect(DB_NAME)

def add_user(name: str, favorite_genres: str = "") -> int:
    """Insert a new user. If the name already exists, return the existing id."""
    conn = _conn()
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO users (name, favorite_genres) VALUES (?, ?)", (name, favorite_genres))
        conn.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError:
        cur = conn.cursor()
        cur.execute("SELECT user_id FROM users WHERE name = ?", (name,))
        return cur.fetchone()[0]
    finally:
        conn.close()

def get_user_favorite_genres(user_id: int) -> str:
    """Return the user's favorite genres."""
    conn = _conn()
    cur = conn.cursor()
    cur.execute("SELECT favorite_genres FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else ""

def get_user_genre_average(user_id: int, genres_str: str) -> float | None:
    """
    Calculate the average rating the user has given to movies in the specified genres.
    genres_str is a comma-separated string from the movie metadata.
    """
    if not genres_str:
        return None
        
    genres = [g.strip().lower() for g in genres_str.split(",")]
    conn = _conn()
    
    # Simple logic: Find all movies the user has rated, then check if they match any of the input genres.
    query = """
        SELECT r.rating, m.genre
        FROM ratings r
        JOIN movies m ON r.movie_id = m.movie_id
        WHERE r.user_id = ?
    """
    df = pd.read_sql_query(query, conn, params=(user_id,))
    conn.close()
    
    if df.empty:
        return None
        
    # Filter rows where at least one genre matches
    matching_ratings = []
    for _, row in df.iterrows():
        m_genres = [g.strip().lower() for g in str(row['genre']).split(",")]
        if any(g in m_genres for g in genres):
            matching_ratings.append(row['rating'])
            
    if not matching_ratings:
        return None
        
    return sum(matching_ratings) / len(matching_ratings)

def get_all_users() -> pd.DataFrame:
    conn = _conn()
    df = pd.read_sql_query("SELECT * FROM users", conn)
    conn.close()
    return df

def add_movie(movie_id: int, title: str, genre: str, tmdb_rating: float, poster_path: str = None):
    conn = _conn()
    conn.execute(
        "INSERT OR REPLACE INTO movies (movie_id, title, genre, tmdb_rating, poster_path) VALUES (?, ?, ?, ?, ?)",
        (movie_id, title, genre, tmdb_rating, poster_path),
    )
    conn.commit()
    conn.close()

def get_movie_by_id(movie_id: int) -> dict | None:
    conn = _conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM movies WHERE movie_id = ?", (movie_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return {"movie_id": row[0], "title": row[1], "genre": row[2], "tmdb_rating": row[3], "poster_path": row[4]}
    return None

def get_all_movies() -> pd.DataFrame:
    conn = _conn()
    df = pd.read_sql_query("SELECT * FROM movies", conn)
    conn.close()
    return df

def add_rating(user_id: int, movie_id: int, rating: float):
    conn = _conn()
    conn.execute("INSERT OR REPLACE INTO ratings (user_id, movie_id, rating) VALUES (?, ?, ?)", (user_id, movie_id, rating))
    conn.commit()
    conn.close()

def get_user_ratings(user_id: int) -> pd.DataFrame:
    conn = _conn()
    df = pd.read_sql_query(
        "SELECT r.movie_id, r.rating, m.title, m.genre, m.poster_path FROM ratings r JOIN movies m ON r.movie_id = m.movie_id WHERE r.user_id = ?",
        conn, params=(user_id,))
    conn.close()
    return df

def get_all_ratings() -> pd.DataFrame:
    conn = _conn()
    df = pd.read_sql_query("SELECT * FROM ratings", conn)
    conn.close()
    return df

def add_to_watchlist(user_id: int, movie_id: int):
    conn = _conn()
    conn.execute("INSERT OR IGNORE INTO watchlist (user_id, movie_id) VALUES (?, ?)", (user_id, movie_id))
    conn.commit()
    conn.close()

def remove_from_watchlist(user_id: int, movie_id: int):
    conn = _conn()
    conn.execute("DELETE FROM watchlist WHERE user_id = ? AND movie_id = ?", (user_id, movie_id))
    conn.commit()
    conn.close()

def get_watchlist(user_id: int) -> pd.DataFrame:
    conn = _conn()
    df = pd.read_sql_query(
        "SELECT m.* FROM movies m JOIN watchlist w ON m.movie_id = w.movie_id WHERE w.user_id = ?",
        conn, params=(user_id,))
    conn.close()
    return df

def is_in_watchlist(user_id: int, movie_id: int) -> bool:
    conn = _conn()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM watchlist WHERE user_id = ? AND movie_id = ?", (user_id, movie_id))
    res = cur.fetchone() is not None
    conn.close()
    return res
