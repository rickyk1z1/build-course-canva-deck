# build-course-canva-deck

`build-course-canva-deck` 是一个 Codex Skill，用于把 PDF、XMind、DOCX、Markdown、TXT、OPML、FreeMind 等课程大纲制作成适合线上录课的 Canva 演示课件。

它不是普通的 PPT 生成器。它会把每节课当成同一套“自媒体认知、剪辑思维、视频剪辑技能”课程体系中的组成部分，要求保持源大纲顺序、课程边界、术语体系、比喻、案例和难度递进一致。

## 推荐安装方式：Git 仓库安装

推荐让 Codex 的 skill 安装路径指向这个 Git 仓库里的 skill 目录：

```bash
git clone https://github.com/rickyk1z1/build-course-canva-deck.git ~/Documents/Codex/build-course-canva-deck
if [ -e ~/.codex/skills/build-course-canva-deck ] || [ -L ~/.codex/skills/build-course-canva-deck ]; then
  mv ~/.codex/skills/build-course-canva-deck ~/.codex/skills/build-course-canva-deck.backup-$(date +%Y%m%d%H%M%S)
fi
ln -s ~/Documents/Codex/build-course-canva-deck/skills/build-course-canva-deck ~/.codex/skills/build-course-canva-deck
```

之后更新 skill 只需要：

```bash
cd ~/Documents/Codex/build-course-canva-deck
git pull
```

安装或更新后重启 Codex，然后使用：

```text
$build-course-canva-deck
```

## 备选安装方式：Skill Installer

如果不需要本地 Git 管理，也可以用 Codex 自带安装器直接安装：

```bash
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py --repo rickyk1z1/build-course-canva-deck --path skills/build-course-canva-deck
```

这种方式适合一次性安装；如果要长期维护和推送改动，优先使用 Git 仓库安装。

## Agent 层级

当前 skill 使用一个总导演加五个 proposal-only 子代理。总导演先读取完整上下文，再给每个子代理下发裁剪后的任务包。子代理只读任务包允许的文件或摘录，只写 scratch 提案，不写最终文件、不改 Canva、不改源文件。

```text
总导演 / build-course-canva-deck
├── 课程统筹师
├── 原稿场记
├── 课堂编剧
├── 视觉分镜师
└── 成片审片员
```

- `总导演`：唯一负责上下文路由、最终写入、合并、生图执行、构建 PPTX、导入 Canva 和交付。
- `课程统筹师`：确认课程位置、邻课边界、术语和排除主题；默认不读完整源文件。
- `原稿场记`：盯住源大纲顺序、节点分组、同级枚举、源图和保真风险；在任务包允许时读取完整源结构。
- `课堂编剧`：基于已批准的节点摘录和保真计划写可独立理解的屏显文案。
- `视觉分镜师`：基于已批准的文案、源图清单和模板摘录规划案例图、生成图任务、模板页、Canva-native motif 和版式容量。
- `成片审片员`：只审查，不创作；负责任务包边界、allowed-read 合规、顺序、重复、缺失、生图任务和渲染后 QA。

子代理工作过程默认使用中文；JSON key、脚本参数、文件路径、schema enum 和工具标识保持英文。

子代理名称代表同一个逻辑角色，不代表每次调用都新建一个独立身份。重复调用 `课程统筹师`、`原稿场记`、`课堂编剧`、`视觉分镜师` 或 `成片审片员` 时，总导演必须通过 `scratch/agent-state/` 传递上一轮状态、提案和未解决问题；即使运行环境物理上开启了新子代理，也要当作同一 `role_id` 的连续 invocation。

详细职责见 `skills/build-course-canva-deck/references/agent-hierarchy.md`。

## 工作模式

每次读取权威源文件后，必须由用户明确选择：

- `细纲`：保留源大纲顺序、例子、比喻、枚举项、判断和范围。只优化教学表达、页面结构和视觉呈现，不新增相邻专业流程。
- `粗纲`：可以比基准课件更细，但只能沿原知识树纵向补充定义、原因、关系、例子、误区和边界。所有补充必须映射到原节点和证据。

Skill 不会根据文件长度、层级深度或主观判断自动选择模式。

## 关键 QA 规则

- 每个有效源节点必须且只能映射一次。
- `source_node_ids` 不等于覆盖；每个节点都必须有同页可见的 `source_node_treatments.screen_evidence`。
- 构建后的 PPTX 必须在对应页面 XML 中包含同页 `screen_evidence`；只存在于 spec、讲稿、图片或其他页面都不算通过。
- 同一页不同源节点不能复用同一句泛化 evidence，除非源文本本身完全相同。
- 同页 evidence 的首次出现顺序必须符合源大纲顺序。
- 细纲中的同级枚举必须完整、按序、可见；不能被版式 point 上限截掉，也不能只藏在生成图或元数据里。
- 不得把后面节点的特征词提前搬到前面页标题或标签里，除非源大纲本身已经这样重复。
- 详细模式普通知识页最多映射 8 个源节点；粗纲最多 10 个。
- 学员页面不得出现 `PDF`、`原稿`、`制作说明`、`详细讲稿` 等幕后措辞。

## 视觉和 Canva 交付

- 每个普通知识页都要有教学型视觉：源案例图、重绘源图、生成案例图、可编辑图解或表格。
- 优先复用源案例图；缺图或抽象页使用无内嵌中文的生成图，标签用可编辑文字。
- 视觉分镜师只规划 `image_generation_tasks`；总导演负责调用生图工具、保存资产、写入 spec 和构建课件。
- 长 deck 需要模板页映射、模板 motif 计划和版式节奏检查，不能为了套 21 页模板而压缩课程。
- Canva 导入前必须完成模板访问预检。
- 原 Canva 模板不能被修改。
- Canva 导入后要核对页数、富文本、页面预览和 forbidden terms。
- 只有用户明确批准后，才提交 Canva 草稿编辑。

## 主要产物

默认输出到源文件旁边的 `<课程名>-课件产物/`：

- `<课程名>-Canva导入稿.pptx`
- `<课程名>-屏显稿.md`
- `source-map.json`
- `curriculum-context.json`
- `deck-spec.json`
- `source-coverage-matrix.md`
- `qa-report.json`
- `canva-access.json`

## 开发验证

首次在新环境维护仓库时，先安装开发验证依赖：

```bash
python3 -m pip install --user -r requirements-dev.txt
```

运行回归测试：

```bash
python3 skills/build-course-canva-deck/tests/test_audit_deck_density.py
```

检查 `audit_deck.py` 语法：

```bash
python3 -m py_compile skills/build-course-canva-deck/scripts/audit_deck.py
```
