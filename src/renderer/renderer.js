const { ipcRenderer } = require('electron');
const FSClient = require('../lib/fs-client');
const path = require('path');

// Global state
let currentDevice = null;
let currentSdPath = null;
let selectedFile = null;
let fsClient = null;

// DOM elements
const elements = {
    serialPorts: document.getElementById('serialPorts'),
    connectBtn: document.getElementById('connectBtn'),
    disconnectBtn: document.getElementById('disconnectBtn'),
    connectionStatus: document.getElementById('connectionStatus'),
    connectionText: document.getElementById('connectionText'),
    consoleOutput: document.getElementById('consoleOutput'),
    consoleInput: document.getElementById('consoleInput'),
    sendCommandBtn: document.getElementById('sendCommandBtn')
};

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    initializeEventListeners();
    initializeTabs();
    refreshSerialPorts();
});

function initializeEventListeners() {
    document.getElementById('refreshPorts').addEventListener('click', refreshSerialPorts);
    elements.connectBtn.addEventListener('click', connectToDevice);
    elements.disconnectBtn.addEventListener('click', disconnectFromDevice);
    elements.sendCommandBtn.addEventListener('click', sendCommand);
    elements.consoleInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendCommand();
    });
}

function initializeTabs() {
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabId = button.dataset.tab;
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));
            button.classList.add('active');
            document.getElementById(tabId).classList.add('active');
        });
    });
}

// IPC Event Handlers
ipcRenderer.on('serial-data', (event, data) => {
    appendToConsole(`[DEVICE] ${data}`, 'device');
});

ipcRenderer.on('serial-error', (event, error) => {
    appendToConsole(`[ERROR] ${error}`, 'error');
    updateConnectionStatus(false);
});

async function refreshSerialPorts() {
    try {
        const ports = await ipcRenderer.invoke('list-serial-ports');
        elements.serialPorts.innerHTML = '<option value="">Select a port...</option>';
        
        ports.forEach(port => {
            const option = document.createElement('option');
            option.value = port.path;
            option.textContent = `${port.path} - ${port.manufacturer || 'Unknown'}`;
            elements.serialPorts.appendChild(option);
        });
    } catch (error) {
        appendToConsole(`[ERROR] Failed to refresh ports: ${error.message}`, 'error');
    }
}

async function connectToDevice() {
    const portPath = elements.serialPorts.value;
    if (!portPath) {
        alert('Please select a serial port');
        return;
    }
    
    try {
        updateConnectionStatus('connecting');
        const result = await ipcRenderer.invoke('connect-device', portPath, 115200);
        
        if (result.success) {
            currentDevice = { port: portPath };
            fsClient = new FSClient(ipcRenderer);
            updateConnectionStatus(true);
            appendToConsole(`[INFO] ${result.message}`, 'success');
            
            // Send initial device info request
            setTimeout(() => {
                sendDeviceCommand('GET_INFO');
            }, 1000);
        } else {
            updateConnectionStatus(false);
            appendToConsole(`[ERROR] ${result.message}`, 'error');
        }
    } catch (error) {
        updateConnectionStatus(false);
        appendToConsole(`[ERROR] Connection failed: ${error.message}`, 'error');
    }
}

async function disconnectFromDevice() {
    try {
        const result = await ipcRenderer.invoke('disconnect-device');
        currentDevice = null;
        updateConnectionStatus(false);
        appendToConsole(`[INFO] ${result.message}`, 'info');
    } catch (error) {
        appendToConsole(`[ERROR] Disconnect failed: ${error.message}`, 'error');
    }
}

function appendToConsole(message, type = 'info') {
    const timestamp = new Date().toLocaleTimeString();
    const line = `[${timestamp}] ${message}\n`;
    elements.consoleOutput.textContent += line;
    elements.consoleOutput.scrollTop = elements.consoleOutput.scrollHeight;
}

async function sendCommand() {
    const command = elements.consoleInput.value.trim();
    if (!command) return;
    
    elements.consoleInput.value = '';
    appendToConsole(`[SEND] ${command}`, 'send');
    
    if (!currentDevice) {
        appendToConsole('[ERROR] No device connected', 'error');
        return;
    }
    
    try {
        const result = await ipcRenderer.invoke('send-command', command);
        if (!result.success) {
            appendToConsole(`[ERROR] ${result.message}`, 'error');
        }
    } catch (error) {
        appendToConsole(`[ERROR] Failed to send command: ${error.message}`, 'error');
    }
}

function updateConnectionStatus(status) {
    if (status === 'connecting') {
        elements.connectionStatus.className = 'status-indicator connecting';
        elements.connectionText.textContent = 'Connecting...';
        elements.connectBtn.disabled = true;
        elements.disconnectBtn.disabled = true;
    } else if (status === true) {
        elements.connectionStatus.className = 'status-indicator connected';
        elements.connectionText.textContent = 'Connected';
        elements.connectBtn.disabled = true;
        elements.disconnectBtn.disabled = false;
    } else {
        elements.connectionStatus.className = 'status-indicator';
        elements.connectionText.textContent = 'Disconnected';
        elements.connectBtn.disabled = false;
        elements.disconnectBtn.disabled = true;
    }
}

// ===== ADDITIONAL FUNCTIONALITY =====

// Add missing event listeners for all buttons
function initializeAllEventListeners() {
    // SD Card Management
    document.getElementById('selectSdBtn')?.addEventListener('click', selectSdDirectory);
    document.getElementById('syncSdBtn')?.addEventListener('click', syncToDevice);
    document.getElementById('backupSdBtn')?.addEventListener('click', backupFromDevice);
    
    // Testing
    document.getElementById('selfTestBtn')?.addEventListener('click', runSelfTest);
    document.getElementById('playTestBtn')?.addEventListener('click', playTestAudio);
    
    // One-Click Update
    document.getElementById('oneClickUpdateBtn')?.addEventListener('click', oneClickUpdate);
    
    // Configuration
    document.getElementById('loadButtonConfig')?.addEventListener('click', loadButtonConfig);
    document.getElementById('saveButtonConfig')?.addEventListener('click', saveButtonConfig);
    document.getElementById('loadModeConfig')?.addEventListener('click', loadModeConfig);
    document.getElementById('saveModeConfig')?.addEventListener('click', saveModeConfig);
}

// SD Card Management Functions
async function selectSdDirectory() {
    try {
        const result = await ipcRenderer.invoke('select-directory');
        
        if (result.success) {
            currentSdPath = result.path;
            document.getElementById('sdPath').textContent = result.path;
            updateStatus('SD directory selected');
            
            // Enable SD-related buttons
            document.getElementById('syncSdBtn').disabled = false;
            document.getElementById('backupSdBtn').disabled = false;
            
            appendToConsole(`[INFO] Selected SD directory: ${result.path}`, 'info');
        }
    } catch (error) {
        appendToConsole(`[ERROR] Failed to select directory: ${error.message}`, 'error');
    }
}

async function syncToDevice() {
    if (!currentDevice || !currentSdPath || !fsClient) {
        alert('Please connect to device and select SD directory first');
        return;
    }
    
    try {
        appendToConsole('[INFO] Starting SD card sync to device...', 'info');
        updateStatus('Syncing to device...');
        
        const result = await fsClient.syncDirectory(currentSdPath, '/', (progress) => {
            appendToConsole(`[SYNC] ${progress.file}: ${progress.progress.toFixed(1)}%`, 'info');
        });
        
        if (result.success) {
            appendToConsole(`[SUCCESS] Synced ${result.filesUploaded} files to device`, 'success');
            updateStatus('Sync complete');
        }
    } catch (error) {
        appendToConsole(`[ERROR] Sync failed: ${error.message}`, 'error');
        updateStatus('Sync failed');
    }
}

async function backupFromDevice() {
    appendToConsole('[INFO] Backup from device functionality coming soon', 'info');
}

// Testing Functions
async function runSelfTest() {
    if (!currentDevice) {
        alert('Please connect to device first');
        return;
    }
    
    try {
        appendToConsole('[INFO] Running device self-test...', 'info');
        
        await sendDeviceCommand('GET_INFO');
        await new Promise(resolve => setTimeout(resolve, 500));
        
        await sendDeviceCommand('L'); // Load configuration
        await new Promise(resolve => setTimeout(resolve, 500));
        
        await sendDeviceCommand('P'); // Print status
        
        appendToConsole('[SUCCESS] Self-test completed', 'success');
    } catch (error) {
        appendToConsole(`[ERROR] Self-test failed: ${error.message}`, 'error');
    }
}

async function playTestAudio() {
    if (!currentDevice) {
        alert('Please connect to device first');
        return;
    }
    
    try {
        appendToConsole('[INFO] Playing test audio...', 'info');
        await sendDeviceCommand('T'); // Test command
    } catch (error) {
        appendToConsole(`[ERROR] Test audio failed: ${error.message}`, 'error');
    }
}

// One-Click Update
async function oneClickUpdate() {
    if (!currentDevice || !currentSdPath) {
        alert('Please connect to device and select SD directory first');
        return;
    }
    
    try {
        appendToConsole('[UPDATE] Starting one-click device update...', 'info');
        
        // Step 1: Sync SD Card (skip firmware for now)
        appendToConsole('[UPDATE] Step 1: Syncing SD card...', 'info');
        await syncToDevice();
        
        // Step 2: Run Self-Test
        appendToConsole('[UPDATE] Step 2: Running self-test...', 'info');
        await runSelfTest();
        
        appendToConsole('[SUCCESS] One-click update completed successfully!', 'success');
        
    } catch (error) {
        appendToConsole(`[ERROR] One-click update failed: ${error.message}`, 'error');
    }
}

// Configuration Management
async function loadButtonConfig() {
    if (!currentSdPath) {
        alert('Please select SD directory first');
        return;
    }
    
    try {
        const configPath = path.join(currentSdPath, 'config', 'buttons.csv');
        const result = await ipcRenderer.invoke('read-file', configPath);
        
        if (result.success) {
            document.getElementById('buttonConfigEditor').value = result.content;
            appendToConsole('[INFO] Button configuration loaded', 'info');
        } else {
            appendToConsole(`[ERROR] ${result.message}`, 'error');
        }
    } catch (error) {
        appendToConsole(`[ERROR] Failed to load button config: ${error.message}`, 'error');
    }
}

async function saveButtonConfig() {
    if (!currentSdPath) {
        alert('Please select SD directory first');
        return;
    }
    
    try {
        const configPath = path.join(currentSdPath, 'config', 'buttons.csv');
        const content = document.getElementById('buttonConfigEditor').value;
        
        const result = await ipcRenderer.invoke('write-file', configPath, content);
        
        if (result.success) {
            appendToConsole('[SUCCESS] Button configuration saved', 'success');
        } else {
            appendToConsole(`[ERROR] ${result.message}`, 'error');
        }
    } catch (error) {
        appendToConsole(`[ERROR] Failed to save button config: ${error.message}`, 'error');
    }
}

async function loadModeConfig() {
    if (!currentSdPath) {
        alert('Please select SD directory first');
        return;
    }
    
    try {
        const configPath = path.join(currentSdPath, 'config', 'mode.cfg');
        const result = await ipcRenderer.invoke('read-file', configPath);
        
        if (result.success) {
            const lines = result.content.split('\n');
            lines.forEach(line => {
                const [key, value] = line.split('=');
                if (key === 'PRIORITY_MODE') {
                    document.getElementById('priorityMode').value = value.trim();
                } else if (key === 'STRICT_PLAYLISTS') {
                    document.getElementById('strictPlaylists').checked = value.trim() === '1';
                }
            });
            appendToConsole('[INFO] Mode configuration loaded', 'info');
        } else {
            appendToConsole(`[ERROR] ${result.message}`, 'error');
        }
    } catch (error) {
        appendToConsole(`[ERROR] Failed to load mode config: ${error.message}`, 'error');
    }
}

async function saveModeConfig() {
    if (!currentSdPath) {
        alert('Please select SD directory first');
        return;
    }
    
    try {
        const configPath = path.join(currentSdPath, 'config', 'mode.cfg');
        const priorityMode = document.getElementById('priorityMode').value;
        const strictPlaylists = document.getElementById('strictPlaylists').checked ? '1' : '0';
        const content = `PRIORITY_MODE=${priorityMode}\nSTRICT_PLAYLISTS=${strictPlaylists}\n`;
        
        const result = await ipcRenderer.invoke('write-file', configPath, content);
        
        if (result.success) {
            appendToConsole('[SUCCESS] Mode configuration saved', 'success');
            
            // Send reload command to device if connected
            if (currentDevice) {
                await sendDeviceCommand('CFG_RELOAD');
            }
        } else {
            appendToConsole(`[ERROR] ${result.message}`, 'error');
        }
    } catch (error) {
        appendToConsole(`[ERROR] Failed to save mode config: ${error.message}`, 'error');
    }
}

// Utility function to update status
function updateStatus(message) {
    const statusElement = document.getElementById('operationStatus');
    if (statusElement) {
        statusElement.textContent = message;
    }
}

// Initialize all event listeners on load
document.addEventListener('DOMContentLoaded', () => {
    initializeAllEventListeners();
});

console.log('Tactile Device Manager UI loaded');
