# 🎬 **Movie Streamer** 

Welcome to **Movie Streamer** – a simple Python Flask app that allows you to stream your favorite movies effortlessly!

---

### 📋 **Prerequisites**

Before you get started, ensure you have the following:

- 🐍 **Python** installed.
- 🎥 **OMDB API token**: Sign up for an API key at [OMDb API](https://www.omdbapi.com/apikey.aspx).
- 🎥 **TMDB API token**: Sign up for an API key at [TMDb API](https://www.themoviedb.org/settings/api).

---

### ⚙️ **Setup**

1. **Clone the repository**:
2. **Create a virtual env**:
3. **Install dependencies**:
4. **Prepare the `.env` file**:
    Create a .env file in the root directory and add your OMDB API key, check `.env-example` file for instructions
5. **Export .env vars**

```
git clone https://github.com/soulaymanebe/movies-app
cd movies-app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export $(grep -v '^#' .env | xargs)
```

---

### 🚀 **Run the Application**

**Once you've set up everything, you can launch the app by running**

### On Linux

```bash
flask --app source.app run --debug # Debug mode
gunicorn source.app:app --bind 0.0.0.0:5000
```

### On Windows

Install waitress
```bash
pip install waitress
```

```bash
python -m waitress --host 127.0.0.1 --port 5000 source.app:app
```

### 🌐 **The app will be available at: `http://127.0.0.1:5000`**

### Using Docker

1. **Build the Docker Image:**
    ```sh
    docker build -t tmenyik .
    ```

2. **Run the Docker Container:**
    ```sh
    docker run -it tmenyik
    ```
