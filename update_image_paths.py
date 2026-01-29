#!/usr/bin/env python3
"""Update all image paths in blog posts"""
import re
from pathlib import Path

def update_image_paths_in_file(md_file):
    """Update image paths to point to /img/blog/slug/"""
    filename = Path(md_file).stem
    slug = '-'.join(filename.split('-')[3:])  # Remove YYYY-MM-DD prefix

    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Pattern 1: ![alt](relative/path/image.png) -> ![alt](/img/blog/slug/image.png)
    def replace_image_path(match):
        alt_text = match.group(1)
        old_path = match.group(2)
        # Skip if already points to /img/blog/
        if old_path.startswith('/img/blog/'):
            return match.group(0)
        img_name = Path(old_path).name
        new_path = f'/img/blog/{slug}/{img_name}'
        return f'![{alt_text}]({new_path})'

    updated_content = re.sub(r'!\[(.*?)\]\((.*?\.(?:png|jpg|jpeg|gif|PNG|JPG))\)',
                             replace_image_path, content, flags=re.IGNORECASE)

    if updated_content != content:
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        return True
    return False

def main():
    blog_dir = Path('website/blog')
    updated_count = 0

    for md_file in sorted(blog_dir.glob('2025-*.md')):
        if update_image_paths_in_file(md_file):
            print(f"Updated: {md_file.name}")
            updated_count += 1

    print(f"\nUpdated {updated_count} files")

if __name__ == '__main__':
    main()
