// Utilities & Authentication

function showToast(message, type = 'info') {
    let toast = document.getElementById('toast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'toast';
        toast.className = 'toast';
        document.body.appendChild(toast);
    }
    
    toast.textContent = message;
    toast.className = 'toast show';
    if (type === 'error') toast.style.borderLeftColor = 'var(--danger)';
    else if (type === 'success') toast.style.borderLeftColor = 'var(--success)';
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

async function login() {
    const password = document.getElementById('password-input').value;
    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ password })
        });

        if (response.ok) {
            const data = await response.json();
            authToken = data.token;
            localStorage.setItem('authToken', authToken);
            document.getElementById('login-overlay').style.display = 'none';
            loadFileList();
        } else {
            alert('Contraseña incorrecta');
        }
    } catch (e) {
        alert('Error de conexión');
    }
}

// Session Management
function saveSession() {
    const session = {
        gridSize,
        activePanel,
        panels: panels.map(p => ({
            file: p.file,
            mode: p.mode
        }))
    };
    localStorage.setItem('editorSession', JSON.stringify(session));
}

async function restoreSession() {
    const saved = localStorage.getItem('editorSession');
    if (!saved) return;

    try {
        const session = JSON.parse(saved);
        
        if (session.gridSize) {
            setGrid(session.gridSize);
        }

        if (session.panels && Array.isArray(session.panels)) {
            for (let i = 0; i < session.panels.length; i++) {
                const p = session.panels[i];
                if (p.file) {
                    await loadFileToPanel(p.file, i);
                    if (p.mode) {
                        setPanelMode(i, p.mode);
                    }
                }
            }
        }

        if (typeof session.activePanel === 'number') {
            setActivePanel(session.activePanel);
        }

    } catch (e) {
        console.error('Error restoring session:', e);
    }
}
