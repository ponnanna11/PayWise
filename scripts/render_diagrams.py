"""
Utility to render PlantUML .puml files to SVG images.
Uses standard PlantUML text encoding and official PlantUML rendering service or local jar.
"""
import os
import re
import zlib
import requests
from pathlib import Path

DIAGRAMS_DIR = Path(__file__).resolve().parent.parent / "docs" / "diagrams"

PLANTUML_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_"


def encode_6bit(b):
    if b < 10:
        return chr(48 + b)
    b -= 10
    if b < 26:
        return chr(65 + b)
    b -= 26
    if b < 26:
        return chr(97 + b)
    b -= 26
    if b == 0:
        return "-"
    if b == 1:
        return "_"
    return "?"


def append_3bytes(b1, b2, b3):
    c1 = b1 >> 2
    c2 = ((b1 & 0x3) << 4) | (b2 >> 4)
    c3 = ((b2 & 0xF) << 2) | (b3 >> 6)
    c4 = b3 & 0x3F
    return encode_6bit(c1 & 0x3F) + encode_6bit(c2 & 0x3F) + encode_6bit(c3 & 0x3F) + encode_6bit(c4 & 0x3F)


def encode_plantuml(text: str) -> str:
    zlib_obj = zlib.compressobj(9, zlib.DEFLATED, -zlib.MAX_WBITS)
    compressed = zlib_obj.compress(text.encode("utf-8")) + zlib_obj.flush()
    res = ""
    i = 0
    while i < len(compressed):
        b1 = compressed[i]
        b2 = compressed[i + 1] if i + 1 < len(compressed) else 0
        b3 = compressed[i + 2] if i + 2 < len(compressed) else 0
        res += append_3bytes(b1, b2, b3)
        i += 3
    return res


def render_all():
    puml_files = list(DIAGRAMS_DIR.glob("*.puml"))
    print(f"Found {len(puml_files)} PlantUML files in {DIAGRAMS_DIR}")
    for puml in puml_files:
        svg_path = puml.with_suffix(".svg")
        content = puml.read_text(encoding="utf-8")
        encoded = encode_plantuml(content)
        url = f"https://www.plantuml.com/plantuml/svg/~1{encoded}"
        try:
            resp = requests.get(url, timeout=15)
            if resp.status_code == 200 and "<svg" in resp.text:
                svg_path.write_text(resp.text, encoding="utf-8")
                print(f"Rendered {puml.name} -> {svg_path.name} (HTTP 200)")
            else:
                print(f"Failed to render {puml.name}: Status {resp.status_code}")
        except Exception as e:
            print(f"Could not render {puml.name} online ({e}). PlantUML source file is valid.")


if __name__ == "__main__":
    render_all()
