import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { ChatCapabilities } from '../api/client'

const apiMock = vi.hoisted(() => ({
  sendChat: vi.fn(),
  resetChatSession: vi.fn(),
  fetchChatCapabilities: vi.fn(),
  uploadChatAttachment: vi.fn(),
  createKnowledgeDraft: vi.fn(),
  approveKnowledgeDraft: vi.fn(),
  discardKnowledgeDraft: vi.fn(),
  createRepoCapabilityDraft: vi.fn(),
  approveRepoCapabilityDraft: vi.fn(),
}))

vi.mock('../api/client', () => ({
  sendChat: apiMock.sendChat,
  resetChatSession: apiMock.resetChatSession,
  fetchChatCapabilities: apiMock.fetchChatCapabilities,
  uploadChatAttachment: apiMock.uploadChatAttachment,
  createKnowledgeDraft: apiMock.createKnowledgeDraft,
  approveKnowledgeDraft: apiMock.approveKnowledgeDraft,
  discardKnowledgeDraft: apiMock.discardKnowledgeDraft,
  createRepoCapabilityDraft: apiMock.createRepoCapabilityDraft,
  approveRepoCapabilityDraft: apiMock.approveRepoCapabilityDraft,
}))

const BASE_CAPABILITIES: ChatCapabilities = {
  research_enabled: true,
  research_provider_available: false,
  research_runtime_ready: false,
  default_research_provider: 'ddgs',
  auto_research_for_research_intent: true,
  attachments_enabled: true,
  save_to_knowledge_enabled: true,
  mit_repo_intake_enabled: true,
  mcp_enabled: false,
  mcp_server_names: [],
  supported_attachment_mime_prefixes: ['application/pdf', 'image/'],
}

describe('Veda React surfaces', () => {
  beforeEach(() => {
    vi.resetModules()
    localStorage.clear()
    apiMock.sendChat.mockReset()
    apiMock.resetChatSession.mockReset()
    apiMock.fetchChatCapabilities.mockReset()
    apiMock.uploadChatAttachment.mockReset()
    apiMock.createKnowledgeDraft.mockReset()
    apiMock.approveKnowledgeDraft.mockReset()
    apiMock.discardKnowledgeDraft.mockReset()
    apiMock.createRepoCapabilityDraft.mockReset()
    apiMock.approveRepoCapabilityDraft.mockReset()
    apiMock.fetchChatCapabilities.mockResolvedValue(BASE_CAPABILITIES)
  })

  it('shows temporary research unavailability on the chat page', async () => {
    const { ChatPage } = await import('../pages/ChatPage')

    render(<ChatPage />)

    const researchButton = screen.getByRole('button', { name: 'RESEARCH UNAVAILABLE' })
    expect(researchButton).toBeDisabled()
    expect(researchButton).toHaveAttribute(
      'title',
      'Research mode is enabled, but no live research provider is available right now.',
    )
  })

  it('keeps the widget attachment accept list synced and blocks research when runtime is down', async () => {
    const { useVedaStore } = await import('../store/vedaStore')
    useVedaStore.setState({ widgetOpen: true })

    const { VedaWidget } = await import('../components/veda/VedaWidget')
    const { container } = render(
      <MemoryRouter>
        <VedaWidget />
      </MemoryRouter>,
    )

    const researchButton = await screen.findByRole('button', { name: 'RESEARCH UNAVAILABLE' })
    expect(researchButton).toBeDisabled()
    expect(screen.getByText('Research is temporarily unavailable')).toBeInTheDocument()

    await waitFor(() => {
      const fileInput = container.querySelector('input[type="file"]')
      expect(fileInput).not.toBeNull()
      expect(fileInput?.getAttribute('accept')).toBe('application/pdf,image/*')
    })
  })
})
