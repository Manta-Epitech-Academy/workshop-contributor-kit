# Create or port a workshop application for the CTFd workshop platform

<!--
HOW TO USE THIS PROMPT (for the human)
1. Gather what you have: the app's source repository, or only its built files (a zip, a single
   HTML page), plus the workshop subject that uses it. If there is no app yet, write down what the
   student should do in it.
2. Open an AI coding assistant that can read files and run commands (Claude Code, for instance)
   in an empty folder.
3. Paste everything below the line "PROMPT STARTS HERE", then tell it where your files are.
4. Answer its questions. It shows you a plan before it writes anything.
-->

PROMPT STARTS HERE

You are helping me put a web application beside a hands-on coding workshop on the Epitech CTFd
workshop platform. The platform calls it a **runtime**: an editor, a game, a console, an emulator,
shown in a pane next to the workshop text. The students are beginners, usually French high-school
students aged 15 to 18.

There are two cases, and I will tell you which one applies:

- **Port:** the app already exists, as source code or only as built files. You make it run on the
  platform with as few changes as possible. Do not rewrite it.
- **Create:** no app exists. You build a small one, designed for the platform from the start.

Work in the phases below, in order. Show me the plan in Phase 2 and wait for my answer before you
build anything.

Talk to me in the language I write to you in. Keep every student-facing text in the workshop's
language, usually French.

## Phase 0 — Read the references first

Clone these public repositories and read the files named. Do not write anything before this.

```sh
git clone --depth 1 https://github.com/Manta-Epitech-Academy/ctfd-workshop-platform
git clone --depth 1 https://github.com/Manta-Epitech-Academy/pacman-ghost-ai_runtime
git clone --depth 1 https://github.com/Manta-Epitech-Academy/miniasm_runtime
git clone --depth 1 -b wrp-port https://github.com/Manta-Epitech-Academy/voxel-world_runtime
git clone --depth 1 https://github.com/kevin-cazal/workshop-content-tools
```

In `ctfd-workshop-platform`:

- `docs/RUNTIME_PROTOCOL.md`: **the reference**. It covers how a runtime is served, the
  messages it exchanges with the page, and what it must never do. If this prompt and that document
  disagree, the document wins. Tell me when it happens.
- `docs/CONTRIBUER.md`, part 4: the short version, in French.
- `plugins/workshop/assets/runtime/adapters/*.js`: one small adapter per runtime. Start from `mock.js`.
- `tools/build_runtime.sh`: one `case` per runtime, either `vite` (built) or `static` (the repo is
  the site).
- `tools/sync_subject.py`: `TOKEN_SCHEMES`, needed only if the app validates steps itself.
- `plugins/workshop/runtime_options.py`: `START_OPTIONS`, needed only if the app takes an option
  in its address.
- `docs/DEPLOY.md`, section "Runtimes on Kubernetes": how production serves runtimes.

In `workshop-content-tools/CONTENT_CONVENTION.md`, read §3.3b, "What proves a step is done", and
the `runtime:` block in §3.2.

Three runtimes to learn from:

- `pacman-ghost-ai_runtime`: a static site (the repo is the site), Monaco and a Lua engine fetched
  by scripts, a Dockerfile serving it under `/runtime/pacman/latest/`. It validates nothing itself.
- `miniasm_runtime`: an app that **validates steps itself** and shows a token. Read its
  `js/token.js` and its adapter `adapters/miniasm.js` on the platform side.
- `voxel-world_runtime` (branch `wrp-port`): an app with **no readable sources**, ported by patching
  its built page (`scripts/port.py`). It has a readable `embed.js` for the token and platform mode,
  an end-to-end test (`tests/check.py`), and a `PORT_PLAN.md`.

## Phase 1 — Ask me these questions, once, in one message

Propose a default for each one, so I can just answer "ok".

1. **Port or create?** For a port: do we have the **source code**, or only built files? Who owns
   the original, and may we fork it?
2. **Which subject uses it**, and which steps? Give me the subject repo, or its text.
3. **What does the student do in it?** Type code (which language?), click, play, type commands?
4. **Where does student code run?**
   - In the page's own JavaScript context, like Fengari or a plain `eval`?
   - In a Web Worker?
   - In WebAssembly with no access to JavaScript, like wasmoon with proxies and injected objects off?
   - On a server?

   This decides whether the app can be trusted to validate steps (Phase 4).
5. **Can the app check a step itself?** For example, "the ghost reaches Pac-Man" or "the floor has
   16,384 blocks". If yes, list the checks per step.
6. **What must survive a reload or a change of computer?** The student's code, settings, progress.
7. **Solutions:** does the app or its repo contain step solutions, a « corrigé » button, or answer
   files?
8. **Network:** must it work with no internet in the room? Is the page heavy (WASM, assets)?
9. **The runtime id:** short, lowercase, with hyphens, for example `voxel-world`. It names the
   `/runtime/<id>/` path, the adapter file and the build case.

## Phase 2 — Study, then show me a plan

**For a port**, find and write down:

- how the app is built: `npm run build`, Vite, a static folder, a single bundled HTML file;
- every absolute URL that would break under `/runtime/<id>/<version>/`;
- every external request at runtime: CDNs, fonts, APIs;
- the `localStorage` keys it writes;
- where the editor lives: Monaco, CodeMirror or a textarea, and how to focus it;
- whether it has its own copy of the workshop instructions, which must be hidden in platform mode;
- whether it has its own step list, and how to switch steps from outside;
- every place a solution can leak: files, bundled strings, buttons, comments;
- where its checks run, and what they return.

When there are no sources, say so plainly. The fallback is to **patch the built file** with exact
string replacements that must each match once, as `voxel-world_runtime/scripts/port.py` does. Never
hand-edit a minified file.

**For a creation**, design the smallest app that does the job. It needs:

- one page;
- an editor, if the student writes code, preferably Monaco, vendored;
- the visible result;
- a console for errors and prints;
- per-step checks with feedback the student can act on, in the workshop's language.

Keep it static: HTML, CSS, JavaScript, optionally WASM, and no backend. Prefer what the existing
runtimes already use.

**The plan** lists:

- the files you will add or change in the app's repository;
- the files to add on the platform side (Phase 3B);
- how each step is validated, and why (Phase 4);
- the tests you will write;
- what is risky or unknown.

Wait for my answer before Phase 3.

## Phase 3A — The app's repository

```
<name>_runtime/
├── index.html, ...          # the site itself (static), or the source + a build that outputs it
├── README.md                # what it is, how to run it alone, how it plugs into the platform
├── tests/                   # end to end, in a headless browser
├── Dockerfile               # nginx serving the site under /runtime/<id>/latest/
├── docker/nginx.conf
└── .github/workflows/docker.yml   # builds the image; publishes it on main
```

These rules must hold:

- **It runs alone.** Opened with no platform around it, the app works. The platform only adds
  things to it.
- **Every URL is relative**, or the build takes its base at build time (Vite: `base` from
  `VITE_BASE`). The platform serves it under `/runtime/<id>/<version>/`.
- **No request to the internet while running.** Vendor Monaco, engines and fonts into the repo, or
  fetch them at build time with a script, like pacman's `scripts/setup-monaco.sh`. Rooms often
  have bad networks or none.
- **Fits a narrow pane.** The pane is 55% of a laptop screen, about 700 px wide. Check the layout
  at that width, and make the important part, the result, keep its room.
- **Platform mode.** When the platform drives the app, it hides its own copy of the workshop text
  and hints, which the platform already shows. It keeps the objective and the checks of the
  current step.
- **Step API.** If the app has steps, expose a function to go to step N and one to read the
  current step, on `window`, for the adapter.
- **Storage.** Keep the student's work in `localStorage` under a few stable, prefixed keys. List
  them for the adapter. The platform saves them per participant on its side, which is why the app
  needs no code for this.
- **No solutions anywhere** in what is served: no « corrigé » button, no solution strings in the
  bundle, no `solutions/` folder copied into the image. Solutions go in a private repository.

**Image.** Copy pacman's `Dockerfile` and `docker/nginx.conf`, and replace `pacman` with your id.
It serves the app at `/runtime/<id>/latest/`, redirects any other version there, answers
`/healthz`, and sends `X-Frame-Options: SAMEORIGIN`. Keep `docs/`, `tests/` and `solutions/` out
of the image.

**CI.** The workflow builds the image on pull requests and publishes it to GHCR on `main`. **Do
not add a step that restarts anything on the cluster.** Deploying is the maintainers' decision.

## Phase 3B — The platform side

These files go in `ctfd-workshop-platform`, on a new branch. If I cannot push there, put them in a
`platform-changes/` folder with a short README, for a maintainer to apply.

1. **`plugins/workshop/assets/runtime/adapters/<id>.js`**, injected into the frame by the page.
   Start from `mock.js`, and see `pacman.js` and `miniasm.js`. It:
   - sends `ready` with `capabilities` and `storageKeys` once the app is usable, not on
     `DOMContentLoaded`;
   - handles `focus`;
   - on `init`, reads `params`: the start options, plus `token_secret` and `exercises` (challenge
     id → the app's step id) for token validation;
   - on `init` and `step`, moves the app to the step the student is reading;
   - may send `result` (advisory) and `propose` (fills a step's answer field).

   Every message carries `wrp: 1`, and both sides check `event.origin`.
2. **`tools/build_runtime.sh`**: a `case` with the repository URL, `KIND`, and the files to leave
   out of the dist.
3. **`tools/sync_subject.py`**: a `TOKEN_SCHEMES` entry, only for token validation (Phase 4).
4. **`plugins/workshop/runtime.py`**: an icon in `ICONS`, a Font Awesome name. Optional.
5. **`plugins/workshop/runtime_options.py`**: a `START_OPTIONS` entry, only if the app reads an
   option from its address before it starts.

The subject then declares the app in its `subject.yaml`:

```yaml
runtime:
  engine: "<what it is>"
  language: "<the student's language, a Monaco id>"
  id: "<id>"
  version: "<commit sha of the app repo>"
  title: "<name shown on the button>"
  pane: {placement: side, open: false, size: 55}
```

## Phase 4 — How steps are validated

Pick one per subject, and per step if needed. The choice is written in the subject, not the app.

| Mode | When | What the app does |
|---|---|---|
| `checkpoint` | a person must look at the work, or the app cannot check | Nothing. An instructor reads out a code; in self-serve, a button. |
| `quiz` | the step's questions are the proof | Nothing. |
| `flag` | the work produces a string the student discovers, CTF style | May `propose` it. |
| `token` | the app checks the step itself | Shows a token when all the step's checks pass. |

**Token**, the strongest when the app can check:

- The app computes `<prefix>{<first 12 hex of HMAC-SHA256(secret, "<id>:<step id>")>}` with
  `crypto.subtle`, for example `monde{f064ca3575f4}`.
- The platform computes the same value from the same secret and sets it as the flag. Add the
  matching entry to `TOKEN_SCHEMES`:
  `"<id>": {"message": "<id>:{id}", "flag": "<prefix>{{{digest}}}"}`.
- The secret is per instance and reaches the app through the adapter, in `params.token_secret`.
- Show nothing without a secret, so the app opened alone stays unchanged.
- The adapter `propose`s the token to the step's answer field. The student still presses Submit.
- Pin the scheme in a test: a fixed secret and step id give a known token.
- `crypto.subtle` exists only on HTTPS or localhost.

**Trust.** A token proves only what the page can prove.

- If student code runs in the page's JavaScript context, it can read the secret and forge every
  token. Then do not use `token`. Use `checkpoint`, or move student code into a Worker or a
  WebAssembly engine with no JavaScript access.
- Write down which case you are in.

## Phase 4b — Exporting scenes for the subject (optional)

If the subject wants 3D scenes in place of stills (convention §3.8b), the app's repository is
where the exporter lives: a script that runs a program in the headless app and writes the result
as one glTF binary (`.glb`), with textures inside. `voxel-world_runtime/scripts/export_scene.py`
is the model: visible faces only, merged, textures tiled, a top-level node named `cut` holding
the cut-away version when asked, and an optional still rendered with the same camera. The output
is data, never code.

## Phase 5 — Rules that never bend

1. **A runtime never solves a step.** `result` is advisory. Only the student's Submit, or an
   instructor's code, validates.
2. **A runtime never calls the CTFd API.** It talks to the page through `postMessage` only.
3. **One frame per workshop.** It is booted once and told the step, never rebooted per step.
4. **Never give the student the correct code for a step they are meant to write.** Not in the app,
   its hints, a « corrigé » button, a bundled string or a starter file.
   - A modelling step's code is the subject's business: it is marked there, and the app does not
     carry it.
   - If the original app has solutions, remove them from what is served. Tell me where they still
     exist, for example in the repo history or a release zip, and propose where to move them.
5. **No secrets** in the app, its repository, its commits or its image. The token secret only ever
   arrives at runtime.
6. **Do not modify the platform's core** (`plugins/workshop/*.py` beyond the files in Phase 3B, and
   `assets/runtime.js`). If the protocol is missing something, tell me. Do not work around it.
7. **Nothing goes live without me.** No push to `main`, no pull request, no image published, no
   cluster change, no instance synced, unless I ask. Work on new branches.
8. **An app served from another origin** (`external: true` with a `src`) cannot get the adapter or
   talk to the page: the page checks the origin. It is a last resort: no token, no step
   following, no saved work. Only propose it for a temporary deployment, and say what it loses.

## Phase 6 — Check your work

- **Tests, in a headless browser** (Playwright with Chromium):
  - the app loads;
  - platform mode hides what it must;
  - the step API works;
  - no solution text is in what is served;
  - for `token`: each step's official solution turns the step green and shows exactly the
    platform's token.
- **Build with the platform's own script**, pointing at your local repo:
  `RUNTIME_SOURCE=<path> tools/build_runtime.sh <id> <sha>`. It runs in Docker. The dist must hold
  only what the page needs.
- **Image:** `docker build`, run it, then check:
  - `/healthz` answers 200;
  - `/runtime/<id>/latest/` serves the app;
  - another version redirects to `latest`;
  - repo-only files return 404.
- **End to end, if you can run the platform locally** (`docker compose up` in
  `ctfd-workshop-platform`; its CTFd image is on GHCR and may need a login):
  1. complete the setup wizard;
  2. import a subject that declares the app, with `tools/sync_subject.py`;
  3. complete step 1 in a browser: open the pane, do the step, see the checks and the token, and
     submit.

  If you cannot run it, say exactly what was not tested.

## Phase 7 — Deliver

1. **The app's repository**, on a new branch, in small commits with clear messages.
2. **The platform changes**, on a new branch of `ctfd-workshop-platform` or in
   `platform-changes/`.
3. **A `PORT_PLAN.md`** in the app's repository, in plain words:
   - what is done, and what was tested and how;
   - what was not tested;
   - where the solutions are;
   - what is left before a real session;
   - risks;
   - decisions for the maintainers;
   - an honest time estimate.
4. **A short report to me**, in my language: what works, what is left, and the decisions only I
   can take.
