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

  // Load debug page for now
  mainWindow.loadFile(path.join(__dirname, '../debug.html'));

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
    console.log('IPC: get-pixels called');
    const pixels = artnetReceiver?.getPixels();
    if (!pixels) {
      console.log('IPC: No pixels available');
      return new Array(420 * 24 * 3).fill(0); // Return empty pixel buffer
    }
    // Convert to regular array for IPC transfer
    const pixelArray = Array.from(pixels);
    console.log(`IPC: Returning ${pixelArray.length} pixels`);
    return pixelArray;
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