import { apiFetch, apiJson } from '@/lib/api'
import type { ChatMessage } from '@/types/chat'

export const fetchMessages = () => apiJson<ChatMessage[]>('/chat/messages')

export const clearMessages = () => apiJson<void>('/chat/messages', { method: 'DELETE' })

interface StreamHandlers {
  onDelta: (text: string) => void
  onStatus?: (stage: string) => void
  signal?: AbortSignal
}

/**
 * Gửi câu hỏi và đọc SSE: `event: status` + `{"stage"}` cho từng bước xử lý, `data: {"delta"}` là nội dung
 * câu trả lời (đã qua kiểm định), kết thúc bằng `event: done` hoặc `event: error`.
 */
export async function streamChat(message: string, { onDelta, onStatus, signal }: StreamHandlers) {
  const response = await apiFetch('/chat', { method: 'POST', body: JSON.stringify({ message }), signal })
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
      if (event === 'status') onStatus?.(payload.stage)
      else if (payload.delta) onDelta(payload.delta)
    }
  }
}
