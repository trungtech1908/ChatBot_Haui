import type { ReactNode } from 'react'

export type Tone = 'gray' | 'green' | 'blue' | 'yellow' | 'orange' | 'red' | 'purple'

const tones: Record<Tone, string> = {
  gray: 'bg-gray-100 text-gray-700 border-gray-200',
  green: 'bg-green-100 text-green-700 border-green-200',
  blue: 'bg-blue-100 text-blue-700 border-blue-200',
  yellow: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  orange: 'bg-orange-100 text-orange-700 border-orange-200',
  red: 'bg-red-100 text-red-700 border-red-200',
  purple: 'bg-purple-100 text-purple-700 border-purple-200',
}

export function Badge({ tone = 'gray', children }: { tone?: Tone; children: ReactNode }) {
  return (
    <span className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-bold ${tones[tone]}`}>
      {children}
    </span>
  )
}
