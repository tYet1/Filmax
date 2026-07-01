# Static data for cold-start recommendations
# Top movies curated for new users based on genre preferences

STATIC_MOVIES = [
    # Action
    {"id": 27205, "title": "Inception", "genre": "Action, Science Fiction", "tmdb_rating": 8.4, "poster_path": "/oYuSwwAIgo4oLRj9j4HTGTaMWNr.jpg"},
    {"id": 155, "title": "The Dark Knight", "genre": "Action, Crime, Drama", "tmdb_rating": 8.5, "poster_path": "/qJ2tW6WMUDp9s1vmsTuI9RCAz0d.jpg"},
    {"id": 603, "title": "The Matrix", "genre": "Action, Science Fiction", "tmdb_rating": 8.2, "poster_path": "/f89U3Y9S7qIDHk8Zp7qG2S3n9v2.jpg"},
    {"id": 120, "title": "The Lord of the Rings: The Fellowship of the Ring", "genre": "Action, Adventure, Fantasy", "tmdb_rating": 8.4, "poster_path": "/6oom5QYv7nyBLo74vS3qtI7ezPn.jpg"},
    {"id": 11, "title": "Star Wars", "genre": "Action, Adventure, Science Fiction", "tmdb_rating": 8.2, "poster_path": "/6FfWpYvt6fM9ImsC6ugHmcJvYvC.jpg"},
    
    # Comedy
    {"id": 105, "title": "Back to the Future", "genre": "Comedy, Science Fiction", "tmdb_rating": 8.3, "poster_path": "/fNbs6tHL9WsY7vWRAoYp9m76oP2.jpg"},
    {"id": 13, "title": "Forrest Gump", "genre": "Comedy, Drama, Romance", "tmdb_rating": 8.5, "poster_path": "/arw2vcBveWOVZr6pxm9LpEVMwwP.jpg"},
    {"id": 12, "title": "Finding Nemo", "genre": "Comedy, Animation, Family", "tmdb_rating": 7.8, "poster_path": "/eHuSUEjILwtDhrTuOBEhiqlTMVY.jpg"},
    {"id": 11324, "title": "The Hangover", "genre": "Comedy", "tmdb_rating": 7.3, "poster_path": "/7L6re69QG676jCjZ9q32lH80i7f.jpg"},
    {"id": 2108, "title": "The Breakfast Club", "genre": "Comedy, Drama", "tmdb_rating": 7.8, "poster_path": "/7XSl7j6p9y6SIn66fN9Y269q87d.jpg"},
    
    # Drama
    {"id": 278, "title": "The Shawshank Redemption", "genre": "Drama, Crime", "tmdb_rating": 8.7, "poster_path": "/9cq97v7yqXpms9vU6B9fU1S8v9f.jpg"},
    {"id": 238, "title": "The Godfather", "genre": "Drama, Crime", "tmdb_rating": 8.7, "poster_path": "/3bhkrjOiERbyv4BaoE606FAvTbh.jpg"},
    {"id": 424, "title": "Schindler's List", "genre": "Drama, History, War", "tmdb_rating": 8.6, "poster_path": "/sF1U4EUxk0Ds9S9An9vFLZz4oYv.jpg"},
    {"id": 389, "title": "12 Angry Men", "genre": "Drama", "tmdb_rating": 8.5, "poster_path": "/ppFdWz9Y5os9SIn66fN9Y269q87d.jpg"},
    {"id": 550, "title": "Fight Club", "genre": "Drama", "tmdb_rating": 8.4, "poster_path": "/jSziioSwPVrOy9Yow3XhWIBDjq1.jpg"},
    
    # Sci-Fi / Fantasy
    {"id": 157336, "title": "Interstellar", "genre": "Adventure, Drama, Science Fiction", "tmdb_rating": 8.4, "poster_path": "/gEU2QniE6E77NI6lCU6MxlSaba7.jpg"},
    {"id": 122, "title": "The Lord of the Rings: The Return of the King", "genre": "Action, Adventure, Fantasy", "tmdb_rating": 8.5, "poster_path": "/rCzpSbtYhi7HjFa1mueT6vUfvRk.jpg"},
    {"id": 121, "title": "The Lord of the Rings: The Two Towers", "genre": "Action, Adventure, Fantasy", "tmdb_rating": 8.4, "poster_path": "/5VTN0pRMG9un3tW3S87Y9ID7S.jpg"},
    {"id": 199, "title": "Star Trek", "genre": "Action, Adventure, Science Fiction", "tmdb_rating": 7.4, "poster_path": "/pfVssWShRToSIn66fN9Y269q87d.jpg"},
    {"id": 1891, "title": "The Empire Strikes Back", "genre": "Action, Adventure, Science Fiction", "tmdb_rating": 8.4, "poster_path": "/7WsyCh999SdwvP70vYv9pID7S.jpg"},

    # Horror / Thriller
    {"id": 694, "title": "The Shining", "genre": "Horror, Thriller", "tmdb_rating": 8.2, "poster_path": "/37SIn66fN9Y269q87d.jpg"},
    {"id": 807, "title": "Se7en", "genre": "Crime, Mystery, Thriller", "tmdb_rating": 8.3, "poster_path": "/69Sns8WoZ2p48p94p7B6Cq0Sdb8.jpg"},
    {"id": 429, "title": "The Good, the Bad and the Ugly", "genre": "Western", "tmdb_rating": 8.5, "poster_path": "/bX2xnavhMYjWDoZp1VM6VnU1xwe.jpg"},
    {"id": 128, "title": "Spirited Away", "genre": "Animation, Family, Fantasy", "tmdb_rating": 8.5, "poster_path": "/cMYCDADoLKLbB83g4WnJegaZimC.jpg"},
    {"id": 497, "title": "The Green Mile", "genre": "Fantasy, Drama, Crime", "tmdb_rating": 8.5, "poster_path": "/8VG8fDNiy50H4FedGwdSVUPoaJe.jpg"},
]

GENRE_OPTIONS = ["Action", "Adventure", "Animation", "Comedy", "Crime", "Documentary", "Drama", "Family", "Fantasy", "History", "Horror", "Music", "Mystery", "Romance", "Science Fiction", "Thriller", "War", "Western"]

def get_preloaded_recommendations(fav_genres, limit=5):
    """Filter STATIC_MOVIES based on the user's favorite genres."""
    recommendations = []
    if not fav_genres:
        return STATIC_MOVIES[:limit]
    
    fav_list = [g.strip().lower() for g in fav_genres.split(",")]
    
    # First pass: direct matches
    for movie in STATIC_MOVIES:
        m_genres = [g.strip().lower() for g in movie['genre'].split(",")]
        if any(g in m_genres for g in fav_list):
            recommendations.append(movie)
    
    # If not enough, fill with general top movies
    if len(recommendations) < limit:
        for movie in STATIC_MOVIES:
            if movie not in recommendations:
                recommendations.append(movie)
            if len(recommendations) >= limit:
                break
                
    return recommendations[:limit]
