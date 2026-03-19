export interface Message {
  role: 'user' | 'assistant'
  content: string
}

export interface ChatResponse {
  answer: string
  sources: string[]
  confidence: number | null
  follow_ups: string[]
  session_id: string | null
}

export interface Conversation {
  session_id: string
  title: string
  project_id: string | null
  updated_at: string
}

export interface ConversationDetail extends Conversation {
  messages: Message[]
  created_at: string
}

export interface Project {
  project_id: string
  name: string
  created_at: string
}

export interface Article {
  source: string
  title: string
  preview: string
}

export interface ArticlesResponse {
  items: Article[]
  total: number
}
