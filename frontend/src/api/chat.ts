import { apiFetch, apiJson } from '@/lib/api'
import type { ChatMessage, ChatStep, Conversation } from '@/types/chat'

export const fetchConversations = () => apiJson<Conversation[]>('/chat/conversations')

export const fetchMessages = (conversationId: string) => apiJson<ChatMessage[]>(`/chat/conversations/${conversationId}/messages`)

export const renameConversation = (conversationId: string, title: string) =>
  apiJson<Conversation>(`/chat/conversations/${conversationId}`, { method: 'PATCH', body: JSON.stringify({ title }) })

export const deleteConversation = (conversationId: string) =>
  apiJson<void>(`/chat/conversations/${conversationId}`, { method: 'DELETE' })

export const deleteAllConversations = () => apiJson<void>('/chat/conversations', { method: 'DELETE' })

interface StreamHandlers {
  /** Server vừa tạo cuộc trò chuyện mới cho câu hỏi này (luôn đến trước mọi sự kiện khác) */
  onConversation: (conversation: Pick<Conversation, 'id' | 'title'>) => void
  onStep: (step: ChatStep) => void
  onDelta: (text: string) => void
  /** Bản nháp bị bác hoặc model chạy lại: xóa phần câu trả lời đã hiện */
  onReset: () => void
  /** Câu trả lời cuối cùng: thay toàn bộ phần đã hiện */
  onAnswer: (text: string) => void
  signal?: AbortSignal
}

/**
 * Gửi câu hỏi vào cuộc trò chuyện `conversationId` (null = tạo mới) và đọc SSE: `conversation` (id cuộc vừa tạo), `step` (bước đang/đã làm), `delta` (token câu trả lời), `reset` (xóa bản nháp),
 * `answer` (câu trả lời cuối), kết thúc bằng `done` hoặc `error`.
 */
export async function streamChat(
  message: string,
  conversationId: string | null,
  { onConversation, onStep, onDelta, onReset, onAnswer, signal }: StreamHandlers,
) {
  const response = await apiFetch('/chat', { method: 'POST', body: JSON.stringify({ message, conversationId }), signal })
  const reader = response.body!.pipeThrough(new TextDecoderStream()).getReader()
  let buffer = ''

  for (;;) {
    const { value, done } = await reader.read()
    if (done) return
    buffer += value

    let boundary
    while ((boundary = buffer.indexOf('\n\n')) !== -1) {
      const block = buffer.slice(0, boundary)
      buffer = buffer.slice(boundary + 2)

      let event = 'message'
      let data = ''
      for (const line of block.split('\n')) {
        if (line.startsWith('event:')) event = line.slice(6).trim()
        else if (line.startsWith('data:')) data += line.slice(5).trim()
      }
      const payload = data ? JSON.parse(data) : {}

      if (event === 'done') return
      if (event === 'error') throw new Error(payload.message)
      if (event === 'conversation') onConversation(payload)
      else if (event === 'step') onStep(payload as ChatStep)
      else if (event === 'delta') onDelta(payload.text)
      else if (event === 'reset') onReset()
      else if (event === 'answer') onAnswer(payload.text)
    }
  }
}
