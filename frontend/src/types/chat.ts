export type ChatRole = 'user' | 'bot'

/** Một bước xử lý server báo qua `event: step` (cùng id là cập nhật trạng thái) */
export interface ChatStep {
  id: string
  label: string
  status: 'running' | 'done' | 'error'
  detail: string
}

export interface ChatMessage {
  id: number | string
  role: ChatRole
  content: string
  createdAt: string
  status?: 'streaming' | 'error'
  /** Các bước xử lý của câu trả lời gửi trong phiên này (tin nhắn tải từ lịch sử không có) */
  steps?: ChatStep[]
  /** Thời điểm kết thúc xử lý, để hiện tổng thời gian */
  finishedAt?: string
}

export interface Conversation {
  id: string
  title: string
  createdAt: string
  updatedAt: string
}
