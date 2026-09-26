import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useCallback, useEffect, useRef, useState } from 'react'

import { fetchMessages, streamChat } from '@/api/chat'
import { ApiError } from '@/lib/api'
import type { ChatMessage, ChatStep, Conversation } from '@/types/chat'

export const CONVERSATIONS_KEY = ['chat', 'conversations']
export const messagesKey = (conversationId: string) => ['chat', 'messages', conversationId]
const NO_MESSAGES: ChatMessage[] = []

function upsertStep(steps: ChatStep[], step: ChatStep) {
  const i = steps.findIndex((s) => s.id === step.id)
  return i < 0 ? [...steps, step] : steps.map((s, j) => (j === i ? step : s))
}

/**
 * Tin nhắn của một cuộc trò chuyện: lịch sử từ server + tin nhắn gửi trong lần mở này (đang/đã stream).
 * conversationId null = cuộc mới; server tạo cuộc ở câu hỏi đầu tiên, `onCreated` nhận id để đổi URL.
 */
export function useChat(conversationId: string | null, onCreated: (id: string) => void) {
  const queryClient = useQueryClient()
  const history = useQuery({
    queryKey: messagesKey(conversationId ?? ''),
    queryFn: () => fetchMessages(conversationId!),
    enabled: !!conversationId,
    staleTime: Infinity, // chỉ tải lại khi đã gửi thêm tin (invalidate), không tải lại mỗi lần chuyển cuộc
  })
  const [session, setSession] = useState<ChatMessage[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const abortRef = useRef<AbortController | null>(null)
  // id cuộc vừa được tạo bởi chính lần gửi đang chạy: đổi URL sang id này không phải là chuyển cuộc
  const createdRef = useRef<string | null>(null)

  useEffect(() => () => abortRef.current?.abort(), [])

  useEffect(() => {
    if (conversationId && conversationId === createdRef.current) {
      createdRef.current = null // chỉ bỏ qua đúng lần đổi URL ngay sau khi tạo
      return
    }
    abortRef.current?.abort()
    setSession([])
  }, [conversationId])

  const updateMessage = (id: string, patch: (m: ChatMessage) => Partial<ChatMessage>) =>
    setSession((list) => list.map((m) => (m.id === id ? { ...m, ...patch(m) } : m)))

  const send = useCallback(async (text: string) => {
    const now = new Date().toISOString()
    const botId = crypto.randomUUID()
    setSession((list) => [
      ...list,
      { id: crypto.randomUUID(), role: 'user', content: text, createdAt: now },
      { id: botId, role: 'bot', content: '', createdAt: now, status: 'streaming', steps: [] },
    ])
    setIsStreaming(true)
    const controller = new AbortController()
    abortRef.current = controller
    let target = conversationId

    try {
      await streamChat(text, conversationId, {
        signal: controller.signal,
        onConversation: ({ id, title }) => {
          target = id
          createdRef.current = id
          // Tin nhắn của cuộc mới đang nằm trong session: đặt sẵn lịch sử rỗng để không tải trùng từ server
          queryClient.setQueryData(messagesKey(id), [])
          queryClient.setQueryData<Conversation[]>(CONVERSATIONS_KEY, (list = []) => [
            { id, title, createdAt: now, updatedAt: now }, ...list,
          ])
          onCreated(id)
        },
        onStep: (step) => updateMessage(botId, (m) => ({ steps: upsertStep(m.steps ?? [], step) })),
        onDelta: (delta) => updateMessage(botId, (m) => ({ content: m.content + delta })),
        onReset: () => updateMessage(botId, () => ({ content: '' })),
        onAnswer: (answer) => updateMessage(botId, () => ({ content: answer })),
      })
      updateMessage(botId, () => ({ status: undefined, finishedAt: new Date().toISOString() }))
    } catch (error) {
      if (controller.signal.aborted) {
        updateMessage(botId, () => ({ status: undefined, finishedAt: new Date().toISOString() }))
        return
      }
      const message = error instanceof Error ? error.message : 'Lỗi kết nối, vui lòng thử lại sau'
      updateMessage(botId, () => ({ content: message, status: 'error', finishedAt: new Date().toISOString() }))
    } finally {
      setIsStreaming(false)
      // Server đã lưu tin nhắn: đánh dấu cũ để lần mở lại cuộc này tải từ DB; thứ tự cuộc trò chuyện đổi theo hoạt động
      if (target) queryClient.invalidateQueries({ queryKey: messagesKey(target), refetchType: 'none' })
      queryClient.invalidateQueries({ queryKey: CONVERSATIONS_KEY })
    }
  }, [conversationId, onCreated, queryClient])

  // Dừng hiển thị; server vẫn lưu câu trả lời đầy đủ vào lịch sử
  const stop = useCallback(() => abortRef.current?.abort(), [])

  return {
    messages: [...(conversationId ? history.data ?? NO_MESSAGES : NO_MESSAGES), ...session],
    isLoading: !!conversationId && history.isPending,
    notFound: history.error instanceof ApiError && history.error.status === 404,
    isStreaming,
    send,
    stop,
  }
}
