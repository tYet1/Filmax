"""
main.py — Streamlit entry point for the Filmax Movie Recommendation System.
Consolidated Home, Search, and Rating functionality.
"""

import streamlit as st
import pandas as pd
from api import (
    get_trending_movies, search_movie_tmdb, get_movie_details_tmdb,
    get_omdb_ratings, get_aggregated_rating, TMDB_POSTER_BASE_URL,
)
from database import (
    init_db, add_user, get_all_users, add_movie, add_rating,
    add_to_watchlist, remove_from_watchlist, get_watchlist,
    get_user_ratings, get_movie_by_id, is_in_watchlist, get_user_genre_average,
)
from recommender import get_hybrid_recommendations
from utils import normalize_user_ratings, rating_color, calculate_user_specific_rating
from static_data import GENRE_OPTIONS

# Initialise DB
init_db()

# Page config
st.set_page_config(page_title="Filmax · Personalized Movies", layout="wide", page_icon="🎬")

# Custom CSS for UI polish and fixing overlaps
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');

/* Apply font safely without breaking Material Icons */
html, body { 
    font-family: 'Outfit', sans-serif; 
}

/* Apply custom font specifically to our custom UI elements */
.hero, .movie-card, .section-hdr, .stat-card {
    font-family: 'Outfit', sans-serif;
}

.main { background-color: #0d0d12; color: #ffffff; }

.hero {
    background: linear-gradient(135deg, #1e1e2f 0%, #12121a 100%);
    border-radius: 20px; padding: 3rem 2rem; margin-bottom: 2rem;
    text-align: center; border: 1px solid rgba(255,255,255,0.05);
}

.hero h1 { font-size: 3.5rem; font-weight: 800; color: #7c4dff; margin-bottom: 0.5rem; }
.hero p { font-size: 1.2rem; color: #a0a0b0; }

.movie-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px; padding: 0; margin-bottom: 25px;
    transition: all 0.3s ease; overflow: hidden;
    display: flex; flex-direction: column;
}
.movie-card:hover { transform: translateY(-5px); border-color: #7c4dff; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }

.card-img-container { position: relative; width: 100%; aspect-ratio: 2/3; overflow: hidden; }
.card-img { width: 100%; height: 100%; object-fit: cover; }

.card-content { padding: 15px; flex-grow: 1; }
.card-title { font-weight: 600; font-size: 1.1rem; margin-bottom: 8px; height: 1.4em; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.card-meta { font-size: 0.85rem; color: #a0a0b0; display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }

.rating-pill {
    background: #7c4dff; color: white; padding: 2px 8px; border-radius: 6px; font-weight: 600; font-size: 0.8rem;
}

.card-actions { padding: 0 15px 15px 15px; }

.search-container { margin-bottom: 3rem; }

/* Fix overlapping buttons */
.stButton button { width: 100%; border-radius: 8px; height: 38px; line-height: 1; }

/* Custom metric styling */
[data-testid="stMetricValue"] { font-size: 1.8rem !important; color: #7c4dff !important; }

/* Fix sidebar color */
section[data-testid="stSidebar"] { background-color: #12121a; }
</style>
""", unsafe_allow_html=True)

# Session state
if "user_id" not in st.session_state: st.session_state.user_id = None
if "user_name" not in st.session_state: st.session_state.user_name = None

# Sidebar — User Profile
with st.sidebar:
    st.markdown("## 👤 User Profile")
    users = get_all_users()
    user_names = users["name"].tolist() if not users.empty else []
    
    choice = st.selectbox("Select User", ["— New User —"] + user_names)
    
    if choice == "— New User —":
        with st.form("create_user"):
            new_name = st.text_input("Name")
            fav_genres = st.multiselect("Favorite Genres", GENRE_OPTIONS)
            if st.form_submit_button("Join Filmax"):
                if new_name.strip():
                    genre_str = ", ".join(fav_genres)
                    uid = add_user(new_name.strip(), genre_str)
                    st.session_state.user_id = uid
                    st.session_state.user_name = new_name.strip()
                    st.rerun()
                else:
                    st.error("Name is required.")
    else:
        u_data = users[users["name"] == choice].iloc[0]
        st.session_state.user_id = int(u_data["user_id"])
        st.session_state.user_name = choice
        
    if st.session_state.user_id:
        st.success(f"Welcome back, **{st.session_state.user_name}**")
        ur = get_user_ratings(st.session_state.user_id)
        wl = get_watchlist(st.session_state.user_id)
        c1, c2 = st.columns(2)
        c1.metric("Rated", len(ur))
        c2.metric("Watchlist", len(wl))
        
    st.markdown("---")
    st.caption("Filmax v2.0 · Powered by TMDb & OMDb")

# Helpers
def _poster(path): 
    import pandas as pd
    if not path or pd.isna(path) or path == "None":
        return "https://via.placeholder.com/300x450?text=No+Poster"
    return f"{TMDB_POSTER_BASE_URL}{path}"

def render_movie_card(movie, key_prefix):
    mid = movie.get("id") or movie.get("movie_id")
    title = movie.get("title") or movie.get("name") or "Unknown Title"
    poster = _poster(movie.get("poster_path"))
    rating = movie.get("vote_average") or movie.get("tmdb_rating") or 0.0
    year = movie.get("release_date", "")[:4] if movie.get("release_date") else ""
    
    st.markdown(f"""
    <div class="movie-card">
        <div class="card-img-container"><img src="{poster}" class="card-img"/></div>
        <div class="card-content">
            <div class="card-title">{title}</div>
            <div class="card-meta">
                <span>📅 {year}</span>
                <span class="rating-pill">⭐ {rating:.1f}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.user_id:
        # Actions
        st.markdown('<div class="card-actions">', unsafe_allow_html=True)
        cols = st.columns(2)
        with cols[0]:
            is_in = is_in_watchlist(st.session_state.user_id, mid)
            if st.button("Saved" if is_in else "＋ List", key=f"{key_prefix}_wl_btn_{mid}", disabled=is_in):
                details = get_movie_details_tmdb(mid)
                genres = ", ".join(g["name"] for g in details.get("genres", [])) if details else movie.get("genre", "")
                add_movie(mid, title, genres, rating, movie.get("poster_path"))
                add_to_watchlist(st.session_state.user_id, mid)
                st.rerun()
        
        with cols[1]:
            if st.button("📊 Score", key=f"{key_prefix}_score_btn_{mid}"):
                st.session_state[f"calc_{mid}"] = True
        st.markdown('</div>', unsafe_allow_html=True)

        # Personalized Rating Section
        if st.session_state.get(f"calc_{mid}"):
            with st.expander("📈 Personalized Rating Breakdown", expanded=True):
                # Ensure movie is in DB for genre lookup
                details = get_movie_details_tmdb(mid)
                genres = ", ".join(g["name"] for g in details.get("genres", [])) if details else movie.get("genre", "")
                add_movie(mid, title, genres, rating, movie.get("poster_path"))
                
                omdb = get_omdb_ratings(title)
                genre_avg = get_user_genre_average(st.session_state.user_id, genres)
                calc = calculate_user_specific_rating(omdb, genre_avg)
                
                c1, c2 = st.columns(2)
                with c1:
                    st.write("**Global Sources**")
                    if calc["global_scores"]:
                        for s, v in calc["global_scores"].items(): st.write(f"- {s}: {v}/10")
                    else: st.caption("No global data found.")
                with c2:
                    st.write("**Your History**")
                    if genre_avg: st.write(f"- Avg in this genre: {genre_avg:.1f}/10")
                    else: st.caption("No genre history yet.")
                
                st.markdown(f"### Filmax Score: **{calc['final_score'] or 'N/A'}/10**")
                
                # FIXED: Added key_prefix to slider and button
                user_val = st.slider("Your Rating", 0.0, 10.0, 5.0, 0.5, key=f"{key_prefix}_rate_val_{mid}")
                if st.button("Submit Rating", key=f"{key_prefix}_submit_rating_{mid}"):
                    add_rating(st.session_state.user_id, mid, user_val)
                    st.success("Rating saved!")
                    st.session_state[f"calc_{mid}"] = False
                    st.rerun()

# Main Tabs
tabs = st.tabs(["🏠 Home", "🧠 Recommendations", "📖 Watchlist"])

# Tab 1: Home & Search
with tabs[0]:
    st.markdown('<div class="hero"><h1>Filmax</h1><p>Search, Discover, and Rate with Precision</p></div>', unsafe_allow_html=True)
    
    # Search Bar
    query = st.text_input("🔍 Search for movies...", placeholder="e.g., Inception, The Dark Knight", key="main_search")
    
    if query:
        st.markdown(f"### Results for '{query}'")
        results = search_movie_tmdb(query)
        if results:
            # 4-column grid for results
            for i in range(0, len(results[:12]), 4):
                cols = st.columns(4)
                for j, movie in enumerate(results[i:i+4]):
                    with cols[j]: render_movie_card(movie, "search")
        else:
            st.info("No movies found.")
    else:
        # Show Trending if no search
        st.markdown("### 🔥 Trending Today")
        trending = get_trending_movies()
        if trending:
            for i in range(0, 12, 4):
                cols = st.columns(4)
                for j, movie in enumerate(trending[i:i+4]):
                    with cols[j]: render_movie_card(movie, "trend")

# Tab 2: Recommendations
with tabs[1]:
    st.markdown('<p class="section-hdr" style="font-size: 1.5rem; font-weight: 600; margin-bottom: 1rem;">🧠 Personalized Recommendations</p>', unsafe_allow_html=True)
    if not st.session_state.user_id:
        st.warning("Please login to see recommendations.")
    else:
        # 1. Show Normalized Ratings Table
        norm = normalize_user_ratings(st.session_state.user_id)
        if not norm.empty:
            s1, s2, s3 = st.columns(3)
            s1.metric("Movies Rated", len(norm))
            s2.metric("Avg Rating", f"{norm['rating'].mean():.1f}")
            s3.metric("Highest Rating", f"{norm['rating'].max():.1f}")
            
            with st.expander("📊 Ratings Analysis Table", expanded=False):
                show = norm[["title", "rating", "genre_avg", "z_score"]].rename(columns={
                    "title": "Movie", "rating": "Rating (/10)", "genre_avg": "Genre Avg", "z_score": "Z-Score"
                })
                st.dataframe(show, use_container_width=True, hide_index=True)
            st.markdown("---")
            
        # 2. Show Recommendations
        n_recs = st.slider("Number of recommendations", 4, 20, 12, key="n_recs")
        recs = get_hybrid_recommendations(st.session_state.user_id, n=n_recs)
        
        if recs:
            st.markdown(f"### 🎯 Top {len(recs)} for You")
            for i in range(0, len(recs), 4):
                cols = st.columns(4)
                for j, movie in enumerate(recs[i:i+4]):
                    m_dict = movie.to_dict() if hasattr(movie, "to_dict") else movie
                    with cols[j]: render_movie_card(m_dict, "rec")
        else:
            if norm.empty:
                st.info("No recommendations available. Please select favorite genres or rate some movies.")
            else:
                st.info("Not enough data for recommendations yet — rate more movies!")

# Tab 3: Watchlist
with tabs[2]:
    if not st.session_state.user_id:
        st.warning("Please login to see your watchlist.")
    else:
        wl = get_watchlist(st.session_state.user_id)
        if not wl.empty:
            for i in range(0, len(wl), 4):
                cols = st.columns(4)
                for j, movie in enumerate(wl.iloc[i:i+4].to_dict('records')):
                    with cols[j]:
                        render_movie_card(movie, "wl_tab")
                        if st.button("🗑️ Remove", key=f"del_wl_{movie['movie_id']}"):
                            remove_from_watchlist(st.session_state.user_id, movie["movie_id"])
                            st.rerun()
        else:
            st.info("Your watchlist is empty.")
