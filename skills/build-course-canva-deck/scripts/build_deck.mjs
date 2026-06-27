#!/usr/bin/env node
import fs from "node:fs/promises";
import os from "node:os";
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

function resolveFrom(baseFile, moduleName) {
  try {
    return createRequire(baseFile).resolve(moduleName);
  } catch {
    return null;
  }
}

async function resolveArtifactTool(workspace) {
  const moduleName = "@oai/artifact-tool";
  const runtimeNodeModules = path.join(
    os.homedir(),
    ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules",
  );
  const candidates = [
    path.join(workspace, "package.json"),
    path.join(process.cwd(), "package.json"),
    path.join(runtimeNodeModules, "codex-artifact-resolver.js"),
  ];
  for (const candidate of candidates) {
    const resolved = resolveFrom(candidate, moduleName);
    if (resolved) return resolved;
  }
  throw new Error(
    `${moduleName} was not found. Use a scratch workspace with ${moduleName} installed, `
    + "or run inside Codex with the bundled primary runtime available.",
  );
}

const workspace = path.resolve(String(args.workspace));
const artifactEntry = await resolveArtifactTool(workspace);
const { Presentation, PresentationFile } = await import(pathToFileURL(artifactEntry).href);

const specPath = path.resolve(String(args.spec));
const outputPath = path.resolve(String(args.output));
const assetDir = path.resolve(String(args["asset-dir"] || path.dirname(specPath)));
const spec = JSON.parse(await fs.readFile(specPath, "utf8"));

const previewDir = path.join(workspace, "preview");
const layoutDir = path.join(workspace, "layout");
const inspectionDir = path.join(workspace, "inspection");
await Promise.all([
  fs.mkdir(previewDir, { recursive: true }),
  fs.mkdir(layoutDir, { recursive: true }),
  fs.mkdir(inspectionDir, { recursive: true }),
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
  const blocks = Array.isArray(screen.blocks) ? screen.blocks : [];
  const blockItems = blocks.flatMap((block) => {
    const heading = String(block?.heading || "").trim();
    const items = Array.isArray(block?.items) ? block.items : [];
    return items.filter(Boolean).map((item) => {
      const text = typeof item === "string" ? item : item?.text || "";
      return heading ? `${heading}：${text}` : text;
    });
  });
  return [...direct, ...blockItems].filter(Boolean);
}

function bulletText(items, max = 6) {
  const selected = (items || []).filter(Boolean);
  if (selected.length > max) {
    throw new Error(`cover keyword list has ${selected.length} items but this layout supports ${max}; shorten or split the cover keywords`);
  }
  return selected.map((item) => `•  ${typeof item === "string" ? item : item.text || ""}`).join("\n");
}

function splitPoint(item) {
  const raw = String(typeof item === "string" ? item : item?.text || "");
  const parts = raw.split(/[：:]/);
  if (parts.length > 1 && parts[0].length <= 12) {
    return { head: parts[0], body: parts.slice(1).join("：").trim() };
  }
  return { head: "", body: raw };
}

function addAccentMark(slide, { left, top, width = 46, height = 8, fill = C.orange, name }) {
  addBox(slide, { left, top, width, height, fill, name });
}

function addPointList(slide, items, theme, position, options = {}) {
  const {
    max = 4,
    columns = 1,
    numbered = false,
    fill = "none",
    accent = C.orange,
    compact = false,
  } = options;
  const selected = (items || []).filter(Boolean);
  if (selected.length > max) {
    const context = options.context || "point list";
    throw new Error(`${context} has ${selected.length} visible items but this layout supports ${max}; split the slide or choose a layout with enough visible slots`);
  }
  if (!selected.length) return;
  const dark = theme === "dark";
  const columnGap = 22;
  const rowGap = compact ? 10 : 14;
  const colWidth = (position.width - columnGap * (columns - 1)) / columns;
  const rows = Math.ceil(selected.length / columns);
  const rowHeight = (position.height - rowGap * Math.max(0, rows - 1)) / rows;
  selected.forEach((item, index) => {
    const col = index % columns;
    const row = Math.floor(index / columns);
    const left = position.left + col * (colWidth + columnGap);
    const top = position.top + row * (rowHeight + rowGap);
    if (fill !== "none") {
      addBox(slide, { left, top, width: colWidth, height: rowHeight, fill, name: `point-bg-${index}` });
    }
    const point = splitPoint(item);
    const label = point.head || (numbered ? String(index + 1).padStart(2, "0") : "");
    if (label) {
      addText(slide, label, {
        left,
        top,
        width: numbered && !point.head ? 46 : colWidth,
        height: 24,
        size: numbered && !point.head ? 26 : 16,
        color: accent,
        typeface: F.deco,
        bold: true,
        name: `point-label-${index}`,
      });
    } else {
      addAccentMark(slide, { left, top: top + 2, name: `point-mark-${index}` });
    }
    addText(slide, point.body || point.head, {
      left: label && numbered && !point.head ? left + 56 : left,
      top: label ? top + (point.head ? 26 : 2) : top + 16,
      width: label && numbered && !point.head ? colWidth - 56 : colWidth,
      height: rowHeight - (point.head ? 30 : 4),
      size: compact ? 16 : 17,
      color: dark ? C.white : C.black,
      typeface: F.body,
      lineSpacing: 1.18,
      name: `point-body-${index}`,
    });
  });
}

function themeFor(layout) {
  if (layout === "dark" || layout === "summary" || String(layout).endsWith("-dark")) return "dark";
  if (layout === "orange" || layout === "accent" || layout === "roadmap" || layout === "lesson-overview" || layout === "section-cover" || String(layout).endsWith("-orange") || String(layout).endsWith("-accent")) return "orange";
  return "light";
}

function imageSideFor(layout) {
  return String(layout).includes("image-left") ? "left" : "right";
}

function templateReferenceFor(item) {
  return item.visual_plan?.template_reference || item.template_reference || {};
}

function referencePageFor(item) {
  const page = templateReferenceFor(item).page;
  return Number(Array.isArray(page) ? page[0] : page) || 0;
}

function layoutVariantFor(item) {
  const explicit = item.visual_plan?.layout_variant
    || item.visual_plan?.composition_variant
    || templateReferenceFor(item).layout_variant
    || templateReferenceFor(item).composition_family;
  if (explicit) return String(explicit);
  const page = referencePageFor(item);
  if ([3, 18, 21].includes(page)) return "index-grid";
  if ([6].includes(page)) return "wide-case-band";
  if ([7].includes(page)) return "close-reading";
  if ([8].includes(page)) return "poster-panel";
  if ([9].includes(page)) return "dark-spotlight";
  if ([10].includes(page)) return "center-anchor";
  if ([12].includes(page)) return "two-panel";
  if ([14].includes(page)) return "gallery-strip";
  return "split-image";
}

function renderedPatternFor(item) {
  return String(
    item.visual_plan?.rendered_pattern
    || item.visual_plan?.thumbnail_pattern
    || templateReferenceFor(item).rendered_pattern
    || templateReferenceFor(item).thumbnail_pattern
    || layoutVariantFor(item),
  );
}

function addHeader(slide, item, theme) {
  const dark = theme === "dark";
  const fg = dark ? C.white : C.black;
  const section = item.section || "COURSE";
  addText(slide, `${String(item.number).padStart(2, "0")}  ${section}`, {
    left: 72, top: 42, width: 620, height: 22, size: 11, color: C.orange,
    typeface: F.deco, bold: true, name: `eyebrow-${item.number}`,
  });
  const titleLength = String(item.title || "").length;
  const titleSize = titleLength > 30 ? 36 : titleLength > 24 ? 40 : titleLength > 18 ? 46 : 58;
  addText(slide, item.title, {
    left: 72, top: 76, width: 1088, height: 98, size: titleSize,
    color: fg, typeface: F.title, bold: true, name: `title-${item.number}`,
    lineSpacing: 1.02,
  });
  addAccentMark(slide, { left: 72, top: 172, width: 56, height: 7, fill: C.orange, name: `title-mark-${item.number}` });
}

function addFooter(slide, item, theme) {
  const dark = theme === "dark";
  const progress = item.framework_progress_label || item.progress_label || "";
  if (progress) {
    addText(slide, progress, {
      left: 72, top: 684, width: 360, height: 16, size: 10,
      color: dark ? C.white : C.muted, typeface: F.deco,
    });
  }
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

function addExplanation(slide, item, theme, position) {
  const text = screenFor(item).explanation || "";
  const size = text.length > 150 ? 16 : text.length > 105 ? 17 : 18;
  addText(slide, text, {
    ...position, size, color: theme === "dark" ? C.white : C.black,
    typeface: F.body, lineSpacing: 1.22, name: `explanation-${item.number}`,
  });
}

function addCaption(slide, item, theme, position) {
  const caption = screenFor(item).caption || "";
  if (!caption) return;
  const dark = theme === "dark";
  addAccentMark(slide, {
    left: position.left,
    top: position.top,
    width: Math.min(70, position.width * 0.22),
    height: 6,
    fill: C.orange,
    name: `caption-mark-${item.number}`,
  });
  addText(slide, caption, {
    left: position.left,
    top: position.top + 13,
    width: position.width,
    height: Math.max(34, position.height - 13),
    size: 15,
    color: dark ? C.white : C.black,
    typeface: F.deco,
    bold: true,
    valign: "top",
    name: `caption-${item.number}`,
  });
}

async function buildCover(presentation, item) {
  const slide = presentation.slides.add();
  slide.background.fill = C.black;
  addText(slide, item.section || "COURSE / 线上课程", {
    left: 72, top: 54, width: 520, height: 24, size: 13, color: C.orange,
    typeface: F.deco, bold: true,
  });
  addText(slide, item.title, {
    left: 72, top: 155, width: 690, height: 140, size: 72, color: C.orange,
    typeface: F.title, bold: true, name: `title-${item.number}`,
  });
  const screen = screenFor(item);
  addText(slide, screen.explanation || "", {
    left: 72, top: 330, width: 650, height: 160, size: 24, color: C.white,
    typeface: F.secondary, lineSpacing: 1.35,
  });
  addBox(slide, { left: 860, top: -40, width: 300, height: 800, fill: C.orange, name: "cover-orange" });
  addBox(slide, { left: 758, top: 210, width: 470, height: 310, fill: C.cream, name: "cover-focus" });
  addText(slide, bulletText(screen.bullets || [], 6), {
    left: 800, top: 275, width: 390, height: 190, size: 22, color: C.black,
    typeface: F.deco, bold: true, align: "center", valign: "middle", lineSpacing: 1.45,
  });
  addFooter(slide, item, "dark");
  return slide;
}

async function buildLessonOverview(presentation, item) {
  const slide = presentation.slides.add();
  slide.background.fill = C.orange;
  addText(slide, item.section || "COURSE / 章节总领", {
    left: 72, top: 48, width: 560, height: 24, size: 13, color: C.black,
    typeface: F.deco, bold: true,
  });
  addText(slide, item.title, {
    left: 72, top: 110, width: 720, height: 118, size: String(item.title || "").length > 20 ? 48 : 58,
    color: C.black, typeface: F.title, bold: true, lineSpacing: 1.05,
    name: `overview-title-${item.number}`,
  });
  addText(slide, screenFor(item).explanation || "", {
    left: 72, top: 260, width: 640, height: 130, size: 22, color: C.black,
    typeface: F.body, lineSpacing: 1.28, name: `overview-explanation-${item.number}`,
  });
  const points = bulletsFor(item);
  addBox(slide, { left: 790, top: 95, width: 338, height: 438, fill: C.cream, name: `overview-index-field-${item.number}` });
  addText(slide, "本节结构", {
    left: 826, top: 132, width: 260, height: 38, size: 26, color: C.black,
    typeface: F.title, bold: true,
  });
  addPointList(slide, points.slice(0, 6), "light", { left: 826, top: 190, width: 265, height: 285 }, {
    max: 6,
    numbered: true,
    compact: true,
    context: `slide ${item.number} lesson overview sections`,
  });
  addBox(slide, { left: 72, top: 505, width: 640, height: 54, fill: C.black, name: `overview-anchor-${item.number}` });
  addText(slide, screenFor(item).caption || "先知道整节课怎么展开，再进入每一节。", {
    left: 104, top: 522, width: 575, height: 24, size: 18, color: C.white,
    typeface: F.deco, bold: true,
  });
  addFooter(slide, item, "orange");
  return slide;
}

async function buildSectionCover(presentation, item) {
  const slide = presentation.slides.add();
  slide.background.fill = C.black;
  const sectionLabel = item.section_label || item.section || `SECTION ${String(item.number).padStart(2, "0")}`;
  addText(slide, sectionLabel, {
    left: 72, top: 58, width: 580, height: 28, size: 14, color: C.orange,
    typeface: F.deco, bold: true, name: `section-eyebrow-${item.number}`,
  });
  addBox(slide, { left: 0, top: 0, width: 342, height: 720, fill: C.orange, name: `section-color-field-${item.number}` });
  addText(slide, String(item.section_number || item.number).padStart(2, "0"), {
    left: 84, top: 238, width: 160, height: 92, size: 76, color: C.black,
    typeface: F.title, bold: true, name: `section-number-${item.number}`,
  });
  addText(slide, item.title, {
    left: 405, top: 190, width: 690, height: 130, size: String(item.title || "").length > 18 ? 50 : 64,
    color: C.orange, typeface: F.title, bold: true, lineSpacing: 1.05,
    name: `section-title-${item.number}`,
  });
  addText(slide, screenFor(item).explanation || "", {
    left: 410, top: 348, width: 650, height: 92, size: 23, color: C.white,
    typeface: F.secondary, lineSpacing: 1.28, name: `section-explanation-${item.number}`,
  });
  const points = bulletsFor(item);
  if (points.length) {
    addPointList(slide, points.slice(0, 3), "dark", { left: 410, top: 478, width: 650, height: 88 }, {
      max: 3,
      columns: Math.min(3, points.length),
      compact: true,
      context: `slide ${item.number} section cover cues`,
    });
  }
  addFooter(slide, item, "dark");
  return slide;
}

async function buildImageSlide(presentation, item) {
  const theme = themeFor(item.layout);
  const dark = theme === "dark";
  const orange = theme === "orange";
  const variant = layoutVariantFor(item);
  const slide = presentation.slides.add();
  slide.background.fill = dark ? C.black : theme === "orange" ? C.orange : C.cream;
  addHeader(slide, item, theme);
  const visual = (item.visuals || [])[0];
  const imageLeft = imageSideFor(item.layout) === "left";
  let imagePosition = imageLeft
    ? { left: 72, top: 205, width: 620, height: 355 }
    : { left: 588, top: 205, width: 620, height: 355 };
  let captionPosition = { left: imagePosition.left, top: 570, width: imagePosition.width, height: 60 };
  let explanationPosition = { left: imageLeft ? 735 : 72, top: 205, width: 473, height: 135 };
  let bulletsPosition = { left: explanationPosition.left, top: 365, width: explanationPosition.width, height: 245 };
  let textTheme = theme;
  let textPanel = null;
  let imageFrame = dark ? {
    left: imagePosition.left - 16,
    top: imagePosition.top - 16,
    width: imagePosition.width + 32,
    height: imagePosition.height + 32,
    fill: C.cream,
  } : null;

  if (variant === "wide-case-band") {
    imagePosition = { left: 72, top: 350, width: 760, height: 205 };
    captionPosition = { left: 72, top: 566, width: 760, height: 52 };
    explanationPosition = { left: 72, top: 208, width: 720, height: 76 };
    bulletsPosition = { left: 870, top: 222, width: 320, height: 330 };
    textPanel = { left: 846, top: 198, width: 362, height: 394, fill: orange ? C.cream : dark ? C.black : C.white };
    imageFrame = dark ? { left: 56, top: 314, width: 792, height: 267, fill: C.cream } : null;
    textTheme = dark ? "dark" : "light";
  } else if (variant === "poster-panel") {
    imagePosition = imageLeft
      ? { left: 72, top: 200, width: 440, height: 370 }
      : { left: 768, top: 200, width: 440, height: 370 };
    captionPosition = { left: imagePosition.left, top: 584, width: imagePosition.width, height: 48 };
    explanationPosition = imageLeft
      ? { left: 560, top: 210, width: 560, height: 86 }
      : { left: 72, top: 210, width: 560, height: 86 };
    bulletsPosition = { left: explanationPosition.left, top: 332, width: 560, height: 220 };
    textPanel = { left: explanationPosition.left - 26, top: 194, width: 616, height: 400, fill: orange ? C.cream : dark ? C.black : C.white };
    imageFrame = dark ? { left: imagePosition.left - 14, top: 186, width: imagePosition.width + 28, height: imagePosition.height + 28, fill: C.cream } : null;
    textTheme = dark ? "dark" : "light";
  } else if (variant === "center-anchor") {
    imagePosition = { left: 270, top: 214, width: 740, height: 265 };
    captionPosition = { left: 270, top: 490, width: 740, height: 45 };
    explanationPosition = { left: 72, top: 562, width: 500, height: 70 };
    bulletsPosition = { left: 625, top: 558, width: 560, height: 92 };
    imageFrame = dark ? { left: 248, top: 192, width: 784, height: 309, fill: C.cream } : { left: 248, top: 192, width: 784, height: 309, fill: orange ? C.cream : C.white };
    textTheme = theme;
  } else if (variant === "gallery-strip") {
    imagePosition = { left: 72, top: 255, width: 710, height: 210 };
    captionPosition = { left: 72, top: 482, width: 710, height: 50 };
    explanationPosition = { left: 826, top: 210, width: 354, height: 90 };
    bulletsPosition = { left: 826, top: 336, width: 354, height: 220 };
    textPanel = { left: 804, top: 194, width: 404, height: 390, fill: orange ? C.cream : dark ? C.black : C.white };
    imageFrame = dark ? { left: 56, top: 239, width: 742, height: 242, fill: C.cream } : null;
    textTheme = dark ? "dark" : "light";
  } else if (variant === "close-reading") {
    imagePosition = imageLeft
      ? { left: 72, top: 210, width: 680, height: 350 }
      : { left: 528, top: 210, width: 680, height: 350 };
    captionPosition = { left: imagePosition.left, top: 574, width: imagePosition.width, height: 48 };
    explanationPosition = imageLeft
      ? { left: 810, top: 220, width: 350, height: 88 }
      : { left: 82, top: 220, width: 350, height: 88 };
    bulletsPosition = { left: explanationPosition.left, top: 345, width: explanationPosition.width, height: 210 };
    textPanel = { left: explanationPosition.left - 24, top: 200, width: explanationPosition.width + 48, height: 370, fill: orange ? C.cream : dark ? C.black : C.white };
    imageFrame = dark ? { left: imagePosition.left - 14, top: 196, width: imagePosition.width + 28, height: imagePosition.height + 28, fill: C.cream } : null;
    textTheme = dark ? "dark" : "light";
  } else if (variant === "dark-spotlight") {
    imagePosition = { left: imageLeft ? 92 : 548, top: 220, width: 560, height: 300 };
    captionPosition = { left: imagePosition.left, top: 535, width: imagePosition.width, height: 52 };
    explanationPosition = { left: imageLeft ? 730 : 72, top: 220, width: 390, height: 94 };
    bulletsPosition = { left: explanationPosition.left, top: 350, width: 390, height: 205 };
    imageFrame = { left: imagePosition.left - 18, top: imagePosition.top - 18, width: imagePosition.width + 36, height: imagePosition.height + 36, fill: C.cream };
    textTheme = "dark";
  } else if (variant === "two-panel") {
    const textLeft = imageLeft ? 724 : 72;
    const imageX = imageLeft ? 72 : 696;
    imagePosition = { left: imageX, top: 220, width: 500, height: 310 };
    captionPosition = { left: imageX, top: 545, width: 500, height: 54 };
    explanationPosition = { left: textLeft, top: 230, width: 410, height: 88 };
    bulletsPosition = { left: textLeft, top: 352, width: 410, height: 210 };
    textPanel = { left: textLeft - 30, top: 205, width: 470, height: 385, fill: orange ? C.cream : dark ? C.black : C.white };
    imageFrame = dark ? { left: imageX - 16, top: 204, width: 532, height: 342, fill: C.cream } : null;
    textTheme = dark ? "dark" : "light";
  } else if (orange) {
    textPanel = {
      left: explanationPosition.left - 24,
      top: 190,
      width: explanationPosition.width + 48,
      height: 420,
      fill: C.cream,
    };
    textTheme = "light";
  }

  if (textPanel) addBox(slide, { ...textPanel, name: `text-field-${variant}-${item.number}` });
  if (imageFrame) addBox(slide, { ...imageFrame, name: `image-field-${variant}-${item.number}` });
  await addImage(slide, visual, imagePosition, visual?.fit || "contain");
  addCaption(slide, item, textTheme, captionPosition);
  addExplanation(slide, item, textTheme, explanationPosition);
  const pointColumns = variant === "center-anchor" ? 3 : 1;
  addPointList(slide, bulletsFor(item), textTheme, bulletsPosition, {
    max: variant === "center-anchor" ? 3 : 4,
    columns: pointColumns,
    numbered: false,
    compact: true,
    context: `slide ${item.number} image-page points`,
  });
  addFooter(slide, item, theme);
  return slide;
}

async function buildComparison(presentation, item) {
  const slide = presentation.slides.add();
  slide.background.fill = C.cream;
  addHeader(slide, item, "light");
  addExplanation(slide, item, "light", { left: 72, top: 205, width: 760, height: 86 });
  const blocks = screenFor(item).blocks || [];
  const left = blocks[0] || { heading: "", items: bulletsFor(item).slice(0, 3) };
  const right = blocks[1] || { heading: "", items: bulletsFor(item).slice(3) };
  addBox(slide, { left: 72, top: 330, width: 520, height: 250, fill: C.black, name: `compare-left-${item.number}` });
  addBox(slide, { left: 628, top: 330, width: 520, height: 250, fill: C.orange, name: `compare-right-${item.number}` });
  addText(slide, left.heading || "", { left: 104, top: 360, width: 456, height: 38, size: 28, color: C.orange, typeface: F.title, bold: true });
  addPointList(slide, left.items || [], "dark", { left: 104, top: 418, width: 430, height: 120 }, { max: 3, numbered: false, compact: true, context: `slide ${item.number} left comparison block` });
  addText(slide, right.heading || "", { left: 660, top: 360, width: 456, height: 38, size: 28, color: C.black, typeface: F.title, bold: true });
  addPointList(slide, right.items || [], "light", { left: 660, top: 418, width: 430, height: 120 }, { max: 3, numbered: false, accent: C.black, compact: true, context: `slide ${item.number} right comparison block` });
  addFooter(slide, item, "light");
  return slide;
}

async function buildTable(presentation, item) {
  const slide = presentation.slides.add();
  slide.background.fill = C.cream;
  addHeader(slide, item, "light");
  addExplanation(slide, item, "light", { left: 72, top: 205, width: 760, height: 78 });
  const blocks = screenFor(item).blocks || [];
  if (blocks.length < 2 || blocks.length > 3) {
    throw new Error(`slide ${item.number} table layout needs 2-3 meaningful columns; split or choose another layout`);
  }
  const maxRows = Math.max(...blocks.map((block) => (block.items || []).length));
  if (maxRows > 4) {
    throw new Error(`slide ${item.number} table has ${maxRows} rows; split the table so all rows remain readable`);
  }
  const left = 72;
  const top = 326;
  const width = 1076;
  const headerHeight = 46;
  const rowHeight = (250 - headerHeight) / Math.max(1, maxRows);
  const gap = 12;
  const colWidth = (width - gap * (blocks.length - 1)) / blocks.length;
  blocks.forEach((block, col) => {
    const colLeft = left + col * (colWidth + gap);
    addBox(slide, { left: colLeft, top, width: colWidth, height: 250, fill: col % 2 === 0 ? C.black : C.orange, name: `table-col-${item.number}-${col}` });
    addText(slide, block.heading || "", {
      left: colLeft + 22, top: top + 16, width: colWidth - 44, height: 28,
      size: 20, color: col % 2 === 0 ? C.orange : C.black, typeface: F.title, bold: true,
      name: `table-head-${item.number}-${col}`,
    });
    (block.items || []).forEach((entry, row) => {
      addText(slide, typeof entry === "string" ? entry : entry?.text || "", {
        left: colLeft + 22,
        top: top + headerHeight + row * rowHeight + 8,
        width: colWidth - 44,
        height: rowHeight - 10,
        size: maxRows >= 4 ? 15 : 16,
        color: col % 2 === 0 ? C.white : C.black,
        typeface: F.body,
        lineSpacing: 1.15,
        name: `table-cell-${item.number}-${col}-${row}`,
      });
    });
  });
  addCaption(slide, item, "light", { left: 72, top: 594, width: 760, height: 46 });
  addFooter(slide, item, "light");
  return slide;
}

async function buildTextSlide(presentation, item) {
  const theme = themeFor(item.layout);
  const dark = theme === "dark";
  const orange = theme === "orange";
  const pattern = renderedPatternFor(item);
  const slide = presentation.slides.add();
  slide.background.fill = dark ? C.black : orange ? C.orange : C.cream;
  addHeader(slide, item, theme);
  if (
    pattern.includes("branch-map")
    || pattern.includes("flow")
    || pattern.includes("roadmap")
    || pattern.includes("route")
  ) {
    addExplanation(slide, item, theme, { left: 72, top: 205, width: 640, height: 82 });
    const points = bulletsFor(item);
    if (points.length > 4) {
      throw new Error(`slide ${item.number} flow pattern has ${points.length} visible points; split into a shorter route page`);
    }
    const railTop = 360;
    const railWidth = 1000;
    addBox(slide, { left: 100, top: railTop + 86, width: railWidth, height: 8, fill: dark ? C.orange : C.black, name: `flow-rail-${item.number}` });
    points.forEach((point, index) => {
      const nodeWidth = 210;
      const gap = (railWidth - nodeWidth * points.length) / Math.max(1, points.length - 1);
      const left = 72 + index * (nodeWidth + Math.max(24, gap));
      const fill = index % 2 === 0 ? (dark ? C.cream : C.black) : C.orange;
      const nodeTheme = index % 2 === 0 && !dark ? "dark" : "light";
      addBox(slide, { left, top: railTop, width: nodeWidth, height: 172, fill, name: `flow-node-${item.number}-${index}` });
      addText(slide, String(index + 1).padStart(2, "0"), {
        left: left + 18,
        top: railTop + 18,
        width: 56,
        height: 32,
        size: 26,
        color: fill === C.black ? C.orange : C.black,
        typeface: F.deco,
        bold: true,
      });
      addText(slide, typeof point === "string" ? point : point?.text || "", {
        left: left + 18,
        top: railTop + 64,
        width: nodeWidth - 36,
        height: 78,
        size: 16,
        color: nodeTheme === "dark" ? C.white : C.black,
        typeface: F.body,
        lineSpacing: 1.15,
        name: `flow-node-text-${item.number}-${index}`,
      });
    });
    addFooter(slide, item, theme);
    return slide;
  }
  if (
    pattern.includes("statement")
    || pattern.includes("principle")
    || pattern.includes("visual-band")
  ) {
    const fieldFill = orange ? C.black : C.orange;
    addBox(slide, { left: 72, top: 220, width: 650, height: 330, fill: fieldFill, name: `statement-field-${item.number}` });
    addText(slide, screenFor(item).explanation || "", {
      left: 108,
      top: 258,
      width: 578,
      height: 210,
      size: 24,
      color: fieldFill === C.black ? C.white : C.black,
      typeface: F.title,
      bold: true,
      lineSpacing: 1.18,
      name: `statement-copy-${item.number}`,
    });
    const points = bulletsFor(item);
    addBox(slide, { left: 780, top: 228, width: 360, height: 126, fill: orange ? C.cream : C.black, name: `statement-support-a-${item.number}` });
    addBox(slide, { left: 780, top: 410, width: 360, height: 126, fill: orange ? C.cream : C.black, name: `statement-support-b-${item.number}` });
    addPointList(slide, points.slice(0, 2), orange ? "light" : "dark", { left: 812, top: 252, width: 300, height: 82 }, {
      max: 2,
      compact: true,
      context: `slide ${item.number} statement support A`,
    });
    addPointList(slide, points.slice(2, 4), orange ? "light" : "dark", { left: 812, top: 434, width: 300, height: 82 }, {
      max: 2,
      compact: true,
      context: `slide ${item.number} statement support B`,
    });
    addFooter(slide, item, theme);
    return slide;
  }
  if (
    pattern.includes("side-rail")
    || pattern.includes("side-panel")
    || pattern.includes("modules")
  ) {
    const sideFill = dark ? C.orange : C.black;
    addBox(slide, { left: 72, top: 205, width: 250, height: 400, fill: sideFill, name: `side-rail-${item.number}` });
    addText(slide, screenFor(item).explanation || "", {
      left: 102,
      top: 250,
      width: 190,
      height: 220,
      size: 22,
      color: sideFill === C.black ? C.white : C.black,
      typeface: F.title,
      bold: true,
      lineSpacing: 1.2,
      name: `side-rail-copy-${item.number}`,
    });
    const points = bulletsFor(item);
    addPointList(slide, points.slice(0, 4), theme, { left: 378, top: 220, width: 760, height: 320 }, {
      max: 4,
      columns: 2,
      fill: orange ? C.cream : dark ? C.black : C.white,
      compact: true,
      context: `slide ${item.number} side-rail modules`,
    });
    addFooter(slide, item, theme);
    return slide;
  }
  addExplanation(slide, item, theme, { left: 72, top: 205, width: 720, height: 90 });
  const points = bulletsFor(item);
  const split = Math.ceil(points.length / 2);
  addBox(slide, { left: 72, top: 365, width: 520, height: 210, fill: dark ? C.orange : C.black, name: `left-block-${item.number}` });
  addBox(slide, { left: 624, top: 365, width: 520, height: 210, fill: dark ? C.cream : orange ? C.cream : C.orange, name: `right-block-${item.number}` });
  addPointList(slide, points.slice(0, split), dark ? "light" : "dark", { left: 104, top: 398, width: 450, height: 122 }, {
    max: 3,
    numbered: false,
    accent: dark ? C.black : C.orange,
    compact: true,
    context: `slide ${item.number} left text block`,
  });
  addPointList(slide, points.slice(split), "light", { left: 656, top: 398, width: 450, height: 122 }, {
    max: 3,
    numbered: false,
    accent: C.black,
    compact: true,
    context: `slide ${item.number} right text block`,
  });
  addFooter(slide, item, theme);
  return slide;
}

async function main() {
  const slides = spec.slides || [];
  if (!slides.length) throw new Error("deck-spec contains no slides");
  const presentation = Presentation.create({ slideSize: { width: 1280, height: 720 } });
  for (const item of slides) {
    if (item.layout === "cover") await buildCover(presentation, item);
    else if (item.layout === "lesson-overview") await buildLessonOverview(presentation, item);
    else if (item.layout === "section-cover") await buildSectionCover(presentation, item);
    else if (String(item.layout).startsWith("image-left") || String(item.layout).startsWith("image-right")) await buildImageSlide(presentation, item);
    else if (item.layout === "comparison") await buildComparison(presentation, item);
    else if (item.layout === "table") await buildTable(presentation, item);
    else await buildTextSlide(presentation, item);
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
  await fs.writeFile(path.join(inspectionDir, "inspect.ndjson"), inspect.ndjson);
  const pptx = await PresentationFile.exportPptx(presentation);
  await pptx.save(outputPath);
  console.log(JSON.stringify({ output: outputPath, slides: slides.length, previewDir, layoutDir }));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
