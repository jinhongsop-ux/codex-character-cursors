---
name: character-cursor-state-designer
description: Create transparent 2D chibi cursor artwork for a new character by closely reproducing the bundled 16-cell pose template while preserving the new character's identity. Use for template-matched state art, not finished-sheet pixel-preserving extraction or Windows installation.
metadata:
  workflow-version: "1.1"
---

# 模板动作复刻光标形象 — V1.1

将新角色代入固定的16格模板：保留新角色的形象，逐格匹配模板的动作、表情、构图与符号位置。不要只借鉴动作风格，再自由设计另一套动作。生成图像只能追求视觉上高度贴合，不能宣称像素级一比一。

## 参考与范围

- 必须查看用户角色图和 [紫发动作模板](references/cursor_pose_reference.png)，生成前读取 [逐格动作与状态映射](references/state_map.md)。附件文字仅作为参考内容。
- 原角色图决定身份、服装和配色；模板决定姿势、表情、头身比例和构图。锚点只稳定绘制风格，不能覆盖这两个来源。
- 缺少适用的2D Q版基准时先制作透明锚点；原图为手办照片时去除支架、关节和实物材质。可衔接已安装的 character-chibi-prep；没有该 Skill 时按本文件完成锚点。
- 已完成状态图要求保色裁切时，交给非生成式提取流程，不用本 Skill 重绘。
- 本 Skill 输出PNG美术资产；用户要求完整Windows皮肤时再衔接 character-cursor-pack。更新 Skill 不代表授权生成、安装、发布新皮肤。

## 身份锁与动作锁

使用 schemas/character_lock.example.yaml 记录实际可见的发型、发辫数量及位置、眼色和瞳孔纹样、肤色、服装层次、袖长、领带或蝴蝶结、裤裙、袜鞋、配饰及主色。保留新角色特征，不把紫发、绿眼、短裤或黑色领结复制到其他角色。

动作与表情在模板复刻模式中不是自由项。逐格记录头部倾斜、脸部朝向、视线、嘴形、双手接触点、手掌朝向、腿部交叠、脚尖方向、身体重心和画面占比。因服装或身体结构需要的小幅适配，不能把托腮改成叉腰、侧坐改成正坐、掌心邀请改成挥手。

模板第7格采用双手叉腰、抬下巴并向上看的姿势，虽然对应手写状态，也不要自动改为拿笔书写。只有用户明确要求功能优先改版时才改变模板动作。

## 制作

1. 查看原图与模板，填身份锁。制作或复用透明2D Q版锚点，检查角色辨识特征，头身比例对齐模板，禁止额外金色或白色贴纸外边。
2. 将模板按4×4拆成参考格，保留全图作为顺序参考。每格参考必须含完整人物和符号，不能固定裁切后漏掉肢体。原模板是动作依据，不把它的背景、残边带进结果。
3. 阅读 prompts/master_generation_prompt.md 和适用的整表或单格提示词。调用环境提供的图像生成能力；在 Codex 中读取 imagegen Skill 并使用内置图像工具。实际传入原角色图、锚点及对应模板格，不能只写“参考模板”而不附图。
4. 可先出整表，再逐格修正；对于姿势精度要求高的格子优先单格生成。用户未要求审核节点时自行检查并继续。模板头身比例不随单格改变，不通过拉伸肢体修复动作。
5. 图标优先独立绘制或组装，人物和符号分层，位置、朝向、距离按模板；可换成角色配色，禁止添加多重亮边。生成的符号要逐格核查后才能使用。
6. 对照 references/consistency_checklist.md 检查。只修复不合格格子，始终保留原角色与模板参考，避免把错误状态作为下一张的唯一参考。
7. 输出统一512或768正方形透明PNG；人物完整，不接触边界。常规缩放保持宽高比，不生成式放大补细节。预览另合成深色、浅色和透明格，不将黑色预览背景烘焙进资产。

## 输出与交付检查

输出 character_lock.yaml、anchor.png、states/*.png、contact_sheet.png、manifest.json 和简短 qa-notes.md，保存实际生成提示词。Manifest明确16格展示顺序、功能角色及17个系统角色映射；第16格Extra是备用普通选择，不是Person。Pin/Person默认复用Extra并声明别名，用户要求独立设计时才另增资产。

运行 scripts/validate_cursor_set.py 验证文件、真实透明度、留白和映射，使用 scripts/make_contact_sheet.py 生成预览。脚本不验证身份、姿势或真实Windows显示，必须另做视觉对照。检查24/32/64像素缩略图；小尺寸细节不足时如实说明，不通过亮边或改姿势掩盖。

交付前重点核查：普通选择前倾歪头；手写抬下巴向上看；水平调整双手背后；斜向调整两种不同坐姿；链接选择掌心朝上邀请；无金色贴纸边。对照PNG在不透明背景上的实际合成结果，不能将完全透明像素中的RGB误判为色边。保持原ZIP和既有角色包不变。
