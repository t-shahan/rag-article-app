import { useState, useEffect, useRef } from 'react'
import client from '../api/client'
import type { ChatResponse } from '../types'

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  sources?: string[]
  confidence?: number | null
  follow_ups?: string[]
}

interface UseChatOptions {
  sessionId: string | null
  onSessionCreated: (sessionId: string) => void
}

export function useChat({ sessionId, onSessionCreated }: UseChatOptions) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [loading, setLoading] = useState(false)
  const activeSessionId = useRef<string | null>(sessionId)
  // When we create a new conversation ourselves, the sessionId change triggers
  // the history-fetch effect — but the conversation is empty at that point and
  // would wipe the optimistic user message. This flag skips that one fetch.
  const skipNextFetch = useRef(false)

  useEffect(() => {
    activeSessionId.current = sessionId
  }, [sessionId])

  // Load history when navigating to an existing conversation
  useEffect(() => {
    if (!sessionId) {
      setMessages([])
      return
    }
    if (skipNextFetch.current) {
      skipNextFetch.current = false
      return
    }
    client.get(`/api/conversations/${sessionId}`).then((res) => {
      const raw: { role: string; content: string }[] = res.data.messages ?? []
      setMessages(raw.map((m) => ({ role: m.role as 'user' | 'assistant', content: m.content })))
    })
  }, [sessionId])

  async function sendMessage(question: string) {
    if (loading) return

    // Show loading dots + user message immediately before any async work
    setLoading(true)
    setMessages((prev) => [...prev, { role: 'user', content: question }])

    try {
      let sid = activeSessionId.current
      if (!sid) {
        const res = await client.post('/api/conversations', {
          title: question.slice(0, 60),
        })
        sid = res.data.session_id as string
        activeSessionId.current = sid
        // Tell the effect to skip the next fetch — we know the conversation is empty
        skipNextFetch.current = true
        onSessionCreated(sid)
      }

      const history = messages.map((m) => ({ role: m.role, content: m.content }))
      const res = await client.post<ChatResponse>('/api/chat', {
        question,
        session_id: sid,
        chat_history: history,
      })

      const { answer, sources, confidence, follow_ups } = res.data
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: answer, sources, confidence, follow_ups },
      ])
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Sorry, something went wrong. Please try again.' },
      ])
    } finally {
      setLoading(false)
    }
  }

  return { messages, loading, sendMessage }
}
