# RG Anywhere

A VS Code extension that runs [ripgrep](https://github.com/BurntSushi/ripgrep) across **any folder on disk**, not just the folders in your workspace.

## Why

VS Code's built-in search is great, but it only searches folders you've explicitly added to the workspace.  
RG Anywhere lets you point it at any path — including directories completely outside your project.

| Feature | VS Code built-in | RG Anywhere |
|---|---|---|
| Search outside workspace | ❌ | ✅ |
| Sort results by hit count | ❌ | ✅ |
| Filter by extension / min hits | ❌ | ✅ |
| Aggregate results across multiple folders | Limited | ✅ |

## Usage

Open the panel via the Command Palette:

```
RG Anywhere: Open Search Panel
```

Or use the default keybinding: **Ctrl+Alt+R** (macOS: **Cmd+Alt+R**).

### Search tab

1. **Add folders** — click `+ Add` to pick one or more directories.
2. **Type a pattern** and press **Enter** (or click **Search**).
3. Results stream in on the left; click a file to preview it on the right.
4. Use **↑ Prev / ↓ Next** to jump between hits in the preview.
5. Click **Open** to open the file in the editor at the matching line.

### Toggles

| Toggle | Default | Effect |
|---|---|---|
| **Aa** | off | Case-sensitive search |
| **.\*** | off | Treat pattern as regex |
| **⤵ Recursive** | on | Search subdirectories |

### Filters (results pane)

- **Filename keyword** — live-filter the result list by path substring.
- **.ext** — keep only files with a specific extension (e.g. `ts`).
- **≥ hits** — hide files with fewer than N matches.

### Sort

Use the dropdown in the results header to sort by:
- Hits ↓ / ↑
- Filename A→Z / Z→A

### Settings tab

Persistent defaults saved to VS Code global settings (`rgAnywhere.*`):

| Setting | Key |
|---|---|
| Default include glob | `rgAnywhere.defaultIncludeGlob` |
| Default exclude glob | `rgAnywhere.defaultExcludeGlob` |
| Default sort order | `rgAnywhere.defaultSort` |

Folder list is also persisted across sessions (stored in extension global state).

## Safety

Files with potentially executable extensions (`.exe`, `.bat`, `.sh`, `.ps1`, etc.)  
will be **revealed in the OS file manager** instead of opened directly in the editor.

## Requirements

- VS Code ≥ 1.85
- No additional installs — the extension bundles `@vscode/ripgrep`

## Development

```bash
npm install
npm run compile      # tsc + copies webview assets to out/webview/
npm run watch        # tsc watch mode (run copy-webview manually after changes to src/webview/)
```

Press **F5** in VS Code to launch the Extension Development Host.

## Building a .vsix

```bash
npm install -g @vscode/vsce
vsce package
```

## License

[Polyform Noncommercial 1.0.0](LICENSE) — free for personal and non-commercial use;
commercial use (including SaaS, paid products, or in-business tooling) is not permitted.
