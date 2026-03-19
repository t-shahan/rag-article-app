import { useState } from 'react'
import { Disclosure, DisclosureButton, DisclosurePanel } from '@headlessui/react'
import { ChevronRight, BookOpen } from 'lucide-react'
import client from '../../api/client'
import type { Article } from '../../types'

interface Props {
  article: Article
}

export default function ArticleCard({ article }: Props) {
  const [chunks, setChunks] = useState<string[]>([])
  const [fetched, setFetched] = useState(false)
  const [loading, setLoading] = useState(false)

  async function handleOpen(open: boolean) {
    // Fetch chunks only once, on first expand
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
            className="w-full flex items-center gap-3 px-4 py-3 text-left cursor-pointer"
          >
            <BookOpen size={15} className="flex-shrink-0 text-[#C2B067] opacity-80" />
            <span className="flex-1 text-sm font-medium text-gray-200 truncate">
              {article.title}
            </span>
            <span className="text-xs text-gray-500 flex-shrink-0 mr-2">
              {article.chunk_count} chunks
            </span>
            <ChevronRight
              size={14}
              className={`flex-shrink-0 text-gray-500 transition-transform duration-150 ${
                open ? 'rotate-90' : ''
              }`}
            />
          </DisclosureButton>

          {/* Expanded content */}
          <DisclosurePanel className="px-4 pb-4">
            {loading && (
              <p className="text-xs text-gray-500 py-2">Loading…</p>
            )}
            {!loading && chunks.length > 0 && (
              <div className="space-y-3 pt-1 max-h-96 overflow-y-auto pr-1">
                {chunks.map((chunk, i) => (
                  <div key={i} className="relative pl-3">
                    {/* Gold left border accent */}
                    <div className="absolute left-0 top-0 bottom-0 w-0.5 rounded-full bg-gradient-to-b from-[#A08340] to-[#C2B067] opacity-40" />
                    <p className="text-xs text-gray-400 leading-relaxed">{chunk}</p>
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
