import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach, vi } from 'vitest'

afterEach(() => {
  cleanup()
})

const fetchMock = vi.fn(async () => ({
  ok: false,
  blob: async () => new Blob(),
  json: async () => null,
}))

vi.stubGlobal('fetch', fetchMock)

class AudioMock {
  src: string
  volume = 1
  currentTime = 0
  onended: (() => void) | null = null
  onerror: (() => void) | null = null

  constructor(src = '') {
    this.src = src
  }

  play = vi.fn().mockResolvedValue(undefined)
  pause = vi.fn()
  load = vi.fn()
}

class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}

class SpeechSynthesisUtteranceMock {
  text: string
  lang = 'en-IN'
  rate = 1
  pitch = 1
  volume = 1
  voice: SpeechSynthesisVoice | null = null
  onend: ((event?: Event) => void) | null = null
  onerror: ((event?: Event) => void) | null = null

  constructor(text: string) {
    this.text = text
  }
}

vi.stubGlobal('Audio', AudioMock)
vi.stubGlobal('ResizeObserver', ResizeObserverMock)
vi.stubGlobal('SpeechSynthesisUtterance', SpeechSynthesisUtteranceMock)
vi.stubGlobal('requestAnimationFrame', vi.fn((cb: FrameRequestCallback) => window.setTimeout(() => cb(0), 0)))
vi.stubGlobal('cancelAnimationFrame', vi.fn((id: number) => window.clearTimeout(id)))

Object.defineProperty(window, 'speechSynthesis', {
  configurable: true,
  value: {
    cancel: vi.fn(),
    speak: vi.fn(),
    getVoices: vi.fn(() => []),
  },
})

Object.defineProperty(window, 'matchMedia', {
  configurable: true,
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

Object.defineProperty(navigator, 'clipboard', {
  configurable: true,
  value: {
    writeText: vi.fn().mockResolvedValue(undefined),
  },
})

Object.defineProperty(HTMLElement.prototype, 'scrollIntoView', {
  configurable: true,
  value: vi.fn(),
})

if (!URL.createObjectURL) {
  Object.defineProperty(URL, 'createObjectURL', {
    configurable: true,
    value: vi.fn(() => 'blob:mock'),
  })
}

if (!URL.revokeObjectURL) {
  Object.defineProperty(URL, 'revokeObjectURL', {
    configurable: true,
    value: vi.fn(),
  })
}
