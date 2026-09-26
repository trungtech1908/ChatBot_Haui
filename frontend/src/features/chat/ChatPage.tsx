import { ArrowUp, History, Square, X } from 'lucide-react'
import { useCallback, useEffect, useRef, useState, type KeyboardEvent } from 'react'
import { useNavigate, useParams } from 'react-router'

import { PageHeader } from '@/components/ui/PageHeader'
import { cn } from '@/lib/cn'
import { formatTime } from '@/lib/format'
import type { ChatMessage } from '@/types/chat'

import { ConversationList } from './ConversationList'
import { Markdown } from './Markdown'
import { Steps } from './Steps'
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
  const streaming = message.status === 'streaming'
  return (
    <div className="max-w-[90%]">
      {message.steps && (message.steps.length > 0 || streaming) && (
        <Steps steps={message.steps} startedAt={message.createdAt} finishedAt={message.finishedAt} streaming={streaming} />
      )}
      {message.status === 'error' ? (
        <p className="text-danger">{message.content}</p>
      ) : message.content ? (
        <Markdown>{message.content}</Markdown>
      ) : null}
      {!streaming && message.content && <p className="mt-1 text-xs text-muted">{formatTime(message.createdAt)}</p>}
    </div>
  )
}

export function ChatPage() {
  const { conversationId = null } = useParams()
  const navigate = useNavigate()
  const onCreated = useCallback((id: string) => navigate(`/chat/${id}`, { replace: true }), [navigate])
  const { messages, isLoading, notFound, isStreaming, send, stop } = useChat(conversationId, onCreated)
  const [text, setText] = useState('')
  const [drawer, setDrawer] = useState(false)
  const listRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const lastContent = messages.at(-1)?.content
  const lastSteps = messages.at(-1)?.steps?.length

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages.length, lastContent, lastSteps])

  useEffect(() => {
    inputRef.current?.focus()
  }, [conversationId])

  function submit(value = text) {
    const question = value.trim()
    if (!question || isStreaming || notFound) return
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

  const list = (
    <ConversationList
      activeId={conversationId}
      disabled={isStreaming}
      onNavigate={() => setDrawer(false)}
      onActiveDeleted={() => navigate('/chat', { replace: true })}
    />
  )

  return (
    <>
      <PageHeader
        title="Hỏi đáp quy chế"
        description="Tra cứu quy chế đào tạo, học phí, học bổng và dữ liệu học vụ của bạn"
        actions={
          <button onClick={() => setDrawer(true)} className="btn-secondary lg:hidden">
            <History size={15} />
            Lịch sử
          </button>
        }
      />

      <div className="card relative flex h-[calc(100dvh-12.5rem)] min-h-[440px] overflow-hidden">
        <aside className="hidden w-64 shrink-0 border-r border-line bg-surface-2 lg:block">{list}</aside>

        {drawer && (
          <div className="absolute inset-0 z-20 flex lg:hidden">
            <aside className="w-72 max-w-[85%] border-r border-line bg-surface shadow-[var(--shadow-md)]">
              <div className="flex items-center justify-between border-b border-line px-3 py-2">
                <span className="text-[13px] font-medium">Lịch sử trò chuyện</span>
                <button onClick={() => setDrawer(false)} className="btn-ghost h-7 w-7 px-0" title="Đóng"><X size={15} /></button>
              </div>
              <div className="h-[calc(100%-45px)]">{list}</div>
            </aside>
            <button aria-label="Đóng lịch sử" onClick={() => setDrawer(false)} className="flex-1 bg-black/20" />
          </div>
        )}

        <div className="flex min-w-0 flex-1 flex-col">
          <div ref={listRef} className="flex-1 space-y-5 overflow-y-auto px-5 py-5">
            {notFound ? (
              <div className="flex h-full flex-col items-center justify-center text-center">
                <p className="font-medium">Không tìm thấy cuộc trò chuyện</p>
                <p className="mt-1 text-muted">Cuộc trò chuyện này đã bị xóa hoặc không thuộc tài khoản của bạn.</p>
                <button onClick={() => navigate('/chat')} className="btn-secondary mt-4">Bắt đầu cuộc mới</button>
              </div>
            ) : isLoading ? (
              <p className="text-muted">Đang tải…</p>
            ) : messages.length ? (
              messages.map((message) => <Message key={message.id} message={message} />)
            ) : (
              <div className="flex h-full flex-col items-center justify-center text-center">
                <p className="font-medium">Bạn muốn hỏi gì?</p>
                <p className="mt-1 max-w-sm text-muted">Câu trả lời dựa trên văn bản và dữ liệu của trường, nên đối chiếu văn bản gốc khi làm thủ tục.</p>
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
            <div className={cn(
              'flex items-end gap-2 rounded-xl border border-line bg-surface px-3 py-2 transition focus-within:border-brand focus-within:ring-3 focus-within:ring-brand/15',
              notFound && 'opacity-50',
            )}>
              <textarea
                ref={inputRef}
                value={text}
                rows={1}
                disabled={notFound}
                placeholder={conversationId ? 'Hỏi tiếp…' : 'Nhập câu hỏi để bắt đầu cuộc trò chuyện mới…'}
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
                <button onClick={() => submit()} disabled={!text.trim() || notFound} className="btn-primary h-8 w-8 shrink-0 px-0" title="Gửi">
                  <ArrowUp size={16} />
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
