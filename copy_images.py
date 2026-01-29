#!/usr/bin/env python3
"""Copy images from 2025/ articles to website/static/img/blog/"""
import os
import shutil
import re
from pathlib import Path

def copy_images_for_article(article_md, source_dir):
    """Copy images for a single article"""
    # Get slug from filename
    filename = Path(article_md).stem  # Remove .md
    slug = '-'.join(filename.split('-')[3:])  # Remove date prefix

    # Read article to find image references
    with open(article_md, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find all image references
    image_pattern = r'!\[.*?\]\((.*?\.(?:png|jpg|jpeg|gif))\)'
    images = re.findall(image_pattern, content, re.IGNORECASE)

    if not images:
        return 0

    # Create target directory
    target_dir = Path('website/static/img/blog') / slug
    target_dir.mkdir(parents=True, exist_ok=True)

    copied = 0
    # Copy each image
    for img_ref in images:
        # Clean path
        img_name = Path(img_ref).name

        # Try to find source image in 2025 directory
        for source_article_dir in Path('2025').glob('*'):
            if source_article_dir.is_dir():
                source_img = source_article_dir / img_name
                if source_img.exists():
                    target_img = target_dir / img_name
                    shutil.copy2(source_img, target_img)
                    print(f"  Copied: {img_name} -> {target_img}")
                    copied += 1
                    break
                # Also check subdirectories
                for subdir in source_article_dir.glob('*'):
                    if subdir.is_dir():
                        source_img = subdir / img_name
                        if source_img.exists():
                            target_img = target_dir / img_name
                            shutil.copy2(source_img, target_img)
                            print(f"  Copied: {img_name} -> {target_img}")
                            copied += 1
                            break

    return copied

def update_image_paths(article_md):
    """Update image paths in article to point to static directory"""
    filename = Path(article_md).stem
    slug = '-'.join(filename.split('-')[3:])

    with open(article_md, 'r', encoding='utf-8') as f:
        content = f.read()

    # Update all image references
    # Pattern: ![alt](path/to/image.png) -> ![alt](/img/blog/slug/image.png)
    def replace_image_path(match):
        alt_text = match.group(1)
        old_path = match.group(2)
        img_name = Path(old_path).name
        new_path = f'/img/blog/{slug}/{img_name}'
        return f'![{alt_text}]({new_path})'

    updated_content = re.sub(r'!\[(.*?)\]\((.*?\.(?:png|jpg|jpeg|gif))\)',
                             replace_image_path, content, flags=re.IGNORECASE)

    if updated_content != content:
        with open(article_md, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        return True
    return False

def main():
    blog_dir = Path('website/blog')
    total_copied = 0
    total_updated = 0

    for md_file in sorted(blog_dir.glob('2025-*.md')):
        print(f"\nProcessing: {md_file.name}")
        copied = copy_images_for_article(md_file, Path('2025'))
        total_copied += copied

        if copied > 0:
            if update_image_paths(md_file):
                print(f"  Updated image paths in {md_file.name}")
                total_updated += 1

    print(f"\n{'='*60}")
    print(f"Total images copied: {total_copied}")
    print(f"Total articles updated: {total_updated}")

if __name__ == '__main__':
    main()
