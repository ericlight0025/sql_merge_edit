import * as vscode from 'vscode';
import { SearchPanel } from './SearchPanel';

export function activate(context: vscode.ExtensionContext) {
  context.subscriptions.push(
    vscode.commands.registerCommand('rgAnywhere.open', () => {
      SearchPanel.createOrShow(context.extensionUri);
    })
  );
}

export function deactivate() {}
