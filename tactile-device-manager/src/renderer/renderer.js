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

// Device Layout Management
let currentWordMappings = {};
let selectedKey = null;

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    initializeEventListeners();
    initializeTabs();
    refreshSerialPorts();
    initializeDeviceLayout();
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
            updateDeviceStatus(true, false); // Connected but SD status unknown
            appendToConsole(`[INFO] ${result.message}`, 'success');
            
            // Send initial device info request
            setTimeout(() => {
                sendDeviceCommand('GET_INFO');
            }, 1000);
        } else {
            updateConnectionStatus(false);
            updateDeviceStatus(false, false);
            appendToConsole(`[ERROR] ${result.message}`, 'error');
        }
    } catch (error) {
        updateConnectionStatus(false);
        updateDeviceStatus(false, false);
        appendToConsole(`[ERROR] Connection failed: ${error.message}`, 'error');
    }
}

async function disconnectFromDevice() {
    try {
        const result = await ipcRenderer.invoke('disconnect-device');
        currentDevice = null;
        fsClient = null;
        updateConnectionStatus(false);
        updateDeviceStatus(false, false);
        appendToConsole('[INFO] Disconnected from device', 'info');
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
        
        if (result.success && result.path) {
            currentSdPath = result.path;
            document.getElementById('sdCardPath').textContent = result.path;
            updateDeviceStatus(currentDevice !== null, true); // Update SD status
            appendToConsole(`[INFO] SD directory selected: ${result.path}`, 'info');
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

// Device Layout Management Functions
function initializeDeviceLayout() {
    // Add click handlers for device buttons
    document.querySelectorAll('.device-button').forEach(button => {
        button.addEventListener('click', () => {
            const key = button.dataset.key;
            selectDeviceButton(key);
        });
    });

    // Mapping panel controls
    const closeMappingPanel = document.getElementById('closeMappingPanel');
    if (closeMappingPanel) {
        closeMappingPanel.addEventListener('click', () => closeMappingPanelFunc());
    }
    
    const addHumanWord = document.getElementById('addHumanWord');
    if (addHumanWord) {
        addHumanWord.addEventListener('click', () => addWord('human'));
    }
    
    const addGeneratedWord = document.getElementById('addGeneratedWord');
    if (addGeneratedWord) {
        addGeneratedWord.addEventListener('click', () => addWord('generated'));
    }
    
    const saveMappings = document.getElementById('saveMappings');
    if (saveMappings) {
        saveMappings.addEventListener('click', saveMappingsFunc);
    }
    
    const testAudio = document.getElementById('testAudio');
    if (testAudio) {
        testAudio.addEventListener('click', testSelectedAudio);
    }
    
    const clearAllMappings = document.getElementById('clearAllMappings');
    if (clearAllMappings) {
        clearAllMappings.addEventListener('click', clearAllMappingsFunc);
    }

    // Enter key handlers for input fields
    const newHumanWord = document.getElementById('newHumanWord');
    if (newHumanWord) {
        newHumanWord.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') addWord('human');
        });
    }
    
    const newGeneratedWord = document.getElementById('newGeneratedWord');
    if (newGeneratedWord) {
        newGeneratedWord.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') addWord('generated');
        });
    }

    // Load initial mappings
    loadWordMappings();
}

function selectDeviceButton(key) {
    // Update visual selection
    document.querySelectorAll('.device-button').forEach(btn => {
        btn.classList.remove('selected');
    });
    const selectedButton = document.querySelector(`[data-key="${key}"]`);
    if (selectedButton) {
        selectedButton.classList.add('selected');
    }

    selectedKey = key;
    const selectedKeySpan = document.getElementById('selectedKey');
    if (selectedKeySpan) {
        selectedKeySpan.textContent = key;
    }
    
    // Show mapping panel
    const mappingPanel = document.getElementById('mappingPanel');
    if (mappingPanel) {
        mappingPanel.style.display = 'block';
    }
    
    // Load mappings for this key
    loadMappingsForKey(key);
}

function loadMappingsForKey(key) {
    const mappings = currentWordMappings[key] || { human: [], generated: [] };
    
    // Update human word list
    const humanList = document.getElementById('humanWordList');
    if (humanList) {
        if (mappings.human.length === 0) {
            humanList.innerHTML = '<div class="no-words">No human recordings</div>';
        } else {
            humanList.innerHTML = mappings.human.map(word => 
                `<div class="word-item">
                    <span class="word-text">${word}</span>
                    <div class="word-actions">
                        <button class="btn btn-sm btn-secondary" onclick="playWord('${key}', '${word}', 'human')">🔊</button>
                        <button class="btn btn-sm btn-danger" onclick="removeWord('${key}', '${word}', 'human')">✕</button>
                    </div>
                </div>`
            ).join('');
        }
    }
    
    // Update generated word list
    const generatedList = document.getElementById('generatedWordList');
    if (generatedList) {
        if (mappings.generated.length === 0) {
            generatedList.innerHTML = '<div class="no-words">No generated audio</div>';
        } else {
            generatedList.innerHTML = mappings.generated.map(word => 
                `<div class="word-item">
                    <span class="word-text">${word}</span>
                    <div class="word-actions">
                        <button class="btn btn-sm btn-secondary" onclick="playWord('${key}', '${word}', 'generated')">🔊</button>
                        <button class="btn btn-sm btn-danger" onclick="removeWord('${key}', '${word}', 'generated')">✕</button>
                    </div>
                </div>`
            ).join('');
        }
    }
}

function addWord(type) {
    if (!selectedKey) return;
    
    const inputId = type === 'human' ? 'newHumanWord' : 'newGeneratedWord';
    const input = document.getElementById(inputId);
    if (!input) return;
    
    const word = input.value.trim();
    if (!word) return;
    
    if (!currentWordMappings[selectedKey]) {
        currentWordMappings[selectedKey] = { human: [], generated: [] };
    }
    
    if (!currentWordMappings[selectedKey][type].includes(word)) {
        currentWordMappings[selectedKey][type].push(word);
        input.value = '';
        loadMappingsForKey(selectedKey);
        updateAudioIndicators();
        appendToConsole(`Added ${type} word "${word}" to key ${selectedKey}`, 'info');
    } else {
        appendToConsole(`Word "${word}" already exists for key ${selectedKey}`, 'warning');
    }
}

function removeWord(key, word, type) {
    if (currentWordMappings[key] && currentWordMappings[key][type]) {
        const index = currentWordMappings[key][type].indexOf(word);
        if (index > -1) {
            currentWordMappings[key][type].splice(index, 1);
            loadMappingsForKey(key);
            updateAudioIndicators();
            appendToConsole(`Removed ${type} word "${word}" from key ${key}`, 'info');
        }
    }
}

function playWord(key, word, type) {
    appendToConsole(`Playing ${type} audio: "${word}" for key ${key}`, 'info');
    // Send command to device to play specific audio
    if (currentDevice) {
        sendDeviceCommand(`PLAY:${key}:${word}:${type}`);
    }
}

function updateAudioIndicators() {
    document.querySelectorAll('.device-button').forEach(button => {
        const key = button.dataset.key;
        const mappings = currentWordMappings[key] || { human: [], generated: [] };
        
        const humanIndicator = button.querySelector('.human-indicator');
        const generatedIndicator = button.querySelector('.generated-indicator');
        
        // Update human indicator
        if (humanIndicator) {
            if (mappings.human.length > 0) {
                humanIndicator.textContent = mappings.human.length;
                humanIndicator.style.display = 'flex';
            } else {
                humanIndicator.style.display = 'none';
            }
        }
        
        // Update generated indicator
        if (generatedIndicator) {
            if (mappings.generated.length > 0) {
                generatedIndicator.textContent = mappings.generated.length;
                generatedIndicator.style.display = 'flex';
            } else {
                generatedIndicator.style.display = 'none';
            }
        }
    });
    
    // Update total counts
    let totalHuman = 0;
    let totalGenerated = 0;
    
    Object.values(currentWordMappings).forEach(mapping => {
        totalHuman += mapping.human ? mapping.human.length : 0;
        totalGenerated += mapping.generated ? mapping.generated.length : 0;
    });
    
    const humanAudioCount = document.getElementById('humanAudioCount');
    if (humanAudioCount) {
        humanAudioCount.textContent = totalHuman;
    }
    
    const generatedAudioCount = document.getElementById('generatedAudioCount');
    if (generatedAudioCount) {
        generatedAudioCount.textContent = totalGenerated;
    }
}

function closeMappingPanelFunc() {
    const mappingPanel = document.getElementById('mappingPanel');
    if (mappingPanel) {
        mappingPanel.style.display = 'none';
    }
    
    document.querySelectorAll('.device-button').forEach(btn => {
        btn.classList.remove('selected');
    });
    selectedKey = null;
}

function loadWordMappings() {
    // Load from local storage
    const savedMappings = localStorage.getItem('wordMappings');
    if (savedMappings) {
        try {
            currentWordMappings = JSON.parse(savedMappings);
            updateAudioIndicators();
            appendToConsole('Loaded word mappings from local storage', 'info');
        } catch (e) {
            appendToConsole('Error loading word mappings: ' + e.message, 'error');
        }
    }
}

function saveMappingsFunc() {
    // Save to local storage
    localStorage.setItem('wordMappings', JSON.stringify(currentWordMappings));
    appendToConsole('Word mappings saved locally', 'success');
    
    // Generate playlist files if SD path is available
    if (currentSdPath) {
        generatePlaylistFiles();
    }
}

function generatePlaylistFiles() {
    if (!currentSdPath) {
        appendToConsole('No SD card path selected. Cannot generate playlist files.', 'warning');
        return;
    }
    
    appendToConsole('Generating playlist files from word mappings...', 'info');
    
    // Generate human and generated playlists
    const humanPlaylist = [];
    const generatedPlaylist = [];
    
    Object.entries(currentWordMappings).forEach(([key, mappings]) => {
        if (mappings.human) {
            mappings.human.forEach(word => {
                humanPlaylist.push(`# ${key}: ${word}`);
                humanPlaylist.push(`human/${key}_${word.replace(/\s+/g, '_')}.mp3`);
            });
        }
        
        if (mappings.generated) {
            mappings.generated.forEach(word => {
                generatedPlaylist.push(`# ${key}: ${word}`);
                generatedPlaylist.push(`generated/${key}_${word.replace(/\s+/g, '_')}.mp3`);
            });
        }
    });
    
    // Write playlist files
    const humanContent = humanPlaylist.join('\n');
    const generatedContent = generatedPlaylist.join('\n');
    
    Promise.all([
        ipcRenderer.invoke('write-file', path.join(currentSdPath, 'human.m3u'), humanContent),
        ipcRenderer.invoke('write-file', path.join(currentSdPath, 'generated.m3u'), generatedContent)
    ]).then(results => {
        if (results[0].success && results[1].success) {
            appendToConsole('Generated playlist files successfully', 'success');
        } else {
            appendToConsole('Error generating some playlist files', 'error');
        }
    }).catch(err => {
        appendToConsole('Error generating playlist files: ' + err.message, 'error');
    });
}

function testSelectedAudio() {
    if (!selectedKey) return;
    
    const mappings = currentWordMappings[selectedKey];
    if (!mappings) return;
    
    appendToConsole(`Testing audio for key ${selectedKey}`, 'info');
    
    // Send test command to device
    if (currentDevice) {
        sendDeviceCommand(`TEST:${selectedKey}`);
    }
}

function clearAllMappingsFunc() {
    if (confirm('Are you sure you want to clear all word mappings? This cannot be undone.')) {
        currentWordMappings = {};
        updateAudioIndicators();
        if (selectedKey) {
            loadMappingsForKey(selectedKey);
        }
        localStorage.removeItem('wordMappings');
        appendToConsole('All word mappings cleared', 'info');
    }
}

// Update device status indicators
function updateDeviceStatus(connected, sdCardPresent) {
    const deviceDot = document.getElementById('deviceStatusDot');
    const deviceText = document.getElementById('deviceStatusText');
    const sdDot = document.getElementById('sdStatusDot');
    const sdText = document.getElementById('sdStatusText');
    
    if (deviceDot && deviceText) {
        if (connected) {
            deviceDot.classList.add('connected');
            deviceText.textContent = 'Connected';
        } else {
            deviceDot.classList.remove('connected');
            deviceText.textContent = 'Disconnected';
        }
    }
    
    if (sdDot && sdText) {
        if (sdCardPresent) {
            sdDot.classList.add('connected');
            sdText.textContent = 'SD Card Ready';
        } else {
            sdDot.classList.remove('connected');
            sdText.textContent = 'No SD Card';
        }
    }
}

// Initialize all event listeners on load
document.addEventListener('DOMContentLoaded', () => {
    initializeAllEventListeners();
});

console.log('Tactile Device Manager UI loaded');
