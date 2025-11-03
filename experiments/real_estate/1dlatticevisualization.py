import numpy as np
import matplotlib.pyplot as plt

# --- 1. Define Model Parameters from your paper ---
#
LATTICE_SIZE = 100  # Number of nodes (i) in our 1D lattice
TIME_STEPS = 200    # Number of time steps (t) to simulate
ALPHA = 1.0         # Self-influence parameter
BETA = 0.5          # Neighbor-influence parameter

def update_lattice(g_t, alpha, beta):
    """
    Applies the 1D lattice update rule from Section 3.
    g_t_plus_1 = f(h_t) where h_i = a*g_i + b*(g_{i-1} + g_{i+1})
    and f(u) = tanh(u).
    """
    
    # Calculate neighbor values using np.roll for circular boundary conditions
    g_i_minus_1 = np.roll(g_t, 1)  # g_{i-1}
    g_i_plus_1 = np.roll(g_t, -1) # g_{i+1}
    
    # Calculate the intermediate 'h' vector
    h_t = alpha * g_t + beta * (g_i_minus_1 + g_i_plus_1)
    
    # Apply the non-linear function f(u) = tanh(u)
    g_t_plus_1 = np.tanh(h_t)
    
    return g_t_plus_1

# --- 2. Initialize Simulation ---
# Create a 2D array to store the entire history of the lattice
# Rows = Lattice Position (i), Columns = Time Step (t)
spacetime_heatmap = np.zeros((LATTICE_SIZE, TIME_STEPS))

# Create the initial state (t=0)
g_current = np.zeros(LATTICE_SIZE)

# Introduce the "micro-cause": a single poke at the center
#
center_index = LATTICE_SIZE // 2
g_current[center_index] = 1.0

# Store the initial state in our heatmap
spacetime_heatmap[:, 0] = g_current

# --- 3. Run Temporal Propagation ---
#
for t in range(TIME_STEPS - 1):
    # Calculate the next state based on the current state
    g_next = update_lattice(g_current, ALPHA, BETA)
    
    # Store the new state in the heatmap
    spacetime_heatmap[:, t + 1] = g_next
    
    # Update the current state for the next iteration
    g_current = g_next

# --- 4. Calculate the "Temporal Integral" ---
# Sum all values along the time axis (axis=1) for each lattice point (i)
temporal_integral = np.sum(spacetime_heatmap, axis=1)

# --- 5. Plot the Results ---
fig, (ax1, ax2) = plt.subplots(
    2, 1, 
    figsize=(12, 10), 
    gridspec_kw={'height_ratios': [2, 1]}
)

# Plot 1: The Space-Time Heatmap
ax1.imshow(
    spacetime_heatmap, 
    aspect='auto', 
    cmap='viridis', 
    origin='lower',
    extent=[0, TIME_STEPS, 0, LATTICE_SIZE]
)
ax1.set_title("Space-Time Heatmap of Ripple Propagation ($g_i^{(t)}$)")
ax1.set_xlabel("Time Step ($t$)")
ax1.set_ylabel("Lattice Position ($i$)")

# Plot 2: The Temporal Integral Plot
ax2.plot(temporal_integral)
ax2.set_title("Temporal Integral (Total Accumulated Influence)")
ax2.set_xlabel("Lattice Position ($i$)")
ax2.set_ylabel("Total Influence ($\sum g_i^{(t)}$)")
ax2.set_xlim(0, LATTICE_SIZE)

plt.tight_layout()
plt.show()