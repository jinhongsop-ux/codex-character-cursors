# 正式版本发布

完整合集版本由 `version.json` 管理；成品源码和素材统一在 `studio`，制作Skills在 `skills`。发行包保留运行所需资源，不嵌套旧ZIP、不包含构建缓存、测试截图和内部记录。

每次更新功能或素材：

1. 更新 `version.json`、`notes.md` 和使用说明。
2. 构建并检查完整包，完成相关功能验证。
3. 提交到GitHub，推送对应版本标签，例如 `v2.0.1`。

`Publish full Windows release` 工作流会在Windows上编译、打包和校验，然后把完整ZIP及SHA-256上传到该版本的GitHub Release。也支持在Actions中手动运行，输入版本号。

本地构建：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\release\build.ps1
```

输出在 `release-output`。同名本地ZIP已存在时停止构建，避免误覆盖旧包。改变版本或移走旧构建后再运行。

新版合集是推荐下载入口，旧独立包继续保留以兼容已有链接。线上预览和README使用Releases最新版本入口；基础形象与五角色素材保持同源。
