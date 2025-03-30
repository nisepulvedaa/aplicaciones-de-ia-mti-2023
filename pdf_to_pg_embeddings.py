from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import PGVector
import psycopg2
import os
import re
from dotenv import load_dotenv
from tqdm import tqdm  #Barra de progreso

load_dotenv()

# === CONFIGURACIÓN ===
PDF_PATH = "data\\Contrato1.pdf"
CHUNK_SIZE = 300
CHUNK_OVERLAP = 30


PG_CONFIG = {"host": "localhost","port": "5432","dbname": "postgres","user": "postgres","password": "","table_name": "pdf_embeddings_large_new_line"}

# === FUNCIÓN DE LIMPIEZA DE TEXTO (1 sola línea) ===
def clean_text(text):
    # Eliminar encabezados tipo "4 de 64"
    text = re.sub(r'^\s*\d+\s+de\s+\d+\s*$', '', text, flags=re.MULTILINE)
    # Reemplazar saltos de línea y múltiples espacios con un solo espacio
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

EMBED_MODEL = "text-embedding-3-large"
# === PASO 1: Cargar el PDF ===
loader = PyPDFLoader(PDF_PATH)
docs = loader.load()

# === PASO 2: Dividir el contenido en chunks ===
splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
chunked_docs = splitter.split_documents(docs)

# === PASO 3: Generar embeddings con OpenAI ===
embedder = OpenAIEmbeddings(model=EMBED_MODEL, openai_api_key=os.environ.get("OPENAI_API_KEY"))

# === PASO 4: Guardar en PostgreSQL ===
conn = psycopg2.connect(host=PG_CONFIG["host"],dbname=PG_CONFIG["dbname"],user=PG_CONFIG["user"],
                        password=PG_CONFIG["password"],port=PG_CONFIG["port"])
cursor = conn.cursor()

# Procesar y guardar cada chunk con limpieza y barra de progreso
for doc in tqdm(chunked_docs, desc="Procesando chunks"):
    raw_text = doc.page_content
    cleaned_text = clean_text(raw_text)
    embedding = embedder.embed_query(cleaned_text)
    cursor.execute(
        f"INSERT INTO {PG_CONFIG['table_name']} (content, embedding) VALUES (%s, %s)",
        (cleaned_text, embedding)
    )

conn.commit()
cursor.close()
conn.close()

print(f"{len(chunked_docs)} chunks procesados, limpiados y almacenados en PostgreSQL.")
