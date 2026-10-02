# 个性化电脑鼠标光标

上传一张角色参考图或状态拼图，用 Codex 制作个性化 Windows 光标。非 Q 版角色可以先转换成 2D Q 版，再制作光标皮肤。

## 已有成品

完整解压下载的 ZIP，再运行里面的“一键安装.cmd”。每个包内都有预览和说明。

| 角色 | 下载 | 预览 |
|---|---|---|
| 蕾塞 V1.5 | [完整包](packs/蕾塞光标-Windows-V1.5.zip) | [查看](previews/reze.png) |
| 蕾姆 V1.2.1 | [完整包](packs/RemCursor-Windows-v1.2.1.zip) | [查看](previews/rem.png) |
| deepseek酱 V1.5 | [完整包](packs/deepseek酱光标-样本-V1.5.zip) | [查看](previews/deepseek.png) |
| Pochita Mini V1.5 | [完整包](packs/Pochita-Mini光标-V1.5.zip) | [查看](previews/pochita.png) |

V1.5 包提供白色小号恢复与系统默认恢复；24×24小号在Windows重新加载方案后可能回到32×32，需重新运行。蕾姆V1.2.1的“一键恢复原状”恢复安装前备份，行为与V1.5不同。

## Skills

将 skills 下的两个文件夹放到自己的 Codex skills 目录，通常为 `~/.codex/skills/`。

- [character-chibi-prep](skills/character-chibi-prep/SKILL.md)：非Q版角色转成一致的2D Q版形象。
- [character-cursor-pack](skills/character-cursor-pack/SKILL.md)：制作16状态素材、17个Windows角色映射、预览及中文安装包。

示例：`使用 $character-chibi-prep 将参考角色转换成Q版，再调用 $character-cursor-pack 做成完整光标包。`

已有Q版角色可直接调用光标skill；成品状态图要求保色时使用裁切/蒙版，跳过AI重绘。生成模式使用Codex内置图像工具；本地构建工具需要Python与Pillow，安装好的光标包不需要Python。

这些成品已在制作电脑上验证，不代表所有Windows版本或其他电脑均已测试。新的非Q版转Q版链路尚待样本验证。

## 素材说明

案例用于展示制作效果。角色IP及第三方原图权利属于各自权利人；不代表拥有商业分发授权。当前未指定项目开源许可证。
