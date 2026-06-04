import sys
sys.path.insert(0, '.')
from utils.matcher import Matcher
from services.spotify_service import SpotifyService
from services.youtube_service import YouTubeService
from services.deezer_service import DeezerService

matcher = Matcher()
spotify = SpotifyService()
youtube = YouTubeService()
deezer = DeezerService()

query_title = "suavignon blanc"
query_artist = "rosalia"

print(f"Searching for title: '{query_title}' artist: '{query_artist}'")

# Normalize via matcher
norm_title = matcher.normalize_text(query_title)
norm_artist = matcher.normalize_text(query_artist)
print(f"Normalized title: '{norm_title}'")
print(f"Normalized artist: '{norm_artist}'")

# Search Spotify
print("\n--- Spotify ---")
try:
    cands = spotify.search_track(norm_title, norm_artist)
    print(f"Found {len(cands)} candidates")
    for i, c in enumerate(cands[:5]):
        print(f"  {i}: {c.get('title')} - {c.get('artist')} (pop={c.get('popularity')})")
    if cands:
        best, score, _ = matcher.find_best_match(query_title, query_artist, cands)
        if best:
            print(f"Best match: {best.get('title')} - {best.get('artist')} score={score}")
        else:
            print("No best match")
except Exception as e:
    print(f"Error: {e}")

# Search YouTube
print("\n--- YouTube ---")
try:
    cands = youtube.search_track(norm_title, norm_artist)
    print(f"Found {len(cands)} candidates")
    for i, c in enumerate(cands[:5]):
        print(f"  {i}: {c.get('title')} - {c.get('artist')}")
    if cands:
        best, score, _ = matcher.find_best_match(query_title, query_artist, cands)
        if best:
            print(f"Best match: {best.get('title')} - {best.get('artist')} score={score}")
        else:
            print("No best match")
except Exception as e:
    print(f"Error: {e}")

# Search Deezer
print("\n--- Deezer ---")
try:
    cands = deezer.search_track(norm_title, norm_artist)
    print(f"Found {len(cands)} candidates")
    for i, c in enumerate(cands[:5]):
        print(f"  {i}: {c.get('title')} - {c.get('artist')}")
    if cands:
        best, score, _ = matcher.find_best_match(query_title, query_artist, cands)
        if best:
            print(f"Best match: {best.get('title')} - {best.get('artist')} score={score}")
        else:
            print("No best match")
except Exception as e:
    print(f"Error: {e}")

# Hybrid search across all
print("\n--- Combined Search ---")
all_cands = []
for svc, name in [(spotify, "Spotify"), (youtube, "YouTube"), (deezer, "Deezer")]:
    try:
        cands = svc.search_track(norm_title, norm_artist)
        for c in cands:
            c['source'] = name
            all_cands.append(c)
    except Exception as e:
        print(f"{name} error: {e}")

print(f"Total candidates: {len(all_cands)}")
if all_cands:
    best, score, status = matcher.find_best_match(query_title, query_artist, all_cands)
    if best:
        print(f"Best overall: {best.get('title')} - {best.get('artist')} from {best.get('source')} score={score} status={status}")
    else:
        print("No best match")
else:
    print("No candidates found")