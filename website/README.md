# 1024 TechCamp 官方网站

这是 1024 实训营的官方网站，使用 [Docusaurus](https://docusaurus.io/) 构建。

## 本地开发

### 安装依赖

```bash
npm install
```

### 启动开发服务器

```bash
npm start
```

此命令启动本地开发服务器并在浏览器中打开网站。大多数更改会实时反映，无需重启服务器。

### 构建

```bash
npm run build
```

此命令生成静态内容到 `build` 目录，可以使用任何静态内容托管服务提供服务。

### 本地预览构建

```bash
npm run serve
```

## GitHub Pages 部署

网站通过 GitHub Actions 自动部署到 GitHub Pages。

当推送到 `main` 分支且修改了 `website/` 目录下的文件时，会自动触发部署。

部署后，网站将在以下地址访问：
**https://qiniu.github.io/techcamp/**

### 启用 GitHub Pages

仓库管理员需要在 GitHub 仓库设置中启用 GitHub Pages：

1. 进入仓库的 **Settings** → **Pages**
2. 在 **Source** 下选择 **GitHub Actions**
3. 保存设置

## 内容管理

### 添加博客文章

在 `blog/` 目录下创建新的 Markdown 文件：

```markdown
---
slug: your-post-slug
title: 文章标题
authors: [techcamp]
tags: [AI, Go, 工程实践]
---

文章内容...

<!-- truncate -->

更多内容...
```

### 添加文档

在 `docs/` 目录下创建或修改 Markdown 文件。文档会自动出现在侧边栏中。

### 更新作者信息

编辑 `blog/authors.yml` 文件添加或修改作者信息。

### 管理标签

编辑 `blog/tags.yml` 文件定义博客标签。

## 配置

主要配置文件是 `docusaurus.config.ts`，包含网站的基本信息、主题配置等。

## 技术栈

- **Docusaurus 3.x** - React 静态站点生成器
- **TypeScript** - 类型安全
- **GitHub Pages** - 免费托管
- **GitHub Actions** - 自动部署

## 了解更多

- [Docusaurus 文档](https://docusaurus.io/)
- [GitHub Pages 文档](https://docs.github.com/en/pages)
