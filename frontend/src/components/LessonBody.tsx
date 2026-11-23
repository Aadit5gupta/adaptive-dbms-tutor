import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

export function LessonBody({ body }: { body: string }) {
  return <div className="lesson-markdown overflow-x-auto">
    <ReactMarkdown remarkPlugins={[remarkGfm]} skipHtml>{body}</ReactMarkdown>
  </div>
}
