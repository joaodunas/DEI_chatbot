from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer
import faiss
import numpy as np
import uvicorn
import re
from sentence_transformers import CrossEncoder
from fastapi.middleware.cors import CORSMiddleware
import requests
import json

ollama_endpoint = "http://10.3.2.181:8080/api/generate"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or restrict to ["http://localhost:3000"] or your frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("🔧 Loading model...", flush=True)
model_name = "intfloat/multilingual-e5-large"
model = SentenceTransformer(model_name)

print("🔧 Loading reranker...", flush=True)
reranker_model = CrossEncoder("cross-encoder/mmarco-mMiniLMv2-L12-H384-v1")

metadata_sections_old = [
    "Apresentação do Departamento de Engenharia Informática (DEI) da Faculdade de Ciências e Tecnologia da Universidade de Coimbra, incluindo uma apresentação Geral, a missão e valores, o histórico e estrutura, parcerias e intercâmbio, e informações de contato completas do departamento, incluindo morada, número de telefone e endereço de email",
    "Órgãos de gestão do Departamento de Engenharia Informática (DEI): direção, comissão científica.",
    "Corpo docente do Departamento de Engenharia Informática (DEI): nomes, categorias, emails e perfis.",
    "Ensino no Departamento de Engenharia Informática (DEI): metodologia, cursos, infraestrutura, direção.",
    "Investigação no Departamento de Engenharia Informática (DEI): informação útil.",
    "Licenciatura em Engenharia Informática (LEI): plano de estudos, coordenação, saídas profissionais.",
    "Licenciatura em Design e Multimédia (LDM): plano de estudos, coordenação, saídas profissionais.",
    "Licenciatura em Engenharia e Ciência de Dados (LECD): plano de estudos, coordenação, saídas profissionais.",
    "Mestrado em Engenharia Informática (MEI): especializações, plano de estudos, coordenação.",
    "Mestrado em Design e Multimédia (MDM): plano de estudos, coordenação, saídas profissionais.",
    "Mestrado em Engenharia e Ciência de Dados (MECD): plano de estudos, coordenação, saídas profissionais.",
    ""
]

metadata_sections = ["", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""]


# Load and chunk the text file
def load_and_chunk(file_path, max_lines_per_chunk=10, tokenizer=None, max_tokens=512, metadata_sections=None):

    """
    Load the text file and chunk it into smaller parts.
    Args:
        file_path (str): Path to the text file.
        max_lines_per_chunk (int): Maximum number of lines per chunk.
        tokenizer: Optional tokenizer for token counting
        max_tokens (int): Maximum tokens per chunk
        metadata_sections (list): List of metadata for each section
    Returns:
        list: List of text chunks with metadata.
    """

    if not isinstance(file_path, str):
        raise ValueError("file_path must be a string")
    if not file_path.endswith(".md"):
        raise ValueError("file_path must be a .md file")
    
    if metadata_sections is None:
        metadata_sections = []
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"The file {file_path} does not exist.")
    
    sections = re.split(r'(?m)^# ', content)
    chunks = []
    
    metadata_sec_id = 0

    for i, sec in enumerate(sections):

        if not sec.strip():
            continue
        
        title_and_body = sec.strip().split("\n", 1)
        title = "# " + title_and_body[0].strip()
        body = title_and_body[1] if len(title_and_body) > 1 else ""
        body = re.sub(r'\n+', ' ', body).strip()
        body = re.sub(r'\s+', ' ', body).strip()
        full_text = f"{title}\n{body}"
        
        metadata = metadata_sections[metadata_sec_id] if i < len(metadata_sections) else ""
        metadata_sec_id += 1
        full_text_with_metadata = f"Resumo: {metadata}\nConteúdo: {full_text}"
        
        # Store as tuple of (text, metadata) for better organization
        chunks.append((full_text_with_metadata, metadata))
    
    return chunks

# Build FAISS index
def build_faiss_index(chunks, model):
    """
    Build a FAISS index from text chunks.
    Args:
        chunks (list): List of text chunks as (text, metadata) tuples.
        model (SentenceTransformer): Embedding model.
    Returns:
        index (faiss.IndexFlatL2): The FAISS index.
        chunk_embeddings (np.ndarray): Embedding matrix.
    """
    # Extract just the text part for embedding
    texts = [chunk[0] for chunk in chunks]
    embeddings = model.encode(texts, convert_to_numpy=True)
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    return index, embeddings

# Search
def search(query, model, index, chunks, top_k=3):

    """
    Search the FAISS index with a query and return top matching chunks.
    Args:
        query (str): The input query string.
        model (SentenceTransformer): Embedding model.
        index (faiss.IndexFlatL2): The FAISS index.
        chunks (list): Original text chunks as (text, metadata) tuples.
        top_k (int): Number of top results to return.
    Returns:
        list: Top-k most similar text chunks.
    """

    replacements = {
        "DEI": "Departamento de Engenharia Informática",
        "lei": "Licenciatura em Engenharia Informática",
        "mei": "Mestrado em Engenharia Informática",
        "lecd": "Licenciatura em Engenharia e Ciência de Dados",
        "mecd": "Mestrado em Engenharia e Ciência de Dados",
        "ldm": "Licenciatura em Design e Multimédia",
        "mdm": "Mestrado em Design e Multimédia",
        "fctuc": "Faculdade de Ciências e Tecnologia da Universidade de Coimbra",
        "fct": "Faculdade de Ciências e Tecnologia",
        "uc": "Universidade de Coimbra",
        "uc.pt": "Universidade de Coimbra",
    }

    query = query.lower()

    # replace
    for key, value in replacements.items():
        pattern = re.compile(rf"\b{key}\b", re.IGNORECASE)
        query = pattern.sub(value, query)
        
    print(query, flush=True)

    query_vec = model.encode([query], convert_to_numpy=True)
    distances, indices = index.search(query_vec, top_k)
    
    results = []
    for i in range(len(indices[0])):  # indices is a 2D array, we need to access the first row
        chunk_idx = indices[0][i]
        # Skip invalid indices that might occur if there are fewer matches than top_k
        if chunk_idx < 0 or chunk_idx >= len(chunks):
            continue
        
        results.append({
            "text": chunks[chunk_idx][0],  # Get the text part of the tuple
            "metadata": chunks[chunk_idx][1],  # Get the metadata part of the tuple
            "distance": float(distances[0][i])  # Convert to Python float for serialization
        })
    
    return results


def rerank(query, top_k_results, reranker_model):

    """
    Re-rank the retrieved documents based on the query using a Cross-Encoder or other reranking model.
    Args:
        query (str): The query string.
        top_k_results (list): List of top-k retrieved results as dictionaries.
        reranker_model: The model used to rerank the results.
    Returns:
        list: Top-ranked documents after reranking.
    """

    # Prepare the input for reranker: list of (query, document) pairs
    rerank_input = [(query, result['text']) for result in top_k_results]

    # Get reranked scores from the Cross-Encoder
    try:
        rerank_scores = reranker_model.predict(rerank_input)
    except Exception as e:
        print(f"Error during reranking: {e}")
        print(rerank_input)
    
    # Sort results based on rerank scores (higher is better)
    for i, result in enumerate(top_k_results):
        result['rerank_score'] = rerank_scores[i]

    # Sort by rerank score and return the top 3
    top_3_results = sorted(top_k_results, key=lambda x: x['rerank_score'], reverse=True)[:3]
    
    return top_3_results


def generate_request(model_name : str, prompt : str, vm_url : str) -> str:

    """
    Make a request to the model (hosted at the VM) and return the response.
    Args:
        model_name (str): The name of the model to use.
        prompt (str): The input prompt for the model.
        vm_url (str): The URL of the VM hosting the model.
    Returns:
        str: The response from the model.
    """

    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False
    }
    headers = {"Content-Type": "application/json"}

    try:
        print("Sending request")
        response = requests.post(vm_url, data=json.dumps(payload), headers=headers)
        response.raise_for_status()  # Raise an error for bad responses (4xx, 5xx)
        return response.json()  # Return JSON response
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


# API setup
class QueryRequest(BaseModel):

    """
    Request model for querying the document.
    Args:
        query (str): The input query string.
        top_k (int): Number of top results to return.
    """

    query: str
    context: str
    top_k: int = 3


@app.post("/query")
def query_docs(request: QueryRequest):

    """
    Endpoint to query the document and return top-k results.
    Args:
        request (QueryRequest): The request object containing the query and top_k.
    Returns:
        dict: A dictionary containing the results or an error message.
    """

    entire_context = f"Chat History: {request.context}\New question: {request.query}"
    query_refactor_question = "Generate a standalone question which is based on the new question plus the chat history. Just create the standalone question without commentary. New question: "

    print(entire_context, flush=True)

    try:
        response = generate_request(model_name = "qwen2.5:72b", 
                                    prompt = f"{entire_context}\n{query_refactor_question}", 
                                    vm_url=ollama_endpoint)
        
        request.query = response["response"]

    except Exception as e:
        return {"error": str(e)}

    try:
        results = search(
            request.query,
            model,
            index,
            chunks,
            top_k=request.top_k
        )
        #reranked_results = rerank(request.query, results, reranker_model)
        return {"results": results}
    except Exception as e:
        return {"error": str(e)}


FILE_PATH = "info_dei.md"

print("📄 Chunking file...", flush=True)
chunks = load_and_chunk(FILE_PATH, max_tokens=512, metadata_sections=metadata_sections)
print(f"🔍 Found {len(chunks)} chunks.", flush=True)

print("📦 Building FAISS index...", flush=True)
index, _ = build_faiss_index(chunks, model)

print("All done", flush=True)