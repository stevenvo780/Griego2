// Editor & Search Functionality

function initPanelEditor(index) {
    const textarea = document.getElementById('textarea-' + index);
    if (!textarea) return;

    const editor = CodeMirror.fromTextArea(textarea, {
        mode: 'markdown',
        theme: 'dracula',
        lineNumbers: true,
        lineWrapping: true,
        extraKeys: {
            'Ctrl-S': () => savePanel(index),
            'Cmd-S': () => savePanel(index),
            'Ctrl-F': () => toggleSearch(index),
            'Cmd-F': () => toggleSearch(index)
        }
    });

    editor.setValue(panels[index].content);
    editor.on('change', () => {
        panels[index].content = editor.getValue();
        updatePanelPreview(index);
        triggerAutoSave(index);
    });

    panels[index].editor = editor;
    updatePanelPreview(index);
}

function updatePanelPreview(index) {
    const content = document.getElementById('content-' + index);
    if (content) {
        content.innerHTML = marked.parse(panels[index].content);
    }
}

// Search Logic
const searchState = {};

function toggleSearch(index) {
    const searchBar = document.getElementById(`search-bar-${index}`);
    const isVisible = searchBar.classList.contains('visible');
    
    if (isVisible) {
        searchBar.classList.remove('visible');
        clearSearch(index);
        if (panels[index].editor) panels[index].editor.focus();
    } else {
        searchBar.classList.add('visible');
        setTimeout(() => {
            const input = document.getElementById(`search-input-${index}`);
            input.focus();
            input.select();
            if (input.value) performSearch(index);
        }, 10);
    }
}

function clearSearch(index) {
    if (panels[index].editor) {
        panels[index].editor.getAllMarks().forEach(mark => {
            if (mark.className === 'highlight-match' || mark.className === 'highlight-current') {
                mark.clear();
            }
        });
    }
    delete searchState[index];
    const countEl = document.getElementById(`search-count-${index}`);
    if (countEl) countEl.textContent = '0/0';
}

function performSearch(index) {
    const query = document.getElementById(`search-input-${index}`).value;
    const editor = panels[index].editor;
    
    if (!editor) return;

    clearSearch(index);
    searchState[index] = { matches: [], current: -1 };

    if (!query) return;

    const cursor = editor.getSearchCursor(query);
    while (cursor.findNext()) {
        const from = cursor.from();
        const to = cursor.to();
        editor.markText(from, to, { className: 'highlight-match' });
        searchState[index].matches.push({ from, to });
    }

    const count = searchState[index].matches.length;
    
    if (count > 0) {
        searchState[index].current = 0;
        highlightCurrent(index);
    }
    
    document.getElementById(`search-count-${index}`).textContent = 
        count > 0 ? `${searchState[index].current + 1}/${count}` : '0/0';
}

function highlightCurrent(index) {
    const state = searchState[index];
    if (!state || state.matches.length === 0) return;

    const editor = panels[index].editor;
    
    editor.getAllMarks().forEach(mark => {
        if (mark.className === 'highlight-current') mark.clear();
    });

    const match = state.matches[state.current];
    editor.markText(match.from, match.to, { className: 'highlight-current' });
    editor.scrollIntoView(match.from, 100);

    document.getElementById(`search-count-${index}`).textContent = 
        `${state.current + 1}/${state.matches.length}`;
}

function findNext(index) {
    const state = searchState[index];
    if (!state || state.matches.length === 0) return;
    state.current = (state.current + 1) % state.matches.length;
    highlightCurrent(index);
}

function findPrev(index) {
    const state = searchState[index];
    if (!state || state.matches.length === 0) return;
    state.current = (state.current - 1 + state.matches.length) % state.matches.length;
    highlightCurrent(index);
}

// Export Functions
function downloadMD(index) {
    const panel = panels[index];
    if (!panel.file) return;

    const blob = new Blob([panel.content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = panel.file.split('/').pop();
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

function copyForDocs(index) {
    if (typeof index === 'undefined') index = activePanel;
    
    const panel = panels[index];
    if (!panel.file) {
        showToast('Selecciona un archivo primero');
        return;
    }
    
    let contentElement = document.getElementById('content-' + index);
    if (!contentElement) return;

    const range = document.createRange();
    range.selectNode(contentElement);
    const selection = window.getSelection();
    selection.removeAllRanges();
    selection.addRange(range);
    try {
        document.execCommand('copy');
        showToast('Copiado para Google Docs');
    } catch (err) {
        showToast('Error al copiar');
    }
    selection.removeAllRanges();
}

function exportPDF(index) {
    if (typeof index === 'undefined') index = activePanel;
    
    const panel = panels[index];
    if (!panel.file) {
        showToast('Selecciona un archivo primero');
        return;
    }

    const element = document.getElementById('content-' + index);
    if (!element) return;

    const filename = panel.file.split('/').pop().replace('.md', '.pdf');
    
    const opt = {
        margin: [15, 20, 15, 20],
        filename: filename,
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { scale: 2 },
        jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
    };

    html2pdf().set(opt).from(element).save();
}
