import { app, BrowserWindow, ipcMain } from 'electron';
import * as path from 'path';
import { ArtNetReceiver } from './artnet-receiver';

let mainWindow: BrowserWindow | null = null;
let artnetReceiver: ArtNetReceiver | null = null;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    },
    title: 'IQE ArtNet LED Visualizer - 420x24'
  });

  mainWindow.loadFile(path.join(__dirname, '../index.html'));

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // Open DevTools for debugging
  mainWindow.webContents.openDevTools();
}

app.whenReady().then(() => {
  createWindow();

  // Start ArtNet receiver
  console.log('Starting ArtNet receiver...');
  artnetReceiver = new ArtNetReceiver();
  artnetReceiver.start();
  console.log('ArtNet receiver started');

  // Set up IPC handlers
  ipcMain.handle('get-pixels', () => {
    const pixels = artnetReceiver?.getPixels();
    if (!pixels) {
      return new Array(420 * 24 * 3).fill(0); // Return empty pixel buffer
    }
    // Convert to regular array for IPC transfer
    return Array.from(pixels);
  });

  ipcMain.handle('get-stats', () => {
    return artnetReceiver?.getStats() || {
      universesReceived: 0,
      activeUniverses: [],
      expectedUniverses: [],
      missingUniverses: [],
      packetCount: 0,
      packetsByUniverse: {},
      lastPacket: 999
    };
  });

  ipcMain.handle('set-config', (event, config) => {
    if (artnetReceiver) {
      artnetReceiver.setConfig(config);
    }
  });

  ipcMain.handle('fatal-error', (event, message) => {
    console.error('\n========================================');
    console.error('FATAL ERROR IN RENDERER PROCESS:');
    console.error(message);
    console.error('========================================\n');
    console.error('Shutting down application...');
    
    // Clean shutdown
    if (artnetReceiver) {
      artnetReceiver.stop();
    }
    
    // Quit after a short delay to ensure message is printed
    setTimeout(() => {
      app.quit();
    }, 100);
  });
});

app.on('window-all-closed', () => {
  if (artnetReceiver) {
    artnetReceiver.stop();
  }
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});