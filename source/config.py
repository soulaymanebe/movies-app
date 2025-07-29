from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

# Other domains
VIDSRC_DOMAINS = [
    "vidsrc.xyz",
    "vidsrc.me",
    "vidsrc.in",
    "vidsrc.pm",
    "vidsrc.net",
    "vidsrc.io",
    "vidsrc.vc"
]

class Config:
    @staticmethod
    def working_vidsrc_url(content_type, imdb_id, season=None, episode=None):
        def build_url(domain):
            if content_type == 'series':
                return f"https://{domain}/embed/tv/{imdb_id}/{season}-{episode}?ads=false"
            else:
                return f"https://{domain}/embed/movie/{imdb_id}?ads=false"

        def check_domain(domain):
            url = build_url(domain)
            try:
                resp = requests.get(url, timeout=3)
                if resp.status_code == 200:
                    return url
            except requests.exceptions.RequestException:
                return None
            return None

        with ThreadPoolExecutor(max_workers=len(VIDSRC_DOMAINS)) as executor:
            futures = {executor.submit(check_domain, domain): domain for domain in VIDSRC_DOMAINS}
            for future in as_completed(futures):
                result = future.result()
                if result:
                    return result
        return None
