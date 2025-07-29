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
        for domain in VIDSRC_DOMAINS:
            try:
                if content_type == 'series':
                    url = f"https://{domain}/embed/tv/{imdb_id}/{season}-{episode}?ads=false"
                else:
                    url = f"https://{domain}/embed/movie/{imdb_id}?ads=false"
                
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    return url
            except requests.exceptions.RequestException:
                continue
        return None
