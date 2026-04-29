import os
import sys
import time
import subprocess
import threading
import json
import psutil
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from multiprocessing.managers import BaseManager
import queue

# Import the native quantum balancer to use its actual hardware probes
from quantum_balancer import QuantumBalancer

class ClusterManager(BaseManager):
    pass

class UnifiedVortexOrchestrator:
    """
    Central Daemon handling the simultaneous execution of all advanced
    mining simulation modules, dynamically throttled to hardware bounds.
    """
    def __init__(self, workspace_dir="."):
        self.workspace_dir = workspace_dir
        self.quantum_balancer = QuantumBalancer()
        
        # Identifying heavy executable modules based on their naming patterns
        self.executable_patterns = [
            "breaker.py", "accelerator.py", "mapper.py", 
            "finder.py", "recovery.py", "_vortex_satoshi.py"
        ]
        
        # Ignored files that are pure utilities or libraries
        self.ignore_list = [
            "ecc_operations.py", "crypto_trigger.py", "quantum_balancer.py",
            "show_key.py", "generate_phrase.py"
        ]
        
        self.active_processes = {}
        self.log_queue = deque(maxlen=100)
        self.is_running = True
        self.max_concurrent_nodes = max(1, psutil.cpu_count(logical=True) - 2)
        
        # --- API Server Initialization ---
        self.work_queue = queue.Queue(maxsize=1000)
        self.global_state = {
            "FOUND_KEY": False, 
            "CRACKED_BY": "", 
            "KEY": "",
            "RESONANCE_SCORE": 0.0 # Your new 7zip Intelligence Metric
        }
        
        # Initialize the global bounds (e.g. standard starting offset or loaded from disk)
        self.current_hive_offset = 0x6000000000000000000000000000000000000000000000000000000000000000
        self.chunk_size = 1000000
        
        self._start_cluster_api_server()
        
    def _start_cluster_api_server(self):
        """Spawns the local IPC SyncManager for drones to checkout chunks."""
        ClusterManager.register('get_work_queue', callable=lambda: self.work_queue)
        ClusterManager.register('get_global_state', callable=lambda: self.global_state)
        
        self.manager = ClusterManager(address=('127.0.0.1', 50000), authkey=b'vortex_hive_mind')
        self.manager_server = self.manager.get_server()
        
        threading.Thread(target=self.manager_server.serve_forever, daemon=True).start()
        print("🔗 [ORCHESTRATOR] Cluster API Server bound to 127.0.0.1:50000")
        
        # Thread to keep the queue seeded ahead of time
        threading.Thread(target=self._seed_key_queue, daemon=True).start()

    def _seed_key_queue(self):
        """Continuously feeds mathematically distinct chunks into the hive queue."""
        while self.is_running:
            if not self.work_queue.full():
                self.work_queue.put(self.current_hive_offset)
                self.current_hive_offset += self.chunk_size
            else:
                time.sleep(1)
        
    def _discover_nodes(self):
        """Scans the directory for valid executables matching our architecture."""
        nodes_to_run = []
        for file in os.listdir(self.workspace_dir):
            if file.endswith(".py") and file not in self.ignore_list:
                if any(file.endswith(p) for p in self.executable_patterns):
                    nodes_to_run.append(file)
        return sorted(nodes_to_run)

    def _stream_output(self, process, node_name):
        """Reads stdout from a subprocess continuously without blocking."""
        try:
            for line in iter(process.stdout.readline, b''):
                if not self.is_running:
                    break
                decoded_line = line.decode('utf-8', errors='replace').strip()
                if decoded_line:
                    # Print to orchestrator terminal securely prefixed
                    print(f"[{node_name}] {decoded_line}")
        except Exception:
            pass

    def run_node(self, node_filename):
        """Spawns an individual python node natively."""
        print(f"🌌 [ORCHESTRATOR] Spawning Node: {node_filename}")
        
        # Setup environmentally injected variables for IPC 
        env_vars = os.environ.copy()
        env_vars["VORTEX_BALANCER_LOCKED"] = "1"
        env_vars["RAM_GATE_SHARED"] = "1"
        
        try:
            process = subprocess.Popen(
                [sys.executable, node_filename],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Combine stdout and stderr
                cwd=self.workspace_dir,
                env=env_vars,
                bufsize=1, # Line buffered
            )
            
            self.active_processes[node_filename] = {
                'process': process,
                'start_time': time.time(),
                'status': 'RUNNING'
            }
            
            # Start a background thread to harvest its logs and pipe to terminal UI
            threading.Thread(target=self._stream_output, args=(process, node_filename), daemon=True).start()
            
        except Exception as e:
            print(f"❌ [ORCHESTRATOR] Failed to launch {node_filename}: {e}")

    def balancing_loop(self):
        """Runs the quantum logic limiting the CPU so the nodes don't crash the rig."""
        while self.is_running:
            # Rebalance
            balancer_status = self.quantum_balancer.balance_step()
            throttle = balancer_status['throttle_factor']
            
            # Dynamic scaling
            if self.global_state.get("FOUND_KEY"):
                print("\n" + "="*80)
                print(f"🎉🚨 GLOBAL HALT: WALLET CRACKED BY {self.global_state.get('CRACKED_BY')}!")
                print(f"🔑 PRIVATE KEY: {self.global_state.get('KEY')}")
                print("="*80)
                self.shutdown()
                break
                
            # Print overarching matrix updates every 15 seconds
            if int(time.time()) % 15 == 0:
                active_count = sum(1 for v in self.active_processes.values() if v['process'].poll() is None)
                print(f"\n============================================================")
                print(f"⚛️ ORCHESTRATOR VORTEX STATE: {active_count} Nodes Active")
                print(f"🌡️ Hardware Temp: {balancer_status['temperature']:.1f}°C | CPU: {balancer_status['cpu_percent']}%")
                print(f"⚖️ Throttle Matrix: {throttle:.2f} (Safe: {balancer_status['is_safe']})")
                print(f"📊 Hive Hive Offset: {hex(self.current_hive_offset)}")
                print(f"🌀 Vortex Resonance: {self.global_state.get('RESONANCE_SCORE', 0.0):.6f}%")
                print(f"============================================================\n")
                
            time.sleep(2)

    def orchestrate(self):
        """Main lifecycle block binding all systems."""
        print("="*80)
        print("🌌 UNIFIED VORTEX ORCHESTRATOR INITIALIZING 🌌")
        print("="*80)
        
        nodes = self._discover_nodes()
        print(f"🔌 Discovered {len(nodes)} valid quantum executable nodes.")
        for n in nodes:
            print(f"   - {n}")
            
        # Start Global Resource Balancer Thread
        balancer_thread = threading.Thread(target=self.balancing_loop, daemon=True)
        balancer_thread.start()
        
        print("\n🚀 Initiating Sub-process Execution Sequence...")
        
        # We start nodes gradually, up to the logical constraints, 
        # allowing continuous looping if they crash or exit
        while self.is_running:
            active_count = sum(1 for v in self.active_processes.values() if v['process'].poll() is None)
            
            if active_count < self.max_concurrent_nodes:
                # Find a node that isn't running
                for node in nodes:
                    state = self.active_processes.get(node)
                    if not state or state['process'].poll() is not None:
                        self.run_node(node)
                        time.sleep(5) # Stagger launches to stabilize memory allocation
                        break
            
            time.sleep(1)

    def shutdown(self):
        """Terminates all child pipes safely."""
        print("\n🛑 SHUTTING DOWN ORCHESTRATOR 🛑")
        self.is_running = False
        for name, data in self.active_processes.items():
            try:
                proc = data['process']
                if proc.poll() is None:
                    proc.terminate()
                    print(f"   Terminated [{name}]")
            except Exception:
                pass

if __name__ == "__main__":
    orchestrator = UnifiedVortexOrchestrator(workspace_dir=os.path.dirname(os.path.abspath(__file__)))
    try:
        orchestrator.orchestrate()
    except KeyboardInterrupt:
        orchestrator.shutdown()
        sys.exit(0)
