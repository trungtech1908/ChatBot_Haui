import { BookOpen, CircleDollarSign, GraduationCap, Loader2, ScrollText, Sparkles, SquarePen } from 'lucide-react'
import { useEffect, useRef } from 'react'

import { useProfile } from '@/api/students'

import { ChatInput } from './ChatInput'
import { MessageBubble } from './MessageBubble'
import { useChat } from './useChat'

const SUGGESTIONS = [
  { icon: GraduationCap, text: 'Điều kiện để nhận học bổng khuyến khích học tập là gì?' },
  { icon: CircleDollarSign, text: 'Học phí một tín chỉ năm học 2025-2026 là bao nhiêu?' },
  { icon: ScrollText, text: 'Sinh viên bị cảnh báo học tập khi nào?' },
  { icon: BookOpen, text: 'Cần bao nhiêu tín chỉ để được tốt nghiệp?' },
]

function Welcome({ name, onPick }: { name?: string | null; onPick: (text: string) => void }) {
  return (
    <div className="flex flex-1 flex-col items-center justify-center py-10 text-center">
      <span className="mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 text-white shadow-lg shadow-indigo-500/30">
        <Sparkles size={26} />
      </span>
      <h2 className="text-2xl font-bold tracking-tight">Xin chào{name ? `, ${name}` : ''}!</h2>
      <p className="mt-2 max-w-md text-muted">Mình là trợ lý AI của HaUI. Hãy hỏi mình về quy chế, quy định, học phí hay học bổng nhé.</p>
      <div className="mt-8 grid w-full gap-3 sm:grid-cols-2">
        {SUGGESTIONS.map(({ icon: Icon, text }) => (
          <button
            key={text}
            onClick={() => onPick(text)}
            className="flex items-start gap-3 rounded-2xl border border-line bg-surface p-4 text-left text-sm transition hover:-translate-y-0.5 hover:border-primary/40 hover:shadow-md"
          >
            <Icon size={18} className="mt-0.5 shrink-0 text-primary" />
            {text}
          </button>
        ))}
      </div>
    </div>
  )
}

export function ChatPage() {
  const { messages, isLoading, isStreaming, send, stop, reset } = useChat()
  const name = useProfile().data?.fullName
  const bottomRef = useRef<HTMLDivElement>(null)
  const lastContent = messages.at(-1)?.content

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages.length, lastContent])

  async function handleReset() {
    if (confirm('Xóa toàn bộ lịch sử trò chuyện?')) await reset()
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex-1 overflow-y-auto">
        <div className="mx-auto flex min-h-full w-full max-w-3xl flex-col px-4 py-6">
          {isLoading ? (
            <Loader2 className="m-auto animate-spin text-primary" />
          ) : messages.length ? (
            <div className="space-y-6">
              {messages.map((message) => (
                <MessageBubble key={message.id} message={message} />
              ))}
            </div>
          ) : (
            <Welcome name={name} onPick={send} />
          )}
          <div ref={bottomRef} />
        </div>
      </div>

      <div className="border-t border-line bg-bg/80 backdrop-blur-md">
        <div className="mx-auto w-full max-w-3xl px-4 pt-3 pb-4">
          <ChatInput streaming={isStreaming} onSend={send} onStop={stop} />
          <div className="mt-2 flex items-center justify-between gap-2 px-2 text-xs text-muted">
            <span>Trợ lý AI có thể sai sót, hãy đối chiếu văn bản gốc khi cần.</span>
            {messages.length > 0 && (
              <button onClick={handleReset} disabled={isStreaming} className="inline-flex shrink-0 items-center gap-1 hover:text-fg disabled:opacity-50">
                <SquarePen size={13} /> Cuộc trò chuyện mới
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
