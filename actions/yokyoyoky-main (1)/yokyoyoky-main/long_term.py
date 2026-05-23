import chromadb
from chromadb.config import Settings
import os

# J.A.R.V.I.S. Uzun Süreli Hafıza Merkezi
class JarvisMemory:
    def __init__(self):
        self.path = os.path.join(os.getcwd(), "memory", "chroma_db")
        self.client = chromadb.PersistentClient(path=self.path)
        self.collection = self.client.get_or_create_collection(name="jarvis_brain")

    def remember(self, key, info):
        """Bilgiyi kalıcı hafızaya yazar."""
        self.collection.add(
            documents=[info],
            ids=[key]
        )

    def recall(self, query):
        """Hafızadan bilgi çağırır."""
        results = self.collection.query(
            query_texts=[query],
            n_results=1
        )
        return results['documents'][0] if results['documents'] else "Bu konuda henüz bir bilgim yok patron."

# Sosyal Analiz Modülü: Arkadaşlarını tanıması için
def social_analyzer(parameters=None, player=None):
    mem = JarvisMemory()
    params = parameters or {}
    name = params.get("name")
    trait = params.get("trait") # 'samimi', 'resmi', 'kanka' vb.
    
    if name and trait:
        mem.remember(f"social_{name}", f"{name} ile olan ilişki tipi: {trait}")
        if player: player.write_log(f"AI: {name} kişisi '{trait}' olarak hafızaya işlendi.")
        return f"{name} artık hafızamda {trait} olarak kayıtlı. Ona göre davranacağım."