import networkx as nx
import json
import os
from pathlib import Path

def get_base_dir() -> Path:
    import sys
    if getattr(sys, "frozen", False): return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent

BASE_DIR = get_base_dir()
PERSIST_DIR = os.getenv("JARVIS_PERSISTENT_DIR", "")
if PERSIST_DIR:
    GRAPH_FILE = Path(os.path.join(PERSIST_DIR, "brain_graph.json"))
else:
    GRAPH_FILE = BASE_DIR / "memory" / "brain_graph.json"

class CognitiveUniverse:
    def __init__(self):
        self.graph = nx.Graph()
        self.load_brain()

    def load_brain(self):
        """Hafızayı diskten yükler."""
        if GRAPH_FILE.exists():
            try:
                with open(GRAPH_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.graph = nx.node_link_graph(data)
            except:
                print("[Bilinç] Hafıza dosyası bozuk, yeni evren oluşturuluyor.")

    def save_brain(self):
        """Hafızayı diske kaydeder (Kuantum Hafıza)."""
        data = nx.node_link_data(self.graph)
        with open(GRAPH_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def learn_concept(self, concept1: str, relation: str, concept2: str):
        """İki kavram arasında mantıksal bir bağ kurar."""
        self.graph.add_edge(concept1.lower(), concept2.lower(), relation=relation)
        self.save_brain()
        print(f"[Bilinç Haritası] Yeni bağ kuruldu: {concept1} --({relation})--> {concept2}")

    def recall_connections(self, concept: str):
        """Bir kavramla ilgili bildiği her şeyi hatırlar."""
        concept = concept.lower()
        if concept in self.graph:
            connections = []
            for neighbor in self.graph.neighbors(concept):
                rel = self.graph[concept][neighbor]['relation']
                connections.append(f"{concept} {rel} {neighbor}")
            return connections
        return []

# Test Etmek İçin:
if __name__ == "__main__":
    brain = CognitiveUniverse()
    # Jarvis kendi kendine öğreniyor:
    brain.learn_concept("kullanici", "sahiptir", "gitar")
    brain.learn_concept("gitar", "kullanilir", "müzik yapmak")
    
    # Hatırlama testi:
    print(brain.recall_connections("kullanici"))