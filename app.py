from flask import Flask, render_template, request
import requests

app = Flask(__name__)
OMDB_API_KEY = '835ed759'

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        movie_name = request.form.get('movieName')
        search_url = f'http://www.omdbapi.com/?apikey={OMDB_API_KEY}&s={movie_name}'
        search_response = requests.get(search_url).json()

        if search_response.get('Response') == 'True':
            results = search_response.get('Search', [])
            return render_template('select.html', results=results)
        else:
            error = search_response.get('Error', 'No results found.')
            return render_template('index.html', error=error)
    return render_template('index.html')

@app.route('/watch/<imdb_id>')
def watch(imdb_id):
    details_url = f'http://www.omdbapi.com/?apikey={OMDB_API_KEY}&i={imdb_id}'
    details_response = requests.get(details_url).json()
    
    print(details_response)

    type    = details_response.get('Type', "N/A")
    title           = details_response.get('Title', "N/A")
    plot            = details_response.get('Plot', "N/A")
    plot            = '<br>'.join(plot[i:i + 223] for i in range(0, len(plot), 225))

    if type == 'series':
        embed_url = f'https://vidsrc.xyz/embed/tv/{imdb_id}?ads=false'
    else:
        embed_url = f'https://vidsrc.xyz/embed/movie/{imdb_id}?ads=false'
    
    return render_template('watch.html', embed_url=embed_url, title=title, plot=plot)

if __name__ == '__main__':
    app.run(debug=True)
