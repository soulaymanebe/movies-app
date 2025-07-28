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

   ```bash
   git clone https://github.com/soulaymanebe/movies-app
   cd movies-app
    ```

2. **Install dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

3. **Prepare the `.env` file**:
    Create a .env file in the root directory and add your OMDB API key, check `.env-example` file for instructions

---

### 🚀 **Run the Application**

**Once you've set up everything, you can launch the app by running**

```bash
gunicorn app:app --bind 0.0.0.0:5000
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
