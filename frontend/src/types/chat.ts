export type ChatRole = 'user' | 'bot'

export interface ChatMessage {
  id: number | string
  role: ChatRole
  content: string
  createdAt: string
  status?: 'streaming' | 'error'
}
