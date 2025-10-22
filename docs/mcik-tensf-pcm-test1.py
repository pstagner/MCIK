import os

# Environment setup to force CPU-only operation
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Suppress most TensorFlow logging

import tensorflow as tf
from typing import List

# Configure for CPU-only operation
tf.config.set_visible_devices([], 'GPU')  # Disable GPU devices
print("🔧 TensorFlow configured for CPU-only operation")

class PCMProperties:
    def __init__(self, name: str, melting_point: float, latent_heat: float, specific_heat: float,
                 thermal_conductivity: float, density: float):
        self.name = name
        self.melting_point = melting_point
        self.latent_heat = latent_heat
        self.specific_heat = specific_heat
        self.thermal_conductivity = thermal_conductivity
        self.density = density
class PCMLattice:
    def __init__(self, pcm: PCMProperties, num_nodes: int, initial_temp: float):
        self.pcm = pcm
        self.num_nodes = num_nodes
        # Track enthalpy instead of just temperature
        self.enthalpy = tf.Variable([pcm.specific_heat * initial_temp] * num_nodes, dtype=tf.float32)
        self.temperature = tf.Variable([initial_temp] * num_nodes, dtype=tf.float32)
        self.phase = tf.Variable([0.0] * num_nodes, dtype=tf.float32)  # 0: solid, 1: liquid

    def update_temperature_and_phase(self):
        # Convert enthalpy to temperature and phase
        mp = self.pcm.melting_point
        lh = self.pcm.latent_heat
        sh = self.pcm.specific_heat
        
        # Vectorized operations for better performance
        h = self.enthalpy.numpy()
        
        # Calculate temperature and phase for all nodes at once
        temp_values = []
        phase_values = []
        
        for i in range(self.num_nodes):
            if h[i] < sh * mp:
                # Solid
                temp_values.append(h[i] / sh)
                phase_values.append(0.0)
            elif h[i] < sh * mp + lh:
                # Phase change
                temp_values.append(mp)
                phase_values.append((h[i] - sh * mp) / lh)
            else:
                # Liquid
                temp_values.append((h[i] - lh) / sh)
                phase_values.append(1.0)
        
        # Update all at once
        self.temperature.assign(temp_values)
        self.phase.assign(phase_values)

    def apply_perturbation(self, node: int, delta_temp: float):
        # Add energy corresponding to delta_temp
        delta_h = self.pcm.specific_heat * delta_temp
        
        # Get current enthalpy values
        current_enthalpy = self.enthalpy.numpy()
        
        # Update the specific node
        current_enthalpy[node] += delta_h
        
        # Assign back to the variable
        self.enthalpy.assign(current_enthalpy)
        self.update_temperature_and_phase()

class MCIKKernel:
    def __init__(self, lattice: PCMLattice):
        self.lattice = lattice

    def heat_flow_step(self, enthalpy: tf.Tensor) -> tf.Tensor:
        # Heat flow using enthalpy (includes latent heat)
        alpha = self.lattice.pcm.thermal_conductivity
        beta = 0.5 * self.lattice.pcm.thermal_conductivity
        enthalpy_padded = tf.concat([[enthalpy[0]], enthalpy, [enthalpy[-1]]], axis=0)
        enthalpy_next = alpha * enthalpy + beta * (enthalpy_padded[:-2] + enthalpy_padded[2:])
        return enthalpy_next

    def compute_jacobian(self) -> tf.Tensor:
        with tf.GradientTape() as tape:
            tape.watch(self.lattice.enthalpy)
            enthalpy_next = self.heat_flow_step(self.lattice.enthalpy)
        jacobian = tape.jacobian(enthalpy_next, self.lattice.enthalpy)
        return jacobian

# ExperimentRunner remains similar, but uses enthalpy and phase logic

def main():
    """Test the PCM simulation with TensorFlow"""
    print("Testing PCM simulation with TensorFlow...")
    
    # Create a test PCM (e.g., paraffin wax)
    pcm = PCMProperties(
        name="Paraffin Wax",
        melting_point=50.0,  # °C
        latent_heat=200000.0,  # J/kg
        specific_heat=2000.0,  # J/(kg·K)
        thermal_conductivity=0.2,  # W/(m·K)
        density=900.0  # kg/m³
    )
    
    # Create lattice
    lattice = PCMLattice(pcm, num_nodes=10, initial_temp=25.0)
    
    print(f"Initial temperature: {lattice.temperature.numpy()}")
    print(f"Initial phase: {lattice.phase.numpy()}")
    
    # Test heat flow
    kernel = MCIKKernel(lattice)
    
    # Apply some heat
    lattice.apply_perturbation(5, 30.0)  # Heat center node by 30°C
    print(f"After heating center node:")
    print(f"Temperature: {lattice.temperature.numpy()}")
    print(f"Phase: {lattice.phase.numpy()}")
    
    # Test heat flow step
    print("\nTesting heat flow step...")
    new_enthalpy = kernel.heat_flow_step(lattice.enthalpy)
    print(f"New enthalpy: {new_enthalpy.numpy()}")
    
    # Test Jacobian computation
    print("\nTesting Jacobian computation...")
    jacobian = kernel.compute_jacobian()
    print(f"Jacobian shape: {jacobian.shape}")
    print(f"Jacobian (first few elements): {jacobian[0, :5].numpy()}")
    
    print("\n✅ TensorFlow PCM simulation test completed successfully!")

if __name__ == "__main__":
    main()