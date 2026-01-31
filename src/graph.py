import json
import os

class KnowledgeGraph:
    def __init__(self, config_path="config/neighbors.json"):
        if not os.path.isabs(config_path):
            # Assume relative to project root if running from root
            config_path = os.path.abspath(config_path)
            
        self.config_path = config_path
        self.graph = self._load_graph()

    def _load_graph(self) -> dict:
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading graph from {self.config_path}: {e}")
            return {}

    def get_core_tickers(self) -> list:
        return list(self.graph.keys())

    def get_neighbors(self, core_ticker: str) -> list:
        node = self.graph.get(core_ticker)
        if node:
            return node.get("neighbors", [])
        return []

    def get_sector(self, core_ticker: str) -> str:
        node = self.graph.get(core_ticker)
        return node.get("sector", "Unknown") if node else "Unknown"

    def get_ripple_logic(self, core_ticker: str) -> str:
        node = self.graph.get(core_ticker)
        return node.get("ripple_logic", "") if node else ""

if __name__ == "__main__":
    kg = KnowledgeGraph()
    cores = kg.get_core_tickers()
    print(f"Loaded {len(cores)} core tickers: {cores}")
    if cores:
        print(f"Neighbors of {cores[0]}: {kg.get_neighbors(cores[0])}")
