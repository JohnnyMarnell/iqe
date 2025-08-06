// Canvas LED Visualizer with Dynamic Resizing
(() => {
  interface ArtNetAPI {
    getPixels: () => Promise<number[]>;
    getStats: () => Promise<Stats>;
    setConfig: (config: { spacedRows?: boolean }) => Promise<void>;
    fatalError: (message: string) => Promise<void>;
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

  // Access the API through window
  const artnetAPI = (window as any).artnetAPI as ArtNetAPI;

class LEDVisualizer {
  private canvas: HTMLCanvasElement;
  private ctx: CanvasRenderingContext2D;
  private canvasInfo: HTMLElement;
  private spacedMode = false;
  private showGrid = true;
  private showLabels = true;
  private autoScale = true;
  private rowGap = 14; // Default spacing
  private pixelRadius = 3; // Pixel size multiplier
  private enableGlow = true; // Enable glow effect
  
  // LED configuration
  private readonly width = 420;
  private readonly height = 24;
  
  // Display state
  private scale = 1;
  private displayWidth = 420;
  private displayHeight = 24;
  
  // Animation
  private animationId: number | null = null;
  private lastStatsUpdate = 0;
  private frameCount = 0;
  
  // Logging
  private logContainer: HTMLElement;
  private maxLogEntries = 100;

  constructor() {
    this.canvas = document.getElementById('led-canvas') as HTMLCanvasElement;
    this.ctx = this.canvas.getContext('2d', { alpha: false })!;
    this.canvasInfo = document.getElementById('canvas-info')!;
    this.logContainer = document.getElementById('log-container')!;
    
    this.log('✓ LED Visualizer initialized', 'success');
    
    this.setupControls();
    this.setupResizeObserver();
    this.updateCanvasSize();
    this.start();
  }

  private setupControls(): void {
    const spacedModeCheckbox = document.getElementById('spaced-mode') as HTMLInputElement;
    const showGridCheckbox = document.getElementById('show-grid') as HTMLInputElement;
    const showLabelsCheckbox = document.getElementById('show-labels') as HTMLInputElement;
    const autoScaleCheckbox = document.getElementById('auto-scale') as HTMLInputElement;
    const pixelRadiusSlider = document.getElementById('pixel-radius') as HTMLInputElement;
    const pixelRadiusValue = document.getElementById('pixel-radius-value')!;
    const enableGlowCheckbox = document.getElementById('enable-glow') as HTMLInputElement;
    const clearLogButton = document.getElementById('clear-log') as HTMLButtonElement;
    const toggleSidebarButton = document.getElementById('toggle-sidebar') as HTMLButtonElement;
    const spacingSliderContainer = document.getElementById('spacing-slider-container')!;
    const spacingSlider = document.getElementById('spacing-slider') as HTMLInputElement;
    const spacingValue = document.getElementById('spacing-value')!;

    spacedModeCheckbox.addEventListener('change', (e) => {
      this.spacedMode = (e.target as HTMLInputElement).checked;
      spacingSliderContainer.style.display = this.spacedMode ? 'flex' : 'none';
      this.updateCanvasSize();
      artnetAPI.setConfig({ spacedRows: this.spacedMode });
      this.log(`Spaced mode: ${this.spacedMode ? 'ON' : 'OFF'}`);
    });

    spacingSlider.addEventListener('input', (e) => {
      this.rowGap = parseInt((e.target as HTMLInputElement).value);
      spacingValue.textContent = this.rowGap.toString();
      this.updateCanvasSize();
    });

    spacingSlider.addEventListener('change', (e) => {
      this.log(`Row spacing changed to: ${this.rowGap} pixels`);
    });

    showGridCheckbox.addEventListener('change', (e) => {
      this.showGrid = (e.target as HTMLInputElement).checked;
    });

    showLabelsCheckbox.addEventListener('change', (e) => {
      this.showLabels = (e.target as HTMLInputElement).checked;
    });

    autoScaleCheckbox.addEventListener('change', (e) => {
      this.autoScale = (e.target as HTMLInputElement).checked;
      this.updateCanvasSize();
    });

    pixelRadiusSlider.addEventListener('input', (e) => {
      this.pixelRadius = parseFloat((e.target as HTMLInputElement).value);
      pixelRadiusValue.textContent = this.pixelRadius.toString();
    });

    pixelRadiusSlider.addEventListener('change', (e) => {
      this.log(`Pixel radius changed to: ${this.pixelRadius}`);
    });

    enableGlowCheckbox.addEventListener('change', (e) => {
      this.enableGlow = (e.target as HTMLInputElement).checked;
      this.log(`Glow effect: ${this.enableGlow ? 'ON' : 'OFF'}`);
    });

    clearLogButton.addEventListener('click', () => {
      this.logContainer.innerHTML = '';
      this.log('Log cleared');
    });

    toggleSidebarButton.addEventListener('click', () => {
      const sidebar = document.getElementById('sidebar')!;
      sidebar.classList.toggle('collapsed');
    });
  }

  private setupResizeObserver(): void {
    const container = document.getElementById('canvas-container')!;
    
    const resizeObserver = new ResizeObserver(() => {
      this.updateCanvasSize();
    });
    
    resizeObserver.observe(container);
    
    // Also handle window resize
    window.addEventListener('resize', () => {
      this.updateCanvasSize();
    });
  }

  private updateCanvasSize(): void {
    const container = document.getElementById('canvas-container')!;
    const containerWidth = container.clientWidth - 40; // Padding
    const containerHeight = container.clientHeight - 40;
    
    // Calculate display dimensions
    if (this.spacedMode) {
      // Dynamic spacing based on slider
      this.displayHeight = 24 + 23 * this.rowGap;
      this.displayWidth = 420;
    } else {
      this.displayHeight = 24;
      this.displayWidth = 420;
    }
    
    if (this.autoScale) {
      // Calculate scale to fit container
      const scaleX = containerWidth / this.displayWidth;
      const scaleY = containerHeight / this.displayHeight;
      this.scale = Math.min(scaleX, scaleY);
      
      // Limit max scale for performance
      this.scale = Math.min(this.scale, 10);
    } else {
      this.scale = 1;
    }
    
    // Set canvas size
    this.canvas.width = Math.floor(this.displayWidth * this.scale);
    this.canvas.height = Math.floor(this.displayHeight * this.scale);
    
    // Update canvas info
    this.canvasInfo.textContent = `${this.displayWidth}×${this.displayHeight} @ ${this.scale.toFixed(1)}x`;
  }

  private log(message: string, type: 'info' | 'success' | 'warning' | 'error' = 'info'): void {
    const time = new Date().toLocaleTimeString('en-US', { hour12: false });
    
    const entry = document.createElement('div');
    entry.className = 'log-entry';
    
    const timeSpan = document.createElement('span');
    timeSpan.className = 'log-time';
    timeSpan.textContent = time;
    
    const messageSpan = document.createElement('span');
    messageSpan.className = `log-${type}`;
    messageSpan.textContent = message;
    
    entry.appendChild(timeSpan);
    entry.appendChild(messageSpan);
    
    this.logContainer.insertBefore(entry, this.logContainer.firstChild);
    
    // Limit log entries
    while (this.logContainer.children.length > this.maxLogEntries) {
      this.logContainer.removeChild(this.logContainer.lastChild!);
    }
  }

  private async animate(): Promise<void> {
    this.frameCount++;
    
    try {
      // Get pixel data
      const pixels = await artnetAPI.getPixels();
      
      // Clear canvas
      this.ctx.fillStyle = '#000';
      this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
      
      // Debug: draw a test rectangle on first frame
      if (this.frameCount === 1) {
        this.ctx.fillStyle = '#ff0000';
        this.ctx.fillRect(10, 10, 50, 20);
        this.log('Drew test red rectangle at 10,10', 'info');
      }
      
      // Draw pixels
      this.drawPixels(pixels);
      
      // Draw overlays
      if (this.showGrid) this.drawGrid();
      if (this.showLabels) this.drawLabels();
      
      // Update stats periodically
      const now = Date.now();
      if (now - this.lastStatsUpdate > 500) {
        this.updateStats();
        this.lastStatsUpdate = now;
      }
      
    } catch (error) {
      if (this.frameCount === 1) {
        this.log(`Animation error: ${error}`, 'error');
      }
    }
    
    // Continue animation
    this.animationId = requestAnimationFrame(() => this.animate());
  }

  private drawPixels(pixels: number[]): void {
    const rowGap = this.spacedMode ? this.rowGap : 0;
    
    // Count lit pixels for logging
    let litPixels = 0;
    
    // Debug pixel data
    if (this.frameCount === 10) {
      let nonZeroFound = false;
      for (let i = 0; i < Math.min(100, pixels.length); i += 3) {
        if (pixels[i] > 0 || pixels[i+1] > 0 || pixels[i+2] > 0) {
          nonZeroFound = true;
          break;
        }
      }
      this.log(`Pixel data check: ${pixels.length} bytes, non-zero: ${nonZeroFound}`, 'info');
    }
    
    for (let row = 0; row < 24; row++) {
      const y = row + row * rowGap;
      
      for (let col = 0; col < 420; col++) {
        const pixelIndex = (row * 420 + col) * 3;
        const r = pixels[pixelIndex] || 0;
        const g = pixels[pixelIndex + 1] || 0;
        const b = pixels[pixelIndex + 2] || 0;
        
        if (r > 0 || g > 0 || b > 0) {
          litPixels++;
          
          const x = col * this.scale;
          const centerY = y * this.scale;
          const baseSize = this.scale * this.pixelRadius;
          
          // Apply glow effect if enabled
          if (this.enableGlow) {
            // Create gradient for glow
            const gradient = this.ctx.createRadialGradient(
              x + baseSize / 2,
              centerY + baseSize / 2,
              0,
              x + baseSize / 2,
              centerY + baseSize / 2,
              baseSize * 1.5
            );
            
            // Brighter core
            const brightness = Math.max(r, g, b);
            const glowIntensity = brightness / 255;
            
            // Inner glow (bright core)
            gradient.addColorStop(0, `rgba(${Math.min(255, r * 1.5)},${Math.min(255, g * 1.5)},${Math.min(255, b * 1.5)},1)`);
            // Mid glow
            gradient.addColorStop(0.4, `rgba(${r},${g},${b},0.9)`);
            // Outer glow fade
            gradient.addColorStop(0.7, `rgba(${r},${g},${b},${0.3 * glowIntensity})`);
            gradient.addColorStop(1, `rgba(${r},${g},${b},0)`);
            
            this.ctx.fillStyle = gradient;
            
            // Draw larger area for glow
            this.ctx.fillRect(
              Math.floor(x - baseSize * 0.5),
              Math.floor(centerY - baseSize * 0.5),
              Math.ceil(baseSize * 2),
              Math.ceil(baseSize * 2)
            );
            
            // Add subtle bloom effect for bright pixels
            if (brightness > 200) {
              this.ctx.globalAlpha = 0.3;
              const bloomGradient = this.ctx.createRadialGradient(
                x + baseSize / 2,
                centerY + baseSize / 2,
                baseSize,
                x + baseSize / 2,
                centerY + baseSize / 2,
                baseSize * 2.5
              );
              bloomGradient.addColorStop(0, `rgba(${r},${g},${b},0.4)`);
              bloomGradient.addColorStop(1, `rgba(${r},${g},${b},0)`);
              this.ctx.fillStyle = bloomGradient;
              this.ctx.fillRect(
                Math.floor(x - baseSize),
                Math.floor(centerY - baseSize),
                Math.ceil(baseSize * 3),
                Math.ceil(baseSize * 3)
              );
              this.ctx.globalAlpha = 1;
            }
          } else {
            // Simple rectangle without glow
            this.ctx.fillStyle = `rgb(${r},${g},${b})`;
            this.ctx.fillRect(
              Math.floor(x),
              Math.floor(centerY),
              Math.ceil(baseSize),
              Math.ceil(baseSize)
            );
          }
        }
      }
    }
    
    // Log every 60 frames
    if (this.frameCount % 60 === 0 && litPixels > 0) {
      this.log(`Rendering ${litPixels} lit pixels at scale ${this.scale.toFixed(2)}`, 'info');
    }
  }

  private drawGrid(): void {
    this.ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
    this.ctx.lineWidth = 1;
    
    const rowGap = this.spacedMode ? this.rowGap : 0;
    
    // Draw strip boundaries (after horizontal flip)
    this.ctx.beginPath();
    
    // Strip boundaries at pixels 80, 250
    [80, 250].forEach(x => {
      this.ctx.moveTo(x * this.scale, 0);
      this.ctx.lineTo(x * this.scale, this.canvas.height);
    });
    
    // Draw row boundaries if in spaced mode
    if (this.spacedMode) {
      for (let row = 1; row < 24; row++) {
        const y = (row + (row - 1) * rowGap) * this.scale;
        this.ctx.moveTo(0, y);
        this.ctx.lineTo(this.canvas.width, y);
      }
    }
    
    this.ctx.stroke();
  }

  private drawLabels(): void {
    this.ctx.fillStyle = 'rgba(255, 255, 255, 0.5)';
    this.ctx.font = `${Math.max(10, 10 * this.scale)}px monospace`;
    
    const rowGap = this.spacedMode ? this.rowGap : 0;
    
    // Strip labels (after horizontal flip)
    this.ctx.fillText('Strip 3', 10, 20);
    this.ctx.fillText('Strip 2', 90 * this.scale, 20);
    this.ctx.fillText('Strip 1', 260 * this.scale, 20);
    
    // Row labels (after vertical flip - Row 24 at top, Row 1 at bottom)
    const labelInterval = this.spacedMode ? 4 : 6;
    for (let i = 0; i < 24; i += labelInterval) {
      const y = (i + i * rowGap + 0.5) * this.scale;
      const rowLabel = 24 - i;
      
      this.ctx.fillText(
        `R${rowLabel}`,
        this.canvas.width - 40,
        y + 5
      );
    }
  }

  private async updateStats(): Promise<void> {
    try {
      const stats = await artnetAPI.getStats();
      const statsDiv = document.getElementById('stats')!;
      
      const activeCount = stats.activeUniverses.length;
      const expectedCount = stats.expectedUniverses.length;
      const missingCount = stats.missingUniverses.length;
      
      let html = '';
      
      if (stats.packetCount === 0) {
        html = '<div class="stat-line warning loading">Waiting for ArtNet data on port 6454...</div>';
      } else {
        // Remove loading class
        statsDiv.classList.remove('loading');
        
        html += `<div class="stat-line">`;
        html += `<span class="universe-info">Active Universes: ${activeCount}/${expectedCount}</span>`;
        
        if (missingCount > 0) {
          const missing = stats.missingUniverses.slice(0, 10).join(', ');
          html += ` <span class="warning">(Missing: ${missing}${missingCount > 10 ? '...' : ''})</span>`;
        }
        html += '</div>';
        
        html += `<div class="stat-line">`;
        html += `Packets: ${stats.packetCount.toLocaleString()} | `;
        html += `Rate: ~${Math.round(stats.packetCount / (Date.now() / 1000))} pps | `;
        html += `Last: ${stats.lastPacket.toFixed(1)}s ago`;
        html += '</div>';
        
        // Show data rate
        const dataRate = activeCount * 30 * 500; // universes * fps * bytes
        html += `<div class="stat-line">`;
        html += `Data Rate: ~${(dataRate / 1024 / 1024).toFixed(1)} MB/s`;
        html += '</div>';
      }
      
      statsDiv.innerHTML = html;
      
      // Log milestones
      if (stats.packetCount === 1) {
        this.log('✓ First ArtNet packet received', 'success');
      } else if (stats.packetCount === 100) {
        this.log(`✓ Receiving from ${activeCount} universes`, 'success');
      }
      
    } catch (error) {
      this.log(`Stats error: ${error}`, 'error');
    }
  }

  start(): void {
    this.animate();
    this.log('✓ Animation started', 'success');
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
    try {
      new LEDVisualizer();
    } catch (error) {
      console.error('Failed to initialize LEDVisualizer:', error);
      const statsDiv = document.getElementById('stats');
      if (statsDiv) {
        statsDiv.innerHTML = `<div class="stat-line error">Initialization Error: ${error}</div>`;
      }
    }
  });
})(); // End IIFE