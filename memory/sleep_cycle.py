import os
import sys
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to sys.path
PROJE_DIZINI = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJE_DIZINI not in sys.path:
    sys.path.insert(0, PROJE_DIZINI)

from memory.graph_db import get_graph_db
from memory.memory_manager import load_memory
from core.services.or_client import client

PERSIST_DIR = os.getenv("JARVIS_PERSISTENT_DIR", "")
if PERSIST_DIR:
    TIME_CAPSULE_PATH = Path(os.path.join(PERSIST_DIR, "infinity", "time_capsule.jsonl"))
else:
    TIME_CAPSULE_PATH = Path(PROJE_DIZINI) / "memory" / "infinity" / "time_capsule.jsonl"

async def run_sleep_cycle(manual_trigger: bool = False):
    """
    Consolidates last 24h memories and events, resolves contradictions via AI,
    and decays old nodes.
    """
    print(f"[SleepCycle] 🌙 Starting consolidation cycle (Manual: {manual_trigger})...")
    
    # 1. Fetch last 24h episodes from flat long_term memory
    episodes_24h = fetch_flat_memory_updates_24h()
    
    # 2. Fetch last 24h events from time_capsule.jsonl
    events_24h = fetch_time_capsule_events_24h()
    
    if not episodes_24h and not events_24h:
        print("[SleepCycle] 💤 No new memories or events found in the last 24 hours. Cycle skipped.")
        return
        
    print(f"[SleepCycle] Found {len(episodes_24h)} flat category updates and {len(events_24h)} event logs.")
    
    # 3. Clean duplicate/contradictory memories using LLM
    consolidated_data = await resolve_memory_conflicts_via_ai(episodes_24h, events_24h)
    
    # 4. Write to graph database
    db = get_graph_db()
    await db.connect()
    try:
        if consolidated_data and (consolidated_data.get("nodes") or consolidated_data.get("edges")):
            print(f"[SleepCycle] Writing {len(consolidated_data.get('nodes', []))} consolidated nodes and {len(consolidated_data.get('edges', []))} edges to Graph DB...")
            await db.write_memory(consolidated_data)
        else:
            # Fallback to direct writes if AI consolidation was empty
            print("[SleepCycle] AI consolidation empty. Writing raw data instead.")
            raw_episode = {
                "nodes": [],
                "edges": []
            }
            # Simple mapping of category items
            user_id = "user_sir"
            raw_episode["nodes"].append({
                "id": user_id,
                "type": "Person",
                "properties": {"name": "Sir", "last_seen": time.time(), "weight": 1.0}
            })
            for cat, key, val in episodes_24h:
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
                
                node_id = f"{node_type.lower()}_{key}"
                raw_episode["nodes"].append({
                    "id": node_id,
                    "type": node_type,
                    "properties": {"name": key.replace("_", " ").title(), "description": val, "last_seen": time.time(), "weight": 1.0}
                })
                raw_episode["edges"].append({
                    "source": user_id,
                    "target": node_id,
                    "type": edge_type,
                    "properties": {"timestamp": time.time()}
                })
            
            # Map events
            for ev in events_24h:
                ev_id = f"event_{int(ev.get('timestamp', time.time()))}"
                raw_episode["nodes"].append({
                    "id": ev_id,
                    "type": "Event",
                    "properties": {
                        "name": ev.get("kind", "Interaction"),
                        "description": ev.get("detail", ""),
                        "last_seen": time.time(),
                        "weight": 1.0
                    }
                })
                raw_episode["edges"].append({
                    "source": user_id,
                    "target": ev_id,
                    "type": "RELATED_TO",
                    "properties": {"timestamp": time.time()}
                })
            await db.write_memory(raw_episode)
            
        # 5. Decay old nodes
        await db.decay_old_nodes()
        
    finally:
        await db.close()
        
    print("[SleepCycle] ✨ Consolidation sleep cycle completed successfully.")

def fetch_flat_memory_updates_24h() -> list[tuple[str, str, str]]:
    """Loads flat memory and filters for items updated in the last 24h."""
    memory = load_memory()
    updates = []
    
    # Threshold date format is YYYY-MM-DD
    yesterday = datetime.now() - timedelta(days=1)
    threshold_str = yesterday.strftime("%Y-%m-%d")
    
    for category, items in memory.items():
        if not isinstance(items, dict):
            continue
        for key, entry in items.items():
            if isinstance(entry, dict):
                updated_date = entry.get("updated", "0000-00-00")
                if updated_date >= threshold_str:
                    val = entry.get("value", "")
                    updates.append((category, key, val))
    return updates

def fetch_time_capsule_events_24h() -> list[dict]:
    """Reads events from time_capsule.jsonl that occurred in the last 24h."""
    events = []
    if not TIME_CAPSULE_PATH.exists():
        return events
        
    yesterday_limit = datetime.now() - timedelta(days=1)
    
    try:
        with open(TIME_CAPSULE_PATH, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    ev = json.loads(line)
                    ts_str = ev.get("ts")
                    if ts_str:
                        # Format is YYYY-MM-DD HH:MM:SS
                        dt = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                        if dt >= yesterday_limit:
                            ev["timestamp"] = dt.timestamp()
                            events.append(ev)
                except Exception:
                    pass
    except Exception as e:
        print(f"[SleepCycle] Error reading time capsule events: {e}")
        
    return events

async def resolve_memory_conflicts_via_ai(flat_updates: list, events: list) -> dict:
    """Uses OpenRouter LLM to clean duplicate/contradictory facts and events into a structured graph."""
    facts = []
    for cat, key, val in flat_updates:
        facts.append({
            "source": "memory_manager",
            "category": cat,
            "key": key,
            "value": val
        })
    for ev in events:
        facts.append({
            "source": "event_log",
            "kind": ev.get("kind"),
            "detail": ev.get("detail"),
            "time": ev.get("ts")
        })

    prompt = (
        "You are J.A.R.V.I.S.'s internal Cognitive Sleep Cycle Consolidator.\n"
        "Your task is to review the raw memory logs from the past 24 hours, identify contradictions or redundancies, "
        "and organize them into a clean, structured cognitive knowledge graph containing unique nodes and edges.\n\n"
        "Input Data (Recent Facts & Events):\n"
        f"{json.dumps(facts, indent=2)}\n\n"
        "Rules:\n"
        "1. Identify contradictions (e.g. if the user changed a preference or details about a project). Keep only the latest or most accurate fact.\n"
        "2. Resolve duplicates. If the same fact appears multiple times, merge it into a single clean description.\n"
        "3. Map facts and events into these exact types:\n"
        "   - Node Types: Person, Project, Concept, Event, File\n"
        "   - Edge Types: WORKS_ON, RELATED_TO, CAUSED_BY, IMPROVES, USES\n"
        "4. Always link nodes back to the user ('user_sir' as a Person node representing 'Sir').\n\n"
        "Return ONLY valid JSON using this format. Do not add markdown backticks or explanation:\n"
        "{\n"
        '  "nodes": [\n'
        '    {"id": "user_sir", "type": "Person", "properties": {"name": "Sir"}},\n'
        '    {"id": "unique_node_id", "type": "Person|Project|Concept|Event|File", "properties": {"name": "Name of node", "description": "Merged description", "weight": 1.0}}\n'
        '  ],\n'
        '  "edges": [\n'
        '    {"source": "user_sir", "target": "unique_node_id", "type": "WORKS_ON|RELATED_TO|CAUSED_BY|IMPROVES|USES", "properties": {}}\n'
        '  ]\n'
        "}"
    )

    try:
        # We run this in a non-blocking thread since requests is sync
        res = await asyncio.to_thread(client.chat_json, prompt)
        if isinstance(res, dict) and "nodes" in res:
            print(f"[SleepCycle] AI successfully consolidated {len(facts)} facts into a clean graph structure.")
            return res
    except Exception as e:
        print(f"[SleepCycle] AI consolidation failed: {e}. Falling back to default heuristics.")
        
    return {}

if __name__ == "__main__":
    # Test execution
    asyncio.run(run_sleep_cycle(manual_trigger=True))
