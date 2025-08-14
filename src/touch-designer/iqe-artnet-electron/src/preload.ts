import { contextBridge, ipcRenderer } from 'electron';

contextBridge.exposeInMainWorld('artnetAPI', {
  getPixels: () => ipcRenderer.invoke('get-pixels'),
  getParCans: () => ipcRenderer.invoke('get-parcans'),
  getStats: () => ipcRenderer.invoke('get-stats'),
  setConfig: (config: any) => ipcRenderer.invoke('set-config', config),
  fatalError: (message: string) => ipcRenderer.invoke('fatal-error', message)
});