import os
import json
import faiss
import numpy as np
import torch
import ollama
from transformers import AutoTokenizer, AutoModel

from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import StreamingHttpResponse

# Paths to the newly generated FAISS index and metadata
BASE_DIR = "/Users/shubhamjain/Documents/pai/ModelPreTrain/inurum_kb"
INDEX_PATH = os.path.join(BASE_DIR, "company_kb.index")
METADATA_PATH = os.path.join(BASE_DIR, "company_kb_metadata.json")
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# 1. Load the FAISS vector index
if not os.path.exists(INDEX_PATH):
    raise FileNotFoundError(f"FAISS index file not found at: {INDEX_PATH}. Please run embed_kb.py first.")
index = faiss.read_index(INDEX_PATH)

# 2. Load the metadata registry
if not os.path.exists(METADATA_PATH):
    raise FileNotFoundError(f"Metadata registry not found at: {METADATA_PATH}. Please run embed_kb.py first.")
with open(METADATA_PATH, "r", encoding="utf-8") as f:
    metadata = json.load(f)

# Extract chunk texts corresponding to the index IDs
chunks = [item["chunk_text"] for item in metadata]

# 3. Load the embedding model locally at startup (aligns with the indexed dimensions)
print("Loading HuggingFace query embedding model...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME)
device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
model = model.to(device)
model.eval()

# Mean Pooling helper
def mean_pooling(model_output, attention_mask):
    token_embeddings = model_output[0]
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)


@api_view(['GET'])
def home(request):
    return Response({
        'message': 'Welcome to the company page!',
        'status': 'success',
    })


@api_view(['POST'])
def chatBot(request):
    question = request.data.get('question', "")

    if not question:
        return Response({
            'message': 'Question is required',
            'status': 'error',
        })

    # Encode query using the same sentence-transformers model (MPS-accelerated on Mac)
    encoded_input = tokenizer([question], padding=True, truncation=True, max_length=512, return_tensors='pt')
    encoded_input = {k: v.to(device) for k, v in encoded_input.items()}
    
    with torch.no_grad():
        model_output = model(**encoded_input)

    query_embedding = mean_pooling(model_output, encoded_input['attention_mask'])
    query_embedding = torch.nn.functional.normalize(query_embedding, p=2, dim=1)
    query_embedding = query_embedding.cpu().numpy().astype('float32')

    # Search FAISS index for top 3 matching chunks
    distance, indices = index.search(query_embedding, 3)

    # Retrieve context from chunks list
    context = ""
    for idx in indices[0]:
        if 0 <= idx < len(chunks):
            context += chunks[idx]
            context += "\n\n"

    # Prompt matching your template
    prompt = f"""<|im_start|>system
You are the AI assistant for Inurum Technologies.
Answer ONLY using the FACTS section below.
If the answer is not in FACTS, say exactly: "I couldn't find that information in the company knowledge base."
Never invent facts. Never say "context", "based on", or "according to".
Be concise and professional.<|im_end|>

<|im_start|>user
FACTS:
{context}

QUESTION: {question}
<|im_end|>

<|im_start|>assistant
"""

    def generate():
        try:
            stream = ollama.chat(
                model='qwen2.5:1.5b',
                messages=[{
                    'role': 'user',
                    'content': prompt
                }],
                stream=True
            )

            for chunk in stream:
                yield chunk['message']['content']
        except Exception as e:
            yield f"\n[Backend Error: {str(e)}]"

    return StreamingHttpResponse(
        generate(),
        content_type='text/plain'
    )
