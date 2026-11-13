#!/usr/bin/env python3
"""Capture illustrations for a workshop: screenshots and GIFs, driven from a URL.

    capture.py probe  <url>                       list selectors worth targeting
    capture.py shot   <url> -o img/etape0.png [--selector "#game"] [--wait 2]
    capture.py run    recipe.json                 a scripted sequence (clicks, typing, gifs)

Runs headless Chromium through Playwright. GIFs are built from frames with ffmpeg.
Every capture uses the same viewport and a 2x pixel density, so a workshop's images look like
one set rather than a collection — which is what a reviewer notices first.

Interpreter: /home/kc/.claude/.venvs/capture/bin/python (see SKILL.md if it is missing).
"""
import argparse, io, json, os, re, shutil, subprocess, sys, tempfile, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import annotate as ann
from PIL import Image

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sys.exit("playwright absent — voir SKILL.md, section Installation")

DEFAULT_VIEWPORT = (1280, 800)
DEFAULT_SCALE = 2

HIDE_SCROLLBARS = """
::-webkit-scrollbar { display: none !important; }
* { scrollbar-width: none !important; }
"""
FREEZE = """
*, *::before, *::after {
  animation-play-state: paused !important;
  transition: none !important;
  caret-color: transparent !important;
}
"""


def new_page(pw, cfg):
    browser = pw.chromium.launch()
    vp = cfg.get("viewport", DEFAULT_VIEWPORT)
    ctx = browser.new_context(
        viewport={"width": vp[0], "height": vp[1]},
        device_scale_factor=cfg.get("scale", DEFAULT_SCALE),
        color_scheme=cfg.get("theme", "light"),
        reduced_motion="no-preference",
        locale=cfg.get("locale", "fr-FR"),
    )
    page = ctx.new_page()
    return browser, page


def install_keycast(page, cfg):
    """Show each key pressed, in the page, for recipes that film something being typed."""
    opts = cfg.get("keycast")
    if not opts:
        return
    opts = {} if opts is True else dict(opts)
    page.add_init_script(f"(() => {{ const run = () => ({KEYCAST_JS})([{json.dumps(opts)}]);"
                         " document.readyState === 'loading'"
                         " ? addEventListener('DOMContentLoaded', run) : run(); })()")


def prepare(page, cfg, freeze):
    page.add_style_tag(content=HIDE_SCROLLBARS)
    if freeze:
        page.add_style_tag(content=FREEZE)
    for sel in cfg.get("hide", []):
        try:
            page.eval_on_selector_all(sel, "els => els.forEach(e => e.style.visibility='hidden')")
        except Exception:
            pass


def target(page, selector):
    return page.locator(selector) if selector else page


def do_shot(page, path, selector=None, full=False):
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    if selector:
        page.locator(selector).screenshot(path=path)
    else:
        page.screenshot(path=path, full_page=full)
    kb = os.path.getsize(path) / 1024
    print(f"  {path}  ({kb:.0f} Ko)")
    return path


def do_gif(page, path, selector=None, seconds=4.0, fps=8, during=(), act=None, step=None, dither=None):
    """Capture frames at `fps`. `during` steps run at their `at` second, between two frames, so a
    GIF can show something being typed, clicked or run rather than only its result.

    `step` is a JS expression run in the page before every frame, for a runtime whose clock the
    page controls (a game loop it can advance by hand). The film is then counted in frames, not in
    seconds on the wall: `at` is a time *in the GIF*, and a slow screenshot cannot speed the
    animation up or move a key press.

    `dither` is ffmpeg's paletteuse mode. The default (ordered) suits a page with gradients and
    anti-aliased text; `"none"` is for pixel art and flat colours, which it would speckle."""
    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg absent : impossible de fabriquer un GIF")
    tmp = tempfile.mkdtemp(prefix="frames")
    n = max(2, int(seconds * fps))
    delay = max(0, (1.0 / fps) * 1000 - 40)
    pending = sorted(during, key=lambda d: float(d.get("at", 0)))
    start = time.monotonic()
    for i in range(n):
        now = i / fps if step else time.monotonic() - start
        while pending and float(pending[0].get("at", 0)) <= now:
            act(page, pending.pop(0))
        if step:
            page.evaluate(step)
        f = os.path.join(tmp, f"f{i:04d}.png")
        if selector:
            page.locator(selector).screenshot(path=f)
        else:
            page.screenshot(path=f)
        if delay and not step:
            page.wait_for_timeout(delay)
    for st in pending:                      # anything scheduled past the end still runs
        act(page, st)
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    pal = os.path.join(tmp, "pal.png")
    common = ["-y", "-loglevel", "error", "-framerate", str(fps), "-i", os.path.join(tmp, "f%04d.png")]
    subprocess.run(["ffmpeg", *common, "-vf", "palettegen=stats_mode=diff", pal], check=True)
    subprocess.run(["ffmpeg", *common, "-i", pal, "-lavfi",
                    "paletteuse=dither=" + (dither or "bayer:bayer_scale=3"), path], check=True)
    shutil.rmtree(tmp, ignore_errors=True)
    kb = os.path.getsize(path) / 1024
    print(f"  {path}  ({kb:.0f} Ko, {n} images, {fps} i/s)")
    if kb > 2000:
        print("    ⚠ au-dessus de 2 Mo : réduis seconds, fps, ou cible un sélecteur plus petit")
    return path


MANIM_PY = os.path.expanduser("~/.claude/.venvs/manim/bin/manim")


def do_anim(scene_file, scene, path, fps=15, width=1920, quality="h", video=True, image_width=960):
    """Render a manim scene to an animated image, and to a video with chapters.

    manim writes an mp4; an animated image (WebP, or GIF if `path` ends in
    .gif) is what a markdown page and GitHub show inline with no player. With
    `video`, the same frames also go to a `.webm` beside it (VP9, smaller than
    the WebP, true colours) plus a `.vtt` of chapters, one per manim section
    (`self.next_section("÷ 8 : plus large")` in the scene): that is what the
    workshop platform plays with its own controls, previous and next state
    included (convention §3.8d). The video is rendered at `width` (1080p by
    default, so the text stays crisp full screen); the animated image at
    `image_width`, since it is the fallback and GitHub's readers download it
    too. The venv is the skill's own (SKILL.md, « Animations »).
    Returns (image, video or None, vtt or None)."""
    if not os.path.isfile(MANIM_PY):
        sys.exit("manim absent : python3 -m venv ~/.claude/.venvs/manim && "
                 "~/.claude/.venvs/manim/bin/pip install manim")
    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg absent : impossible de fabriquer une animation")
    media = tempfile.mkdtemp(prefix="manim")
    height = round(width * 9 / 32) * 2      # even: h264 refuses an odd height
    subprocess.run([MANIM_PY, "render", "-q", quality, "--fps", str(fps), "-r", f"{width},{height}",
                    "--progress_bar", "none", "--save_sections",
                    "--format", "mp4", "--media_dir", media, scene_file, scene],
                   check=True, stdout=subprocess.DEVNULL)
    mp4s = [os.path.join(r, f) for r, _, fs in os.walk(media) for f in fs if f == scene + ".mp4"]
    if not mp4s:
        sys.exit("manim n'a pas produit de vidéo")
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    scale = f"fps={fps},scale={width}:-2:flags=lanczos"
    scale_image = f"fps={fps},scale={min(width, image_width)}:-2:flags=lanczos"
    if path.lower().endswith(".gif"):
        pal = os.path.join(media, "pal.png")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp4s[0], "-vf",
                        f"{scale_image},palettegen=stats_mode=diff", pal], check=True)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp4s[0], "-i", pal, "-lavfi",
                        f"{scale_image}[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=3", path], check=True)
    else:
        # -loop 0: forever, like a GIF. -q:v 75: lossy, invisible on a dark figure.
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp4s[0], "-vf", scale_image,
                        "-c:v", "libwebp", "-lossless", "0", "-q:v", "75", "-loop", "0", "-an", path],
                       check=True)
    kb = os.path.getsize(path) / 1024
    print(f"  {path}  ({kb:.0f} Ko, {fps} i/s, {min(width, image_width)} px)")
    if kb > 2000:
        print("    ⚠ au-dessus de 2 Mo : réduis fps ou width, ou raccourcis la scène")

    webm = vtt = None
    if video:
        stem = os.path.splitext(path)[0]
        webm, vtt = stem + ".webm", stem + ".vtt"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp4s[0], "-vf", scale,
                        "-c:v", "libvpx-vp9", "-b:v", "0", "-crf", "34", "-row-mt", "1", "-an", webm],
                       check=True)
        chapters = manim_chapters(media, scene)
        with open(vtt, "w", encoding="utf-8") as fh:
            fh.write("WEBVTT\n\n")
            for start, end, name in chapters:
                fh.write(f"{_vtt_time(start)} --> {_vtt_time(end)}\n{name}\n\n")
        print(f"  {webm}  ({os.path.getsize(webm) / 1024:.0f} Ko, {width} px), {vtt}  ({len(chapters)} chapitre(s))")
    shutil.rmtree(media, ignore_errors=True)
    return path, webm, vtt


def manim_chapters(media, scene):
    """[(start, end, name)] from manim's sections JSON, one chapter per named section.

    manim opens an unnamed section at the start of every scene; what the author
    puts before the first `next_section` is folded into the first named one,
    and a scene with no sections at all is one chapter named after itself."""
    found = [os.path.join(r, f) for r, _, fs in os.walk(media) for f in fs if f == scene + ".json"]
    sections = json.load(open(found[0], encoding="utf-8")) if found else []
    chapters, t = [], 0.0
    for sec in sections:
        d = float(sec.get("duration", 0))
        name = sec.get("name", "")
        if name == "autocreated" or not name.strip():
            if chapters:
                chapters[-1][1] += d
            else:
                chapters.append([0.0, d, ""])
        elif chapters and chapters[-1][2] == "":
            chapters[-1][1] += d
            chapters[-1][2] = name
        else:
            chapters.append([t, t + d, name])
        t += d
    if not chapters:
        chapters = [[0.0, t, scene]]
    if chapters[0][2] == "":
        chapters[0][2] = scene
    return [(a, b, n) for a, b, n in chapters]


def _vtt_time(seconds):
    m, s = divmod(seconds, 60)
    return f"{int(m):02d}:{s:06.3f}"


def anim_marker(md_path, img_path, webm, vtt):
    """The `ws:anim` marker (convention §3.8d) on the line after the image, replaced if present."""
    rel = lambda p: os.path.relpath(os.path.abspath(p), os.path.dirname(os.path.abspath(md_path)))
    line = f"<!-- ws:anim {{src: {rel(webm)}" + (f", chapters: {rel(vtt)}" if vtt else "") + "} -->"
    src = io.open(md_path, encoding="utf-8").read()
    img = f"]({rel(img_path)})"
    out, done = [], False
    lines = src.split("\n")
    for i, l in enumerate(lines):
        out.append(l)
        if not done and l.startswith("![") and l.rstrip().endswith(img):
            if i + 1 < len(lines) and lines[i + 1].lstrip().startswith("<!-- ws:anim"):
                lines[i + 1] = line
            else:
                out.append(line)
            done = True
    if done:
        io.open(md_path, "w", encoding="utf-8").write("\n".join(out))
        print(f"    → {os.path.basename(md_path)} : {line}")


def _rect_of(page, selector, origin, scale):
    b = page.locator(selector).bounding_box()
    if not b:
        print(f"    (sélecteur introuvable, annotation ignorée : {selector})")
        return None
    return [(b["x"] - origin[0]) * scale, (b["y"] - origin[1]) * scale,
            b["width"] * scale, b["height"] * scale]


def resolve_annotations(page, spec, origin, scale):
    """Turn selector-based annotations into pixel operations for annotate.py."""
    ops = []
    cfg_scale_hint = [max(1.0, scale)]
    for a in spec:
        if "box" in a:
            r = _rect_of(page, a["box"], origin, scale)
            if r: ops.append({"op": "box", "rect": r, "width": a.get("width", 4)})
        elif "spotlight" in a:
            r = _rect_of(page, a["spotlight"], origin, scale)
            if r: ops.append({"op": "spotlight", "rect": r, "dim": a.get("dim", 0.55)})
        elif "blur" in a:
            r = _rect_of(page, a["blur"], origin, scale)
            if r: ops.append({"op": "blur", "rect": r})
        elif "arrow" in a:
            f = _rect_of(page, a["arrow"]["from"], origin, scale)
            t = _rect_of(page, a["arrow"]["to"], origin, scale)
            if f and t:
                import math as _m
                fc = (f[0] + f[2] / 2, f[1] + f[3] / 2)
                tc = (t[0] + t[2] / 2, t[1] + t[3] / 2)
                # pointe sur le BORD de la cible, avec un petit écart : une pointe posée au
                # centre disparaît derrière l'objet qu'elle désigne
                dx, dy = fc[0] - tc[0], fc[1] - tc[1]
                n = _m.hypot(dx, dy) or 1
                ux, uy = dx / n, dy / n
                hw, hh = t[2] / 2, t[3] / 2
                k = min(hw / abs(ux) if ux else 1e9, hh / abs(uy) if uy else 1e9)
                gap = 10 * cfg_scale_hint[0]
                ops.append({"op": "arrow", "from": list(fc),
                            "to": [tc[0] + ux * (k + gap), tc[1] + uy * (k + gap)]})
        elif "crop" in a:
            r = _rect_of(page, a["crop"], origin, scale)
            if r: ops.append({"op": "crop", "rect": r})
    return ops


def apply_annotations(path, ops):
    if not ops:
        return
    img = Image.open(path).convert("RGB")
    img = ann.apply_ops(img, ops)
    img.save(path)
    print(f"    + {len(ops)} annotation(s)")


MARKER_RE = re.compile(r"^.*\[CAPTURE À FAIRE\s*:?[^\]]*\].*$", re.M)


def insert_image(md_path, img_path, alt, marker=None, after=None, before=None, dry=False):
    """Put ![alt](relative/path) into a markdown file, and report exactly what changed.

    Anchors, in order of precedence: an explicit `marker` substring to replace (typically a
    [CAPTURE À FAIRE] line left by a review), then `after`/`before` a line containing that text.
    Re-running is safe: an image already referenced by the same path is replaced in place rather
    than appended a second time.
    """
    md_path = os.path.abspath(md_path)
    if not os.path.isfile(md_path):
        print(f"    ! fichier introuvable, insertion ignorée : {md_path}")
        return
    rel = os.path.relpath(os.path.abspath(img_path), os.path.dirname(md_path))
    line = f"![{alt}]({rel})"
    src = io.open(md_path, encoding="utf-8").read()
    how = None

    if f"]({rel})" in src:                       # déjà présent : on remplace sur place
        src = re.sub(r"^!\[[^\]]*\]\(" + re.escape(rel) + r"\)[ \t]*$", line, src, flags=re.M)
        how = "remplacée (même chemin)"
    elif marker and marker in src:
        src = src.replace(marker, line, 1)
        how = "à la place du marqueur"
    elif marker is None and after is None and before is None and MARKER_RE.search(src):
        src = MARKER_RE.sub(line, src, count=1)
        how = "à la place du premier [CAPTURE À FAIRE]"
    elif after or before:
        needle = after or before
        out, done = [], False
        for l in src.split("\n"):
            if not done and needle in l:
                if after:
                    out += [l, "", line]
                else:
                    out += [line, "", l]
                done = True
                continue
            out.append(l)
        if not done:
            print(f"    ! ancre absente ({needle!r}), insertion ignorée")
            return
        src = "\n".join(out)
        how = f"{'après' if after else 'avant'} {needle!r}"
    else:
        src = src.rstrip("\n") + "\n\n" + line + "\n"
        how = "ajoutée à la fin"

    if dry:
        print(f"    [essai] {os.path.basename(md_path)} : {line}  ({how})")
        return
    io.open(md_path, "w", encoding="utf-8").write(src)
    print(f"    → {os.path.basename(md_path)} : {line}  ({how})")


def cmd_markers(args):
    """Lister les [CAPTURE À FAIRE] d'un ou plusieurs .md — ce qu'il reste à photographier."""
    total = 0
    for f in args.files:
        src = io.open(f, encoding="utf-8").read()
        for i, l in enumerate(src.split("\n"), 1):
            if "CAPTURE À FAIRE" in l:
                print(f"{os.path.basename(f)}:{i}  {l.strip()[:120]}")
                total += 1
    print(f"\n{total} capture(s) à faire")


def cmd_probe(args):
    with sync_playwright() as pw:
        browser, page = new_page(pw, {})
        page.goto(args.url, wait_until="load")
        page.wait_for_timeout(int(args.wait * 1000))
        info = page.evaluate("""() => {
          const q = (s) => Array.from(document.querySelectorAll(s));
          const vis = (e) => { const r = e.getBoundingClientRect();
                               return r.width > 30 && r.height > 20; };
          const nm = (e) => e.id ? '#'+e.id
                    : (e.getAttribute('data-testid') ? `[data-testid="${e.getAttribute('data-testid')}"]`
                    : (e.className && typeof e.className === 'string' && e.className.trim()
                       ? e.tagName.toLowerCase()+'.'+e.className.trim().split(/\\s+/)[0] : e.tagName.toLowerCase()));
          const box = (e) => { const r = e.getBoundingClientRect();
                               return `${Math.round(r.width)}x${Math.round(r.height)}`; };
          return {
            title: document.title,
            panes: q('main,section,div,canvas,iframe,pre,textarea').filter(vis)
                    .filter(e => { const r = e.getBoundingClientRect();
                                   return r.width > 200 && r.height > 120; })
                    .slice(0, 14).map(e => `${nm(e)}  ${box(e)}  <${e.tagName.toLowerCase()}>`),
            buttons: q('button,[role=button],a.btn,input[type=submit]').filter(vis)
                    .slice(0, 14).map(e => `${nm(e)}  « ${(e.innerText||e.value||'').trim().slice(0,30)} »`),
            inputs: q('input,textarea,[contenteditable=true],.cm-content,.monaco-editor').filter(vis)
                    .slice(0, 10).map(e => `${nm(e)}  <${e.tagName.toLowerCase()}>`),
            frames: q('iframe').map(e => `${nm(e)}  src=${(e.getAttribute('src')||'').slice(0,60)}`)
          };
        }""")
        print(f"\ntitre : {info['title']}\n")
        for k, label in [("panes", "Zones capturables"), ("buttons", "Boutons"),
                         ("inputs", "Champs de saisie / éditeurs"), ("frames", "iframes")]:
            if info[k]:
                print(f"--- {label}")
                for line in info[k]:
                    print("   " + line)
                print()
        if info["frames"]:
            print("Note : du contenu dans une iframe se cible avec \"frame\" dans la recette.")
        browser.close()


def cmd_shot(args):
    with sync_playwright() as pw:
        cfg = {"viewport": tuple(map(int, args.viewport.split("x"))), "scale": args.scale,
               "theme": args.theme}
        browser, page = new_page(pw, cfg)
        page.goto(args.url, wait_until="load")
        if args.wait_for:
            page.wait_for_selector(args.wait_for, timeout=30000)
        page.wait_for_timeout(int(args.wait * 1000))
        prepare(page, cfg, freeze=not args.animate)
        do_shot(page, args.out, args.selector, args.full)
        browser.close()
    if args.into:
        insert_image(args.into, args.out, args.alt or "capture", args.marker, args.after)
    else:
        print(f"\nÀ coller : ![{args.alt or 'capture'}]({args.out})")


# Affichage des touches, façon showmethekey / KeyCastr : chaque touche frappée apparaît un instant
# dans un coin de la zone capturée. Le navigateur dessine ces touches DANS la page, avec sa police :
# rien n'est peint sur l'image après coup (voir SKILL.md, "Labels: only from the runtime").
KEYCAST_JS = """([opts]) => {
  if (window.__captureKeycast) return;
  window.__captureKeycast = true;
  const LABELS = {
    Enter: '\u21b5', Escape: 'Esc', Tab: '\u21e5', Backspace: '\u232b', Delete: 'Suppr',
    ArrowUp: '\u2191', ArrowDown: '\u2193', ArrowLeft: '\u2190', ArrowRight: '\u2192',
    ' ': 'Espace', Control: 'Ctrl', Shift: '\u21e7', Alt: 'Alt', Meta: '\u2318',
    Home: 'Home', End: 'End', PageUp: 'PgUp', PageDown: 'PgDn',
  };
  const box = document.createElement('div');
  box.dataset.captureKeycast = '';
  // resolved on each use: the pane may not exist yet when this runs
  const side = opts.position || 'bottom-right';
  Object.assign(box.style, {
    position: 'fixed', zIndex: 2147483647, pointerEvents: 'none', display: 'flex',
    gap: '6px', alignItems: 'center', margin: 0, padding: 0,
    fontFamily: getComputedStyle(document.body).fontFamily || 'system-ui, sans-serif',
    fontSize: (opts.size || 15) + 'px', lineHeight: 1,
  });
  document.body.appendChild(box);
  const place = () => {
    const anchor = opts.selector ? document.querySelector(opts.selector) : null;
    const r = anchor ? anchor.getBoundingClientRect()
                     : { left: 0, top: 0, right: innerWidth, bottom: innerHeight };
    const pad = opts.margin === undefined ? 12 : opts.margin;
    const bottom = !side.startsWith('top');
    box.style.left = (side.endsWith('left') ? r.left + pad : 'auto') + (side.endsWith('left') ? 'px' : '');
    box.style.right = side.endsWith('left') ? 'auto' : (innerWidth - r.right + pad) + 'px';
    box.style.top = bottom ? 'auto' : (r.top + pad) + 'px';
    box.style.bottom = bottom ? (innerHeight - r.bottom + pad) + 'px' : 'auto';
  };
  place();
  addEventListener('resize', place, true);
  addEventListener('scroll', place, true);

  const chip = (text) => {
    place();
    const el = document.createElement('kbd');
    el.textContent = text;
    Object.assign(el.style, {
      background: opts.background || 'rgba(20, 20, 24, 0.86)', color: opts.color || '#fff',
      border: '1px solid rgba(255, 255, 255, 0.35)', borderRadius: '6px',
      padding: '0.25em 0.55em', font: 'inherit', boxShadow: '0 2px 6px rgba(0, 0, 0, 0.45)',
      transition: 'opacity 180ms linear', whiteSpace: 'nowrap',
    });
    box.appendChild(el);
    while (box.children.length > (opts.max || 4)) box.firstChild.remove();
    setTimeout(() => { el.style.opacity = '0'; setTimeout(() => el.remove(), 200); },
               (opts.keep === undefined ? 1.1 : opts.keep) * 1000);
  };

  addEventListener('keydown', (e) => {
    if (e.repeat) return;
    if (['Control', 'Shift', 'Alt', 'Meta'].includes(e.key)) return;   // only shown in a combo
    let text = LABELS[e.key] || e.key;
    const mods = [e.ctrlKey && 'Ctrl', e.altKey && 'Alt', e.metaKey && LABELS.Meta,
                  e.shiftKey && e.key.length > 1 && LABELS.Shift].filter(Boolean);
    if (mods.length) text = mods.join(' + ') + ' + ' + (text.length === 1 ? text.toUpperCase() : text);
    chip(text);
  }, true);
}"""


# Une étiquette est un élément ajouté DANS la page : c'est le navigateur qui la dessine, avec la
# police, la taille et les couleurs de l'application. Jamais de texte peint après la capture.
LABEL_JS = """([sel, text, side, cls]) => {
  const t = document.querySelector(sel);
  if (!t) return false;
  // a block of text is as wide as its parent: measure the text itself, not the box
  let r = t.getBoundingClientRect();
  if (t.children.length === 0 && t.textContent.trim()) {
    const range = document.createRange(); range.selectNodeContents(t);
    const tr = range.getBoundingClientRect();
    if (tr.width) r = tr;
  }
  const el = document.createElement('div');
  el.dataset.captureLabel = '';
  el.textContent = text;
  const cs = getComputedStyle(t);
  // outside the target, the label sits on what surrounds it
  let bg = 'transparent', n = side === 'inside' ? t : t.parentElement;
  while (n && n !== document.documentElement) {
    const c = getComputedStyle(n).backgroundColor;
    if (c && c !== 'transparent' && !/rgba\\(.*,\\s*0\\)$/.test(c)) { bg = c; break; }
    n = n.parentElement;
  }
  if (bg === 'transparent') bg = getComputedStyle(document.body).backgroundColor || 'white';
  if (cls) {
    el.className = cls;                       // une classe de l'application : rendu identique
  } else {
    Object.assign(el.style, {
      fontFamily: cs.fontFamily, fontSize: cs.fontSize, fontWeight: cs.fontWeight,
      lineHeight: cs.lineHeight, color: cs.color, background: bg,
      padding: '0.1em 0.45em', borderRadius: '0.3em',
      boxShadow: '0 0 0 1px ' + cs.color,
    });
  }
  Object.assign(el.style, {position: 'absolute', zIndex: 2147483647, pointerEvents: 'none',
                           whiteSpace: 'nowrap', margin: 0});
  document.body.appendChild(el);
  const w = el.offsetWidth, h = el.offsetHeight, gap = 6;
  const sx = window.scrollX, sy = window.scrollY;
  const pos = {
    top:    [r.left + r.width / 2 - w / 2, r.top - h - gap],
    bottom: [r.left + r.width / 2 - w / 2, r.bottom + gap],
    left:   [r.left - w - gap, r.top + r.height / 2 - h / 2],
    right:  [r.right + gap, r.top + r.height / 2 - h / 2],
    inside: [r.left + gap, r.top + gap],
  }[side] || [r.left, r.top - h - gap];
  const maxX = document.documentElement.clientWidth - w;
  el.style.left = Math.max(0, Math.min(pos[0], maxX) + sx) + 'px';
  el.style.top = Math.max(0, pos[1] + sy) + 'px';
  return true;
}"""


def perform(page, st):
    """Every step that acts on the page. Used by run_steps, and by a gif's `during` schedule."""
    if "goto" in st:
        page.goto(st["goto"], wait_until="load")
    if "wait_for" in st:
        page.wait_for_selector(st["wait_for"], timeout=st.get("timeout", 30000))
    if "click" in st:
        page.click(st["click"])
    if "fill" in st:
        page.fill(st["fill"], st.get("text", ""))
    if "type" in st:
        page.type(st["type"], st.get("text", ""), delay=st.get("delay", 25))
    if "key" in st:
        page.keyboard.press(st["key"])
    if "js" in st:
        page.evaluate(st["js"])
    if "scroll_to" in st:
        page.locator(st["scroll_to"]).scroll_into_view_if_needed()
    if "hide" in st:
        for sel in ([st["hide"]] if isinstance(st["hide"], str) else st["hide"]):
            page.eval_on_selector_all(sel, "els => els.forEach(e => e.style.visibility='hidden')")
    if "wait" in st:
        page.wait_for_timeout(int(float(st["wait"]) * 1000))
    if "highlight" in st:
        sels = [st["highlight"]] if isinstance(st["highlight"], str) else st["highlight"]
        for sel in sels:
            page.eval_on_selector_all(
                sel, "els => els.forEach(e => { e.style.outline='4px solid #e63c32';"
                     " e.style.outlineOffset='3px'; e.style.borderRadius='6px'; })")
    if "label" in st:
        ok = page.evaluate(LABEL_JS, [st["label"], st.get("text", ""),
                                      st.get("side", "top"), st.get("class")])
        if not ok:
            print(f"    (sélecteur introuvable, étiquette ignorée : {st['label']})")
    if st.get("clear_labels"):
        page.evaluate("document.querySelectorAll('[data-capture-label]').forEach(e => e.remove())")


def run_steps(page, steps, outdir, cfg, default_into=None, dry=False):
    produced = []
    for st in steps:
        perform(page, st)
        if "shot" in st:
            prepare(page, cfg, freeze=not st.get("animate", False))
            sel = st.get("selector")
            origin = (0, 0)
            if sel:
                b = page.locator(sel).bounding_box()
                origin = (b["x"], b["y"]) if b else (0, 0)
            path = do_shot(page, os.path.join(outdir, st["shot"] + ".png"), sel, st.get("full", False))
            apply_annotations(path, resolve_annotations(page, st.get("annotate", []),
                                                        origin, cfg.get("scale", DEFAULT_SCALE)))
            alt = st.get("alt", st["shot"])
            into = st.get("into", default_into)
            produced.append((path, alt, bool(into)))
            if into:
                insert_image(into, path, alt, st.get("marker"), st.get("after"),
                             st.get("before"), dry)
        if "manim" in st:
            name = st.get("webp") or st.get("gif")
            path, webm, vtt = do_anim(st["manim"], st["scene"],
                                      os.path.join(outdir, name + (".gif" if "gif" in st else ".webp")),
                                      int(st.get("fps", 15)), int(st.get("width", 1920)),
                                      video=st.get("video", True), image_width=int(st.get("image_width", 960)))
            alt = st.get("alt", name)
            into = st.get("into", default_into)
            produced.append((path, alt, bool(into)))
            if into:
                insert_image(into, path, alt, st.get("marker"), st.get("after"), st.get("before"), dry)
                if webm and not dry:
                    anim_marker(into, path, webm, vtt)
            continue
        if "gif" in st:
            produced.append((do_gif(page, os.path.join(outdir, st["gif"] + ".gif"),
                                    st.get("selector"), float(st.get("seconds", 4)),
                                    int(st.get("fps", 8)), st.get("during", ()), perform,
                                    st.get("step"), st.get("dither")),
                             st.get("alt", st["gif"]), bool(st.get("into", default_into))))
            into = st.get("into", default_into)
            if into:
                insert_image(into, produced[-1][0], produced[-1][1], st.get("marker"),
                             st.get("after"), st.get("before"), dry)
    return produced


def cmd_anim(args):
    path, webm, vtt = do_anim(args.scene_file, args.scene, args.output, args.fps, args.width,
                              video=not args.no_video, image_width=args.image_width)
    if args.into:
        insert_image(args.into, path, args.alt or os.path.basename(path), args.marker,
                     args.after, args.before, args.dry_run)
        if webm and not args.dry_run:
            anim_marker(args.into, path, webm, vtt)
    else:
        print(f"![{args.alt or ''}]({path})")
        if webm:
            print(f"<!-- ws:anim {{src: {webm}, chapters: {vtt}}} -->")


def cmd_run(args):
    recipe = json.load(open(args.recipe, encoding="utf-8"))
    cfg = {"viewport": tuple(recipe.get("viewport", DEFAULT_VIEWPORT)),
           "scale": recipe.get("scale", DEFAULT_SCALE),
           "theme": recipe.get("theme", "light"),
           "hide": recipe.get("hide", []),
           "keycast": recipe.get("keycast")}
    outdir = recipe.get("out", "img")
    os.makedirs(outdir, exist_ok=True)
    with sync_playwright() as pw:
        browser, page = new_page(pw, cfg)
        install_keycast(page, cfg)
        if recipe.get("url"):
            page.goto(recipe["url"], wait_until="load")
        produced = run_steps(page, recipe.get("steps", []), outdir, cfg,
                             recipe.get("into"), args.dry_run)
        browser.close()
    rest = [(p, a) for p, a, inserted in produced if not inserted]
    if rest:
        print("\n--- à coller dans le sujet ---")
        for path, alt in rest:
            print(f"![{alt}]({path})")
    else:
        print(f"\n{len(produced)} image(s) insérée(s) dans le sujet, rien à coller à la main.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("probe", help="lister les sélecteurs utiles d'une page")
    p.add_argument("url"); p.add_argument("--wait", type=float, default=2.0)
    p.set_defaults(func=cmd_probe)

    p = sub.add_parser("anim", help="une animation manim, en WebP animé (ou GIF si -o finit par .gif)")
    p.add_argument("scene_file"); p.add_argument("scene")
    p.add_argument("-o", "--output", required=True)
    p.add_argument("--fps", type=int, default=15)
    p.add_argument("--width", type=int, default=1920, help="largeur de la vidéo (1080p par défaut)")
    p.add_argument("--image-width", type=int, default=960, help="largeur de l'image animée de secours")
    p.add_argument("--into"); p.add_argument("--alt"); p.add_argument("--marker")
    p.add_argument("--after"); p.add_argument("--before"); p.add_argument("--dry-run", action="store_true")
    p.add_argument("--no-video", action="store_true", help="image animée seule, sans .webm ni chapitres")
    p.set_defaults(func=cmd_anim)

    p = sub.add_parser("shot", help="une capture")
    p.add_argument("url"); p.add_argument("-o", "--out", required=True)
    p.add_argument("--selector"); p.add_argument("--wait", type=float, default=1.0)
    p.add_argument("--wait-for"); p.add_argument("--viewport", default="1280x800")
    p.add_argument("--scale", type=int, default=DEFAULT_SCALE)
    p.add_argument("--theme", default="light", choices=["light", "dark"])
    p.add_argument("--full", action="store_true"); p.add_argument("--animate", action="store_true")
    p.add_argument("--alt", default="")
    p.add_argument("--into", help="fichier .md dans lequel insérer l'image")
    p.add_argument("--marker", help="texte à remplacer dans ce fichier")
    p.add_argument("--after", help="insérer après la ligne contenant ce texte")
    p.set_defaults(func=cmd_shot)

    p = sub.add_parser("run", help="exécuter une recette JSON")
    p.add_argument("recipe")
    p.add_argument("--dry-run", action="store_true",
                   help="montrer les insertions markdown sans écrire dans les fichiers")
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("markers", help="lister les [CAPTURE À FAIRE] d'un ou plusieurs .md")
    p.add_argument("files", nargs="+"); p.set_defaults(func=cmd_markers)

    a = ap.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
