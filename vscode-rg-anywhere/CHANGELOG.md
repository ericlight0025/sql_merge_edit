# Changelog

## [0.1.0] — 2026-06-08

### Added
- Three-column panel: search sidebar / results list / code preview
- Search any folder on disk via `+ Add` (uses `vscode.window.showOpenDialog`)
- Folder list persisted across sessions (extension global state)
- Case-sensitive, regex, recursive toggles
- Include / exclude glob inputs
- Streaming results via `rg --json` — files appear as they are found
- Result list with hit-count badges
- Live filter by filename keyword, file extension, minimum hit count
- Sort by hit count or filename (ascending / descending)
- Code preview with line numbers and submatch highlighting
- Prev / Next hit navigation within a file
- Open file in editor at matching line (`vscode.window.showTextDocument`)
- Dangerous-extension guard — reveals in OS instead of opening directly
- Syntax highlighting in preview (JS/TS, Python, Rust, Go)
- Settings tab with persistent defaults (`rgAnywhere.*` configuration keys)
- Keyboard shortcut: Ctrl+Alt+R (Cmd+Alt+R on macOS)
