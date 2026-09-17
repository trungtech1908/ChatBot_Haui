import { useEffect, useRef, useState, type KeyboardEvent } from 'react'

import { PageHeader } from '@/components/ui/PageHeader'
import { cn } from '@/lib/cn'
import { formatTime } from '@/lib/format'
import type { ChatMessage } from '@/types/chat'

import { Markdown } from './Markdown'
import { useChat } from './useChat'

const SUGGESTIONS = [
  'Điều kiện để nhận học bổng khuyến khích học tập là gì?',
  'Học phí một tín chỉ năm học 2025–2026 là bao nhiêu?',
  'Khi nào sinh viên bị cảnh báo học tập?',
  'Cần tích lũy bao nhiêu tín chỉ để tốt nghiệp?',
]

function Message({ message }: { message: ChatMessage }) {
  const isUser = message.role === 'user'
  return (
    <div className={cn('border-b border-line px-4 py-3 last:border-b-0', isUser && 'bg-surface-2')}>
      <p className="mb-1 text-xs text-muted">
        <span className={cn('font-semibold', isUser ? 'text-fg' : 'text-brand')}>{isUser ? 'Bạn' : 'Trợ lý'}</span>
        {' · '}
        {message.status === 'streaming' ? 'đang trả lời…' : formatTime(message.createdAt)}
      </p>
      {isUser ? (
        <p className="text-sm whitespace-pre-wrap">{message.content}</p>
      ) : message.status === 'error' ? (
        <p className="text-sm text-accent">{message.content}</p>
      ) : message.content ? (
        <Markdown>{message.content}</Markdown>
      ) : (
        <p className="text-sm text-muted">…</p>
      )}
    </div>
  )
}

export function ChatPage() {
  const { messages, isLoading, isStreaming, send, stop, reset } = useChat()
  const [text, setText] = useState('')
  const listRef = useRef<HTMLDivElement>(null)
  const lastContent = messages.at(-1)?.content

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight })
  }, [messages.length, lastContent])

  function submit(value = text) {
    const question = value.trim()
    if (!question || isStreaming) return
    send(question)
    setText('')
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
        section="Hỗ trợ"
        title="Hỏi đáp quy chế"
        actions={
          messages.length > 0 && (
            <button onClick={handleReset} disabled={isStreaming} className="btn-outline">
              Xóa lịch sử
            </button>
          )
        }
      />

      <div className="flex h-[calc(100dvh-13rem)] min-h-[420px] flex-col rounded-md border border-line bg-surface">
        <div ref={listRef} className="flex-1 overflow-y-auto">
          {isLoading ? (
            <p className="p-4 text-sm text-muted">Đang tải lịch sử…</p>
          ) : messages.length ? (
            messages.map((message) => <Message key={message.id} message={message} />)
          ) : (
            <div className="p-4 text-sm">
              <p className="text-muted">
                Tra cứu nhanh quy chế đào tạo, học phí, học bổng, khen thưởng – kỷ luật dựa trên văn bản của nhà trường. Câu trả lời chỉ
                mang tính tham khảo, cần đối chiếu văn bản gốc khi làm thủ tục.
              </p>
              <p className="mt-4 mb-1.5 font-medium">Câu hỏi thường gặp</p>
              <ul className="list-disc space-y-1 pl-5">
                {SUGGESTIONS.map((question) => (
                  <li key={question}>
                    <button onClick={() => submit(question)} className="text-left link">
                      {question}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        <div className="border-t border-line p-3">
          <textarea
            value={text}
            rows={2}
            placeholder="Nhập câu hỏi (Enter để gửi, Shift + Enter để xuống dòng)"
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            className="input resize-none"
          />
          <div className="mt-2 flex justify-end gap-2">
            {isStreaming ? (
              <button onClick={stop} className="btn-outline">Dừng</button>
            ) : (
              <button onClick={() => submit()} disabled={!text.trim()} className="btn-primary">Gửi câu hỏi</button>
            )}
          </div>
        </div>
      </div>
    </>
  )
}
