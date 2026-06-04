import os
import re
import requests

def public_search_track(title, artist):
    clean_title = re.sub(r'[^\w\s\-&\']', '', title)
    clean_artist = re.sub(r'[^\w\s\-&\']', '', artist)

    if not clean_title or not clean_artist:
        return []

    query = f'{clean_artist} {clean_title}'.strip()
    search_url = f'https://open.spotify.com/search/{requests.utils.quote(query)}'

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9'
    }

    res = requests.get(search_url, headers=headers, timeout=10)
    print(f'Search URL: {search_url}')
    print(f'Status code: {res.status_code}')
    print(f'HTML length: {len(res.text)}')

    html = res.text

    # Find track IDs in the HTML - more flexible pattern
    track_ids1 = re.findall(r'trackUri.*?spotify:track:([a-zA-Z0-9]+)', html)
    print(f'Pattern 1 found: {len(track_ids1)} track IDs')

    # Try different patterns
    track_ids2 = re.findall(r'/track/([a-zA-Z0-9]+)', html)
    print(f'Pattern 2 found: {len(track_ids2)} track IDs')

    track_ids = track_ids1[:5] if track_ids1 else track_ids2[:5]

    candidates = []
    seen_ids = set()

    for track_id in track_ids:
        if track_id in seen_ids:
            continue
        seen_ids.add(track_id)

        try:
            track_url = f'https://open.spotify.com/track/{track_id}'
            track_res = requests.get(track_url, headers=headers, timeout=10)
            print(f'Track {track_id} status: {track_res.status_code}')

            if not track_res.ok:
                continue

            track_html = track_res.text

            title_match = re.search(r'<title>([^<]+)</title>', track_html)
            if title_match:
                raw_title = title_match.group(1).strip()
                print(f'Raw title: {raw_title}')

                # Parse title and artist
                clean = raw_title.replace(' - Spotify', '').strip()
                if ' - ' in clean:
                    parts = clean.split(' - ', 1)
                    track_title = parts[0].strip()
                    track_artist = parts[1].strip()
                else:
                    track_title = clean.strip()
                    track_artist = 'Unknown Artist'

                candidates.append({
                    'title': track_title,
                    'artist': track_artist,
                    'url': f'https://open.spotify.com/track/{track_id}'
                })
                print(f'Added: {track_title} - {track_artist}')
        except Exception as e:
            print(f'Error: {e}')
            continue

    return candidates

if __name__ == '__main__':
    results = public_search_track('Creo', 'Callejeros')
    print(f'\nTotal results: {len(results)}')
    for r in results[:3]:
        print(f'  - {r["title"]} | {r["artist"]} | {r["url"]}')