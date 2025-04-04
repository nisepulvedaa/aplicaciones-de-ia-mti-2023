# Sistema RAG Basado en Agentes - Proyecto Aplicaciones de IA MTI 2023

## 👥 Integrantes
- **Gabriela Castillo**
- **Oscar Mendoza**
- **Nicolás Sepúlveda**

![Foto de los Integrantes](https://deinsoluciones.cl/web_semantica/integrantes.png)

---

## 🧠 Descripción del Proyecto

Este proyecto propone la implementación de un sistema RAG (Retrieval-Augmented Generation) avanzado con múltiples agentes de IA para asistir a Colbún en la extracción de conocimiento desde su base documental.

El sistema aborda la problemática de acceso a información dispersa en grandes volúmenes de documentos provenientes del ciclo de vida de proyectos, normativas regulatorias y documentos internos.

---

## 🏗️ Arquitectura General

![Arquitectura General de la Solución](https://deinsoluciones.cl/post/arquitectura_general_de_la_solucion.png)

---

## ⚙️ Stack Tecnológico

![Stack Tecnológico](https://deinsoluciones.cl/post/stack_tecnologico.png)

El proyecto está construido sobre una pila moderna de tecnologías:

- **Python** y **LangChain** para orquestación de agentes
- **OpenAI Embedding Models** (`text-embedding-3-small`, `text-embedding-3-large`)
- **FAISS** y **PostgreSQL** para vector store y consultas eficientes
- **Streamlit** para visualización de la demo en vivo

---

## 🔍 Flujo del Sistema RAG con Agentes

![RAG Systems](https://deinsoluciones.cl/post/rag_systems.png)

- El sistema cuenta con agentes especializados para:
  - Recuperación de información contextual.
  - Análisis y resumen de textos largos.
  - Generación de respuestas en lenguaje natural.

---

## 🚀 Demo

Se implementó una demo funcional donde el usuario puede ingresar preguntas en lenguaje natural, y el sistema responde basándose en los documentos vectorizados previamente. Los agentes colaboran para entregar una respuesta precisa y contextualizada.

---

## 📚 Fuentes

- [arxiv.org - RAG Systems 2024](https://arxiv.org/abs/2407.19994)
- Documentación interna Colbún (no pública)

