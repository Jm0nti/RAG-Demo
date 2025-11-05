import pandas as pd
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv
import os


load_dotenv(override=True)
os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')

csv_files = {
    "Asignaturas": "data/Contexto_Asignaturas/Asignaturas_normalizado.csv",
    "AsignaturasCarrera": "data/Contexto_Asignaturas/AsignaturasCarrera_normalizado.csv",
    "Horarios": "data/Contexto_Asignaturas/Horarios_normalizado.csv",
    "Prerrequisitos": "data/Contexto_Asignaturas/Prerrequisitos_normalizado.csv",
    "Profesores": "data/Contexto_Asignaturas/Profesores_normalizado.csv",
    "Oficinas": "data/Contexto_Asignaturas/Oficinas_normalizado.csv"
}

# Embeddings
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")


VECTORDB_PATH = "data/Vector DBs/FAISS/vector_db"


documents = []
for fuente, filepath in csv_files.items():
    df = pd.read_csv(filepath)
    
    for _, row in df.iterrows():
        # Convertir fila en texto legible para el LLM
        content = " | ".join([f"{col}: {row[col]}" for col in df.columns])
        
        # Añadir metadatos
        metadata = {"fuente": fuente}
        for col in df.columns:
            metadata[col] = row[col]
        
        documents.append({
            "content": content,
            "metadata": metadata
        })

# Dividir en chunks 
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
docs_ready = []
for doc in documents:
    splits = text_splitter.split_text(doc["content"])
    for chunk in splits:
        docs_ready.append({"content": chunk, "metadata": doc["metadata"]})

# Crear vectorstore 
texts = [doc["content"] for doc in docs_ready]
metadatas = [doc["metadata"] for doc in docs_ready]

vectorstore = FAISS.from_texts(texts, embeddings, metadatas=metadatas)

# Guardar en disco
vectorstore.save_local(VECTORDB_PATH)

print(f"✅ VectorDB creada con {len(texts)} chunks y guardada en {VECTORDB_PATH}")
