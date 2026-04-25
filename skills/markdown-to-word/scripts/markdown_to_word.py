from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, cast
from zipfile import ZIP_DEFLATED, ZipFile

import lxml.etree as etree
from docx import Document
from docx.document import Document as DocxDocument
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from docx.styles.style import ParagraphStyle
from docx.text.paragraph import Paragraph


NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
}

SKILL_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = SKILL_ROOT / "templates"
TEMPLATE_MANIFEST_PATH = TEMPLATES_DIR / "manifest.json"
DEFAULT_TEMPLATE_ID = "generic-default"

REFERENCE_MARKER_RE = re.compile(r"(?<!\S)\[\d+\]")
MARKDOWN_HEADING_RE = re.compile(r"^#{1,6}\s+")
NUMBERED_BOLD_LEADIN_RE = re.compile(r"^\d+\.\s*$")
STAR_BULLET_RE = re.compile(r"^\*\s*$")

DEFAULT_MERMAID_CLI_VERSION = "11.4.2"
DEFAULT_MERMAID_STARTERS = (
    "graph",
    "flowchart",
    "sequenceDiagram",
    "classDiagram",
    "stateDiagram",
    "stateDiagram-v2",
    "erDiagram",
    "journey",
    "gantt",
    "pie",
    "gitGraph",
    "mindmap",
    "timeline",
    "requirementDiagram",
    "quadrantChart",
    "xychart-beta",
)

DEFAULT_CONFIG: dict[str, Any] = {
    "name": "markdown-to-word",
    "template": DEFAULT_TEMPLATE_ID,
    "workdir": ".",
    "title_text": "Document Title",
    "input_parts": [],
    "merged_markdown": "merged.md",
    "normalized_output": None,
    "reference_doc": "outputs/reference.docx",
    "reference_template": None,
    "output_docx": "outputs/output.docx",
    "features": {
        "normalize_markdown": True,
        "replace_mermaid": False,
        "normalize_image_wrap": True,
        "normalize_tables": True,
    },
    "style_names": {
        "body": "Normal",
        "title": "Title",
        "heading_1": "Heading 1",
        "heading_2": "Heading 2",
        "heading_3": "Heading 3",
        "heading_4": "Heading 4",
        "caption": "MDW Caption",
        "abstract_label": "MDW Abstract Label",
        "keywords": "MDW Keywords",
        "reference": "MDW Reference",
        "code": "MDW Code",
    },
    "style_profile": {
        "fonts": {
            "normal_east_asia": "等线",
            "normal_ascii": "Times New Roman",
            "title_east_asia": "等线",
            "heading_east_asia": "等线",
            "caption_east_asia": "等线",
            "abstract_label_east_asia": "等线",
            "keywords_east_asia": "等线",
            "reference_east_asia": "等线",
            "code_east_asia": "等线",
            "code_ascii": "Courier New",
        },
        "sizes": {
            "normal": 12,
            "title": 18,
            "heading_1": 18,
            "heading_2": 15,
            "heading_3": 14,
            "heading_4": 12,
            "caption": 10.5,
            "abstract_label": 12,
            "keywords": 12,
            "reference": 12,
            "code": 10.5,
            "footer": 9,
        },
        "page": {
            "top_margin_cm": 3.8,
            "bottom_margin_cm": 3.0,
            "left_margin_cm": 3.0,
            "right_margin_cm": 3.0,
            "header_distance_cm": 3.0,
            "footer_distance_cm": 2.3,
        },
        "paragraph": {
            "body_first_line_indent_pt": 24,
        },
        "caption_paragraph": {
            "default_space_before_lines": 0.5,
            "default_space_after_lines": 0.5,
            "figure_space_before_lines": 0.5,
            "figure_space_after_lines": 0.5,
            "table_space_before_lines": 0.5,
            "table_space_after_lines": 0.5,
        },
        "samples": {
            "heading_1": "Chapter 1 Example Section",
            "heading_2": "1.1 Example Subsection",
            "heading_3": "1.1.1 Example Detail",
            "body": "This is a body text style sample.",
            "caption": "Figure 1-1 Example Caption",
        },
    },
    "detection": {
        "chapter_patterns": [],
        "section_patterns": [],
        "subsection_patterns": [],
        "subsubsection_patterns": [],
        "caption_patterns": [r"^(Figure|Table|图|表)\s*[0-9A-Za-z\-]+"],
        "figure_caption_patterns": [r"^(Figure|图)\s*[0-9A-Za-z\-]+"],
        "table_caption_patterns": [r"^(Table|表)\s*[0-9A-Za-z\-]+"],
        "reference_heading_patterns": [r"^References?$", r"^Bibliography$", r"^参考文献$"],
        "reference_end_prefixes": ["附录", "Appendix"],
        "reference_item_pattern": r"^\[[0-9]+\]",
        "keywords_prefixes": ["关键词：", "Keywords:"],
        "abstract_label_prefixes": ["题目：", "Title:", "摘要：", "Abstract:"],
        "code_style_names": [
            "Source Code",
            "Code Block",
            "Verbatim Char",
            "MDW Code",
            "Thesis Code",
        ],
    },
    "mermaid": {
        "version": DEFAULT_MERMAID_CLI_VERSION,
        "background": "transparent",
        "starters": list(DEFAULT_MERMAID_STARTERS),
    },
}


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            merged[key] = deep_merge(cast(dict[str, Any], base[key]), value)
        else:
            merged[key] = value
    return merged


def resolve_workdir(value: str | None, base_dir: Path) -> Path:
    if not value:
        return Path.cwd()
    path = Path(value)
    if path.is_absolute():
        return path
    return (base_dir / path).resolve()


def resolve_path(value: str | Path | None, workdir: Path) -> Path | None:
    if value is None:
        return None
    path = Path(value)
    if path.is_absolute():
        return path
    return (workdir / path).resolve()


def style_name(settings: dict[str, Any], role: str) -> str:
    return settings["style_names"][role]


def style_name_or_default(settings: dict[str, Any], role: str, default: str) -> str:
    return settings["style_names"].get(role, default)


def is_style_role(paragraph, settings: dict[str, Any], role: str) -> bool:
    return bool(paragraph.style) and paragraph.style.name == style_name(settings, role)


def code_style_names(settings: dict[str, Any]) -> set[str]:
    names = set(settings["detection"]["code_style_names"])
    names.add(style_name(settings, "code"))
    return names


def load_template_manifest() -> dict[str, dict[str, Any]]:
    raw = json.loads(TEMPLATE_MANIFEST_PATH.read_text(encoding="utf-8"))
    templates: dict[str, dict[str, Any]] = {}
    manifest_dir = TEMPLATE_MANIFEST_PATH.parent
    for entry in raw["templates"]:
        resolved = dict(entry)
        resolved["template_path"] = (manifest_dir / entry["template_path"]).resolve()
        resolved["preview_path"] = (manifest_dir / entry["preview_path"]).resolve()
        resolved["sample_path"] = (manifest_dir / entry["sample_path"]).resolve()
        templates[entry["id"]] = resolved
    return templates


def load_template(template_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    templates = load_template_manifest()
    if template_id not in templates:
        available = ", ".join(sorted(templates))
        raise SystemExit(f"Unknown template '{template_id}'. Available templates: {available}")

    entry = templates[template_id]
    template = json.loads(Path(entry["template_path"]).read_text(encoding="utf-8"))
    template["template"] = template_id
    return template, entry


def print_template_list() -> None:
    templates = load_template_manifest()
    for template_id in sorted(templates):
        entry = templates[template_id]
        print(f"{entry['id']}: {entry['name']}")
        print(f"  {entry['description']}")
        languages = ", ".join(entry.get("languages", []))
        use_cases = ", ".join(entry.get("use_cases", []))
        if languages:
            print(f"  Languages: {languages}")
        if use_cases:
            print(f"  Use cases: {use_cases}")
        if entry.get("selection_hint"):
            print(f"  Hint: {entry['selection_hint']}")


def print_template_details(template_id: str) -> None:
    template, entry = load_template(template_id)
    print(f"Template: {entry['id']}")
    print(f"Name: {entry['name']}")
    print(f"Description: {entry['description']}")
    if entry.get("languages"):
        print(f"Languages: {', '.join(entry['languages'])}")
    if entry.get("use_cases"):
        print(f"Use cases: {', '.join(entry['use_cases'])}")
    if entry.get("preferred_input"):
        print(f"Preferred input: {entry['preferred_input']}")
    print(f"Requires title text: {entry.get('requires_title_text', False)}")
    if entry.get("mermaid_caption_policy"):
        print(f"Mermaid caption policy: {entry['mermaid_caption_policy']}")
    if entry.get("selection_hint"):
        print(f"Selection hint: {entry['selection_hint']}")
    print(f"Template file: {entry['template_path']}")
    print(f"Preview file: {entry['preview_path']}")
    print(f"Sample file: {entry['sample_path']}")
    print(f"Default features: {json.dumps(template['features'], ensure_ascii=False)}")


def caption_spacing_lines(text: str, settings: dict[str, Any]) -> tuple[float, float]:
    style_profile = settings["style_profile"]
    caption_paragraph = style_profile.get("caption_paragraph", {})
    detection = settings["detection"]

    if matches_any(detection.get("figure_caption_patterns", []), text):
        return (
            caption_paragraph.get("figure_space_before_lines", 0.5),
            caption_paragraph.get("figure_space_after_lines", 0.5),
        )
    if matches_any(detection.get("table_caption_patterns", []), text):
        return (
            caption_paragraph.get("table_space_before_lines", 0.5),
            caption_paragraph.get("table_space_after_lines", 0.5),
        )
    return (
        caption_paragraph.get("default_space_before_lines", 0.5),
        caption_paragraph.get("default_space_after_lines", 0.5),
    )


def matches_any(patterns: list[str], text: str) -> bool:
    return any(re.match(pattern, text) for pattern in patterns)


def starts_with_any(text: str, prefixes: list[str]) -> bool:
    return any(text.startswith(prefix) for prefix in prefixes)


def is_markdown_heading(text: str) -> bool:
    return bool(MARKDOWN_HEADING_RE.match(text))


def markdown_heading_text(text: str) -> str:
    return MARKDOWN_HEADING_RE.sub("", text).strip()


def is_reference_heading_text(text: str, detection: dict[str, Any]) -> bool:
    return matches_any(detection["reference_heading_patterns"], text)


def merge_markdown_sources(paths: list[Path], output_path: Path) -> None:
    existing_paths = [path for path in paths if path.exists()]
    if not existing_paths:
        raise SystemExit("No markdown input files found to merge.")

    merged_parts: list[str] = []
    for path in existing_paths:
        merged_parts.append(path.read_text(encoding="utf-8").rstrip())

    merged_text = "\n\n".join(part for part in merged_parts if part)
    if merged_text:
        merged_text += "\n"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(merged_text, encoding="utf-8")


def normalize_markdown_for_word(text: str, detection: dict[str, Any]) -> str:
    def split_reference_entries(line: str) -> list[str]:
        matches = list(REFERENCE_MARKER_RE.finditer(line))
        if len(matches) <= 1:
            stripped = line.strip()
            return [stripped] if stripped else []

        entries: list[str] = []
        for idx, match in enumerate(matches):
            end = matches[idx + 1].start() if idx + 1 < len(matches) else len(line)
            entry = line[match.start() : end].strip()
            if entry:
                entries.append(entry)
        return entries

    def line_kind(line: str) -> str:
        stripped = line.strip()
        if not stripped:
            return "blank"
        if re.match(r"^\d+\.\s+", stripped):
            return "ordered"
        if re.match(r"^\*\s+", stripped):
            return "unordered"
        return "other"

    lines = text.splitlines()
    expanded: list[str] = []
    in_fence = False
    in_references = False

    for raw in lines:
        line = raw.rstrip()
        stripped = line.strip()

        if stripped.startswith("```"):
            in_fence = not in_fence
            expanded.append(line)
            continue

        if in_fence:
            expanded.append(line)
            continue

        if is_markdown_heading(stripped):
            heading = markdown_heading_text(stripped)
            if is_reference_heading_text(heading, detection):
                in_references = True
                expanded.append(line)
                continue
            if in_references:
                in_references = False

        if re.match(r"^\s{2,}(?:\*|\d+\.)\s+", line):
            line = line.lstrip()
        elif re.match(r"^\s{4,}\S", line):
            line = line.lstrip()

        if in_references:
            reference_entries = split_reference_entries(line)
            if reference_entries:
                expanded.extend(reference_entries)
            else:
                expanded.append("")
            continue

        line = re.sub(r"(?<=\S)\s+\*\s+(?=\S)", "\n* ", line)

        if "\n" in line:
            expanded.extend(line.split("\n"))
        else:
            expanded.append(line)

    rebuilt: list[str] = []
    for line in expanded:
        kind = line_kind(line)

        prev_nonblank_kind = "start"
        for prev in reversed(rebuilt):
            previous_kind = line_kind(prev)
            if previous_kind != "blank":
                prev_nonblank_kind = previous_kind
                break

        if kind in {"ordered", "unordered"}:
            need_blank = prev_nonblank_kind == "other" or (
                prev_nonblank_kind in {"ordered", "unordered"}
                and prev_nonblank_kind != kind
            )
            if need_blank and rebuilt and rebuilt[-1] != "":
                rebuilt.append("")
            rebuilt.append(line)
            continue

        if kind == "other":
            if (
                prev_nonblank_kind in {"ordered", "unordered"}
                and rebuilt
                and rebuilt[-1] != ""
            ):
                rebuilt.append("")
            rebuilt.append(line)
            continue

        if rebuilt and rebuilt[-1] != "":
            rebuilt.append("")

    normalized = "\n".join(rebuilt)
    if text.endswith("\n"):
        normalized += "\n"
    return normalized


def set_east_asia(target, east_asia: str, ascii_font: str = "Times New Roman") -> None:
    target.font.name = ascii_font
    element: Any = target._element
    rpr = element.find(qn("w:rPr"))
    if rpr is None:
        rpr = OxmlElement("w:rPr")
        element.append(rpr)
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    rfonts.set(qn("w:eastAsia"), east_asia)


def set_style_fonts(
    style: ParagraphStyle,
    east_asia: str,
    size_pt: float,
    bold: bool = False,
    ascii_font: str = "Times New Roman",
) -> None:
    style.font.name = ascii_font
    style.font.size = Pt(size_pt)
    style.font.bold = bold
    style.font.italic = False
    style.font.color.rgb = RGBColor(0, 0, 0)
    element: Any = style._element
    rpr = element.find(qn("w:rPr"))
    if rpr is None:
        rpr = OxmlElement("w:rPr")
        element.append(rpr)
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    rfonts.set(qn("w:eastAsia"), east_asia)


def ensure_style(
    doc: DocxDocument, name: str, base: str | None = None
) -> ParagraphStyle:
    styles = doc.styles
    if name in [style.name for style in styles]:
        return cast(ParagraphStyle, styles[name])
    style = cast(ParagraphStyle, styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH))
    if base:
        style.base_style = styles[base]
    return style


def configure_styles(doc: DocxDocument, settings: dict[str, Any]) -> None:
    style_profile = settings["style_profile"]
    fonts = style_profile["fonts"]
    sizes = style_profile["sizes"]
    paragraph = style_profile.get("paragraph", {})
    body_name = style_name(settings, "body")

    body = ensure_style(doc, body_name)
    set_style_fonts(
        body,
        fonts["normal_east_asia"],
        sizes["normal"],
        ascii_font=fonts["normal_ascii"],
    )
    body_pf = body.paragraph_format
    body_pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    body_pf.line_spacing = 1.25
    body_pf.first_line_indent = Pt(paragraph.get("body_first_line_indent_pt", 24))
    body_pf.space_before = Pt(0)
    body_pf.space_after = Pt(0)
    body_pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    title = ensure_style(doc, style_name(settings, "title"), body_name)
    set_style_fonts(title, fonts["title_east_asia"], sizes["title"], bold=False)
    title.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.paragraph_format.line_spacing_rule = None
    title.paragraph_format.line_spacing = None
    title.paragraph_format.space_before = Pt(12)
    title.paragraph_format.space_after = Pt(6)

    h1 = ensure_style(doc, style_name(settings, "heading_1"), body_name)
    set_style_fonts(h1, fonts["heading_east_asia"], sizes["heading_1"], bold=False)
    h1.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    h1.paragraph_format.first_line_indent = Cm(0)
    h1.paragraph_format.line_spacing_rule = None
    h1.paragraph_format.line_spacing = None
    h1.paragraph_format.space_before = Pt(sizes["heading_1"] * 1.0)
    h1.paragraph_format.space_after = Pt(sizes["heading_1"] * 0.8)
    h1.paragraph_format.keep_with_next = True

    h2 = ensure_style(doc, style_name(settings, "heading_2"), body_name)
    set_style_fonts(h2, fonts["heading_east_asia"], sizes["heading_2"], bold=False)
    h2.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    h2.paragraph_format.first_line_indent = Cm(0)
    h2.paragraph_format.line_spacing_rule = None
    h2.paragraph_format.line_spacing = None
    h2.paragraph_format.space_before = Pt(sizes["heading_2"] * 0.5)
    h2.paragraph_format.space_after = Pt(sizes["heading_2"] * 0.5)
    h2.paragraph_format.keep_with_next = True

    h3 = ensure_style(doc, style_name(settings, "heading_3"), body_name)
    set_style_fonts(h3, fonts["heading_east_asia"], sizes["heading_3"], bold=False)
    h3.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    h3.paragraph_format.first_line_indent = Cm(0)
    h3.paragraph_format.line_spacing_rule = None
    h3.paragraph_format.line_spacing = None
    h3.paragraph_format.space_before = Pt(sizes["heading_3"] * 0.5)
    h3.paragraph_format.space_after = Pt(sizes["heading_3"] * 0.5)
    h3.paragraph_format.keep_with_next = True

    h4 = ensure_style(doc, style_name(settings, "heading_4"), body_name)
    set_style_fonts(h4, fonts["heading_east_asia"], sizes["heading_4"], bold=False)
    h4.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    h4.paragraph_format.first_line_indent = Cm(0)
    h4.paragraph_format.line_spacing_rule = None
    h4.paragraph_format.line_spacing = None
    h4.paragraph_format.space_before = Pt(sizes["heading_4"] * 0.5)
    h4.paragraph_format.space_after = Pt(sizes["heading_4"] * 0.5)
    h4.paragraph_format.keep_with_next = True

    caption = ensure_style(doc, style_name(settings, "caption"), body_name)
    set_style_fonts(caption, fonts["caption_east_asia"], sizes["caption"])
    caption.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption.paragraph_format.first_line_indent = Cm(0)
    caption.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    caption.paragraph_format.line_spacing = Pt(20)
    default_before, default_after = caption_spacing_lines(
        style_profile["samples"]["caption"], settings
    )
    caption.paragraph_format.space_before = Pt(sizes["caption"] * default_before)
    caption.paragraph_format.space_after = Pt(sizes["caption"] * default_after)

    abstract_head = ensure_style(doc, style_name(settings, "abstract_label"), body_name)
    set_style_fonts(
        abstract_head,
        fonts["abstract_label_east_asia"],
        sizes["abstract_label"],
        bold=True,
    )
    abstract_head.paragraph_format.first_line_indent = Cm(0)

    keywords = ensure_style(doc, style_name(settings, "keywords"), body_name)
    set_style_fonts(keywords, fonts["keywords_east_asia"], sizes["keywords"])
    keywords.paragraph_format.first_line_indent = Cm(0)

    reference = ensure_style(doc, style_name(settings, "reference"), body_name)
    set_style_fonts(reference, fonts["reference_east_asia"], sizes["reference"])
    reference.paragraph_format.first_line_indent = Cm(-0.74)
    reference.paragraph_format.left_indent = Cm(0.74)
    reference.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    reference.paragraph_format.line_spacing = Pt(24)
    reference.paragraph_format.space_before = Pt(0)
    reference.paragraph_format.space_after = Pt(0)

    code_style = ensure_style(doc, style_name(settings, "code"), body_name)
    set_style_fonts(
        code_style,
        fonts["code_east_asia"],
        sizes["code"],
        ascii_font=fonts["code_ascii"],
    )
    code_style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    code_style.paragraph_format.first_line_indent = Cm(0)
    code_style.paragraph_format.left_indent = Cm(0.74)
    code_style.paragraph_format.right_indent = Cm(0.74)
    code_style.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    code_style.paragraph_format.line_spacing = Pt(18)
    code_style.paragraph_format.space_before = Pt(6)
    code_style.paragraph_format.space_after = Pt(6)


def set_page_layout(doc: DocxDocument, style_profile: dict[str, Any]) -> None:
    page = style_profile["page"]
    for section in doc.sections:
        section.top_margin = Cm(page["top_margin_cm"])
        section.bottom_margin = Cm(page["bottom_margin_cm"])
        section.left_margin = Cm(page["left_margin_cm"])
        section.right_margin = Cm(page["right_margin_cm"])
        section.header_distance = Cm(page["header_distance_cm"])
        section.footer_distance = Cm(page["footer_distance_cm"])


def clear_paragraph(paragraph) -> None:
    element = paragraph._element
    for child in list(element):
        element.remove(child)


def remove_paragraph(paragraph) -> None:
    element = paragraph._element
    parent = element.getparent()
    if parent is not None:
        parent.remove(element)


def insert_paragraph_after(paragraph, text: str = "", style_name: str | None = None):
    new_paragraph_xml = OxmlElement("w:p")
    paragraph._element.addnext(new_paragraph_xml)
    new_paragraph = Paragraph(new_paragraph_xml, paragraph._parent)
    if style_name:
        new_paragraph.style = paragraph.part.document.styles[style_name]
    if text:
        new_paragraph.add_run(text)
    return new_paragraph


def style_run(
    run,
    east_asia: str,
    size_pt: float,
    ascii_font: str = "Times New Roman",
    bold: bool | None = None,
    italic: bool | None = None,
) -> None:
    run.font.name = ascii_font
    set_east_asia(run, east_asia, ascii_font=ascii_font)
    run.font.size = Pt(size_pt)
    if bold is not None:
        run.font.bold = bold
    if italic is not None:
        run.font.italic = italic
    run.font.color.rgb = RGBColor(0, 0, 0)


def split_paragraph_after_run_index(paragraph, start_index: int):
    runs = list(paragraph.runs)
    body_text = "".join(run.text for run in runs[start_index:]).lstrip()
    if not body_text:
        return None

    paragraph_style_name = paragraph.style.name if paragraph.style else None
    new_paragraph = insert_paragraph_after(
        paragraph, body_text, paragraph_style_name
    )
    for run in runs[start_index:]:
        run.text = ""
    return new_paragraph


def split_reference_entries(text: str) -> list[str]:
    matches = list(REFERENCE_MARKER_RE.finditer(text))
    if len(matches) <= 1:
        stripped = text.strip()
        return [stripped] if stripped else []

    entries: list[str] = []
    for idx, match in enumerate(matches):
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        entry = text[match.start() : end].strip()
        if entry:
            entries.append(entry)
    return entries


def split_reference_paragraphs(doc: DocxDocument, settings: dict[str, Any]) -> None:
    detection = settings["detection"]
    in_references = False
    for paragraph in list(doc.paragraphs):
        text = paragraph.text.strip()
        if is_reference_heading_text(text, detection):
            in_references = True
            continue
        if starts_with_any(text, detection["reference_end_prefixes"]):
            in_references = False
        if not in_references:
            continue

        entries = split_reference_entries(text)
        if len(entries) <= 1:
            continue

        paragraph_style_name = (
            paragraph.style.name if paragraph.style else style_name(settings, "reference")
        )
        paragraph.text = entries[0]
        paragraph.style = paragraph.part.document.styles[paragraph_style_name]

        current = paragraph
        for entry in entries[1:]:
            current = insert_paragraph_after(current, entry, paragraph_style_name)


def remove_paragraph_numbering(paragraph) -> None:
    paragraph_properties = paragraph._element.find(qn("w:pPr"))
    if paragraph_properties is None:
        return
    numbering = paragraph_properties.find(qn("w:numPr"))
    if numbering is not None:
        paragraph_properties.remove(numbering)


def has_paragraph_numbering(paragraph) -> bool:
    paragraph_properties = paragraph._element.find(qn("w:pPr"))
    if paragraph_properties is None:
        return False
    return paragraph_properties.find(qn("w:numPr")) is not None


def force_paragraph_zero_indent(paragraph) -> None:
    paragraph.paragraph_format.first_line_indent = Cm(0)
    paragraph.paragraph_format.left_indent = Cm(0)
    paragraph.paragraph_format.right_indent = Cm(0)

    paragraph_properties = paragraph._element.find(qn("w:pPr"))
    if paragraph_properties is None:
        paragraph_properties = OxmlElement("w:pPr")
        paragraph._element.insert(0, paragraph_properties)

    indent = paragraph_properties.find(qn("w:ind"))
    if indent is None:
        indent = OxmlElement("w:ind")
        paragraph_properties.append(indent)

    for key in (
        "left",
        "right",
        "firstLine",
        "hanging",
        "leftChars",
        "rightChars",
        "firstLineChars",
        "hangingChars",
    ):
        indent.set(qn(f"w:{key}"), "0")


def align_ordered_list_indentation(
    doc: DocxDocument, body_first_line_indent_pt: float
) -> None:
    numbering_part = getattr(doc.part, "numbering_part", None)
    if numbering_part is None:
        return

    root = numbering_part._element
    normal_first_indent_twips = str(int(round(body_first_line_indent_pt * 20)))
    ordered_hanging_twips = "360"

    for node in root.iter():
        if etree.QName(node).localname != "lvl":
            continue

        number_format = node.find(qn("w:numFmt"))
        format_value = number_format.get(qn("w:val")) if number_format is not None else None
        if not format_value or format_value == "bullet":
            continue

        paragraph_properties = node.find(qn("w:pPr"))
        if paragraph_properties is None:
            paragraph_properties = OxmlElement("w:pPr")
            node.append(paragraph_properties)

        indent = paragraph_properties.find(qn("w:ind"))
        if indent is None:
            indent = OxmlElement("w:ind")
            paragraph_properties.append(indent)

        indent.set(qn("w:left"), normal_first_indent_twips)
        indent.set(qn("w:hanging"), ordered_hanging_twips)
        if qn("w:firstLine") in indent.attrib:
            del indent.attrib[qn("w:firstLine")]


def align_ordered_list_text(doc: DocxDocument, settings: dict[str, Any]) -> None:
    numbering_settings = settings.get("numbering", {})
    decimal_level_text = numbering_settings.get("decimal_level_text")
    if not decimal_level_text:
        return

    numbering_part = getattr(doc.part, "numbering_part", None)
    if numbering_part is None:
        return

    root = numbering_part._element
    for node in root.iter():
        if etree.QName(node).localname != "lvl":
            continue

        numfmt = node.find(qn("w:numFmt"))
        fmt_val = numfmt.get(qn("w:val")) if numfmt is not None else None
        if fmt_val != "decimal":
            continue

        ilvl = node.get(qn("w:ilvl"), "0")
        target_text = decimal_level_text.get(ilvl)
        if target_text is None:
            continue

        lvl_text = node.find(qn("w:lvlText"))
        if lvl_text is None:
            lvl_text = OxmlElement("w:lvlText")
            node.append(lvl_text)
        lvl_text.set(qn("w:val"), target_text)


def build_numbering_numfmt_lookup(doc: DocxDocument) -> dict[str, dict[str, str]]:
    lookup: dict[str, dict[str, str]] = {}
    numbering_part = getattr(doc.part, "numbering_part", None)
    if numbering_part is None:
        return lookup

    root = numbering_part._element
    abstract_map: dict[str, dict[str, str]] = {}

    for abstract in root:
        if etree.QName(abstract).localname != "abstractNum":
            continue
        abstract_id = abstract.get(qn("w:abstractNumId"))
        if not abstract_id:
            continue
        level_map: dict[str, str] = {}
        for level in abstract:
            if etree.QName(level).localname != "lvl":
                continue
            level_index = level.get(qn("w:ilvl"), "0")
            number_format = level.find(qn("w:numFmt"))
            format_value = number_format.get(qn("w:val")) if number_format is not None else None
            if format_value:
                level_map[level_index] = format_value
        abstract_map[abstract_id] = level_map

    for numbering in root:
        if etree.QName(numbering).localname != "num":
            continue
        number_id = numbering.get(qn("w:numId"))
        if not number_id:
            continue

        abstract_ref = numbering.find(qn("w:abstractNumId"))
        abstract_id = abstract_ref.get(qn("w:val")) if abstract_ref is not None else None
        merged = dict(abstract_map.get(abstract_id or "", {}))

        for override in numbering:
            if etree.QName(override).localname != "lvlOverride":
                continue
            level_index = override.get(qn("w:ilvl"), "0")
            level = override.find(qn("w:lvl"))
            if level is None:
                continue
            number_format = level.find(qn("w:numFmt"))
            format_value = number_format.get(qn("w:val")) if number_format is not None else None
            if format_value:
                merged[level_index] = format_value

        lookup[number_id] = merged

    return lookup


def is_unordered_list_paragraph(
    paragraph, numbering_lookup: dict[str, dict[str, str]]
) -> bool:
    paragraph_properties = paragraph._element.find(qn("w:pPr"))
    if paragraph_properties is None:
        return False
    numbering = paragraph_properties.find(qn("w:numPr"))
    if numbering is None:
        return False

    number_id_element = numbering.find(qn("w:numId"))
    if number_id_element is None:
        return False
    number_id = number_id_element.get(qn("w:val"), "")
    level_element = numbering.find(qn("w:ilvl"))
    level_index = level_element.get(qn("w:val"), "0") if level_element is not None else "0"

    level_map = numbering_lookup.get(number_id, {})
    format_value = level_map.get(level_index) or level_map.get("0")
    return format_value == "bullet"


def append_page_field(paragraph) -> None:
    field_begin = OxmlElement("w:fldChar")
    field_begin.set(qn("w:fldCharType"), "begin")
    instruction = OxmlElement("w:instrText")
    instruction.set(qn("xml:space"), "preserve")
    instruction.text = "PAGE"
    field_separator = OxmlElement("w:fldChar")
    field_separator.set(qn("w:fldCharType"), "separate")
    field_end = OxmlElement("w:fldChar")
    field_end.set(qn("w:fldCharType"), "end")

    run = paragraph.add_run()
    run._r.append(field_begin)
    run._r.append(instruction)
    run._r.append(field_separator)
    placeholder_run = paragraph.add_run("1")
    placeholder_run._r.append(field_end)


def set_footer_page_number(doc: DocxDocument, style_profile: dict[str, Any]) -> None:
    fonts = style_profile["fonts"]
    sizes = style_profile["sizes"]
    for section in doc.sections:
        footer = section.footer
        paragraph = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
        clear_paragraph(paragraph)
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        append_page_field(paragraph)
        for run in paragraph.runs:
            run.font.name = fonts["normal_ascii"]
            set_east_asia(run, fonts["normal_east_asia"], ascii_font=fonts["normal_ascii"])
            run.font.size = Pt(sizes["footer"])


def apply_three_line_borders(table_properties) -> None:
    borders = table_properties.find(qn("w:tblBorders"))
    if borders is None:
        borders = OxmlElement("w:tblBorders")
        table_properties.append(borders)

    border_specs = {
        "top": ("single", "12"),
        "bottom": ("single", "12"),
        "insideH": ("single", "8"),
        "left": ("nil", "0"),
        "right": ("nil", "0"),
        "insideV": ("nil", "0"),
    }
    for side, (value, size) in border_specs.items():
        side_element = borders.find(qn(f"w:{side}"))
        if side_element is None:
            side_element = OxmlElement(f"w:{side}")
            borders.append(side_element)
        side_element.set(qn("w:val"), value)
        side_element.set(qn("w:sz"), size)
        side_element.set(qn("w:space"), "0")
        side_element.set(qn("w:color"), "000000")


def infer_table_paragraph_alignment(table, row_index: int, col_index: int, text: str):
    stripped = text.strip()
    if row_index == 0:
        return WD_ALIGN_PARAGRAPH.CENTER
    if len(table.columns) >= 4 and col_index >= 2 and len(stripped) > 12:
        return WD_ALIGN_PARAGRAPH.JUSTIFY
    if len(stripped) > 20:
        return WD_ALIGN_PARAGRAPH.JUSTIFY
    return WD_ALIGN_PARAGRAPH.CENTER


def trim_table_paragraph_leading_whitespace(paragraph) -> None:
    for run in paragraph.runs:
        if not run.text:
            continue
        run.text = run.text.lstrip(" \t\u3000")
        if run.text:
            break


def format_table(
    table, doc: DocxDocument, settings: dict[str, Any], style_profile: dict[str, Any]
) -> None:
    fonts = style_profile["fonts"]
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    available_styles = {style.name for style in doc.styles}
    if "Table Grid" in available_styles:
        table.style = "Table Grid"

    table_properties = table._tbl.tblPr
    if table_properties is None:
        table_properties = OxmlElement("w:tblPr")
        table._tbl.insert(0, table_properties)

    apply_three_line_borders(table_properties)

    cell_margin = table_properties.find(qn("w:tblCellMar"))
    if cell_margin is None:
        cell_margin = OxmlElement("w:tblCellMar")
        table_properties.append(cell_margin)
    for side in ("top", "left", "bottom", "right"):
        side_element = cell_margin.find(qn(f"w:{side}"))
        if side_element is None:
            side_element = OxmlElement(f"w:{side}")
            cell_margin.append(side_element)
        side_element.set(qn("w:w"), "40")
        side_element.set(qn("w:type"), "dxa")

    for row_index, row in enumerate(table.rows):
        for col_index, cell in enumerate(row.cells):
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            cell_properties = cell._tc.get_or_add_tcPr()
            cell_margin = cell_properties.find(qn("w:tcMar"))
            if cell_margin is None:
                cell_margin = OxmlElement("w:tcMar")
                cell_properties.append(cell_margin)
            for side in ("top", "left", "bottom", "right"):
                side_element = cell_margin.find(qn(f"w:{side}"))
                if side_element is None:
                    side_element = OxmlElement(f"w:{side}")
                    cell_margin.append(side_element)
                side_element.set(qn("w:w"), "40")
                side_element.set(qn("w:type"), "dxa")

            vertical_align = cell_properties.find(qn("w:vAlign"))
            if vertical_align is None:
                vertical_align = OxmlElement("w:vAlign")
                cell_properties.append(vertical_align)
            vertical_align.set(qn("w:val"), "center")

            for paragraph in cell.paragraphs:
                trim_table_paragraph_leading_whitespace(paragraph)
                paragraph.style = doc.styles[style_name(settings, "body")]
                force_paragraph_zero_indent(paragraph)
                paragraph.paragraph_format.right_indent = Cm(0)
                paragraph.paragraph_format.space_before = Pt(0)
                paragraph.paragraph_format.space_after = Pt(0)
                paragraph.paragraph_format.line_spacing_rule = None
                paragraph.paragraph_format.line_spacing = None
                paragraph.paragraph_format.alignment = infer_table_paragraph_alignment(
                    table, row_index, col_index, paragraph.text
                )
                for run in paragraph.runs:
                    run.font.name = style_profile["fonts"]["normal_ascii"]
                    set_east_asia(
                        run,
                        fonts["normal_east_asia"],
                        ascii_font=fonts["normal_ascii"],
                    )
                    run.font.size = Pt(10.5)


def convert_drawing_xml(data: bytes) -> bytes:
    parser = etree.XMLParser(remove_blank_text=False)
    root = etree.fromstring(data, parser)
    changed = False

    for inline in root.xpath("//wp:inline", namespaces=NS):
        anchor = etree.Element(qn("wp:anchor"))
        for key, value in {
            "distT": inline.get("distT", "0"),
            "distB": inline.get("distB", "0"),
            "distL": inline.get("distL", "0"),
            "distR": inline.get("distR", "0"),
            "simplePos": "0",
            "relativeHeight": "251659264",
            "behindDoc": "0",
            "locked": "0",
            "layoutInCell": "1",
            "allowOverlap": "1",
        }.items():
            anchor.set(key, value)

        simple_pos = etree.Element(qn("wp:simplePos"))
        simple_pos.set("x", "0")
        simple_pos.set("y", "0")

        position_h = etree.Element(qn("wp:positionH"))
        position_h.set("relativeFrom", "column")
        position_h_offset = etree.Element(qn("wp:posOffset"))
        position_h_offset.text = "0"
        position_h.append(position_h_offset)

        position_v = etree.Element(qn("wp:positionV"))
        position_v.set("relativeFrom", "paragraph")
        position_v_offset = etree.Element(qn("wp:posOffset"))
        position_v_offset.text = "0"
        position_v.append(position_v_offset)

        wrap = etree.Element(qn("wp:wrapTopAndBottom"))

        anchor.append(simple_pos)
        anchor.append(position_h)
        anchor.append(position_v)

        for child in list(inline):
            anchor.append(child)

        effect = anchor.find(qn("wp:effectExtent"))
        extent = anchor.find(qn("wp:extent"))
        doc_properties = anchor.find(qn("wp:docPr"))
        if effect is not None:
            effect.addnext(wrap)
        elif extent is not None:
            extent.addnext(wrap)
        elif doc_properties is not None:
            anchor.insert(anchor.index(doc_properties), wrap)
        else:
            anchor.append(wrap)

        parent = inline.getparent()
        if parent is not None:
            parent.replace(inline, anchor)
            changed = True

    for anchor in root.xpath("//wp:anchor", namespaces=NS):
        existing_wraps = [
            child for child in anchor if etree.QName(child).localname.startswith("wrap")
        ]
        if any(
            etree.QName(child).localname == "wrapTopAndBottom"
            for child in existing_wraps
        ):
            continue
        for child in existing_wraps:
            anchor.remove(child)
        wrap = etree.Element(qn("wp:wrapTopAndBottom"))
        effect = anchor.find(qn("wp:effectExtent"))
        extent = anchor.find(qn("wp:extent"))
        doc_properties = anchor.find(qn("wp:docPr"))
        if effect is not None:
            effect.addnext(wrap)
        elif extent is not None:
            extent.addnext(wrap)
        elif doc_properties is not None:
            anchor.insert(anchor.index(doc_properties), wrap)
        else:
            anchor.append(wrap)
        changed = True

    if not changed:
        return data
    return etree.tostring(
        root, xml_declaration=True, encoding="UTF-8", standalone="yes"
    )


def convert_inline_images_to_top_bottom_wrap(docx_path: Path) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir) / docx_path.name
        with (
            ZipFile(docx_path, "r") as source,
            ZipFile(tmp_path, "w", ZIP_DEFLATED) as destination,
        ):
            for item in source.infolist():
                data = source.read(item.filename)
                if item.filename.startswith("word/") and item.filename.endswith(".xml"):
                    data = convert_drawing_xml(data)
                destination.writestr(item, data)
        tmp_path.replace(docx_path)


def normalize_table_xml(data: bytes) -> bytes:
    parser = etree.XMLParser(remove_blank_text=False)
    root = etree.fromstring(data, parser)
    changed = False

    for tag in ("tblPrChange", "trPrChange", "tcPrChange", "pPrChange"):
        for node in root.xpath(f"//w:{tag}", namespaces=NS):
            parent = node.getparent()
            if parent is not None:
                parent.remove(node)
                changed = True

    for table in root.xpath("//w:tbl", namespaces=NS):
        table_properties = table.find(qn("w:tblPr"))
        if table_properties is None:
            table_properties = OxmlElement("w:tblPr")
            table.insert(0, table_properties)
            changed = True

        table_width = table_properties.find(qn("w:tblW"))
        if table_width is None:
            table_width = OxmlElement("w:tblW")
            table_properties.append(table_width)
            changed = True
        if table_width.get(qn("w:type")) != "pct" or table_width.get(qn("w:w")) != "5000":
            table_width.set(qn("w:type"), "pct")
            table_width.set(qn("w:w"), "5000")
            changed = True

        table_layout = table_properties.find(qn("w:tblLayout"))
        if table_layout is None:
            table_layout = OxmlElement("w:tblLayout")
            table_properties.append(table_layout)
            changed = True
        if table_layout.get(qn("w:type")) != "fixed":
            table_layout.set(qn("w:type"), "fixed")
            changed = True

        table_indent = table_properties.find(qn("w:tblInd"))
        if table_indent is None:
            table_indent = OxmlElement("w:tblInd")
            table_properties.append(table_indent)
            changed = True
        if table_indent.get(qn("w:w")) != "0" or table_indent.get(qn("w:type")) != "dxa":
            table_indent.set(qn("w:w"), "0")
            table_indent.set(qn("w:type"), "dxa")
            changed = True

        borders = table_properties.find(qn("w:tblBorders"))
        if borders is None:
            borders = OxmlElement("w:tblBorders")
            table_properties.append(borders)
            changed = True
        border_specs = {
            "top": ("single", "12"),
            "bottom": ("single", "12"),
            "insideH": ("single", "8"),
            "left": ("nil", "0"),
            "right": ("nil", "0"),
            "insideV": ("nil", "0"),
        }
        for side, (value, size) in border_specs.items():
            side_element = borders.find(qn(f"w:{side}"))
            if side_element is None:
                side_element = OxmlElement(f"w:{side}")
                borders.append(side_element)
                changed = True
            if (
                side_element.get(qn("w:val")) != value
                or side_element.get(qn("w:sz")) != size
                or side_element.get(qn("w:color")) != "000000"
            ):
                side_element.set(qn("w:val"), value)
                side_element.set(qn("w:sz"), size)
                side_element.set(qn("w:space"), "0")
                side_element.set(qn("w:color"), "000000")
                changed = True

        cell_margin = table_properties.find(qn("w:tblCellMar"))
        if cell_margin is None:
            cell_margin = OxmlElement("w:tblCellMar")
            table_properties.append(cell_margin)
            changed = True
        for side in ("top", "left", "bottom", "right"):
            side_element = cell_margin.find(qn(f"w:{side}"))
            if side_element is None:
                side_element = OxmlElement(f"w:{side}")
                cell_margin.append(side_element)
                changed = True
            if side_element.get(qn("w:w")) != "40" or side_element.get(qn("w:type")) != "dxa":
                side_element.set(qn("w:w"), "40")
                side_element.set(qn("w:type"), "dxa")
                changed = True

        for cell in table.xpath(".//w:tc", namespaces=NS):
            cell_properties = cell.find(qn("w:tcPr"))
            if cell_properties is None:
                cell_properties = OxmlElement("w:tcPr")
                cell.insert(0, cell_properties)
                changed = True
            cell_margin = cell_properties.find(qn("w:tcMar"))
            if cell_margin is None:
                cell_margin = OxmlElement("w:tcMar")
                cell_properties.append(cell_margin)
                changed = True
            for side in ("top", "left", "bottom", "right"):
                side_element = cell_margin.find(qn(f"w:{side}"))
                if side_element is None:
                    side_element = OxmlElement(f"w:{side}")
                    cell_margin.append(side_element)
                    changed = True
                if side_element.get(qn("w:w")) != "40" or side_element.get(qn("w:type")) != "dxa":
                    side_element.set(qn("w:w"), "40")
                    side_element.set(qn("w:type"), "dxa")
                    changed = True

            vertical_align = cell_properties.find(qn("w:vAlign"))
            if vertical_align is None:
                vertical_align = OxmlElement("w:vAlign")
                cell_properties.append(vertical_align)
                changed = True
            if vertical_align.get(qn("w:val")) != "center":
                vertical_align.set(qn("w:val"), "center")
                changed = True

        for paragraph in table.xpath(".//w:p", namespaces=NS):
            paragraph_properties = paragraph.find(qn("w:pPr"))
            if paragraph_properties is None:
                paragraph_properties = OxmlElement("w:pPr")
                paragraph.insert(0, paragraph_properties)
                changed = True

            numbering = paragraph_properties.find(qn("w:numPr"))
            if numbering is not None:
                paragraph_properties.remove(numbering)
                changed = True

            indent = paragraph_properties.find(qn("w:ind"))
            if indent is None:
                indent = OxmlElement("w:ind")
                paragraph_properties.append(indent)
                changed = True
            for key in (
                "left",
                "firstLine",
                "hanging",
                "right",
                "leftChars",
                "rightChars",
                "firstLineChars",
                "hangingChars",
            ):
                if indent.get(qn(f"w:{key}")) != "0":
                    indent.set(qn(f"w:{key}"), "0")
                    changed = True

    if not changed:
        return data
    return etree.tostring(
        root, xml_declaration=True, encoding="UTF-8", standalone="yes"
    )


def normalize_tables_in_docx(docx_path: Path) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir) / docx_path.name
        with (
            ZipFile(docx_path, "r") as source,
            ZipFile(tmp_path, "w", ZIP_DEFLATED) as destination,
        ):
            for item in source.infolist():
                data = source.read(item.filename)
                if item.filename.startswith("word/") and item.filename.endswith(".xml"):
                    data = normalize_table_xml(data)
                destination.writestr(item, data)
        tmp_path.replace(docx_path)


def detect_style_name(paragraph, in_references: bool, settings: dict[str, Any]) -> str:
    detection = settings["detection"]
    body_style = style_name(settings, "body")
    text = paragraph.text.strip()
    original = paragraph.style.name if paragraph.style else ""
    if not text:
        return original or body_style

    if settings["title_text"] and text == settings["title_text"]:
        return style_name(settings, "title")
    if is_reference_heading_text(text, detection) or matches_any(
        detection["chapter_patterns"], text
    ):
        return style_name(settings, "heading_1")
    if matches_any(detection["subsubsection_patterns"], text):
        return style_name(settings, "heading_4")
    if matches_any(detection["subsection_patterns"], text):
        return style_name(settings, "heading_3")
    if matches_any(detection["section_patterns"], text):
        return style_name(settings, "heading_2")
    if matches_any(detection["caption_patterns"], text) and len(text) < 80:
        return style_name(settings, "caption")
    if starts_with_any(text, detection["abstract_label_prefixes"]):
        return style_name(settings, "abstract_label")
    if starts_with_any(text, detection["keywords_prefixes"]):
        return style_name(settings, "keywords")
    if in_references and re.match(detection["reference_item_pattern"], text):
        return style_name(settings, "reference")
    if original in code_style_names(settings):
        return style_name(settings, "code")
    return body_style


def apply_paragraph_style(paragraph, style_name_value: str, settings: dict[str, Any]) -> None:
    paragraph.style = paragraph.part.document.styles[style_name_value]
    if style_name_value != style_name(settings, "body"):
        return
    text = paragraph.text.strip()
    if text.startswith(tuple(f"{value}." for value in range(1, 10))):
        paragraph.paragraph_format.first_line_indent = Cm(0)
    if text.startswith(("*", "-")):
        paragraph.paragraph_format.first_line_indent = Cm(0)


def format_code_paragraph(paragraph, style_profile: dict[str, Any]) -> None:
    fonts = style_profile["fonts"]
    sizes = style_profile["sizes"]
    paragraph.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    paragraph.paragraph_format.first_line_indent = Cm(0)
    paragraph.paragraph_format.left_indent = Cm(0.74)
    paragraph.paragraph_format.right_indent = Cm(0.74)
    paragraph.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    paragraph.paragraph_format.line_spacing = Pt(18)
    paragraph.paragraph_format.space_before = Pt(6)
    paragraph.paragraph_format.space_after = Pt(6)

    paragraph_properties = paragraph._element.get_or_add_pPr()
    shading = paragraph_properties.find(qn("w:shd"))
    if shading is None:
        shading = OxmlElement("w:shd")
        paragraph_properties.append(shading)
    shading.set(qn("w:val"), "clear")
    shading.set(qn("w:color"), "auto")
    shading.set(qn("w:fill"), "F5F5F5")

    for run in paragraph.runs:
        if not run.text:
            continue
        style_run(
            run,
            fonts["code_east_asia"],
            sizes["code"],
            ascii_font=fonts["code_ascii"],
        )


def format_caption_paragraph(paragraph, settings: dict[str, Any]) -> None:
    style_profile = settings["style_profile"]
    fonts = style_profile["fonts"]
    sizes = style_profile["sizes"]
    before_lines, after_lines = caption_spacing_lines(paragraph.text.strip(), settings)
    paragraph.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.first_line_indent = Cm(0)
    paragraph.paragraph_format.space_before = Pt(sizes["caption"] * before_lines)
    paragraph.paragraph_format.space_after = Pt(sizes["caption"] * after_lines)
    for run in paragraph.runs:
        if not run.text:
            continue
        style_run(
            run,
            fonts["caption_east_asia"],
            sizes["caption"],
            ascii_font=fonts["normal_ascii"],
            bold=False,
            italic=False,
        )


def format_heading_paragraph(paragraph, settings: dict[str, Any], level: int) -> None:
    style_profile = settings["style_profile"]
    fonts = style_profile["fonts"]
    sizes = style_profile["sizes"]
    size_key = f"heading_{level}"
    for run in paragraph.runs:
        if not run.text:
            continue
        style_run(
            run,
            fonts["heading_east_asia"],
            sizes[size_key],
            ascii_font=fonts["normal_ascii"],
            bold=False,
            italic=False,
        )


def insert_break_after_numbered_bold_leadin(paragraph) -> None:
    if "\n" in paragraph.text:
        return
    runs = [run for run in paragraph.runs if run.text]
    if len(runs) < 3:
        return
    if not (bool(runs[0].bold) and NUMBERED_BOLD_LEADIN_RE.match(runs[0].text)):
        return

    lead_end = 0
    for index in range(1, len(runs)):
        if bool(runs[index].bold):
            lead_end = index
            continue
        break

    if lead_end == 0:
        return

    body_index = lead_end + 1
    while body_index < len(runs) and runs[body_index].text.isspace():
        body_index += 1
    if body_index >= len(runs):
        return

    split_paragraph_after_run_index(paragraph, body_index)
    for index in range(lead_end + 1, body_index):
        runs[index].text = ""


def insert_break_after_starred_bold_leadin(paragraph) -> None:
    runs = [run for run in paragraph.runs if run.text]
    if len(runs) < 3:
        return

    index = 0
    while index < len(runs) - 2:
        if not STAR_BULLET_RE.match(runs[index].text):
            index += 1
            continue

        bold_start = index + 1
        while bold_start < len(runs) and runs[bold_start].text.isspace():
            bold_start += 1
        if bold_start >= len(runs) or not bool(runs[bold_start].bold):
            index += 1
            continue

        bold_end = bold_start
        while bold_end + 1 < len(runs) and bool(runs[bold_end + 1].bold):
            bold_end += 1

        body_index = bold_end + 1
        if body_index >= len(runs):
            break

        body_text = runs[body_index].text
        stripped_body = body_text.lstrip()
        prefix_length = len(body_text) - len(stripped_body)

        punctuation = ""
        if stripped_body.startswith(("：", ":")):
            punctuation = stripped_body[0]
            stripped_body = stripped_body[1:]

        if not stripped_body:
            index = body_index + 1
            continue

        if punctuation:
            runs[bold_end].text = runs[bold_end].text + punctuation
            runs[body_index].text = stripped_body.lstrip()
        elif prefix_length:
            runs[body_index].text = stripped_body

        runs[bold_end].add_break(WD_BREAK.LINE)
        index = body_index


def is_mermaid_code_block(text: str, settings: dict[str, Any]) -> bool:
    stripped = text.lstrip()
    if not stripped:
        return False
    starters = tuple(settings["mermaid"]["starters"])
    for line in stripped.splitlines():
        line_stripped = line.strip()
        if not line_stripped or line_stripped.startswith("%%"):
            continue
        directive = line_stripped.split(None, 1)[0]
        return directive in starters
    return False


def render_mermaid_png(mermaid_source: str, settings: dict[str, Any]) -> Path:
    tmpdir = Path(tempfile.mkdtemp(prefix="mermaid-render-"))
    input_path = tmpdir / "diagram.mmd"
    output_path = tmpdir / "diagram.png"
    mermaid = settings["mermaid"]

    try:
        input_path.write_text(mermaid_source, encoding="utf-8")
        result = subprocess.run(
            [
                "npx",
                "-y",
                f"@mermaid-js/mermaid-cli@{mermaid['version']}",
                "-i",
                str(input_path),
                "-o",
                str(output_path),
                "-b",
                mermaid["background"],
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            stderr = (result.stderr or "").strip()
            raise RuntimeError(
                f"Mermaid render failed with exit code {result.returncode}: {stderr}"
            )
        return output_path
    except Exception:
        shutil.rmtree(tmpdir, ignore_errors=True)
        raise


def cleanup_mermaid_rendered_png(image_path: Path) -> None:
    parent = image_path.parent
    if parent.name.startswith("mermaid-render-"):
        shutil.rmtree(parent, ignore_errors=True)
        return
    image_path.unlink(missing_ok=True)


def get_image_intrinsic_width(image_path: Path):
    probe = Document()
    probe.add_paragraph().add_run().add_picture(str(image_path))
    return probe.inline_shapes[0].width


def get_mermaid_starter_text(text: str) -> str:
    stripped = text.lstrip()
    first_line = stripped.splitlines()[0] if stripped else ""
    return first_line[:80]


def replace_mermaid_code_blocks(doc: DocxDocument, settings: dict[str, Any]) -> None:
    paragraphs = list(doc.paragraphs)
    replacements = []

    try:
        for index, paragraph in enumerate(paragraphs):
            paragraph_style_name = paragraph.style.name if paragraph.style else ""
            if paragraph_style_name != style_name(settings, "code") or not is_mermaid_code_block(
                paragraph.text, settings
            ):
                continue

            if index + 1 >= len(paragraphs):
                raise ValueError(
                    "Mermaid code block at paragraph "
                    f"{index} must be followed by a Thesis Caption paragraph: "
                    f"{get_mermaid_starter_text(paragraph.text)}"
                )

            caption = paragraphs[index + 1]
            caption_style = caption.style.name if caption.style else ""
            if caption_style != style_name(settings, "caption"):
                raise ValueError(
                    "Mermaid code block at paragraph "
                    f"{index} must be followed by a Thesis Caption paragraph: "
                    f"{get_mermaid_starter_text(paragraph.text)}"
                )

            replacements.append(
                (paragraph, caption, render_mermaid_png(paragraph.text, settings))
            )
    except Exception:
        for _, _, image_path in replacements:
            cleanup_mermaid_rendered_png(image_path)
        raise

    if not replacements:
        return

    section = doc.sections[0]
    max_width = (
        int(cast(Any, section.page_width))
        - int(cast(Any, section.left_margin))
        - int(cast(Any, section.right_margin))
    )

    try:
        for paragraph, caption, image_path in replacements:
            try:
                intrinsic_width = int(get_image_intrinsic_width(image_path))
                image_width = intrinsic_width if intrinsic_width < max_width else max_width

                image_paragraph = doc.add_paragraph()
                caption._element.addprevious(image_paragraph._element)
                image_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                paragraph_format = image_paragraph.paragraph_format
                paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
                paragraph_format.first_line_indent = Cm(0)
                paragraph_format.left_indent = Cm(0)
                paragraph_format.right_indent = Cm(0)
                paragraph_format.space_before = Pt(6)
                paragraph_format.space_after = Pt(6)

                image_paragraph.add_run().add_picture(str(image_path), width=image_width)
                remove_paragraph(paragraph)
            finally:
                cleanup_mermaid_rendered_png(image_path)
    except Exception:
        for _, _, image_path in replacements:
            cleanup_mermaid_rendered_png(image_path)
        raise


def normalize_document(doc: DocxDocument, settings: dict[str, Any]) -> None:
    style_profile = settings["style_profile"]
    detection = settings["detection"]
    configure_styles(doc, settings)
    set_page_layout(doc, style_profile)
    set_footer_page_number(doc, style_profile)
    align_ordered_list_indentation(
        doc, style_profile.get("paragraph", {}).get("body_first_line_indent_pt", 24)
    )
    align_ordered_list_text(doc, settings)
    split_reference_paragraphs(doc, settings)
    numbering_lookup = build_numbering_numfmt_lookup(doc)

    in_references = False
    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()
        if is_reference_heading_text(text, detection):
            in_references = True
        elif starts_with_any(text, detection["reference_end_prefixes"]):
            in_references = False

        detected_style_name = detect_style_name(paragraph, in_references, settings)
        apply_paragraph_style(paragraph, detected_style_name, settings)

        paragraph_style = paragraph.style.name if paragraph.style else ""
        if paragraph_style == "List Bullet" or is_unordered_list_paragraph(
            paragraph, numbering_lookup
        ):
            remove_paragraph_numbering(paragraph)
            paragraph.style = cast(
                ParagraphStyle, doc.styles[style_name(settings, "body")]
            )
            force_paragraph_zero_indent(paragraph)
            paragraph.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
        elif has_paragraph_numbering(paragraph):
            force_paragraph_zero_indent(paragraph)

        if is_style_role(paragraph, settings, "code"):
            format_code_paragraph(paragraph, style_profile)
        else:
            insert_break_after_numbered_bold_leadin(paragraph)
            insert_break_after_starred_bold_leadin(paragraph)

        if paragraph.style and paragraph.style.name == style_name(settings, "caption"):
            format_caption_paragraph(paragraph, settings)
        elif paragraph.style and paragraph.style.name == style_name(settings, "heading_1"):
            format_heading_paragraph(paragraph, settings, 1)
        elif paragraph.style and paragraph.style.name == style_name(settings, "heading_2"):
            format_heading_paragraph(paragraph, settings, 2)
        elif paragraph.style and paragraph.style.name == style_name(settings, "heading_3"):
            format_heading_paragraph(paragraph, settings, 3)
        elif paragraph.style and paragraph.style.name == style_name(settings, "heading_4"):
            format_heading_paragraph(paragraph, settings, 4)

        if starts_with_any(text, detection["keywords_prefixes"]):
            paragraph.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
        if matches_any(detection["caption_patterns"], text) and len(text) < 80:
            paragraph.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER

    for table in doc.tables:
        format_table(table, doc, settings, style_profile)


def build_reference_doc(path: Path, settings: dict[str, Any]) -> None:
    doc = Document()
    configure_styles(doc, settings)
    set_page_layout(doc, settings["style_profile"])
    set_footer_page_number(doc, settings["style_profile"])

    samples = settings["style_profile"]["samples"]
    doc.add_paragraph(settings["title_text"], style=style_name(settings, "title"))
    doc.add_paragraph(samples["heading_1"], style=style_name(settings, "heading_1"))
    doc.add_paragraph(samples["heading_2"], style=style_name(settings, "heading_2"))
    doc.add_paragraph(samples["heading_3"], style=style_name(settings, "heading_3"))
    doc.add_paragraph(samples["body"], style=style_name(settings, "body"))
    doc.add_paragraph(samples["caption"], style=style_name(settings, "caption"))
    path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(path))


def prepare_reference_doc(
    reference_doc: Path, reference_template: Path | None, settings: dict[str, Any]
) -> None:
    reference_doc.parent.mkdir(parents=True, exist_ok=True)
    if reference_template is not None and reference_template.exists():
        shutil.copyfile(reference_template, reference_doc)
        return
    build_reference_doc(reference_doc, settings)


def convert_markdown_to_docx(
    input_md: Path,
    reference_doc: Path,
    output_docx: Path,
    workdir: Path,
    settings: dict[str, Any],
) -> None:
    output_docx.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "pandoc",
        str(input_md),
        f"--reference-doc={reference_doc}",
        "-o",
        str(output_docx),
    ]
    subprocess.run(cmd, check=True, cwd=workdir)

    rebuilt = Document(str(output_docx))
    normalize_document(rebuilt, settings)
    if settings["features"]["replace_mermaid"]:
        replace_mermaid_code_blocks(rebuilt, settings)
    rebuilt.save(str(output_docx))

    if settings["features"]["normalize_image_wrap"]:
        convert_inline_images_to_top_bottom_wrap(output_docx)
    if settings["features"]["normalize_tables"]:
        normalize_tables_in_docx(output_docx)


def build_runtime(args: argparse.Namespace) -> dict[str, Any]:
    template_id = args.template or DEFAULT_TEMPLATE_ID
    template_settings, template_entry = load_template(template_id)

    settings = deep_merge(DEFAULT_CONFIG, template_settings)
    settings["template"] = template_id

    workdir_value = str(args.workdir) if args.workdir else settings.get("workdir")
    workdir = resolve_workdir(workdir_value, Path.cwd())

    if args.input_parts:
        settings["input_parts"] = [str(path) for path in args.input_parts]
    if args.input_md:
        settings["input_md"] = str(args.input_md)
    if args.title_text:
        settings["title_text"] = args.title_text
    if args.merged_output:
        settings["merged_markdown"] = str(args.merged_output)
    if args.normalized_output:
        settings["normalized_output"] = str(args.normalized_output)
    if args.reference_doc:
        settings["reference_doc"] = str(args.reference_doc)
    if args.reference_template:
        settings["reference_template"] = str(args.reference_template)
    if args.output_docx:
        settings["output_docx"] = str(args.output_docx)
    if args.skip_normalize_markdown:
        settings["features"]["normalize_markdown"] = False
    if args.enable_mermaid:
        settings["features"]["replace_mermaid"] = True
    if args.enable_image_wrap:
        settings["features"]["normalize_image_wrap"] = True
    if args.enable_table_normalize:
        settings["features"]["normalize_tables"] = True

    input_parts = [
        resolve_path(value, workdir)
        for value in cast(list[str], settings.get("input_parts", []))
    ]
    runtime = {
        "settings": settings,
        "template_entry": template_entry,
        "workdir": workdir,
        "input_parts": [path for path in input_parts if path is not None],
        "input_md": resolve_path(settings.get("input_md"), workdir),
        "merged_markdown": resolve_path(settings.get("merged_markdown"), workdir),
        "normalized_output": resolve_path(settings.get("normalized_output"), workdir),
        "reference_doc": resolve_path(settings.get("reference_doc"), workdir),
        "reference_template": resolve_path(settings.get("reference_template"), workdir),
        "output_docx": resolve_path(settings.get("output_docx"), workdir),
    }
    return runtime


def select_input_markdown(runtime: dict[str, Any]) -> Path:
    input_parts = cast(list[Path], runtime["input_parts"])
    input_md = cast(Path | None, runtime["input_md"])
    merged_markdown = cast(Path | None, runtime["merged_markdown"])

    if input_parts:
        if merged_markdown is None:
            raise SystemExit("input_parts requires a merged_markdown output path.")
        merge_markdown_sources(input_parts, merged_markdown)
        return merged_markdown

    if input_md is not None:
        return input_md

    if merged_markdown is not None and merged_markdown.exists():
        return merged_markdown

    raise SystemExit("Provide --input-md or --input-parts together with --merged-output.")


def maybe_normalize_markdown(runtime: dict[str, Any], input_md: Path, force: bool) -> Path:
    settings = cast(dict[str, Any], runtime["settings"])
    if not force and not settings["features"]["normalize_markdown"]:
        return input_md

    original = input_md.read_text(encoding="utf-8")
    normalized = normalize_markdown_for_word(original, settings["detection"])

    output_path = cast(Path | None, runtime["normalized_output"]) or input_md
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(normalized, encoding="utf-8")
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--list-templates", action="store_true")
    parser.add_argument("--show-template")
    parser.add_argument("--template")
    parser.add_argument("--workdir", type=Path)
    parser.add_argument("--input-md", type=Path)
    parser.add_argument("--input-parts", type=Path, nargs="+")
    parser.add_argument("--title-text")
    parser.add_argument("--merged-output", type=Path)
    parser.add_argument("--normalized-output", type=Path)
    parser.add_argument("--reference-doc", type=Path)
    parser.add_argument("--reference-template", type=Path)
    parser.add_argument("--output-docx", type=Path)
    parser.add_argument("--normalize-markdown-only", action="store_true")
    parser.add_argument("--skip-normalize-markdown", action="store_true")
    parser.add_argument("--enable-mermaid", action="store_true")
    parser.add_argument("--enable-image-wrap", action="store_true")
    parser.add_argument("--enable-table-normalize", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.list_templates:
        print_template_list()
        return

    if args.show_template:
        print_template_details(args.show_template)
        return

    runtime = build_runtime(args)
    input_md = select_input_markdown(runtime)

    effective_input_md = maybe_normalize_markdown(
        runtime, input_md, force=args.normalize_markdown_only
    )
    if args.normalize_markdown_only:
        print(effective_input_md)
        return

    settings = cast(dict[str, Any], runtime["settings"])
    reference_doc = cast(Path | None, runtime["reference_doc"])
    output_docx = cast(Path | None, runtime["output_docx"])
    if reference_doc is None or output_docx is None:
        raise SystemExit("reference_doc and output_docx must be configured.")

    prepare_reference_doc(
        reference_doc,
        cast(Path | None, runtime["reference_template"]),
        settings,
    )
    convert_markdown_to_docx(
        effective_input_md,
        reference_doc,
        output_docx,
        cast(Path, runtime["workdir"]),
        settings,
    )

    print(reference_doc)
    print(output_docx)


if __name__ == "__main__":
    main()
