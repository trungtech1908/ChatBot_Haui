import { Inbox } from 'lucide-react'

export function EmptyState({ message }: { message: string }) {
  return (
    <div className="card flex min-h-44 flex-col items-center justify-center gap-2 px-6 py-10 text-center text-muted">
      <Inbox size={22} strokeWidth={1.5} />
      {message}
    </div>
  )
}
