import type { LucideIcon } from 'lucide-react'
import { Inbox } from 'lucide-react'

export function EmptyState({ message, icon: Icon = Inbox }: { message: string; icon?: LucideIcon }) {
  return (
    <div className="rounded-xl bg-white p-10 text-center text-gray-500 shadow-sm">
      <Icon className="mx-auto mb-3 text-gray-300" size={40} />
      {message}
    </div>
  )
}
