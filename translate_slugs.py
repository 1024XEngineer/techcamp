#!/usr/bin/env python3
"""
Translate Chinese article slugs to English using pinyin and keyword mapping.
This script updates existing blog articles with English slugs.
"""
import os
import re
from pathlib import Path
from typing import Dict, List

# Manual translation mapping for common technical terms and phrases
TRANSLATION_MAP = {
    # Engineering practices
    '工程实践': 'engineering-practices',
    '工程师': 'engineer',
    '工程': 'engineering',
    '实践': 'practice',
    '分享': 'sharing',
    '把小事做好': 'doing-small-things-well',
    '写代码不是第一步': 'coding-is-not-the-first-step',

    # AI and Technology
    'ai': 'ai',
    'AI': 'ai',
    '人工智能': 'artificial-intelligence',
    '大模型': 'large-language-model',
    '智能': 'intelligence',
    '重构': 'refactoring',
    '软件开发': 'software-development',
    '工具': 'tool',
    '规则': 'rules',
    '范式': 'paradigm',
    '革命': 'revolution',
    '时代': 'era',
    '应用': 'application',

    # Programming Languages
    'go': 'go',
    'xgo': 'xgo',
    'llgo': 'llgo',
    'python': 'python',
    'llpyg': 'llpyg',

    # Compiler and System
    '编译器': 'compiler',
    '类型系统': 'type-system',
    '理解': 'understanding',
    '实现': 'implementation',
    '从': 'from',
    '到': 'to',
    '集成': 'integration',
    '运行时': 'runtime',
    '编译': 'compilation',
    '桥梁': 'bridge',
    '生态': 'ecosystem',
    '快速': 'fast',

    # Architecture and Design
    '架构': 'architecture',
    '设计': 'design',
    '该从何入手': 'where-to-start',
    '入手': 'getting-started',
    '认知': 'understanding',
    '体会': 'insights',
    '几点': 'several',
    '关于': 'about',

    # Code Review and Development
    'code': 'code',
    'review': 'review',
    'pr': 'pr',
    'github': 'github',
    '合并': 'merge',
    '三选一': 'three-options',
    '主分支': 'main-branch',
    '该怎么选': 'how-to-choose',
    '不是什么': 'what-it-is-not',

    # Career and Development
    '职业': 'career',
    '发展': 'development',
    '成长': 'growth',
    '核心': 'core',
    '竞争力': 'competitiveness',
    '特质': 'characteristics',
    '优秀': 'excellent',
    '我眼中的': 'my-view-on',
    '眼中': 'perspective',
    '聊': 'talking-about',
    '观': 'perspective',
    '能写代码': 'can-write-code',
    '当': 'when',
    '是什么': 'what-is',

    # Projects and Tools
    'spx': 'spx',
    'algorithm': 'algorithm',
    'xlink': 'xlink',
    '构建': 'building',
    '多模态': 'multimodal',
    '搜索': 'search',
    '服务': 'service',
    '心得': 'experience',
    '一些': 'some',
    '项目': 'project',
    '看': 'from',
    '产品': 'product',
    '开发': 'development',
    '决策': 'decision',
    '层次': 'hierarchy',

    # Education and Training
    '同学': 'students',
    '为什么': 'why',
    '我建议': 'i-recommend',
    '建议': 'recommend',
    '你': 'you',
    '关注': 'follow',
    '1024': '1024',
    '实训营': 'techcamp',

    # Specific Topics
    '一行之差': 'one-line-difference',
    '文件': 'file',
    '末尾': 'end',
    '应该': 'should',
    '留': 'leave',
    '一个': 'a',
    '空行': 'blank-line',
    '如何': 'how',
    '才算': 'to-count-as',
    '完成': 'complete',
    '代码': 'code',
    '不是': 'not',
    '核心': 'core',
    '绘图': 'drawing',
    '让': 'making',
    '融入': 'integrate',
    '产品': 'product',
    '发布': 'released',
    '全景图': 'panorama',
    '全民': 'universal',
    '编程语言': 'programming-language',
    '语言': 'language',

    # Names
    '许式伟': 'xu-shiwei',
}

def translate_chinese_slug(chinese_slug: str) -> str:
    """
    Translate Chinese slug to English using manual mapping and fallback strategies.

    Args:
        chinese_slug: Chinese slug to translate

    Returns:
        English slug
    """
    # First, try direct mapping for the entire slug
    if chinese_slug in TRANSLATION_MAP:
        return TRANSLATION_MAP[chinese_slug]

    # Split the slug and translate each part
    parts = []
    remaining = chinese_slug

    # Try to match longest phrases first
    sorted_keys = sorted(TRANSLATION_MAP.keys(), key=len, reverse=True)

    while remaining:
        matched = False
        for key in sorted_keys:
            if remaining.startswith(key):
                parts.append(TRANSLATION_MAP[key])
                remaining = remaining[len(key):]
                matched = True
                break

        if not matched:
            # If character is already ASCII, keep it
            if ord(remaining[0]) < 128:
                if remaining[0].isalnum():
                    parts.append(remaining[0])
                elif remaining[0] == '-' and (not parts or parts[-1] != '-'):
                    parts.append('-')
                remaining = remaining[1:]
            else:
                # Skip unknown Chinese characters
                remaining = remaining[1:]

    # Join parts and clean up
    slug = '-'.join(parts)

    # Clean up multiple dashes
    slug = re.sub(r'-+', '-', slug)

    # Remove leading/trailing dashes
    slug = slug.strip('-')

    # Convert to lowercase
    slug = slug.lower()

    return slug if slug else 'untitled'


def generate_slug_mapping() -> Dict[str, str]:
    """
    Generate mapping of all current Chinese slugs to English slugs.

    Returns:
        Dictionary mapping Chinese slugs to English slugs
    """
    blog_dir = Path('website/blog')
    mapping = {}

    for md_file in sorted(blog_dir.glob('2025-*.md')):
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract current slug from frontmatter
        slug_match = re.search(r'^slug:\s*(.+)$', content, re.MULTILINE)
        if slug_match:
            chinese_slug = slug_match.group(1).strip()
            english_slug = translate_chinese_slug(chinese_slug)
            mapping[chinese_slug] = english_slug

    return mapping


def update_article_slug(file_path: Path, slug_mapping: Dict[str, str]) -> bool:
    """
    Update an article's slug in its frontmatter.

    Args:
        file_path: Path to the markdown file
        slug_mapping: Dictionary mapping Chinese slugs to English slugs

    Returns:
        True if updated, False otherwise
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract current slug
    slug_match = re.search(r'^slug:\s*(.+)$', content, re.MULTILINE)
    if not slug_match:
        return False

    chinese_slug = slug_match.group(1).strip()

    if chinese_slug not in slug_mapping:
        return False

    english_slug = slug_mapping[chinese_slug]

    # Replace slug in frontmatter
    new_content = re.sub(
        r'^slug:\s*.+$',
        f'slug: {english_slug}',
        content,
        count=1,
        flags=re.MULTILINE
    )

    # Update image paths if needed (from Chinese slug to English slug)
    new_content = new_content.replace(
        f'/img/blog/{chinese_slug}/',
        f'/img/blog/{english_slug}/'
    )

    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    return True


def rename_image_directories(slug_mapping: Dict[str, str]):
    """
    Rename image directories from Chinese slugs to English slugs.

    Args:
        slug_mapping: Dictionary mapping Chinese slugs to English slugs
    """
    img_blog_dir = Path('website/static/img/blog')

    if not img_blog_dir.exists():
        return

    for chinese_slug, english_slug in slug_mapping.items():
        chinese_dir = img_blog_dir / chinese_slug
        english_dir = img_blog_dir / english_slug

        if chinese_dir.exists() and not english_dir.exists():
            print(f"  Renaming image directory: {chinese_slug} -> {english_slug}")
            chinese_dir.rename(english_dir)


def main():
    """Main execution function."""
    print("="*80)
    print("CHINESE TO ENGLISH SLUG TRANSLATION")
    print("="*80)

    # Generate slug mapping
    print("\nGenerating slug mappings...")
    slug_mapping = generate_slug_mapping()

    print(f"\nFound {len(slug_mapping)} articles to translate:\n")
    for chinese, english in sorted(slug_mapping.items()):
        print(f"  {chinese}")
        print(f"    -> {english}\n")

    # Update articles
    print("\nUpdating article slugs...")
    blog_dir = Path('website/blog')
    updated_count = 0

    for md_file in sorted(blog_dir.glob('2025-*.md')):
        if update_article_slug(md_file, slug_mapping):
            print(f"  Updated: {md_file.name}")
            updated_count += 1

    print(f"\nUpdated {updated_count} articles")

    # Rename image directories
    print("\nRenaming image directories...")
    rename_image_directories(slug_mapping)

    print("\n" + "="*80)
    print("TRANSLATION COMPLETE")
    print("="*80)
    print("\nSlug mapping saved for reference:")
    for chinese, english in sorted(slug_mapping.items()):
        print(f"  {chinese} -> {english}")


if __name__ == '__main__':
    main()
