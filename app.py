from flask import Flask, render_template, request
import requests, os, re, unicodedata
from flask_caching import Cache
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
app = Flask(__name__)
cache = Cache(app, config={'CACHE_TYPE': 'simple'})
OMDB_API_KEY = os.getenv("OMDB_API_KEY")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

# Custom filter to clean special characters
@app.template_filter('slugify')
def slugify(value):
    if not value:
        return ''
    value = str(value)
    value = unicodedata.normalize('NFD', value)
    value = value.encode('ascii', 'ignore').decode('utf-8')
    value = re.sub(r'[^a-zA-Z0-9]+', '-', value)
    return value.strip('-')

# Main endpoint
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

# Results endpoint
@cache.cached(timeout=300, query_string=True)
@app.route('/results/<search_request>')
def results(search_request):
    error_message = None
    results = []

    try:
        # TMDb Search API for fuzzy matching
        tmdb_search_url = f'https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={search_request}'
        tmdb_response = requests.get(tmdb_search_url)
        tmdb_response.raise_for_status()
        tmdb_data = tmdb_response.json()

        if tmdb_data.get('results'):
            results = tmdb_data['results']
            detailed_results = []

            # Fetch detailed movie info from OMDb using the corrected TMDb titles
            for result in results:
                movie_title = result['title']
                omdb_url = f'http://www.omdbapi.com/?apikey={OMDB_API_KEY}&t={movie_title}'
                omdb_response = requests.get(omdb_url)
                omdb_response.raise_for_status()
                detailed_results.append(omdb_response.json())

            return render_template('select.html', results=detailed_results, search_request=search_request)

        else:
            error_message = "No results found. Please try a different search."

    except requests.exceptions.RequestException as e:
        error_message = str(e)

    return render_template('index.html', error=error_message)

# Watch endpoint
@cache.cached(timeout=300, query_string=True)
@app.route('/watch/<title>')
def watch(title):
    title = title.replace('-', ' ')
    omdb_url = f'http://www.omdbapi.com/?apikey={OMDB_API_KEY}&t={title}'
    
    try:
        omdb_response = requests.get(omdb_url)
        omdb_response.raise_for_status()
        details_data = omdb_response.json()
    except requests.exceptions.RequestException as e:
        return render_template('watch.html', error_message=str(e))

    imdb_id = details_data.get('imdbID')
    movie_type = details_data.get('Type', "N/A")
    movie_title = details_data.get('Title', "N/A")
    plot = details_data.get('Plot', "N/A")
    plot = '<br>'.join(plot[i:i + 223] for i in range(0, len(plot), 225))

    season = int(request.args.get('season', 1))
    episode = int(request.args.get('episode', 1))

    if movie_type == 'series':
        embed_url = f'https://vidsrc.xyz/embed/tv/{imdb_id}/{season}-{episode}?ads=false'
    else:
        embed_url = f'https://vidsrc.xyz/embed/movie/{imdb_id}?ads=false'

    return render_template(
        'watch.html',
        embed_url=embed_url,
        title=movie_title,
        plot=plot,
        type=movie_type
    )

# 404 Error Handler
@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(debug=True)
