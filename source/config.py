import logging
import os
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlencode

import requests

logger = logging.getLogger("tmenyik.config")

_DEFAULT_DOMAINS = [
    "vidsrcme.ru",
    "vidsrcme.su",
    "vidsrc-me.ru",
    "vidsrc-me.su",
    "vidsrc-embed.ru",
    "vidsrc-embed.su",
    "vsrc.su"
]

VIDSRC_DOMAINS = [
    d.strip()
    for d in os.getenv("VIDSRC_DOMAINS", ",".join(_DEFAULT_DOMAINS)).split(",")
    if d.strip()
]

PLAYER_PARAM_KEYS = {
    "autoplay": "autoplay",
    "color": "color",
    "sub": "sub",
    "start": "start",
}

_session = requests.Session()

class Config:
    @staticmethod
    def working_vidsrc_url(content_type, imdb_id, season=None, episode=None,
                           autoplay=None, color=None, sub=None, start=None):
        extra = {}
        if autoplay is not None:
            extra[PLAYER_PARAM_KEYS["autoplay"]] = "1" if autoplay else "0"
        if color:
            extra[PLAYER_PARAM_KEYS["color"]] = color.lstrip("#")
        if sub:
            extra[PLAYER_PARAM_KEYS["sub"]] = sub
        if start:
            extra[PLAYER_PARAM_KEYS["start"]] = str(start)

        def build_url(domain):
            if content_type == "series":
                base = f"https://{domain}/embed/tv/{imdb_id}/{season}-{episode}?ads=false"
            else:
                base = f"https://{domain}/embed/movie/{imdb_id}?ads=false"
            if extra:
                base += "&" + urlencode(extra)
            return base

        def is_reachable(domain):
            url = build_url(domain)
            try:
                resp = _session.get(url, timeout=3, stream=True)
                resp.close()
                return url if resp.status_code == 200 else None
            except requests.exceptions.RequestException:
                return None

        if not VIDSRC_DOMAINS:
            logger.warning("No embed domains configured (set VIDSRC_DOMAINS).")
            return None

        with ThreadPoolExecutor(max_workers=len(VIDSRC_DOMAINS)) as executor:
            results = dict(zip(VIDSRC_DOMAINS, executor.map(is_reachable, VIDSRC_DOMAINS)))

        for domain in VIDSRC_DOMAINS:
            if results.get(domain):
                return results[domain]

        logger.info("No reachable embed domain for %s.", imdb_id)
        return None
