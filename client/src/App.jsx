import React from 'react'
import Chatbot from './Chatbot'

export default function App() {
  return (
    <div className="app">
      <header>
        <h1>RAG Demo</h1>
        <p>Demostración de generación de texto a partir de memoria no paramétrica vs. sólo memoria paramétrica en modelos LLM</p>
      </header>
      <main>
        <Chatbot />
      </main>
    </div>
  )
}
