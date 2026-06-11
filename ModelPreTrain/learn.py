import ollama
import faiss
import numpy as np

# -----------------------
# 1. LOAD DATA
# -----------------------
with open("data.txt", "r") as f:
    text = f.read()

# Split into chunks (simple for now)
chunks = [chunk.strip() for chunk in text.split("\n") if chunk.strip()]

print(f"Total chunks: {len(chunks)}")

# -----------------------
# 2. CREATE EMBEDDINGS
# -----------------------
embeddings = []

for chunk in chunks:
    res = ollama.embeddings(
        model="nomic-embed-text",
        prompt=chunk
    )
    embeddings.append(res["embedding"])

# Convert to numpy array
vectors = np.array(embeddings).astype("float32")

# -----------------------
# 3. CREATE VECTOR DB (FAISS)
# -----------------------
dimension = len(vectors[0])
index = faiss.IndexFlatL2(dimension)
index.add(vectors)

print("Vector DB ready!")

# -----------------------
# 4. CHAT LOOP
# -----------------------
while True:
    question = input("\nYou: ")

    # Question embedding
    q_emb = ollama.embeddings(
        model="nomic-embed-text",
        prompt=question
    )["embedding"]

    query_vector = np.array([q_emb]).astype("float32")

    # Search similar chunks
    D, I = index.search(query_vector, k=3)

    # Get relevant context
    context = "\n".join([chunks[i] for i in I[0]])

    print("\n--- Retrieved Context ---")
    print(context)

    # # LLM response
    # response = ollama.chat(
    #     model="llama3",
    #     messages=[
    #         {
    #             "role": "system",
    #             "content": "Answer only from given context."
    #         },
    #         {
    #             "role": "user",
    #             "content": f"""
    #             Context: {context}
    #             Question: {question}"""
    #         }
    #     ]
    # )

    # print("\nBot:", response["message"]["content"])