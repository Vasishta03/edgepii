import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const workspaceDir = "/home/pixie/Documents/manipal/minor_proj";
const skillDir = "/home/pixie/.codex/plugins/cache/openai-primary-runtime/presentations/26.1026.10807/skills/presentations";
const runtimePython = "/home/pixie/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3";
const buildDir = path.join(workspaceDir, "presentation", ".build");
const outputDir = path.join(workspaceDir, "presentation", "output");
const finalPath = path.join(outputDir, "EdgePII_Presentation_2026-11-03.pptx");
const fontFamily = "Liberation Sans";

const C = {
  navy: "#17324D",
  blue: "#2F638E",
  green: "#176B4F",
  red: "#A43B3B",
  amber: "#A16619",
  text: "#1D2733",
  muted: "#637083",
  line: "#D8DEE5",
  light: "#F4F6F8",
  white: "#FFFFFF",
};

async function writeBlob(filePath, blob) {
  await fs.writeFile(filePath, new Uint8Array(await blob.arrayBuffer()));
}

function addText(slide, text, left, top, width, height, options = {}) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    position: { left, top, width, height },
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  shape.text = text;
  shape.text.style = {
    typeface: fontFamily,
    fontSize: options.fontSize ?? 22,
    bold: options.bold ?? false,
    color: options.color ?? C.text,
    alignment: options.alignment ?? "left",
  };
  return shape;
}

function addRect(slide, left, top, width, height, options = {}) {
  return slide.shapes.add({
    geometry: options.geometry ?? "rect",
    position: { left, top, width, height },
    fill: options.fill ?? C.white,
    line: {
      style: "solid",
      fill: options.line ?? C.line,
      width: options.lineWidth ?? 1,
    },
  });
}

function addTitle(slide, title, number) {
  addText(slide, title, 64, 42, 1080, 52, { fontSize: 31, bold: true, color: C.navy });
  addText(slide, String(number).padStart(2, "0"), 1170, 49, 46, 30, {
    fontSize: 13,
    bold: true,
    color: C.muted,
    alignment: "right",
  });
  const rule = addRect(slide, 64, 102, 1152, 2, { fill: C.navy, line: C.navy, lineWidth: 0 });
  rule.name = "title-rule";
}

function addSource(slide, source) {
  addText(slide, source, 64, 682, 1100, 20, { fontSize: 10, color: C.muted });
}

function addBullet(slide, text, left, top, width, options = {}) {
  addText(slide, "•", left, top, 24, 30, { fontSize: options.fontSize ?? 20, bold: true, color: options.color ?? C.green });
  addText(slide, text, left + 28, top, width - 28, options.height ?? 64, {
    fontSize: options.fontSize ?? 20,
    color: options.textColor ?? C.text,
    bold: options.bold ?? false,
  });
}

function styleTable(table, headerColor = C.navy) {
  table.borders.assign({ style: "solid", fill: C.line, width: 1 });
  for (let column = 0; column < table.columns.length; column += 1) {
    const cell = table.getCell(0, column);
    cell.fill = headerColor;
    cell.text.style = { typeface: fontFamily, fontSize: 14, bold: true, color: C.white, alignment: "center" };
  }
  for (let row = 1; row < table.rows.length; row += 1) {
    for (let column = 0; column < table.columns.length; column += 1) {
      const cell = table.getCell(row, column);
      cell.fill = row % 2 === 0 ? C.light : C.white;
      cell.text.style = {
        typeface: fontFamily,
        fontSize: 14,
        color: C.text,
        alignment: column === 0 ? "left" : "center",
      };
    }
  }
}

const presentation = Presentation.create({ slideSize: { width: 1280, height: 720 } });
presentation.theme.defaultFont = fontFamily;

// 1. Title
{
  const slide = presentation.slides.add();
  slide.background.fill = C.white;
  addRect(slide, 0, 0, 22, 720, { fill: C.navy, line: C.navy, lineWidth: 0 });
  addText(slide, "EdgePII", 86, 142, 800, 68, { fontSize: 48, bold: true, color: C.navy });
  addText(slide, "Lightweight Context-Aware PII Detection for Local Inference", 86, 226, 980, 92, {
    fontSize: 30,
    color: C.text,
  });
  addText(slide, "Vasishta Nandipati", 86, 408, 310, 32, { fontSize: 19, bold: true });
  addText(slide, "Karthikeya Davasam", 410, 408, 310, 32, { fontSize: 19, bold: true });
  addText(slide, "Tirth Koradia", 752, 408, 260, 32, { fontSize: 19, bold: true });
  addText(slide, "Manipal Institute of Technology, Manipal", 86, 462, 720, 34, { fontSize: 18, color: C.muted });
  addText(slide, "Minor Project Presentation", 86, 614, 360, 30, { fontSize: 15, color: C.green, bold: true });
}

// 2. Research problem
{
  const slide = presentation.slides.add();
  slide.background.fill = C.white;
  addTitle(slide, "Research problem", 2);
  addText(slide, "Remote language model prompts can contain personal details that the task does not need.", 72, 142, 520, 96, { fontSize: 25, bold: true, color: C.text });
  addBullet(slide, "Blanket masking reduces disclosure but may remove useful context.", 72, 282, 520, { fontSize: 19 });
  addBullet(slide, "Context-aware retention adds utility but can expose sensitive information when detection or relevance fails.", 72, 365, 520, { fontSize: 19, height: 88 });
  addRect(slide, 660, 150, 2, 420, { fill: C.line, line: C.line, lineWidth: 0 });
  addText(slide, "RQ1", 712, 158, 90, 38, { fontSize: 22, bold: true, color: C.green });
  addText(slide, "What is the smallest tested transformer that maintains detection and relevance quality under local resource constraints?", 712, 202, 470, 118, { fontSize: 20 });
  addText(slide, "RQ2", 712, 368, 90, 38, { fontSize: 22, bold: true, color: C.green });
  addText(slide, "How does additional PII training data affect accuracy and computational cost?", 712, 412, 470, 92, { fontSize: 20 });
  addSource(slide, "Scope: local CPU inference using MiniLM, DistilBERT, and BERT-base");
}

// 3. System design
{
  const slide = presentation.slides.add();
  slide.background.fill = C.white;
  addTitle(slide, "System design", 3);
  const steps = [
    ["1", "Input", "Context and task question"],
    ["2", "Detect", "PII spans and entity types"],
    ["3", "Score", "Relevance for each entity"],
    ["4", "Mask", "Policy and frozen threshold"],
    ["5", "Review", "Protected local output"],
  ];
  const width = 205;
  const gap = 25;
  for (let i = 0; i < steps.length; i += 1) {
    const left = 66 + i * (width + gap);
    addText(slide, steps[i][0], left, 166, 48, 38, { fontSize: 28, bold: true, color: C.green });
    addText(slide, steps[i][1], left, 220, width, 38, { fontSize: 23, bold: true, color: C.navy });
    addText(slide, steps[i][2], left, 274, width, 86, { fontSize: 17, color: C.text });
    if (i < steps.length - 1) addRect(slide, left + width, 236, gap, 2, { fill: C.line, line: C.line, lineWidth: 0 });
  }
  addRect(slide, 66, 410, 1148, 1, { fill: C.line, line: C.line, lineWidth: 0 });
  addBullet(slide, "Sliding windows cover long contexts and average repeated token offsets before one global BIO decode.", 80, 446, 1080, { fontSize: 19 });
  addBullet(slide, "The demonstration defaults to masking every detected entity. Context-aware retention requires an explicit choice.", 80, 524, 1080, { fontSize: 19 });
  addSource(slide, "Implementation: src/edgepii/modeling.py, src/edgepii/demo.py");
}

// 4. Data and protocol
{
  const slide = presentation.slides.add();
  slide.background.fill = C.white;
  addTitle(slide, "Data and experimental protocol", 4);
  const table = slide.tables.add({
    rows: 3,
    columns: 5,
    left: 66,
    top: 152,
    width: 730,
    height: 175,
    values: [
      ["Source", "Train", "Validation", "Test", "Reddit"],
      ["AI4Privacy v2", "34,801", "4,347", "4,349", "None"],
      ["CAPID retained", "1,813", "180", "191", "122"],
    ],
  });
  styleTable(table);
  addText(slide, "Common controls", 856, 150, 300, 34, { fontSize: 22, bold: true, color: C.navy });
  addBullet(slide, "Seeds 42, 43, 44 for pilots", 856, 204, 330, { fontSize: 17, height: 48 });
  addBullet(slide, "Strict typed span F1", 856, 264, 330, { fontSize: 17, height: 48 });
  addBullet(slide, "Validation-only checkpoint and threshold selection", 856, 324, 330, { fontSize: 17, height: 68 });
  addText(slide, "Reduced scaling study", 66, 392, 420, 34, { fontSize: 22, bold: true, color: C.navy });
  addBullet(slide, "5K and 10K requested AI4Privacy documents, seed 42", 66, 446, 520, { fontSize: 18 });
  addBullet(slide, "Complete 4,349-document research-v2 test split", 66, 516, 520, { fontSize: 18 });
  addText(slide, "Declared limitation", 664, 410, 300, 34, { fontSize: 20, bold: true, color: C.amber });
  addText(slide, "The 25K, full-data, multiseed scaling matrix was not feasible on the CPU-only laptop.", 664, 458, 500, 92, { fontSize: 18 });
  addSource(slide, "Sources: data manifests, docs/PROTOCOL.md, results/data_audit.json");
}

// 5. Pilot results
{
  const slide = presentation.slides.add();
  slide.background.fill = C.white;
  addTitle(slide, "Three-seed pilot results", 5);
  slide.charts.add("bar", {
    position: { left: 62, top: 142, width: 760, height: 460 },
    categories: ["MiniLM", "DistilBERT", "BERT"],
    series: [
      { name: "CAPID detection F1", values: [0.504, 0.729, 0.771], fill: C.navy },
      { name: "Relevance macro-F1", values: [0.705, 0.738, 0.628], fill: C.green },
    ],
    hasLegend: true,
    legend: { position: "bottom", textStyle: { fontSize: 14 } },
    barOptions: { direction: "column", grouping: "clustered", gapWidth: 70 },
    yAxis: {
      min: 0,
      max: 1,
      majorUnit: 0.2,
      numberFormatCode: "0.0",
      textStyle: { fontSize: 12 },
      majorGridlines: { style: "solid", fill: C.line, width: 1 },
    },
    xAxis: { textStyle: { fontSize: 13 } },
    dataLabels: { showValue: true, position: "outEnd", numberFormatCode: "0.000", textStyle: { fontSize: 12 } },
    chartFill: C.white,
    chartLine: { fill: C.white, width: 0 },
  });
  addText(slide, "Interpretation", 872, 158, 300, 34, { fontSize: 22, bold: true, color: C.navy });
  addBullet(slide, "BERT has the strongest CAPID detector.", 872, 218, 320, { fontSize: 17 });
  addBullet(slide, "DistilBERT has the highest mean relevance F1.", 872, 298, 320, { fontSize: 17 });
  addBullet(slide, "BERT seed 43 collapses to the majority baseline and remains in the aggregate.", 872, 378, 320, { fontSize: 17, height: 92, color: C.red });
  addSource(slide, "Source: results/seed_variance_summary.csv");
}

// 6. Scaling
{
  const slide = presentation.slides.add();
  slide.background.fill = C.white;
  addTitle(slide, "Effect of additional training data", 6);
  slide.charts.add("line", {
    position: { left: 66, top: 148, width: 760, height: 450 },
    categories: ["4,930 usable", "9,854 usable"],
    series: [
      { name: "MiniLM", values: [0.9217, 0.9396], line: { fill: C.blue, width: 3 }, marker: { symbol: "circle", size: 8, fill: C.blue } },
      { name: "DistilBERT", values: [0.9414, 0.9573], line: { fill: C.green, width: 3 }, marker: { symbol: "circle", size: 8, fill: C.green } },
      { name: "BERT", values: [0.9425, 0.9592], line: { fill: C.red, width: 3 }, marker: { symbol: "circle", size: 8, fill: C.red } },
    ],
    hasLegend: true,
    legend: { position: "bottom", textStyle: { fontSize: 14 } },
    yAxis: { min: 0.90, max: 0.97, majorUnit: 0.01, numberFormatCode: "0.00", title: { text: "Strict span F1", textStyle: { fontSize: 13 } }, textStyle: { fontSize: 12 }, majorGridlines: { style: "solid", fill: C.line, width: 1 } },
    xAxis: { textStyle: { fontSize: 13 } },
    dataLabels: { showValue: true, position: "top", numberFormatCode: "0.000", textStyle: { fontSize: 12 } },
    chartFill: C.white,
    chartLine: { fill: C.white, width: 0 },
  });
  addText(slide, "Observed change", 870, 158, 310, 34, { fontSize: 22, bold: true, color: C.navy });
  addText(slide, "+0.0179", 870, 224, 150, 48, { fontSize: 30, bold: true, color: C.blue });
  addText(slide, "MiniLM F1", 1028, 235, 160, 30, { fontSize: 16, color: C.muted });
  addText(slide, "+0.0158", 870, 304, 150, 48, { fontSize: 30, bold: true, color: C.green });
  addText(slide, "DistilBERT F1", 1028, 315, 160, 30, { fontSize: 16, color: C.muted });
  addText(slide, "+0.0167", 870, 384, 150, 48, { fontSize: 30, bold: true, color: C.red });
  addText(slide, "BERT F1", 1028, 395, 160, 30, { fontSize: 16, color: C.muted });
  addText(slide, "Training time approximately doubled for every model.", 870, 492, 310, 72, { fontSize: 18, bold: true });
  addSource(slide, "Source: results/scaling_summary.csv. Single seed, fixed epochs.");
}

// 7. Resources
{
  const slide = presentation.slides.add();
  slide.background.fill = C.white;
  addTitle(slide, "Local resource cost", 7);
  const table = slide.tables.add({
    rows: 4,
    columns: 4,
    left: 70,
    top: 154,
    width: 760,
    height: 280,
    values: [
      ["Model", "Median ms", "p95 ms", "Peak RSS MiB"],
      ["MiniLM", "345", "623", "585"],
      ["DistilBERT", "734", "1,127", "870"],
      ["BERT", "1,424", "2,002", "1,192"],
    ],
  });
  styleTable(table);
  addText(slide, "Measured pipeline", 880, 164, 300, 34, { fontSize: 21, bold: true, color: C.navy });
  addText(slide, "Detection, per-entity relevance inference, masking, tokenization, and decoding on CPU.", 880, 214, 300, 120, { fontSize: 18 });
  addText(slide, "Live interface RAM", 70, 492, 320, 34, { fontSize: 21, bold: true, color: C.green });
  addText(slide, "The web page reports current server-process RSS after each run. It does not display training memory.", 70, 538, 710, 72, { fontSize: 18 });
  addText(slide, "DistilBERT uses less local memory and about half BERT's median pipeline latency.", 880, 410, 300, 118, { fontSize: 20, bold: true });
  addSource(slide, "Source: results/*-pipeline-benchmark.json");
}

// 8. Privacy
{
  const slide = presentation.slides.add();
  slide.background.fill = C.white;
  addTitle(slide, "Privacy trade-off", 8);
  const table = slide.tables.add({
    rows: 7,
    columns: 4,
    left: 64,
    top: 148,
    width: 740,
    height: 400,
    values: [
      ["Split", "Model", "Leakage", "Retention"],
      ["Test", "MiniLM", "0.183", "0.454"],
      ["Test", "DistilBERT", "0.127", "0.478"],
      ["Test", "BERT", "0.096", "0.322"],
      ["Reddit", "MiniLM", "0.475", "0.465"],
      ["Reddit", "DistilBERT", "0.350", "0.389"],
      ["Reddit", "BERT", "0.330", "0.395"],
    ],
  });
  styleTable(table, C.red);
  addText(slide, "Primary result", 860, 154, 300, 34, { fontSize: 22, bold: true, color: C.red });
  addText(slide, "The 5% irrelevant-character leakage target is infeasible for every model and seed.", 860, 212, 330, 122, { fontSize: 23, bold: true });
  addText(slide, "Why", 860, 382, 100, 32, { fontSize: 19, bold: true, color: C.navy });
  addText(slide, "Detector misses remain visible even when every detected entity is masked.", 860, 424, 330, 92, { fontSize: 18 });
  addText(slide, "Reddit leakage confirms substantial domain shift.", 860, 554, 330, 52, { fontSize: 18, color: C.muted });
  addSource(slide, "Source: results/adjusted_privacy_summary.csv. Values are three-seed means.");
}

// 9. Error analysis
{
  const slide = presentation.slides.add();
  slide.background.fill = C.white;
  addTitle(slide, "Error analysis", 9);
  slide.charts.add("bar", {
    position: { left: 64, top: 152, width: 720, height: 430 },
    categories: ["MiniLM", "DistilBERT", "BERT"],
    series: [{ name: "Long-context CAPID F1", values: [0.348, 0.720, 0.811], fill: C.navy }],
    hasLegend: false,
    barOptions: { direction: "bar", grouping: "clustered", gapWidth: 65 },
    xAxis: { min: 0, max: 1, majorUnit: 0.2, numberFormatCode: "0.0", textStyle: { fontSize: 12 }, majorGridlines: { style: "solid", fill: C.line, width: 1 } },
    yAxis: { textStyle: { fontSize: 14 } },
    dataLabels: { showValue: true, position: "outEnd", numberFormatCode: "0.000", textStyle: { fontSize: 13 } },
    chartFill: C.white,
    chartLine: { fill: C.white, width: 0 },
  });
  addText(slide, "Observed failure modes", 842, 164, 350, 34, { fontSize: 22, bold: true, color: C.navy });
  addBullet(slide, "Missed entities set the leakage floor.", 842, 224, 350, { fontSize: 17 });
  addBullet(slide, "One entity may split into several predicted spans.", 842, 296, 350, { fontSize: 17 });
  addBullet(slide, "Entity types can be wrong even when the sensitive string is fully masked.", 842, 378, 350, { fontSize: 17, height: 88 });
  addBullet(slide, "BERT relevance training is unstable across seeds.", 842, 480, 350, { fontSize: 17 });
  addSource(slide, "Source: results/ERROR_ANALYSIS.md");
}

// 10. Demo
{
  const slide = presentation.slides.add();
  slide.background.fill = C.white;
  addTitle(slide, "Live demonstration", 10);
  addText(slide, "Recommended setup", 70, 148, 320, 34, { fontSize: 22, bold: true, color: C.navy });
  addText(slide, "Model: BERT\nPolicy: Mask all detected", 70, 200, 330, 90, { fontSize: 20 });
  addText(slide, "Input", 458, 148, 120, 34, { fontSize: 22, bold: true, color: C.navy });
  addText(slide, "My passport number is A1234567. I was born on 14 March 1998.", 458, 202, 720, 86, { fontSize: 21 });
  addRect(slide, 458, 324, 720, 1, { fill: C.line, line: C.line, lineWidth: 0 });
  addText(slide, "Protected output", 458, 356, 260, 34, { fontSize: 22, bold: true, color: C.green });
  addText(slide, "My passport number is [REDACTED]. I was born on [REDACTED].", 458, 410, 720, 92, { fontSize: 21, bold: true });
  addText(slide, "Why BERT for the demo", 70, 352, 320, 34, { fontSize: 20, bold: true, color: C.green });
  addText(slide, "It has the strongest measured CAPID detector and produces the cleanest boundaries on the verified examples.", 70, 402, 320, 118, { fontSize: 18 });
  addText(slide, "The example proves the software path works. Held-out evaluation, not the example, supports the research conclusion.", 70, 558, 1100, 62, { fontSize: 17, color: C.muted });
  addSource(slide, "Guide: docs/DEMO_GUIDE.md");
}

// 11. Conclusions
{
  const slide = presentation.slides.add();
  slide.background.fill = C.white;
  addTitle(slide, "Conclusions", 11);
  addText(slide, "RQ1", 70, 152, 90, 38, { fontSize: 23, bold: true, color: C.green });
  addText(slide, "No model meets every declared criterion. DistilBERT offers the strongest measured accuracy and efficiency compromise.", 168, 148, 980, 86, { fontSize: 23, bold: true });
  addText(slide, "RQ2", 70, 282, 90, 38, { fontSize: 23, bold: true, color: C.green });
  addText(slide, "Increasing usable training data from 4,930 to 9,854 documents improves all three detectors by 0.016 to 0.018 F1 while training time roughly doubles.", 168, 278, 980, 102, { fontSize: 22 });
  addRect(slide, 70, 420, 1080, 1, { fill: C.line, line: C.line, lineWidth: 0 });
  addText(slide, "Main limitation", 70, 458, 220, 34, { fontSize: 21, bold: true, color: C.red });
  addText(slide, "Detector misses make the 5% leakage target infeasible. The system is a research prototype, not a privacy guarantee.", 300, 452, 850, 86, { fontSize: 21, bold: true });
  addText(slide, "Next work: improve recall, stabilize relevance training, and evaluate natural-domain prompts before optional compression.", 70, 590, 1080, 54, { fontSize: 18, color: C.muted });
  addSource(slide, "Paper: paper/ieee/main.pdf");
}

await fs.mkdir(buildDir, { recursive: true });
await fs.mkdir(outputDir, { recursive: true });

for (const [index, slide] of presentation.slides.items.entries()) {
  const fileName = `slide-${String(index + 1).padStart(2, "0")}.png`;
  const rendered = await presentation.export({ slide, format: "png", scale: 1 });
  await writeBlob(path.join(buildDir, fileName), rendered);
}
const montage = await presentation.export({ format: "webp", montage: true });
await writeBlob(path.join(buildDir, "montage.webp"), montage);

const candidatePath = path.join(buildDir, "candidate.pptx");
await (await PresentationFile.exportPptx(presentation)).save(candidatePath);

const { finalizePresentation } = await import(pathToFileURL(
  path.join(skillDir, "container_tools", "artifact_tool_utils.mjs"),
).href);

const requirements = {
  explicitTotalSlideCount: 11,
  requiredNativeTableOwnerSlides: [4, 7, 8],
  requiredNativeChartOwnerSlides: [5, 6, 9],
  materializeLiteralChartWorkbooks: true,
  nativeChartTargetApplication: "powerpoint",
};

await finalizePresentation({
  ...requirements,
  workspaceDir,
  candidatePath,
  finalPath,
  pythonExecutable: runtimePython,
  integrityValidatorPath: path.join(skillDir, "container_tools", "inspect_presentation_package_integrity.py"),
  layoutValidatorPath: path.join(skillDir, "container_tools", "inspect_presentation_layout_geometry.py"),
  layoutArgs: [
    "--expected-slide-size-emu", "12192000,6858000",
    "--validate-bullet-geometry",
    "--validate-heading-fit",
    "--require-native-table-slide", "4",
    "--require-native-table-slide", "7",
    "--require-native-table-slide", "8",
  ],
  requiredNativeTableOwnerSlides: requirements.requiredNativeTableOwnerSlides,
  requiredNativeChartOwnerSlides: requirements.requiredNativeChartOwnerSlides,
  materializeLiteralChartWorkbooks: true,
  nativeChartTargetApplication: "powerpoint",
  fontPolicy: { basis: "design", families: [fontFamily] },
  verifyArtifactToolImport: true,
  receiptPath: path.join(buildDir, "EdgePII_Presentation.validation.json"),
});

console.log(finalPath);
