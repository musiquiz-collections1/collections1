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
    indent = "  " * level

    # Sort items: directories first, then files
    sorted_items = sorted(structure.items(), key=lambda x: (x[1] is None, x[0].lower()))

    for name, content in sorted_items:
        if content is None:
            # It's a file
            file_path = f"{base_path}/{name}" if base_path else name
            html += f'{indent}├ <a href="{file_path}">{name}</a>\n'
        else:
            # It's a directory
            dir_id = f"dir_{base_path.replace('/', '_')}_{name}" if base_path else f"dir_{name}"
            dir_id = dir_id.replace(' ', '_').replace('-', '_')
            html += f'{indent}├ <span class="dir-toggle" onclick="toggleDirectory(\'{dir_id}\')">▶</span> <span class="dir-name" onclick="toggleDirectory(\'{dir_id}\')">{name}/</span>\n'
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

    # Read current index.html
    index_path = script_dir / "index.html"
    with open(index_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find and replace the directory section using a simple approach
    # Look for the directory div and replace everything until the next top-level </div>
    import re

    # Find the directory div
    dir_start = content.find('\t<div class="directory">')
    if dir_start == -1:
        print("Warning: Could not find directory section in HTML")
        updated_content = content
    else:
        # Find the end of the directory div (the matching closing div at the same level)
        # We'll use a simple approach: find the closing div that comes after the directory content
        dir_content_start = dir_start + len('\t<div class="directory">')

        # Find all div tags after the directory start
        remaining_content = content[dir_content_start:]
        div_count = 0
        end_pos = 0

        i = 0
        while i < len(remaining_content):
            if remaining_content[i:i+5] == '<div':
                div_count += 1
                i += 5
            elif remaining_content[i:i+6] == '</div>':
                div_count -= 1
                if div_count < 0:  # This is our matching closing div
                    end_pos = dir_content_start + i + 6
                    break
                i += 6
            else:
                i += 1

        if end_pos > 0:
            # Replace the content between the div tags
            updated_content = content[:dir_content_start] + '\n' + tree_html + '\n' + content[end_pos:]
        else:
            print("Warning: Could not find matching closing div for directory section")
            updated_content = content

    # Add JavaScript for expand/collapse functionality if not already present
    if 'function toggleDirectory' not in updated_content:
        js_script = '''
    <script>
        function toggleDirectory(dirId) {
            const element = document.getElementById(dirId);
            const toggle = element.previousElementSibling.previousElementSibling;

            if (element.classList.contains('collapsed')) {
                element.classList.remove('collapsed');
                element.classList.add('expanded');
                toggle.textContent = '▼';
            } else {
                element.classList.remove('expanded');
                element.classList.add('collapsed');
                toggle.textContent = '▶';
            }
        }
    </script>
'''
        # Insert before closing body tag
        updated_content = updated_content.replace('</body>', js_script + '</body>')

    # Write updated content
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)

    print("Directory structure updated in index.html")

if __name__ == "__main__":
    update_index_html()