import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

export function Markdown({ children }: { children: string }) {
  return (
    <div className="prose prose-sm max-w-none text-fg prose-slate dark:prose-invert prose-headings:text-fg prose-p:my-2 prose-a:text-brand prose-strong:text-fg prose-li:my-0.5 prose-table:my-3 prose-th:border prose-th:border-line prose-th:bg-surface-2 prose-th:px-2 prose-th:py-1 prose-td:border prose-td:border-line prose-td:px-2 prose-td:py-1">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{children}</ReactMarkdown>
    </div>
  )
}
