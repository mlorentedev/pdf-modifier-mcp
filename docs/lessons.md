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

### [2026-03-14] Worktree agents lose staged changes when main repo branch operations interfere
**Context:** Running two parallel agents in git worktrees while also creating branches in the main repo
**Problem:** When I created a branch in the main repo with the same name the worktree agent was going to use, the worktree's staged changes were lost. Git worktrees share the same repository, so branch operations in one worktree can affect others.
**Solution:** Do NOT create branches in the main repo while worktree agents are running. Let the agents finish first, then create branches from their output. Use git stash to extract changes from worktrees safely. Always check worktree status before manipulating shared branches.
**Tags:** `#git` `#worktree` `#parallel-agents` `#pattern`
