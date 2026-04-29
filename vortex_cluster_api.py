import time
import os
from multiprocessing.managers import BaseManager

class ClusterManager(BaseManager):
    pass

# We register the functions we'll expect from the remote manager
ClusterManager.register('get_work_queue')
ClusterManager.register('get_global_state')

class VortexClusterAPI:
    """
    Universal IPC API connector for Cluster Unit Agents.
    Forces standalone algorithms to dynamically checkout work chunks,
    guaranteeing zero mathematical duplicate hashes across 30+ nodes.
    """
    def __init__(self, port=50000, authkey=b'vortex_hive_mind'):
        self.manager = ClusterManager(address=('127.0.0.1', port), authkey=authkey)
        self._connected = False
        self.state = None
        self.queue = None
        
        # Only try to connect if we are running under the orchestrator
        if os.environ.get("VORTEX_BALANCER_LOCKED") == "1":
            self._connect()

    def _connect(self):
        for _ in range(5): # Give Orchestrator 5 seconds to boot the server
            try:
                self.manager.connect()
                self.state = self.manager.get_global_state()
                self.queue = self.manager.get_work_queue()
                self._connected = True
                print(f"🔗 [API] Cluster Sync Established.")
                return
            except ConnectionRefusedError:
                time.sleep(1)
        print("⚠️ [API] Warning: Cluster connection timed out. Falling back to standalone.")

    def is_connected(self) -> bool:
        return self._connected

    def check_global_halt(self) -> bool:
        """Checks if any node in the hive cracked the wallet."""
        if not self._connected: 
            return False
        try:
            return self.state.get("FOUND_KEY")
        except Exception:
            return False

    def broadcast_victory(self, private_key_hex: str, agent_name: str):
        """Broadcasts success up to the orchestrator to halt all 30 scripts."""
        if not self._connected:
            return
        try:
            self.state.update({
                "FOUND_KEY": True,
                "CRACKED_BY": agent_name,
                "KEY": private_key_hex
            })
            print(f"📡 [API] VICTORY BROADCASTED: {private_key_hex} found by {agent_name}!")
        except Exception as e:
            print(f"📡 [API Error] Failed to broadcast victory: {e}")

    def update_resonance(self, value: float):
        """Update the global resonance score (Vortex Conjunction Strength)."""
        if not self._connected: return
        try:
            current = self.state.get("RESONANCE_SCORE", 0.0)
            self.state.update({"RESONANCE_SCORE": current + value})
        except Exception:
            pass

    def get_resonance(self) -> float:
        """Get the current qualitative resonance level."""
        if not self._connected: return 0.0
        try:
            return self.state.get("RESONANCE_SCORE", 0.0)
        except Exception:
            return 0.0

    def checkout_cluster_bounds(self, agent_name: str, batch_size: int = 1000000) -> tuple:
        """
        Pulls a deterministic math chunk from the hive queue.
        If running standalone without orchestrator, falls back to random guessing.
        """
        if not self._connected:
            import random
            start = random.randint(1, 2**256 - batch_size)
            return start, start + batch_size
            
        try:
            # We fetch the definitive mathematical chunk from the hive queue
            chunk_start = self.queue.get(timeout=2)
            chunk_end = chunk_start + batch_size
            return chunk_start, chunk_end
        except Exception:
            return None, None
