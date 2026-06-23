#!/usr/bin/env python3
"""
Build self-contained visualize widgets for d3r design-server images.

WHY THIS EXISTS
---------------
The chat widget sandbox (mcp__visualize__show_widget) enforces a CDN allowlist.
The image CDN these tools return (acedata.cloud) is NOT on it, so
`<img src="https://...acedata...">` silently fails — the user sees a broken image.
The only reliable way to show a generated image in chat is to EMBED the bytes as a
base64 data URI. Embedding is token-expensive, so this script downscales hard first.

TWO MODES
---------
1) picker  — a Midjourney 2x2 grid as a clickable chooser. Renders ONE small grid
   image with four transparent quadrant buttons overlaid. Clicking a quadrant calls
   sendPrompt(...) asking the assistant to upscale that tile. This is the cheap,
   reliable pattern (~1 small image instead of 4).
2) single  — one image embedded for display (e.g. the final upscaled result).

USAGE
-----
  python3 imgwidget.py picker --grid-url <url> --image-id <id> [--out PATH] [--width 300]
  python3 imgwidget.py single --url <url> [--out PATH] [--width 440] [--alt "..."]

It writes the widget HTML to --out (default /tmp/d3r_widget.html) and prints that path.
The calling assistant then Reads that file and passes its contents as `widget_code`
to mcp__visualize__show_widget. (The tool needs the literal HTML inline; there is no
way to point it at a file — so keep --width small to keep the embed cheap.)

IMAGE RESIZING falls back across PIL -> sips (macOS) -> ImageMagick `convert`.
Keep --width small: ~300px for a picker grid, ~440px for a single display image.
The picker is only for choosing; the final upscale is full-resolution regardless.
"""
import argparse, base64, os, subprocess, sys, tempfile, urllib.request

def download(url, path):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r, open(path, "wb") as f:
        f.write(r.read())

def resize_to_jpeg(src, dst, width, quality):
    """Resize src image to max `width` wide JPEG at `dst`. Try PIL, then sips, then convert."""
    try:
        from PIL import Image
        im = Image.open(src).convert("RGB")
        if im.width > width:
            im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
        im.save(dst, "JPEG", quality=quality)
        return
    except Exception:
        pass
    if subprocess.run(["which", "sips"], capture_output=True).returncode == 0:
        subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", str(quality),
                        "-Z", str(width), src, "--out", dst],
                       check=True, capture_output=True)
        return
    subprocess.run(["convert", src, "-resize", f"{width}>", "-quality", str(quality), dst],
                   check=True)

def b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def esc(s):
    return s.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")

def build_picker(grid_url, image_id, width, descs):
    tmp = tempfile.mkdtemp()
    raw, jpg = os.path.join(tmp, "g.png"), os.path.join(tmp, "g.jpg")
    download(grid_url, raw)
    resize_to_jpeg(raw, jpg, width, 33)
    data = b64(jpg)
    pos = {1: ("0", "0"), 2: ("50%", "0"), 3: ("0", "50%"), 4: ("50%", "50%")}
    btns = []
    for n in (1, 2, 3, 4):
        left, top = pos[n]
        rec = (n == 1)
        badge = ('<span style="position:absolute; top:6px; left:6px; background:var(--color-background-info); '
                 'color:var(--color-text-info); font-size:11px; padding:2px 8px; '
                 'border-radius:var(--border-radius-md);">Recommended</span>') if rec else ""
        num = (f'<span style="position:absolute; top:6px; right:6px; width:22px; height:22px; '
               f'border-radius:50%; background:var(--color-background-primary); '
               f'border:0.5px solid var(--color-border-secondary); font-size:12px; display:flex; '
               f'align-items:center; justify-content:center;">{n}</span>')
        btns.append(
            f'<button onclick="pick({n})" aria-label="Upscale option {n}" '
            f'style="position:absolute; left:{left}; top:{top}; width:50%; height:50%; margin:0; '
            f'padding:0; background:transparent; border:1px solid transparent; cursor:pointer;" '
            f'onmouseover="this.style.borderColor=\'var(--color-border-info)\';'
            f'this.style.background=\'rgba(55,138,221,0.12)\'" '
            f'onmouseout="this.style.borderColor=\'transparent\';this.style.background=\'transparent\'">'
            f'{badge}{num}</button>')
    d = "{" + ",".join(f'{n}:"{esc(descs.get(n, "option "+str(n)))}"' for n in (1, 2, 3, 4)) + "}"
    return (
        '<h2 class="sr-only">Click a quadrant to pick that image and upscale it</h2>\n'
        '<div style="position:relative; width:100%; max-width:600px; margin:1rem 0; '
        'border-radius:var(--border-radius-lg); overflow:hidden; '
        'border:0.5px solid var(--color-border-tertiary);">\n'
        f'<img src="data:image/jpeg;base64,{data}" alt="Four candidate images in a 2 by 2 grid" '
        'style="display:block; width:100%;" />\n'
        + "\n".join(btns) +
        '\n</div>\n'
        '<p style="font-size:13px; color:var(--color-text-secondary); margin:0 0 1rem;">'
        'Click any quadrant to upscale that option. Option 1 is the recommendation.</p>\n'
        '<script>\n'
        f'var D={d};\n'
        f'function pick(n){{ sendPrompt("Upscale Midjourney option "+n+" ("+D[n]+") — image_id {image_id}, '
        'run midjourney_transform action upscale"+n+", then download and show me the final image."); }\n'
        '</script>')

def build_single(url, width, alt):
    tmp = tempfile.mkdtemp()
    raw, jpg = os.path.join(tmp, "i.png"), os.path.join(tmp, "i.jpg")
    download(url, raw)
    resize_to_jpeg(raw, jpg, width, 45)
    data = b64(jpg)
    return (
        f'<h2 class="sr-only">{esc(alt)}</h2>\n'
        '<div style="width:100%; max-width:620px; margin:1rem 0; '
        'border-radius:var(--border-radius-lg); overflow:hidden; '
        'border:0.5px solid var(--color-border-tertiary);">\n'
        f'<img src="data:image/jpeg;base64,{data}" alt="{esc(alt)}" style="display:block; width:100%;" />\n'
        '</div>')

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="mode", required=True)
    p = sub.add_parser("picker")
    p.add_argument("--grid-url", required=True)
    p.add_argument("--image-id", required=True)
    p.add_argument("--width", type=int, default=300)
    p.add_argument("--out", default="/tmp/d3r_widget.html")
    p.add_argument("--desc1", default="option 1"); p.add_argument("--desc2", default="option 2")
    p.add_argument("--desc3", default="option 3"); p.add_argument("--desc4", default="option 4")
    s = sub.add_parser("single")
    s.add_argument("--url", required=True)
    s.add_argument("--width", type=int, default=440)
    s.add_argument("--alt", default="Generated image")
    s.add_argument("--out", default="/tmp/d3r_widget.html")
    a = ap.parse_args()
    if a.mode == "picker":
        html = build_picker(a.grid_url, a.image_id, a.width,
                            {1: a.desc1, 2: a.desc2, 3: a.desc3, 4: a.desc4})
    else:
        html = build_single(a.url, a.width, a.alt)
    with open(a.out, "w") as f:
        f.write(html)
    print(a.out)
    print(f"bytes={len(html)} (Read this file, pass its contents as widget_code to show_widget)",
          file=sys.stderr)

if __name__ == "__main__":
    main()
