"""Helpers for converting generated LaTeX body content into Mathematica code."""

from __future__ import annotations

import re

_ALIGNMENT_ENVS = frozenset(
    {
        "align",
        "align*",
        "aligned",
        "aligned*",
        "alignat",
        "alignat*",
        "flalign",
        "flalign*",
    }
)

_SKIPPED_WRAPPER_ENVS = _ALIGNMENT_ENVS | frozenset(
    {
        "equation",
        "equation*",
        "gather",
        "gather*",
        "multline",
        "multline*",
        "split",
    }
)

_BEGIN_ENV_RE = re.compile(r"^\\begin\{([^}]+)\}$")
_END_ENV_RE = re.compile(r"^\\end\{([^}]+)\}$")
_ALIGN_ROW_SPLIT_RE = re.compile(r"(?<!\\)\\\\(?:\[[^\]]*\])?")
_PAGE_MARKER_RE = re.compile(r"^% ====== Page (\d+) ======$")
_INLINE_COMMENT_RE = re.compile(r"(?<!\\)%.*$")
_UNESCAPED_AMPERSAND_RE = re.compile(r"(?<!\\)&")


def latex_body_to_mathematica(latex: str) -> str:
    """Convert LaTeX body content into line-oriented Mathematica code."""
    output_lines: list[str] = []
    alignment_depth = 0

    for raw_line in latex.splitlines():
        stripped = raw_line.strip()

        if not stripped:
            output_lines.append("")
            continue

        page_match = _PAGE_MARKER_RE.fullmatch(stripped)
        if page_match:
            output_lines.append(f"(* ====== Page {page_match.group(1)} ====== *)")
            continue

        if stripped.startswith("%"):
            comment = stripped[1:].strip()
            output_lines.append(f"(* {comment} *)" if comment else "")
            continue

        begin_match = _BEGIN_ENV_RE.fullmatch(stripped)
        if begin_match:
            env = begin_match.group(1)
            if env in _ALIGNMENT_ENVS:
                alignment_depth += 1
            if env in _SKIPPED_WRAPPER_ENVS:
                continue

        end_match = _END_ENV_RE.fullmatch(stripped)
        if end_match:
            env = end_match.group(1)
            if env in _ALIGNMENT_ENVS and alignment_depth > 0:
                alignment_depth -= 1
            if env in _SKIPPED_WRAPPER_ENVS:
                continue

        cleaned_line = _INLINE_COMMENT_RE.sub("", stripped).strip()
        if not cleaned_line:
            output_lines.append("")
            continue

        logical_lines = _split_logical_lines(cleaned_line, in_alignment=alignment_depth > 0)
        for logical_line in logical_lines:
            normalized = _normalize_tex_line(logical_line, in_alignment=alignment_depth > 0)
            if normalized:
                output_lines.append(_to_mathematica_line(normalized))

    return _join_lines(output_lines)


def _split_logical_lines(line: str, *, in_alignment: bool) -> list[str]:
    if not in_alignment:
        return [line]
    return [part.strip() for part in _ALIGN_ROW_SPLIT_RE.split(line)]


def _normalize_tex_line(line: str, *, in_alignment: bool) -> str:
    normalized = line.strip()
    if not normalized:
        return ""

    if in_alignment:
        normalized = _UNESCAPED_AMPERSAND_RE.sub("", normalized).strip()
    elif normalized.endswith(r"\\"):
        normalized = normalized[:-2].rstrip()

    return normalized


def _to_mathematica_line(tex_line: str) -> str:
    if "=" in tex_line:
        lhs, rhs = tex_line.split("=", 1)
        return (
            f'ToExpression["{_escape_mathematica_string(lhs.strip())}", TeXForm] '
            f'= ToExpression["{_escape_mathematica_string(rhs.strip())}", TeXForm]'
        )
    return f'ToExpression["{_escape_mathematica_string(tex_line.strip())}", TeXForm]'


def _escape_mathematica_string(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', r'\"')


def _join_lines(lines: list[str]) -> str:
    collapsed: list[str] = []
    previous_blank = False

    for line in lines:
        is_blank = line == ""
        if is_blank and previous_blank:
            continue
        collapsed.append(line)
        previous_blank = is_blank

    return "\n".join(collapsed).strip() + "\n"
