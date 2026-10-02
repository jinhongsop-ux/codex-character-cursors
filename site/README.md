# 在线预览站

静态网页提供五款角色的状态预览、16–256 屏幕物理像素的尺寸预览，以及完整 Windows 安装包下载。

线上页面仅预览，不会修改系统光标，也不会按照网页选中的尺寸重新打包。应用和恢复由下载包中的本地程序完成。

## 构建

在仓库根目录执行：

```sh
npm run build
```

无需安装额外依赖。输出目录为 `site/public`，包含网页、透明素材和六份原始 ZIP。构建时生成下载校验文件 `downloads/SHA256SUMS.txt`。

## 部署到 Vercel

导入此 GitHub 仓库，根目录保持仓库根目录。仓库中的 `vercel.json` 配置了构建命令和静态输出目录，ZIP 下载由 Vercel 直接提供。

也可以在已登录的 Vercel CLI 中，从仓库根目录执行 `vercel link`，然后 `vercel --prod`。

## 素材

五款角色统一来自 `studio/themes`，基础形象来自 `previews/characters`。预览始终从原始透明图缩放，不从缩略图反复放大。

更新成品时，将对应 ZIP 放入 `packs`，并更新 `build.mjs` 中的版本和文件映射。
