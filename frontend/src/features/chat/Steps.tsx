import { AlertCircle, CheckCircle2, ChevronRight, LoaderCircle } from 'lucide-react'
import { useEffect, useState } from 'react'

import { cn } from '@/lib/cn'
import type { ChatStep } from '@/types/chat'

function useElapsed(since: string, until?: string) {
  const [now, setNow] = useState(() => Date.now())
  useEffect(() => {
    if (until) return
    const timer = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(timer)
  }, [until])
  return Math.max(0, Math.round(((until ? new Date(until).getTime() : now) - new Date(since).getTime()) / 1000))
}

function StepIcon({ status }: { status: ChatStep['status'] }) {
  if (status === 'running') return <LoaderCircle size={15} className="animate-spin text-brand" />
  if (status === 'done') return <CheckCircle2 size={15} className="text-success" />
  return <AlertCircle size={15} className="text-warning" />
}

/** Các bước chatbot đang/đã làm cho câu hỏi: mở khi đang xử lý, thu gọn thành một dòng khi xong. */
export function Steps({ steps, startedAt, finishedAt, streaming }: {
  steps: ChatStep[]
  startedAt: string
  finishedAt?: string
  streaming: boolean
}) {
  const [open, setOpen] = useState(false)
  const seconds = useElapsed(startedAt, finishedAt)
  const expanded = streaming || open
  const current = steps.findLast((s) => s.status === 'running')

  return (
    <div className="mb-2">
      <button
        onClick={() => setOpen((v) => !v)}
        disabled={streaming}
        aria-expanded={expanded}
        className="inline-flex items-center gap-1.5 rounded-md py-0.5 text-[13px] text-muted transition-colors hover:text-fg disabled:hover:text-muted"
      >
        {streaming ? (
          <>
            <LoaderCircle size={14} className="animate-spin text-brand" />
            <span className="text-fg-2">{current?.label ?? 'Đang xử lý'}…</span>
          </>
        ) : (
          <>
            <ChevronRight size={14} className={cn('transition-transform', open && 'rotate-90')} />
            Đã xử lý qua {steps.length} bước
          </>
        )}
        <span className="tabular-nums">· {seconds} giây</span>
      </button>

      {expanded && steps.length > 0 && (
        <ol className="mt-2 space-y-2 border-l border-line pl-3.5">
          {steps.map((step) => (
            <li key={step.id} className="flex gap-2.5">
              <span className="mt-px shrink-0"><StepIcon status={step.status} /></span>
              <div className="min-w-0 text-[13px] leading-5">
                <p className={step.status === 'running' ? 'font-medium text-fg' : 'text-fg-2'}>{step.label}</p>
                {step.detail && <p className="text-muted">{step.detail}</p>}
              </div>
            </li>
          ))}
        </ol>
      )}
    </div>
  )
}
