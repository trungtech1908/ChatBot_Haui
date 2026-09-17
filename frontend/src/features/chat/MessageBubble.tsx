import { Bot, Loader2, User } from 'lucide-react'
import type { ReactNode } from 'react'

import { formatTime } from '@/lib/format'
import type { ChatMessage } from '@/types/chat'

export function BotBubble({ children }: { children: ReactNode }) {
  return (
    <div className="flex animate-fade-in justify-start">
      <div className="max-w-[85%] rounded-3xl rounded-tl-md border border-gray-200 bg-white p-4 shadow-md md:max-w-[75%] md:p-5">
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0 rounded-full bg-blue-100 p-2">
            <Bot className="text-blue-600" size={20} />
          </div>
          <div className="min-w-0 flex-1 text-sm leading-relaxed break-words whitespace-pre-wrap text-gray-800 md:text-base">
            {children}
          </div>
        </div>
      </div>
    </div>
  )
}

export function MessageBubble({ message }: { message: ChatMessage }) {
  if (message.role === 'user') {
    return (
      <div className="flex animate-fade-in justify-end">
        <div className="max-w-[85%] rounded-3xl rounded-tr-md bg-gradient-to-br from-blue-600 to-blue-700 p-4 text-white shadow-lg md:max-w-[75%] md:p-5">
          <div className="flex items-end gap-3">
            <div className="min-w-0 flex-1">
              <p className="text-sm leading-relaxed break-words whitespace-pre-wrap md:text-base">{message.content}</p>
              <span className="mt-2 block text-xs text-blue-200">{formatTime(message.createdAt)}</span>
            </div>
            <div className="flex-shrink-0 rounded-full bg-white/20 p-2">
              <User size={14} />
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <BotBubble>
      <span className={message.status === 'error' ? 'text-red-600' : ''}>{message.content}</span>
      {message.status === 'streaming' && !message.content && (
        <span className="inline-flex animate-pulse items-center gap-2 text-sm text-gray-400">
          <Loader2 className="animate-spin" size={14} /> đang trả lời...
        </span>
      )}
    </BotBubble>
  )
}
