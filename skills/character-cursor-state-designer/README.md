# Character Cursor State Designer V1.1

将新角色代入紫发蕾塞的16格动作模板。保留新角色的身份、服装和配色，逐格匹配动作、表情、构图及符号位置。

把 character-cursor-state-designer 文件夹放到 Codex 的 skills 目录，上传角色图后调用 `$character-cursor-state-designer`。已有2D基准可直接使用；手办或非Q版角色先建立2D锚点。使用内置图像能力生成，Python和Pillow仅用于透明PNG检查与预览组装。

默认输出16格PNG、角色约束、锚点、manifest和对照检查记录。第12格是候选选择，第15格是链接选择，第16格为Extra；Pin/Person复用Extra后形成17个系统角色映射。

保留叉腰仰头的手写格和掌心朝上的链接格，不根据功能名称自由改动作。无新增金色贴纸边，符号保留模板布局，可使用新角色配色。生成式结果需要逐格核查，不能保证像素级一比一。

本 Skill 只制作美术资产。要求完整 Windows 光标包时继续调用 character-cursor-pack，安装、打包和发布仍遵循具体任务授权。模板和角色素材的权利属于各自权利人。
