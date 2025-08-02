// Canvas LED Visualizer

interface ArtNetAPI {
  getPixels: () => Promise<number[]>;
  getStats: () => Promise<Stats>;
  setConfig: (config: { spacedRows?: boolean }) => Promise<void>;
}

interface Stats {
  universesReceived: number;
  activeUniverses: number[];
  expectedUniverses: number[];
  missingUniverses: number[];
  packetCount: number;
  packetsByUniverse: { [key: number]: number };
  lastPacket: number;
}

declare global {
  interface Window {
    artnetAPI: ArtNetAPI;
  }
}

class LEDVisualizer {
  private canvas: HTMLCanvasElement;
  private ctx: CanvasRenderingContext2D;
  private spacedMode = false;
  private showGrid = true;
  private showLabels = true;
  
  // LED configuration
  private readonly width = 420;
  private readonly height = 24;
  private readonly pixelSize = 2; // Base pixel size
  private readonly gap = 1; // Gap between pixels
  
  // Display dimensions
  private displayWidth: number = 420;
  private displayHeight: number = 24;
  private rowHeight: number = 1;
  private rowGap: number = 0;
  
  // Animation
  private animationId: number | null = null;
  private lastStatsUpdate = 0;

  constructor() {
    this.canvas = document.getElementById('led-canvas') as HTMLCanvasElement;
    this.ctx = this.canvas.getContext('2d')!;
    
    console.log('LEDVisualizer initialized');
    
    this.setupControls();
    this.updateDisplayDimensions();
    this.start();
  }

  private setupControls(): void {
    const spacedModeCheckbox = document.getElementById('spaced-mode') as HTMLInputElement;
    const showGridCheckbox = document.getElementById('show-grid') as HTMLInputElement;
    const showLabelsCheckbox = document.getElementById('show-labels') as HTMLInputElement;
    const clearStatsButton = document.getElementById('clear-stats') as HTMLButtonElement;

    spacedModeCheckbox.addEventListener('change', (e) => {
      this.spacedMode = (e.target as HTMLInputElement).checked;
      this.updateDisplayDimensions();
      window.artnetAPI.setConfig({ spacedRows: this.spacedMode });
    });

    showGridCheckbox.addEventListener('change', (e) => {
      this.showGrid = (e.target as HTMLInputElement).checked;
    });

    showLabelsCheckbox.addEventListener('change', (e) => {
      this.showLabels = (e.target as HTMLInputElement).checked;
    });

    clearStatsButton.addEventListener('click', () => {
      // Could implement stats clearing if needed
    });
  }

  private updateDisplayDimensions(): void {
    if (this.spacedMode) {
      // Real world: 25' x 21' = 420 pixels x 353 pixels (maintaining aspect ratio)
      this.rowHeight = 1;
      this.rowGap = 14; // Same spacing as Python version
      this.displayHeight = 24 * this.rowHeight + 23 * this.rowGap;
    } else {
      this.displayHeight = 24;
      this.rowHeight = 1;
      this.rowGap = 0;
    }
    
    this.displayWidth = 420;
    
    // Set canvas size
    const scale = 2; // For better pixel rendering
    this.canvas.width = this.displayWidth * (this.pixelSize + this.gap) * scale;
    this.canvas.height = this.displayHeight * (this.pixelSize + this.gap) * scale;
    
    // Set CSS size
    this.canvas.style.width = `${this.canvas.width / 2}px`;
    this.canvas.style.height = `${this.canvas.height / 2}px`;
    
    // Scale context for sharp pixels
    this.ctx.scale(scale, scale);
  }

  private async animate(): Promise<void> {
    try {
      // Get pixel data
      const pixels = await window.artnetAPI.getPixels();
      
      // Log first time
      if (!this.lastStatsUpdate) {
        console.log('Got pixels:', pixels.length);
      }
      
      // Clear canvas
      this.ctx.fillStyle = '#000';
      this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
      
      // Draw pixels
      this.drawPixels(pixels);
      
      // Draw grid and labels
      if (this.showGrid) this.drawGrid();
      if (this.showLabels) this.drawLabels();
      
      // Update stats periodically
      const now = Date.now();
      if (now - this.lastStatsUpdate > 500) { // Update every 500ms
        this.updateStats();
        this.lastStatsUpdate = now;
      }
      
    } catch (error) {
      console.error('Animation error:', error);
    }
    
    // Continue animation
    this.animationId = requestAnimationFrame(() => this.animate());
  }

  private drawPixels(pixels: number[]): void {
    const pixelDraw = this.pixelSize + this.gap;
    
    for (let row = 0; row < 24; row++) {
      const displayRow = this.spacedMode ? 
        row * (this.rowHeight + this.rowGap) : row;
      
      for (let col = 0; col < 420; col++) {
        const pixelIndex = (row * 420 + col) * 3;
        const r = pixels[pixelIndex];
        const g = pixels[pixelIndex + 1];
        const b = pixels[pixelIndex + 2];
        
        if (r > 0 || g > 0 || b > 0) {
          this.ctx.fillStyle = `rgb(${r},${g},${b})`;
          this.ctx.fillRect(
            col * pixelDraw,
            displayRow * pixelDraw,
            this.pixelSize,
            this.pixelSize
          );
        }
      }
    }
  }

  private drawGrid(): void {
    this.ctx.strokeStyle = '#222';
    this.ctx.lineWidth = 0.5;
    
    // Draw strip boundaries
    const pixelDraw = this.pixelSize + this.gap;
    
    // Strip boundaries at pixels 80, 250 (after horizontal flip)
    [80, 250].forEach(x => {
      this.ctx.beginPath();
      this.ctx.moveTo(x * pixelDraw, 0);
      this.ctx.lineTo(x * pixelDraw, this.displayHeight * pixelDraw);
      this.ctx.stroke();
    });
    
    // Draw row boundaries if in spaced mode
    if (this.spacedMode) {
      for (let row = 0; row < 24; row++) {
        const y = row * (this.rowHeight + this.rowGap) * pixelDraw;
        this.ctx.beginPath();
        this.ctx.moveTo(0, y);
        this.ctx.lineTo(this.displayWidth * pixelDraw, y);
        this.ctx.stroke();
      }
    }
  }

  private drawLabels(): void {
    this.ctx.fillStyle = '#666';
    this.ctx.font = '10px monospace';
    
    const pixelDraw = this.pixelSize + this.gap;
    
    // Strip labels (after horizontal flip)
    this.ctx.fillText('Strip 3', 5, 15);
    this.ctx.fillText('Strip 2', 85 * pixelDraw, 15);
    this.ctx.fillText('Strip 1', 255 * pixelDraw, 15);
    
    // Row labels (after vertical flip - Row 24 at top, Row 1 at bottom)
    const labelInterval = this.spacedMode ? 4 : 6;
    for (let i = 0; i < 24; i += labelInterval) {
      const displayRow = this.spacedMode ? 
        i * (this.rowHeight + this.rowGap) : i;
      const rowLabel = 24 - i; // Flipped
      
      this.ctx.fillText(
        `Row ${rowLabel}`,
        this.canvas.width / 2 - 20,
        (displayRow + 0.5) * pixelDraw + 5
      );
    }
  }

  private async updateStats(): Promise<void> {
    try {
      const stats = await window.artnetAPI.getStats();
      const statsDiv = document.getElementById('stats')!;
      
      const activeCount = stats.activeUniverses.length;
      const expectedCount = stats.expectedUniverses.length;
      const missingCount = stats.missingUniverses.length;
      
      let html = '';
      
      if (stats.packetCount === 0) {
        html = '<div class="stat-line warning">Waiting for ArtNet data on port 6454...</div>';
      } else {
        html += `<div class="stat-line">`;
        html += `<span class="universe-info">Active Universes: ${activeCount}/${expectedCount}</span>`;
        
        if (missingCount > 0) {
          const missing = stats.missingUniverses.slice(0, 10).join(', ');
          html += ` <span class="warning">Missing: [${missing}${missingCount > 10 ? '...' : ''}]</span>`;
        } else {
          html += ' <span class="universe-info">✓ All universes active</span>';
        }
        html += '</div>';
        
        html += `<div class="stat-line">`;
        html += `Total Packets: ${stats.packetCount} | `;
        html += `Last: ${stats.lastPacket.toFixed(1)}s ago`;
        
        // Show top universes by packet count
        if (stats.packetsByUniverse) {
          const topUniverses = Object.entries(stats.packetsByUniverse)
            .sort(([, a], [, b]) => (b as number) - (a as number))
            .slice(0, 5)
            .map(([u, c]) => `U${u}:${c}`)
            .join(', ');
          
          html += ` | Top: ${topUniverses}`;
        }
        html += '</div>';
      }
      
      statsDiv.innerHTML = html;
      
    } catch (error) {
      console.error('Stats update error:', error);
    }
  }

  start(): void {
    this.animate();
  }

  stop(): void {
    if (this.animationId !== null) {
      cancelAnimationFrame(this.animationId);
      this.animationId = null;
    }
  }
}

// Start visualizer when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  new LEDVisualizer();
});

// Export to make this a module
export {};