import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

export function Markdown({ children }: { children: string }) {
  return (
    <div className="prose prose-sm max-w-none prose-slate dark:prose-invert prose-headings:font-semibold prose-a:text-primary prose-p:leading-relaxed prose-pre:rounded-xl prose-table:text-sm md:prose-base">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{children}</ReactMarkdown>
    </div>
  )
}
