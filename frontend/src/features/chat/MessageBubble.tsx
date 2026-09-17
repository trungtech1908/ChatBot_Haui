import { Check, Copy, Sparkles, TriangleAlert } from 'lucide-react'
import { useState } from 'react'

import { cn } from '@/lib/cn'
import { formatTime } from '@/lib/format'
import type { ChatMessage } from '@/types/chat'

import { Markdown } from './Markdown'

function TypingDots() {
  return (
    <span className="inline-flex items-center gap-1 py-2">
      {[0, 150, 300].map((delay) => (
        <span key={delay} className="h-2 w-2 animate-bounce rounded-full bg-muted" style={{ animationDelay: `${delay}ms` }} />
      ))}
    </span>
  )
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)
  async function copy() {
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }
  return (
    <button onClick={copy} className="btn-ghost h-7 gap-1 px-2 text-xs" title="Sao chép">
      {copied ? <Check size={13} /> : <Copy size={13} />} {copied ? 'Đã chép' : 'Sao chép'}
    </button>
  )
}

export function MessageBubble({ message }: { message: ChatMessage }) {
  if (message.role === 'user') {
    return (
      <div className="flex animate-fade-up justify-end">
        <div className="max-w-[85%] md:max-w-[75%]">
          <div className="rounded-2xl rounded-br-md bg-primary px-4 py-2.5 text-white shadow-sm">
            <p className="leading-relaxed break-words whitespace-pre-wrap">{message.content}</p>
          </div>
          <p className="mt-1 text-right text-xs text-muted">{formatTime(message.createdAt)}</p>
        </div>
      </div>
    )
  }

  const streaming = message.status === 'streaming'
  const error = message.status === 'error'

  return (
    <div className="group flex animate-fade-up gap-3">
      <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 text-white shadow-sm">
        <Sparkles size={15} />
      </span>
      <div className="min-w-0 flex-1 pt-1">
        {error ? (
          <p className="flex items-center gap-2 text-rose-600 dark:text-rose-400">
            <TriangleAlert size={16} /> {message.content}
          </p>
        ) : message.content ? (
          <div className={cn(streaming && 'after:ml-0.5 after:inline-block after:h-4 after:w-1.5 after:animate-pulse after:bg-primary after:align-middle')}>
            <Markdown>{message.content}</Markdown>
          </div>
        ) : (
          <TypingDots />
        )}
        {!streaming && !error && message.content && (
          <div className="mt-1 flex items-center gap-2 opacity-0 transition group-hover:opacity-100">
            <CopyButton text={message.content} />
            <span className="text-xs text-muted">{formatTime(message.createdAt)}</span>
          </div>
        )}
      </div>
    </div>
  )
}
