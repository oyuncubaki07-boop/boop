import nltk
import spacy
import networkx as nx

# Placeholder for a global knowledge graph (in a real system, this would be persistent)
# For this simulation, we'll use a simple in-memory graph
global_knowledge_graph = nx.DiGraph()

# spaCy model yüklemesi (ilk kullanımda indirme gerekebilir: python -m spacy download en_core_web_sm)
try:
    nlp = spacy.load("en_core_web_sm") # Genel İngilizce model, örneklerdeki Türkçe kavramlar için daha ileri özelleştirme gerekir.
except OSError:
    print("spaCy 'en_core_web_sm' modeli bulunamadı. Lütfen indirin: python -m spacy download en_core_web_sm")
    print("Model bulunamadığı için entity extraction çok basitleştirilmiş bir şekilde çalışacaktır.")
    nlp = None

def simulate_entity_extraction(text):
    entities = set()
    if nlp:
        doc = nlp(text)
        for ent in doc.ents:
            entities.add(ent.text)
        for token in doc:
            if token.pos_ == "NOUN" and len(token.text) > 2:
                entities.add(token.text)
    else: # Fallback if spaCy model is not loaded
        # Çok basitleştirilmiş kelime tabanlı ayrıştırma
        words = text.replace(',', '').replace('.', '').lower().split()
        # Örneklerdeki özel kavramları manuel olarak ekleme
        if "python" in text.lower(): entities.add("Python")
        if "programlama dili" in text.lower(): entities.add("Programlama Dili")
        if "yazılım geliştirme" in text.lower(): entities.add("Yazılım Geliştirme")

    return list(entities)

def simulate_relationship_detection(entities, text):
    relationships = []
    text_lower = text.lower()

    # Kavramsal İlişkiler (örneklerden)
    if "Python" in entities and "Programlama Dili" in entities and ("python bir programlama dilidir" in text_lower or "python is a programming language" in text_lower):
        relationships.append(("Python", "bir_türüdür", "Programlama Dili"))
    if "Programlama Dili" in entities and "Yazılım Geliştirme" in entities and ("yazılım geliştirme için kullanılır" in text_lower or "used for software development" in text_lower):
        relationships.append(("Programlama Dili", "için_kullanılır", "Yazılım Geliştirme"))
    
    # Genel 'ilişkili' ilişkisi (basit yakınlık kontrolü)
    for i in range(len(entities)):
        for j in range(i + 1, len(entities)):
            e1 = entities[i]
            e2 = entities[j]
            if e1 in text and e2 in text and abs(text.find(e1) - text.find(e2)) < 50:
                if (e1, "ilişkili", e2) not in relationships and (e2, "ilişkili", e1) not in relationships:
                     relationships.append((e1, "ilişkili", e2))
    return relationships

def run_action(params):
    global global_knowledge_graph, nlp
    information_units = params.get("information_units", [])
    return_insights = params.get("return_insights", False)

    if not information_units:
        return {"status": "error", "message": "Entegre edilecek bilgi birimleri sağlanmadı."}

    integrated_info_count = 0
    new_nodes_added = 0
    new_edges_added = 0
    insights = []

    for unit_text in information_units:
        # 1. Bilgi Parçacığı Ayrıştırma (Simülasyon)
        concepts = simulate_entity_extraction(unit_text)

        # 2. İlişki Tespiti (Simülasyon)
        relationships = simulate_relationship_detection(concepts, unit_text)

        # 3. Ağ İnşası/Genişletme
        for concept in concepts:
            if concept not in global_knowledge_graph:
                global_knowledge_graph.add_node(concept, type="concept")
                new_nodes_added += 1
        
        for source, rel_type, target in relationships:
            # Düğümlerin varlığını kontrol et ve ekle
            if source not in global_knowledge_graph:
                global_knowledge_graph.add_node(source, type="concept")
                new_nodes_added += 1
            if target not in global_knowledge_graph:
                global_knowledge_graph.add_node(target, type="concept")
                new_nodes_added += 1
            
            # Kenarı ekle veya güncelle
            if not global_knowledge_graph.has_edge(source, target) or global_knowledge_graph[source][target].get('type') != rel_type:
                global_knowledge_graph.add_edge(source, target, type=rel_type)
                new_edges_added += 1
                insights.append(f"Yeni ilişki kuruldu: '{source}' --{rel_type}--> '{target}'")
        
        integrated_info_count += 1
    
    result = {
        "status": "success",
        "message": f"{integrated_info_count} bilgi birimi başarıyla bilgi ağına entegre edildi.",
        "total_nodes_in_graph": global_knowledge_graph.number_of_nodes(),
        "total_edges_in_graph": global_knowledge_graph.number_of_edges(),
        "new_nodes_added_in_this_run": new_nodes_added,
        "new_edges_added_in_this_run": new_edges_added
    }

    if return_insights and insights:
        result["insights"] = insights
    elif return_insights and not insights and integrated_info_count > 0:
        result["insights"] = ["Entegre edilen bilgilerden belirgin yeni içgörüler veya ilişkiler tespit edilemedi."]
    elif return_insights and integrated_info_count == 0:
        result["insights"] = ["Hiçbir bilgi birimi entegre edilmediği için içgörü bulunamadı."]

    return result