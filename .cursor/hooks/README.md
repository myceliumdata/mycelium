# Mycelium Cursor hooks

Project hooks for agent approval policy.

**Two locations (by design):**

| File | Shown in Settings → Hooks? |
|------|----------------------------|
| `.cursor/hooks.json` (this repo) | Often **no** — project hooks still apply when this folder is the workspace root |
| `~/.cursor/hooks.json` (your machine) | **Yes** — forwards to these scripts via `forward-to-project-hook.py` |

Reload: save either file, then **Developer: Reload Window**. Open the **Hooks** output channel to debug.

| Hook | Script | Behavior |
|------|--------|----------|
| `preToolUse` (Delete) | `allow-file-delete.py` | Auto-allow file deletes via the Delete tool (workflow cleanup, etc.) |
| `beforeShellExecution` | `gate-directory-deletion.py` | Prompt before `rm -r`, `rm -rf`, `rmdir`, and similar directory-removal commands |

Adjust matchers in `.cursor/hooks.json` if policies change.

Hooks are invoked via `python3` (no execute bit required). Debug in Cursor **Hooks** output channel.

If hooks block normal work, temporarily disable them in **Cursor Settings → Hooks** or fix the script exit code.
