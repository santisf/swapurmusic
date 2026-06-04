import os
import re
import requests
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SpotifyService:
    def __init__(self):
        self.sp = None
        self.configured = False
        self._init_spotify()

    def _init_spotify(self):
        """Initialize Spotify client using environment variables."""
        try:
            import spotipy
            from spotipy.oauth2 import SpotifyClientCredentials
            client_id = os.getenv('SPOTIFY_CLIENT_ID')
            client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')

            if client_id and client_secret:
                auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
                self.sp = spotipy.Spotify(auth_manager=auth_manager)
                self.configured = True
                logger.info("Spotify client configured successfully")
        except Exception as e:
            logger.warning(f"Spotify client not configured: {e}")

    def is_configured(self):
        return self.configured

    @staticmethod
    def parse_song_and_artist_from_title(raw_title: str) -> dict:
        """Parse title string to separate song title and artist."""
        raw_title = re.sub(r'\s*-\s*Topic$', '', raw_title, flags=re.IGNORECASE)
        raw_title = re.sub(r'\s*-\s*Official$', '', raw_title, flags=re.IGNORECASE)
        raw_title = re.sub(r'\s*-\s*Lyrics?$', '', raw_title, flags=re.IGNORECASE).strip()

        if ' - ' in raw_title:
            parts = raw_title.split(' - ', 1)
            title = parts[0].strip()
            artist = parts[1].strip()
        else:
            title = raw_title.strip()
            artist = "Unknown Artist"

        artist = re.sub(r'\s*-\s*Topic$', '', artist, flags=re.IGNORECASE).strip()
        title = re.sub(r'[\(\[][Oo]fficial[\s\w]*[\)\]]', '', title, flags=re.IGNORECASE).strip()
        return {"title": title, "artist": artist}

    def public_search_track(self, title: str, artist: str) -> list:
        """
        Public search method - currently returns empty list.
        Spotify's search page requires JavaScript rendering and their API
        needs a Premium account. For now, this method is a placeholder.
        """
        logger.warning("Public search not available - Spotify API requires Premium subscription")
        return []

    def search_track(self, title: str, artist: str) -> list:
        """Search for a track on Spotify, with fallback to public scraping."""
        if self.sp:
            try:
                clean_title = re.sub(r"[\(\[][Oo]fficial[\s\w]*[\)\]]", "", title, flags=re.IGNORECASE).strip()
                clean_artist = artist.replace(" - Topic", "").strip()

                artists_list = [s.strip() for s in re.split(r"[,&]|\bfeat\.?\b|\band\b", clean_artist) if s.strip()]
                primary_artist = artists_list[0] if artists_list else ""

                strategies = []
                if primary_artist:
                    strategies.append(f'track:"{clean_title}" artist:"{primary_artist}"')
                if clean_artist and clean_artist != primary_artist:
                    strategies.append(f'track:"{clean_title}" artist:"{clean_artist}"')
                if primary_artist:
                    strategies.append(f"{primary_artist} {clean_title}")
                if artists_list:
                    strategies.append(f'{" ".join(artists_list)} {clean_title}')
                strategies.append(clean_title)

                tracks = []
                api_failed = False
                for query in strategies:
                    try:
                        results = self.sp.search(q=query, type="track", limit=5)
                        items = results.get("tracks", {}).get("items", [])
                        if items:
                            tracks = items
                            break
                    except Exception as ex:
                        logger.warning(f"Spotify strategy search failed: {ex}")
                        api_failed = True
                        break

                if tracks:
                    candidates = []
                    for track in tracks:
                        candidates.append({
                            "title": track["name"],
                            "artist": ", ".join([a["name"] for a in track["artists"]]),
                            "url": f"https://open.spotify.com/track/{track['id']}"
                        })
                    return candidates

                if api_failed:
                    return self.public_search_track(title, artist)
            except Exception as e:
                logger.error(f"Spotify API error: {e}")
                return []
        else:
            return self.public_search_track(title, artist)

    def get_track_details(self, track_id: str) -> dict:
        """Get detailed metadata for a Spotify track using fallback methods."""
        if self.sp:
            try:
                track = self.sp.track(track_id)
                return {
                    "title": track["name"],
                    "artist": ", ".join([a["name"] for a in track["artists"]]),
                    "album": track["album"]["name"],
                    "url": track["external_urls"]["spotify"],
                    "duration_ms": track["duration_ms"]
                }
            except Exception as e:
                logger.error(f"Spotify API error fetching track details: {e}")

        # Fallback: try to get details using public scraping
        try:
            track_url = f"https://open.spotify.com/track/{track_id}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9"
            }

            res = requests.get(track_url, headers=headers, timeout=10)
            if not res.ok:
                return {}

            html = res.text

            title_match = re.search(r'<title>([^<]+)</title>', html)
            og_title_match = re.search(r'<meta\s+property="og:title"\s+content="([^"]+)"', html)
            title = title_match.group(1) if title_match else (og_title_match.group(1) if og_title_match else "Unknown Title")

            artist_match = re.search(r'"artistName":"([^"]+)"', html)
            artist = artist_match.group(1) if artist_match else "Unknown Artist"

            return {
                "title": title,
                "artist": artist,
                "url": track_url
            }
        except Exception as e:
            logger.error(f"Error extracting track details: {e}")
            return {}