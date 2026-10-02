# 在线预览站

静态网页与本地工作台共用`studio/web`中的HTML、CSS和交互代码，构建时切换运行模式。提供完整目录的角色卡片、搜索分类、状态预览、16–256 屏幕物理像素的尺寸预览，以及完整 Windows 安装包下载。

线上页面仅预览，不会修改系统光标，也不会按照网页选中的尺寸重新打包。应用和恢复由下载包中的本地程序完成。

## 构建

在仓库根目录执行：

```sh
npm run build
```

无需安装额外依赖。输出目录为 `site/public`，包含网页、透明素材和六份原始 ZIP。构建时生成下载校验文件 `downloads/SHA256SUMS.txt`。

## 部署到 Vercel

导入此 GitHub 仓库，根目录保持仓库根目录。仓库中的 `vercel.json` 配置了构建命令和静态输出目录。完整合集下载链接指向 GitHub Releases，早期独立包由 Vercel 提供。

也可以在已登录的 Vercel CLI 中，从仓库根目录执行 `vercel link`，然后 `vercel --prod`。

## 素材

全部角色统一来自 `studio/themes`，基础形象来自 `previews/characters`。预览始终从原始透明图缩放，不从缩略图反复放大。

新增角色时，加入 `studio/themes/catalog.json` 与对应素材目录，同时更新基础形象和状态预览。发布完整合集时更新 `release/version.json` 并运行发布工作流；新角色通过完整合集下载，不必重复增加独立ZIP。
