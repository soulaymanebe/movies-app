from flask import Flask, render_template, request
import requests

app = Flask(__name__)

# Replace with your actual OMDb API key
OMDB_API_KEY = 'Add_Your_OMDb_Token'

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        movie_name = request.form.get('movieName')
        omdb_url = f'http://www.omdbapi.com/?apikey={OMDB_API_KEY}&t={movie_name}'
        omdb_response = requests.get(omdb_url).json()

        if omdb_response.get('Response') == 'True':
            imdb_id = omdb_response.get('imdbID')
            # Generate VidSRC embed URL
            embed_url = f'https://vidsrc.xyz/embed/movie/{imdb_id}'
            return render_template('watch.html', embed_url=embed_url, movie_title=omdb_response.get('Title'))
        else:
            error = omdb_response.get('Error', 'Movie not found.')
            return render_template('index.html', error=error)
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
