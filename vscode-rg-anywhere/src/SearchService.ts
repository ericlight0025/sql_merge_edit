import * as cp from 'child_process';
import { SearchOptions, SearchFileResult, SearchHit, SubMatch } from './models';

interface RgBegin { type: 'begin'; data: { path: { text: string } } }
interface RgMatch {
  type: 'match';
  data: {
    path: { text: string };
    lines: { text: string };
    line_number: number;
    submatches: Array<{ match: { text: string }; start: number; end: number }>;
  };
}
interface RgEnd { type: 'end'; data: { path: { text: string } } }
type RgEvent = RgBegin | RgMatch | RgEnd | { type: 'summary' };

export type ResultCallback = (result: SearchFileResult) => void;
export type DoneCallback = (totalFiles: number, totalHits: number) => void;
export type ErrorCallback = (msg: string) => void;

class RgStreamParser {
  private currentFile: string | null = null;
  private currentHits: SearchHit[] = [];
  private buffer = '';

  feed(chunk: string): SearchFileResult[] {
    this.buffer += chunk;
    const lines = this.buffer.split('\n');
    this.buffer = lines.pop() ?? '';
    const emitted: SearchFileResult[] = [];
    for (const line of lines) {
      if (!line.trim()) { continue; }
      try {
        const result = this.handleEvent(JSON.parse(line) as RgEvent);
        if (result) { emitted.push(result); }
      } catch { /* skip malformed */ }
    }
    return emitted;
  }

  private handleEvent(event: RgEvent): SearchFileResult | null {
    if (event.type === 'begin') {
      this.currentFile = event.data.path.text;
      this.currentHits = [];
    } else if (event.type === 'match') {
      const submatches: SubMatch[] = event.data.submatches.map(sm => ({
        text: sm.match.text,
        start: sm.start,
        end: sm.end,
      }));
      this.currentHits.push({
        lineNumber: event.data.line_number,
        lineText: event.data.lines.text.replace(/\n$/, ''),
        submatches,
      });
    } else if (event.type === 'end' && this.currentFile !== null) {
      if (this.currentHits.length > 0) {
        const result: SearchFileResult = {
          filePath: this.currentFile,
          hits: [...this.currentHits],
          hitCount: this.currentHits.length,
        };
        this.currentFile = null;
        this.currentHits = [];
        return result;
      }
      this.currentFile = null;
      this.currentHits = [];
    }
    return null;
  }
}

export class SearchService {
  private activeProcesses: cp.ChildProcess[] = [];

  cancel() {
    for (const proc of this.activeProcesses) {
      try { proc.kill(); } catch { /* already dead */ }
    }
    this.activeProcesses = [];
  }

  search(
    opts: SearchOptions,
    onResult: ResultCallback,
    onDone: DoneCallback,
    onError: ErrorCallback
  ): void {
    this.cancel();

    if (!opts.query.trim() || opts.folders.length === 0) {
      onDone(0, 0);
      return;
    }

    const rgPath = this.getRgPath();
    const args = this.buildArgs(opts);
    let pending = opts.folders.length;
    let totalFiles = 0;
    let totalHits = 0;

    for (const folder of opts.folders) {
      const parser = new RgStreamParser();
      const proc = cp.spawn(rgPath, [...args, '--', opts.query, folder], {
        stdio: ['ignore', 'pipe', 'pipe'],
      });
      this.activeProcesses.push(proc);

      proc.stdout.on('data', (chunk: Buffer) => {
        const results = parser.feed(chunk.toString());
        for (const r of results) {
          totalFiles++;
          totalHits += r.hitCount;
          onResult(r);
        }
      });

      proc.stderr.on('data', (chunk: Buffer) => {
        const msg = chunk.toString().trim();
        if (msg) { onError(msg); }
      });

      proc.on('close', () => {
        this.activeProcesses = this.activeProcesses.filter(p => p !== proc);
        pending--;
        if (pending === 0) {
          onDone(totalFiles, totalHits);
        }
      });
    }
  }

  private buildArgs(opts: SearchOptions): string[] {
    const args = ['--json', '--no-heading'];
    if (!opts.caseSensitive) { args.push('--ignore-case'); }
    if (!opts.useRegex) { args.push('--fixed-strings'); }
    if (!opts.recursive) { args.push('--max-depth', '1'); }
    if (opts.includeGlob) { args.push('--glob', opts.includeGlob); }
    if (opts.excludeGlob) { args.push('--glob', `!${opts.excludeGlob}`); }
    return args;
  }

  private getRgPath(): string {
    try {
      // eslint-disable-next-line @typescript-eslint/no-var-requires
      return require('@vscode/ripgrep').rgPath as string;
    } catch {
      return 'rg';
    }
  }
}
