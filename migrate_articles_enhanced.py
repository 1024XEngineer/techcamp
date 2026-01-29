#!/usr/bin/env python3
"""
Enhanced article migration script with automatic slug translation.
This script migrates articles from source directory to Docusaurus blog with English slugs.
"""
import os
import re
import sys
from pathlib import Path
from datetime import datetime, timedelta
import shutil

# Import translation function from translate_slugs
sys.path.insert(0, str(Path(__file__).parent))
from translate_slugs import translate_chinese_slug

# Tag mapping based on keywords
TAG_KEYWORDS = {
    'ai': ['AI', 'ai', '大模型', '智能', '人工智能'],
    'go': ['Go', 'go', 'golang'],
    'compiler': ['编译器', 'XGo', 'LLGo', '类型系统', 'typesystem'],
    'engineering': ['工程实践', '工程师', 'Code Review', 'GitHub', 'PR', '质量', '代码'],
    'architecture': ['架构设计', '架构', '设计', '系统'],
    'xgo': ['XGo', 'xgo'],
    'llgo': ['LLGo', 'llgo', 'llpyg'],
    'career': ['职业', '发展', '成长', '特质', '核心竞争力'],
    'python': ['Python', 'python', 'llpyg'],
    'podcast': ['播客', '访谈', '对话', 'podcast', 'interview'],
}

# Base date for articles
BASE_DATE = datetime(2025, 1, 15)

def extract_title_from_content(content: str) -> str:
    """Extract title from markdown content."""
    lines = content.strip().split('\n')
    for line in lines:
        if line.startswith('# '):
            return line[2:].strip()
    return None


def generate_slug_from_title(title: str) -> str:
    """
    Generate English slug from Chinese title.
    Uses the translation mapping from translate_slugs.py
    """
    # If title is already mostly English, just clean it
    if all(ord(char) < 128 or char in '-_' for char in title if char.isalnum() or char in '-_'):
        slug = re.sub(r'[^\w\s-]', '', title.lower())
        slug = re.sub(r'[\s_]+', '-', slug)
        return slug.strip('-')

    # Translate Chinese to English
    return translate_chinese_slug(title)


def extract_tags(title: str, content: str, folder_name: str = '') -> list:
    """Extract relevant tags based on keywords."""
    tags = set()
    text_to_check = f"{title} {content} {folder_name}".lower()

    for tag, keywords in TAG_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in text_to_check:
                tags.add(tag)
                break

    # Always add engineering if no tags
    if not tags:
        tags.add('engineering')

    return sorted(list(tags))


def extract_description(content: str, max_length: int = 150) -> str:
    """Extract first meaningful paragraph as description."""
    lines = [l.strip() for l in content.split('\n')
             if l.strip() and not l.startswith('#')]

    for line in lines:
        if len(line) > 20 and not line.startswith('```'):
            desc = line[:max_length]
            if len(line) > max_length:
                desc += '...'
            return desc

    return "技术分享文章"


def is_podcast_article(content: str, tags: list) -> bool:
    """Determine if article is a podcast episode."""
    # Check if content mentions podcast/interview keywords
    podcast_keywords = ['播客', '访谈', '对话', 'podcast', 'interview', '音频']
    content_lower = content.lower()

    # Or if it has podcast tag
    return 'podcast' in tags or any(kw in content_lower for kw in podcast_keywords)


def migrate_article(source_path: Path, index: int, dest_dir: Path = Path('website/blog')) -> dict:
    """
    Migrate a single article with English slug.

    Args:
        source_path: Path to source markdown file
        index: Article index for date calculation
        dest_dir: Destination directory

    Returns:
        Dictionary with migration results
    """
    with open(source_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract title
    title = extract_title_from_content(content)
    if not title:
        print(f"⚠️  Warning: No title found in {source_path}")
        return None

    # Generate metadata
    folder_name = str(source_path.parent.name)
    chinese_slug = re.sub(r'[^\w\s-]', '', title.lower())
    chinese_slug = re.sub(r'[\s_]+', '-', chinese_slug)[:100]

    # Translate slug to English
    english_slug = generate_slug_from_title(title)

    tags = extract_tags(title, content, folder_name)
    description = extract_description(content)

    # Check if podcast
    is_podcast = is_podcast_article(content, tags)

    # Generate date (increment by 2 days for each article)
    article_date = BASE_DATE + timedelta(days=index * 2)
    date_str = article_date.strftime('%Y-%m-%d')

    # Remove title from content
    content_lines = content.split('\n')
    if content_lines and content_lines[0].startswith('# '):
        content_lines = content_lines[1:]
        while content_lines and not content_lines[0].strip():
            content_lines.pop(0)

    content_body = '\n'.join(content_lines)

    # Create frontmatter
    frontmatter_parts = [
        '---',
        f'slug: {english_slug}',
        f'title: "{title}"',
        'authors: [techcamp]',
        f'tags: [{", ".join(tags)}]',
        f'date: {date_str}',
        f'description: "{description}"',
    ]

    # Add podcast-specific fields if applicable
    if is_podcast:
        frontmatter_parts.extend([
            'type: podcast',
            '# episode_number: 1',
            '# audio_url: https://cdn.example.com/podcast.mp3',
            '# duration: "45:30"',
        ])

    frontmatter_parts.append('---')
    frontmatter = '\n'.join(frontmatter_parts) + '\n\n'

    # Combine
    new_content = frontmatter + content_body

    # Generate filename
    new_filename = f"{date_str}-{english_slug}.md"
    new_path = dest_dir / new_filename

    # Handle images
    source_dir = source_path.parent
    for img_pattern in ['*.png', '*.jpg', '*.jpeg', '*.gif']:
        for img_file in source_dir.glob(img_pattern):
            dest_img_dir = Path('website/static/img/blog') / english_slug
            dest_img_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(img_file, dest_img_dir / img_file.name)

            # Update image references
            new_content = new_content.replace(
                img_file.name,
                f'/img/blog/{english_slug}/{img_file.name}'
            )

    # Write file
    with open(new_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    return {
        'source': str(source_path),
        'destination': str(new_path),
        'title': title,
        'date': date_str,
        'tags': tags,
        'chinese_slug': chinese_slug,
        'english_slug': english_slug,
        'is_podcast': is_podcast,
    }


def main():
    """Main migration function."""
    print("="*80)
    print("ENHANCED ARTICLE MIGRATION WITH SLUG TRANSLATION")
    print("="*80)

    # Check source directory
    source_dir = Path('2025')
    if not source_dir.exists():
        print(f"❌ Source directory '{source_dir}' not found")
        return

    # Get all markdown files
    source_files = sorted(source_dir.glob('*/*.md'))

    if not source_files:
        print(f"❌ No markdown files found in {source_dir}")
        return

    print(f"\n📁 Found {len(source_files)} articles to migrate\n")

    # Migrate articles
    results = []
    for index, source_file in enumerate(source_files):
        print(f"📝 [{index + 1}/{len(source_files)}] Migrating: {source_file.name}")
        result = migrate_article(source_file, index)
        if result:
            results.append(result)
            print(f"   ✓ Slug: {result['chinese_slug']} → {result['english_slug']}")
            if result['is_podcast']:
                print(f"   🎙️  Identified as podcast episode")

    # Print summary
    print("\n" + "="*80)
    print("MIGRATION SUMMARY")
    print("="*80)
    print(f"✓ Total articles migrated: {len(results)}")

    # Tag distribution
    tags_count = {}
    podcast_count = 0
    for result in results:
        for tag in result['tags']:
            tags_count[tag] = tags_count.get(tag, 0) + 1
        if result['is_podcast']:
            podcast_count += 1

    print(f"\n📊 Tag Distribution:")
    for tag, count in sorted(tags_count.items(), key=lambda x: x[1], reverse=True):
        emoji = '🎙️ ' if tag == 'podcast' else ''
        print(f"   {emoji}{tag}: {count} articles")

    if podcast_count > 0:
        print(f"\n🎙️  Podcast episodes: {podcast_count}")

    print("\n📋 Slug Translation Mapping:")
    for result in results:
        print(f"   {result['chinese_slug']}")
        print(f"   → {result['english_slug']}\n")

    print("="*80)
    print("✨ Migration complete!")
    print("="*80)


if __name__ == '__main__':
    main()
