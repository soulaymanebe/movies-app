import logging
import os
import re
import unicodedata

from flask import Flask, render_template, request, abort
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
                # Details all failed (likely network) — don't cache an empty page.
                return render_template(
                    "index.html",
                    error="Couldn't load details right now. Please try again.",
                )

            html = render_template(
                "select.html",
                results=detailed,
                search_request=search_request,
            )
            cache.set(cache_key, html, timeout=300)  # cache the good result only
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

        season = safe_int(request.args.get("season"), default=1)
        episode = safe_int(request.args.get("episode"), default=1)

        # Only successful renders are cached (keyed on id/season/episode), so a
        # failed metadata load is never stored and won't stick after reconnect.
        cache_key = f"watch:{imdb_id}:{season}:{episode}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            details_list = Helper.omdb_details([{"imdbID": imdb_id}])
            infos = details_list[0] if details_list else None
        except Exception:
            logger.exception("omdb_details() failed for %s", imdb_id)
            infos = None

        if not infos:
            return render_template(
                "watch.html",
                error_message="Failed to load movie details.",
            )

        content_type = infos.get("Type", "N/A")
        title = infos.get("Title", "N/A")
        plot = infos.get("Plot", "N/A")

        if content_type == "series":
            embed_url = Config.working_vidsrc_url("series", imdb_id, season, episode)
            total_seasons = safe_int(infos.get("totalSeasons"), default=0, minimum=0)
            seasons_object = Helper.seasons_and_episodes(imdb_id, total_seasons)
        else:
            embed_url = Config.working_vidsrc_url("movie", imdb_id)
            total_seasons = None
            seasons_object = None

        html = render_template(
            "watch.html",
            embed_url=embed_url,
            title=title,
            plot=plot,
            type=content_type,
            seasons_object=seasons_object,
            current_episode=episode,
            current_season=season,
            total_seasons=total_seasons,
            imdb_id=imdb_id,
        )
        cache.set(cache_key, html, timeout=300)
        return html

    # Lightweight health check
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
    # debug is OFF unless explicitly enabled
    app.run(debug=os.getenv("FLASK_DEBUG", "0") == "1")
