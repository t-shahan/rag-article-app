import ReactMarkdown from 'react-markdown'
import ConfidenceBadge from './ConfidenceBadge'
import SourcesList from './SourcesList'
import FollowUpButtons from './FollowUpButtons'
import type { ChatMessage } from '../../hooks/useChat'

interface Props {
  message: ChatMessage
  isLast: boolean
  onFollowUp: (q: string) => void
}

export default function Message({ message, isLast, onFollowUp }: Props) {
  if (message.role === 'user') {
    return (
      <div className="flex justify-end">
        <div className="max-w-[75%] px-4 py-2.5 rounded-2xl rounded-br-sm bg-[#C2B067]/15 border border-[#C2B067]/20 text-gray-100 text-sm">
          {message.content}
        </div>
      </div>
    )
  }

  return (
    <div className="flex justify-start">
      <div className="max-w-[85%] space-y-2">
        <div className="px-4 py-3 rounded-2xl rounded-bl-sm bg-white/5 border border-white/8 text-gray-200 text-sm prose prose-invert prose-sm max-w-none">
          <ReactMarkdown>{message.content}</ReactMarkdown>
        </div>
        <div className="px-1 space-y-2">
          <ConfidenceBadge confidence={message.confidence} />
          <SourcesList sources={message.sources ?? []} />
          {isLast && (
            <FollowUpButtons questions={message.follow_ups ?? []} onSelect={onFollowUp} />
          )}
        </div>
      </div>
    </div>
  )
}
