/**
 * ConfidenceBadge — colored dot + percentage showing how confident the RAG retrieval was.
 * Green ≥70%, orange 40–69%, red <40%. Mirrors the Streamlit implementation.
 */
interface Props {
  confidence: number | null | undefined
}

export default function ConfidenceBadge({ confidence }: Props) {
  if (confidence == null) return null

  const color =
    confidence >= 70
      ? 'bg-green-500'
      : confidence >= 40
      ? 'bg-orange-400'
      : 'bg-red-500'

  return (
    <span className="inline-flex items-center gap-1.5 text-xs text-gray-400">
      <span className={`w-2 h-2 rounded-full ${color}`} />
      {confidence}% confidence
    </span>
  )
}
