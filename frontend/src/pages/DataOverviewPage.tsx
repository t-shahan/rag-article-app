/**
 * DataOverviewPage — browsable, searchable index of the knowledge base.
 */
import { useEffect, useState } from 'react'
import { Search } from 'lucide-react'
import client from '../api/client'
import ArticleCard from '../components/DataOverview/ArticleCard'
import type { Article } from '../types'

export default function DataOverviewPage() {
  const [articles, setArticles] = useState<Article[]>([])
  const [loading, setLoading] = useState(true)
  const [query, setQuery] = useState('')

  useEffect(() => {
    client.get<Article[]>('/api/articles').then((res) => {
      setArticles(res.data)
      setLoading(false)
    })
  }, [])

  const filtered = query.trim()
    ? articles.filter((a) => a.title.toLowerCase().includes(query.toLowerCase()))
    : articles

  return (
    <div className="flex-1 overflow-y-auto px-6 py-8">
      <h1 className="text-xl font-semibold text-gray-100 mb-1">Knowledge Base</h1>

      {/* Single stat banner */}
      {!loading && (
        <p className="text-sm text-gray-500 mb-6">
          {articles.length} articles indexed
        </p>
      )}

      {/* Search bar */}
      <div className="relative mb-5">
        <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 pointer-events-none" />
        <input
          type="text"
          placeholder="Search articles…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="w-full pl-8 pr-4 py-2 rounded-xl bg-white/5 border border-white/10 text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-[#C2B067]/40 focus:bg-white/7 transition-colors"
        />
      </div>

      {/* Article list */}
      {loading ? (
        <p className="text-sm text-gray-500">Loading…</p>
      ) : filtered.length === 0 ? (
        <p className="text-sm text-gray-500">No articles match "{query}"</p>
      ) : (
        <div className="flex flex-col gap-2">
          {filtered.map((a) => (
            <ArticleCard key={a.source} article={a} />
          ))}
        </div>
      )}
    </div>
  )
}
