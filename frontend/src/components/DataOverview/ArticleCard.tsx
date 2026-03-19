import { useState } from 'react'
import { Disclosure, DisclosureButton, DisclosurePanel } from '@headlessui/react'
import { ChevronRight, BookOpen } from 'lucide-react'
import client from '../../api/client'
import type { Article } from '../../types'

interface Props {
  article: Article
}

/** Strip the "Title: ..." header line that leads every first chunk. */
function stripHeader(text: string): string {
  return text.replace(/^Title:.*\n?/i, '').trim()
}

export default function ArticleCard({ article }: Props) {
  const [chunks, setChunks] = useState<string[]>([])
  const [fetched, setFetched] = useState(false)
  const [loading, setLoading] = useState(false)

  async function handleOpen(open: boolean) {
    if (open && !fetched) {
      setLoading(true)
      try {
        const res = await client.get<string[]>('/api/articles/chunks', {
          params: { source: article.source },
        })
        setChunks(res.data)
        setFetched(true)
      } finally {
        setLoading(false)
      }
    }
  }

  return (
    <Disclosure>
      {({ open }) => (
        <div
          className={`rounded-xl border transition-colors ${
            open ? 'border-[#C2B067]/30 bg-white/5' : 'border-white/8 bg-white/3 hover:bg-white/5'
          }`}
        >
          {/* Header row */}
          <DisclosureButton
            onClick={() => handleOpen(!open)}
            className="w-full flex items-start gap-3 px-4 py-3 text-left cursor-pointer"
          >
            <BookOpen size={15} className="flex-shrink-0 text-[#C2B067] opacity-80 mt-0.5" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-200 truncate">{article.title}</p>
              {!open && article.preview && (
                <p className="text-xs text-gray-500 mt-0.5 line-clamp-2 leading-relaxed">
                  {article.preview}
                </p>
              )}
            </div>
            <ChevronRight
              size={14}
              className={`flex-shrink-0 text-gray-500 transition-transform duration-150 mt-0.5 ${
                open ? 'rotate-90' : ''
              }`}
            />
          </DisclosureButton>

          {/* Expanded content */}
          <DisclosurePanel className="px-4 pb-4">
            {loading && <p className="text-xs text-gray-500 py-2">Loading…</p>}
            {!loading && chunks.length > 0 && (
              <div className="space-y-4 pt-1 max-h-96 overflow-y-auto pr-1">
                {chunks.map((chunk, i) => (
                  <div key={i} className="relative pl-3">
                    <div className="absolute left-0 top-0 bottom-0 w-0.5 rounded-full bg-gradient-to-b from-[#A08340] to-[#C2B067] opacity-40" />
                    <p className="text-xs text-gray-500 mb-1">Section {i + 1}</p>
                    <p className="text-xs text-gray-400 leading-relaxed whitespace-pre-line">
                      {i === 0 ? stripHeader(chunk) : chunk}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </DisclosurePanel>
        </div>
      )}
    </Disclosure>
  )
}
