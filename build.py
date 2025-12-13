#!/usr/bin/env python3
"""
Directory tree generator for musiquiz-collections1 index.html
Generates an expandable/collapsible directory structure
"""

import os
import json
from pathlib import Path
import fnmatch

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

def get_directory_structure(root_path, ignore_patterns=None):
	"""Generate a nested dictionary structure of the directory tree"""
	if ignore_patterns is None:
		ignore_patterns = read_gitignore(root_path)

	structure = {}

	for item in sorted(os.listdir(root_path)):
		item_path = os.path.join(root_path, item)

		# Check if item should be ignored
		if should_ignore(item_path, ignore_patterns, root_path):
			continue

		if os.path.isdir(item_path):
			# It's a directory
			structure[item] = get_directory_structure(item_path, ignore_patterns)
		else:
			# It's a file
			structure[item] = None

	return structure

def generate_html_tree(structure, base_path="", level=0):
	"""Generate HTML for the directory tree with expand/collapse functionality"""
	html = ""
	indent = "  " * level if level > 0 else ""  # Only indent for subdirectories

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
			# It's a file - don't indent files inside directories since CSS handles indentation
			file_indent = "" if level > 0 else indent
			file_path = f"{base_path}/{name}" if base_path else name
			html += f'{file_indent}<a href="{file_path}">{name}</a>\n'
		else:
			# It's a directory
			dir_id = f"dir_{base_path.replace('/', '_')}_{name}" if base_path else f"dir_{name}"
			dir_id = dir_id.replace(' ', '_').replace('-', '_')
			html += f'{indent}<span class="dir-toggle" onclick="toggleDirectory(`{dir_id}`)">&#9656;</span><span class="dir-name" onclick="toggleDirectory(`{dir_id}`)"> {name}/</span><div id="{dir_id}" class="dir-content collapsed">'
			html += generate_html_tree(content, f"{base_path}/{name}" if base_path else name, level + 1)
			html += f'</div>\n'

	return html

def update_index_html():
	"""Update the index.html file with the current directory structure"""
	script_dir = Path(__file__).parent
	root_path = script_dir

	# Get directory structure
	structure = get_directory_structure(root_path)

	# Generate HTML tree
	tree_html = generate_html_tree(structure)

	index_path = script_dir / "index.html"

	# Read existing timestamp from current index.html if it exists
	timestamp = "TIMESTAMP_PLACEHOLDER"
	if index_path.exists():
		import re
		try:
			with open(index_path, 'r', encoding='utf-8') as f:
				content = f.read()
				# Extract timestamp from <p class="updated"> tag
				match = re.search(r'<p class="updated">(.*?)</p>', content)
				if match:
					timestamp = match.group(1)
		except:
			pass  # Fall back to placeholder if reading fails

	# Create the complete HTML content from scratch
	html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
	<meta charset="UTF-8">
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
	<link rel="icon" href="https://savocid.github.io/musiquiz/img/favicon2.png">
	<title>Musiquiz Collections</title>
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
		.headerElement {{
			--color1: gold;
			--color2: cyan;
			font-size: 4rem;
			text-shadow: 2px 2px 0px rgba(0,0,0,0.15);
			letter-spacing: 2px;
			font-weight: 900;
			font-family: 'Roboto', sans-serif;
			background: linear-gradient(90deg, var(--color1) 0%, var(--color1) 50%,var(--color2) 50%, var(--color2) 100%);
			-webkit-background-clip: text;
			-webkit-text-fill-color: transparent;
			background-clip: text;
		}}
		h2 {{
			font-size: 2rem;
			color: brown;
			text-shadow: 2px 2px 1px rgba(0,0,0,0.5);
			margin-bottom: 0.5rem;
		}}
		p {{
			font-size: 1.2rem;
			padding: 0;
			margin-bottom: 0.5rem;
		}}
		a {{
			color:cornflowerblue;
			text-decoration: none;
		}}
		a:hover,
		a:active {{
			color:lightblue;
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
			margin-left: 1rem;
		}}
		.dir-content.collapsed {{
			display: none;
		}}
		.dir-content.expanded {{
			display: block;
		}}
		#copyLink {{
			display:block;
			outline: none;
			background: darkgray;
			text-align:center;
			font-weight: bold;
			font-size: 1rem;
			color: rgba(0,0,0,0.5);
			margin: 0 0 0.5rem;
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
	</style>
</head>
<body>
	<a onclick="location.reload(true)" style="font-size: 1.5em; position: absolute; top: 1rem; left: 1rem; cursor: pointer;user-select: none;">Refresh</a>
	<span style="margin: 5rem 0 0;"><h1 class="headerElement"><a href="https://savocid.github.io/musiquiz">MusiQuiz</a></h1><h2>Collections</h1></span>
	<p class="updated">{timestamp}</p>
	<span id="copyLink" onclick="this.classList.add('anim');setTimeout(()=>this.classList.remove('anim'),500);selectText(this); navigator.clipboard.writeText(this.innerText);"></span>
	<div class="directory"><strong class="directory-title">Directory</strong><a class="expand-collapse-all" onclick="toggleAllDirectories()">Expand</a>{tree_html}\t</div>
	<script>
		document.getElementById("copyLink").innerText = (window.location.href).replace("index.html","");
		function selectText(element) {{
			const range = document.createRange();
			range.selectNodeContents(element);
			const selection = window.getSelection();
			selection.removeAllRanges();
			selection.addRange(range);
		}}
		function toggleDirectory(dirId) {{
			const element = document.getElementById(dirId);
			const toggle = element.previousElementSibling.previousElementSibling;

			if (element.classList.contains('collapsed')) {{
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
			
			// Get all directory content divs
			const dirContents = document.querySelectorAll('.dir-content');
			const dirToggles = document.querySelectorAll('.dir-toggle');
			
			dirContents.forEach((content, index) => {{
				const toggle = dirToggles[index];
				const dirId = content.id;
				
				if (isExpanding) {{
					// Expand all
					content.classList.remove('collapsed');
					content.classList.add('expanded');
					if (toggle) toggle.textContent = '\u25be';
					sessionStorage.setItem(dirId, 'expanded');
				}} else {{
					// Collapse all
					content.classList.remove('expanded');
					content.classList.add('collapsed');
					if (toggle) toggle.textContent = '\u25b8';
					sessionStorage.removeItem(dirId);
				}}
			}});
			
			// Update button text
			button.textContent = isExpanding ? 'Collapse' : 'Expand';
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
							element.classList.remove('collapsed');
							element.classList.add('expanded');
							const toggle = element.previousElementSibling.previousElementSibling;
							if (toggle) {{
								toggle.textContent = '\u25be';
							}}
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

	print(f"Directory structure updated in index.html at {timestamp}")

if __name__ == "__main__":
	update_index_html()