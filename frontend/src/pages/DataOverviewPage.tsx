/**
 * DataOverviewPage — searchable, paginated index of the knowledge base.
 *
 * Search is server-side and debounced so this scales to any collection size.
 * Pagination is built into the API (?limit=50&skip=N) — add a Load More button
 * or virtual scroll here when article counts grow large enough to need it.
 */
import { useEffect, useRef, useState } from 'react'
import { Search } from 'lucide-react'
import client from '../api/client'
import ArticleCard from '../components/DataOverview/ArticleCard'
import type { Article, ArticlesResponse } from '../types'

const LIMIT = 50
const DEBOUNCE_MS = 300

export default function DataOverviewPage() {
  const [articles, setArticles] = useState<Article[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [query, setQuery] = useState('')
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  function fetchArticles(q: string) {
    setLoading(true)
    client
      .get<ArticlesResponse>('/api/articles', { params: { q, limit: LIMIT, skip: 0 } })
      .then((res) => {
        setArticles(res.data.items)
        setTotal(res.data.total)
      })
      .finally(() => setLoading(false))
  }

  // Initial load
  useEffect(() => { fetchArticles('') }, [])

  function handleSearch(value: string) {
    setQuery(value)
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => fetchArticles(value), DEBOUNCE_MS)
  }

  const subtitle = loading
    ? 'Loading…'
    : query.trim()
    ? `${total} result${total !== 1 ? 's' : ''} for "${query}"`
    : `${total} article${total !== 1 ? 's' : ''} indexed`

  return (
    <div className="flex-1 overflow-y-auto px-6 py-8">
      <h1 className="text-xl font-semibold text-gray-100 mb-1">Knowledge Base</h1>
      <p className="text-sm text-gray-500 mb-6">{subtitle}</p>

      {/* Search bar */}
      <div className="relative mb-5">
        <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 pointer-events-none" />
        <input
          type="text"
          placeholder="Search articles…"
          value={query}
          onChange={(e) => handleSearch(e.target.value)}
          className="w-full pl-8 pr-4 py-2 rounded-xl bg-white/5 border border-white/10 text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-[#C2B067]/40 focus:bg-white/7 transition-colors"
        />
      </div>

      {/* Article list */}
      {!loading && articles.length === 0 ? (
        <p className="text-sm text-gray-500">No articles match "{query}"</p>
      ) : (
        <div className="flex flex-col gap-2">
          {articles.map((a) => (
            <ArticleCard key={a.source} article={a} />
          ))}
        </div>
      )}
    </div>
  )
}
