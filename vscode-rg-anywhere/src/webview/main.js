/* global acquireVsCodeApi */
'use strict';

const vscode = acquireVsCodeApi();

// ── State ──────────────────────────────────────────────────────────────────
const state = {
  folders: [],
  results: [],          // SearchFileResult[]  (all from last search)
  filtered: [],         // after filter/sort
  activeFileIdx: -1,    // index in filtered
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

// ── Tabs ───────────────────────────────────────────────────────────────────
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(btn.dataset.target).classList.add('active');
  });
});

// ── Toggle buttons ─────────────────────────────────────────────────────────
function initToggle(el, defaultOn) {
  el.classList.toggle('on', defaultOn);
  el.addEventListener('click', () => el.classList.toggle('on'));
}

initToggle(toggleCase, false);
initToggle(toggleRegex, false);
initToggle(toggleRecur, true);

// ── Search ─────────────────────────────────────────────────────────────────
function doSearch() {
  if (state.folders.length === 0) {
    setStatus('Add at least one folder first.');
    return;
  }
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
  if (state.searching) {
    vscode.postMessage({ type: 'cancelSearch' });
  } else {
    doSearch();
  }
});

// ── Folders ────────────────────────────────────────────────────────────────
btnAddFolder.addEventListener('click', () => {
  vscode.postMessage({ type: 'addFolder' });
});

function addFolderToUI(folder) {
  if (state.folders.includes(folder)) { return; }
  state.folders.push(folder);
  const item = document.createElement('div');
  item.className = 'folder-item';
  item.dataset.folder = folder;

  const label = document.createElement('span');
  label.textContent = folder;
  label.style.flex = '1';
  label.style.overflow = 'hidden';
  label.style.textOverflow = 'ellipsis';
  label.style.whiteSpace = 'nowrap';
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

// ── Results ────────────────────────────────────────────────────────────────
function applyFiltersAndSort() {
  const nameKw  = filterName.value.toLowerCase();
  const extKw   = filterExt.value.toLowerCase().replace(/^\*\./, '').replace(/^\./, '');
  const minHits = parseInt(filterMinHits.value, 10) || 0;

  let list = state.results.filter(r => {
    if (nameKw && !r.filePath.toLowerCase().includes(nameKw)) { return false; }
    if (extKw) {
      const ext = r.filePath.split('.').pop().toLowerCase();
      if (ext !== extKw) { return false; }
    }
    if (r.hitCount < minHits) { return false; }
    return true;
  });

  const [field, dir] = sortSelect.value.split('-');
  list.sort((a, b) => {
    let cmp = 0;
    if (field === 'hits') {
      cmp = a.hitCount - b.hitCount;
    } else {
      cmp = a.filePath.localeCompare(b.filePath);
    }
    return dir === 'asc' ? cmp : -cmp;
  });

  state.filtered = list;
  state.activeFileIdx = Math.min(state.activeFileIdx, list.length - 1);
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
    info.style.flex = '1';
    info.style.overflow = 'hidden';

    const nameEl = document.createElement('div');
    nameEl.className = 'file-name';
    nameEl.textContent = name;
    nameEl.title = r.filePath;

    const dirEl = document.createElement('div');
    dirEl.className = 'file-dir';
    dirEl.textContent = dir;
    dirEl.title = r.filePath;

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
  state.activeHitIdx = 0;
  renderFileList();
  renderPreview();
}

// ── Preview ────────────────────────────────────────────────────────────────
function renderPreview() {
  const r = state.filtered[state.activeFileIdx];
  if (!r) {
    previewPath.textContent = '';
    previewCode.innerHTML = '<div class="placeholder">Select a file to preview</div>';
    btnPrev.disabled = true;
    btnNext.disabled = true;
    btnOpen.disabled = true;
    return;
  }

  previewPath.textContent = r.filePath;
  btnOpen.disabled = false;

  const hitRows = r.hits;
  const activeHit = hitRows[state.activeHitIdx];

  btnPrev.disabled = state.activeHitIdx <= 0;
  btnNext.disabled = state.activeHitIdx >= hitRows.length - 1;

  const table = document.createElement('table');
  table.className = 'code-table';

  for (let i = 0; i < hitRows.length; i++) {
    const hit = hitRows[i];
    const tr  = document.createElement('tr');
    tr.className = 'hit-line' + (i === state.activeHitIdx ? ' active-hit' : '');

    const ln  = document.createElement('td');
    ln.className = 'ln';
    ln.textContent = hit.lineNumber;

    const code = document.createElement('td');
    code.className = 'code-line';
    code.appendChild(highlightLine(hit.lineText, hit.submatches));

    tr.append(ln, code);
    table.appendChild(tr);
  }

  previewCode.innerHTML = '';
  previewCode.appendChild(table);

  // scroll active hit into view
  if (activeHit) {
    const activeRow = table.querySelectorAll('tr.active-hit')[0];
    if (activeRow) { activeRow.scrollIntoView({ block: 'center' }); }
  }
}

function highlightLine(text, submatches) {
  const frag = document.createDocumentFragment();
  let pos = 0;
  for (const sm of submatches) {
    if (sm.start > pos) {
      frag.appendChild(document.createTextNode(text.slice(pos, sm.start)));
    }
    const mark = document.createElement('mark');
    mark.className = 'hit-text';
    mark.textContent = text.slice(sm.start, sm.end);
    frag.appendChild(mark);
    pos = sm.end;
  }
  if (pos < text.length) {
    frag.appendChild(document.createTextNode(text.slice(pos)));
  }
  return frag;
}

btnPrev.addEventListener('click', () => {
  if (state.activeHitIdx > 0) {
    state.activeHitIdx--;
    renderPreview();
  }
});

btnNext.addEventListener('click', () => {
  const r = state.filtered[state.activeFileIdx];
  if (r && state.activeHitIdx < r.hits.length - 1) {
    state.activeHitIdx++;
    renderPreview();
  }
});

btnOpen.addEventListener('click', () => {
  const r = state.filtered[state.activeFileIdx];
  if (!r) { return; }
  const hit = r.hits[state.activeHitIdx] ?? r.hits[0];
  vscode.postMessage({ type: 'openFile', filePath: r.filePath, lineNumber: hit?.lineNumber ?? 1 });
});

// ── Filters / sort live update ─────────────────────────────────────────────
[filterName, filterExt, filterMinHits, sortSelect].forEach(el => {
  el.addEventListener('input', () => {
    applyFiltersAndSort();
    renderFileList();
    if (state.activeFileIdx === -1 && state.filtered.length > 0) {
      state.activeFileIdx = 0;
    }
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
      setStatus(`${msg.totalFiles} file(s), ${msg.totalHits} hit(s)`);
      applyFiltersAndSort();
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
