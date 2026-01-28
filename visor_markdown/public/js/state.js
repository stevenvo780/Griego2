// Global State
let panels = [
    { file: null, content: '', editor: null, mode: 'preview' }
];
let activePanel = 0;
let gridSize = 1;
let files = [];
let authToken = localStorage.getItem('authToken');
let saveTimeouts = {};
let panelForDownload = null;
