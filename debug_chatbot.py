import sys
import os
sys.path.insert(0, '.')

# Reproduce the exact flow from main.py
import json
import re
from utils.matcher import Matcher

matcher = Matcher()

# Simulate user input
user_input = "suavignon blanc rosalia"
print(f"\n=== DEBUG CHATBOT FLOW ===")
print(f"User input: '{user_input}'")

# Step 1: Extract title/artist (same logic as main.py)
title, artist = None, None

# Lista de artistas conocidos (para ayudar en la detección)
known_artists = ["rosalia", "bad bunny", "j balvin", "ozuna", "anuel aa", "billie eilish",
                 "taylor swift", "ed sheeran", "the weeknd", "dua lipa", "shakira",
                 "luis fonsi", "maluma", "myke towers", "beyonce", "ariana grande",
                 "justin bieber", "drake", "post malone"]

patterns = [
    # Formato: "título – artista" (con guion)
    r"(?i)^(?P<title>.+?)\s[-–—]\s(?P<artist>.+)$",
    r"(?i)^(?P<artist>.+?)\s[-–—]\s(?P<title>.+)$",
    # Formato: "canción título de artista" o "song title by artist"
    r"(?i)\b(?:canción|song|busca|find)\s+['\"]?(?P<title>[^'\"]+)['\"]?\s+(?:de|by)\s+['\"]?(?P<artist>[^'\"]+)['\"]?",
    r"(?i)\b(?:canción|song|busca|find)\s+['\"]?(?P<title>[^'\"]+)['\"]?",
]

for pat in patterns:
    m = re.search(pat, user_input)
    if m:
        title = m.groupdict().get("title")
        artist = m.groupdict().get("artist")
        print(f"Pattern matched: {pat[:40]}...")
        break

# Si no se encontró con patrones anteriores, intentar detección heurística
if not title:
    clean_input = matcher.normalize_text(user_input)
    words = clean_input.split()

    if len(words) >= 2:
        # Buscar si la última palabra o combinación es un artista conocido
        last_word = words[-1].lower()
        last_two = ' '.join(words[-2:]).lower()

        for artist_name in known_artists:
            if artist_name in last_word or artist_name in last_two:
                artist = artist_name
                title = ' '.join(words[:-1]) if len(words) > 1 else ''
                print(f"Artist found: '{artist}', title: '{title}'")
                break

        # Si no se encontró artista conocido, tomar la última palabra como artista
        if not artist:
            artist = words[-1]
            title = ' '.join(words[:-1])
            print(f"No known artist found. Using last word as artist: '{artist}', title: '{title}'")

print(f"Title extracted: '{title}'")
print(f"Artist extracted: '{artist}'")

# Step 2: Check if title exists
if not title:
    print("NO TITLE EXTRACTED - would show 'No pude identificar la canción'")
else:
    print("Title extracted successfully")

    # Step 3: Simulate pending_search
    ps = {
        "title": title.strip(),
        "artist": artist.strip() if artist else "",
        "trigger": True
    }
    print(f"\nPending search: {ps}")

    # Step 4: Search in services
    from services.spotify_service import SpotifyService
    from services.youtube_service import YouTubeService
    from services.deezer_service import DeezerService

    spotify_service = SpotifyService()
    youtube_service = YouTubeService()
    deezer_service = DeezerService()

    # Search in each platform
    sp_link = yt_link = dz_link = None

    print("\n--- Searching in platforms ---")

    try:
        cands = spotify_service.search_track(title, artist)
        print(f"Spotify candidates: {len(cands)}")
        best, sc, _ = matcher.find_best_match(title, artist, cands)
        if best:
            sp_link = best["url"]
            print(f"Spotify best: {best.get('title')} - score: {sc}")
    except Exception as e:
        print(f"Spotify error: {e}")

    try:
        cands = youtube_service.search_track(title, artist)
        print(f"YouTube candidates: {len(cands)}")
        best, sc, _ = matcher.find_best_match(title, artist, cands)
        if best:
            yt_link = best["url"]
            print(f"YouTube best: {best.get('title')} - score: {sc}")
    except Exception as e:
        print(f"YouTube error: {e}")

    try:
        cands = deezer_service.search_track(title, artist)
        print(f"Deezer candidates: {len(cands)}")
        best, sc, _ = matcher.find_best_match(title, artist, cands)
        if best:
            dz_link = best["url"]
            print(f"Deezer best: {best.get('title')} - score: {sc}")
    except Exception as e:
        print(f"Deezer error: {e}")

    print(f"\n--- Results ---")
    print(f"Spotify link: {sp_link}")
    print(f"YouTube link: {yt_link}")
    print(f"Deezer link: {dz_link}")