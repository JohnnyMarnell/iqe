import { OscClient } from './osc-client'
import { logger } from './logger'
import './styles.css'

class Controls {
  private oscClient: OscClient
  private sliderTrack: HTMLElement
  private sliderFill: HTMLElement
  private sliderThumb: HTMLElement
  private valueDisplay: HTMLElement
  private statusEl: HTMLElement
  private toggleLogBtn: HTMLElement
  private logContainer: HTMLElement
  private isDragging = false
  private currentValue = 0
  private logVisible = false

  constructor() {
    logger.init()
    
    this.oscClient = new OscClient()
    
    this.sliderTrack = document.querySelector('.slider-track')!
    this.sliderFill = document.querySelector('.slider-fill')!
    this.sliderThumb = document.querySelector('.slider-thumb')!
    this.valueDisplay = document.querySelector('.value-display')!
    this.statusEl = document.querySelector('.status')!
    this.toggleLogBtn = document.querySelector('.toggle-log')!
    this.logContainer = document.querySelector('.log-container')!

    this.setupEventListeners()
    this.oscClient.connect()
    
    setTimeout(() => {
      this.statusEl.textContent = 'Connected'
      this.statusEl.classList.add('connected')
      this.oscClient.queryCurrentState()
    }, 1000)
  }

  private setupEventListeners() {
    this.sliderTrack.addEventListener('mousedown', this.handleStart.bind(this))
    this.sliderTrack.addEventListener('touchstart', this.handleStart.bind(this), { passive: true })
    
    document.addEventListener('mousemove', this.handleMove.bind(this))
    document.addEventListener('touchmove', this.handleMove.bind(this), { passive: true })
    
    document.addEventListener('mouseup', this.handleEnd.bind(this))
    document.addEventListener('touchend', this.handleEnd.bind(this))

    window.addEventListener('speedUpdate', ((e: CustomEvent) => {
      if (!this.isDragging) {
        this.updateValue(e.detail, false)
      }
    }) as EventListener)

    this.toggleLogBtn.addEventListener('click', () => {
      this.logVisible = !this.logVisible
      this.logContainer.classList.toggle('visible', this.logVisible)
      this.toggleLogBtn.textContent = this.logVisible ? 'Hide Log' : 'Show Log'
    })
  }

  private handleStart(e: MouseEvent | TouchEvent) {
    this.isDragging = true
    this.updateFromEvent(e)
  }

  private handleMove(e: MouseEvent | TouchEvent) {
    if (!this.isDragging) return
    this.updateFromEvent(e)
  }

  private handleEnd() {
    this.isDragging = false
  }

  private updateFromEvent(e: MouseEvent | TouchEvent) {
    const rect = this.sliderTrack.getBoundingClientRect()
    const y = 'touches' in e ? e.touches[0].clientY : e.clientY
    
    const relativeY = rect.bottom - y
    const percent = Math.max(0, Math.min(1, relativeY / rect.height))
    
    this.updateValue(percent)
  }

  private updateValue(value: number, sendOsc = true) {
    this.currentValue = value
    const percent = value * 100
    
    this.sliderFill.style.height = `${percent}%`
    this.sliderThumb.style.bottom = `${percent}%`
    this.valueDisplay.textContent = value.toFixed(2)

    if (sendOsc) {
      this.oscClient.sendSpeed(value)
    }
  }
}

new Controls()