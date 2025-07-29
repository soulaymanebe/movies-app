import os
import requests
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor

load_dotenv()
OMDB_API_KEY = os.getenv("OMDB_API_KEY")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

class Helper:
    @staticmethod
    def search_tmdb(search_request):
        tmdb_url = f'https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={search_request}'
        try:
            response = requests.get(tmdb_url)
            response.raise_for_status()
            tmdb_data = response.json()

            if tmdb_data.get('results'):
                return [movie['title'] for movie in tmdb_data['results']]
            else:
                return []
        except requests.exceptions.RequestException as e:
            print(f"Error querying TMDB: {e}")
            return []

    @staticmethod
    def search_omdb(search_term):
        search_url = f'http://www.omdbapi.com/?apikey={OMDB_API_KEY}&s={search_term}'
        try:
            response = requests.get(search_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data if data.get('Response') == 'True' else None
        except requests.exceptions.RequestException as e:
            print(f"OMDB search failed: {e}")
            return None

    @staticmethod
    def omdb_details(imdb_data):
        imdb_ids = [item["imdbID"] for item in imdb_data if "imdbID" in item]

        def fetch_details(imdb_id):
            url = f'http://www.omdbapi.com/?apikey={OMDB_API_KEY}&i={imdb_id}'
            try:
                resp = requests.get(url, timeout=5)
                resp.raise_for_status()
                return resp.json()
            except requests.exceptions.RequestException:
                return None

        results = []
        with ThreadPoolExecutor(max_workers=10) as executor:  # 10 parallel requests
            for result in executor.map(fetch_details, imdb_ids):
                if result:
                    results.append(result)
        return results

    @staticmethod
    def seasons_and_episodes(imdb_id, total_seasons):
        def fetch_season(s):
            url = f'http://www.omdbapi.com/?apikey={OMDB_API_KEY}&i={imdb_id}&Season={s}'
            try:
                resp = requests.get(url, timeout=5)
                resp.raise_for_status()
                episodes = resp.json().get('Episodes', [])
                return (f'Season {s}', [{"title": ep["Title"], "episode": ep["Episode"]} for ep in episodes])
            except requests.exceptions.RequestException:
                return (f'Season {s}', [])
        
        seasons_object = {}
        with ThreadPoolExecutor(max_workers=10) as executor:
            for season, episodes in executor.map(fetch_season, range(1, total_seasons + 1)):
                seasons_object[season] = episodes
        return seasons_object
