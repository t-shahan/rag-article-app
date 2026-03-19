/**
 * DataOverviewPage — shows aggregate stats + a browsable article list.
 * Equivalent to the Streamlit "Data Overview" page.
 */
import { useEffect, useState } from 'react'
import client from '../api/client'
import ArticleCard from '../components/DataOverview/ArticleCard'
import type { Article } from '../types'

export default function DataOverviewPage() {
  const [articles, setArticles] = useState<Article[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    client.get<Article[]>('/api/articles').then((res) => {
      setArticles(res.data)
      setLoading(false)
    })
  }, [])

  const totalChunks = articles.reduce((sum, a) => sum + a.chunk_count, 0)

  return (
    <div className="flex-1 overflow-y-auto px-6 py-8">
      <h1 className="text-xl font-semibold text-gray-100 mb-1">Data Overview</h1>
      <p className="text-sm text-gray-500 mb-6">
        The articles indexed in this knowledge base.
      </p>

      {/* Summary stats */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-8">
        <StatCard label="Articles" value={articles.length} />
        <StatCard label="Total chunks" value={totalChunks} />
        <StatCard label="Embedding model" value="text-embedding-3-small" small />
      </div>

      {/* Article list */}
      {loading ? (
        <p className="text-sm text-gray-500">Loading…</p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
          {articles.map((a) => (
            <ArticleCard key={a.title} article={a} />
          ))}
        </div>
      )}
    </div>
  )
}

function StatCard({ label, value, small }: { label: string; value: string | number; small?: boolean }) {
  return (
    <div className="px-4 py-3 rounded-xl border border-white/8 bg-white/3">
      <p className="text-xs text-gray-500 mb-0.5">{label}</p>
      <p className={`font-semibold text-gray-100 ${small ? 'text-sm' : 'text-2xl'}`}>{value}</p>
    </div>
  )
}
