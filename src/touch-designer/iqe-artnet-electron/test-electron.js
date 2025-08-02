const { app, BrowserWindow } = require('electron');

app.whenReady().then(() => {
  console.log('Electron is ready!');
  
  const win = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  });
  
  win.loadURL('data:text/html,<h1>Electron Test</h1><p>If you see this, Electron is working!</p>');
  
  setTimeout(() => {
    console.log('Test complete');
    app.quit();
  }, 3000);
});

app.on('window-all-closed', () => {
  app.quit();
});