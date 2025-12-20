import os
import json
from mutagen import File

AUDIO_ROOT = "."
SONGS_PATH = "songs.json"

def get_metadata(filepath):
	audio = File(filepath, easy=True)
	if not audio:
		return {"title": None, "year": None, "artists": []}
	title = audio.get("title", [None])[0]
	year_raw = audio.get("date", [None])[0] or audio.get("year", [None])[0]
	year = None
	if year_raw:
		if len(year_raw) >= 4 and year_raw[:4].isdigit():
			year = int(year_raw[:4])
	artists = audio.get("artist", [""])
	if artists:
		artists = [a.strip() for a in artists[0].replace(";", ",").split(",") if a.strip()]
	return {"title": title, "year": year, "artists": artists}

def load_songs():
	if os.path.exists(SONGS_PATH):
		with open(SONGS_PATH, "r", encoding="utf-8") as f:
			return json.load(f)
	return {}

def save_songs(songs):
	with open(SONGS_PATH, "w", encoding="utf-8") as f:
		json.dump(songs, f, indent=2, ensure_ascii=False)

def canonicalize_songs(songs):
	"""
	Reorder keys for each song dict into a canonical order, preserving existing
	values and never overwriting existing data. Missing keys get sensible defaults.
	"""
	ORDER = ['title', 'sources', 'year', 'audioFile', 'level', 'startTime', 'endTime', 'processed',]

	def default_for(key, original):
		if key == 'title':
			return original.get('title', [True, 'Unknown Title'])
		if key == 'sources':
			return original.get('sources', [[True, 'Unknown Artist']])
		if key == 'audioFile':
			return original.get('audioFile', None)
		if key == 'startTime':
			return original.get('startTime', None)
		if key == 'endTime':
			return original.get('endTime', None)
		if key == 'processed':
			# preserve existing or default to False
			return original.get('processed', False)
		if key == 'level':
			return original.get('level', None)
		if key == 'year':
			return original.get('year', None)
		return original.get(key, None)

	new_songs = {}
	for song_key, song in songs.items():
		# preserve original order for extra keys
		other_keys = [k for k in song.keys() if k not in ORDER]

		ordered = {}
		# Add canonical keys in desired order (only add with existing or sensible default)
		for k in ORDER:
			if k in song:
				ordered[k] = song[k]
			else:
				# Only add default if we have something sensible (keeps objects consistent)
				val = default_for(k, song)
				# Add key even if None to ensure consistent ordering (optional)
				ordered[k] = val

		# Append any other keys that existed previously (do not overwrite)
		for k in other_keys:
			ordered[k] = song[k]

		new_songs[song_key] = ordered

	return new_songs

def scan_audio_files():
	songs = load_songs()
	existing_files = set(songs.keys())

	for root, dirs, files in os.walk(AUDIO_ROOT):
		for file in files:
			if file.lower().endswith(('.mp3', '.flac', '.m4a', '.ogg', '.wav')):
				filepath = os.path.join(root, file)
				relative_path = os.path.relpath(filepath, AUDIO_ROOT).replace("\\", "/")
				# Remove file extension from key to match existing format
				key_path = os.path.splitext(relative_path)[0]

				if key_path not in existing_files:
					print(f"Processing new file: {relative_path}")
					metadata = get_metadata(filepath)

					# Create song entry
					song = {
						"title": [True, metadata["title"] or "Unknown Title"],
						"sources": [[True, artist] for artist in metadata["artists"]] if metadata["artists"] else [[True, "Unknown Artist"]],
						"audioFile": relative_path,
						"startTime": None,
						"endTime": None,
						"level": None,
						"year": metadata["year"],
						"processed": False,
					}

					songs[key_path] = song

	songs = canonicalize_songs(songs)

	save_songs(songs)
	
	print(f"Total songs: {len(songs)}")



if __name__ == "__main__":
	scan_audio_files()