import type { ReactNode } from 'react'

export function PageHeader({ section, title, actions }: { section?: string; title: string; actions?: ReactNode }) {
  return (
    <div className="mb-5 flex flex-col gap-3 border-b border-line pb-4 sm:flex-row sm:items-end sm:justify-between">
      <div>
        {section && <p className="text-xs font-medium tracking-wide text-muted uppercase">{section}</p>}
        <h1 className="mt-0.5 text-[22px] leading-tight font-semibold">{title}</h1>
      </div>
      {actions}
    </div>
  )
}
