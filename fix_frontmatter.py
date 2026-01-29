#!/usr/bin/env python3
"""Fix YAML frontmatter issues in blog posts"""
import os
import re
from pathlib import Path

def fix_frontmatter(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract frontmatter
    match = re.match(r'^---\n(.*?)\n---\n(.*)$', content, re.DOTALL)
    if not match:
        return False

    frontmatter, body = match.groups()

    # Parse and fix frontmatter lines
    fixed_lines = []
    for line in frontmatter.split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            value = value.strip()

            # For title and description, handle quotes properly
            if key.strip() in ['title', 'description']:
                # Remove existing quotes
                value = value.strip('"').strip("'")
                # Replace Chinese quotes with regular text or escape them
                value = value.replace('"', '').replace('"', '')
                value = value.replace(''', '').replace(''', '')
                # Truncate long descriptions
                if key.strip() == 'description' and len(value) > 120:
                    value = value[:120] + '...'
                # Re-quote with proper escaping
                value = f'"{value}"'
                fixed_lines.append(f'{key}: {value}')
            else:
                fixed_lines.append(line)
        else:
            fixed_lines.append(line)

    new_content = f"---\n{chr(10).join(fixed_lines)}\n---\n{body}"

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    return True

def main():
    blog_dir = Path('website/blog')
    fixed_count = 0

    for md_file in blog_dir.glob('2025-*.md'):
        try:
            if fix_frontmatter(md_file):
                print(f"Fixed: {md_file.name}")
                fixed_count += 1
        except Exception as e:
            print(f"Error fixing {md_file.name}: {e}")

    print(f"\nFixed {fixed_count} files")

if __name__ == '__main__':
    main()
