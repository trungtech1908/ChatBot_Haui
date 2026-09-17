import { Bot, Loader2, Trash2 } from 'lucide-react'
import { useEffect, useRef } from 'react'

import { useProfile } from '@/api/students'

import { ChatInput } from './ChatInput'
import { BotBubble, MessageBubble } from './MessageBubble'
import { useChat } from './useChat'

export function ChatPage() {
  const { messages, isLoading, isStreaming, send, reset } = useChat()
  const name = useProfile().data?.fullName
  const bottomRef = useRef<HTMLDivElement>(null)

  const lastContent = messages.at(-1)?.content

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages.length, lastContent])

  async function handleReset() {
    if (confirm('Bạn có chắc chắn muốn xóa toàn bộ lịch sử chat?')) await reset()
  }

  return (
    <div className="flex h-[calc(100vh-7rem)] min-h-[500px] flex-col overflow-hidden rounded-xl bg-white shadow-md md:h-[calc(100vh-8rem)]">
      <div className="flex items-center justify-between bg-gradient-to-r from-blue-600 via-blue-700 to-indigo-700 p-4 text-white shadow-lg md:p-6">
        <div className="flex items-center gap-3 md:gap-4">
          <div className="rounded-full bg-white/20 p-2 md:p-3">
            <Bot size={28} />
          </div>
          <div>
            <h2 className="text-lg font-bold md:text-2xl">Trợ lý ảo Sinh viên</h2>
            <p className="mt-1 text-xs text-blue-100 md:text-sm">Hỏi đáp quy chế, quy định, học phí của trường</p>
          </div>
        </div>
        <button
          onClick={handleReset}
          disabled={isStreaming}
          title="Xóa lịch sử chat"
          className="rounded-full bg-white/20 p-2 transition hover:scale-110 hover:bg-white/30 disabled:opacity-50 md:p-3"
        >
          <Trash2 size={20} />
        </button>
      </div>

      <div className="flex-1 space-y-4 overflow-y-auto bg-gradient-to-b from-gray-50 to-white p-4 md:space-y-6 md:p-6">
        <BotBubble>
          Xin chào <span className="font-bold text-blue-600">{name}</span>! 👋{'\n'}
          Tôi là trợ lý ảo của bạn. Tôi có thể giúp bạn trả lời các câu hỏi về quy định, quy chế, học phí và các thông tin
          khác của trường. Hãy đặt câu hỏi cho tôi nhé!
        </BotBubble>
        {isLoading ? (
          <Loader2 className="mx-auto animate-spin text-blue-600" />
        ) : (
          messages.map((message) => <MessageBubble key={message.id} message={message} />)
        )}
        <div ref={bottomRef} />
      </div>

      <ChatInput disabled={isStreaming} onSend={send} />
    </div>
  )
}
