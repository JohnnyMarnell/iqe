// Use the unified client if available, otherwise fall back to osc-js
import { OscClient } from './osc-client-unified'
import { logger } from './logger'
import './styles.css'

interface ControlConfig {
  type: 'button' | 'slider'
  label: string
  oscParam?: string
  oscPath?: string
  className?: string
  onAction?: (value?: number) => void
}

class Controls {
  private oscClient: OscClient
  private statusEl: HTMLElement
  private toggleLogBtn: HTMLElement
  private logContainer: HTMLElement
  private logVisible = false
  private controls: Map<string, HTMLElement> = new Map()
  private sliderConfigs: Map<HTMLElement, ControlConfig> = new Map()
  private isDragging = false
  private currentSlider: HTMLElement | null = null

  constructor() {
    logger.init()
    
    this.oscClient = new OscClient()
    
    this.statusEl = document.querySelector('.status')!
    this.toggleLogBtn = document.querySelector('.toggle-log')!
    this.logContainer = document.querySelector('.log-container')!

    // Define all controls
    const controlConfigs: ControlConfig[] = [
      {
        type: 'slider',
        label: 'Speed Up',
        oscPath: '/lx/mixer/master/effect/1/speed',
        className: 'speed-slider'
      },
      {
        type: 'button',
        label: 'Transition All',
        oscParam: 'transitionAll',  // Use the actual field name
        className: 'transition-all-btn'
      },
      {
        type: 'button',
        label: 'Color Change',
        oscParam: 'color',  // Use the existing color parameter
        className: 'color-btn'
      },
      {
        type: 'button',
        label: 'Hold (30s)',
        oscParam: 'pauseTransitions',  // Use the actual field name
        className: 'hold-btn'
      },
      {
        type: 'button',
        label: 'Solo Visuals',
        className: 'solo-visuals-btn',
        onAction: () => {
          this.oscClient.sendCommand('solo', 'Visuals')
        }
      },
      {
        type: 'slider',
        label: 'Pong P1',
        className: 'pong1-slider',
        onAction: (value?: number) => {
          if (value !== undefined) {
            this.oscClient.sendCommand('pong1', value.toString())
          }
        }
      },
      {
        type: 'slider',
        label: 'Pong P2',
        className: 'pong2-slider',
        onAction: (value?: number) => {
          if (value !== undefined) {
            this.oscClient.sendCommand('pong2', value.toString())
          }
        }
      },
      {
        type: 'button',
        label: 'Toggle Parcans',
        className: 'toggle-parcans-btn',
        onAction: () => {
          this.oscClient.sendCommand('toggleparcans', '')
        }
      }
    ]

    this.createControls(controlConfigs)
    this.setupEventListeners()
    this.oscClient.connect()
    
    setTimeout(() => {
      this.statusEl.textContent = 'Connected'
      this.statusEl.classList.add('connected')
      this.oscClient.queryCurrentState()
    }, 1000)
  }

  private createControls(configs: ControlConfig[]) {
    const app = document.getElementById('app')!
    const container = app.querySelector('.container')!
    
    // Clear existing controls except info section
    const info = container.querySelector('.info')
    container.innerHTML = ''
    
    // Create controls wrapper
    const controlsWrapper = document.createElement('div')
    controlsWrapper.className = 'controls-wrapper'
    
    configs.forEach(config => {
      if (config.type === 'slider') {
        const sliderGroup = this.createSlider(config)
        controlsWrapper.appendChild(sliderGroup)
      } else if (config.type === 'button') {
        // Buttons go in a shared button group
        let buttonGroup = controlsWrapper.querySelector('.button-group')
        if (!buttonGroup) {
          buttonGroup = document.createElement('div')
          buttonGroup.className = 'button-group'
          controlsWrapper.appendChild(buttonGroup)
        }
        const button = this.createButton(config)
        buttonGroup.appendChild(button)
      }
    })
    
    container.appendChild(controlsWrapper)
    if (info) container.appendChild(info)
  }

  private createSlider(config: ControlConfig): HTMLElement {
    const group = document.createElement('div')
    group.className = 'control-group'
    
    const label = document.createElement('h2')
    label.className = 'slider-label'
    label.textContent = config.label
    
    const sliderContainer = document.createElement('div')
    sliderContainer.className = 'slider-container'
    if (config.className) sliderContainer.classList.add(config.className)
    
    const track = document.createElement('div')
    track.className = 'slider-track'
    track.dataset.oscPath = config.oscPath || ''
    if (config.onAction) {
      track.dataset.onAction = 'true'
      // Store the config for this track
      this.sliderConfigs.set(track, config)
    }
    
    const fill = document.createElement('div')
    fill.className = 'slider-fill'
    
    const thumb = document.createElement('div')
    thumb.className = 'slider-thumb'
    
    const valueDisplay = document.createElement('div')
    valueDisplay.className = 'value-display'
    valueDisplay.textContent = '0.00'
    
    track.appendChild(fill)
    track.appendChild(thumb)
    sliderContainer.appendChild(track)
    sliderContainer.appendChild(valueDisplay)
    
    group.appendChild(label)
    group.appendChild(sliderContainer)
    
    // Store references
    this.controls.set(`${config.className}-track`, track)
    this.controls.set(`${config.className}-fill`, fill)
    this.controls.set(`${config.className}-thumb`, thumb)
    this.controls.set(`${config.className}-value`, valueDisplay)
    
    // Add slider event listeners
    track.addEventListener('mousedown', (e) => this.handleSliderStart(e, track))
    track.addEventListener('touchstart', (e) => this.handleSliderStart(e, track), { passive: true })
    
    // Listen for updates from OSC
    if (config.oscPath) {
      const pathParts = config.oscPath.split('/')
      const paramName = pathParts[pathParts.length - 1]
      window.addEventListener(`${paramName}Update`, ((e: CustomEvent) => {
        if (!this.isDragging) {
          this.updateSliderValue(track, e.detail, false)
        }
      }) as EventListener)
    }
    
    return group
  }

  private createButton(config: ControlConfig): HTMLElement {
    const button = document.createElement('button')
    button.className = config.className || 'control-btn'
    button.textContent = config.label
    
    button.addEventListener('click', () => {
      if (config.onAction) {
        config.onAction()
      } else if (config.oscParam) {
        this.oscClient.sendTrigger(config.oscParam)
      }
      
      // Visual feedback
      button.style.transform = 'scale(0.95)'
      setTimeout(() => {
        button.style.transform = ''
      }, 100)
    })
    
    this.controls.set(config.className || config.label, button)
    return button
  }

  private handleSliderStart(e: MouseEvent | TouchEvent, track: HTMLElement) {
    this.isDragging = true
    this.currentSlider = track
    this.updateFromEvent(e, track)
  }

  private handleSliderMove(e: MouseEvent | TouchEvent) {
    if (!this.isDragging || !this.currentSlider) return
    this.updateFromEvent(e, this.currentSlider)
  }

  private handleSliderEnd() {
    this.isDragging = false
    this.currentSlider = null
  }

  private updateFromEvent(e: MouseEvent | TouchEvent, track: HTMLElement) {
    const rect = track.getBoundingClientRect()
    const y = 'touches' in e ? e.touches[0].clientY : e.clientY
    
    // Calculate from bottom up - bottom of slider = 0, top = 1
    const relativeY = rect.bottom - y
    const percent = Math.max(0, Math.min(1, relativeY / rect.height))
    
    this.updateSliderValue(track, percent, true)
  }

  private updateSliderValue(track: HTMLElement, value: number, sendOsc = true) {
    const fill = track.querySelector('.slider-fill') as HTMLElement
    const thumb = track.querySelector('.slider-thumb') as HTMLElement
    const valueDisplay = track.parentElement?.querySelector('.value-display') as HTMLElement
    
    // Invert the visual display - when value is 0, show at bottom (0%), when 1, show at top (100%)
    const percent = (1 - value) * 100
    
    fill.style.height = `${100 - percent}%`  // Fill from bottom up
    thumb.style.bottom = `${100 - percent}%`  // Position thumb
    valueDisplay.textContent = value.toFixed(2)

    if (sendOsc) {
      if (track.dataset.oscPath) {
        this.oscClient.sendParameter(track.dataset.oscPath, value)
      } else if (track.dataset.onAction) {
        // Call the stored onAction callback
        const config = this.sliderConfigs.get(track)
        if (config?.onAction) {
          config.onAction(value)
        }
      }
    }
  }

  private setupEventListeners() {
    // Global slider event listeners
    document.addEventListener('mousemove', (e) => this.handleSliderMove(e))
    document.addEventListener('touchmove', (e) => this.handleSliderMove(e), { passive: true })
    
    document.addEventListener('mouseup', () => this.handleSliderEnd())
    document.addEventListener('touchend', () => this.handleSliderEnd())

    // Log toggle
    this.toggleLogBtn.addEventListener('click', () => {
      this.logVisible = !this.logVisible
      this.logContainer.classList.toggle('visible', this.logVisible)
      this.toggleLogBtn.textContent = this.logVisible ? 'Hide Log' : 'Show Log'
    })

    // Debug button if it exists
    const queryBtn = document.querySelector('.query-paths-btn')
    if (queryBtn) {
      queryBtn.addEventListener('click', () => {
        this.oscClient.queryAutopilotPaths()
        if (!this.logVisible) {
          this.logVisible = true
          this.logContainer.classList.add('visible')
          this.toggleLogBtn.textContent = 'Hide Log'
        }
      })
    }
  }
}

new Controls()