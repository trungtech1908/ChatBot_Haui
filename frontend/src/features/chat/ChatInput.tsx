import { ArrowUp, Square } from 'lucide-react'
import { useRef, useState, type KeyboardEvent } from 'react'

interface Props {
  streaming: boolean
  onSend: (text: string) => void
  onStop: () => void
}

export function ChatInput({ streaming, onSend, onStop }: Props) {
  const [text, setText] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  function resize(el: HTMLTextAreaElement) {
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`
  }

  function submit() {
    const value = text.trim()
    if (!value || streaming) return
    onSend(value)
    setText('')
    if (textareaRef.current) textareaRef.current.style.height = 'auto'
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault()
      submit()
    }
  }

  return (
    <div className="rounded-3xl border border-line bg-surface p-2 shadow-lg shadow-slate-900/5 transition focus-within:border-primary focus-within:ring-4 focus-within:ring-primary-soft">
      <div className="flex items-end gap-2">
        <textarea
          ref={textareaRef}
          value={text}
          rows={1}
          autoFocus
          placeholder="Hỏi về quy chế, học phí, học bổng..."
          onChange={(e) => {
            setText(e.target.value)
            resize(e.target)
          }}
          onKeyDown={handleKeyDown}
          className="max-h-[200px] flex-1 resize-none bg-transparent px-3 py-2.5 leading-relaxed outline-none placeholder:text-muted"
        />
        {streaming ? (
          <button onClick={onStop} className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-fg text-bg transition hover:opacity-80" title="Dừng">
            <Square size={14} fill="currentColor" />
          </button>
        ) : (
          <button
            onClick={submit}
            disabled={!text.trim()}
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary text-white transition hover:bg-primary-hover disabled:bg-surface-2 disabled:text-muted"
            title="Gửi (Enter)"
          >
            <ArrowUp size={18} />
          </button>
        )}
      </div>
    </div>
  )
}
