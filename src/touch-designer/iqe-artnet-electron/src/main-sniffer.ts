import { app, BrowserWindow, ipcMain } from 'electron';
import * as path from 'path';
import { ArtNetSniffer } from './artnet-sniffer';

let mainWindow: BrowserWindow | null = null;
let artnetSniffer: ArtNetSniffer | null = null;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    backgroundColor: '#0a0a0a',
    titleBarStyle: 'hiddenInset',
    title: 'IQE ArtNet Sniffer - LED Grid + ParCans'
  });

  // Load the sniffer HTML
  mainWindow.loadFile(path.join(__dirname, '../index-sniffer.html'));

  // Open DevTools in development
  if (process.env.NODE_ENV !== 'production') {
    mainWindow.webContents.openDevTools();
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.whenReady().then(() => {
  createWindow();
  
  // Start ArtNet sniffer
  artnetSniffer = new ArtNetSniffer();
  artnetSniffer.start();
  
  console.log('ArtNet Sniffer started - monitoring network for ArtNet packets');
  console.log('Note: This will capture ArtNet traffic even if not addressed to localhost');

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (artnetSniffer) {
    artnetSniffer.stop();
  }
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// IPC handlers for renderer communication
ipcMain.handle('artnet:getPixels', async () => {
  if (!artnetSniffer) return new Uint8Array(420 * 24 * 3);
  return Array.from(artnetSniffer.getPixels());
});

ipcMain.handle('artnet:getStats', async () => {
  if (!artnetSniffer) {
    return {
      universesReceived: 0,
      activeUniverses: [],
      expectedUniverses: [],
      missingUniverses: [],
      packetCount: 0,
      packetsByUniverse: {},
      lastPacket: 999
    };
  }
  return artnetSniffer.getStats();
});

ipcMain.handle('artnet:getParCans', async () => {
  if (!artnetSniffer) {
    return {
      config: [],
      colors: {}
    };
  }
  const parCanData = artnetSniffer.getParCans();
  // Convert Map to object for serialization
  const colorsObj: { [key: number]: { r: number, g: number, b: number } } = {};
  parCanData.colors.forEach((color, id) => {
    colorsObj[id] = color;
  });
  return {
    config: parCanData.config,
    colors: colorsObj
  };
});

ipcMain.handle('artnet:setConfig', async (event, config) => {
  if (!artnetSniffer) return;
  artnetSniffer.setConfig(config);
});

ipcMain.handle('artnet:fatalError', async (event, message) => {
  console.error('Fatal error from renderer:', message);
  if (artnetSniffer) {
    artnetSniffer.stop();
  }
  app.quit();
});

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
  console.error('Uncaught exception:', error);
  if (mainWindow) {
    mainWindow.webContents.send('error', error.message);
  }
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled rejection at:', promise, 'reason:', reason);
});