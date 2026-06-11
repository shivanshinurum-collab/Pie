import os
import json
import hashlib
import re
import numpy as np
import faiss
import ollama

class RAGDatabase:
    def __init__(self, data_path="inurum_full_data.txt", db_json_path="inurum_db.json", db_index_path="inurum_db.index"):
        # Resolve data path: check current directory, then fallback to inurum_kb/
        if not os.path.exists(data_path) and os.path.exists(os.path.join("inurum_kb", data_path)):
            self.data_path = os.path.join("inurum_kb", data_path)
        else:
            self.data_path = data_path
            
        self.db_json_path = db_json_path
        self.db_index_path = db_index_path
        self.chunks = []
        self.index = None
        self.dimension = None

    def calculate_file_hash(self):
        if not os.path.exists(self.data_path):
            return ""
        hasher = hashlib.md5()
        with open(self.data_path, "rb") as f:
            buf = f.read()
            hasher.update(buf)
        return hasher.hexdigest()

    def chunk_markdown(self, text):
        lines = text.split('\n')
        temp_chunks = []
        
        current_section = ""
        current_h2 = ""
        current_h3 = ""
        current_h4 = ""
        
        current_chunk_lines = []
        
        def save_temp_chunk():
            if not current_chunk_lines:
                return
            
            content = "\n".join(current_chunk_lines).strip()
            if not content:
                return
                
            prefix_parts = []
            if current_section:
                prefix_parts.append(current_section)
            if current_h2:
                prefix_parts.append(current_h2)
            if current_h3:
                prefix_parts.append(current_h3)
            if current_h4:
                prefix_parts.append(current_h4)
                
            header_path = " > ".join(prefix_parts)
            temp_chunks.append((header_path, content))
            current_chunk_lines.clear()

        for line in lines:
            stripped = line.strip()
            
            # Check for section boundaries
            if stripped.startswith("SECTION "):
                save_temp_chunk()
                current_section = stripped
                current_h2 = ""
                current_h3 = ""
                current_h4 = ""
                continue
                
            # Ignore lines of just equal signs or dashes
            if set(stripped) == {'='} and len(stripped) > 3:
                continue
            if set(stripped) == {'-'} and len(stripped) > 3:
                save_temp_chunk()
                continue
                
            # Check for markdown headers
            if stripped.startswith("#### "):
                save_temp_chunk()
                current_h4 = stripped.lstrip("#").strip()
                continue
            elif stripped.startswith("### "):
                save_temp_chunk()
                current_h3 = stripped.lstrip("#").strip()
                current_h4 = ""
                continue
            elif stripped.startswith("## "):
                save_temp_chunk()
                current_h2 = stripped.lstrip("#").strip()
                current_h3 = ""
                current_h4 = ""
                continue
            elif stripped.startswith("# "):
                save_temp_chunk()
                current_section = stripped.lstrip("#").strip()
                current_h2 = ""
                current_h3 = ""
                current_h4 = ""
                continue
                
            current_chunk_lines.append(line)
            
        save_temp_chunk()
        
        # Split large chunks (e.g. lists of apps) into sub-chunks to avoid context bloat
        final_chunks = []
        for header_path, content in temp_chunks:
            if len(content) > 600:
                # Split by double newlines to keep paragraphs/items intact
                parts = re.split(r'\n\s*\n', content)
                
                sub_chunk = []
                for part in parts:
                    part = part.strip()
                    if not part:
                        continue
                    
                    # Accumulate parts up to a maximum length per sub-chunk
                    if sub_chunk and sum(len(p) for p in sub_chunk) + len(part) > 800:
                        sub_content = "\n\n".join(sub_chunk)
                        full_text = f"Context Path: {header_path}\n\n{sub_content}"
                        final_chunks.append({
                            "header_path": header_path,
                            "content": sub_content,
                            "full_text": full_text
                        })
                        sub_chunk = [part]
                    else:
                        sub_chunk.append(part)
                if sub_chunk:
                    sub_content = "\n\n".join(sub_chunk)
                    full_text = f"Context Path: {header_path}\n\n{sub_content}"
                    final_chunks.append({
                        "header_path": header_path,
                        "content": sub_content,
                        "full_text": full_text
                    })
            else:
                full_text = f"Context Path: {header_path}\n\n{content}"
                final_chunks.append({
                    "header_path": header_path,
                    "content": content,
                    "full_text": full_text
                })
                
        return final_chunks

    def build_database(self):
        print(f"Reading and chunking {self.data_path}...")
        with open(self.data_path, "r", encoding="utf-8") as f:
            text = f.read()
            
        self.chunks = self.chunk_markdown(text)
        print(f"Total chunks generated: {len(self.chunks)}")
        
        if not self.chunks:
            raise ValueError("No text chunks could be generated from the file.")
            
        print("Generating embeddings via Ollama (nomic-embed-text)...")
        embeddings = []
        for i, chunk in enumerate(self.chunks):
            # Single line status indicator
            print(f"Embedding chunk {i+1}/{len(self.chunks)}...", end="\r")
            res = ollama.embeddings(
                model="nomic-embed-text",
                prompt=chunk["full_text"]
            )
            embeddings.append(res["embedding"])
        print("\nEmbeddings generation complete.")
        
        vectors = np.array(embeddings).astype("float32")
        self.dimension = len(vectors[0])
        
        print("Building FAISS index...")
        self.index = faiss.IndexFlatL2(self.dimension)
        self.index.add(vectors)
        
        # Save to disk
        print("Saving database files to disk...")
        faiss.write_index(self.index, self.db_index_path)
        
        db_data = {
            "version": "v2",
            "file_hash": self.calculate_file_hash(),
            "chunks": self.chunks
        }
        with open(self.db_json_path, "w", encoding="utf-8") as f:
            json.dump(db_data, f, indent=2, ensure_ascii=False)
            
        print("Database build and save complete.")

    def load_database(self):
        current_hash = self.calculate_file_hash()
        
        # Check if database files exist
        if not os.path.exists(self.db_index_path) or not os.path.exists(self.db_json_path):
            print("Database files not found. Building database from scratch...")
            self.build_database()
            return
            
        # Load JSON database content
        try:
            with open(self.db_json_path, "r", encoding="utf-8") as f:
                db_data = json.load(f)
        except Exception as e:
            print(f"Error reading JSON database: {e}. Rebuilding...")
            self.build_database()
            return
            
        # Verify hash and version match
        if db_data.get("file_hash") != current_hash or db_data.get("version") != "v2":
            print("Source data file or database version has changed. Rebuilding database...")
            self.build_database()
            return
            
        # Load FAISS index
        try:
            self.index = faiss.read_index(self.db_index_path)
            self.chunks = db_data["chunks"]
            self.dimension = self.index.d
            print(f"Loaded existing database from cache successfully ({len(self.chunks)} chunks).")
        except Exception as e:
            print(f"Error reading FAISS index: {e}. Rebuilding...")
            self.build_database()
            return

    def search(self, question, k=3):
        # Question embedding
        res = ollama.embeddings(
            model="nomic-embed-text",
            prompt=question
        )
        q_emb = res["embedding"]
        query_vector = np.array([q_emb]).astype("float32")
        
        # Search similar chunks
        D, I = self.index.search(query_vector, k=k)
        
        retrieved_chunks = []
        for idx in I[0]:
            if idx >= 0 and idx < len(self.chunks):
                retrieved_chunks.append(self.chunks[idx])
        return retrieved_chunks

# -----------------------
# MAIN EXECUTION
# -----------------------
if __name__ == "__main__":
    db = RAGDatabase()
    db.load_database()

    # Chat loop
    print("\n--- Inurum Technologies RAG Chatbot ---")
    print("Ask any question about Inurum. Type 'exit' to quit.")
    
    while True:
        try:
            question = input("\nYou: ").strip()
            if not question:
                continue
            if question.lower() == 'exit':
                print("Goodbye!")
                break
                
            # Retrieve similar chunks
            retrieved = db.search(question, k=3)
            
            # Format context with section path and chunk contents
            context_blocks = []
            for i, chunk in enumerate(retrieved):
                context_blocks.append(chunk["full_text"])
            
            context = "\n\n---\n\n".join(context_blocks)
            
            print("\n--- Retrieved Context ---")
            print(context)
            print("-------------------------")
            
            # Generate LLM response
            response = ollama.chat(
                model="llama3",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful AI assistant for Inurum Technologies. Answer the question accurately using ONLY the provided context. If the answer cannot be found in the context, say 'I cannot find the answer in the context.'"
                    },
                    {
                        "role": "user",
                        "content": f"Context:\n{context}\n\nQuestion: {question}"
                    }
                ]
            )
            
            print("\nBot:", response["message"]["content"])
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError occurred: {e}")