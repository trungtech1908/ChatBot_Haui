import { SendHorizontal } from 'lucide-react'
import { useRef, useState, type KeyboardEvent } from 'react'

export function ChatInput({ disabled, onSend }: { disabled: boolean; onSend: (text: string) => void }) {
  const [text, setText] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  function submit() {
    const value = text.trim()
    if (!value || disabled) return
    onSend(value)
    setText('')
    if (textareaRef.current) textareaRef.current.style.height = 'auto'
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      submit()
    }
  }

  return (
    <div className="border-t-2 border-gray-200 bg-white p-3 shadow-lg md:p-4">
      <div className="relative">
        <textarea
          ref={textareaRef}
          value={text}
          rows={1}
          placeholder="Nhập câu hỏi của bạn..."
          onChange={(e) => {
            setText(e.target.value)
            e.target.style.height = 'auto'
            e.target.style.height = `${Math.min(e.target.scrollHeight, 150)}px`
          }}
          onKeyDown={handleKeyDown}
          className="w-full resize-none rounded-2xl border-2 border-transparent bg-gray-100 px-4 py-3 pr-14 text-sm transition focus:border-blue-400 focus:bg-white focus:ring-4 focus:ring-blue-300 focus:outline-none md:px-6 md:py-4 md:text-base"
        />
        <button
          onClick={submit}
          disabled={disabled || !text.trim()}
          title="Gửi (Enter)"
          className="absolute right-3 bottom-3.5 flex h-10 w-10 items-center justify-center rounded-full bg-blue-600 text-white shadow-lg transition hover:scale-110 hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <SendHorizontal size={18} />
        </button>
      </div>
      <p className="mt-2 text-center text-xs text-gray-500">
        Nhấn <kbd className="rounded bg-gray-200 px-1.5 py-0.5">Enter</kbd> để gửi,{' '}
        <kbd className="rounded bg-gray-200 px-1.5 py-0.5">Shift + Enter</kbd> để xuống dòng
      </p>
    </div>
  )
}
