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

  // Open DevTools in development
  if (process.env.NODE_ENV === 'development') {
    mainWindow.webContents.openDevTools();
  }
}

app.whenReady().then(() => {
  createWindow();

  // Start ArtNet receiver
  artnetReceiver = new ArtNetReceiver();
  artnetReceiver.start();

  // Set up IPC handlers
  ipcMain.handle('get-pixels', () => {
    return artnetReceiver?.getPixels() || [];
  });

  ipcMain.handle('get-stats', () => {
    return artnetReceiver?.getStats() || {};
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