# Non-regression checklist

These are the failure modes that have recurred across many rounds of this skill. They are written in plain language a human verifies on the rendered deck, not as fields or numbers. The audit script does not check these; the director does.

Before delivering any deck, the director goes through every item below against the actual contact sheet and full-size pages, and records the result in `交付前自检.md` in the output folder: for each item, write the slide numbers checked and either "无问题" or the concrete problem found. A checklist with empty or generic answers is not a completed review.

If any item is hit, do not patch only that page. Run the director acceptance lock: mark the deck not approved, trace back to the earliest responsible stage (source grouping → screen copy → visual plan → deck-spec → PPTX/contact sheet → Canva), fix that stage, rebuild, and re-run this whole checklist.

## The checklist

1. **章节骨架缺失** — 看完整 deck:是否先总领,再每个二级标题都有固定章节封面,然后才进入该节内容,最后有总结?有没有把章节标题混进普通内容页导致结构不清?
2. **章节封面提前讲结论** — 每张章节封面的小字是否只是这一节将讲的三级标题/知识点概述?有没有写成“这一节要解决什么”“正确做法是什么”这类结论、承诺或价值判断?
3. **版式重复** — 看联系页缩略图:结构页固定是一致性,不算问题;但每节内部有没有 ≥3 页内容页几何雷同、只换了颜色或左右位置?换了 `layout_variant` 名字但缩略图看起来一样,仍算重复。
4. **源层级拍平** — detailed 模式下,有没有把源大纲的一级/二级/三级压成一条重排后的脚本?学员是否还能感到思维导图路径在按章节展开?
5. **同级枚举丢失** — 源节点有四个 peer 子项时,页面是否完整显示四项(或拆成连续页),而不是省略或塞进备注?
6. **后台文字泄漏** — 有没有 `本页顺序`、来源路径、`对应节点`、制作说明类文字出现在学员可见的标题/正文/要点/标注里?
7. **无意义对比/表格** — comparison/table 页的栏标题是否命名了真实关系,而不是 `对比A/B`、`左/右` 这类填充标签?
8. **生成图离题** — 每张生成图,学员能否在三秒内看出它教的是哪个知识点?只是漂亮、符合配色、通用场景的图要换掉。
9. **拥挤/截断** — 有没有页面文字溢出、被压字、或为塞下内容用了 12-13pt?
10. **字号过小** — 正文是否 <16pt、标题是否 <36pt?录课时要看得清。
11. **版面失衡/重叠** — 有没有像内容都挤在上半区、下半区空掉、主块和辅助块比例失调、文字与元素重叠的页面?这类页即使没有脚本 overflow 也失败。
12. **模板理解偏差** — 整套是否只是"套了模板配色的白底通用页",或错误理解成所有元素都要方方正正的块?重点看是否贴近模板的整体布局、对齐轴、色块比例、字号梯度、图片处理和留白。
13. **课程越界** — 有没有抢讲相邻课的主任务,或重复了其它课已完整覆盖的内容?

## Adding to this list

When user feedback reveals a new repeatable failure mode, add it here as a plain-language, learner-verifiable item — not as a new audit field or numeric threshold. This list is the durable memory of "what went wrong before"; keeping it in prose the director must actively check is what stops "this round remembered, next round forgot."
