import { act } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { ChatCapabilities } from '../api/client'

const apiMock = vi.hoisted(() => ({
  deleteAllChatSavedSessions: vi.fn(),
  deleteChatSavedSession: vi.fn(),
  sendChat: vi.fn(),
  resetChatSession: vi.fn(),
  fetchChatCapabilities: vi.fn(),
  fetchChatSavedSessions: vi.fn(),
  upsertChatSavedSession: vi.fn(),
  uploadChatAttachment: vi.fn(),
}))

vi.mock('../api/client', () => ({
  deleteAllChatSavedSessions: apiMock.deleteAllChatSavedSessions,
  deleteChatSavedSession: apiMock.deleteChatSavedSession,
  sendChat: apiMock.sendChat,
  resetChatSession: apiMock.resetChatSession,
  fetchChatCapabilities: apiMock.fetchChatCapabilities,
  fetchChatSavedSessions: apiMock.fetchChatSavedSessions,
  upsertChatSavedSession: apiMock.upsertChatSavedSession,
  uploadChatAttachment: apiMock.uploadChatAttachment,
}))

const BASE_CAPABILITIES: ChatCapabilities = {
  research_enabled: true,
  research_provider_available: true,
  research_runtime_ready: true,
  default_research_provider: 'ddgs',
  auto_research_for_research_intent: true,
  attachments_enabled: true,
  save_to_knowledge_enabled: true,
  mit_repo_intake_enabled: true,
  mcp_enabled: false,
  mcp_server_names: [],
  supported_attachment_mime_prefixes: ['application/pdf', 'image/'],
}

describe('vedaStore research readiness', () => {
  beforeEach(() => {
    vi.resetModules()
    localStorage.clear()
    apiMock.sendChat.mockReset()
    apiMock.resetChatSession.mockReset()
    apiMock.fetchChatCapabilities.mockReset()
    apiMock.fetchChatSavedSessions.mockReset()
    apiMock.upsertChatSavedSession.mockReset()
    apiMock.deleteChatSavedSession.mockReset()
    apiMock.deleteAllChatSavedSessions.mockReset()
    apiMock.uploadChatAttachment.mockReset()
    apiMock.fetchChatCapabilities.mockResolvedValue(BASE_CAPABILITIES)
    apiMock.fetchChatSavedSessions.mockResolvedValue({ sessions: [] })
  })

  it('stores runtime readiness and turns off research mode when live research is unavailable', async () => {
    localStorage.setItem('cfip-research-mode', 'on')
    apiMock.fetchChatCapabilities.mockResolvedValue({
      ...BASE_CAPABILITIES,
      research_provider_available: false,
      research_runtime_ready: false,
    })

    const { useVedaStore } = await import('../store/vedaStore')

    expect(useVedaStore.getState().researchMode).toBe(true)

    await act(async () => {
      await useVedaStore.getState().refreshCapabilities()
    })

    const state = useVedaStore.getState()
    expect(state.researchEnabled).toBe(true)
    expect(state.researchProviderAvailable).toBe(false)
    expect(state.researchRuntimeReady).toBe(false)
    expect(state.researchMode).toBe(false)
    expect(state.attachmentAccept).toBe('application/pdf,image/*')
    expect(localStorage.getItem('cfip-research-mode')).toBe('off')
  })

  it('blocks research mode when no live provider is ready', async () => {
    const { useVedaStore } = await import('../store/vedaStore')

    act(() => {
      useVedaStore.setState({
        researchEnabled: true,
        researchRuntimeReady: false,
        apiError: null,
      })
      useVedaStore.getState().setResearchMode(true)
    })

    const state = useVedaStore.getState()
    expect(state.researchMode).toBe(false)
    expect(state.apiError).toBe('Research mode is enabled, but no live research provider is available right now.')
  })
})

// ─── Bug Condition Tests (Property 1) ─────────────────────────────────────────

describe("browserTtsFallback — bug condition (Property 1)", () => {
  let capturedUtterance: SpeechSynthesisUtterance | null = null

  beforeEach(() => {
    vi.resetModules()
    vi.clearAllMocks()
    localStorage.clear()
    capturedUtterance = null

    vi.mocked(window.speechSynthesis.speak).mockImplementation((u: SpeechSynthesisUtterance) => {
      capturedUtterance = u
      // Simulate onend to resolve the speak() promise
      setTimeout(() => { u.onend?.(new Event('end') as unknown as SpeechSynthesisEvent) }, 0)
    })
  })

  it("1.1 selects female voice when female+lang voice is available", async () => {
    // **Validates: Requirements 1.1, 1.2**
    const hiINFemaleVoice = {
      lang: 'hi-IN',
      name: 'Microsoft Swara Female',
      voiceURI: 'hi-IN-female',
    } as unknown as SpeechSynthesisVoice

    vi.mocked(window.speechSynthesis.getVoices).mockReturnValueOnce([hiINFemaleVoice])

    // Trigger browserTtsFallback via a failed fetch
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({ ok: false, status: 500 } as Response)

    const { useVedaStore } = await import('../store/vedaStore')
    useVedaStore.setState({ voiceLang: 'hi' })

    await useVedaStore.getState().speak('जी बोलिए')

    // On unfixed code this FAILS: voice stays null
    expect(capturedUtterance?.voice).not.toBeNull()
  })

  it("1.2 selects lang-only voice when no female label in name", async () => {
    // **Validates: Requirements 1.1, 1.2**
    const hiINVoice = {
      lang: 'hi-IN',
      name: 'hi-IN-SwaraNeural',
      voiceURI: 'swara',
    } as unknown as SpeechSynthesisVoice

    vi.mocked(window.speechSynthesis.getVoices).mockReturnValueOnce([hiINVoice])

    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({ ok: false, status: 500 } as Response)

    const { useVedaStore } = await import('../store/vedaStore')
    useVedaStore.setState({ voiceLang: 'hi' })

    await useVedaStore.getState().speak('जी बोलिए')

    // On unfixed code this FAILS: voice stays null (lang-only not picked either)
    expect(capturedUtterance?.voice).not.toBeNull()
  })
})

// ─── Preservation Tests (Property 2) ──────────────────────────────────────────

describe("browserTtsFallback — preservation (Property 2)", () => {
  let capturedUtterance: SpeechSynthesisUtterance | null = null

  beforeEach(() => {
    vi.resetModules()
    vi.clearAllMocks()
    localStorage.clear()
    capturedUtterance = null

    vi.mocked(window.speechSynthesis.speak).mockImplementation((u: SpeechSynthesisUtterance) => {
      capturedUtterance = u
      setTimeout(() => { u.onend?.(new Event('end') as unknown as SpeechSynthesisEvent) }, 0)
    })
  })

  it("2.1 speaks with null voice when getVoices returns empty list", async () => {
    // **Validates: Requirements 3.3, 3.7**
    // getVoices default mock already returns [] from setup.ts

    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({ ok: false, status: 500 } as Response)

    const { useVedaStore } = await import('../store/vedaStore')
    useVedaStore.setState({ voiceLang: 'hi' })

    await useVedaStore.getState().speak('test')

    expect(window.speechSynthesis.speak).toHaveBeenCalled()
    expect(capturedUtterance?.voice).toBeNull()
  })

  it("2.2 still speaks when getVoices throws", async () => {
    // **Validates: Requirements 3.2, 3.3**
    vi.mocked(window.speechSynthesis.getVoices).mockImplementationOnce(() => {
      throw new Error('not supported')
    })

    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({ ok: false, status: 500 } as Response)

    const { useVedaStore } = await import('../store/vedaStore')
    useVedaStore.setState({ voiceLang: 'hi' })

    await useVedaStore.getState().speak('test')

    // Must not crash — speak must still be called
    expect(window.speechSynthesis.speak).toHaveBeenCalled()
  })

  it("2.3 does not invoke browser TTS when primary path succeeds", async () => {
    // **Validates: Requirements 3.1**
    // vedaStore fires 2 prefetch calls (greeting + filler) on import.
    // We let those fail (ok: false) and give the actual TTS call a blob response.
    const blob = new Blob(['audio'], { type: 'audio/mpeg' })
    const failResponse = { ok: false, status: 500 } as Response
    const blobResponse = { ok: true, blob: async () => blob } as unknown as Response

    vi.spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(failResponse)  // greeting prefetch
      .mockResolvedValueOnce(failResponse)  // filler prefetch
      .mockResolvedValueOnce(blobResponse)  // actual TTS call for speak('test')

    vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:fake-url')

    const { useVedaStore } = await import('../store/vedaStore')
    useVedaStore.setState({ voiceLang: 'hi' })

    // Start speak — primary path should use Audio element, not speechSynthesis.speak
    const speakPromise = useVedaStore.getState().speak('test')

    // Give the async path enough time to resolve fetchTtsUrl and start playUrl
    await new Promise(r => setTimeout(r, 100))

    expect(window.speechSynthesis.speak).not.toHaveBeenCalled()

    // Resolve cleanly
    speakPromise.catch(() => {})
  })
})
