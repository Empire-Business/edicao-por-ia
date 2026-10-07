#!/usr/bin/env python3
"""Build short, consistent names for user-facing video previews and finals."""
from __future__ import annotations
import argparse
import math
import re
import unicodedata
from pathlib import Path


PROPORTIONS = {"9:16": "9x16", "16:9": "16x9", "1:1": "1x1", "4:5": "4x5", "5:4": "5x4"}


def slug(value: str, label: str, limit: int = 40) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must not be empty")
    normalized = unicodedata.normalize("NFKD", value.strip())
    ascii_value = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    result = re.sub(r"[^A-Za-z0-9]+", "-", ascii_value).strip("-").lower()[:limit].rstrip("-")
    if not result:
        raise ValueError(f"{label} needs at least one letter or number")
    return result


def proportion_label(value: str) -> str:
    if value in PROPORTIONS:
        return PROPORTIONS[value]
    match = re.fullmatch(r"(\d+)x(\d+)", value or "", re.IGNORECASE)
    if match and int(match.group(1)) > 0 and int(match.group(2)) > 0:
        width,height=map(int,match.groups()); divisor=math.gcd(width,height)
        return f"{width//divisor}x{height//divisor}"
    raise ValueError("proportion must look like 9:16 or 9x16")


def output_filename(name: str, proportion: str, format_id: str, version: int,
                    kind: str = "final", extension: str = "mp4", variant: str | None = None, visual_id: str | None = None, edition_code: str | None = None) -> str:
    if type(version) is not int or version < 1:
        raise ValueError("version must be a positive integer")
    if kind not in {"preview", "final"}:
        raise ValueError("kind must be preview or final")
    ext = extension.lower().lstrip(".")
    if not re.fullmatch(r"[a-z0-9]{2,5}", ext):
        raise ValueError("invalid video extension")
    profile=format_id.upper() if re.fullmatch(r'(?:FP|F)[0-9]{2,}',format_id or '',re.I) else slug(format_id or "sem-formato", "format", 20)
    parts = [slug(name, "video name"), proportion_label(proportion), profile]
    if visual_id:
        if not re.fullmatch(r'(?:IDP|ID)[0-9]{2,}',visual_id,re.I):raise ValueError('Código de ID visual inválido')
        parts.append(visual_id.upper())
    if edition_code:
        if not re.fullmatch(r'(?:EP|E)[0-9]{2,}',edition_code,re.I):raise ValueError('Código de edição inválido')
        parts.insert(0,edition_code.upper())
    if variant:
        parts.append(slug(variant, "variant", 16).upper())
    if kind == "preview":
        parts.append("PREVIEW")
    parts.append(f"{'VP' if edition_code and edition_code.upper().startswith('EP') else 'V'}{version}")
    return "_".join(parts) + "." + ext


def next_version(directory: str | Path, name: str, format_id: str,
                 kind: str = "final", extension: str = "mp4",
                 variant: str | None = None, visual_id: str | None = None, edition_code: str | None = None) -> int:
    """Return the next version for a video/profile/kind, shared across proportions."""
    if kind not in {"preview", "final"}:
        raise ValueError("kind must be preview or final")
    ext = extension.lower().lstrip(".")
    video = ((edition_code.upper()+"_") if edition_code else "") + slug(name, "video name")
    profile = (format_id.upper() if re.fullmatch(r"(?:FP|F)[0-9]{2,}",format_id or "",re.I) else slug(format_id or "sem-formato", "format", 20)) + (("_"+visual_id.upper()) if visual_id else "")
    variant_part = f"_{slug(variant, 'variant', 16).upper()}" if variant else ""
    stage = r"_PREVIEW" if kind == "preview" else ""
    revision='VP' if edition_code and edition_code.upper().startswith('EP') else 'V'
    pattern = re.compile(rf"^{re.escape(video)}_\d+x\d+_{re.escape(profile)}{variant_part}{stage}_{revision}(\d+)\.{re.escape(ext)}$", re.IGNORECASE)
    versions = []
    for path in Path(directory).glob("*"):
        match = pattern.fullmatch(path.name)
        if match:
            versions.append(int(match.group(1)))
    return max(versions, default=0) + 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True, help="Video title/name (or source filename stem)")
    parser.add_argument("--proportion", required=True, help="For example 9:16 or 16:9")
    parser.add_argument("--format", default="sem-formato", help="Short format profile ID")
    parser.add_argument("--visual-id");parser.add_argument("--edition-code")
    parser.add_argument("--kind", choices=("preview", "final"), default="preview")
    parser.add_argument("--version", type=int, help="Positive version number; defaults to the next available")
    parser.add_argument("--directory", type=Path, default=Path("renders"))
    parser.add_argument("--variant", help="Optional short variant label, placed before PREVIEW/Vn")
    parser.add_argument("--extension", default="mp4")
    args = parser.parse_args()
    version = args.version if args.version is not None else next_version(
        args.directory, args.name, args.format, args.kind, args.extension, args.variant, args.visual_id, args.edition_code)
    path = args.directory / output_filename(args.name, args.proportion, args.format,
        version, args.kind, args.extension, args.variant, args.visual_id, args.edition_code)
    print(path)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValueError as error:
        raise SystemExit(str(error))
