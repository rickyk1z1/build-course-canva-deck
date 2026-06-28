# Non-regression checklist

These are the failure modes that have recurred across many rounds of this skill. They are written in plain language a human verifies on the rendered deck, not as fields or numbers. The audit script does not check these; the director does.

Before delivering any deck, the director goes through every item below against the actual contact sheet and full-size pages, and records the result in `交付前自检.md` in the output folder: for each item, write the slide numbers checked and either "无问题" or the concrete problem found. A checklist with empty or generic answers is not a completed review.

If any item is hit, do not patch only that page. Run the director acceptance lock: mark the deck not approved, trace back to the earliest responsible stage (source grouping → screen copy → visual plan → deck-spec → PPTX/contact sheet → Canva), fix that stage, rebuild, and re-run this whole checklist.

## The checklist

1. **章节骨架缺失** — 看完整 deck:是否先做过源树阅读并记录 `course.chapter_spine`?是否先总领,再每个 approved chapter node 都有固定章节封面,然后才进入该节内容,最后有总结?有没有把上层容器节点误当章节,或把真正章节标题混进普通内容页导致结构不清?
2. **章节封面提前讲结论** — 每张章节封面的小字是否只是这一节将讲的直接子标题/知识点概述?有没有写成“这一节要解决什么”“正确做法是什么”这类结论、承诺或价值判断?
3. **框架进度页脚错误** — 普通内容页左下角是否显示当前 approved chapter heading/知识框架进度?有没有还显示 `线上录课课件`?总领、小节封面、总结页可以没有这个小字。
4. **版式重复** — 看联系页缩略图:结构页固定是一致性,不算问题;但每节内部有没有 ≥3 页内容页几何雷同、只换了颜色或左右位置?换了 `layout_variant` 名字但缩略图看起来一样,仍算重复。`audit_deck.py` 现在会对同一 section 内连续 ≥3 页结构签名相同(layout/是否有图/bullet 数/block 数)发 warning;这只是提示该亲眼看哪几页,不替代肉眼判断。交付前必须把每条几何重复 warning 在联系页上确认掉,要么是真重复就改版,要么确认缩略图几何确有差异。warning 未处理不得交付。
5. **源层级拍平** — detailed 模式下,有没有把源大纲的一级/二级/三级压成一条重排后的脚本?对于包装层较深的 XMind,是否先判断真实章节从三级/四级或更深层开始,而不是机械按一级/二级展开?学员是否还能感到思维导图路径在按章节展开?
6. **同级枚举丢失** — 源节点有四个 peer 子项时,页面是否完整显示四项(或拆成连续页),而不是省略或塞进备注?
7. **后台文字泄漏** — 有没有 `本页顺序`、来源路径、`对应节点`、制作说明类文字出现在学员可见的标题/正文/要点/标注里?有没有“先知道整节课怎么展开”“再进入每一节”这类给制作者捋结构的流程话术,而不是直接教给学员的课程内容?有没有 `不进入软件按钮`、`不讲快捷键`、`不涉及调色` 这类给制作者看的邻课边界/排除项被写成屏显 bullet?
8. **参考讲稿泄漏/越权** — 如果用户同时给了讲稿,它是否只作为屏显文案参考?有没有把讲稿顺序、讲稿缺失/新增内容、录制提示或口播废话当成源覆盖、章节骨架、源图锚点或生图任务?屏显里有没有“根据讲稿整理”“这一段讲的是”“本段讲的是”这类处理痕迹?
9. **参考讲稿喧宾夺主** — 如果参考讲稿让页面更顺口,是否仍然能看出每页来自当前 XMind/大纲节点?有没有为了贴合讲稿而改变源大纲顺序、丢失同级枚举、增加相邻课内容,或把大纲没有承载的口播细节写成课件知识点?
10. **无意义对比/表格** — comparison/table 页的栏标题是否命名了真实关系,而不是 `对比A/B`、`左/右` 这类填充标签?
11. **源图被筛掉 / 放错节点** — authoritative source 里的每张非 thumbnail 源图,是否都保留了 `source_node_id` / `source_path`,并出现在该节点、其祖先或其后代对应的普通知识页里作为教学案例被解释?有没有把源图当 moodboard 先筛选强弱、靠看图重新判断知识点,或因为重复/小字多/看起来不够强就 omit?重复图也要作为局部、对照或连续案例处理;密集图要裁切或重绘,不能直接丢掉。
12. **源图被拼小** — 是否把多张源图先合成为一张 montage/contact sheet/composite 再塞进页面,导致每张图都看不清?多图同页时是否是独立大图/独立面板,且每张图在录课尺寸下能看清关键画面?如果看不清,是否已经拆页或减少文字,而不是继续缩图?
13. **案例图不教学** — 每张案例图是否能让学员直观看到右侧枚举点/知识点的含义?如果只是一个相近场景、漂亮配图、情绪氛围,但看不出每个要点对应的画面细节,要换图或改图。
14. **纯文字页过多** — 有没有很多普通内容页其实可以用案例教学图、前后对比图、错误/正确场景或可编辑图解帮助理解,却被做成纯文字?纯文字例外必须有具体理由。
15. **生成图离题** — 每张生成图,学员能否在三秒内看出它教的是哪个知识点?只是漂亮、符合配色、通用场景的图要换掉。
16. **拥挤/截断** — 有没有页面文字溢出、被压字、或为塞下内容用了 12-13pt?
17. **字号过小** — 正文是否 <16pt、标题是否 <36pt?录课时要看得清。
18. **版面失衡/重叠** — 有没有像内容都挤在上半区、下半区空掉、主块和辅助块比例失调、文字与元素重叠的页面?这类页即使没有脚本 overflow 也失败。
19. **留白和边界失控** — 看 full-size 页面:图片、文字、图解是否意外贴住白/黑/橙色块边缘或页面边缘?案例图是否像被硬贴进矩形,而不是有意识地装在共享舞台里?多图同页时,每张图之间和图到舞台边缘是否有稳定、可读、符合模板气质的呼吸空间?不要只看脚本是否通过,要按平面设计常识判断对齐轴、内边距和负空间是否舒服。
20. **模板理解偏差** — 整套是否只是"套了模板配色的白底通用页",或错误理解成所有元素都要方方正正的块?重点看是否贴近模板的整体布局、对齐轴、色块比例、字号梯度、图片处理和留白。
21. **课程越界** — 有没有抢讲相邻课的主任务,或重复了其它课已完整覆盖的内容?

## Adding to this list

When user feedback reveals a new repeatable failure mode, add it here as a plain-language, learner-verifiable item — not as a new audit field or numeric threshold. This list is the durable memory of "what went wrong before"; keeping it in prose the director must actively check is what stops "this round remembered, next round forgot."
