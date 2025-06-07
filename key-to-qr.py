#!/usr/bin/env python3
import json
import subprocess
import sys
import os
from datetime import datetime
from lxml import etree
import tempfile
import argparse
import textwrap

# Extracts the scalar and optional comment from the given OpenSSH private key file
def extract_scalar_and_comment(key_path):
    try:
        result = subprocess.run(
            ["./extract-scalar.py", key_path],
            check=True,
            stdout=subprocess.PIPE,
            text=True
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        sys.stderr.write(f"Error extracting scalar: {e}\n")
        sys.exit(1)

# Generates a QR code in SVG format using qrencode for the given scalar data
def generate_svg_qr(data):
    try:
        result = subprocess.run(
            ["qrencode", "-t", "SVG", "-l", "H"],
            input=data,
            check=True,
            stdout=subprocess.PIPE,
            text=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        sys.stderr.write(f"Error generating QR code: {e}\n")
        sys.exit(1)

# Inserts label metadata below the QR code and resizes it appropriately for receipt printing
def insert_label(svg_content, label_dict, filename_label=None, target_width_px=575):
    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.fromstring(svg_content.encode(), parser)

    rects = root.findall(".//{http://www.w3.org/2000/svg}rect")
    max_x = max_y = 0
    for rect in rects:
        x = float(rect.get("x", "0"))
        y = float(rect.get("y", "0"))
        max_x = max(max_x, x)
        max_y = max(max_y, y)

    module_count = max(int(max_x), int(max_y)) + 1
    qr_size = 520  # increased fixed QR code size
    scale = qr_size // module_count
    qr_size = module_count * scale  # recalculate to keep it exact

    line_height = 26
    char_width_px = 10
    key_x = 26
    val_x = 140  # spacing between label keys and values
    value_width_px = target_width_px - val_x - 10
    value_wrap_chars = max(1, int(value_width_px // char_width_px) - 8)

    label_lines = []
    for key, val in label_dict.items():
        wrapped_val_lines = textwrap.wrap(val, width=value_wrap_chars)
        label_lines.append((f"{key}:", wrapped_val_lines[0] if wrapped_val_lines else ""))
        for extra_line in wrapped_val_lines[1:]:
            label_lines.append(("", extra_line))

    label_height = len(label_lines) * line_height + 30
    title_lines = textwrap.wrap(filename_label, width=26) if filename_label else []
    title_font_size = 34
    title_height = title_font_size * len(title_lines) if filename_label else 0
    title_margin_top = 12 if filename_label else 0
    title_margin_bottom = 20 if filename_label else 0
    qr_top_margin = 0
    qr_bottom_margin = 20
    total_height = title_margin_top + title_height + title_margin_bottom + qr_size + qr_bottom_margin + label_height

    qr_offset_x = (target_width_px - qr_size - 8) // 2
    for rect in rects:
        x = float(rect.get("x", "0")) * scale + qr_offset_x
        y = float(rect.get("y", "0")) * scale + title_margin_top + title_height + title_margin_bottom
        rect.set("x", str(int(x)))
        rect.set("y", str(int(y)))
        rect.set("width", str(scale))
        rect.set("height", str(scale))

    root.set("width", str(target_width_px))
    root.set("height", str(total_height))
    root.set("viewBox", f"0 0 {target_width_px} {total_height}")

    if title_lines:
        for i, line in enumerate(title_lines):
            y = title_margin_top + (i + 1) * title_font_size
            title_el = etree.Element("text", x=str(target_width_px // 2), y=str(y), attrib={
                "font-size": str(title_font_size),
                "font-family": "monospace",
                "text-anchor": "middle"
            })
            title_el.text = line
            root.append(title_el)

    for i, (key, val) in enumerate(label_lines):
        y = title_margin_top + title_height + title_margin_bottom + qr_size + qr_bottom_margin + 30 + i * line_height

        if key:
            key_el = etree.Element("text", x=str(key_x), y=str(y), attrib={
                "font-size": "20",
                "font-family": "monospace"
            })
            key_el.text = key
            root.append(key_el)

        if val:
            val_el = etree.Element("text", x=str(val_x), y=str(y), attrib={
                "font-size": "20",
                "font-family": "monospace"
            })
            val_el.text = val
            root.append(val_el)

    border = etree.Element("rect", attrib={
        "x": "0",
        "y": "0",
        "width": str(target_width_px),
        "height": str(total_height),
        "fill": "none",
        "stroke": "black",
        "stroke-width": "2"
    })
    root.insert(0, border)

    return etree.tostring(root, pretty_print=True, encoding="unicode")

# Constructs label metadata dictionary
def build_label_dict(comment):
    items = {
        "Content": "ssh Ed25519 scalar",
        "Comment": comment if comment else None,
        "Created": datetime.now().strftime('%Y-%m-%d %H:%M'),
        "Format": "json",
        "Schema": "[base64_scalar,comment]",
        "Tools": "github.com/mike-cr/ssh-qr-tools",
    }
    return {k: v for k, v in items.items() if v is not None}

def main():
    parser = argparse.ArgumentParser(description="Generate a labeled QR code from an OpenSSH Ed25519 key")
    parser.add_argument("key_path", nargs="?", help="Path to id_ed25519 file")
    parser.add_argument("--stdout", action="store_true", help="Print SVG to stdout")
    parser.add_argument("--svg", metavar="FILE", help="Write SVG to file")
    parser.add_argument("--pdf", metavar="FILE", help="Write PDF to file")
    parser.add_argument("--png", metavar="FILE", help="Write PNG to file")
    parser.add_argument("--print", action="store_true", help="Send to printer")
    args = parser.parse_args()

    if not args.key_path or not (args.stdout or args.svg or args.pdf or args.png or args.print):
        parser.print_usage()
        sys.exit(1)

    data = extract_scalar_and_comment(args.key_path)
    scalar = data[0]
    comment = data[1] if len(data) > 1 else ""
    filename = os.path.basename(args.key_path)
    label_dict = build_label_dict(comment)
    svg = generate_svg_qr(json.dumps([scalar, comment], separators=(",", ":")))
    final_svg = insert_label(svg, label_dict, filename_label=filename)

    if args.stdout:
        print(final_svg)

    if args.svg:
        with open(args.svg, "w") as f:
            f.write(final_svg)
        print(f"🖼️  SVG saved to {args.svg}")

    if args.pdf:
        subprocess.run(["rsvg-convert", "-f", "pdf", "-o", args.pdf], input=final_svg.encode(), check=True)
        print(f"📄 PDF saved to {args.pdf}")

    if args.png:
        subprocess.run(["rsvg-convert", "-b", "white", "-f", "png", "-o", args.png], input=final_svg.encode(), check=True)
        print(f"🖼️  PNG saved to {args.png}")

    if args.print:
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".svg") as tmp_svg:
            tmp_svg.write(final_svg)
            tmp_svg.flush()
            with tempfile.NamedTemporaryFile("wb", delete=False, suffix=".pdf") as tmp_pdf:
                subprocess.run(["rsvg-convert", "-f", "pdf", "-o", tmp_pdf.name, tmp_svg.name], check=True)
                subprocess.run(["lp", tmp_pdf.name], check=True)
        print("📨  Printed successfully")

if __name__ == "__main__":
    main()

