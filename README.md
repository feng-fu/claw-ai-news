# Claw AI News

全球 AI 日报仓库，采用 **GitHub Pages + Jekyll**。

## 目标

- 每天只新增一篇 Markdown
- GitHub Pages 自动渲染
- 封面图独立存放在 `assets/`
- 首页自动列出日报归档

## 目录结构

- `_config.yml`：GitHub Pages / Jekyll 配置
- `_layouts/`：页面模板
- `index.md`：站点首页
- `daily/YYYY-MM-DD.md`：每日一篇日报 Markdown
- `assets/`：公共样式与封面图等静态资源

## 每日更新规则

### 1. 新增日报文件

文件命名：

```text
daily/YYYY-MM-DD.md
```

例如：

```text
daily/2026-03-11.md
```

### 2. Markdown 头部格式

```md
---
title: 全球 AI 日报｜2026-03-11
date: 2026-03-11
cover: /assets/cover-2026-03-11.png
tags:
  - OpenAI
  - Anthropic
---
```

### 3. 封面图路径

```text
assets/cover-YYYY-MM-DD.png
```

例如：

```text
assets/cover-2026-03-11.png
```

## GitHub Pages 设置

在仓库 `Settings -> Pages` 中配置：

- Source: `Deploy from a branch`
- Branch: `main`
- Folder: `/ (root)`

保存后，GitHub Pages 会自动构建 Jekyll 站点。

## 后续工作流

每次新增日报时：

1. 生成封面图到 `assets/cover-YYYY-MM-DD.png`
2. 新建 `daily/YYYY-MM-DD.md`
3. 提交并推送到 `main`
4. GitHub Pages 自动发布
