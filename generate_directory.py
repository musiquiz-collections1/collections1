#!/usr/bin/env python3
"""
Directory tree generator for musiquiz-collections1 index.html
Generates an expandable/collapsible directory structure
"""

import os
import json
from pathlib import Path

def get_directory_structure(root_path, exclude_dirs=None):
    """Generate a nested dictionary structure of the directory tree"""
    if exclude_dirs is None:
        exclude_dirs = ['.git', '__pycache__', '.vscode']

    structure = {}

    for item in sorted(os.listdir(root_path)):
        if item in exclude_dirs:
            continue

        item_path = os.path.join(root_path, item)
        if os.path.isdir(item_path):
            # It's a directory
            structure[item] = get_directory_structure(item_path, exclude_dirs)
        else:
            # It's a file
            structure[item] = None

    return structure

def generate_html_tree(structure, base_path="", level=0):
    """Generate HTML for the directory tree with expand/collapse functionality"""
    html = ""
    indent = "  " * level

    for name, content in structure.items():
        if content is None:
            # It's a file
            file_path = f"{base_path}/{name}" if base_path else name
            html += f'{indent}├ <a href="{file_path}">{name}</a>\n'
        else:
            # It's a directory
            dir_id = f"dir_{base_path.replace('/', '_')}_{name}" if base_path else f"dir_{name}"
            dir_id = dir_id.replace(' ', '_').replace('-', '_')
            html += f'{indent}├ <span class="dir-toggle" onclick="toggleDirectory(\'{dir_id}\')">▶</span> <span class="dir-name">{name}/</span>\n'
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

    # Replace the directory section
    old_directory = '<div class="directory">\n\t\t├ <a href="data.json">data.json</a>\n\t</div>'
    new_directory = f'<div class="directory">\n{tree_html}\t</div>'

    updated_content = content.replace(old_directory, new_directory)

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