#!/usr/bin/env node
import fs from "node:fs/promises";
import path from "node:path";
import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";

function argsFrom(argv) {
  const out = {};
  for (let i = 0; i < argv.length; i += 1) {
    if (!argv[i].startsWith("--")) continue;
    const key = argv[i].slice(2);
    const value = argv[i + 1] && !argv[i + 1].startsWith("--") ? argv[++i] : true;
    out[key] = value;
  }
  return out;
}

const args = argsFrom(process.argv.slice(2));
for (const key of ["spec", "output", "workspace"]) {
  if (!args[key]) throw new Error(`Missing --${key}`);
}

const workspace = path.resolve(String(args.workspace));
const requireFromWorkspace = createRequire(path.join(workspace, "package.json"));
const artifactEntry = requireFromWorkspace.resolve("@oai/artifact-tool");
const { Presentation, PresentationFile } = await import(pathToFileURL(artifactEntry).href);

const specPath = path.resolve(String(args.spec));
const outputPath = path.resolve(String(args.output));
const assetDir = path.resolve(String(args["asset-dir"] || path.dirname(specPath)));
const spec = JSON.parse(await fs.readFile(specPath, "utf8"));

const previewDir = path.join(workspace, "preview");
const layoutDir = path.join(workspace, "layout");
const qaDir = path.join(workspace, "qa");
await Promise.all([
  fs.mkdir(previewDir, { recursive: true }),
  fs.mkdir(layoutDir, { recursive: true }),
  fs.mkdir(qaDir, { recursive: true }),
  fs.mkdir(path.dirname(outputPath), { recursive: true }),
]);

const profile = spec.course?.design_profile || {};
const profileColors = profile.colors || {};
const profileFonts = profile.fonts || {};
const C = {
  black: profileColors.dark || profileColors.black || "#1C1C1C",
  orange: profileColors.accent || profileColors.orange || "#FC6736",
  cream: profileColors.light || profileColors.cream || "#F2EBE3",
  white: profileColors.neutral || profileColors.white || "#FFFFFF",
  muted: profileColors.muted || "#6C6661",
};
const F = {
  title: profileFonts.title || "站酷高端黑",
  secondary: profileFonts.secondary || "思源黑体 CN Light",
  body: profileFonts.body || "字由点字烈黑",
  deco: profileFonts.decorative || profileFonts.deco || "思源黑体 CN Bold",
};

function addBox(slide, { left, top, width, height, fill, name }) {
  return slide.shapes.add({
    geometry: "rect",
    name,
    position: { left, top, width, height },
    fill,
    line: { style: "solid", fill: "none", width: 0 },
  });
}

function addText(slide, text, options) {
  const {
    left, top, width, height, size = 18, color = C.black, typeface = F.body,
    bold = false, align = "left", valign = "top", lineSpacing = 1.2, name,
  } = options;
  const shape = slide.shapes.add({
    geometry: "textbox",
    name,
    position: { left, top, width, height },
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  shape.text = String(text || "");
  shape.text.style = {
    fontSize: size,
    color,
    typeface,
    bold,
    alignment: align,
    verticalAlignment: valign,
    lineSpacing,
    autoFit: "shrinkText",
    insets: { left: 0, right: 0, top: 0, bottom: 0 },
  };
  return shape;
}

function screenFor(slideSpec) {
  return slideSpec.screen || { explanation: "", bullets: [], caption: "", blocks: [] };
}

function bulletsFor(slideSpec) {
  const screen = screenFor(slideSpec);
  const direct = Array.isArray(screen.bullets) ? screen.bullets : [];
  const blockItems = (screen.blocks || []).flatMap((block) => block.items || []);
  return [...direct, ...blockItems].filter(Boolean);
}

function bulletText(items, max = 6) {
  return items.slice(0, max).map((item) => `•  ${typeof item === "string" ? item : item.text || ""}`).join("\n");
}

function themeFor(layout) {
  if (layout === "dark" || layout === "summary" || String(layout).endsWith("-dark")) return "dark";
  if (layout === "orange" || layout === "accent" || layout === "roadmap" || String(layout).endsWith("-orange") || String(layout).endsWith("-accent")) return "orange";
  return "light";
}

function imageSideFor(layout) {
  return String(layout).includes("image-left") ? "left" : "right";
}

function addHeader(slide, item, theme) {
  const dark = theme === "dark";
  const fg = dark ? C.white : C.black;
  const section = item.section || "COURSE";
  addText(slide, `${String(item.number).padStart(2, "0")}  ${section}`, {
    left: 72, top: 42, width: 620, height: 24, size: 12, color: C.orange,
    typeface: F.deco, bold: true, name: `eyebrow-${item.number}`,
  });
  const titleSize = String(item.title || "").length > 24 ? 35 : 42;
  addText(slide, item.title, {
    left: 72, top: 80, width: 1136, height: 66, size: titleSize,
    color: fg, typeface: F.title, bold: true, name: `title-${item.number}`,
  });
  addBox(slide, { left: 72, top: 160, width: 1136, height: 2, fill: dark ? C.orange : C.black, name: `rule-${item.number}` });
}

function addFooter(slide, item, theme) {
  const dark = theme === "dark";
  addText(slide, "线上录课课件", {
    left: 72, top: 684, width: 280, height: 16, size: 10,
    color: dark ? C.white : C.muted, typeface: F.deco,
  });
  addText(slide, String(item.number).padStart(2, "0"), {
    left: 1150, top: 680, width: 58, height: 20, size: 12,
    color: dark ? C.orange : C.black, typeface: F.deco, bold: true, align: "right",
  });
}

async function imageInfo(visual) {
  if (!visual?.path) return null;
  const resolved = path.isAbsolute(visual.path) ? visual.path : path.resolve(assetDir, visual.path);
  const bytes = await fs.readFile(resolved);
  const ext = path.extname(resolved).toLowerCase();
  const contentType = ext === ".jpg" || ext === ".jpeg" ? "image/jpeg" : ext === ".webp" ? "image/webp" : "image/png";
  return { bytes: bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength), contentType, alt: visual.alt || "课程案例图" };
}

async function addImage(slide, visual, position, fit = "cover") {
  const info = await imageInfo(visual);
  if (!info) return null;
  return slide.images.add({ blob: info.bytes, contentType: info.contentType, alt: info.alt, fit, position });
}

function motifFor(item) {
  return item.template_motif || item.visual_plan?.template_motif || null;
}

function splitCoverTitle(title) {
  const text = String(title || "");
  if (text.includes("决定")) return text.replace("决定", "\n决定");
  if (text.length <= 14) return text;
  const punctuation = ["，", "、", "：", "｜", "|", " "];
  const middle = Math.floor(text.length / 2);
  let best = -1;
  for (const mark of punctuation) {
    let index = text.indexOf(mark);
    while (index !== -1) {
      if (index > 4 && index < text.length - 4 && (best === -1 || Math.abs(index - middle) < Math.abs(best - middle))) {
        best = index + 1;
      }
      index = text.indexOf(mark, index + 1);
    }
  }
  if (best !== -1) return `${text.slice(0, best)}\n${text.slice(best)}`;
  return `${text.slice(0, middle)}\n${text.slice(middle)}`;
}

function coverKeywordLines(bullets) {
  const items = (bullets || []).filter(Boolean);
  if (items.length <= 2) return items.join("   /   ");
  const split = Math.ceil(items.length / 2);
  return `${items.slice(0, split).join("   /   ")}\n${items.slice(split).join("   /   ")}`;
}

async function addTemplateMotifPreview(slide, item) {
  const motif = motifFor(item);
  if (!motif) return;
  const previewPath = motif.local_preview_path || motif.localPreviewPath;
  const motifLayout = motif.local_ppt_layout || motif.localPptLayout || {};
  const motifBox = motifLayout.motif_box || motifLayout.motifBox || {};
  if (!previewPath || typeof motifBox.left !== "number" || typeof motifBox.top !== "number") return;
  await addImage(slide, { path: previewPath, alt: motif.alt || "模板原生元素预览" }, {
    left: motifBox.left,
    top: motifBox.top,
    width: motifBox.width,
    height: motifBox.height,
  }, motif.fit || "contain");
}

function addExplanation(slide, item, theme, position) {
  const text = screenFor(item).explanation || "";
  const size = text.length > 150 ? 16 : text.length > 105 ? 18 : 20;
  addText(slide, text, {
    ...position, size, color: theme === "dark" ? C.white : C.black,
    typeface: F.body, lineSpacing: 1.28, name: `explanation-${item.number}`,
  });
}

function addCaption(slide, item, theme, position) {
  const caption = screenFor(item).caption || "";
  if (!caption) return;
  addBox(slide, { ...position, fill: theme === "dark" ? C.orange : C.black, name: `caption-bg-${item.number}` });
  addText(slide, caption, {
    left: position.left + 18, top: position.top + 10,
    width: position.width - 36, height: position.height - 20,
    size: 14, color: theme === "dark" ? C.black : C.white,
    typeface: F.body, bold: true, valign: "middle", name: `caption-${item.number}`,
  });
}

async function buildCover(presentation, item) {
  const slide = presentation.slides.add();
  slide.background.fill = C.black;
  const motif = motifFor(item);
  const heroRightMotif = motif?.kind === "hero-right";
  const motifLayout = motif?.local_ppt_layout || motif?.localPptLayout || {};
  const motifBox = motifLayout.motif_box || motifLayout.motifBox || {};
  const textColumnWidth = motifLayout.text_column_width || motifLayout.textColumnWidth || 560;
  const titleBox = heroRightMotif
    ? { left: 72, top: 150, width: textColumnWidth, height: 170, size: 56, text: splitCoverTitle(item.title) }
    : { left: 72, top: 160, width: 690, height: 130, size: 68, text: item.title };
  const explanationBox = heroRightMotif
    ? { left: 72, top: 360, width: textColumnWidth, height: 170, size: 22 }
    : { left: 72, top: 330, width: 650, height: 160, size: 24 };
  addText(slide, item.section || "COURSE / 线上课程", {
    left: 72, top: 54, width: 520, height: 24, size: 13, color: C.orange,
    typeface: F.deco, bold: true,
  });
  addText(slide, titleBox.text, {
    left: titleBox.left, top: titleBox.top, width: titleBox.width, height: titleBox.height,
    size: titleBox.size, color: C.orange,
    typeface: F.title, bold: true, name: `title-${item.number}`,
  });
  const screen = screenFor(item);
  addText(slide, screen.explanation || "", {
    left: explanationBox.left, top: explanationBox.top, width: explanationBox.width,
    height: explanationBox.height, size: explanationBox.size, color: C.white,
    typeface: F.secondary, lineSpacing: 1.35,
  });
  if (heroRightMotif) {
    const previewPath = motif.local_preview_path || motif.localPreviewPath;
    if (previewPath) {
      await addImage(slide, { path: previewPath, alt: motif.alt || "模板装饰素材" }, {
        left: motifBox.left ?? motif.left ?? 680,
        top: motifBox.top ?? motif.top ?? 60,
        width: motifBox.width ?? motif.width ?? 600,
        height: motifBox.height ?? motif.height ?? 600,
      }, motif.fit || "contain");
    }
    addText(slide, coverKeywordLines(screen.bullets || []), {
      left: 72, top: 555, width: textColumnWidth, height: 58, size: 15, color: C.orange,
      typeface: F.deco, bold: true, name: `cover-keywords-${item.number}`,
    });
  } else {
    addBox(slide, { left: 860, top: -40, width: 300, height: 800, fill: C.orange, name: "cover-orange" });
    addBox(slide, { left: 758, top: 210, width: 470, height: 310, fill: C.cream, name: "cover-focus" });
    addText(slide, bulletText(screen.bullets || [], 6), {
      left: 800, top: 275, width: 390, height: 190, size: 22, color: C.black,
      typeface: F.deco, bold: true, align: "center", valign: "middle", lineSpacing: 1.45,
    });
  }
  addFooter(slide, item, "dark");
  return slide;
}

async function buildImageSlide(presentation, item) {
  const theme = themeFor(item.layout);
  const dark = theme === "dark";
  const orange = theme === "orange";
  const slide = presentation.slides.add();
  slide.background.fill = dark ? C.black : theme === "orange" ? C.orange : C.cream;
  addHeader(slide, item, theme);
  const visual = (item.visuals || [])[0];
  const imageLeft = imageSideFor(item.layout) === "left";
  const imagePosition = imageLeft
    ? { left: 72, top: 205, width: 620, height: 355 }
    : { left: 588, top: 205, width: 620, height: 355 };
  const textLeft = imageLeft ? 735 : 72;
  const textWidth = 473;
  if (orange) {
    addBox(slide, {
      left: textLeft - 24, top: 190, width: textWidth + 48, height: 420,
      fill: C.cream, name: `orange-text-field-${item.number}`,
    });
  }
  if (dark) {
    addBox(slide, {
      left: imagePosition.left - 16, top: imagePosition.top - 16,
      width: imagePosition.width + 32, height: imagePosition.height + 32,
      fill: C.cream, name: `dark-image-field-${item.number}`,
    });
  }
  await addImage(slide, visual, imagePosition, visual?.fit || "contain");
  addCaption(slide, item, theme, { left: imagePosition.left, top: 570, width: imagePosition.width, height: 60 });
  addExplanation(slide, item, theme, { left: textLeft, top: 205, width: textWidth, height: 135 });
  addText(slide, bulletText(bulletsFor(item), 5), {
    left: textLeft, top: 365, width: textWidth, height: 245, size: 17,
    color: dark ? C.white : C.black, typeface: F.body, lineSpacing: 1.34,
    name: `bullets-${item.number}`,
  });
  addFooter(slide, item, theme);
  return slide;
}

function buildComparison(presentation, item) {
  const slide = presentation.slides.add();
  slide.background.fill = C.cream;
  addHeader(slide, item, "light");
  addExplanation(slide, item, "light", { left: 72, top: 195, width: 1136, height: 105 });
  const blocks = screenFor(item).blocks || [];
  const left = blocks[0] || { heading: "对比 A", items: bulletsFor(item).slice(0, 3) };
  const right = blocks[1] || { heading: "对比 B", items: bulletsFor(item).slice(3) };
  addBox(slide, { left: 72, top: 330, width: 544, height: 280, fill: C.black, name: `compare-left-${item.number}` });
  addBox(slide, { left: 640, top: 330, width: 568, height: 280, fill: C.orange, name: `compare-right-${item.number}` });
  addText(slide, left.heading || "", { left: 100, top: 360, width: 488, height: 40, size: 25, color: C.orange, typeface: F.secondary });
  addText(slide, bulletText(left.items || [], 5), { left: 100, top: 420, width: 488, height: 160, size: 17, color: C.white, typeface: F.body, lineSpacing: 1.32 });
  addText(slide, right.heading || "", { left: 668, top: 360, width: 512, height: 40, size: 25, color: C.black, typeface: F.secondary });
  addText(slide, bulletText(right.items || [], 5), { left: 668, top: 420, width: 512, height: 160, size: 17, color: C.black, typeface: F.body, lineSpacing: 1.32 });
  addFooter(slide, item, "light");
  return slide;
}

function buildTextSlide(presentation, item) {
  const theme = themeFor(item.layout);
  const dark = theme === "dark";
  const orange = theme === "orange";
  const slide = presentation.slides.add();
  slide.background.fill = dark ? C.black : orange ? C.orange : C.cream;
  addHeader(slide, item, theme);
  addExplanation(slide, item, theme, { left: 72, top: 205, width: 760, height: 145 });
  addText(slide, String(item.number).padStart(2, "0"), {
    left: 990, top: 185, width: 218, height: 150, size: 100,
    color: dark ? C.orange : C.black, typeface: F.title, bold: true,
    align: "right", valign: "middle",
  });
  const points = bulletsFor(item);
  const split = Math.ceil(points.length / 2);
  addBox(slide, { left: 72, top: 390, width: 544, height: 225, fill: dark ? C.orange : C.black, name: `left-block-${item.number}` });
  addBox(slide, { left: 640, top: 390, width: 568, height: 225, fill: dark ? C.cream : orange ? C.cream : C.orange, name: `right-block-${item.number}` });
  addText(slide, bulletText(points.slice(0, split), 4), {
    left: 100, top: 420, width: 488, height: 170, size: 17,
    color: dark ? C.black : C.white, typeface: F.body, lineSpacing: 1.34,
  });
  addText(slide, bulletText(points.slice(split), 4), {
    left: 668, top: 420, width: 512, height: 170, size: 17,
    color: C.black, typeface: F.body, lineSpacing: 1.34,
  });
  addFooter(slide, item, theme);
  return slide;
}

async function main() {
  const slides = spec.slides || [];
  if (!slides.length) throw new Error("deck-spec contains no slides");
  const presentation = Presentation.create({ slideSize: { width: 1280, height: 720 } });
  for (const item of slides) {
    let slide;
    if (item.layout === "cover") slide = await buildCover(presentation, item);
    else if (String(item.layout).startsWith("image-left") || String(item.layout).startsWith("image-right")) slide = await buildImageSlide(presentation, item);
    else if (item.layout === "comparison" || item.layout === "table") slide = buildComparison(presentation, item);
    else slide = buildTextSlide(presentation, item);
    if (item.layout !== "cover") await addTemplateMotifPreview(slide, item);
  }
  for (const [index, slide] of presentation.slides.items.entries()) {
    const stem = `slide-${String(index + 1).padStart(3, "0")}`;
    const png = await presentation.export({ slide, format: "png", scale: 1 });
    await fs.writeFile(path.join(previewDir, `${stem}.png`), new Uint8Array(await png.arrayBuffer()));
    const layout = await slide.export({ format: "layout" });
    await fs.writeFile(path.join(layoutDir, `${stem}.json`), await layout.text());
  }
  const montage = await presentation.export({ format: "webp", montage: true, scale: 1 });
  await fs.writeFile(path.join(previewDir, "deck-montage.webp"), new Uint8Array(await montage.arrayBuffer()));
  const inspect = await presentation.inspect({ kind: "slide,textbox,image,shape,layout", maxChars: 100000 });
  await fs.writeFile(path.join(qaDir, "inspect.ndjson"), inspect.ndjson);
  const pptx = await PresentationFile.exportPptx(presentation);
  await pptx.save(outputPath);
  console.log(JSON.stringify({ output: outputPath, slides: slides.length, previewDir, layoutDir }));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
