const { app, BrowserWindow, ipcMain, dialog, Menu } = require('electron');
const path = require('path');
const fs = require('fs').promises;
const { SerialPort } = require('serialport');

class TactileDeviceManager {
  constructor() {
    this.mainWindow = null;
    this.sdCardPath = null;
    this.devicePort = null;
    this.manifest = null;
  }

  async createWindow() {
    this.mainWindow = new BrowserWindow({
      width: 1400,
      height: 900,
      minWidth: 1200,
      minHeight: 800,
      webPreferences: {
        nodeIntegration: true,
        contextIsolation: false,
        enableRemoteModule: true
      },
      icon: path.join(__dirname, '../assets/icon.png'),
      title: 'Tactile Device Manager',
      show: false
    });

    await this.mainWindow.loadFile(path.join(__dirname, 'renderer/index.html'));
    
    this.mainWindow.once('ready-to-show', () => {
      this.mainWindow.show();
      if (process.argv.includes('--dev')) {
        this.mainWindow.webContents.openDevTools();
      }
    });

    this.mainWindow.on('closed', () => {
      this.mainWindow = null;
    });

    this.setupMenu();
    this.setupIpcHandlers();
  }

  setupMenu() {
    const template = [
      {
        label: 'File',
        submenu: [
          {
            label: 'Select SD Card...',
            accelerator: 'CmdOrCtrl+O',
            click: () => this.selectSDCard()
          },
          {
            label: 'Refresh Device',
            accelerator: 'F5',
            click: () => this.refreshDevice()
          },
          { type: 'separator' },
          {
            label: 'Exit',
            accelerator: process.platform === 'darwin' ? 'Cmd+Q' : 'Ctrl+Q',
            click: () => app.quit()
          }
        ]
      },
      {
        label: 'Device',
        submenu: [
          {
            label: 'Connect Serial',
            click: () => this.connectSerial()
          },
          {
            label: 'Test All Buttons',
            click: () => this.testAllButtons()
          },
          {
            label: 'Toggle Priority Mode',
            click: () => this.togglePriorityMode()
          }
        ]
      },
      {
        label: 'Audio',
        submenu: [
          {
            label: 'Add Human Recording...',
            click: () => this.addAudioFile('human')
          },
          {
            label: 'Add Generated Audio...',
            click: () => this.addAudioFile('generated')
          },
          {
            label: 'Generate Missing Audio...',
            click: () => this.generateMissingAudio()
          }
        ]
      },
      {
        label: 'Help',
        submenu: [
          {
            label: 'About',
            click: () => this.showAbout()
          },
          {
            label: 'User Guide',
            click: () => this.showUserGuide()
          }
        ]
      }
    ];

    const menu = Menu.buildFromTemplate(template);
    Menu.setApplicationMenu(menu);
  }

  setupIpcHandlers() {
    // SD Card Management
    ipcMain.handle('select-sd-card', () => this.selectSDCard());
    ipcMain.handle('load-manifest', () => this.loadManifest());
    ipcMain.handle('save-manifest', (event, manifest) => this.saveManifest(manifest));
    
    // Device Communication
    ipcMain.handle('scan-serial-ports', () => this.scanSerialPorts());
    ipcMain.handle('connect-device', (event, port) => this.connectDevice(port));
    ipcMain.handle('send-command', (event, command) => this.sendCommand(command));
    
    // Audio Management
    ipcMain.handle('get-playlists', (event, key) => this.getPlaylists(key));
    ipcMain.handle('save-playlist', (event, key, type, tracks) => this.savePlaylist(key, type, tracks));
    ipcMain.handle('add-audio-file', (event, key, type) => this.addAudioFileDialog(key, type));
    ipcMain.handle('remove-audio-file', (event, filePath) => this.removeAudioFile(filePath));
    
    // Button Configuration
    ipcMain.handle('get-button-config', () => this.getButtonConfig());
    ipcMain.handle('save-button-config', (event, config) => this.saveButtonConfig(config));
    
    // System Status
    ipcMain.handle('get-system-status', () => this.getSystemStatus());
  }

  async selectSDCard() {
    const result = await dialog.showOpenDialog(this.mainWindow, {
      title: 'Select SD Card or Device Folder',
      properties: ['openDirectory'],
      message: 'Select the root directory of your SD card or device storage'
    });

    if (!result.canceled && result.filePaths.length > 0) {
      this.sdCardPath = result.filePaths[0];
      await this.loadManifest();
      this.mainWindow.webContents.send('sd-card-selected', this.sdCardPath);
      return this.sdCardPath;
    }
    return null;
  }

  async loadManifest() {
    if (!this.sdCardPath) return null;
    
    try {
      const manifestPath = path.join(this.sdCardPath, 'manifest.json');
      const manifestData = await fs.readFile(manifestPath, 'utf-8');
      this.manifest = JSON.parse(manifestData);
      return this.manifest;
    } catch (error) {
      console.log('No manifest found, creating default...');
      this.manifest = this.createDefaultManifest();
      await this.saveManifest(this.manifest);
      return this.manifest;
    }
  }

  createDefaultManifest() {
    return {
      schema: "tcd-playlists@1",
      version: "1.0.0",
      created: new Date().toISOString().split('T')[0],
      description: "Tactile communication device configuration",
      priority: "HUMAN_FIRST",
      strict_playlists: true,
      hardware: {
        pcf8575_count: 3,
        gpio_pins: [8, 9, 2, 5],
        total_capacity: 52
      },
      keys: []
    };
  }

  async saveManifest(manifest) {
    if (!this.sdCardPath) return false;
    
    try {
      const manifestPath = path.join(this.sdCardPath, 'manifest.json');
      await fs.writeFile(manifestPath, JSON.stringify(manifest, null, 2), 'utf-8');
      this.manifest = manifest;
      return true;
    } catch (error) {
      console.error('Failed to save manifest:', error);
      return false;
    }
  }

  async scanSerialPorts() {
    try {
      const ports = await SerialPort.list();
      return ports.filter(port => 
        port.manufacturer && 
        (port.manufacturer.includes('Arduino') || 
         port.manufacturer.includes('FTDI') ||
         port.manufacturer.includes('CH340'))
      );
    } catch (error) {
      console.error('Failed to scan serial ports:', error);
      return [];
    }
  }

  async connectDevice(portPath) {
    try {
      if (this.devicePort && this.devicePort.isOpen) {
        this.devicePort.close();
      }

      this.devicePort = new SerialPort({
        path: portPath,
        baudRate: 115200
      });

      return new Promise((resolve, reject) => {
        this.devicePort.on('open', () => {
          console.log('Device connected:', portPath);
          this.mainWindow.webContents.send('device-connected', portPath);
          resolve(true);
        });

        this.devicePort.on('error', (error) => {
          console.error('Serial port error:', error);
          reject(error);
        });

        this.devicePort.on('data', (data) => {
          const message = data.toString();
          this.mainWindow.webContents.send('device-message', message);
        });
      });
    } catch (error) {
      console.error('Failed to connect device:', error);
      return false;
    }
  }

  async sendCommand(command) {
    if (!this.devicePort || !this.devicePort.isOpen) {
      throw new Error('Device not connected');
    }

    return new Promise((resolve, reject) => {
      this.devicePort.write(command + '\n', (error) => {
        if (error) {
          reject(error);
        } else {
          resolve(true);
        }
      });
    });
  }

  async getPlaylists(key) {
    if (!this.sdCardPath) return { human: [], generated: [] };

    try {
      const humanPath = path.join(this.sdCardPath, 'mappings', 'playlists', `${key}_human.m3u`);
      const generatedPath = path.join(this.sdCardPath, 'mappings', 'playlists', `${key}_generated.m3u`);

      const [humanTracks, generatedTracks] = await Promise.all([
        this.readPlaylist(humanPath),
        this.readPlaylist(generatedPath)
      ]);

      return { human: humanTracks, generated: generatedTracks };
    } catch (error) {
      console.error('Failed to load playlists:', error);
      return { human: [], generated: [] };
    }
  }

  async readPlaylist(playlistPath) {
    try {
      const content = await fs.readFile(playlistPath, 'utf-8');
      return content.split('\n')
        .map(line => line.trim())
        .filter(line => line && !line.startsWith('#'));
    } catch (error) {
      return [];
    }
  }

  async savePlaylist(key, type, tracks) {
    if (!this.sdCardPath) return false;

    try {
      const playlistPath = path.join(this.sdCardPath, 'mappings', 'playlists', `${key}_${type}.m3u`);
      const playlistDir = path.dirname(playlistPath);
      
      await fs.mkdir(playlistDir, { recursive: true });
      
      const content = [
        `# ${type.charAt(0).toUpperCase() + type.slice(1)} recordings for ${key}`,
        ...tracks
      ].join('\n');

      await fs.writeFile(playlistPath, content, 'utf-8');
      return true;
    } catch (error) {
      console.error('Failed to save playlist:', error);
      return false;
    }
  }

  async addAudioFileDialog(key, type) {
    const result = await dialog.showOpenDialog(this.mainWindow, {
      title: `Add ${type} audio for ${key}`,
      properties: ['openFile'],
      filters: [
        { name: 'Audio Files', extensions: ['mp3', 'wav', 'ogg'] },
        { name: 'All Files', extensions: ['*'] }
      ]
    });

    if (!result.canceled && result.filePaths.length > 0) {
      return await this.addAudioFile(key, type, result.filePaths[0]);
    }
    return null;
  }

  async addAudioFile(key, type, sourceFilePath) {
    if (!this.sdCardPath) return null;

    try {
      const targetDir = path.join(this.sdCardPath, 'audio', type, key);
      await fs.mkdir(targetDir, { recursive: true });

      // Find next available filename
      const existingFiles = await fs.readdir(targetDir);
      const mp3Files = existingFiles.filter(f => f.endsWith('.mp3'));
      const nextNum = mp3Files.length + 1;
      const targetFileName = `${nextNum.toString().padStart(3, '0')}.mp3`;
      const targetFilePath = path.join(targetDir, targetFileName);

      // Copy the file
      await fs.copyFile(sourceFilePath, targetFilePath);

      // Update playlist
      const playlists = await this.getPlaylists(key);
      const relativePath = `audio/${type}/${key}/${targetFileName}`;
      playlists[type].push(relativePath);
      await this.savePlaylist(key, type, playlists[type]);

      return targetFilePath;
    } catch (error) {
      console.error('Failed to add audio file:', error);
      return null;
    }
  }

  async getButtonConfig() {
    if (!this.sdCardPath) return [];

    try {
      const configPath = path.join(this.sdCardPath, 'config', 'buttons.csv');
      const content = await fs.readFile(configPath, 'utf-8');
      
      return content.split('\n')
        .map(line => line.trim())
        .filter(line => line && !line.startsWith('#'))
        .map(line => {
          const [input, key] = line.split(',');
          return { input: input?.trim(), key: key?.trim() };
        })
        .filter(mapping => mapping.input && mapping.key);
    } catch (error) {
      console.error('Failed to load button config:', error);
      return [];
    }
  }

  async saveButtonConfig(config) {
    if (!this.sdCardPath) return false;

    try {
      const configPath = path.join(this.sdCardPath, 'config', 'buttons.csv');
      const configDir = path.dirname(configPath);
      
      await fs.mkdir(configDir, { recursive: true });
      
      const content = [
        '#INPUT,KEY',
        ...config.map(mapping => `${mapping.input},${mapping.key}`)
      ].join('\n');

      await fs.writeFile(configPath, content, 'utf-8');
      return true;
    } catch (error) {
      console.error('Failed to save button config:', error);
      return false;
    }
  }

  async getSystemStatus() {
    const status = {
      sdCard: !!this.sdCardPath,
      device: !!(this.devicePort && this.devicePort.isOpen),
      manifest: !!this.manifest,
      timestamp: new Date().toISOString()
    };

    if (this.sdCardPath) {
      try {
        const stats = await fs.stat(this.sdCardPath);
        status.sdCardPath = this.sdCardPath;
        status.sdCardAccessible = true;
      } catch (error) {
        status.sdCardAccessible = false;
      }
    }

    return status;
  }
}

const deviceManager = new TactileDeviceManager();

app.whenReady().then(() => {
  deviceManager.createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      deviceManager.createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
