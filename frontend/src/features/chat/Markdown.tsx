import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

export function Markdown({ children }: { children: string }) {
  return (
    <div className="prose prose-sm max-w-none prose-zinc dark:prose-invert prose-p:leading-relaxed prose-a:text-brand prose-li:my-0.5 prose-table:text-[13px] prose-th:font-medium">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{children}</ReactMarkdown>
    </div>
  )
}
