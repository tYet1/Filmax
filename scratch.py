import requests, os, json
from dotenv import load_dotenv
load_dotenv('d:/FDA/FDA_Project/.env')
TMDB_API_KEY = os.getenv('TMDB_API_KEY')
movies = ['Inception', 'The Dark Knight', 'The Matrix', 'The Lord of the Rings: The Fellowship of the Ring', 'Star Wars', 'Back to the Future', 'Forrest Gump', 'Finding Nemo', 'The Hangover', 'The Breakfast Club', 'The Shawshank Redemption', 'The Godfather', 'Schindler\'s List', '12 Angry Men', 'Fight Club', 'Interstellar', 'The Lord of the Rings: The Return of the King', 'The Lord of the Rings: The Two Towers', 'Star Trek', 'The Empire Strikes Back', 'The Shining', 'Se7en', 'The Good, the Bad and the Ugly', 'Spirited Away', 'The Green Mile']

res = []
for m in movies:
    r = requests.get(f'https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={m}').json()
    if r.get('results'):
        best = r['results'][0]
        # get details for genres
        d = requests.get(f'https://api.themoviedb.org/3/movie/{best["id"]}?api_key={TMDB_API_KEY}').json()
        genres = ", ".join([g['name'] for g in d.get('genres', [])])
        res.append({
            'id': best['id'],
            'title': best['title'],
            'genre': genres,
            'tmdb_rating': best['vote_average'],
            'poster_path': best['poster_path']
        })

print(json.dumps(res, indent=4))
