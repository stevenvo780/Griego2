// File System Operations

async function loadFileList() {
    try {
        const response = await fetch('/api/files', {
            headers: { 'Authorization': 'Bearer ' + authToken }
        });
        
        if (response.status === 401) {
            document.getElementById('login-overlay').style.display = 'flex';
            localStorage.removeItem('authToken');
            return;
        }
        
        files = await response.json();
        renderFileTree(files);
    } catch (error) {
        console.error('Error loading files:', error);
    }
}

async function loadFileToPanel(path, panelIndex, forceRefresh = false) {
    try {
        const ext = path.split('.').pop().toLowerCase();
        const isMarkdown = ext === 'md' || ext === 'txt';
        const isPDF = ext === 'pdf';
        
        // Handle PDF/Binary View
        if (isPDF) {
             panels[panelIndex] = {
                file: path,
                content: '',
                editor: null,
                mode: 'preview',
                type: 'pdf' // New property
            };
            
            // Allow manual refresh if needed?
            // Just update UI
            renderPanels();
            setActivePanel(panelIndex);
            
            // Inject PDF viewer directly since renderPanels mostly handles MD
            // We need to update renderPanels to handle 'pdf' type or handle it here?
            // renderPanels creates <div>s.
            // initPanelEditor won't run if we don't set it up differently.
            // Let's rely on renderPanels checking panel.type
            
            saveSession();
            return;
        }

        if (!isMarkdown) {
             showToast('Tipo de archivo no soportado para edición');
             return;
        }

        // Standard Markdown/Text Load
        const url = '/api/file?path=' + encodeURIComponent(path) + (forceRefresh ? '&t=' + Date.now() : '');
        
        const response = await fetch(url, {
            headers: { 'Authorization': 'Bearer ' + authToken }
        });
        
        if (response.status === 401) {
            showToast('Sesión expirada');
            return;
        }
        
        const data = await response.json();

        const existingMode = panels[panelIndex].mode || 'preview';

        panels[panelIndex] = {
            file: path,
            content: data.content,
            editor: null,
            mode: existingMode,
            type: 'markdown'
        };

        renderPanels();
        setActivePanel(panelIndex);
        if (forceRefresh) showToast('Contenido recargado');
        saveSession();

    } catch (error) {
        console.error('Error loading file:', error);
        showToast('Error al cargar archivo');
    }
}

function refreshPanel(index) {
    const panel = panels[index];
    if (panel && panel.file) {
            loadFileToPanel(panel.file, index, true);
    }
}

function triggerAutoSave(index) {
    if (saveTimeouts[index]) clearTimeout(saveTimeouts[index]);
    saveTimeouts[index] = setTimeout(() => {
        savePanel(index);
    }, 2000);
}

async function savePanel(index) {
    const panel = panels[index];
    if (!panel.file) return;

    try {
        const response = await fetch('/api/save', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + authToken
            },
            body: JSON.stringify({ path: panel.file, content: panel.content })
        });

        if (response.ok) {
            showToast('Guardado: ' + panel.file.split('/').pop());
        } else {
            showToast('Error: ' + response.statusText);
        }
    } catch (error) {
        showToast('Error al guardar');
    }
}

function saveCurrentPanel() {
    savePanel(activePanel);
}

// Upload Logic
async function handleFileUpload(fileList) {
    if (!authToken) return;
    
    const formData = new FormData();
    for (let i = 0; i < fileList.length; i++) {
        formData.append('files', fileList[i]);
    }

    showToast('Subiendo archivos...', 'info');

    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            headers: { 'Authorization': 'Bearer ' + authToken },
            body: formData
        });

        if (response.ok) {
            const result = await response.json();
            showToast(`Subidos ${result.count} archivos`, 'success');
            loadFileList();
        } else {
            showToast('Error al subir', 'error');
        }
    } catch (e) {
        console.error(e);
        showToast('Error de conexión', 'error');
    }
}
