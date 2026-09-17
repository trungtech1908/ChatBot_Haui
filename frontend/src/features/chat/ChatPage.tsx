import { ArrowUp, Square } from 'lucide-react'
import { useEffect, useRef, useState, type KeyboardEvent } from 'react'

import { PageHeader } from '@/components/ui/PageHeader'
import { formatTime } from '@/lib/format'
import type { ChatMessage } from '@/types/chat'

import { Markdown } from './Markdown'
import { useChat } from './useChat'

const SUGGESTIONS = [
  'Điều kiện nhận học bổng khuyến khích học tập?',
  'Học phí một tín chỉ năm 2025–2026?',
  'Khi nào bị cảnh báo học tập?',
  'Cần bao nhiêu tín chỉ để tốt nghiệp?',
]

function Message({ message }: { message: ChatMessage }) {
  if (message.role === 'user') {
    return (
      <div className="flex justify-end">
        <div className="max-w-[80%] rounded-2xl rounded-br-md bg-hover px-3.5 py-2 whitespace-pre-wrap">{message.content}</div>
      </div>
    )
  }
  return (
    <div className="max-w-[90%]">
      {message.status === 'error' ? (
        <p className="text-danger">{message.content}</p>
      ) : message.content ? (
        <Markdown>{message.content}</Markdown>
      ) : (
        <p className="animate-pulse text-muted">Đang tìm trong quy chế…</p>
      )}
      {message.status !== 'streaming' && message.content && <p className="mt-1 text-xs text-muted">{formatTime(message.createdAt)}</p>}
    </div>
  )
}

export function ChatPage() {
  const { messages, isLoading, isStreaming, send, stop, reset } = useChat()
  const [text, setText] = useState('')
  const listRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const lastContent = messages.at(-1)?.content

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages.length, lastContent])

  function submit(value = text) {
    const question = value.trim()
    if (!question || isStreaming) return
    send(question)
    setText('')
    if (inputRef.current) inputRef.current.style.height = 'auto'
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault()
      submit()
    }
  }

  async function handleReset() {
    if (confirm('Xóa toàn bộ lịch sử hỏi đáp?')) await reset()
  }

  return (
    <>
      <PageHeader
        title="Hỏi đáp quy chế"
        description="Tra cứu quy chế đào tạo, học phí, học bổng của nhà trường"
        actions={messages.length > 0 && <button onClick={handleReset} disabled={isStreaming} className="btn-secondary">Xóa lịch sử</button>}
      />

      <div className="card flex h-[calc(100dvh-12.5rem)] min-h-[440px] flex-col overflow-hidden">
        <div ref={listRef} className="flex-1 space-y-5 overflow-y-auto px-5 py-5">
          {isLoading ? (
            <p className="text-muted">Đang tải…</p>
          ) : messages.length ? (
            messages.map((message) => <Message key={message.id} message={message} />)
          ) : (
            <div className="flex h-full flex-col items-center justify-center text-center">
              <p className="font-medium">Bạn muốn hỏi gì?</p>
              <p className="mt-1 max-w-sm text-muted">Câu trả lời dựa trên văn bản của trường, nên đối chiếu văn bản gốc khi làm thủ tục.</p>
              <div className="mt-5 flex max-w-lg flex-wrap justify-center gap-2">
                {SUGGESTIONS.map((q) => (
                  <button key={q} onClick={() => submit(q)} className="btn-secondary h-8 rounded-full px-3 text-[13px] font-normal">
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="border-t border-line p-3">
          <div className="flex items-end gap-2 rounded-xl border border-line bg-surface px-3 py-2 transition focus-within:border-brand focus-within:ring-3 focus-within:ring-brand/15">
            <textarea
              ref={inputRef}
              value={text}
              rows={1}
              placeholder="Nhập câu hỏi…"
              onChange={(e) => {
                setText(e.target.value)
                e.target.style.height = 'auto'
                e.target.style.height = `${Math.min(e.target.scrollHeight, 160)}px`
              }}
              onKeyDown={handleKeyDown}
              className="max-h-40 flex-1 resize-none bg-transparent py-1 outline-none placeholder:text-muted"
            />
            {isStreaming ? (
              <button onClick={stop} className="btn-secondary h-8 w-8 shrink-0 px-0" title="Dừng">
                <Square size={12} fill="currentColor" />
              </button>
            ) : (
              <button onClick={() => submit()} disabled={!text.trim()} className="btn-primary h-8 w-8 shrink-0 px-0" title="Gửi">
                <ArrowUp size={16} />
              </button>
            )}
          </div>
        </div>
      </div>
    </>
  )
}
