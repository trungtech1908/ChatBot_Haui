import type { ReactNode } from 'react'

export function InfoRow({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div>
      <p className="text-sm text-gray-500">{label}</p>
      <p className="font-medium text-gray-800">{children ?? '---'}</p>
    </div>
  )
}
