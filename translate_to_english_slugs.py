#!/usr/bin/env python3
"""Translate Chinese article titles to English slugs and re-migrate articles"""
import re
from pathlib import Path
from typing import Dict
import yaml

# Manual mapping of Chinese titles to English slugs
TITLE_TO_SLUG_MAPPING = {
    "工程实践分享-把小事做好": "engineering-practice-doing-small-things-well",
    "工程实践分享写代码不是第一步": "engineering-practice-coding-is-not-first-step",
    "同学为什么我建议你关注-1024-实训营": "why-you-should-join-1024-techcamp",
    "当-ai-能写代码工程师的核心竞争力是什么": "engineer-core-competitiveness-in-ai-era",
    "我眼中的优秀工程师特质": "qualities-of-excellent-engineers",
    "一行之差为什么你的文件末尾应该留一个空行": "why-end-files-with-newline",
    "从类型系统理解-xgo-编译器的实现": "understanding-xgo-compiler-through-type-system",
    "ai-重构软件开发从工具到规则的范式革命": "ai-reshaping-software-development-paradigm-shift",
    "许式伟聊-ai-时代下的工程师发展观": "xu-shiwei-on-engineer-development-in-ai-era",
    "许式伟发布-xgo-全景图ai-时代的全民编程语言": "xu-shiwei-releases-xgo-roadmap-programming-for-all",
    "github-pr-合并三选一主分支该怎么选": "github-pr-merge-strategies-which-to-choose",
    "如何才算完成一个ai应用": "what-makes-ai-application-complete",
    "从类型系统理解-llgo-编译器的实现": "understanding-llgo-compiler-through-type-system",
    "code-review-不是什么": "what-code-review-is-not",
    "架构设计该从何入手": "where-to-start-architecture-design",
    "关于架构设计的几点认知体会": "insights-on-architecture-design",
    "spx-algorithm构建多模态搜索服务的一些心得": "spx-algorithm-building-multimodal-search-service",
    "代码不是核心从-xlink-项目看产品开发的决策层次": "code-is-not-core-decision-layers-in-xlink-project",
    "llpyg-llgo-快速集成-python-生态的桥梁": "llpyg-bridge-for-llgo-python-integration",
    "x绘图-让ai融入产品": "xdraw-integrating-ai-into-products",
    "让ai融入产品": "integrating-ai-into-products",  # Alternative
    "x绘图-我们是如何让AI更好的融入我们的产品的": "xdraw-integrating-ai-into-products",
    "llgo-python-编译与运行时集成": "llgo-python-compilation-and-runtime-integration",
}

def extract_frontmatter(content: str) -> tuple[dict, str]:
    """Extract YAML frontmatter and body from markdown content"""
    match = re.match(r'^---\n(.*?)\n---\n(.*)$', content, re.DOTALL)
    if not match:
        return {}, content

    frontmatter_text = match.group(1)
    body = match.group(2)

    try:
        frontmatter = yaml.safe_load(frontmatter_text)
        return frontmatter, body
    except yaml.YAMLError as e:
        print(f"Error parsing YAML: {e}")
        return {}, content

def get_english_slug(chinese_slug: str, title: str) -> str:
    """Get English slug from mapping or generate from title"""
    # Try direct mapping first
    if chinese_slug in TITLE_TO_SLUG_MAPPING:
        return TITLE_TO_SLUG_MAPPING[chinese_slug]

    # Try to extract from title
    clean_title = title.replace('"', '').replace("'", "").strip()
    if clean_title in TITLE_TO_SLUG_MAPPING:
        return TITLE_TO_SLUG_MAPPING[clean_title]

    # Fallback: simple transliteration
    slug = re.sub(r'[^\w\s-]', '', chinese_slug.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug.strip('-')

def migrate_article(md_file: Path) -> bool:
    """Migrate a single article to English slug"""
    print(f"\nProcessing: {md_file.name}")

    # Read current file
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract frontmatter
    frontmatter, body = extract_frontmatter(content)

    if not frontmatter:
        print(f"  ⚠️  No frontmatter found, skipping")
        return False

    # Get current slug and title
    current_slug = frontmatter.get('slug', '')
    title = frontmatter.get('title', '')
    date = frontmatter.get('date', '')

    # Generate English slug
    english_slug = get_english_slug(current_slug, title)

    print(f"  Current slug: {current_slug}")
    print(f"  English slug: {english_slug}")

    # Update frontmatter with new slug format
    frontmatter['slug'] = f"/blog/2025/{english_slug}"

    # Generate new filename
    # Extract date from current filename
    filename_parts = md_file.stem.split('-', 3)
    if len(filename_parts) >= 3:
        year, month, day = filename_parts[0], filename_parts[1], filename_parts[2]
        new_filename = f"{year}-{month}-{day}-{english_slug}.md"
    else:
        new_filename = f"{english_slug}.md"

    new_filepath = md_file.parent / new_filename

    # Build new content with updated frontmatter
    frontmatter_yaml = yaml.dump(frontmatter, allow_unicode=True, sort_keys=False, default_flow_style=False)
    new_content = f"---\n{frontmatter_yaml}---\n{body}"

    # Write to new file
    with open(new_filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"  ✅ Created: {new_filename}")

    # Delete old file if different
    if new_filepath != md_file:
        md_file.unlink()
        print(f"  🗑️  Deleted: {md_file.name}")

    return True

def main():
    blog_dir = Path('website/blog')
    migrated_count = 0

    # Get all 2025 articles (excluding welcome.md)
    articles = sorted([f for f in blog_dir.glob('2025-*.md') if 'welcome' not in f.name])

    print(f"Found {len(articles)} articles to migrate\n")
    print("="*70)

    for md_file in articles:
        if migrate_article(md_file):
            migrated_count += 1

    print("\n" + "="*70)
    print(f"✅ Successfully migrated {migrated_count}/{len(articles)} articles")

if __name__ == '__main__':
    main()
