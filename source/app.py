from flask import Flask, render_template, request
from flask_caching import Cache
import unicodedata
import re
from source.config import Config
from source.helper import Helper

# Prepare env
app = Flask(__name__)
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

# Clean special characters
@app.template_filter('slugify')
def slugify(value):
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
    # Try OMDB search
    search_data = Helper.search_omdb(search_request)

    # Fallback to TMDB suggestions
    if not search_data:
        tmdb_suggestions = Helper.search_tmdb(search_request)
        if tmdb_suggestions:
            search_data = Helper.search_omdb(tmdb_suggestions[0])

    if not search_data:
        return render_template('index.html', error="No results found. Try different keywords.")

    # Fetch detailed info
    results = search_data.get('Search', [])
    detailed_results = Helper.omdb_details(results)

    return render_template('select.html', results=detailed_results, search_request=search_request)

# Watch endpoint
@cache.cached(timeout=300, query_string=True)
@app.route('/watch/<title>')
def watch(title):
    imdb_id = request.args.get('id')
    season = int(request.args.get('season', 1))
    episode = int(request.args.get('episode', 1))
    title = title.replace('-', ' ')

    # Fetch all informations
    infos = Helper.omdb_details([{"imdbID": imdb_id}])[0]
    if not infos:
        return render_template('watch.html', error_message="Failed to load movie details")
    
    content_type = infos.get('Type', "N/A")
    title = infos.get('Title', "N/A")
    plot = infos.get('Plot', "N/A")

    # Build embed URL + seasons if series
    if content_type == 'series':
        embed_url = Config.working_vidsrc_url('series', imdb_id, season, episode)
        total_seasons = int(infos.get('totalSeasons', 0))
        seasons_object = Helper.seasons_and_episodes(imdb_id, total_seasons)
    else:
        embed_url = Config.working_vidsrc_url('movie', imdb_id)
        total_seasons = None
        seasons_object = None

    # watch.html details
    details = {
        "embed_url": embed_url,
        "title": title,
        "plot": plot,
        "type": content_type,
        "seasons_object": seasons_object,
        "current_episode": episode,
        "current_season": season,
        "total_seasons": total_seasons,
        "imdb_id": imdb_id,
    }

    return render_template('watch.html', **details)

# 404 error handler
@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(debug=True)
