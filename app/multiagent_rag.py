# Archivo: app/multiagent_rag.py

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.runnables import RunnableLambda
from langchain_core.pydantic_v1 import BaseModel, Field
from langgraph.graph import END, StateGraph
from operator import itemgetter
from typing import List, Dict
import psycopg2
import os
from dotenv import load_dotenv
from scipy.spatial.distance import cosine
from langchain_community.tools.tavily_search import TavilySearchResults

load_dotenv()

# === PostgreSQL Config ===
PG_CONFIG = {
    "host": os.getenv("PG_HOST", "localhost"),
    "port": os.getenv("PG_PORT", "5432"),
    "dbname": os.getenv("PG_DB", "postgres"),
    "user": os.getenv("PG_USER", "postgres"),
    "password": os.getenv("PG_PASS", ""),
    "table_name": "pdf_embeddings_large_line"
}

# === Recuperador desde PostgreSQL ===
def get_pg_embeddings():
    conn = psycopg2.connect(
        host=PG_CONFIG["host"],
        dbname=PG_CONFIG["dbname"],
        user=PG_CONFIG["user"],
        password=PG_CONFIG["password"],
        port=PG_CONFIG["port"]
    )
    cursor = conn.cursor()
    cursor.execute(f"SELECT content, embedding FROM {PG_CONFIG['table_name']}")
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

# === Vector Similarity Function ===
def retrieve_similar_documents(query_embedding, top_k=5):
    all_docs = get_pg_embeddings()
    similarities = [
        (content, 1 - cosine(query_embedding, embedding))
        for content, embedding in all_docs
    ]
    sorted_docs = sorted(similarities, key=lambda x: x[1], reverse=True)
    return [doc[0] for doc in sorted_docs[:top_k]]

# === Embedding & LLM Models ===
embedder = OpenAIEmbeddings(model="text-embedding-3-large", openai_api_key=os.environ.get("OPENAI_API_KEY"))
llm = ChatOpenAI(model_name="gpt-4-turbo", temperature=0)


# === QA RAG Chain ===
prompt_template = ChatPromptTemplate.from_template("""
Eres un asistente experto en análisis legal y contratos.
Responde la pregunta usando el siguiente fragmento de contexto. 
Si no encuentras suficiente información en el contexto, utiliza tu conocimiento general para ayudar al usuario.
intenta no cambiar tanto el contenido de la respuesta.
Pregunta: {question}
Contexto: {context}
Respuesta:
""")

'''
prompt_template = ChatPromptTemplate.from_template("""
Eres un asistente experto en análisis legal y contratos.
Responde la pregunta usando el siguiente fragmento de contexto.
Si no hay contexto o no sabes la respuesta, responde que no tienes suficiente información.
No inventes respuestas que no estén en el contexto.
Pregunta: {question}
Contexto: {context}
Respuesta:
""")
'''

def format_docs(docs):
    return "\n\n".join(docs)

qa_rag_chain = (
    {
        "context": (itemgetter("context") | RunnableLambda(format_docs)),
        "question": itemgetter("question")
    } | prompt_template | llm | StrOutputParser()
)

# === Doc Grader (Agente 1 - Evaluador Legal) ===
class GradeDocuments(BaseModel):
    binary_score: str = Field(description="sí o no")

structured_llm_grader = llm.with_structured_output(GradeDocuments)

grade_prompt = ChatPromptTemplate.from_messages([
    ("system", "Eres un abogado experto que evalúa la relevancia de fragmentos de documentos legales. Si el fragmento contiene nombres, entidades, cláusulas o información clave útil para responder la pregunta, responde 'sí'. De lo contrario, responde 'no'."),
    ("human", "Fragmento del documento: {document}\n\nPregunta del usuario: {question}")
])

doc_grader = (grade_prompt | structured_llm_grader)

# === Rewriter (Agente 2) ===
rewrite_prompt = ChatPromptTemplate.from_messages([
    ("system", "Actúa como un reformulador de preguntas y optimiza la consulta para una búsqueda en la web."),
    ("human", "Pregunta original:\n{question}\nReformula la pregunta de manera más efectiva para buscar información relevante.")
])

question_rewriter = (rewrite_prompt | llm | StrOutputParser())

# === Web Search Tool (Agente 3) ===
web_search_tool = TavilySearchResults(max_results=3)

# === Hallucination Grader (Agente 4) ===
hallucination_prompt = PromptTemplate(
    template="""
    Eres un evaluador legal que detecta si una respuesta contiene alucinaciones o invenciones.
    Devuelve 'sí' si detectas afirmaciones no respaldadas por el contexto legal. Devuelve 'no' si todo está respaldado.
    Entrega el resultado como JSON con una única clave 'score' y sin explicaciones.
    -----
    {documents}
    -----
    Respuesta generada: {generation}
    """,
    input_variables=["generation", "documents"]
)

hallucination_grader = hallucination_prompt | llm | JsonOutputParser()

# === Graph State ===
class GraphState(BaseModel):
    question: str
    generation: str = None
    context: List[str] = None
    hallucination: str = None

# === Funciones del Grafo ===
def retrieve(state):
    embedding = embedder.embed_query(state.question)
    docs = retrieve_similar_documents(embedding)
    return {"context": docs, "question": state.question}

def grade_documents(state):
    #grades = [doc_grader.invoke({"question": state.question, "document": doc}) for doc in state.context]
    #relevant_docs = [doc for doc, grade in zip(state.context, grades) if grade.binary_score.lower() == "sí"]
    #return {"context": relevant_docs, "question": state.question}
    return {"context": state.context, "question": state.question}

def rewrite_query(state):
    rewritten = question_rewriter.invoke({"question": state.question})
    return {"question": rewritten}

def web_search(state):
    results = web_search_tool.invoke(state.question)
    texts = [item["content"] if isinstance(item, dict) and "content" in item else str(item) for item in results]
    return {"context": texts, "question": state.question}

def generate_answer(state):
    result = qa_rag_chain.invoke({"context": state.context, "question": state.question})
    return {"generation": result, "context": state.context, "question": state.question}

def hallucination_check(state):
    result = hallucination_grader.invoke({"documents": format_docs(state.context), "generation": state.generation})
    return {"generation": state.generation, "hallucination": result.get("score", "unknown")}

# === Grafo de ejecución ===
workflow = StateGraph(GraphState)
workflow.add_node("retrieve", retrieve)
workflow.add_node("grade_documents", grade_documents)
workflow.add_node("rewrite_query", rewrite_query)
workflow.add_node("web_search", web_search)
workflow.add_node("generate_answer", generate_answer)
workflow.add_node("hallucination_check", hallucination_check)

workflow.set_entry_point("retrieve")
workflow.add_edge("retrieve", "grade_documents")
workflow.add_conditional_edges(
    "grade_documents",
    lambda state: "generate_answer" if state.context else "rewrite_query",
    {"generate_answer": "generate_answer", "rewrite_query": "rewrite_query"}
)
workflow.add_edge("rewrite_query", "web_search")
workflow.add_edge("web_search", "generate_answer")
workflow.add_edge("generate_answer", "hallucination_check")
workflow.add_edge("hallucination_check", END)
workflow = workflow.compile()

# === Ejecutar ===
def run_multiagent(query: str) -> Dict[str, str]:
    initial_state = GraphState(question=query)
    result = workflow.invoke(initial_state)
    return {
        "respuesta": result.get("generation", "No se encontró una respuesta relevante."),
        "hallucination": result.get("hallucination", "unknown")
    }
