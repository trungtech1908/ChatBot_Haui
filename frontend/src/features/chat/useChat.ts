import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useCallback, useEffect, useRef, useState } from 'react'

import { clearMessages, fetchMessages, streamChat } from '@/api/chat'
import type { ChatMessage } from '@/types/chat'

const HISTORY_KEY = ['chat', 'messages']
const NO_MESSAGES: ChatMessage[] = []

/** Lịch sử chat từ server + tin nhắn gửi trong phiên hiện tại (đang/đã stream). */
export function useChat() {
  const queryClient = useQueryClient()
  const history = useQuery({ queryKey: HISTORY_KEY, queryFn: fetchMessages })
  const [session, setSession] = useState<ChatMessage[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const abortRef = useRef<AbortController | null>(null)

  useEffect(() => () => abortRef.current?.abort(), [])

  const updateMessage = (id: string, patch: (m: ChatMessage) => Partial<ChatMessage>) =>
    setSession((list) => list.map((m) => (m.id === id ? { ...m, ...patch(m) } : m)))

  const send = useCallback(async (text: string) => {
    const now = new Date().toISOString()
    const botId = crypto.randomUUID()
    setSession((list) => [
      ...list,
      { id: crypto.randomUUID(), role: 'user', content: text, createdAt: now },
      { id: botId, role: 'bot', content: '', createdAt: now, status: 'streaming' },
    ])
    setIsStreaming(true)
    const controller = new AbortController()
    abortRef.current = controller

    try {
      await streamChat(text, {
        signal: controller.signal,
        onDelta: (delta) => updateMessage(botId, (m) => ({ content: m.content + delta })),
      })
      updateMessage(botId, () => ({ status: undefined }))
    } catch (error) {
      if (controller.signal.aborted) {
        updateMessage(botId, () => ({ status: undefined }))
        return
      }
      const message = error instanceof Error ? error.message : 'Lỗi kết nối, vui lòng thử lại sau'
      updateMessage(botId, () => ({ content: message, status: 'error' }))
    } finally {
      setIsStreaming(false)
      // Server đã lưu tin nhắn; đánh dấu cũ để lần mở trang sau tải lại từ DB
      queryClient.invalidateQueries({ queryKey: HISTORY_KEY, refetchType: 'none' })
    }
  }, [queryClient])

  // Dừng hiển thị; server vẫn lưu câu trả lời đầy đủ vào lịch sử
  const stop = useCallback(() => abortRef.current?.abort(), [])

  const reset = useCallback(async () => {
    abortRef.current?.abort()
    await clearMessages()
    queryClient.setQueryData(HISTORY_KEY, [])
    setSession([])
  }, [queryClient])

  return {
    messages: [...(history.data ?? NO_MESSAGES), ...session],
    isLoading: history.isPending,
    isStreaming,
    send,
    stop,
    reset,
  }
}
