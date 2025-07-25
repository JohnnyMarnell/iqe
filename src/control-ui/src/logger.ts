export class Logger {
  private logContainer: HTMLElement | null = null
  private maxEntries = 100
  private filters = {
    outgoing: true,
    incoming: false,
    info: false
  }

  init() {
    this.logContainer = document.querySelector('.log-content')
    this.interceptConsole()
    this.setupFilters()
  }

  private setupFilters() {
    const outgoingCheckbox = document.querySelector('.filter-outgoing') as HTMLInputElement
    const incomingCheckbox = document.querySelector('.filter-incoming') as HTMLInputElement
    const infoCheckbox = document.querySelector('.filter-info') as HTMLInputElement

    outgoingCheckbox?.addEventListener('change', () => {
      this.filters.outgoing = outgoingCheckbox.checked
      this.applyFilters()
    })

    incomingCheckbox?.addEventListener('change', () => {
      this.filters.incoming = incomingCheckbox.checked
      this.applyFilters()
    })

    infoCheckbox?.addEventListener('change', () => {
      this.filters.info = infoCheckbox.checked
      this.applyFilters()
    })
  }

  private applyFilters() {
    const entries = this.logContainer?.querySelectorAll('.log-entry')
    entries?.forEach(entry => {
      const element = entry as HTMLElement
      const isSent = element.classList.contains('sent')
      const isReceived = element.classList.contains('received')
      const isInfo = element.classList.contains('info')

      const shouldShow = 
        (isSent && this.filters.outgoing) ||
        (isReceived && this.filters.incoming) ||
        (isInfo && this.filters.info)

      element.classList.toggle('hidden', !shouldShow)
    })
  }

  private interceptConsole() {
    const originalLog = console.log
    const originalWarn = console.warn
    
    console.log = (...args) => {
      originalLog.apply(console, args)
      this.addLogEntry('info', args)
    }
    
    console.warn = (...args) => {
      originalWarn.apply(console, args)
      this.addLogEntry('info', args)
    }
  }

  private addLogEntry(type: string, args: any[]) {
    if (!this.logContainer) return
    
    const logClass = this.getLogClass(args)
    const entry = document.createElement('div')
    entry.className = `log-entry ${logClass}`
    
    // Apply filter visibility
    const shouldShow = 
      (logClass === 'sent' && this.filters.outgoing) ||
      (logClass === 'received' && this.filters.incoming) ||
      (logClass === 'info' && this.filters.info)
    
    if (!shouldShow) {
      entry.classList.add('hidden')
    }
    
    const time = new Date().toLocaleTimeString()
    const timeSpan = document.createElement('span')
    timeSpan.className = 'log-time'
    timeSpan.textContent = time
    
    const content = document.createElement('span')
    content.textContent = this.formatArgs(args)
    
    entry.appendChild(timeSpan)
    entry.appendChild(content)
    
    this.logContainer.insertBefore(entry, this.logContainer.firstChild)
    
    // Keep only last N entries
    while (this.logContainer.children.length > this.maxEntries) {
      this.logContainer.removeChild(this.logContainer.lastChild!)
    }
  }

  private getLogClass(args: any[]): string {
    const str = args.join(' ')
    if (str.includes('📤') || str.includes('Sending')) return 'sent'
    if (str.includes('📥') || str.includes('Received')) return 'received'
    return 'info'
  }

  private formatArgs(args: any[]): string {
    return args.map(arg => {
      if (typeof arg === 'object') {
        return JSON.stringify(arg, null, 2)
      }
      return String(arg)
    }).join(' ')
  }
}

export const logger = new Logger()