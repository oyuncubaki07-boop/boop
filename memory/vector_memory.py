# -*- coding: utf-8 -*-
"""
J.A.R.V.I.S. Vektör Tabanlı Anı ve Bellek Yönetimi (ChromaDB Fallback Entegrasyonu)
"""

import os
import sys
import json
import logging
from pathlib import Path

logger = logging.getLogger("JARVIS_VectorMemory")

def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent

# Dinamik Kütüphane Yükleme
try:
    import chromadb
    from chromadb.config import Settings
    from sentence_transformers import SentenceTransformer
    HAS_VECTOR_DB = True
except ImportError:
    HAS_VECTOR_DB = False

class VectorMemory:
    def __init__(self):
        self.base_dir = get_base_dir()
        PERSIST_DIR = os.getenv("JARVIS_PERSISTENT_DIR", "")
        if HAS_VECTOR_DB:
            try:
                if PERSIST_DIR:
                    db_dir = os.path.join(PERSIST_DIR, "chroma_db")
                else:
                    db_dir = str(self.base_dir / "memory" / "chroma_db")
                self.client = chromadb.PersistentClient(path=db_dir)
                self.collection = self.client.get_or_create_collection("conversations")
                self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
                self.mode = "chroma"
                logger.info("[VectorMemory] ChromaDB ve SentenceTransformer aktif.")
                return
            except Exception as e:
                logger.warning(f"[VectorMemory] ChromaDB başlatılamadı: {e}. Fallback moduna geçiliyor.")
        
        # Fallback Modu (JSON tabanlı)
        self.mode = "fallback"
        if PERSIST_DIR:
            self.fallback_file = Path(os.path.join(PERSIST_DIR, "vector_memory_fallback.json"))
        else:
            self.fallback_file = self.base_dir / "memory" / "vector_memory_fallback.json"
        self.memories = []
        self._load_fallback()
        logger.info("[VectorMemory] Hafif JSON tabanlı anı hafızası aktif.")

    def _load_fallback(self):
        if self.fallback_file.exists():
            try:
                with open(self.fallback_file, "r", encoding="utf-8") as f:
                    self.memories = json.load(f)
            except Exception as e:
                logger.warning(f"[VectorMemory] Fallback hafıza dosyası okunamadı: {e}")
                self.memories = []

    def _save_fallback(self):
        try:
            self.fallback_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.fallback_file, "w", encoding="utf-8") as f:
                json.dump(self.memories, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"[VectorMemory] Fallback hafıza dosyası kaydedilemedi: {e}")

    def add_memory(self, text: str, metadata: dict = None):
        """Hafızaya yeni bir anı ekler."""
        if not text or not text.strip():
            return

        if self.mode == "chroma":
            try:
                embedding = self.model.encode(text).tolist()
                doc_id = str(hash(text) + hash(os.urandom(4)))
                self.collection.add(
                    documents=[text],
                    embeddings=[embedding],
                    metadatas=[metadata or {}],
                    ids=[doc_id]
                )
                logger.info("[VectorMemory] Anı ChromaDB veritabanına eklendi.")
                return
            except Exception as e:
                logger.error(f"[VectorMemory] ChromaDB anı ekleme hatası: {e}")

        # Fallback ekleme
        self.memories.append({
            "text": text,
            "metadata": metadata or {}
        })
        self._save_fallback()
        logger.info("[VectorMemory] Anı yerel JSON hafızasına eklendi.")

    def search_similar(self, query: str, n_results: int = 3) -> list[str]:
        """Arama kelimesine benzer geçmiş anıları döndürür."""
        if not query or not query.strip():
            return []

        if self.mode == "chroma":
            try:
                embedding = self.model.encode(query).tolist()
                results = self.collection.query(
                    query_embeddings=[embedding],
                    n_results=n_results
                )
                docs = results.get("documents", [[]])[0]
                return docs if docs else []
            except Exception as e:
                logger.error(f"[VectorMemory] ChromaDB arama hatası: {e}")

        # Fallback Arama (Basit anahtar kelime eşleştirme)
        query_words = set(query.lower().split())
        scored_memories = []
        for mem in self.memories:
            text = mem["text"]
            text_words = set(text.lower().split())
            intersection = query_words.intersection(text_words)
            if intersection:
                score = len(intersection) / len(query_words)
                scored_memories.append((score, text))

        # Puanına göre sırala ve en yüksek olanları seç
        scored_memories.sort(key=lambda x: x[0], reverse=True)
        return [text for score, text in scored_memories[:n_results]]

    def get_mindscape_data(self, query_text: str = None) -> str:
        """
        Generates JSON representation of memory points, associations, and active states for MindScape.
        """
        import numpy as np
        import json

        embeddings = []
        ids = []
        documents = []
        
        # Try fetching embeddings from ChromaDB
        if self.mode == "chroma":
            try:
                data = self.collection.get(include=["embeddings", "documents"])
                if data and data.get("ids"):
                    ids = data["ids"]
                    embeddings = data.get("embeddings", [])
                    documents = data.get("documents", [])
            except Exception as e:
                logger.error(f"[VectorMemory] Failed to get chroma embeddings: {e}")
                
        # Fallback to local memories if empty or in fallback mode
        if not ids:
            ids = [f"id_{i}" for i in range(len(self.memories))]
            documents = [mem["text"] for mem in self.memories]
            # Simple pseudo-embedding generation
            for doc in documents:
                vec = [0.0] * 12
                for char in doc:
                    vec[ord(char) % 12] += 1.0
                norm = np.linalg.norm(vec)
                if norm > 0:
                    vec = (np.array(vec) / norm).tolist()
                embeddings.append(vec)

        if not ids:
            return json.dumps({"points": [], "active_ids": [], "connections": []})

        embeddings = np.array(embeddings)
        
        # Calculate query embedding similarity
        query_emb = None
        if query_text and query_text.strip():
            if self.mode == "chroma" and hasattr(self, "model"):
                try:
                    query_emb = self.model.encode(query_text)
                except Exception:
                    pass
            if query_emb is None:
                vec = [0.0] * embeddings.shape[1]
                for char in query_text:
                    vec[ord(char) % len(vec)] += 1.0
                norm = np.linalg.norm(vec)
                if norm > 0:
                    query_emb = np.array(vec) / norm

        similarities = np.zeros(len(ids))
        if query_emb is not None:
            try:
                norms = np.linalg.norm(embeddings, axis=1)
                query_norm = np.linalg.norm(query_emb)
                if query_norm > 0:
                    norms[norms == 0] = 1.0
                    similarities = np.dot(embeddings, query_emb) / (norms * query_norm)
            except Exception as e:
                logger.error(f"[VectorMemory] Similarity calculation failed: {e}")

        active = np.where(similarities > 0.65)[0].tolist()
        active_ids = [ids[i] for i in active]

        # 2D projection
        projected_2d = None
        try:
            import umap
            reducer = umap.UMAP(n_components=2, random_state=42)
            projected_2d = reducer.fit_transform(embeddings)
        except Exception:
            try:
                # Fallback: PCA via SVD
                X = embeddings - np.mean(embeddings, axis=0)
                u, s, vt = np.linalg.svd(X, full_matrices=False)
                projected_2d = u[:, :2] * s[:2]
            except Exception:
                # Fallback 2: Deterministic pseudo-random projection
                rng = np.random.default_rng(42)
                projected_2d = rng.random((len(ids), 2))

        # Normalize 2D points to [0, 1] range
        try:
            min_vals = projected_2d.min(axis=0)
            max_vals = projected_2d.max(axis=0)
            ranges = max_vals - min_vals
            ranges[ranges == 0] = 1.0
            projected_2d = (projected_2d - min_vals) / ranges
        except Exception:
            pass

        # Prepare points list
        points = []
        for i in range(len(ids)):
            x, y = projected_2d[i]
            sim = similarities[i]
            points.append({
                'id': ids[i],
                'text': documents[i][:120],
                'x': float(x),
                'y': float(y),
                'brightness': float(sim) if query_emb is not None else 0.5,
                'color': [0, 212, 255] if ids[i] in active_ids else [143, 252, 255],
                'size': 3.0 + float(sim) * 5.0 if query_emb is not None else 4.0
            })

        # Calculate connections
        connections = []
        for i in range(len(points)):
            for j in range(i+1, len(points)):
                dist = np.sqrt((projected_2d[i][0] - projected_2d[j][0])**2 + (projected_2d[i][1] - projected_2d[j][1])**2)
                if dist < 0.25:
                    connections.append({
                        'from': ids[i],
                        'to': ids[j],
                        'strength': float(1.0 - (dist / 0.25))
                    })

        return json.dumps({"points": points, "active_ids": active_ids, "connections": connections})
