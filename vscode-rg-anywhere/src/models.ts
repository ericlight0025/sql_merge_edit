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

export interface FilterOptions {
  filenameKeyword: string;
  extensionFilter: string;
  minHits: number;
}

export type SortField = 'hitCount' | 'filename';
export type SortDir = 'asc' | 'desc';

export interface SortOptions {
  field: SortField;
  dir: SortDir;
}

// Messages from webview → extension
export type WebviewMessage =
  | { type: 'search'; options: SearchOptions }
  | { type: 'addFolder' }
  | { type: 'removeFolder'; folder: string }
  | { type: 'openFile'; filePath: string; lineNumber: number }
  | { type: 'revealFile'; filePath: string }
  | { type: 'cancelSearch' };

// Messages from extension → webview
export type ExtensionMessage =
  | { type: 'folderAdded'; folder: string }
  | { type: 'searchStart' }
  | { type: 'searchResult'; result: SearchFileResult }
  | { type: 'searchDone'; totalFiles: number; totalHits: number }
  | { type: 'searchError'; message: string }
  | { type: 'searchCancelled' };
