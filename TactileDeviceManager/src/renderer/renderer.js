const { ipcRenderer } = require('electron');

class TactileDeviceUI {
    constructor() {
        this.selectedButton = null;
        this.manifest = null;
        this.buttonConfig = [];
        this.systemStatus = null;
        
        this.initializeEventListeners();
        this.updateSystemStatus();
        
        // Auto-refresh status every 5 seconds
        setInterval(() => this.updateSystemStatus(), 5000);
    }

    initializeEventListeners() {
        // Header buttons
        document.getElementById('connect-btn').addEventListener('click', () => this.connectDevice());
        document.getElementById('select-sd-btn').addEventListener('click', () => this.selectSDCard());
        
        // Priority mode
        document.getElementById('priority-mode').addEventListener('change', (e) => this.changePriorityMode(e.target.value));
        
        // Device buttons
        document.querySelectorAll('.device-button').forEach(button => {
            button.addEventListener('click', () => this.selectButton(button));
        });
        
        // Configuration buttons
        document.getElementById('add-human-audio').addEventListener('click', () => this.addAudioFile('human'));
        document.getElementById('add-generated-audio').addEventListener('click', () => this.addAudioFile('generated'));
        document.getElementById('save-button-config').addEventListener('click', () => this.saveButtonConfiguration());
        document.getElementById('test-button').addEventListener('click', () => this.testSelectedButton());
        
        // Console
        document.getElementById('clear-console').addEventListener('click', () => this.clearConsole());
        document.getElementById('send-command-btn').addEventListener('click', () => this.sendCommand());
        document.getElementById('command-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendCommand();
        });
        
        // Modal
        document.querySelector('.modal-close').addEventListener('click', () => this.closeModal());
        document.getElementById('audio-modal').addEventListener('click', (e) => {
            if (e.target.id === 'audio-modal') this.closeModal();
        });
        
        // IPC listeners
        ipcRenderer.on('sd-card-selected', (event, path) => this.onSDCardSelected(path));
        ipcRenderer.on('device-connected', (event, port) => this.onDeviceConnected(port));
        ipcRenderer.on('device-message', (event, message) => this.onDeviceMessage(message));
    }

    async selectSDCard() {
        try {
            const sdPath = await ipcRenderer.invoke('select-sd-card');
            if (sdPath) {
                await this.loadConfiguration();
                this.updateSystemStatus();
                this.addConsoleMessage('SD card selected: ' + sdPath, 'response');
            }
        } catch (error) {
            this.addConsoleMessage('Failed to select SD card: ' + error.message, 'error');
        }
    }

    async connectDevice() {
        try {
            const ports = await ipcRenderer.invoke('scan-serial-ports');
            
            if (ports.length === 0) {
                this.addConsoleMessage('No Arduino devices found. Check USB connection.', 'error');
                return;
            }
            
            // For now, connect to the first available port
            // In a real app, you'd show a selection dialog
            const selectedPort = ports[0];
            await ipcRenderer.invoke('connect-device', selectedPort.path);
            
        } catch (error) {
            this.addConsoleMessage('Failed to connect device: ' + error.message, 'error');
        }
    }

    async loadConfiguration() {
        try {
            // Load manifest
            this.manifest = await ipcRenderer.invoke('load-manifest');
            if (this.manifest) {
                document.getElementById('priority-mode').value = this.manifest.priority || 'HUMAN_FIRST';
            }
            
            // Load button configuration
            this.buttonConfig = await ipcRenderer.invoke('get-button-config');
            
            // Update button mappings and audio counts
            await this.updateButtonMappings();
            await this.updateAudioCounts();
            
        } catch (error) {
            this.addConsoleMessage('Failed to load configuration: ' + error.message, 'error');
        }
    }

    async updateButtonMappings() {
        // Clear existing mappings
        document.querySelectorAll('.device-button').forEach(button => {
            button.classList.remove('has-audio', 'has-human', 'has-generated');
        });
        
        // Apply button configuration
        this.buttonConfig.forEach(mapping => {
            const button = document.querySelector(`[data-input="${mapping.input}"]`);
            if (button) {
                button.setAttribute('data-key', mapping.key);
                button.querySelector('.button-label').textContent = mapping.key;
            }
        });
    }

    async updateAudioCounts() {
        const buttons = document.querySelectorAll('.device-button');
        
        for (const button of buttons) {
            const key = button.getAttribute('data-key');
            if (!key) continue;
            
            try {
                const playlists = await ipcRenderer.invoke('get-playlists', key);
                const humanCount = playlists.human.length;
                const generatedCount = playlists.generated.length;
                
                // Update count display
                button.querySelector('.human-count').textContent = humanCount;
                button.querySelector('.generated-count').textContent = generatedCount;
                
                // Update visual indicators
                if (humanCount > 0 || generatedCount > 0) {
                    button.classList.add('has-audio');
                }
                if (humanCount > 0) {
                    button.classList.add('has-human');
                }
                if (generatedCount > 0) {
                    button.classList.add('has-generated');
                }
                
            } catch (error) {
                console.error('Failed to load playlists for', key, error);
            }
        }
    }

    selectButton(buttonElement) {
        // Remove previous selection
        document.querySelectorAll('.device-button').forEach(btn => {
            btn.classList.remove('selected');
        });
        
        // Select new button
        buttonElement.classList.add('selected');
        this.selectedButton = buttonElement;
        
        // Update configuration panel
        this.showButtonConfiguration();
    }

    async showButtonConfiguration() {
        if (!this.selectedButton) return;
        
        const key = this.selectedButton.getAttribute('data-key');
        const input = this.selectedButton.getAttribute('data-input');
        
        // Show configuration panel
        document.getElementById('button-config').style.display = 'block';
        document.getElementById('selected-button-text').textContent = `Configuring: ${key || 'Unnamed Button'}`;
        
        // Populate form
        document.getElementById('button-input').value = input || '';
        document.getElementById('button-key').value = key || '';
        
        // Load audio lists
        if (key) {
            await this.loadAudioLists(key);
        }
    }

    async loadAudioLists(key) {
        try {
            const playlists = await ipcRenderer.invoke('get-playlists', key);
            
            // Update human audio list
            this.updateAudioList('human-audio-list', playlists.human, 'human');
            
            // Update generated audio list
            this.updateAudioList('generated-audio-list', playlists.generated, 'generated');
            
        } catch (error) {
            this.addConsoleMessage('Failed to load audio lists: ' + error.message, 'error');
        }
    }

    updateAudioList(containerId, tracks, type) {
        const container = document.getElementById(containerId);
        container.innerHTML = '';
        
        if (tracks.length === 0) {
            container.innerHTML = '<div class="audio-item"><div class="audio-info">No audio files</div></div>';
            return;
        }
        
        tracks.forEach((track, index) => {
            const filename = track.split('/').pop();
            const audioItem = document.createElement('div');
            audioItem.className = 'audio-item';
            audioItem.innerHTML = `
                <div class="audio-info">
                    <div class="audio-filename">${filename}</div>
                    <div class="audio-path">${track}</div>
                </div>
                <div class="audio-actions">
                    <button class="play-btn" onclick="ui.previewAudio('${track}', '${type}')">
                        <i class="fas fa-play"></i>
                    </button>
                    <button class="remove-btn" onclick="ui.removeAudioFile('${track}', '${type}')">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            `;
            container.appendChild(audioItem);
        });
    }

    async addAudioFile(type) {
        if (!this.selectedButton) {
            this.addConsoleMessage('Please select a button first', 'error');
            return;
        }
        
        const key = this.selectedButton.getAttribute('data-key');
        if (!key) {
            this.addConsoleMessage('Button must have a key assigned', 'error');
            return;
        }
        
        try {
            const filePath = await ipcRenderer.invoke('add-audio-file', key, type);
            if (filePath) {
                this.addConsoleMessage(`Added ${type} audio file: ${filePath}`, 'response');
                await this.loadAudioLists(key);
                await this.updateAudioCounts();
            }
        } catch (error) {
            this.addConsoleMessage('Failed to add audio file: ' + error.message, 'error');
        }
    }

    async removeAudioFile(filePath, type) {
        if (!confirm('Are you sure you want to remove this audio file?')) {
            return;
        }
        
        try {
            await ipcRenderer.invoke('remove-audio-file', filePath);
            this.addConsoleMessage(`Removed audio file: ${filePath}`, 'response');
            
            // Reload audio lists
            const key = this.selectedButton.getAttribute('data-key');
            if (key) {
                await this.loadAudioLists(key);
                await this.updateAudioCounts();
            }
        } catch (error) {
            this.addConsoleMessage('Failed to remove audio file: ' + error.message, 'error');
        }
    }

    previewAudio(filePath, type) {
        const modal = document.getElementById('audio-modal');
        const audio = document.getElementById('audio-preview');
        const filename = document.getElementById('audio-filename');
        const audioType = document.getElementById('audio-type');
        
        // Set audio source (this would need to be adapted for actual file paths)
        audio.src = filePath;
        filename.textContent = filePath.split('/').pop();
        audioType.textContent = type.charAt(0).toUpperCase() + type.slice(1);
        
        modal.classList.add('show');
    }

    closeModal() {
        const modal = document.getElementById('audio-modal');
        const audio = document.getElementById('audio-preview');
        
        modal.classList.remove('show');
        audio.pause();
        audio.src = '';
    }

    async saveButtonConfiguration() {
        if (!this.selectedButton) return;
        
        const input = document.getElementById('button-input').value.trim();
        const key = document.getElementById('button-key').value.trim();
        
        if (!input || !key) {
            this.addConsoleMessage('Both input and key are required', 'error');
            return;
        }
        
        try {
            // Update button configuration
            const existingIndex = this.buttonConfig.findIndex(config => config.input === input);
            if (existingIndex >= 0) {
                this.buttonConfig[existingIndex].key = key;
            } else {
                this.buttonConfig.push({ input, key });
            }
            
            // Save to SD card
            await ipcRenderer.invoke('save-button-config', this.buttonConfig);
            
            // Update UI
            this.selectedButton.setAttribute('data-key', key);
            this.selectedButton.setAttribute('data-input', input);
            this.selectedButton.querySelector('.button-label').textContent = key;
            
            this.addConsoleMessage(`Saved configuration: ${input} → ${key}`, 'response');
            
        } catch (error) {
            this.addConsoleMessage('Failed to save configuration: ' + error.message, 'error');
        }
    }

    async testSelectedButton() {
        if (!this.selectedButton) {
            this.addConsoleMessage('Please select a button first', 'error');
            return;
        }
        
        const key = this.selectedButton.getAttribute('data-key');
        if (!key) {
            this.addConsoleMessage('Button must have a key assigned', 'error');
            return;
        }
        
        try {
            // Add visual feedback
            this.selectedButton.classList.add('testing');
            setTimeout(() => {
                this.selectedButton.classList.remove('testing');
            }, 2000);
            
            // Send test command to device
            await ipcRenderer.invoke('send-command', `T${key}`);
            this.addConsoleMessage(`Testing button: ${key}`, 'command');
            
        } catch (error) {
            this.addConsoleMessage('Failed to test button: ' + error.message, 'error');
            this.selectedButton.classList.remove('testing');
        }
    }

    async changePriorityMode(mode) {
        try {
            if (this.manifest) {
                this.manifest.priority = mode;
                await ipcRenderer.invoke('save-manifest', this.manifest);
            }
            
            // Send command to device
            await ipcRenderer.invoke('send-command', 'M');
            this.addConsoleMessage(`Priority mode changed to: ${mode}`, 'command');
            
        } catch (error) {
            this.addConsoleMessage('Failed to change priority mode: ' + error.message, 'error');
        }
    }

    async sendCommand() {
        const input = document.getElementById('command-input');
        const command = input.value.trim();
        
        if (!command) return;
        
        try {
            await ipcRenderer.invoke('send-command', command);
            this.addConsoleMessage(`> ${command}`, 'command');
            input.value = '';
        } catch (error) {
            this.addConsoleMessage('Failed to send command: ' + error.message, 'error');
        }
    }

    async updateSystemStatus() {
        try {
            this.systemStatus = await ipcRenderer.invoke('get-system-status');
            
            // Update header status indicators
            const sdStatus = document.getElementById('sd-status');
            const deviceStatus = document.getElementById('device-status');
            
            if (this.systemStatus.sdCard) {
                sdStatus.classList.add('connected');
                sdStatus.classList.remove('disconnected');
                document.getElementById('sd-status-text').textContent = 'Connected';
            } else {
                sdStatus.classList.add('disconnected');
                sdStatus.classList.remove('connected');
                document.getElementById('sd-status-text').textContent = 'Not Connected';
            }
            
            if (this.systemStatus.device) {
                deviceStatus.classList.add('connected');
                deviceStatus.classList.remove('disconnected');
                document.getElementById('device-status-text').textContent = 'Connected';
            } else {
                deviceStatus.classList.add('disconnected');
                deviceStatus.classList.remove('connected');
                document.getElementById('device-status-text').textContent = 'Not Connected';
            }
            
            // Update status cards
            document.getElementById('sd-card-status').textContent = 
                this.systemStatus.sdCard ? 'Connected' : 'Not Connected';
            document.getElementById('device-connection-status').textContent = 
                this.systemStatus.device ? 'Connected' : 'Not Connected';
            document.getElementById('configured-buttons-count').textContent = 
                `${this.buttonConfig.length} buttons`;
            
        } catch (error) {
            console.error('Failed to update system status:', error);
        }
    }

    onSDCardSelected(path) {
        this.addConsoleMessage(`SD card selected: ${path}`, 'response');
        this.loadConfiguration();
    }

    onDeviceConnected(port) {
        this.addConsoleMessage(`Device connected on ${port}`, 'response');
        this.updateSystemStatus();
    }

    onDeviceMessage(message) {
        this.addConsoleMessage(message.trim(), 'response');
    }

    addConsoleMessage(message, type = 'normal') {
        const console = document.getElementById('console-output');
        const line = document.createElement('div');
        line.className = `console-line ${type}`;
        line.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
        
        console.appendChild(line);
        console.scrollTop = console.scrollHeight;
        
        // Limit console history
        const lines = console.querySelectorAll('.console-line');
        if (lines.length > 1000) {
            lines[0].remove();
        }
    }

    clearConsole() {
        document.getElementById('console-output').innerHTML = '';
        this.addConsoleMessage('Console cleared');
    }
}

// Initialize the UI when the page loads
const ui = new TactileDeviceUI();

// Make ui globally available for onclick handlers
window.ui = ui;
