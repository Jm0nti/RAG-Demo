import os, logging
from dotenv import load_dotenv
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_groq import ChatGroq


load_dotenv(override=True)
logger = logging.getLogger(__name__)

OPENAI_KEY = os.getenv("OPENAI_API_KEY")
GROQ_KEY = os.getenv("GROQ_API_KEY")
if not OPENAI_KEY or not GROQ_KEY:
    raise RuntimeError("Missing API keys: check .env file")



# --- Base Bot ---
class Bot:

    def __init__(
        self,
        system_prompt: str = "Eres un asistente general.",
        model: str = "llama-3.1-8b-instant",
        temperature: float = 0,
        verbose: bool = False
            ) -> None:


        self.system_prompt_text = system_prompt
        self.llm = ChatGroq(model=model, temperature=temperature)
        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        system_prompt_template = SystemMessagePromptTemplate.from_template(system_prompt)
        human_prompt_template = HumanMessagePromptTemplate.from_template("{question}")
        self.chat_prompt = ChatPromptTemplate.from_messages([system_prompt_template, human_prompt_template])
        self.verbose = verbose

    def ask(self, question: str) -> str:

        # Default implementation: call the LLM chain with the stored prompt and memory.
        chain = LLMChain(llm=self.llm, prompt=self.chat_prompt, memory=self.memory, verbose=self.verbose)
        try:
            # LLMChain.run accepts the prompt input variable name(s); our human template uses {question}
            return chain.run(question)
        except Exception as e:
            logger.exception("Error calling LLM: %s", e)
            # Return fallback string
            return f"(LLM error) Could not generate response: {e}"


class RAGBot(Bot):
 

    def ask_with_docs(self, question: str, docs: list) -> str:
  
        # Build a system prompt that includes the retrieved context
        context_parts = []
        for d in docs:
            title = d.get("title") or d.get("id", "")
            content = d.get("content", "")
            context_parts.append(f"- {title}: {content}")
        context_text = "\n".join(context_parts)

        system_with_context = f"{self.system_prompt_text}\n\nContext:\n{context_text}\n\nUse only the information from the context to answer when possible."

        system_template = SystemMessagePromptTemplate.from_template(system_with_context)
        human_template = HumanMessagePromptTemplate.from_template("{question}")
        prompt = ChatPromptTemplate.from_messages([system_template, human_template])

        chain = LLMChain(llm=self.llm, prompt=prompt, memory=self.memory, verbose=self.verbose)
        try:
            return chain.run(question)
        except Exception as e:
            logger.exception("Error calling RAG LLM: %s", e)
            return f"(LLM error) Could not generate RAG response: {e}"

    def chat_loop(self) -> None:
        """
        Inicia un ciclo de chat interactivo con el bot en la terminal.
        """
        print(f"🤖 {self.__class__.__name__} activo (escribe 'salir' para terminar)\n")
        while True:
            query = input("Tú: ")
            if query.lower() in ["salir", "exit", "quit"]:
                print("Bot: Hasta luego 👋")
                break
            try:
                print("Bot:", self.ask(query))
            except Exception as e:
                logger.exception("Error en chat_loop: %s", e)
                print("Bot: Ocurrió un error, revisa los logs.")