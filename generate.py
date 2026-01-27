import os
import json
import re
from mutagen import File

AUDIO_ROOT = "."
SONGS_PATH = "songs.json"

def parse_comment_metadata(comment_text):
	"""
	Extract structured data from comment field.
	Looks for patterns like {{key: value}} in the comment.
	Returns a dict with extracted fields.
	"""
	if not comment_text:
		return {}
	
	# Find all {{...}} patterns in the comment
	pattern = r'\{\{([^}]+)\}\}'
	matches = re.findall(pattern, comment_text)
	
	extracted = {}
	for match in matches:
		# Find all key: value pairs in the match
		# Use a more robust pattern that captures everything after the colon
		remaining = match
		while remaining.strip():
			# Find the key
			key_match = re.match(r'\s*(\w+)\s*:\s*', remaining)
			if not key_match:
				break
			
			key = key_match.group(1)
			remaining = remaining[key_match.end():]
			
			# Find the value - it could be an array or a simple value
			# For arrays, we need to find the matching closing bracket
			if remaining.startswith('['):
				# Count brackets to find the end of the array
				bracket_count = 0
				end_pos = 0
				for i, char in enumerate(remaining):
					if char == '[':
						bracket_count += 1
					elif char == ']':
						bracket_count -= 1
						if bracket_count == 0:
							end_pos = i + 1
							break
				
				value_str = remaining[:end_pos]
				remaining = remaining[end_pos:].lstrip(', ')
				
				# Parse the array value using JSON
				try:
					import json
					value = json.loads(value_str)
				except:
					# Fallback to manual parsing if JSON fails
					value = value_str
			else:
				# Simple value - find the next comma or end
				next_comma = remaining.find(',')
				if next_comma > 0:
					value_str = remaining[:next_comma].strip()
					remaining = remaining[next_comma + 1:]
				else:
					value_str = remaining.strip()
					remaining = ''
				
				# Remove quotes if present
				if value_str.startswith('"') and value_str.endswith('"'):
					value = value_str[1:-1]
				else:
					value = value_str
			
			extracted[key] = value
	
	return extracted

def get_metadata(filepath):
	# Use easy=True for most tags
	audio = File(filepath, easy=True)
	if not audio:
		return {"title": None, "year": None, "artists": [], "comment_data": {}}
	
	title = audio.get("title", [None])[0]
	year_raw = audio.get("date", [None])[0] or audio.get("year", [None])[0]
	year = None
	if year_raw:
		if len(year_raw) >= 4 and year_raw[:4].isdigit():
			year = int(year_raw[:4])
	artists = audio.get("artist", [""])
	if artists:
		artists = [a.strip() for a in artists[0].replace(";", ",").split(",") if a.strip()]
	
	# Extract comment metadata - need to load again without easy=True to get COMM frames
	from mutagen.mp3 import MP3
	try:
		mp3 = MP3(filepath)
		comment = None
		# Look for COMM frames
		for key in mp3.tags.keys() if mp3.tags else []:
			if 'COMM' in key:
				frame_text = str(mp3.tags[key])
				# Look for our structured data marker {{
				if '{{' in frame_text:
					comment = frame_text
					break
	except Exception:
		comment = None
	
	comment_data = parse_comment_metadata(comment)
	
	return {"title": title, "year": year, "artists": artists, "comment_data": comment_data}

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
	ORDER = ['title', 'artists', 'sources', 'platforms', 'year', 'audioFile', 'startTime', 'endTime', 'processed',]

	def default_for(key, original):
		if key == 'title':
			return original.get('title', [True, 'Unknown Title'])
		if key == 'artists':
			return original.get('artists', [])
		if key == 'audioFile':
			return original.get('audioFile', None)
		if key == 'startTime':
			return original.get('startTime', None)
		if key == 'endTime':
			return original.get('endTime', None)
		if key == 'processed':
			# preserve existing or default to False
			return original.get('processed', False)
		if key == 'year':
			return original.get('year', None)
		if key == 'platforms':
			return original.get('platforms', None)
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

				# Always get metadata
				metadata = get_metadata(filepath)

				# Merge into existing entry without overwriting existing values
				existing = songs.get(key_path, {})
				# Log new files for visibility
				if not existing:
					print(f"Processing new file: {relative_path}")

				# Start from a copy of existing to preserve unknown extra keys
				song = dict(existing)

				# Title: priority is comment_data > existing > metadata > filename
				if "title" in metadata["comment_data"]:
					# Use title from comment metadata (already an array)
					song["title"] = [True] + metadata["comment_data"]["title"]
				elif not song.get("title"):
					filename_without_ext = os.path.splitext(file)[0]
					song["title"] = [True, metadata["title"] or filename_without_ext]

				# Artists: priority is comment_data > existing > metadata > empty list
				if "artists" in metadata["comment_data"]:
					# Comment data is already in the format we need - array of arrays like [["Artist1", "Artist2"]]
					song["artists"] = [[True] + artist_list for artist_list in metadata["comment_data"]["artists"]]
				elif not song.get("artists"):
					song["artists"] = [[True, artist] for artist in metadata["artists"]] if metadata["artists"] else []

				# Sources: priority is comment_data > existing > None
				if "sources" in metadata["comment_data"]:
					# Comment data is already in the format we need - array of arrays like [["Source1", "Source2"]]
					song["sources"] = [[True] + source_list for source_list in metadata["comment_data"]["sources"]]
				else:
					song["sources"] = song.get("sources", None)

				# audioFile: set if missing
				if not song.get("audioFile"):
					song["audioFile"] = relative_path

				# startTime / endTime / processed: preserve existing or set sensible defaults
				song["startTime"] = song.get("startTime", None)
				song["endTime"] = song.get("endTime", None)
				song["processed"] = song.get("processed", False)

				# Year: priority is comment_data > existing > metadata > None
				if "year" in metadata["comment_data"]:
					song["year"] = int(metadata["comment_data"]["year"])
				elif song.get("year") is None:
					song["year"] = metadata["year"]

				# Platforms: priority order is comment_data > existing > None
				# Comment metadata has highest priority
				if "platforms" in metadata["comment_data"]:
					song["platforms"] = metadata["comment_data"]["platforms"]
				elif song.get("platforms") is None:
					song["platforms"] = None

				# Store the merged entry
				songs[key_path] = song

	songs = canonicalize_songs(songs)

	save_songs(songs)
	
	print(f"Total songs: {len(songs)}")



if __name__ == "__main__":
	scan_audio_files()