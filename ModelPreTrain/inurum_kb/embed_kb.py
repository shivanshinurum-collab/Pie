#!/usr/bin/env python3
import os
import re
import json
import argparse
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModel

# Configuration
KB_DIR = "/Users/shubhamjain/Documents/pai/ModelPreTrain/inurum_kb/company_knowledge_base"
INDEX_FILE = "company_kb.index"
METADATA_FILE = "company_kb_metadata.json"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Check if FAISS is available
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("Warning: faiss-cpu is not installed in the Python environment. Falling back to numpy similarity search.")

# Mean Pooling function for Hugging Face model outputs
def mean_pooling(model_output, attention_mask):
    token_embeddings = model_output[0] # First element of model_output contains all token embeddings
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)

def parse_markdown_file(filepath):
    """Parses a markdown file to extract frontmatter and split by headings."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Parse metadata frontmatter
    metadata = {}
    if content.startswith("---\n"):
        match = re.search(r"^---\n(.*?)\n------------------\n", content, re.DOTALL)
        if match:
            frontmatter_text = match.group(1)
            body_text = content[match.end():]
            
            # Simple YAML-like parser
            for line in frontmatter_text.split("\n"):
                if ":" in line:
                    k, v = line.split(":", 1)
                    metadata[k.strip()] = v.strip()
        else:
            body_text = content
    else:
        body_text = content

    # Get document title
    title_match = re.search(r"^# (.*?)$", body_text, re.MULTILINE)
    doc_title = title_match.group(1).strip() if title_match else os.path.basename(filepath)

    # Split body into sections by markdown headings (e.g. ## Overview)
    sections = re.split(r"\n(## .*?)\n", body_text)
    
    chunks = []
    
    # The first element before any ## heading is the intro (if any)
    intro = sections[0].strip()
    if intro and len(intro.split()) > 20: # only keep meaningful intros
        chunks.append({
            "section": "Introduction",
            "content": intro
        })
        
    # Process heading-body pairs
    for i in range(1, len(sections), 2):
        heading = sections[i].strip("# ")
        body = sections[i+1].strip() if i+1 < len(sections) else ""
        if body:
            chunks.append({
                "section": heading,
                "content": body
            })
            
    # Compile chunks with metadata
    compiled_chunks = []
    for c in chunks:
        # Prepend metadata to the chunk text to give context during embedding and retrieval
        meta_prefix = (
            f"Document Title: {doc_title}\n"
            f"Document Type: {metadata.get('document_type', 'N/A')}\n"
            f"Department: {metadata.get('department', 'N/A')}\n"
            f"Section: {c['section']}\n\n"
        )
        full_text = meta_prefix + c["content"]
        
        compiled_chunks.append({
            "doc_id": metadata.get("document_id", "N/A"),
            "doc_title": doc_title,
            "filepath": os.path.relpath(filepath, KB_DIR),
            "department": metadata.get("department", "N/A"),
            "owner": metadata.get("owner", "N/A"),
            "section": c["section"],
            "chunk_text": full_text,
            "raw_content": c["content"]
        })
        
    return compiled_chunks

def load_documents():
    """Recursively crawls the KB directory and extracts all chunks."""
    all_chunks = []
    print(f"Scanning directory: {KB_DIR}")
    for root, _, files in os.walk(KB_DIR):
        for file in files:
            if file.endswith(".md"):
                filepath = os.path.join(root, file)
                try:
                    chunks = parse_markdown_file(filepath)
                    all_chunks.extend(chunks)
                except Exception as e:
                    print(f"Error parsing {file}: {e}")
    print(f"Extracted {len(all_chunks)} semantic chunks from knowledge base.")
    return all_chunks

def embed_chunks(chunks, tokenizer, model):
    """Generates embeddings for a list of document chunks using the HF model."""
    print("Initializing embedding generation...")
    device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    print(f"Using compute device: {device}")
    model = model.to(device)
    model.eval()

    embeddings = []
    batch_size = 16
    
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i+batch_size]
        texts = [c["chunk_text"] for c in batch]
        
        # Tokenize sentences
        encoded_input = tokenizer(texts, padding=True, truncation=True, max_length=512, return_tensors='pt')
        encoded_input = {k: v.to(device) for k, v in encoded_input.items()}
        
        # Compute token embeddings
        with torch.no_grad():
            model_output = model(**encoded_input)
            
        # Perform pooling
        batch_embeddings = mean_pooling(model_output, encoded_input['attention_mask'])
        
        # Normalize embeddings for cosine similarity
        batch_embeddings = torch.nn.functional.normalize(batch_embeddings, p=2, dim=1)
        embeddings.append(batch_embeddings.cpu().numpy())
        
        if (i + batch_size) % 64 == 0 or (i + batch_size) >= len(chunks):
            print(f"Processed {min(i + batch_size, len(chunks))}/{len(chunks)} chunks...")
            
    return np.vstack(embeddings)

def build_index(embeddings, chunks):
    """Builds and saves the FAISS index and metadata registry."""
    dimension = embeddings.shape[1]
    
    if FAISS_AVAILABLE:
        print(f"Building FAISS Index (dimension: {dimension})...")
        index = faiss.IndexFlatIP(dimension)  # IndexFlatIP does Inner Product (Cosine Similarity since vectors are normalized)
        index.add(embeddings.astype("float32"))
        
        faiss.write_index(index, INDEX_FILE)
        print(f"Saved FAISS index to: {INDEX_FILE}")
    else:
        # Fallback: save embeddings as a numpy binary file
        np.save("company_kb_embeddings.npy", embeddings)
        print("Saved embeddings matrix to: company_kb_embeddings.npy")
        
    # Save metadata mapping file
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2)
    print(f"Saved metadata registry to: {METADATA_FILE}")

def run_search(query, k=5):
    """Executes a similarity search against the FAISS index."""
    print(f"\nSearching for: '{query}'")
    
    if not os.path.exists(METADATA_FILE):
        print(f"Error: Metadata file {METADATA_FILE} not found. Run embedding first.")
        return
        
    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        chunks = json.load(f)
        
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModel.from_pretrained(MODEL_NAME)
    
    # Embed the query
    encoded_input = tokenizer([query], padding=True, truncation=True, max_length=512, return_tensors='pt')
    with torch.no_grad():
        model_output = model(**encoded_input)
    query_embedding = mean_pooling(model_output, encoded_input['attention_mask'])
    query_embedding = torch.nn.functional.normalize(query_embedding, p=2, dim=1).numpy()
    
    if FAISS_AVAILABLE and os.path.exists(INDEX_FILE):
        index = faiss.read_index(INDEX_FILE)
        # Search index
        scores, indices = index.search(query_embedding.astype("float32"), k)
        scores = scores[0]
        indices = indices[0]
    else:
        # Fallback numpy cosine similarity
        print("Using fallback NumPy search...")
        if os.path.exists("company_kb_embeddings.npy"):
            embeddings = np.load("company_kb_embeddings.npy")
            scores = np.dot(embeddings, query_embedding.T).flatten()
            indices = np.argsort(scores)[::-1][:k]
            scores = scores[indices]
        else:
            print("Error: Embeddings matrix file not found.")
            return

    # Print results
    print("\n--- Search Results ---")
    for idx, (score, doc_idx) in enumerate(zip(scores, indices), 1):
        if doc_idx < 0 or doc_idx >= len(chunks):
            continue
        chunk = chunks[doc_idx]
        print(f"\nResult {idx} | Relevance Score: {score:.4f}")
        print(f"Document ID: {chunk['doc_id']} | File: {chunk['filepath']}")
        print(f"Department: {chunk['department']} | Section: {chunk['section']}")
        print("-" * 50)
        print(chunk['raw_content'])
        print("=" * 60)

def main():
    parser = argparse.ArgumentParser(description="Embed Inurum Knowledge Base files for RAG chatbot.")
    parser.add_argument("--search", type=str, help="Search query to run test retrieval")
    parser.add_argument("--k", type=int, default=3, help="Number of search results to return")
    args = parser.parse_args()

    if args.search:
        run_search(args.search, args.k)
    else:
        print("=== Inurum Technologies RAG Embedder ===")
        # 1. Load documents
        chunks = load_documents()
        if not chunks:
            print("No documents found in knowledge base directory. Exiting.")
            return
            
        # 2. Initialize Model
        print(f"Loading embedding model: {MODEL_NAME}")
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        model = AutoModel.from_pretrained(MODEL_NAME)
        
        # 3. Generate Embeddings
        embeddings = embed_chunks(chunks, tokenizer, model)
        
        # 4. Save Index and Metadata
        build_index(embeddings, chunks)
        print("\nAll documents indexed successfully! You can test searches using:")
        print("python embed_kb.py --search \"Your search query here\"")

if __name__ == "__main__":
    main()
