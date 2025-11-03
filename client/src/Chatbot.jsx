import React, { useState } from 'react'

export default function Chatbot() {
  const [query, setQuery] = useState('')
  const [messages, setMessages] = useState([]) // {role: 'user'|'assistant', text, usedRag}
  const [useRag, setUseRag] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function send() {
    if (!query.trim()) return
    setError(null)

    const userMsg = { role: 'user', text: query }
    setMessages(prev => [...prev, userMsg])
    setLoading(true)

    try {
      const res = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, useRag })
      })

      if (!res.ok) throw new Error('Server error')

      const data = await res.json()
      const assistantMsg = { role: 'assistant', text: data.reply, usedRag: data.usedRag, context: data.context }
      setMessages(prev => [...prev, assistantMsg])
      setQuery('')
    } catch (e) {
      setError(String(e))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="chatbot">
      <div className="messages">
        {messages.map((m, i) => (
          <div key={i} className={`msg ${m.role}`}>
            <div className="meta">
              <strong>{m.role === 'user' ? 'You' : 'Assistant'}</strong>
              {m.usedRag ? <span className="tag">RAG</span> : null}
            </div>
            <div className="text">{m.text}</div>
            {m.context ? (
              <details className="context">
                <summary>Context (retrieved)</summary>
                <pre>{JSON.stringify(m.context, null, 2)}</pre>
              </details>
            ) : null}
          </div>
        ))}
      </div>

      <div className="composer">
        <textarea
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="Introduce tu consulta..."
          rows={4}
        />

        <div className="controls">
          <div className="rag-toggles">
            <button
              className={!useRag ? 'active' : ''}
              onClick={() => setUseRag(false)}
              aria-pressed={!useRag}
            >
              Sin RAG
            </button>
            <button
              className={useRag ? 'active' : ''}
              onClick={() => setUseRag(true)}
              aria-pressed={useRag}
            >
              RAG
            </button>
          </div>

          <div className="actions">
            <button onClick={send} disabled={loading}>{loading ? 'Sending...' : 'Enviar'}</button>
          </div>
        </div>

        {error ? <div className="error">{error}</div> : null}
      </div>
    </div>
  )
}
