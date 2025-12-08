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
			# It's a file
			file_path = f"{base_path}/{name}" if base_path else name
			html += f'{indent}<a href="{file_path}">{name}</a>\n'
		else:
			# It's a directory
			dir_id = f"dir_{base_path.replace('/', '_')}_{name}" if base_path else f"dir_{name}"
			dir_id = dir_id.replace(' ', '_').replace('-', '_')
			html += f'{indent}<span class="dir-toggle" onclick="toggleDirectory(\'{dir_id}\')">▶</span> <span class="dir-name" onclick="toggleDirectory(\'{dir_id}\')">{name}/</span>\n'
			html += f'{indent}  <div id="{dir_id}" class="dir-content collapsed">\n'
			html += generate_html_tree(content, f"{base_path}/{name}" if base_path else name, level + 1)
			html += f'{indent}  </div>\n'

	return html

def update_index_html():
	"""Update the index.html file with the current directory structure"""
	script_dir = Path(__file__).parent
	root_path = script_dir

	# Get directory structure
	structure = get_directory_structure(root_path)

	# Generate HTML tree
	tree_html = generate_html_tree(structure)

	# Read current index.html to preserve the timestamp
	index_path = script_dir / "index.html"
	from datetime import datetime
	timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Current timestamp

	# Create the complete HTML content from scratch
	html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
	<meta charset="UTF-8">
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
	<link rel="icon" href="https://savocid.github.io/musiquiz/img/favicon2.png">
	<title>Musiquiz Collections</title>
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
			justify-content: center;
			align-items: center;
		}}
		body > * {{
			padding: 0.5rem;
		}}
		h1 {{
			font-size: 3rem;
			color: #1db954;
		}}
		p {{
			font-size: 1.2rem;
			padding: 0;
			margin-bottom: 0.5rem;
		}}
		a {{
			color:cornflowerblue;
			text-decoration: none;
			padding-bottom: 0rem;
		}}
		a:hover,
		a:active {{
			color:lightblue;
		}}
		.directory {{
			font-family: 'Courier New', monospace;
			text-align: left;
			background: rgba(0, 0, 0, 0.3);
			padding: 1rem;
			border-radius: 8px;
			max-width: 600px;
			margin: 1rem auto;
			line-height: 1.4;
			white-space: pre-wrap;
		}}
		.expand-collapse-all {{
			display: block;
			margin: 0.5rem auto 1rem auto;
			padding: 0.5rem 1rem;
			background: #1db954;
			color: white;
			border: none;
			border-radius: 4px;
			cursor: pointer;
			font-size: 0.9rem;
			transition: background-color 0.2s;
		}}
		.expand-collapse-all:hover {{
			background: #1ed760;
		}}
		.dir-toggle {{
			cursor: pointer;
			color: #1db954;
			font-weight: bold;
			margin-right: 0.2rem;
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
	</style>
</head>
<body>
	<h1>Musiquiz Collections</h1>
	<p class="updated">{timestamp}</p>
	<a href="" style="margin-top: 0.5rem; font-size: 1.5em;">Refresh</a>
	<div class="directory"><button class="expand-collapse-all" onclick="toggleAllDirectories()">Expand All</button>{tree_html}\t</div>
	<script>
		function toggleDirectory(dirId) {{
			const element = document.getElementById(dirId);
			const toggle = element.previousElementSibling.previousElementSibling;

			if (element.classList.contains('collapsed')) {{
				element.classList.remove('collapsed');
				element.classList.add('expanded');
				toggle.textContent = '▼';
				localStorage.setItem(dirId, 'expanded');
			}} else {{
				element.classList.remove('expanded');
				element.classList.add('collapsed');
				toggle.textContent = '▶';
				localStorage.removeItem(dirId);
			}}
		}}

		function toggleAllDirectories() {{
			const button = document.querySelector('.expand-collapse-all');
			const isExpanding = button.textContent === 'Expand All';
			
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
					if (toggle) toggle.textContent = '▼';
					localStorage.setItem(dirId, 'expanded');
				}} else {{
					// Collapse all
					content.classList.remove('expanded');
					content.classList.add('collapsed');
					if (toggle) toggle.textContent = '▶';
					localStorage.removeItem(dirId);
				}}
			}});
			
			// Update button text
			button.textContent = isExpanding ? 'Collapse All' : 'Expand All';
		}}

		// Handle scroll position preservation for browser back/forward navigation
		window.addEventListener('pageshow', function(event) {{
			// Update button text based on current state (no directories expanded initially)
			updateExpandAllButton();
			
			// If page was loaded from cache (back/forward navigation), restore expanded state
			if (event.persisted) {{
				// Wait for browser to finish its scroll restoration, then restore our expanded state
				setTimeout(() => {{
					// Get expanded directories from localStorage
					const expandedDirs = Object.keys(localStorage).filter(key => key.startsWith('dir_'));

					// Restore expanded state
					expandedDirs.forEach(dirId => {{
						const element = document.getElementById(dirId);
						if (element && element.classList.contains('collapsed')) {{
							element.classList.remove('collapsed');
							element.classList.add('expanded');
							const toggle = element.previousElementSibling.previousElementSibling;
							if (toggle) {{
								toggle.textContent = '▼';
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
				button.textContent = 'Collapse All';
			}} else {{
				button.textContent = 'Expand All';
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