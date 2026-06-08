export interface SearchOptions {
  query: string;
  folders: string[];
  caseSensitive: boolean;
  useRegex: boolean;
  recursive: boolean;
  includeGlob: string;
  excludeGlob: string;
}

export interface SubMatch {
  text: string;
  start: number;
  end: number;
}

export interface SearchHit {
  lineNumber: number;
  lineText: string;
  submatches: SubMatch[];
}

export interface SearchFileResult {
  filePath: string;
  hits: SearchHit[];
  hitCount: number;
}

export interface UserSettings {
  defaultIncludeGlob: string;
  defaultExcludeGlob: string;
  defaultSort: string;
}

export type SortField = 'hitCount' | 'filename';
export type SortDir = 'asc' | 'desc';

// Messages from webview → extension
export type WebviewMessage =
  | { type: 'search'; options: SearchOptions }
  | { type: 'addFolder' }
  | { type: 'removeFolder'; folder: string }
  | { type: 'openFile'; filePath: string; lineNumber: number }
  | { type: 'revealFile'; filePath: string }
  | { type: 'cancelSearch' }
  | { type: 'saveSettings'; settings: UserSettings };

// Messages from extension → webview
export type ExtensionMessage =
  | { type: 'folderAdded'; folder: string }
  | { type: 'searchStart' }
  | { type: 'searchResult'; result: SearchFileResult }
  | { type: 'searchDone'; totalFiles: number; totalHits: number }
  | { type: 'searchError'; message: string }
  | { type: 'searchCancelled' }
  | { type: 'init'; settings: UserSettings; folders: string[] };
