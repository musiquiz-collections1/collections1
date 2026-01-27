#!/usr/bin/env python3
"""
Directory tree generator for musiquiz-collections1 index.html
Generates an expandable/collapsible directory structure
"""

import os
import json
from pathlib import Path
import fnmatch

# Load AUDIO_BASE_URL from config.json
script_dir = Path(__file__).parent
config_path = script_dir / "config.json"
with open(config_path, 'r', encoding='utf-8') as f:
	config = json.load(f)
	AUDIO_BASE_URL = config['audioBaseUrl']

def read_gitignore(root_path):
	"""Read .gitignore file and return list of ignore patterns"""
	gitignore_path = os.path.join(root_path, '.gitignore')
	ignore_patterns = []

	# Add default patterns that should always be ignored
	default_ignores = ['.git', '__pycache__', '.vscode', '*.pyc', '.DS_Store', 'Thumbs.db']
	ignore_patterns.extend(default_ignores)

	if os.path.exists(gitignore_path):
		with open(gitignore_path, 'r', encoding='utf-8') as f:
			for line in f:
				line = line.strip()
				# Skip empty lines and comments
				if line and not line.startswith('#'):
					ignore_patterns.append(line)

	ignore_patterns.append("_headers")
	ignore_patterns.append(".htaccess")
	ignore_patterns.append(".gitignore")
	
	return ignore_patterns

def should_ignore(item_path, ignore_patterns, root_path):
	"""Check if an item should be ignored based on gitignore patterns"""
	# Get relative path from root
	rel_path = os.path.relpath(item_path, root_path)
	item_name = os.path.basename(rel_path)

	for pattern in ignore_patterns:
		# Remove trailing slash if present
		clean_pattern = pattern.rstrip('/')

		# Handle directory patterns (ending with /*)
		if clean_pattern.endswith('/*'):
			dir_name = clean_pattern[:-2]  # Remove /*
			if rel_path == dir_name or rel_path.startswith(dir_name + os.sep):
				return True
		# Handle exact matches
		elif rel_path == clean_pattern or item_name == clean_pattern:
			return True
		# Handle wildcard patterns
		elif fnmatch.fnmatch(rel_path, clean_pattern) or fnmatch.fnmatch(item_name, clean_pattern):
			return True

	return False

def get_audio_structure_from_json(root_path):
	"""Generate directory structure for audio files from songs.json"""
	audio_structure = {}
	songs_json_path = os.path.join(root_path, 'songs.json')
	
	try:
		with open(songs_json_path, 'r', encoding='utf-8') as f:
			songs = json.load(f)
		
		# Build directory tree from audioFile paths
		for song_data in songs.values():
			audio_file = song_data.get('audioFile', '')
			if not audio_file:
				continue
			
			# Split path into parts (e.g., "billboard/1960-1969/Song.mp3")
			parts = audio_file.split('/')
			
			# Navigate/create nested structure
			current = audio_structure
			for i, part in enumerate(parts):
				if i == len(parts) - 1:
					# Last part is the file
					current[part] = None
				else:
					# It's a directory
					if part not in current:
						current[part] = {}
					current = current[part]
	except Exception as e:
		print(f"Error reading songs.json: {e}")
		return {}
	
	return audio_structure

def get_directory_structure(root_path, ignore_patterns=None):
	"""Generate a nested dictionary structure of the directory tree"""
	if ignore_patterns is None:
		ignore_patterns = read_gitignore(root_path)

	structure = {}

	for item in sorted(os.listdir(root_path)):
		item_path = os.path.join(root_path, item)

		# Check if item should be ignored
		if should_ignore(item_path, ignore_patterns, root_path):
			# Special case: if ignoring audio directory, build structure from songs.json
			if item == 'audio':
				audio_structure = get_audio_structure_from_json(root_path)
				if audio_structure:
					structure['audio'] = audio_structure
			continue

		if os.path.isdir(item_path):
			# It's a directory
			structure[item] = get_directory_structure(item_path, ignore_patterns)
		else:
			# It's a file
			structure[item] = None

	return structure

def generate_html_tree(structure, base_path="", level=0, is_audio_dir=False, max_preload_level=2):
	"""Generate HTML for the directory tree with expand/collapse functionality"""
	html = ""

	# Sort items: directories first, then files (by extension then filename)
	def sort_key(item):
		name, content = item
		if content is None:  # It's a file
			# Split filename and extension
			name_part, ext_part = os.path.splitext(name.lower())
			return (1, ext_part, name_part)  # Files come after directories (1), sorted by extension then filename
		else:  # It's a directory
			return (0, "", name.lower())  # Directories come first (0)

	sorted_items = sorted(structure.items(), key=sort_key)

	for name, content in sorted_items:
		if content is None:
			# It's a file
			file_path = f"{base_path}/{name}" if base_path else name
			
			# Use Cloudflare Worker URL for audio files
			if is_audio_dir or base_path.startswith('audio'):
				href = f"{AUDIO_BASE_URL}/{file_path}"
			else:
				href = file_path
			
			html += f'<div class="tree-item file" data-level="{level}"><a href="{href}">{name}</a></div>'
		else:
			# It's a directory
			dir_id = f"dir_{base_path.replace('/', '_')}_{name}" if base_path else f"dir_{name}"
			dir_id = dir_id.replace(' ', '_').replace('-', '_')
			
			# Check if we're in audio directory
			new_is_audio = is_audio_dir or (base_path == '' and name == 'audio') or base_path.startswith('audio')
			
			html += f'<div class="tree-item dir" data-level="{level}"><span class="dir-toggle" onclick="toggleDirectory(`{dir_id}`)">&#9656;</span><span class="dir-name" onclick="toggleDirectory(`{dir_id}`)"> {name}/</span></div><div id="{dir_id}" class="dir-content collapsed">'
			
			# Only pre-generate children up to max_preload_level
			if level < max_preload_level:
				html += generate_html_tree(content, f"{base_path}/{name}" if base_path else name, level + 1, new_is_audio, max_preload_level)
			else:
				# Add lazy load marker for deeper levels
				path = f"{base_path}/{name}" if base_path else name
				html += f'<div class="lazy-placeholder" data-path="{path}" data-level="{level + 1}" data-is-audio="{str(new_is_audio).lower()}"></div>'
			
			html += '</div>'

	return html

def update_index_html():
	"""Update the index.html file with the current directory structure"""
	script_dir = Path(__file__).parent
	root_path = script_dir

	# Get directory structure
	structure = get_directory_structure(root_path)

	# Generate HTML tree (pre-render everything - no lazy loading)
	tree_html = generate_html_tree(structure, max_preload_level=999)
	
	# Convert structure to JSON for lazy loading
	structure_json = json.dumps(structure, indent=2)

	index_path = script_dir / "index.html"

	version = "PLACEHOLDER"
	if index_path.exists():
		import re
		try:
			with open(index_path, 'r', encoding='utf-8') as f:
				content = f.read()
				match = re.search(r'<p id="version">(.*?)</p>', content)
				if match:
					version = match.group(1)
		except:
			pass  # Fall back to placeholder if reading fails

	# Create the complete HTML content from scratch
	html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
	<meta charset="UTF-8">
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
	<link rel="icon" href="https://savocid.github.io/musiquiz/img/favicon2.png">
	<title>Collections</title>
	<link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;700;900&display=swap" rel="stylesheet">
	<style>
		* {{
			margin: 0;
			padding: 0;
		}}
		body {{
			font-family: Arial, sans-serif;
			background: linear-gradient(to right, #1a1a1a, #1e1e1e, #1e2e2e);
			color: #fff;
			text-align: center;
			margin: 0;
			padding: 0;
			min-height: 100vh;
			display: flex;
			flex-direction: column;
			justify-content: flex-start;
			align-items: center;
		}}
		body > * {{
			padding: 0.5rem;
		}}
		a {{
			color:cornflowerblue;
			text-decoration: none;
		}}
		a:hover,
		a:active {{
			color:lightblue;
		}}
		.headerElement {{
			--color1: gold;
			--color2: cyan;
			font-size: 4rem;
			text-shadow: 2px 2px 0px rgba(0,0,0,0.15);
			letter-spacing: 2px;
			font-weight: 900;
			font-family: 'Roboto', sans-serif;
			background: linear-gradient(90deg, var(--color1) 0%, var(--color1) 50.2%,var(--color2) 50.2%, var(--color2) 100%);
			-webkit-background-clip: text;
			-webkit-text-fill-color: transparent;
			background-clip: text;
		}}
		h2 {{
			margin-bottom: 0.5rem;
		}}
		h2 > * {{
			font-size: 2rem;
			color: brown;
			text-shadow: 2px 2px 1px rgba(0,0,0,0.5);
		}}
		h2 > a:hover,
		h2 > a:active  {{
			color: indianred;
		}}
		p {{
			font-size: 1.2rem;
			padding: 0;
			margin-bottom: 0.5rem;
		}}
	
		.directory {{
			font-family: 'Courier New', monospace;
			text-align: left;
			background: rgba(0, 0, 0, 0.3);
			padding: 0 1rem 1rem;
			border-radius: 8px;
			max-width: 600px;
			margin: 1rem auto;
			line-height: 1.4;
			white-space: pre-wrap;
		}}
		.directory-title {{
			display: block;
			padding: 1rem 0 0.5rem;
			text-align: center;
			font-size: 1.5rem;
			font-weight: bold;
			border-bottom: 2px solid rgba(255, 255, 255, 0.1);
			text-transform: uppercase;
			font-family: 'Roboto', sans-serif;
		}}
		.expand-collapse-all {{
			text-align: center;
			display: block;
			padding: 1rem 0 0.5rem;
			cursor: pointer;
			font-size: 1.1rem;
			transition: background-color 0.2s;
			font-weight:bold;
			text-transform: uppercase;
			font-family: Arial, sans-serif;
		}}
		.dir-toggle {{
			cursor: pointer;
			color: #1db954;
			font-weight: bold;
			padding-right: 0.2rem;
			font-size: 1.2rem;
    		line-height: normal;
			user-select: none;
		}}
		.dir-toggle:hover {{
			color: #1ed760;
		}}
		.dir-name {{
			color: #1db954;
			font-weight: bold;
			cursor: pointer;
		}}
		.dir-name:hover {{
			color: #1ed760;
		}}
		.dir-content {{
			margin-left: 0;
			contain: layout style paint;
		}}
		.tree-item {{
			display: block;
			margin-left: calc(attr(data-level number, 0) * 1rem);
			contain: layout;
		}}
		.dir-content.collapsed {{
			content-visibility: hidden;
			height: 0;
			overflow: hidden;
		}}
		.dir-content.expanded {{
			content-visibility: auto;
			height: auto;
		}}
		#copyLink {{
			display:block;
			outline: none;
			background: darkgray;
			text-align:center;
			font-weight: bold;
			font-size: 1rem;
			color: rgba(0,0,0,0.5);
			margin: 0 1rem 0.5rem;
			border: 4px inset hsl(0,0%,55%);
			cursor: text;
		}}
		#copyLink::selection {{
			background: rgba(0,0,0,0.25);
		}}
	
		#copyLink.anim {{
			animation: flash 0.5s ease;
		}}
		@keyframes flash {{
			0%, 50% {{ filter: brightness(1.2); }}
			100% {{ filter: brightness(1); }}
		}}
		#version {{
			position:absolute;
			top: 1rem;
			right: 1rem;
			font-size: 1rem;
    		font-weight: bold;
			user-select: all;
    		cursor: default;
			background: var(--color);
			padding: 0.5rem;
			border-radius: 1px;
			outline: solid;
			outline-width: 2px;
			outline-color: var(--color);
			outline-offset: 3px;
			filter: contrast(0.5);
		}}
		#version > span {{
			color: var(--color);
			filter: brightness(10) invert(1);
			padding: 0 1rem;
		}}
		
		@media (max-width: 600px) {{
			.headerElement {{
				font-size: 2rem;
			}}
			h2 {{
				font-size: 1rem;
			}}
			#version {{
				font-size: 0.75rem;
			}}
		}}
	</style>
</head>
<body>
	<p id="version">{version}</p>
	<span style="margin: 5rem 0 0;"><h1 class="headerElement"><a href="https://savocid.github.io/musiquiz">MusiQuiz</a></h1><h2><a href="./index.html" style=>Collections</a></h1></span>
	<span id="copyLink" onclick="this.classList.add('anim');setTimeout(()=>this.classList.remove('anim'),500);selectText(this); navigator.clipboard.writeText(this.innerText);"></span>
	<div class="directory"><strong class="directory-title">Directory</strong><a class="expand-collapse-all" onclick="toggleAllDirectories()">Expand</a>{tree_html}\t</div>
	<script>
		// Directory structure for lazy loading
		const dirStructure = {structure_json};
		const AUDIO_BASE_URL = "{AUDIO_BASE_URL}";
		
		// Clear any cached lazy-loaded content (version bump to invalidate old cache)
		const STRUCTURE_VERSION = '3';
		if (sessionStorage.getItem('structure_version') !== STRUCTURE_VERSION) {{
			// Clear all directory-related sessionStorage
			Object.keys(sessionStorage).filter(key => key.startsWith('dir_')).forEach(key => {{
				sessionStorage.removeItem(key);
			}});
			sessionStorage.setItem('structure_version', STRUCTURE_VERSION);
		}}
		
		// Force clear dir_audio specifically (may have corrupted content from old lazy loading bug)
		sessionStorage.removeItem('dir_audio');
		
		document.getElementById("copyLink").innerText = (window.location.href).replace("index.html","");
		
		function selectText(element) {{
			const range = document.createRange();
			range.selectNodeContents(element);
			const selection = window.getSelection();
			selection.removeAllRanges();
			selection.addRange(range);
		}}
		
		function generateTreeHtml(structure, basePath, level, isAudioDir) {{
			let html = '';
			
			// Sort items: directories first, then files
			const items = Object.entries(structure).sort((a, b) => {{
				const [nameA, contentA] = a;
				const [nameB, contentB] = b;
				
				if (contentA === null && contentB !== null) return 1;
				if (contentA !== null && contentB === null) return -1;
				
				return nameA.toLowerCase().localeCompare(nameB.toLowerCase());
			}});
			
			for (const [name, content] of items) {{
				if (content === null) {{
					// It's a file
					const filePath = basePath ? `${{basePath}}/${{name}}` : name;
					const href = (isAudioDir || basePath.startsWith('audio')) 
						? `${{AUDIO_BASE_URL}}/${{filePath}}` 
						: filePath;
					html += `<div class="tree-item file" data-level="${{level}}"><a href="${{href}}">${{name}}</a></div>`;
				}} else {{
					// It's a directory
					const dirPath = basePath ? `${{basePath}}/${{name}}` : name;
					const dirId = `dir_${{dirPath.replace(/\\//g, '_').replace(/[\\s-]/g, '_')}}`;
					const newIsAudio = isAudioDir || (basePath === '' && name === 'audio') || basePath.startsWith('audio');
					
					html += `<div class="tree-item dir" data-level="${{level}}"><span class="dir-toggle" onclick="toggleDirectory('${{dirId}}')">&#9656;</span><span class="dir-name" onclick="toggleDirectory('${{dirId}}')"> ${{name}}/</span></div><div id="${{dirId}}" class="dir-content collapsed">`;
					html += generateTreeHtml(content, dirPath, level + 1, newIsAudio);
					html += '</div>';
				}}
			}}
			
			return html;
		}}
		
		function toggleDirectory(dirId) {{
			const element = document.getElementById(dirId);
			if (!element) {{
				console.error('Directory element not found:', dirId);
				return;
			}}
			
			const toggle = element.previousElementSibling?.querySelector('.dir-toggle');
			if (!toggle) {{
				console.error('Toggle element not found for:', dirId);
				return;
			}}

			if (element.classList.contains('collapsed')) {{
				// Expanding - check if lazy loading needed
				const placeholder = element.querySelector('.lazy-placeholder');
				if (placeholder) {{
					const path = placeholder.getAttribute('data-path');
					const level = parseInt(placeholder.getAttribute('data-level'));
					const isAudio = placeholder.getAttribute('data-is-audio') === 'true';
					
					// Navigate to the structure at this path
					const parts = path.split('/').filter(p => p);
					let current = dirStructure;
					
					for (const part of parts) {{
						if (!current || typeof current !== 'object') {{
							console.error('Invalid structure navigation at:', part, 'in path:', path);
							return;
						}}
						current = current[part];
						if (!current) {{
							console.error('Path not found:', part, 'in path:', path);
							return;
						}}
					}}
					
					// Generate HTML for this directory
					const html = generateTreeHtml(current, path, level, isAudio);
					element.innerHTML = html;
				}}
				
				element.classList.remove('collapsed');
				element.classList.add('expanded');
				toggle.textContent = '\u25be';
				sessionStorage.setItem(dirId, 'expanded');
			}} else {{
				element.classList.remove('expanded');
				element.classList.add('collapsed');
				toggle.textContent = '\u25b8';
				sessionStorage.removeItem(dirId);
			}}
		}}

		function toggleAllDirectories() {{
			const button = document.querySelector('.expand-collapse-all');
			const isExpanding = button.textContent === 'Expand';
			
			if (isExpanding) {{
				// Expand all directories
				const allDirs = Array.from(document.querySelectorAll('.dir-content'));
				
				allDirs.forEach(content => {{
					if (content.classList.contains('collapsed')) {{
						toggleDirectory(content.id);
					}}
				}});
				
				button.textContent = 'Collapse';
			}} else {{
				// Collapse all directories
				const dirContents = document.querySelectorAll('.dir-content');
				const dirToggles = document.querySelectorAll('.dir-toggle');
				
				dirContents.forEach((content, index) => {{
					const toggle = dirToggles[index];
					const dirId = content.id;
					
					content.classList.remove('expanded');
					content.classList.add('collapsed');
					if (toggle) toggle.textContent = '\u25b8';
					sessionStorage.removeItem(dirId);
				}});
				
				button.textContent = 'Expand';
			}}
		}}

		// Handle scroll position preservation for browser back/forward navigation
		window.addEventListener('pageshow', function(event) {{
			// Update button text based on current state (no directories expanded initially)
			updateExpandAllButton();
			
			// If page was loaded from cache (back/forward navigation), restore expanded state
			if (event.persisted) {{
				// Wait for browser to finish its scroll restoration, then restore our expanded state
				setTimeout(() => {{
					// Get expanded directories from sessionStorage
					const expandedDirs = Object.keys(sessionStorage).filter(key => key.startsWith('dir_'));

					// Restore expanded state
					expandedDirs.forEach(dirId => {{
						const element = document.getElementById(dirId);
						if (element && element.classList.contains('collapsed')) {{
							toggleDirectory(dirId);
						}}
					}});

					// Update expand/collapse all button
					updateExpandAllButton();
				}}, 50);
			}}
		}});

		function updateExpandAllButton() {{
			const button = document.querySelector('.expand-collapse-all');
			const expandedDirs = document.querySelectorAll('.dir-content.expanded');
			const totalDirs = document.querySelectorAll('.dir-content').length;
			
			if (expandedDirs.length === totalDirs) {{
				button.textContent = 'Collapse';
			}} else {{
				button.textContent = 'Expand';
			}}
		}}

	</script>
</body>
</html>'''

	# Write the new content
	with open(index_path, 'w', encoding='utf-8') as f:
		f.write(html_content)

if __name__ == "__main__":
	update_index_html()