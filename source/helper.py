import logging
import os
from concurrent.futures import ThreadPoolExecutor

import requests
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

load_dotenv()

logger = logging.getLogger("tmenyik.helper")

OMDB_API_KEY = os.getenv("OMDB_API_KEY")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

OMDB_URL = "https://www.omdbapi.com/"
TMDB_SEARCH_URL = "https://api.themoviedb.org/3/search/multi"

if not OMDB_API_KEY:
    logger.warning("OMDB_API_KEY is not set — OMDB requests will fail.")
if not TMDB_API_KEY:
    logger.warning("TMDB_API_KEY is not set — TMDB fallback is disabled.")


def _build_session(pool_size=10):
    session = requests.Session()
    retry = Retry(
        total=2,
        backoff_factor=0.3,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET", "HEAD"),
    )
    adapter = HTTPAdapter(
        max_retries=retry,
        pool_connections=pool_size,
        pool_maxsize=pool_size,
    )
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


SESSION = _build_session()

class Helper:
    @staticmethod
    def search_tmdb(search_request):
        if not TMDB_API_KEY:
            return []
        try:
            resp = SESSION.get(
                TMDB_SEARCH_URL,
                params={"api_key": TMDB_API_KEY, "query": search_request},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
        except requests.exceptions.RequestException as e:
            logger.warning("TMDB query failed for %r: %s", search_request, e)
            return []

        titles = []
        for item in data.get("results", []):
            if item.get("media_type") in ("movie", "tv"):
                name = item.get("title") or item.get("name")
                if name:
                    titles.append(name)
        return titles

    @staticmethod
    def search_omdb(search_term):
        if not OMDB_API_KEY:
            return None
        try:
            resp = SESSION.get(
                OMDB_URL,
                params={"apikey": OMDB_API_KEY, "s": search_term},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
        except requests.exceptions.RequestException as e:
            logger.warning("OMDB search failed for %r: %s", search_term, e)
            return None
        return data if data.get("Response") == "True" else None

    @staticmethod
    def omdb_details(imdb_data):
        imdb_ids = [item["imdbID"] for item in imdb_data if item.get("imdbID")]
        if not imdb_ids:
            return []

        def fetch_details(imdb_id):
            try:
                resp = SESSION.get(
                    OMDB_URL,
                    params={"apikey": OMDB_API_KEY, "i": imdb_id},
                    timeout=5,
                )
                resp.raise_for_status()
                return resp.json()
            except requests.exceptions.RequestException as e:
                logger.warning("OMDB details failed for %s: %s", imdb_id, e)
                return None

        results = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            for result in executor.map(fetch_details, imdb_ids):
                if result and result.get("Response") == "True":
                    results.append(result)
        return results

    @staticmethod
    def seasons_and_episodes(imdb_id, total_seasons):
        if total_seasons <= 0:
            return {}

        def fetch_season(season_num):
            try:
                resp = SESSION.get(
                    OMDB_URL,
                    params={"apikey": OMDB_API_KEY, "i": imdb_id, "Season": season_num},
                    timeout=5,
                )
                resp.raise_for_status()
                episodes = resp.json().get("Episodes", []) or []
            except requests.exceptions.RequestException as e:
                logger.warning("OMDB season %s failed for %s: %s", season_num, imdb_id, e)
                return (season_num, [])

            parsed = [
                {"title": ep.get("Title", "N/A"), "episode": ep.get("Episode", "")}
                for ep in episodes
            ]

            parsed.sort(
                key=lambda ep: int(ep["episode"]) if str(ep["episode"]).isdigit() else 0
            )
            return (season_num, parsed)

        seasons_object = {}
        with ThreadPoolExecutor(max_workers=10) as executor:
            for season_num, episodes in executor.map(
                fetch_season, range(1, total_seasons + 1)
            ):
                seasons_object[f"Season {season_num}"] = episodes
        return seasons_object
