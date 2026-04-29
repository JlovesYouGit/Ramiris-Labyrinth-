import time
import os
import sys
import math
import random
from vortex_cluster_api import VortexClusterAPI

class VortexHUD:
    def __init__(self):
        self.api = VortexClusterAPI()
        self.symbols = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.colors = {
            "gold": "\033[93m",
            "cyan": "\033[96m",
            "magenta": "\033[95m",
            "red": "\033[91m",
            "reset": "\033[0m",
            "bold": "\033[1m"
        }

    def clear(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def render_waveform(self, resonance):
        """Renders a pulsing wave representing pattern conjunction."""
        width = 60
        wave = ""
        for i in range(width):
            t = time.time() * 5 + (i * 0.2)
            y = int(10 + math.sin(t) * (resonance * 10 + 2))
            if i % 2 == 0:
                wave += self.colors["cyan"] + "█" + self.colors["reset"]
            else:
                wave += " "
        return wave

    def run(self):
        self.clear()
        print(f"{self.colors['bold']}🛰️ RAMIRIS LABYRINTH: QUANTUM COMPUTE HUD{self.colors['reset']}")
        print("="*65)
        
        try:
            while True:
                resonance = self.api.get_resonance()
                # Simulate thermal load for visualization
                load = random.uniform(85, 98)
                
                # Header Section
                sys.stdout.write("\033[H") # Home cursor
                print(f"\n{self.colors['bold']}🌀 VORTEX RESONANCE STRENGTH{self.colors['reset']}")
                print(f"[{'█' * int(resonance * 20)}{'░' * (20 - int(resonance * 20))}] {resonance:.8f}%")
                
                # Waveform Section
                print(f"\n{self.colors['magenta']}📡 KEYSPACE CONJUNCTION WAVEFORM{self.colors['reset']}")
                print(self.render_waveform(resonance))
                
                # Hardware Experience Layer
                print(f"\n{self.colors['cyan']}💻 HARDWARE EXPERIENCE (THERMAL/COMPUTE){self.colors['reset']}")
                thermal_bar = "🔥" * int(load / 10)
                print(f"Silicon Stress: {thermal_bar} {load:.1f}%")
                
                # Active Tiers
                print(f"\n{self.colors['gold']}🕸️ LABYRINTH TIER STATUS{self.colors['reset']}")
                print(f"  ● EntropyPeak:      {self.colors['cyan']}SYNCHRONIZED{self.colors['reset']}")
                print(f"  ● GeometricSpiral:  {self.colors['cyan']}MAPPING DELTAS{self.colors['reset']}")
                print(f"  ● TemporalResidue:  {self.colors['cyan']}CONJOINED{self.colors['reset']}")
                
                # Random "Conjunction Sparks"
                if random.random() > 0.8:
                    spark = random.choice(["✨", "🎇", "🌠", "💎"])
                    print(f"\n{spark} [7zip] DATA SWAP DETECTED: Conjoining pattern piece...")
                else:
                    print("\n" + " " * 60) # Clear spark line
                
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\n🛑 HUD Disconnected.")

if __name__ == "__main__":
    hud = VortexHUD()
    hud.run()
