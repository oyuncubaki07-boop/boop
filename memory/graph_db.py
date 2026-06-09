import os
import sys
import json
import time
import asyncio
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to sys.path
PROJE_DIZINI = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJE_DIZINI not in sys.path:
    sys.path.insert(0, PROJE_DIZINI)

# Optional imports with graceful fallback
NEO4J_AVAILABLE = False
try:
    from neo4j import AsyncGraphDatabase, exceptions as neo4j_exceptions
    NEO4J_AVAILABLE = True
except ImportError:
    pass

import networkx as nx

# Paths
DB_DIR = Path(__file__).resolve().parent
PERSIST_DIR = os.getenv("JARVIS_PERSISTENT_DIR", "")
if PERSIST_DIR:
    GRAPH_FILE = Path(os.path.join(PERSIST_DIR, "cognitive_graph.json"))
else:
    GRAPH_FILE = DB_DIR / "cognitive_graph.json"

class GraphDB:
    def __init__(self):
        self.uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.environ.get("NEO4J_USER", "neo4j")
        self.password = os.environ.get("NEO4J_PASSWORD", "password")
        self.driver = None
        self.use_neo4j = False
        self.nx_graph = nx.MultiDiGraph()
        self._load_local_graph()

    async def connect(self):
        """Initializes connection to Neo4j, falls back to NetworkX on failure."""
        if not NEO4J_AVAILABLE:
            print("[GraphDB] Neo4j library not installed. Using NetworkX fallback.")
            self.use_neo4j = False
            return

        try:
            self.driver = AsyncGraphDatabase.driver(self.uri, auth=(self.user, self.password))
            # Verify connectivity
            async with self.driver.session() as session:
                await session.run("RETURN 1")
            self.use_neo4j = True
            print("[GraphDB] Connected to Neo4j successfully.")
        except Exception as e:
            print(f"[GraphDB] Failed to connect to Neo4j: {e}. Falling back to NetworkX.")
            self.use_neo4j = False
            if self.driver:
                await self.driver.close()
                self.driver = None

    async def close(self):
        if self.driver:
            await self.driver.close()
            self.driver = None

    def _load_local_graph(self):
        """Loads the local NetworkX graph from disk."""
        if GRAPH_FILE.exists():
            try:
                with open(GRAPH_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.nx_graph = nx.node_link_graph(data)
                print(f"[GraphDB] Loaded NetworkX graph from {GRAPH_FILE.name}")
            except Exception as e:
                print(f"[GraphDB] Error loading NetworkX graph: {e}. Creating new graph.")
                self.nx_graph = nx.MultiDiGraph()
        else:
            self.nx_graph = nx.MultiDiGraph()

    def _save_local_graph(self):
        """Saves the local NetworkX graph to disk."""
        try:
            data = nx.node_link_data(self.nx_graph)
            with open(GRAPH_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[GraphDB] Error saving NetworkX graph: {e}")

    async def write_memory(self, episode: dict):
        """
        Creates nodes and edges for a given episode.
        Supports structured input (list of nodes and edges) or dictionary mapping.
        """
        nodes = episode.get("nodes", [])
        edges = episode.get("edges", [])

        # Auto-extract from unstructured/flat memory categories if present
        if not nodes and not edges:
            nodes, edges = self._parse_flat_episode(episode)

        if not nodes:
            return

        if self.use_neo4j and self.driver:
            await self._write_neo4j(nodes, edges)
        else:
            await self._write_networkx(nodes, edges)

    def _parse_flat_episode(self, episode: dict) -> tuple[list, list]:
        """Parses a flat episode dict (e.g. from memory_manager) into nodes/edges."""
        nodes = []
        edges = []
        
        # We always have a Person: Sir/User
        user_id = "user_sir"
        nodes.append({
            "id": user_id,
            "type": "Person",
            "properties": {"name": "Sir", "last_seen": time.time(), "weight": 1.0}
        })
        
        # Parse flat categories
        for cat, items in episode.items():
            if not isinstance(items, dict):
                continue
            for key, val in items.items():
                val_str = val.get("value", str(val)) if isinstance(val, dict) else str(val)
                node_type = "Concept"
                edge_type = "RELATED_TO"
                
                if cat == "projects":
                    node_type = "Project"
                    edge_type = "WORKS_ON"
                elif cat == "relationships":
                    node_type = "Person"
                    edge_type = "RELATED_TO"
                elif cat == "notes":
                    node_type = "Concept"
                    edge_type = "USES"
                elif cat == "identity":
                    node_type = "Concept"
                    edge_type = "RELATED_TO"
                
                node_id = f"{node_type.lower()}_{key}"
                nodes.append({
                    "id": node_id,
                    "type": node_type,
                    "properties": {"name": key.replace("_", " ").title(), "description": val_str, "last_seen": time.time(), "weight": 1.0}
                })
                
                edges.append({
                    "source": user_id,
                    "target": node_id,
                    "type": edge_type,
                    "properties": {"timestamp": time.time()}
                })
                
        return nodes, edges

    async def _write_neo4j(self, nodes: list, edges: list):
        """Writes nodes and edges to Neo4j database."""
        async with self.driver.session() as session:
            # 1. Write Nodes
            for node in nodes:
                node_id = node["id"]
                node_type = node.get("type", "Concept")
                props = node.get("properties", {})
                props["id"] = node_id
                props["last_seen"] = props.get("last_seen", time.time())
                props["weight"] = props.get("weight", 1.0)
                
                # Cypher query to merge nodes
                query = f"""
                MERGE (n:{node_type} {{id: $id}})
                ON CREATE SET n = $props
                ON MATCH SET n.last_seen = $props.last_seen, n.weight = $props.weight, n.name = $props.name
                """
                await session.run(query, id=node_id, props=props)

            # 2. Write Edges
            for edge in edges:
                source = edge["source"]
                target = edge["target"]
                edge_type = edge.get("type", "RELATED_TO")
                props = edge.get("properties", {})
                props["timestamp"] = props.get("timestamp", time.time())

                query = f"""
                MATCH (s {{id: $source}}), (t {{id: $target}})
                MERGE (s)-[r:{edge_type}]->(t)
                ON CREATE SET r = $props
                ON MATCH SET r.timestamp = $props.timestamp
                """
                await session.run(query, source=source, target=target, props=props)

    async def _write_networkx(self, nodes: list, edges: list):
        """Writes nodes and edges to local NetworkX MultiDiGraph and saves it."""
        for node in nodes:
            node_id = node["id"]
            node_type = node.get("type", "Concept")
            props = node.get("properties", {})
            props["type"] = node_type
            props["last_seen"] = props.get("last_seen", time.time())
            props["weight"] = props.get("weight", 1.0)
            
            if self.nx_graph.has_node(node_id):
                # Update properties
                self.nx_graph.nodes[node_id].update(props)
            else:
                self.nx_graph.add_node(node_id, **props)

        for edge in edges:
            source = edge["source"]
            target = edge["target"]
            edge_type = edge.get("type", "RELATED_TO")
            props = edge.get("properties", {})
            props["timestamp"] = props.get("timestamp", time.time())
            
            # Check if edge already exists to prevent duplicate MultiDiGraph edges
            exists = False
            if self.nx_graph.has_edge(source, target):
                for key in self.nx_graph[source][target]:
                    if self.nx_graph[source][target][key].get("relation") == edge_type:
                        self.nx_graph[source][target][key].update(props)
                        exists = True
                        break
            
            if not exists:
                self.nx_graph.add_edge(source, target, relation=edge_type, **props)

        await asyncio.to_thread(self._save_local_graph)

    async def query_context(self, query: str) -> list[dict]:
        """
        Returns related nodes within 2 hops of matching query nodes.
        Returns a list of dicts describing nodes and relations.
        """
        if self.use_neo4j and self.driver:
            return await self._query_neo4j(query)
        else:
            return await self._query_networkx(query)

    async def _query_neo4j(self, query: str) -> list[dict]:
        results = []
        async with self.driver.session() as session:
            # Query nodes matching query, retrieve them and their 1-2 hop neighbors
            cypher = """
            MATCH (n)
            WHERE toLower(n.name) CONTAINS toLower($query) 
               OR toLower(n.description) CONTAINS toLower($query)
               OR toLower(n.id) CONTAINS toLower($query)
            MATCH (n)-[r*1..2]-(m)
            RETURN DISTINCT n, r, m LIMIT 50
            """
            result = await session.run(cypher, query=query)
            async for record in result:
                n = record["n"]
                m = record["m"]
                results.append({
                    "source": {"id": n["id"], "type": list(n.labels)[0], "name": n.get("name", "")},
                    "target": {"id": m["id"], "type": list(m.labels)[0], "name": m.get("name", "")}
                })
        return results

    async def _query_networkx(self, query: str) -> list[dict]:
        results = []
        query_lower = query.lower()
        matching_nodes = []
        
        # Find matching nodes
        for node, data in self.nx_graph.nodes(data=True):
            name = str(data.get("name", "")).lower()
            desc = str(data.get("description", "")).lower()
            node_id = str(node).lower()
            if query_lower in name or query_lower in desc or query_lower in node_id:
                matching_nodes.append(node)

        visited = set()
        for root in matching_nodes:
            # 1-hop
            if root in self.nx_graph:
                # Out edges
                for neighbor in self.nx_graph.successors(root):
                    edge_key = (root, neighbor)
                    if edge_key not in visited:
                        visited.add(edge_key)
                        results.append({
                            "source": {"id": root, "type": self.nx_graph.nodes[root].get("type", "Concept"), "name": self.nx_graph.nodes[root].get("name", "")},
                            "target": {"id": neighbor, "type": self.nx_graph.nodes[neighbor].get("type", "Concept"), "name": self.nx_graph.nodes[neighbor].get("name", "")}
                        })
                    # 2-hop from neighbors
                    for neighbor_2 in self.nx_graph.successors(neighbor):
                        edge_key_2 = (neighbor, neighbor_2)
                        if edge_key_2 not in visited:
                            visited.add(edge_key_2)
                            results.append({
                                "source": {"id": neighbor, "type": self.nx_graph.nodes[neighbor].get("type", "Concept"), "name": self.nx_graph.nodes[neighbor].get("name", "")},
                                "target": {"id": neighbor_2, "type": self.nx_graph.nodes[neighbor_2].get("type", "Concept"), "name": self.nx_graph.nodes[neighbor_2].get("name", "")}
                            })
                # In edges (since Graph is Directed, traverse backwards too for fully connected 2-hops)
                for predecessor in self.nx_graph.predecessors(root):
                    edge_key = (predecessor, root)
                    if edge_key not in visited:
                        visited.add(edge_key)
                        results.append({
                            "source": {"id": predecessor, "type": self.nx_graph.nodes[predecessor].get("type", "Concept"), "name": self.nx_graph.nodes[predecessor].get("name", "")},
                            "target": {"id": root, "type": self.nx_graph.nodes[root].get("type", "Concept"), "name": self.nx_graph.nodes[root].get("name", "")}
                        })
                    for predecessor_2 in self.nx_graph.predecessors(predecessor):
                        edge_key_2 = (predecessor_2, predecessor)
                        if edge_key_2 not in visited:
                            visited.add(edge_key_2)
                            results.append({
                                "source": {"id": predecessor_2, "type": self.nx_graph.nodes[predecessor_2].get("type", "Concept"), "name": self.nx_graph.nodes[predecessor_2].get("name", "")},
                                "target": {"id": predecessor, "type": self.nx_graph.nodes[predecessor].get("type", "Concept"), "name": self.nx_graph.nodes[predecessor].get("name", "")}
                            })
        return results

    async def decay_old_nodes(self):
        """Reduces the weight of nodes that have not been updated or seen for 7+ days."""
        cutoff_time = time.time() - (7 * 24 * 3600)  # 7 days ago
        
        if self.use_neo4j and self.driver:
            async with self.driver.session() as session:
                # Decays weight of nodes older than cutoff
                cypher = """
                MATCH (n)
                WHERE n.last_seen < $cutoff
                SET n.weight = n.weight * 0.85
                """
                await session.run(cypher, cutoff=cutoff_time)
                # Optionally delete extremely low weight nodes
                delete_cypher = """
                MATCH (n)
                WHERE n.weight < 0.15 AND n.id <> "user_sir"
                DETACH DELETE n
                """
                await session.run(delete_cypher)
                print("[GraphDB] Decayed old nodes in Neo4j.")
        else:
            to_delete = []
            for node, data in self.nx_graph.nodes(data=True):
                if node == "user_sir":
                    continue
                last_seen = data.get("last_seen", 0.0)
                if last_seen < cutoff_time:
                    current_weight = data.get("weight", 1.0)
                    new_weight = current_weight * 0.85
                    self.nx_graph.nodes[node]["weight"] = new_weight
                    if new_weight < 0.15:
                        to_delete.append(node)
            
            if to_delete:
                for node in to_delete:
                    self.nx_graph.remove_node(node)
                print(f"[GraphDB] Pruned {len(to_delete)} decayed nodes from NetworkX graph.")
            
            await asyncio.to_thread(self._save_local_graph)
            print("[GraphDB] Decayed old nodes in NetworkX graph.")

# Global instance manager
_graph_instance = None

def get_graph_db() -> GraphDB:
    global _graph_instance
    if _graph_instance is None:
        _graph_instance = GraphDB()
    return _graph_instance
