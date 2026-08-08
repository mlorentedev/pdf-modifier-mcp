---
id: pdf-modifier-mcp-lessons
type: lesson
status: active
created: "2026-03-07"
owner: manu
---

# Lessons Learned

### [2026-03-07] Decoupled File-based Logging for MCP Servers
**Context:** Adding background observability to a CLI/MCP tool without polluting the standard output.
**Problem:** When deploying an MCP server, stdout/stderr is often consumed by the MCP transport protocol (stdio). If a silent error happens in production, there's no way to debug it because the LLM context only shows generic fallback error messages.
**Solution:** Created a centralized `logger.py` that implements a `RotatingFileHandler` writing directly to `~/.pdf-modifier/logs/pdf-modifier.log`. This decoupled file-based logging captures stack traces and unhandled exceptions natively, providing a "black box" flight recorder for debugging without breaking the MCP stdio JSON protocol.
**Tags:** `#mcp` `#observability` `#logging` `#cli`

### [2026-03-07] Solving Branch Protection Conflicts in CI Releases
**Context:** Handling CI/CD releases on branches with strict protection (Require Pull Request).
**Problem:** Tools like `python-semantic-release` attempt to push version commits directly to the default branch. This triggers GitHub's `GH006` error because the push isn't coming through a Pull Request, even when using an administrator token. Adding administrators to the "bypass" list doesn't work if "Require status checks" is also enabled, as the new version commit hasn't passed any checks yet.
**Solution:** Migrated to the **release-please** flow used in `hive-vault`. This tool creates a release PR with the version bump and changelog. Since it's a PR, it fulfills all branch protection requirements. Merging the PR triggers the tag creation and actual publication to PyPI/MCP Registry. This is the only robust way to maintain strict branch security while having automated releases.
**Tags:** `#ci-cd` `#release-please` `#github-actions` `#branch-protection`

### [2026-03-13] Branch Protection Must Match CI Matrix After Python Version Bump
**Context:** Bumped Python target from 3.10 to 3.12 and updated CI matrix from [3.10, 3.12] to [3.12, 3.13]
**Problem:** PR checks showed perpetually pending — GitHub branch protection still required `test (3.10)` which no longer exists in the CI matrix. The check name includes the Python version from the matrix, so changing the matrix silently breaks branch protection.
**Solution:** Update branch protection required status checks via `gh api repos/.../branches/master/protection/required_status_checks -X PATCH` to match the new matrix names. Always update branch protection as part of any CI matrix change.
**Tags:** `#ci-cd` `#github-actions` `#branch-protection` `#python`

### [2026-03-13] Release-Please PRs Need Manual CI Trigger
**Context:** Release-please created PR #52 but CI never ran on the release-please branch
**Problem:** Release-please uses GITHUB_TOKEN which by design does not trigger workflow runs (to prevent infinite loops). The release PR sits with pending checks forever because CI never runs on it.
**Solution:** Push an empty commit (`git commit --allow-empty -m "chore: trigger CI"`) to the release-please branch to trigger CI. Alternative: add `workflow_dispatch` trigger to ci.yml so `gh workflow run` works without a push.
**Tags:** `#ci-cd` `#release-please` `#github-actions`

### [2026-03-14] GITHUB_TOKEN events don't trigger other workflows — release-please CI workaround
**Context:** Using release-please with branch protection that requires CI status checks (e.g. test matrix jobs)
**Problem:** release-please pushes to its branch using GITHUB_TOKEN. By GitHub design, events from GITHUB_TOKEN don't trigger other workflows. This means the CI workflow never runs on the release-please branch, leaving required status checks perpetually pending and blocking the merge.
**Solution:** Run the test matrix inside the Release workflow itself, conditioned on release_created != true. Checkout the release-please branch, run tests, then use the GitHub Statuses API (gh api repos/OWNER/REPO/statuses/SHA) to report the check results on the correct commit SHA. The status context names must match branch protection's required checks exactly (e.g. "test (3.12)"). Add statuses: write to workflow permissions.
**Tags:** `#github-actions` `#release-please` `#ci` `#branch-protection` `#pattern`

### [2026-06-24] Docker multi-stage: venv shebangs broken across builder/runtime + COPY content semantics
**Context:** INFRA-001 — Docker multi-stage build for FastAPI backend.
**Problem:** Serie de errores encadenados al construir el Dockerfile multi-stage:
1. **Shebang del venv en el builder stage** — copiar el venv creado en `builder` (`/build/.venv/`) al `runtime` produce shebangs apuntando a `/build/.venv/bin/python` (inexistente en runtime). Solución: crear venv limpio en runtime y copiar solo los wheels (`pip wheel --wheel-dir` + `pip install /wheels/*`).
2. **`COPY src/ ./` copia contenido, no directorio** — `src/` contiene `pdf_modifier/`. `COPY src/ ./` copia el *contenido* de `src/` a `/app/`, resultando en `/app/pdf_modifier/` (correcto). Pero `COPY src/ ./pdf_modifier/` copia el contenido al subdirectorio `pdf_modifier/`, generando `/app/pdf_modifier/pdf_modifier/` (anidamiento doble).
3. **Orden COPY/RUN** — `pip install .` necesita `pyproject.toml`. Si el COPY de `pyproject.toml` está después del RUN, el install falla silenciosamente.
4. **Permissions** — el runtime user es `appuser`, pero los directorios (`/app/.pdf-modifier/`, `/app/storage/`) los crea la app en primer inicio. Si no existen y el appuser no tiene permisos en `/app/` (dueño root), falla con `PermissionError`. Solución: `mkdir -p` + `chown` ANTES de `USER appuser`.
**Solution:**
- Fase builder: `pip wheel --wheel-dir /wheels` para descargar wheels.
- Fase runtime: crear venv limpio, instalar wheels, instalar package con `pip install .` (necesita pyproject.toml en el directorio).
- Orden estricto: COPY todo → RUN install → RUN mkdir+chown → USER → CMD.
- Verificar con `docker run --entrypoint ls` antes de correr.
- El error de `pip install .` sin pyproject.toml es **visible en build**, no silencioso: `ERROR: Directory '.' is not installable. Neither 'setup.py' nor 'pyproject.toml' found.`
**Tags:** `#docker` `#multi-stage` `#venv` `#windows-wsl` `#python`

### [2026-08-04] Canvas render must run after DOM mount in Svelte {#if}
**Context:** Rendering a PDF to a `<canvas>` inside a Svelte `{#if loading}` block.
**Problem:** `renderPage()` called in `onMount` silently no-oped — the canvas was wrapped in `{#if loading}`, so it wasn't in the DOM yet and `canvas` was `null`. Result: black screen, no error.
**Solution:** Set `loading = false` first, `await tick()` to let Svelte flush the DOM, then call `renderPage()`. Also: reactive prop changes (e.g. `highlightText`) need a `$effect` to trigger re-render — calling once in `onMount` isn't enough.
**Tags:** `#frontend` `#svelte` `#canvas` `#lifecycle`

### [2026-03-14] Worktree agents lose staged changes when main repo branch operations interfere
**Context:** Running two parallel agents in git worktrees while also creating branches in the main repo
**Problem:** When I created a branch in the main repo with the same name the worktree agent was going to use, the worktree's staged changes were lost. Git worktrees share the same repository, so branch operations in one worktree can affect others.
**Solution:** Do NOT create branches in the main repo while worktree agents are running. Let the agents finish first, then create branches from their output. Use git stash to extract changes from worktrees safely. Always check worktree status before manipulating shared branches.
**Tags:** `#git` `#worktree` `#parallel-agents` `#pattern`

### [2026-08-06] pdf.js v6 render API + grouping real-world PDF spans
**Context:** WEB-002 — PDF preview element grouping, click-to-locate, precise highlight (Svelte + pdf.js).
**Problem:**
1. **pdf.js v6 `render()`** — `page.render({ canvasContext, viewport })` fails type-check; v6 requires `{ canvas, viewport }` (canvas is the primary param, canvasContext is a compat shim).
2. **Multi-item term matching** — a search term crossing several pdf.js text items needs a space inserted between items on the same baseline only when there is a horizontal gap (real word boundary); visually contiguous items (one word split by a style change, e.g. subset/Type3 fonts) join without a separator. PyMuPDF span bboxes carry ~1e-5pt float jitter, so `gap > 0` must be `gap > JOIN_SPACE_EPSILON` (0.5pt) or tightly packed glyph runs get spurious spaces.
3. **Svelte 5 + pdf.js concurrency** — a sidebar click fires two effects that both render the same canvas; pdf.js throws "Cannot use the same canvas during multiple render()". Fix: cancel the in-flight RenderTask, expose the render promise synchronously (before `await getPage()`), and abort a superseded render right after `getPage()` if the render token changed.
**Solution:** Two-tier grouping heuristic — strong rule (gap ≤ 0.5×size, same baseline) merges regardless of font/size to recover Type3 fragments ("B"+"ooking" → "Booking"); weak rule (gap ≤ 1.2×size + same font/size) for inter-word spacing; column gutters stay split. Validate against real PDFs locally with `scripts/dump-pdf-spans.py` + `scripts/eval-grouping.ts`.
**Tags:** `#frontend` `#pdfjs` `#svelte5` `#grouping` `#type3` `#canvas`

### [2026-06-24] Bind mount silently overwrites a venv built into the image
**Context:** INFRA-001 — dev compose mounted the repo as `../:/app` over an image whose venv had been created at `/app/.venv` during build.
**Problem:** The container died with `uvicorn: not found` even though the build log clearly showed a successful install. Nothing in the build output hints at the failure, because the build genuinely succeeded — the breakage happens at run time.
**Solution:** Move the venv outside every mount point: create it at `/opt/venv` and point `PATH` at `/opt/venv/bin`. Update the Dockerfile and both compose files together.
**Why:** A bind mount replaces the image's directory contents at that path wholesale. Anything the build wrote under the mount point still exists in the image layer but is invisible at run time — the host directory shadows it. Any build artifact living under a path you also mount is subject to this; the venv is just the most common casualty.
**Tags:** `#docker` `#compose` `#venv` `#bind-mount` `#debugging`

### [2026-06-24] .gitignore negation patterns match paths literally, not by suffix
**Context:** Moved the test suite to `backend/tests/` and the fixture `sample.pdf` stopped being tracked.
**Problem:** CI failed with "PDF file not found". The un-ignore rule `!tests/data/*.pdf` was still present and looked correct, but no longer matched anything after the move.
**Solution:** Add `!backend/tests/data/*.pdf` to match the new location, and drop the over-broad `data/` rule that was ignoring the directory in the first place.
**Why:** A pattern containing a `/` anywhere except at the end is anchored to the `.gitignore` file's directory — `tests/data/*.pdf` means exactly `<root>/tests/data/`, not "any path ending in tests/data". Moving a directory therefore silently invalidates every anchored negation that pointed into it. A negation also cannot resurrect a file whose *parent directory* is excluded, so the broad `data/` rule had to go regardless. Verify with `git check-ignore -v <path>`, which prints the exact rule that decided.
**Tags:** `#git` `#gitignore` `#ci` `#file-tracking`

### [2026-06-24] GitHub Actions: uv-installed tools need `uv run`, not bare names
**Context:** Security and mutation workflows invoking `pip-audit`, `bandit`, and `mutmut` after installing them with uv.
**Problem:** Every job failed with `command not found`, despite the install step reporting success.
**Solution:** Invoke them through the project environment — `uv run pip-audit`, `uv run bandit`, `uv run mutmut`. (Fixed alongside a wrong gitleaks action major version, v8 → v3.)
**Why:** uv installs into the project's `.venv` without activating it; each `run:` step is a fresh non-login shell that never sources it, so the venv's `bin/` is absent from `PATH`. `uv run` resolves the environment explicitly per invocation, which is why it works where the bare name does not. The alternative — activating the venv in every step — is more fragile because activation does not persist across steps.
**Tags:** `#ci` `#github-actions` `#uv` `#debugging`
