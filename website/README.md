# 1024 TechCamp Website

Official website for 1024 TechCamp - A platform for engineers to grow together.

## 🚀 Project Structure

```
website/
├── public/          # Static assets
├── src/
│   ├── content/     # Content collections (blog posts)
│   ├── layouts/     # Page layouts
│   ├── pages/       # Route pages
│   ├── components/  # Reusable components
│   └── styles/      # Global styles
├── astro.config.mjs # Astro configuration
└── package.json     # Dependencies
```

## 🛠️ Development

### Prerequisites

- Node.js 18+
- npm or pnpm

### Setup

```bash
cd website
npm install
```

### Commands

| Command           | Action                                       |
|-------------------|----------------------------------------------|
| `npm run dev`     | Start dev server at `localhost:4321`        |
| `npm run build`   | Build production site to `./dist/`          |
| `npm run preview` | Preview built site locally                   |

## 📝 Adding Content

### Blog Posts

Create a new `.md` or `.mdx` file in `src/content/blog/`:

```markdown
---
title: "Your Post Title"
description: "Brief description"
pubDate: 2025-01-28
author: "Your Name"
tags: ["tag1", "tag2"]
---

Your content here...
```

### Images

Place images in `public/` directory and reference them in markdown:

```markdown
![Alt text](/techcamp/image.png)
```

## 🌐 Deployment

The site automatically deploys to GitHub Pages when you push to the `blog` branch.

- Site URL: `https://qiniu.github.io/techcamp`
- Configured in: `.github/workflows/deploy.yml`

## 📄 License

Apache-2.0 - See [LICENSE](../LICENSE) for details.
