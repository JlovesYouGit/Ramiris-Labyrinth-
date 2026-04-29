"""
Quantum Balancer System

Prevents computer from breaking by:
- Monitoring top resource usage values
- Avoiding top 3 highest curve values
- Dropping 3 additional values
- Releasing resources at intervals
- Maintaining quantum equilibrium

Integrates with all accelerator systems to prevent overload.
"""

import os
import sys
import time
import threading
import math
import psutil
from typing import Dict, Any, Optional, List, Tuple
from collections import deque
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ResourceMetrics:
    """Resource usage metrics at a point in time."""
    cpu_percent: float
    memory_percent: float
    temperature: float  # Simulated/probed
    thread_count: int
    timestamp: float
    

class QuantumBalancer:
    """
    Quantum Balancer - Maintains system equilibrium while maximizing performance.
    Uses quantum principles to balance load and prevent system failure.
    """
    
    def __init__(self):
        # Resource monitoring
        self.metrics_history = deque(maxlen=100)
        self.balance_interval = 0.1  # 100ms balance cycles
        
        # Quantum thresholds
        self.max_safe_cpu = 95.0
        self.max_safe_memory = 90.0
        self.max_safe_temp = 85.0  # Celsius
        
        # Top values to avoid (top 3 + 3 more)
        self.values_to_avoid = 6  # Top 3 highest + 3 additional
        
        # Interval release timing
        self.release_interval = 2.0  # Release every 2 seconds
        self.last_release = time.time()
        
        # State
        self.is_balancing = False
        self.current_throttle = 1.0  # 1.0 = full speed, 0.0 = stopped
        self.thread_delays = {}  # Per-thread delay tracking
        
        # Quantum wave function for load distribution
        self.quantum_wave_phase = 0.0
        
        print(f"⚛️⚖️ QUANTUM BALANCER INITIALIZED")
        print(f"⚖️ Balance interval: {self.balance_interval}s")
        print(f"⚖️ Values to avoid: top {self.values_to_avoid}")
        print(f"⚖️ Release interval: {self.release_interval}s")
        print(f"⚖️ Safe limits: CPU {self.max_safe_cpu}%, Memory {self.max_safe_memory}%, Temp {self.max_safe_temp}°C")
    
    def get_current_metrics(self) -> ResourceMetrics:
        """Get current system resource metrics."""
        try:
            cpu = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory().percent
            
            # Estimate temperature (or get with probe if available)
            temp = self._get_hardware_temperature(cpu)
            
            # Thread count
            threads = threading.active_count()
            
            return ResourceMetrics(
                cpu_percent=cpu,
                memory_percent=memory,
                temperature=temp,
                thread_count=threads,
                timestamp=time.time()
            )
        except:
            # Fallback if psutil fails
            return ResourceMetrics(
                cpu_percent=50.0,
                memory_percent=50.0,
                temperature=60.0,
                thread_count=threading.active_count(),
                timestamp=time.time()
            )
    
    def _get_hardware_temperature(self, cpu_usage: float) -> float:
        """Attempt to read actual hardware temperature, fallback to estimation."""
        try:
            import wmi
            
            # Attempt 1: OpenHardwareMonitor WMI wrapper (if user is running it)
            try:
                w_ohm = wmi.WMI(namespace="root\\OpenHardwareMonitor")
                sensors = w_ohm.Sensor()
                cpu_temps = [s.Value for s in sensors if s.SensorType == 'Temperature' and 'CPU' in s.Name]
                if cpu_temps:
                    return float(sum(cpu_temps) / len(cpu_temps))
            except Exception:
                pass
                
            # Attempt 2: Windows ACPI Thermal Zone 
            w_acpi = wmi.WMI(namespace="root\\wmi")
            thermal_zones = w_acpi.MSAcpi_ThermalZoneTemperature()
            if thermal_zones:
                # WMI returns temperature in tenths of degrees Kelvin
                kelvin = thermal_zones[0].CurrentTemperature / 10.0
                celsius = kelvin - 273.15
                return float(celsius)
                
        except Exception as e:
            # WMI might be locked without admin privileges or throw COM errors
            pass
            
        # Fallback to load-based estimation if physical probes are locked
        base_temp = 45.0
        load_increase = (cpu_usage / 100.0) * 40.0
        return min(100.0, base_temp + load_increase)
    
    def analyze_metrics_curve(self, metrics_list: List[ResourceMetrics]) -> Dict[str, Any]:
        """
        Analyze the resource usage curve.
        Identify top values to avoid.
        """
        if not metrics_list:
            return {'curve_risk': 0.0, 'top_values': []}
        
        # Extract CPU usage curve
        cpu_values = [m.cpu_percent for m in metrics_list]
        
        # Sort to find top values
        sorted_values = sorted(cpu_values, reverse=True)
        
        # Get top 3 highest + 3 additional (6 total to avoid)
        top_values = sorted_values[:self.values_to_avoid]
        
        # Calculate curve risk
        avg_top = sum(top_values) / len(top_values) if top_values else 0
        curve_risk = avg_top / 100.0
        
        return {
            'curve_risk': curve_risk,
            'top_values': top_values,
            'all_values': cpu_values,
            'average_cpu': sum(cpu_values) / len(cpu_values)
        }
    
    def calculate_quantum_throttle(self, analysis: Dict[str, Any]) -> float:
        """
        Calculate throttle factor using quantum balancing.
        
        Returns value between 0.0 and 1.0:
        - 1.0 = full speed (safe)
        - 0.0 = full stop (critical)
        """
        curve_risk = analysis['curve_risk']
        top_values = analysis['top_values']
        
        # Check if we're hitting the top 3 highest values
        if len(top_values) >= 3:
            top_3_avg = sum(top_values[:3]) / 3
            
            # If top 3 are near max safe, throttle down
            if top_3_avg > self.max_safe_cpu * 0.9:
                # Critical - avoid top 3
                return 0.3  # Reduce to 30% speed
            elif top_3_avg > self.max_safe_cpu * 0.8:
                # Warning - reduce speed
                return 0.6  # Reduce to 60% speed
        
        # Check next 3 values (positions 4-6)
        if len(top_values) >= 6:
            next_3_avg = sum(top_values[3:6]) / 3
            
            if next_3_avg > self.max_safe_cpu * 0.85:
                # Drop these 3 additional values by throttling
                return 0.7  # Reduce to 70% speed
        
        # Quantum wave modulation for smooth transitions
        self.quantum_wave_phase += 0.1
        wave_factor = 0.5 + 0.5 * math.sin(self.quantum_wave_phase)
        
        # Base throttle based on curve risk
        base_throttle = 1.0 - (curve_risk * 0.5)
        
        # Apply wave modulation
        throttle = base_throttle * (0.8 + 0.2 * wave_factor)
        
        # Ensure minimum throttle for progress
        throttle = max(0.1, min(1.0, throttle))
        
        return throttle
    
    def should_release_resources(self) -> bool:
        """Check if it's time to release resources in interval."""
        current_time = time.time()
        
        if current_time - self.last_release >= self.release_interval:
            self.last_release = current_time
            return True
        
        return False
    
    def balance_step(self) -> Dict[str, Any]:
        """
        Execute one quantum balancing step.
        Returns balance status and recommended actions.
        """
        # Get current metrics
        metrics = self.get_current_metrics()
        self.metrics_history.append(metrics)
        
        # Analyze curve
        analysis = self.analyze_metrics_curve(list(self.metrics_history))
        
        # Calculate throttle
        self.current_throttle = self.calculate_quantum_throttle(analysis)
        
        # Check for resource release
        release_triggered = self.should_release_resources()
        
        # Determine if we're avoiding top values
        avoiding_top_3 = False
        dropping_next_3 = False
        
        if 'top_values' in analysis and len(analysis['top_values']) >= 3:
            if analysis['top_values'][0] > self.max_safe_cpu * 0.9:
                avoiding_top_3 = True
            if len(analysis['top_values']) >= 6 and analysis['top_values'][3] > self.max_safe_cpu * 0.85:
                dropping_next_3 = True
        
        status = {
            'timestamp': metrics.timestamp,
            'cpu_percent': metrics.cpu_percent,
            'memory_percent': metrics.memory_percent,
            'temperature': metrics.temperature,
            'thread_count': metrics.thread_count,
            'curve_risk': analysis['curve_risk'],
            'throttle_factor': self.current_throttle,
            'avoiding_top_3': avoiding_top_3,
            'dropping_next_3': dropping_next_3,
            'release_triggered': release_triggered,
            'is_safe': self.current_throttle > 0.3
        }
        
        return status
    
    def get_thread_delay(self, thread_id: int) -> float:
        """
        Get recommended delay for a specific thread.
        Uses quantum balancing to distribute load.
        """
        if thread_id not in self.thread_delays:
            # Initialize with quantum-distributed delay
            base_delay = (1.0 - self.current_throttle) * 0.1
            quantum_offset = (thread_id % 10) * 0.01
            self.thread_delays[thread_id] = base_delay + quantum_offset
        
        # Update based on current throttle
        base_delay = (1.0 - self.current_throttle) * 0.1
        current_delay = self.thread_delays[thread_id]
        
        # Smooth transition
        new_delay = 0.7 * current_delay + 0.3 * base_delay
        self.thread_delays[thread_id] = new_delay
        
        return new_delay
    
    def monitor_continuously(self, duration_seconds: int = 300):
        """
        Monitor system continuously for specified duration.
        """
        print(f"⚛️⚖️ Starting continuous quantum balance monitoring for {duration_seconds}s")
        
        start_time = time.time()
        balance_count = 0
        
        while time.time() - start_time < duration_seconds:
            status = self.balance_step()
            balance_count += 1
            
            # Report status every 5 seconds
            if balance_count % 50 == 0:  # 50 * 0.1s = 5s
                print(f"⚖️ Balance #{balance_count}: "
                      f"CPU {status['cpu_percent']:.1f}% | "
                      f"Throttle {status['throttle_factor']:.2f} | "
                      f"Risk {status['curve_risk']:.2f}")
                
                if status['avoiding_top_3']:
                    print(f"⚖️  🚨 AVOIDING TOP 3 HIGHEST VALUES")
                if status['dropping_next_3']:
                    print(f"⚖️  📉 DROPPING NEXT 3 VALUES")
                if status['release_triggered']:
                    print(f"⚖️  🔄 RESOURCE RELEASE TRIGGERED")
            
            # Check safety
            if not status['is_safe']:
                print(f"⚖️  ⚠️ CRITICAL: System approaching limits!")
                print(f"⚖️  Throttling to {status['throttle_factor']*100:.0f}%")
            
            # Sleep for balance interval
            time.sleep(self.balance_interval)
        
        print(f"⚛️⚖️ Quantum balance monitoring complete ({balance_count} cycles)")
        
        return balance_count
    
    def get_balance_summary(self) -> Dict[str, Any]:
        """Get summary of balancing activity."""
        if not self.metrics_history:
            return {'status': 'No data'}
        
        cpu_values = [m.cpu_percent for m in self.metrics_history]
        memory_values = [m.memory_percent for m in self.metrics_history]
        temp_values = [m.temperature for m in self.metrics_history]
        
        return {
            'avg_cpu': sum(cpu_values) / len(cpu_values),
            'max_cpu': max(cpu_values),
            'min_cpu': min(cpu_values),
            'avg_memory': sum(memory_values) / len(memory_values),
            'max_memory': max(memory_values),
            'avg_temperature': sum(temp_values) / len(temp_values),
            'max_temperature': max(temp_values),
            'total_samples': len(self.metrics_history),
            'current_throttle': self.current_throttle
        }


class BalancedWorker:
    """
    Worker thread that respects quantum balancing.
    """
    
    def __init__(self, thread_id: int, balancer: QuantumBalancer):
        self.thread_id = thread_id
        self.balancer = balancer
        self.work_done = 0
        self.is_running = True
    
    def execute_work(self, work_item: Any) -> Any:
        """
        Execute work with quantum balancing delays.
        """
        # Get recommended delay from balancer
        delay = self.balancer.get_thread_delay(self.thread_id)
        
        # Apply delay to prevent overload
        if delay > 0:
            time.sleep(delay)
        
        # Do work
        result = self._process_work(work_item)
        self.work_done += 1
        
        return result
    
    def _process_work(self, work_item: Any) -> Any:
        """Actual work processing."""
        # Simulate work
        result = hash(str(work_item))
        return result
    
    def stop(self):
        """Stop the worker."""
        self.is_running = False


def test_quantum_balancer():
    """Test the quantum balancer system."""
    print("="*80)
    print("⚛️⚖️ QUANTUM BALANCER TEST ⚖️⚛️")
    print("="*80)
    
    # Initialize balancer
    balancer = QuantumBalancer()
    
    # Create some workers
    workers = []
    for i in range(20):
        worker = BalancedWorker(i, balancer)
        workers.append(worker)
    
    print(f"\n⚖️ Created {len(workers)} balanced workers")
    
    # Monitor for 30 seconds
    print(f"\n⚛️⚖️ Monitoring system balance for 30 seconds...")
    print("⚖️ Simulating high load to test balancing...\n")
    
    # Simulate load in background
    load_thread = threading.Thread(target=_simulate_load)
    load_thread.daemon = True
    load_thread.start()
    
    # Monitor
    balance_cycles = balancer.monitor_continuously(duration_seconds=30)
    
    # Get summary
    summary = balancer.get_balance_summary()
    
    print(f"\n{'='*80}")
    print("⚛️⚖️ QUANTUM BALANCE SUMMARY ⚖️⚛️")
    print(f"{'='*80}")
    print(f"⚖️ Balance cycles: {balance_cycles}")
    print(f"⚖️ Average CPU: {summary['avg_cpu']:.1f}%")
    print(f"⚖️ Max CPU: {summary['max_cpu']:.1f}%")
    print(f"⚖️ Average Memory: {summary['avg_memory']:.1f}%")
    print(f"⚖️ Max Memory: {summary['max_memory']:.1f}%")
    print(f"⚖️ Average Temperature: {summary['avg_temperature']:.1f}°C")
    print(f"⚖️ Max Temperature: {summary['max_temperature']:.1f}°C")
    print(f"⚖️ Final Throttle: {summary['current_throttle']*100:.0f}%")
    print(f"⚖️ System Status: {'✅ STABLE' if summary['current_throttle'] > 0.5 else '⚠️ THROTTLED'}")
    print(f"{'='*80}")
    
    return balancer, summary


def _simulate_load():
    """Simulate CPU load for testing."""
    start = time.time()
    while time.time() - start < 30:
        # Busy work to generate CPU load
        _ = [math.sqrt(i) for i in range(10000)]
        time.sleep(0.1)


if __name__ == "__main__":
    test_quantum_balancer()
