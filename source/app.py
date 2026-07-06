import logging
import os
import re
import unicodedata

from flask import Flask, render_template, request, abort, url_for, redirect
from flask_caching import Cache

from source.config import Config
from source.helper import Helper


def create_app():
    app = Flask(__name__)

    app.config.update(
        CACHE_TYPE=os.getenv("CACHE_TYPE", "SimpleCache"),
        CACHE_DEFAULT_TIMEOUT=int(os.getenv("CACHE_TIMEOUT", "300")),
    )
    cache = Cache(app)

    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    logger = logging.getLogger("tmenyik")

    # --- Jinja filter ---
    @app.template_filter("slugify")
    def slugify(value):
        value = unicodedata.normalize("NFD", value or "")
        value = value.encode("ascii", "ignore").decode("utf-8")
        value = re.sub(r"[^a-zA-Z0-9]+", "-", value)
        return value.strip("-")

    def safe_int(raw, default=1, minimum=1):
        try:
            return max(minimum, int(raw))
        except (TypeError, ValueError):
            return default

    # --- Routes ---
    @app.route("/", methods=["GET"])
    def index():
        return render_template("index.html")

    @app.route("/results/<search_request>")
    def results(search_request):
        cache_key = f"results:{search_request}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            search_data = Helper.search_omdb(search_request)

            # Fallback: let TMDB correct the spelling, then re-query OMDB
            if not search_data:
                suggestions = Helper.search_tmdb(search_request)
                if suggestions:
                    search_data = Helper.search_omdb(suggestions[0])

            if not search_data:
                return render_template(
                    "index.html",
                    error="No results found. Try different keywords.",
                )

            # Keep only movies and series — OMDB also returns games and episodes.
            items = [
                i for i in search_data.get("Search", [])
                if i.get("Type") in ("movie", "series")
            ]
            if not items:
                return render_template(
                    "index.html",
                    error="No movies or series found. Try different keywords.",
                )

            detailed = Helper.omdb_details(items)
            detailed = [d for d in detailed if d.get("Type") in ("movie", "series")]
            if not detailed:
                return render_template(
                    "index.html",
                    error="Couldn't load details right now. Please try again.",
                )

            html = render_template(
                "select.html",
                results=detailed,
                search_request=search_request,
            )
            cache.set(cache_key, html, timeout=300)
            return html
        except Exception:
            logger.exception("results() failed for %r", search_request)
            return render_template(
                "index.html",
                error="Something went wrong while searching. Please try again.",
            )

    @app.route("/watch/<title>")
    def watch(title):
        imdb_id = request.args.get("id")
        if not imdb_id:
            abort(404)

        raw_season = request.args.get("season")
        raw_episode = request.args.get("episode")

        season = safe_int(raw_season, default=1)
        episode = safe_int(raw_episode, default=1, minimum=0)

        try:
            details_list = Helper.omdb_details([{"imdbID": imdb_id}])
            infos = details_list[0] if details_list else None
        except Exception:
            logger.exception("omdb_details() failed for %s", imdb_id)
            infos = None

        if not infos:
            return render_template(
                "watch.html",
                title=title.replace("-", " ").title(),
                error_message="Couldn't load this title right now — check your connection and retry.",
            )

        content_type = infos.get("Type", "N/A")
        title = infos.get("Title", "N/A")
        plot = infos.get("Plot", "")
        poster = infos.get("Poster", "")

        THEME_COLOR = "ff6347"

        if content_type == "series":
            total_seasons = safe_int(infos.get("totalSeasons"), default=0, minimum=0)
            seasons_object = Helper.seasons_and_episodes(imdb_id, total_seasons)

            if raw_season is None or raw_episode is None:
                first_s, first_e = Helper.first_episode(seasons_object)
                return redirect(url_for(
                    "watch",
                    title=title.replace(" ", "-"),
                    id=imdb_id,
                    season=first_s,
                    episode=first_e,
                ))

            cache_key = f"watch:{imdb_id}:{season}:{episode}"
            cached = cache.get(cache_key)
            if cached is not None:
                return cached

            embed_url = Config.working_vidsrc_url(
                "series", imdb_id, season, episode, autoplay=True, color=THEME_COLOR
            )
            prev_pair, next_pair = Helper.episode_neighbors(seasons_object, season, episode)
        else:
            cache_key = f"watch:{imdb_id}:movie"
            cached = cache.get(cache_key)
            if cached is not None:
                return cached

            embed_url = Config.working_vidsrc_url(
                "movie", imdb_id, autoplay=True, color=THEME_COLOR
            )
            total_seasons = None
            seasons_object = None
            prev_pair, next_pair = (None, None)

        def ep_url(pair):
            if not pair:
                return None
            s, e = pair
            return url_for("watch", title=title.replace(" ", "-"), id=imdb_id, season=s, episode=e)

        runtime_match = re.match(r"(\d+)", infos.get("Runtime", "") or "")
        runtime_minutes = int(runtime_match.group(1)) if runtime_match else 0

        html = render_template(
            "watch.html",
            embed_url=embed_url,
            title=title,
            plot=plot,
            poster=poster,
            type=content_type,
            seasons_object=seasons_object,
            current_episode=episode,
            current_season=season,
            total_seasons=total_seasons,
            imdb_id=imdb_id,
            prev_url=ep_url(prev_pair),
            next_url=ep_url(next_pair),
            next_season=next_pair[0] if next_pair else None,
            next_episode=next_pair[1] if next_pair else None,
            runtime_minutes=runtime_minutes,
        )
        cache.set(cache_key, html, timeout=300)
        return html

    @app.route("/healthz")
    def healthz():
        return {"status": "ok"}, 200

    # --- Error handlers ---
    @app.errorhandler(404)
    def page_not_found(error):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def server_error(error):
        logger.exception("Unhandled server error")
        return render_template("500.html"), 500

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "0") == "1")