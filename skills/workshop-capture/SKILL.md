---
name: workshop-capture
description: Take screenshots and GIF animations of a live app or workshop runtime from a URL, and annotate them with frames, arrows, or short labels drawn by the runtime itself (never text painted onto the image afterwards — sentences go in the caption). Use this skill whenever a workshop needs illustrations — the expected output of a step, what the screen should look like, where to click, a short animation of something moving — and whenever a review left `[CAPTURE À FAIRE]` markers, or the user asks for screenshots, captures, images, GIFs, or says a subject has no visuals. Also use it when an existing screenshot needs a frame, an arrow, or a face/name blurred out, or when an animation has to show what is being typed (keys displayed on screen, like showmethekey or KeyCastr).
---

# Capturing illustrations for a workshop

A workshop with no images cannot be self-verified: the student has no way to tell whether what is
on their screen is what should be there. That is criterion V1 in `workshop-quality`, it is the
most commonly missing thing in a draft, and it is missing because taking the screenshots is a
chore. This skill makes it a two-minute job.

Everything runs headless, so captures come out with **no browser chrome, no bookmarks bar, no
notifications, no cursor** — the things that make a hand-taken screenshot look amateur, and the
first thing a strict reviewer points at.

## The three commands

Run them with the venv interpreter: `~/.claude/.venvs/capture/bin/python`.

```bash
PY=~/.claude/.venvs/capture/bin/python
S=~/.claude/skills/workshop-capture/scripts

# 1. What is on this page, and what can I target?
$PY $S/capture.py probe https://exemple.fr/atelier

# 2. One capture, quickly
$PY $S/capture.py shot https://exemple.fr/atelier -o img/etape0.png \
    --selector "#game" --wait-for "#game" --theme dark

# 3. A scripted sequence: click, type, wait, capture, animate
$PY $S/capture.py run recette.json          # capture ET insère dans le .md
$PY $S/capture.py markers sujet/*.md        # ce qu'il reste à photographier
```

**Always start with `probe`.** It lists the capturable panes with their sizes, the buttons with
their labels, the inputs and editors, and any iframes. Writing a recipe without it means guessing
selectors, and guessing selectors is where this goes wrong.

## The workflow

1. **Find what is missing.** `capture.py markers sujet/*.md` lists every `[CAPTURE À FAIRE]` a
   review left behind — that is your shot list.
2. `probe` the URL, read the selectors.
3. Write a recipe (format and patterns in `references/recipes.md`).
4. `run` it. Images are written **and inserted into the markdown files** — see below.
5. **Look at the images before shipping them.** Read the PNG back and check it shows what you
   think it shows: an exit code of 0 only means a file was written. Real defects caught this way
   in testing — an arrowhead invisible because it landed on a same-coloured object, and a label
   clipped off the edge of the frame.

## Writing the images into the subject

A capture that is not in the page is not done. Give the recipe an `into` and each shot goes
straight into the markdown:

```json
{
  "into": "sujet/atelier1.md",
  "out": "sujet/img",
  "steps": [
    {"shot": "etape3-resultat", "selector": "#game", "alt": "Le fantôme part vers la gauche"},
    {"shot": "etape5-console", "selector": "#out", "alt": "La console après Démarrer",
     "after": "### Comment tester"}
  ]
}
```

Anchors, in order of precedence:

| Clé | Effet |
|---|---|
| `marker` | remplace ce texte exact — typiquement une ligne `[CAPTURE À FAIRE : …]` |
| *(rien)* | remplace le **premier `[CAPTURE À FAIRE]` restant** du fichier |
| `after` / `before` | insère autour de la première ligne contenant ce texte |
| *(aucune ancre trouvée)* | ajoute à la fin, et le dit |

Details that matter:

- **Paths are relative to the `.md`**, not to where you ran the command, so the image resolves
  wherever the file is rendered.
- **Re-running is safe.** An image already referenced by the same path is replaced in place, never
  appended a second time — so you can iterate on a capture until it is right.
- **`--dry-run`** prints every insertion without touching a file. Use it the first time.
- **The alt text is the caption.** It is where sentences belong, so write one saying what the
  reader should be seeing. The image itself holds at most a few short labels drawn by the runtime
  (see below).
- If the folder is a git repo, check `git status` first so your image commits stay separable.

Only images that were *not* inserted are printed at the end for manual pasting. For a workshop
that lives in Notion, capture to files and attach them with the Notion MCP — `into` writes to
markdown files only.

## Annotating — frames, arrows, and labels from the runtime

A capture is plain, or it carries one of these:

1. **Plain.** The default, and usually enough.
2. **A frame** — `box`, a rounded outline around the thing that matters.
3. **An arrow** — `arrow`, pointing at it.
4. **A label** — one short term (`X`, `Y`, `largeur`, `+100`), **drawn by the runtime
   itself**, before the capture.

### Labels: only from the runtime

**Text is never painted onto an image after it is captured.** Not with Pillow, not with
`annotate.py`, not in an image editor. Post-processed text always looks stuck on: a different
font, a different size, a different colour from everything around it, and it sits badly as soon
as the capture is scaled or re-taken.

A label is allowed when **the runtime draws it**, with its own text rendering. It then has the
app's font, size and colours, it scales with the capture, and it looks like part of the screen.
The whole set stays homogeneous. It also stays editable: the label lives in the recipe or in the
illustration program, so a re-run redraws it.

| Runtime | How to label |
|---|---|
| Web page, DOM app | the `label` step: an element added **in the page**, which takes the target's font, size and colour, or an existing app class with `"class"` |
| Keys being pressed | the `keycast` option (see GIFs): the browser draws each key in the page while it is filmed |
| Canvas runtime (TIC-80, a web game, p5, pygame-web…) | the runtime's own text function in the program you capture: TIC-80 `print`, `ctx.fillText` with the game's font, etc. |

```json
{"label": "#ghost", "text": "X + 2", "side": "top"},
{"label": "#score", "text": "+100", "side": "right", "class": "badge"},
{"shot": "etape4", "selector": "#game", "alt": "Le fantôme avance de 2 pixels vers la droite à chaque image"},
{"clear_labels": true}
```

`side` is `top`, `bottom`, `left`, `right` or `inside`. `clear_labels` removes them all before
the next capture.

```lua
-- TIC-80: the label is part of the illustration program, in the console's own font
print("X + 2", ex + 10, ey - 8, 4)
```

Rules for labels:

- **Only short terms.** Axis names and sizes (`X`, `Y`, `largeur`, `longueur`, `hauteur`), numbers
  and signs (`0`, `8`, `-10`, `+100`, `X + 2`). Nothing longer.
- **No long words, no sentences.** A label that needs a verb, or a word a student has to stop and
  read, is a caption.
- **Never at the cost of readability.** A label must not cover or crowd the thing it names. If the
  capture is harder to read with the label than without it, remove the label.
- **Few.** Two or three per image at most. Past that, use the caption.
- **The runtime's font, never another.** No custom font, no size picked to "look nicer".
- **French in a French workshop**, like the rest of the deliverable.
- **Still a caption.** The label names things; the caption says what the reader should notice.

### Frames and arrows

Annotate **by selector**, never by pixel coordinates: the geometry is computed from the live
element, so it stays correct when the app changes.

```json
{"shot": "etape3", "selector": "#game", "alt": "Le fantôme se dirige vers Pac-Man",
 "annotate": [
   {"box": "#ghost"},
   {"arrow": {"from": "#code", "to": "#ghost"}}
 ]}
```

- **`box`** — the frame. Use it for "this bit".
- **`arrow`** — stops at the **edge** of its target and carries a light halo, so it stays visible
  over anything, including an object of the same colour.
- **`spotlight`** — dims everything outside the region and frames it. A frame variant;
  use it when the interesting thing is small and the screen is busy.
- **`blur`** — redaction, not decoration. Run it over any name, avatar, email or token before an
  image leaves the building.
- **`highlight`** is a *step*, not an annotation: it draws the outline **in the page** with CSS
  before the capture. Crisper than post-processing when a frame is all you need.

Sizes scale with image width, so a frame or an arrow reads the same on a 400px crop and a 2000px
page. `scripts/annotate.py` works standalone on any PNG you already have.

**Write the caption.** The recipe's `alt` becomes the markdown caption that gets printed for you
to paste. That is where the explanation lives — one sentence saying what the reader should be
seeing, not a description of the image.

## GIFs

```json
{"gif": "etape5-poursuite", "selector": "#game", "seconds": 4, "fps": 8}
```

**Filming something happening**, rather than its result: `during` runs steps *while* the frames are
captured, each at its own second.

```json
{"gif": "etape2-lancer", "selector": "#game", "seconds": 6, "fps": 10,
 "during": [{"at": 0.5, "type": "#console", "text": "studio", "delay": 150},
            {"at": 2.5, "key": "Enter"},
            {"at": 4.0, "click": "#run"}]}
```

Any action step works there (`type`, `key`, `click`, `js`, `label`…), and a step scheduled past the
end still runs, once the recording is over.

### Showing the keys — `keycast`

When the workshop says "type this", the reader wants to see the keys. `keycast` shows each key
pressed, the way *showmethekey* or *KeyCastr* do on a desktop recording:

```json
{
  "url": "http://localhost:8090/",
  "keycast": {"selector": "#game", "position": "bottom-right"},
  "steps": [
    {"gif": "etape1-studio", "selector": "#game", "seconds": 5, "fps": 10,
     "during": [{"at": 0.5, "type": "#game", "text": "studio", "delay": 160},
                {"at": 2.5, "key": "Enter"}]}
  ]
}
```

`keycast: true` is enough for the defaults. The options:

| Clé | Effet |
|---|---|
| `selector` | anchor the keys inside that pane, so an element capture includes them (without it: the viewport corner) |
| `position` | `bottom-right` (default), `bottom-left`, `top-right`, `top-left` |
| `keep` | seconds a key stays on screen (default 1.1) |
| `max` | how many keys at once (default 4) |
| `size`, `background`, `color`, `margin` | the look |

Named keys are shown as symbols — `↵`, `Esc`, `⇥`, `↑`, `⌫`, `Espace` — and a shortcut appears as
one key (`Ctrl + R`). Modifiers alone are not shown, only in combination.

**This is still the rule about text, not an exception to it.** The keys are drawn *in the page*
by the browser, in the page's own font, before the capture — like the `label` step. Nothing is
painted onto the image afterwards. Because they live in the page, they fade on their own, so a
still taken a second later is clean.

Frames are captured in a loop and assembled by ffmpeg with a generated palette. Keep them
**short, small and targeted**: 3-5 seconds, 8 fps, and always a `selector` rather than the whole
page. The script warns above 2 MB. A GIF earns its place only when motion *is* the information —
a character moving, a value changing, a layout reflowing. For anything static, a still is better:
it loads instantly, it prints, and the reader controls how long they look at it.

## Animations of an idea — manim

A GIF of the app shows *what happens*. Some steps need to show *why*: a formula whose terms
each do something, a loop that walks a grid, a wave that widens when you divide x. For that,
the tool is [manim](https://www.manim.community/), the library behind 3Blue1Brown's videos:
a dark background, one object that transforms, the formula that changes above it, and one
short phrase per change. The reader watches the term appear and sees its effect at once.

```bash
PY=~/.claude/.venvs/capture/bin/python
S=~/.claude/skills/workshop-capture/scripts
$PY $S/capture.py anim anim/vague.py LaVague -o img/etape4b-vague.webp \
    --into sujet/atelier.md --after "🧰 **`math.sin`" \
    --alt "La vague, terme par terme : ÷ 8 l'élargit, × 4 la grandit, + 20 la monte."
```

Or as a recipe step, beside shots and GIFs:

```json
{"manim": "anim/vague.py", "scene": "LaVague", "webp": "etape4b-vague", "fps": 12, "width": 800,
 "alt": "La vague, terme par terme.", "after": "🧰 **`math.sin`"}
```

**Chapters.** Put `self.next_section("÷ 8 : la vague s'élargit")` in the scene at the start of
each state. The command then also writes, beside the image, a `.webm` of the same frames and a
`.vtt` with one chapter per section, and puts the `ws:anim` marker under the image when `--into`
is given (convention §3.8d). The platform plays the video under its own controls: play/pause,
a progress bar ticked at each chapter, ‹ › to the previous or next state. `--no-video` skips
this. Name the sections as the phrase the reader will see under the bar.

How it works: manim renders the scene to a video in its own venv (`~/.claude/.venvs/manim`,
`pip install manim`, which needs `libpango1.0-dev` and `libcairo2-dev` on Debian), then
ffmpeg turns it into an **animated WebP**: a plain `![...](x.webp)` for markdown, GitHub and
every current browser, at about half a GIF's weight and with real colours, which a 3D surface
or a gradient needs. An output path ending in `.gif` gives a GIF instead, through a palette
like the page GIFs. Manim itself cannot write an animated SVG.

Rules, on top of the ones below:

- **Keep the scene file in the subject repo**, in `anim/`, next to `img/`. The GIF is the
  deliverable, the scene is its source: a change in the subject means re-rendering, not
  redrawing.
- **The formula on screen is the code.** Write it with `Text(..., font="DejaVu Sans Mono")`,
  exactly as the student will type it (`h = 20 + 4 * math.sin(x / 8)`), not a typeset version
  of it: a beginner has to recognise the line in the editor. `MathTex` (LaTeX is installed:
  texlive-latex-extra, texlive-science, dvisvgm) is for real mathematics the workshop explains
  as such, a fraction, a square root, an angle, and for `add_coordinates` on axes.
- **One idea per animation, 10 to 20 seconds.** Build the formula one term at a time, with
  `Transform` from one state to the next so the eye follows the change. Say in one phrase,
  under the figure, what the new term does. End on the link with the workshop: the blocks
  appearing under the curve, the grid filling up.
- **The app's colours**: take the background and the accents from the app's stylesheet, so
  the GIF sits in the page like one of its own captures.
- **French, short labels, Pango font.** The same text rules as the labels above.
- **Size**: the video at 1920 px (1080p, the default, so the text is crisp full screen) and
  10 to 12 fps; the animated image at 960 px (`--image-width`), under 2 MB, since GitHub's
  readers download it too. The `anim` command warns above that.
- **Look at it before shipping**: extract a few frames with ffmpeg and read them. A phrase
  that overflows the frame or a curve that leaves the axes is invisible in the exit code.

## Quality rules, which are also review criteria

- **One viewport for the whole workshop.** Mixed sizes are the fastest way to look sloppy.
- **`scale: 2`.** Default, and what makes text crisp on a modern screen.
- **One theme.** Pick light or dark and keep it across every image of the set.
- **Nothing personal in frame** — names, avatars, emails, tokens, other tabs. `blur` them.
- **Capture a pane, not the page**, whenever the page has a pane. A full-page screenshot of an
  app is mostly empty space, and the reader has to hunt for the part that matters.
- **Name files for the step they illustrate** (`etape3-resultat.png`), not `screenshot-4.png`.

## Installation

Two virtualenvs, one for the captures and one for manim, and two system tools. On a Debian or
Ubuntu machine:

```bash
# Captures: Playwright with Chromium, and Pillow for the annotations.
python3 -m venv ~/.claude/.venvs/capture
~/.claude/.venvs/capture/bin/pip install playwright Pillow
~/.claude/.venvs/capture/bin/playwright install chromium

# GIFs, WebP and the videos of the animations.
sudo apt-get install -y ffmpeg

# Animations: manim needs the Pango and Cairo headers to build, and LaTeX only
# for MathTex (optional, about 1 GB).
sudo apt-get install -y libpango1.0-dev libcairo2-dev python3-dev
python3 -m venv ~/.claude/.venvs/manim
~/.claude/.venvs/manim/bin/pip install manim Pillow
sudo apt-get install -y texlive-latex-base texlive-latex-extra texlive-fonts-recommended texlive-science dvisvgm
```

The scripts look for the two venvs at those paths, so keep them. Check with
`~/.claude/.venvs/manim/bin/manim --version` and `~/.claude/.venvs/capture/bin/python -c "import playwright"`.

## Files

- `scripts/capture.py` — probe, shot, run, markers. Drives the browser, resolves annotations,
  and writes the images into the markdown.
- `scripts/annotate.py` — the drawing primitives, also usable standalone on any PNG.
- `capture.py anim` — a manim scene rendered to an animated WebP (see « Animations of an idea »).
- `references/recipes.md` — the recipe format in full, and patterns for the awkward cases: code
  editors, canvas games, iframes, waiting for a stable frame, login.

## Related

`workshop-quality` criterion V1 is what this exists to satisfy; run a review first so you know
which steps actually need an image, then capture only those.
