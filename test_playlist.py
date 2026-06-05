import os
os.environ['SPOTIFY_CLIENT_ID'] = 'b6cf76b814484b5a813892591e3d7fc6'
os.environ['SPOTIFY_CLIENT_SECRET'] = '7886b8d639614563af112ec344e55222'
import sys
sys.path.insert(0, '.')
from services.spotify_service import SpotifyService

svc = SpotifyService()
print('Configured:', svc.is_configured())

playlist_id = '3fcy7HQFovLuUXGE88T7kx'
tracks = svc.get_playlist_tracks(playlist_id)
print('Tracks returned:', len(tracks))

if tracks:
    for t in tracks[:3]:
        print(f'  - {t["title"]} by {t["artist"]}')
else:
    print("No tracks found!")