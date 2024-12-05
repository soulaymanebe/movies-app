from flask import Flask, render_template, request
import requests, os, re, unicodedata
from flask_caching import Cache
from dotenv import load_dotenv

# Prepare app env
load_dotenv()
app = Flask(__name__)
cache = Cache(app, config={'CACHE_TYPE': 'simple'})
OMDB_API_KEY = os.getenv("OMDB_API_KEY")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")


# Custom filter to clean special characters
@app.template_filter('slugify')
def slugify(value):
    value = unicodedata.normalize('NFD', value)
    value = value.encode('ascii', 'ignore').decode('utf-8')
    value = re.sub(r'[^a-zA-Z0-9]+', '-', value)
    return value.strip('-')

# Function to Search TMDB
def search_tmdb_for_suggestions(search_request):
    tmdb_url = f'https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={search_request}'
    try:
        response = requests.get(tmdb_url)
        response.raise_for_status()
        tmdb_data = response.json()

        if tmdb_data.get('results'):
            # Extract movie titles from the TMDB results
            return [movie['title'] for movie in tmdb_data['results']]
        else:
            return []
    except requests.exceptions.RequestException as e:
        print(f"Error querying TMDB: {e}")
        return []

# Main endpoint
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

# Results endpoint with caching
@cache.cached(timeout=300, query_string=True)
@app.route('/results/<search_request>')
def results(search_request):    
    error_message = None
    results = []

    try:
        # Search OMDB first
        search_url = f'http://www.omdbapi.com/?apikey={OMDB_API_KEY}&s={search_request}'
        search_response = requests.get(search_url)
        search_response.raise_for_status()
        search_data = search_response.json()

        if search_data.get('Response') == 'True':
            results = search_data.get('Search', [])
            detailed_results = []

            for result in results:
                details_url = f'http://www.omdbapi.com/?apikey={OMDB_API_KEY}&i={result["imdbID"]}'
                details_response = requests.get(details_url)
                details_response.raise_for_status()
                detailed_results.append(details_response.json())

            return render_template('select.html', results=detailed_results, search_request=search_request)

        else:
            # Fallback to TMDB for suggestions
            tmdb_suggestions = search_tmdb_for_suggestions(search_request)
            print(tmdb_suggestions)

            if tmdb_suggestions:
                # Use the first suggestion to query OMDB again
                corrected_search = tmdb_suggestions[0]
                corrected_search_url = f'http://www.omdbapi.com/?apikey={OMDB_API_KEY}&s={corrected_search}'
                corrected_search_response = requests.get(corrected_search_url)
                corrected_search_response.raise_for_status()
                corrected_search_data = corrected_search_response.json()

                if corrected_search_data.get('Response') == 'True':
                    results = corrected_search_data.get('Search', [])
                    detailed_results = []

                    for result in results:
                        details_url = f'http://www.omdbapi.com/?apikey={OMDB_API_KEY}&i={result["imdbID"]}'
                        details_response = requests.get(details_url)
                        details_response.raise_for_status()
                        detailed_results.append(details_response.json())

                    return render_template('select.html', results=detailed_results, search_request=corrected_search)

            error_message = search_data.get('Error', 'No results found. Try searching with different keywords.')

    except requests.exceptions.RequestException as e:
        error_message = str(e)

    return render_template('index.html', error=error_message)

# Watch endpoint with caching for details
@cache.cached(timeout=300, query_string=True)
@app.route('/watch/<title>')
def watch(title):
    title = title.replace('-', ' ')
    details_url = f'http://www.omdbapi.com/?apikey={OMDB_API_KEY}&t={title}'
    
    try:
        details_response = requests.get(details_url)
        details_response.raise_for_status()
        details_data = details_response.json()
    except requests.exceptions.RequestException as e:
        return render_template('watch.html', error_message=str(e))

    imdb_id = details_data.get('imdbID')
    type = details_data.get('Type', "N/A")
    title = details_data.get('Title', "N/A")
    plot = details_data.get('Plot', "N/A")
    plot = '<br>'.join(plot[i:i + 223] for i in range(0, len(plot), 225))

    season = int(request.args.get('season', 1))
    episode = int(request.args.get('episode', 1))

    # Gather season/episode data for series
    if type == 'series':
        embed_url = f'https://vidsrc.xyz/embed/tv/{imdb_id}/{season}-{episode}?ads=false'
        total_seasons = int(details_data.get('totalSeasons', 0))
        seasons_object = {}
        for s in range(1, total_seasons + 1):
            season_url = f'http://www.omdbapi.com/?apikey={OMDB_API_KEY}&i={imdb_id}&Season={s}'
            season_response = requests.get(season_url)
            season_response.raise_for_status()
            episodes = season_response.json().get('Episodes', [])
            seasons_object[f'Season {s}'] = [
                {"title": ep["Title"], "episode": ep["Episode"]} for ep in episodes
            ]
    else:
        embed_url = f'https://vidsrc.xyz/embed/movie/{imdb_id}?ads=false'
        seasons_object = None
        total_seasons = None

    return render_template('watch.html', embed_url=embed_url, title=title, plot=plot, type=type, seasons_object=seasons_object, current_episode=episode, current_season=season, total_seasons=total_seasons)

# 404 error handler
@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(debug=True)
