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

const C = {
  black: "#1C1C1C",
  orange: "#FC6736",
  cream: "#F2EBE3",
  white: "#FFFFFF",
  muted: "#6C6661",
};
const F = {
  title: "站酷高端黑",
  secondary: "思源黑体 CN Light",
  body: "字由点字烈黑",
  deco: "思源黑体 CN Bold",
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
  if (layout === "dark" || layout === "summary") return "dark";
  if (layout === "orange" || layout === "roadmap") return "orange";
  return "light";
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
  addText(slide, item.section || "COURSE / 线上课程", {
    left: 72, top: 54, width: 520, height: 24, size: 13, color: C.orange,
    typeface: F.deco, bold: true,
  });
  addText(slide, item.title, {
    left: 72, top: 160, width: 690, height: 130, size: 68, color: C.orange,
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
}

async function buildImageSlide(presentation, item) {
  const theme = themeFor(item.layout);
  const dark = theme === "dark";
  const slide = presentation.slides.add();
  slide.background.fill = dark ? C.black : theme === "orange" ? C.orange : C.cream;
  addHeader(slide, item, theme);
  const visual = (item.visuals || [])[0];
  const imageLeft = item.layout !== "image-right";
  const imagePosition = imageLeft
    ? { left: 72, top: 205, width: 500, height: 350 }
    : { left: 708, top: 205, width: 500, height: 350 };
  const textLeft = imageLeft ? 620 : 72;
  await addImage(slide, visual, imagePosition, visual?.fit || "contain");
  addCaption(slide, item, theme, { left: imagePosition.left, top: 570, width: imagePosition.width, height: 60 });
  addExplanation(slide, item, theme, { left: textLeft, top: 205, width: 588, height: 135 });
  addText(slide, bulletText(bulletsFor(item), 5), {
    left: textLeft, top: 365, width: 588, height: 245, size: 17,
    color: dark ? C.white : C.black, typeface: F.body, lineSpacing: 1.34,
    name: `bullets-${item.number}`,
  });
  addFooter(slide, item, theme);
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
}

async function main() {
  const slides = spec.slides || [];
  if (!slides.length) throw new Error("deck-spec contains no slides");
  const presentation = Presentation.create({ slideSize: { width: 1280, height: 720 } });
  for (const item of slides) {
    if (item.layout === "cover") await buildCover(presentation, item);
    else if (item.layout === "image-left" || item.layout === "image-right") await buildImageSlide(presentation, item);
    else if (item.layout === "comparison" || item.layout === "table") buildComparison(presentation, item);
    else buildTextSlide(presentation, item);
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
