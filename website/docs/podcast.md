---
sidebar_position: 5
title: 播客
description: 收听我们的技术播客节目
slug: /podcast
---

# 🎙️ 技术播客

欢迎来到 1024 TechCamp 技术播客频道！在这里，我们与行业专家深入探讨 AI、工程实践和技术趋势。

## 最新节目

:::info
播客节目即将上线，敬请期待！
:::

<!--
播客节目列表将自动显示在这里
当有播客文章时，它们会自动出现在 /blog 页面，并可通过 'podcast' 标签筛选
-->

## 订阅方式

播客上线后，您可以通过以下方式订阅：

- **RSS 订阅**：`/blog/rss.xml`
- **Atom 订阅**：`/blog/atom.xml`
- 您也可以在 [博客页面](/blog) 通过 `podcast` 标签筛选播客节目

## 播客节目归档

<!--
播客节目表格将在这里显示
格式示例：

| 节目编号 | 标题 | 发布日期 | 时长 |
|---------|------|---------|------|
| EP001 | 对话AI专家：未来的智能系统 | 2025-01-20 | 45:30 |
-->

## 如何发布播客节目

要发布新的播客节目，请在 `website/blog/` 目录中创建新的 Markdown 文件，并添加以下 frontmatter：

```markdown
---
slug: your-podcast-slug
title: "播客标题"
authors: [host1, guest1]
tags: [podcast, ai, interview]
date: 2025-01-20
description: "播客节目简介"
type: podcast
episode_number: 1
audio_url: https://cdn.example.com/podcasts/your-podcast.mp3
duration: "45:30"
---

## 节目简介

播客节目内容简介...

## 嘉宾介绍

嘉宾信息...

## 时间线

- 00:00 开场介绍
- 05:30 话题一
- 20:15 话题二
- ...

## 相关链接

- [嘉宾 GitHub](https://github.com/...)
- [相关项目](https://...)
```

### Frontmatter 字段说明

- **slug**: URL友好的节目标识符（英文）
- **title**: 节目标题
- **authors**: 主持人和嘉宾列表
- **tags**: 必须包含 `podcast` 标签，还可以添加其他相关标签
- **date**: 发布日期
- **description**: 节目简介（用于SEO和预览）
- **type**: 设置为 `podcast` 以标识为播客节目
- **episode_number**: 节目编号
- **audio_url**: 音频文件URL（MP3格式）
- **duration**: 音频时长（格式：MM:SS 或 HH:MM:SS）

## 技术实现

本网站的播客功能基于 Docusaurus 博客系统实现：

- 播客节目作为特殊的博客文章存储
- 通过 `podcast` 标签进行分类和筛选
- 支持 RSS/Atom 订阅
- 可以在博客列表页面查看所有内容
- 未来可扩展音频播放器组件
