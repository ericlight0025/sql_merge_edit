/* global acquireVsCodeApi */
'use strict';

const vscode = acquireVsCodeApi();

// ── State ──────────────────────────────────────────────────────────────────
const state = {
  folders: [],
  results: [],
  filtered: [],
  activeFileIdx: -1,
  activeHitIdx: 0,
  searching: false,
};

// ── DOM refs ───────────────────────────────────────────────────────────────
const $ = id => document.getElementById(id);

const queryInput    = $('query');
const btnSearch     = $('btn-search');
const btnAddFolder  = $('btn-add-folder');
const folderList    = $('folder-list');
const fileList      = $('file-list');
const statusText    = $('status-text');
const sortSelect    = $('sort-select');
const filterName    = $('filter-name');
const filterExt     = $('filter-ext');
const filterMinHits = $('filter-min-hits');
const previewCode   = $('preview-code');
const previewPath   = $('preview-filepath');
const btnPrev       = $('btn-prev');
const btnNext       = $('btn-next');
const btnOpen       = $('btn-open');
const spinnerEl     = $('spinner');
const toggleCase    = $('toggle-case');
const toggleRegex   = $('toggle-regex');
const toggleRecur   = $('toggle-recur');

// settings tab
const prefInclude   = $('pref-include');
const prefExclude   = $('pref-exclude');
const prefSort      = $('pref-sort');

// ── Tabs ───────────────────────────────────────────────────────────────────
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    $(btn.dataset.target).classList.add('active');
  });
});

// ── Toggle buttons ─────────────────────────────────────────────────────────
function initToggle(el, defaultOn) {
  el.classList.toggle('on', defaultOn);
  el.addEventListener('click', () => el.classList.toggle('on'));
}

initToggle(toggleCase,  false);
initToggle(toggleRegex, false);
initToggle(toggleRecur, true);

// ── Search ─────────────────────────────────────────────────────────────────
function doSearch() {
  if (state.folders.length === 0) { setStatus('Add at least one folder first.'); return; }
  const query = queryInput.value.trim();
  if (!query) { return; }

  state.results = [];
  state.filtered = [];
  state.activeFileIdx = -1;
  state.activeHitIdx = 0;
  renderFileList();
  renderPreview();

  vscode.postMessage({
    type: 'search',
    options: {
      query,
      folders: state.folders,
      caseSensitive: toggleCase.classList.contains('on'),
      useRegex: toggleRegex.classList.contains('on'),
      recursive: toggleRecur.classList.contains('on'),
      includeGlob: $('include-glob').value.trim(),
      excludeGlob: $('exclude-glob').value.trim(),
    },
  });
}

queryInput.addEventListener('keydown', e => { if (e.key === 'Enter') { doSearch(); } });
btnSearch.addEventListener('click', () => {
  if (state.searching) { vscode.postMessage({ type: 'cancelSearch' }); }
  else { doSearch(); }
});

// ── Folders ────────────────────────────────────────────────────────────────
btnAddFolder.addEventListener('click', () => vscode.postMessage({ type: 'addFolder' }));

function addFolderToUI(folder) {
  if (state.folders.includes(folder)) { return; }
  state.folders.push(folder);

  const item = document.createElement('div');
  item.className = 'folder-item';

  const label = document.createElement('span');
  label.textContent = folder;
  label.style.cssText = 'flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;';
  label.title = folder;

  const rmBtn = document.createElement('button');
  rmBtn.className = 'btn-remove-folder';
  rmBtn.textContent = '×';
  rmBtn.title = 'Remove';
  rmBtn.addEventListener('click', () => {
    state.folders = state.folders.filter(f => f !== folder);
    item.remove();
    vscode.postMessage({ type: 'removeFolder', folder });
  });

  item.append(label, rmBtn);
  folderList.appendChild(item);
}

// ── Settings persistence ───────────────────────────────────────────────────
function applySettings(settings) {
  prefInclude.value = settings.defaultIncludeGlob ?? '';
  prefExclude.value = settings.defaultExcludeGlob ?? '';
  prefSort.value    = settings.defaultSort ?? 'hits-desc';
  // Mirror defaults to search form
  $('include-glob').value = settings.defaultIncludeGlob ?? '';
  $('exclude-glob').value = settings.defaultExcludeGlob ?? '';
  sortSelect.value        = settings.defaultSort ?? 'hits-desc';
}

function saveSettings() {
  vscode.postMessage({
    type: 'saveSettings',
    settings: {
      defaultIncludeGlob: prefInclude.value.trim(),
      defaultExcludeGlob: prefExclude.value.trim(),
      defaultSort: prefSort.value,
    },
  });
}

[prefInclude, prefExclude, prefSort].forEach(el => el.addEventListener('change', saveSettings));

// ── Results ────────────────────────────────────────────────────────────────
function applyFiltersAndSort() {
  const nameKw  = filterName.value.toLowerCase();
  const extKw   = filterExt.value.toLowerCase().replace(/^\*?\./, '');
  const minHits = parseInt(filterMinHits.value, 10) || 0;

  let list = state.results.filter(r => {
    if (nameKw && !r.filePath.toLowerCase().includes(nameKw)) { return false; }
    if (extKw) {
      const ext = r.filePath.split('.').pop().toLowerCase();
      if (ext !== extKw) { return false; }
    }
    return r.hitCount >= minHits;
  });

  const [field, dir] = sortSelect.value.split('-');
  list.sort((a, b) => {
    const cmp = field === 'hits'
      ? a.hitCount - b.hitCount
      : a.filePath.localeCompare(b.filePath);
    return dir === 'asc' ? cmp : -cmp;
  });

  state.filtered = list;
  if (state.activeFileIdx >= list.length) { state.activeFileIdx = list.length - 1; }
}

function renderFileList() {
  fileList.innerHTML = '';
  if (state.filtered.length === 0) {
    fileList.innerHTML = '<div class="placeholder">No results</div>';
    return;
  }
  state.filtered.forEach((r, idx) => {
    const parts = r.filePath.replace(/\\/g, '/').split('/');
    const name  = parts.pop();
    const dir   = parts.join('/');

    const item = document.createElement('div');
    item.className = 'file-item' + (idx === state.activeFileIdx ? ' active' : '');
    item.addEventListener('click', () => selectFile(idx));

    const info = document.createElement('div');
    info.style.cssText = 'flex:1;overflow:hidden;';

    const nameEl = document.createElement('div');
    nameEl.className = 'file-name';
    nameEl.textContent = name;
    nameEl.title = r.filePath;

    const dirEl = document.createElement('div');
    dirEl.className = 'file-dir';
    dirEl.textContent = dir;

    const badge = document.createElement('span');
    badge.className = 'hit-badge';
    badge.textContent = r.hitCount;

    info.append(nameEl, dirEl);
    item.append(info, badge);
    fileList.appendChild(item);
  });
}

function selectFile(idx) {
  state.activeFileIdx = idx;
  state.activeHitIdx  = 0;
  renderFileList();
  renderPreview();
}

// ── Preview ────────────────────────────────────────────────────────────────
function renderPreview() {
  const r = state.filtered[state.activeFileIdx];
  if (!r) {
    previewPath.textContent = '';
    previewCode.innerHTML = '<div class="placeholder">Select a file to preview</div>';
    btnPrev.disabled = btnNext.disabled = btnOpen.disabled = true;
    return;
  }

  previewPath.textContent = r.filePath;
  btnOpen.disabled = false;

  const ext = r.filePath.split('.').pop().toLowerCase();
  btnPrev.disabled = state.activeHitIdx <= 0;
  btnNext.disabled = state.activeHitIdx >= r.hits.length - 1;

  const table = document.createElement('table');
  table.className = 'code-table';

  r.hits.forEach((hit, i) => {
    const tr   = document.createElement('tr');
    tr.className = 'hit-line' + (i === state.activeHitIdx ? ' active-hit' : '');

    const ln   = document.createElement('td');
    ln.className = 'ln';
    ln.textContent = hit.lineNumber;

    const code = document.createElement('td');
    code.className = 'code-line';
    code.appendChild(renderHitLine(hit.lineText, hit.submatches, ext));

    tr.append(ln, code);
    table.appendChild(tr);
  });

  previewCode.innerHTML = '';
  previewCode.appendChild(table);

  const activeRow = table.querySelector('tr.active-hit');
  if (activeRow) { activeRow.scrollIntoView({ block: 'center' }); }
}

// ── Hit line renderer (syntax + match highlight) ───────────────────────────
function renderHitLine(text, submatches, ext) {
  const frag = document.createDocumentFragment();
  let pos = 0;

  for (const sm of submatches) {
    if (sm.start > pos) {
      appendSyntaxNodes(frag, text.slice(pos, sm.start), ext);
    }
    const mark = document.createElement('mark');
    mark.className = 'hit-text';
    mark.textContent = text.slice(sm.start, sm.end);
    frag.appendChild(mark);
    pos = sm.end;
  }

  if (pos < text.length) {
    appendSyntaxNodes(frag, text.slice(pos), ext);
  }

  return frag;
}

function appendSyntaxNodes(frag, text, ext) {
  const tokens = tokenize(text, ext);
  for (const tok of tokens) {
    if (tok.type === 'plain') {
      frag.appendChild(document.createTextNode(tok.text));
    } else {
      const span = document.createElement('span');
      span.className = 'sh-' + tok.type;
      span.textContent = tok.text;
      frag.appendChild(span);
    }
  }
}

// ── Syntax tokenizer ───────────────────────────────────────────────────────
const KW_JS = new Set([
  'if','else','for','while','do','return','function','const','let','var',
  'class','import','export','default','from','new','delete','typeof',
  'instanceof','switch','case','break','continue','try','catch','finally',
  'throw','async','await','yield','static','public','private','protected',
  'interface','type','enum','extends','implements','super','this','void',
  'true','false','null','undefined','of','in','get','set','abstract',
]);

const KW_PY = new Set([
  'if','elif','else','for','while','return','def','class','import','from',
  'as','with','in','not','and','or','True','False','None','pass','break',
  'continue','try','except','finally','raise','yield','lambda','global',
  'nonlocal','del','is','assert','async','await',
]);

const KW_RS = new Set([
  'fn','let','mut','const','static','struct','impl','trait','enum','use',
  'mod','pub','crate','super','self','return','if','else','for','while',
  'loop','match','where','ref','move','dyn','type','unsafe','extern',
  'true','false',
]);

const KW_GO = new Set([
  'func','var','const','type','struct','interface','package','import',
  'return','if','else','for','range','switch','case','default','break',
  'continue','go','defer','chan','select','map','make','new','nil',
  'true','false','len','cap','append','copy','delete','close',
]);

const EXT_MAP = {
  js: KW_JS, jsx: KW_JS, ts: KW_JS, tsx: KW_JS, mjs: KW_JS, cjs: KW_JS,
  py: KW_PY, pyw: KW_PY,
  rs: KW_RS,
  go: KW_GO,
};

function getKeywords(ext) {
  return EXT_MAP[ext] ?? null;
}

function tokenize(text, ext) {
  const kws = getKeywords(ext);
  const tokens = [];
  let i = 0;
  const n = text.length;

  while (i < n) {
    const ch = text[i];

    // Line comment: // or #
    if ((ch === '/' && text[i + 1] === '/') || (ch === '#' && ext !== 'sh' || ch === '#')) {
      tokens.push({ type: 'cm', text: text.slice(i) });
      break;
    }

    // Block comment /* ... */
    if (ch === '/' && text[i + 1] === '*') {
      const end = text.indexOf('*/', i + 2);
      const tok = end === -1 ? text.slice(i) : text.slice(i, end + 2);
      tokens.push({ type: 'cm', text: tok });
      i += tok.length;
      continue;
    }

    // String literals: ", ', `
    if (ch === '"' || ch === "'" || ch === '`') {
      let j = i + 1;
      while (j < n) {
        if (text[j] === '\\') { j += 2; continue; }
        if (text[j] === ch)   { j++;    break; }
        j++;
      }
      tokens.push({ type: 'str', text: text.slice(i, j) });
      i = j;
      continue;
    }

    // Number literal (not preceded by identifier char)
    if (/\d/.test(ch) && (i === 0 || !/[\w$]/.test(text[i - 1]))) {
      let j = i;
      // hex
      if (text[j] === '0' && (text[j + 1] === 'x' || text[j + 1] === 'X')) {
        j += 2;
        while (j < n && /[0-9a-fA-F_]/.test(text[j])) { j++; }
      } else {
        while (j < n && /[\d._]/.test(text[j])) { j++; }
        if (j < n && (text[j] === 'e' || text[j] === 'E')) {
          j++;
          if (j < n && (text[j] === '+' || text[j] === '-')) { j++; }
          while (j < n && /\d/.test(text[j])) { j++; }
        }
      }
      tokens.push({ type: 'num', text: text.slice(i, j) });
      i = j;
      continue;
    }

    // Identifier, keyword, or function name
    if (/[A-Za-z_$]/.test(ch)) {
      let j = i;
      while (j < n && /[\w$]/.test(text[j])) { j++; }
      const word = text.slice(i, j);
      // skip whitespace after word to check for '('
      let k = j;
      while (k < n && text[k] === ' ') { k++; }
      if (kws && kws.has(word)) {
        tokens.push({ type: 'kw', text: word });
      } else if (k < n && text[k] === '(') {
        tokens.push({ type: 'fn', text: word });
      } else if (/^[A-Z]/.test(word) && kws) {
        // PascalCase → treat as type
        tokens.push({ type: 'ty', text: word });
      } else {
        tokens.push({ type: 'plain', text: word });
      }
      i = j;
      continue;
    }

    // Consume a run of non-special chars as plain text
    let j = i + 1;
    while (j < n) {
      const c = text[j];
      if (c === '/' || c === '#' || c === '"' || c === "'" || c === '`' ||
          /[\d]/.test(c) || /[A-Za-z_$]/.test(c)) { break; }
      j++;
    }
    tokens.push({ type: 'plain', text: text.slice(i, j) });
    i = j;
  }

  return tokens;
}

// ── Nav buttons ────────────────────────────────────────────────────────────
btnPrev.addEventListener('click', () => {
  if (state.activeHitIdx > 0) { state.activeHitIdx--; renderPreview(); }
});

btnNext.addEventListener('click', () => {
  const r = state.filtered[state.activeFileIdx];
  if (r && state.activeHitIdx < r.hits.length - 1) { state.activeHitIdx++; renderPreview(); }
});

btnOpen.addEventListener('click', () => {
  const r = state.filtered[state.activeFileIdx];
  if (!r) { return; }
  const hit = r.hits[state.activeHitIdx] ?? r.hits[0];
  vscode.postMessage({ type: 'openFile', filePath: r.filePath, lineNumber: hit?.lineNumber ?? 1 });
});

// ── Filters / sort ─────────────────────────────────────────────────────────
[filterName, filterExt, filterMinHits, sortSelect].forEach(el => {
  el.addEventListener('input', () => {
    applyFiltersAndSort();
    renderFileList();
    if (state.activeFileIdx === -1 && state.filtered.length > 0) { state.activeFileIdx = 0; }
    renderPreview();
  });
});

// ── Status helpers ─────────────────────────────────────────────────────────
function setStatus(text) { statusText.textContent = text; }

function setSearching(on) {
  state.searching = on;
  btnSearch.textContent = on ? 'Cancel' : 'Search';
  spinnerEl.style.display = on ? 'inline-block' : 'none';
}

// ── Message handler ────────────────────────────────────────────────────────
window.addEventListener('message', ({ data: msg }) => {
  switch (msg.type) {
    case 'init':
      applySettings(msg.settings);
      for (const f of (msg.folders ?? [])) { addFolderToUI(f); }
      break;

    case 'folderAdded':
      addFolderToUI(msg.folder);
      break;

    case 'searchStart':
      setSearching(true);
      setStatus('Searching…');
      state.results = [];
      state.filtered = [];
      renderFileList();
      break;

    case 'searchResult':
      state.results.push(msg.result);
      applyFiltersAndSort();
      renderFileList();
      setStatus(`${state.results.length} file(s)…`);
      if (state.activeFileIdx === -1 && state.filtered.length > 0) {
        state.activeFileIdx = 0;
        renderPreview();
      }
      break;

    case 'searchDone':
      setSearching(false);
      applyFiltersAndSort();
      setStatus(`${msg.totalFiles} file(s), ${msg.totalHits} hit(s)`);
      renderFileList();
      if (state.activeFileIdx === -1 && state.filtered.length > 0) {
        state.activeFileIdx = 0;
        renderPreview();
      }
      break;

    case 'searchError':
      setStatus('Error: ' + msg.message);
      break;

    case 'searchCancelled':
      setSearching(false);
      setStatus('Cancelled.');
      break;
  }
});
