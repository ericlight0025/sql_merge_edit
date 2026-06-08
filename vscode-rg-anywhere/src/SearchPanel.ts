import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { SearchService } from './SearchService';
import { WebviewMessage, ExtensionMessage, SearchOptions } from './models';

const DANGEROUS_EXTENSIONS = new Set([
  '.exe', '.bat', '.cmd', '.com', '.sh', '.bash', '.zsh', '.ps1',
  '.msi', '.dmg', '.pkg', '.deb', '.rpm', '.AppImage',
]);

export class SearchPanel {
  static readonly viewType = 'rgAnywhere.searchPanel';
  private static instance: SearchPanel | undefined;

  private readonly panel: vscode.WebviewPanel;
  private readonly service: SearchService;
  private folders: string[] = [];
  private disposables: vscode.Disposable[] = [];

  static createOrShow(extensionUri: vscode.Uri) {
    const column = vscode.window.activeTextEditor
      ? vscode.window.activeTextEditor.viewColumn
      : undefined;

    if (SearchPanel.instance) {
      SearchPanel.instance.panel.reveal(column);
      return;
    }

    const panel = vscode.window.createWebviewPanel(
      SearchPanel.viewType,
      'RG Anywhere',
      column ?? vscode.ViewColumn.One,
      {
        enableScripts: true,
        retainContextWhenHidden: true,
        localResourceRoots: [],
      }
    );

    SearchPanel.instance = new SearchPanel(panel);
  }

  private constructor(panel: vscode.WebviewPanel) {
    this.panel = panel;
    this.service = new SearchService();

    this.panel.webview.html = this.getHtml();

    this.panel.webview.onDidReceiveMessage(
      (msg: WebviewMessage) => this.handleMessage(msg),
      null,
      this.disposables
    );

    this.panel.onDidDispose(() => this.dispose(), null, this.disposables);
  }

  private async handleMessage(msg: WebviewMessage) {
    switch (msg.type) {
      case 'search':
        this.runSearch({ ...msg.options, folders: this.folders });
        break;

      case 'addFolder': {
        const uris = await vscode.window.showOpenDialog({
          canSelectFolders: true,
          canSelectFiles: false,
          canSelectMany: true,
          openLabel: 'Add Folder',
        });
        if (uris) {
          for (const uri of uris) {
            const f = uri.fsPath;
            if (!this.folders.includes(f)) {
              this.folders.push(f);
              this.post({ type: 'folderAdded', folder: f });
            }
          }
        }
        break;
      }

      case 'removeFolder':
        this.folders = this.folders.filter(f => f !== msg.folder);
        break;

      case 'openFile': {
        const ext = path.extname(msg.filePath).toLowerCase();
        if (DANGEROUS_EXTENSIONS.has(ext)) {
          vscode.commands.executeCommand('revealFileInOS', vscode.Uri.file(msg.filePath));
        } else {
          const uri = vscode.Uri.file(msg.filePath);
          const doc = await vscode.workspace.openTextDocument(uri);
          const editor = await vscode.window.showTextDocument(doc, { preview: false });
          const line = Math.max(0, msg.lineNumber - 1);
          const range = editor.document.lineAt(line).range;
          editor.selection = new vscode.Selection(range.start, range.start);
          editor.revealRange(range, vscode.TextEditorRevealType.InCenter);
        }
        break;
      }

      case 'revealFile':
        vscode.commands.executeCommand('revealFileInOS', vscode.Uri.file(msg.filePath));
        break;

      case 'cancelSearch':
        this.service.cancel();
        this.post({ type: 'searchCancelled' });
        break;
    }
  }

  private runSearch(opts: SearchOptions) {
    this.post({ type: 'searchStart' });
    this.service.search(
      opts,
      result => this.post({ type: 'searchResult', result }),
      (totalFiles, totalHits) => this.post({ type: 'searchDone', totalFiles, totalHits }),
      msg => this.post({ type: 'searchError', message: msg }),
    );
  }

  private post(msg: ExtensionMessage) {
    this.panel.webview.postMessage(msg);
  }

  private getHtml(): string {
    const webviewDir = path.join(__dirname, 'webview');
    const htmlPath = path.join(webviewDir, 'index.html');
    const cssPath = path.join(webviewDir, 'style.css');
    const jsPath = path.join(webviewDir, 'main.js');

    let html = fs.readFileSync(htmlPath, 'utf8');
    const css = fs.existsSync(cssPath) ? fs.readFileSync(cssPath, 'utf8') : '';
    const js = fs.existsSync(jsPath) ? fs.readFileSync(jsPath, 'utf8') : '';

    // Inline CSS and JS to avoid CSP issues with local file URIs
    html = html
      .replace('/* INLINE_CSS */', css)
      .replace('/* INLINE_JS */', js);
    return html;
  }

  dispose() {
    SearchPanel.instance = undefined;
    this.service.cancel();
    this.panel.dispose();
    for (const d of this.disposables) { d.dispose(); }
    this.disposables = [];
  }
}
