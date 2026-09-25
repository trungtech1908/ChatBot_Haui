export type ChatRole = 'user' | 'bot'

export interface ChatMessage {
  id: number | string
  role: ChatRole
  content: string
  createdAt: string
  status?: 'streaming' | 'error'
  /** Bước xử lý hiện tại khi chưa có câu trả lời (server gửi qua `event: status`) */
  stage?: string
}
