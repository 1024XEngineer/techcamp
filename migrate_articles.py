#!/usr/bin/env python3
"""
Migrate articles from 2025/ directory to website/blog/ with Docusaurus frontmatter
"""
import os
import re
from pathlib import Path
from datetime import datetime
import shutil

# Tag mapping based on keywords in titles and content
TAG_KEYWORDS = {
    'ai': ['AI', 'ai', '大模型', '智能', '人工智能'],
    'go': ['Go', 'go', 'golang'],
    'compiler': ['编译器', 'XGo', 'LLGo', '类型系统', 'typesystem'],
    'engineering': ['工程实践', '工程师', 'Code Review', 'GitHub', 'PR', '质量'],
    'architecture': ['架构设计', '架构', '设计', '系统'],
    'xgo': ['XGo', 'xgo'],
    'llgo': ['LLGo', 'llgo', 'llpyg'],
    'career': ['职业', '发展', '成长', '特质', '核心竞争力'],
    'python': ['Python', 'python', 'llpyg'],
}

# Article index mapping to dates (starting from 2025-01-15)
base_date = datetime(2025, 1, 15)

def extract_title_from_content(content):
    """Extract title from markdown content"""
    lines = content.strip().split('\n')
    for line in lines:
        if line.startswith('# '):
            return line[2:].strip()
    return None

def generate_slug(title):
    """Generate URL-friendly slug from title"""
    # Remove special characters and convert to lowercase
    slug = re.sub(r'[^\w\s-]', '', title.lower())
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = slug[:100]  # Limit length
    return slug

def extract_tags(title, content, folder_name):
    """Extract relevant tags based on keywords"""
    tags = set()
    text_to_check = (title + ' ' + content + ' ' + folder_name).lower()

    for tag, keywords in TAG_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in text_to_check:
                tags.add(tag)
                break

    # Always add engineering for general articles if no specific tag
    if not tags:
        tags.add('engineering')

    return sorted(list(tags))

def extract_description(content, max_length=150):
    """Extract first meaningful paragraph as description"""
    # Remove title and empty lines
    lines = [l.strip() for l in content.split('\n') if l.strip() and not l.startswith('#')]

    for line in lines:
        if len(line) > 20 and not line.startswith('```'):
            desc = line[:max_length]
            if len(line) > max_length:
                desc += '...'
            return desc

    return "技术分享文章"

def migrate_article(source_path, index):
    """Migrate a single article"""
    with open(source_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract title
    title = extract_title_from_content(content)
    if not title:
        print(f"Warning: No title found in {source_path}")
        return None

    # Generate metadata
    folder_name = str(Path(source_path).parent.name)
    slug = generate_slug(title)
    tags = extract_tags(title, content, folder_name)
    description = extract_description(content)

    # Generate date (increment by 2 days for each article)
    from datetime import timedelta
    article_date = base_date + timedelta(days=index * 2)
    date_str = article_date.strftime('%Y-%m-%d')

    # Remove the title from content if it exists (we'll add it in frontmatter)
    content_lines = content.split('\n')
    if content_lines and content_lines[0].startswith('# '):
        content_lines = content_lines[1:]
        # Remove empty lines after title
        while content_lines and not content_lines[0].strip():
            content_lines.pop(0)

    content_body = '\n'.join(content_lines)

    # Create frontmatter
    frontmatter = f"""---
slug: {slug}
title: "{title}"
authors: [techcamp]
tags: [{', '.join(tags)}]
date: {date_str}
description: "{description}"
---

"""

    # Combine frontmatter and content
    new_content = frontmatter + content_body

    # Generate new filename
    new_filename = f"{date_str}-{slug}.md"
    new_path = Path('website/blog') / new_filename

    # Copy images if they exist in the same directory
    source_dir = Path(source_path).parent
    for img_file in source_dir.glob('*.png'):
        dest_img_dir = Path('website/static/img/blog') / slug
        dest_img_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(img_file, dest_img_dir / img_file.name)
        # Update image references in content
        new_content = new_content.replace(img_file.name, f'/img/blog/{slug}/{img_file.name}')

    for img_file in source_dir.glob('*.jpg'):
        dest_img_dir = Path('website/static/img/blog') / slug
        dest_img_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(img_file, dest_img_dir / img_file.name)
        new_content = new_content.replace(img_file.name, f'/img/blog/{slug}/{img_file.name}')

    # Write new file
    with open(new_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    return {
        'source': source_path,
        'destination': str(new_path),
        'title': title,
        'date': date_str,
        'tags': tags,
        'slug': slug
    }

def main():
    # Get all markdown files from 2025/
    source_files = sorted(Path('2025').glob('*/*.md'))

    results = []
    for index, source_file in enumerate(source_files):
        print(f"Migrating [{index + 1}/{len(source_files)}]: {source_file}")
        result = migrate_article(source_file, index)
        if result:
            results.append(result)

    # Print summary
    print("\n" + "="*80)
    print("MIGRATION SUMMARY")
    print("="*80)
    print(f"Total articles migrated: {len(results)}\n")

    # Group by tags
    tags_count = {}
    for result in results:
        for tag in result['tags']:
            tags_count[tag] = tags_count.get(tag, 0) + 1

    print("Tags distribution:")
    for tag, count in sorted(tags_count.items(), key=lambda x: x[1], reverse=True):
        print(f"  {tag}: {count} articles")

    print("\n" + "="*80)
    print("Migrated articles:")
    for result in results:
        print(f"\n  {result['date']} - {result['title']}")
        print(f"    File: {result['destination']}")
        print(f"    Tags: {', '.join(result['tags'])}")

if __name__ == '__main__':
    main()
