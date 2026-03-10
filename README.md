# Claw AI News

全球 AI 日报仓库。

## 结构

- `index.html`：站点首页（GitHub Pages 入口）
- `assets/`：全站公共样式与公共资源
- `daily/YYYY-MM-DD/index.md`：日报 Markdown 原稿
- `daily/YYYY-MM-DD/index.html`：日报静态页面
- `daily/YYYY-MM-DD/assets/`：该日报对应图片资源

## GitHub Pages

建议在仓库 Settings → Pages 中启用：

- Source: `Deploy from a branch`
- Branch: `main`
- Folder: `/ (root)`

启用后，站点会直接托管根目录下的 `index.html` 与 `daily/*/index.html`。

## 后续工作流

每次新增日报时：

1. 新建 `daily/YYYY-MM-DD/`
2. 放入 `index.md`
3. 放入 `index.html`
4. 放入 `assets/cover.png`
5. 更新首页 `index.html` 列表
