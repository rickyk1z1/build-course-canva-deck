# 课程大纲转 Canva 课件 Skill

`build-course-canva-deck` 用于把 PDF、XMind、DOCX、Markdown、TXT、OPML 等课程大纲制作成适合线上录课的 Canva 演示文稿。

所有产出都被视为同一套“自媒体认知、剪辑思维、视频剪辑技能”课程体系中的组成部分。Skill 会保持课程顺序、术语、比喻、难度递进和相邻课程分工一致。

## 一行安装

```bash
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py --repo rickyk1z1/canva-create-note --path skills/build-course-canva-deck
```

安装后重启 Codex，然后使用：

```text
$build-course-canva-deck
```

## 核心规则

- 每次读取大纲后，必须由用户明确选择“细纲”或“粗纲”，Skill 不自行判断。
- 细纲以已定稿的《影像基础参数》内容深度为基准，只优化教学表达和视觉呈现。
- 粗纲要比该基准更细，但只能沿原知识树分支纵向补充，不得横向扩展新主题。
- 每套课件都要结合整体课程地图，避免抢讲后续课程或重复相邻课程内容。
- 学员页面不出现 PDF、原稿、制作说明、详细讲稿等幕后措辞。
- 固定使用黑、橙、米白模板体系，并在 Canva 最终保存前进行一次整套审查。

## 支持格式

- PDF
- XMind
- DOCX
- Markdown / TXT
- OPML / FreeMind

## 使用条件

- 需要能够运行 Codex Skills。
- 最终写入 Canva 时，需要连接可访问模板 `DAHM5fsVEB0` 的 Canva 账号。

## 更新

安装器不会覆盖已经存在的 Skill。更新时先把 `~/.codex/skills/build-course-canva-deck` 移到备份目录，再重新执行上面的一行安装命令；确认新版正常后删除备份。
