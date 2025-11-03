import numpy as np
import matplotlib.pyplot as plt

# --- 1. Define Model Parameters (Same as before) ---
LATTICE_SIZE = 100
TIME_STEPS = 200
ALPHA = 1.0
BETA = 0.5  # Try 0.5 for simple ripples, 0.9 for more chaos

def run_simulation(pokes):
    """
    Runs the full 1D lattice simulation and returns the
    TEMPORAL INTEGRAL (the aggregated data for analysis).
    
    'pokes' is a dictionary: {position: poke_value}
    """
    
    # Initialize the lattice state
    g_current = np.zeros(LATTICE_SIZE)
    
    # Apply all micro-cause pokes at t=0
    for position, value in pokes.items():
        g_current[position] = value
        
    # Store the t=0 state
    temporal_accumulator = g_current.copy()
    
    # --- Run Temporal Propagation ---
    for t in range(TIME_STEPS - 1):
        # Calculate neighbor values
        g_i_minus_1 = np.roll(g_current, 1)
        g_i_plus_1 = np.roll(g_current, -1)
        
        # Calculate h_t
        h_t = ALPHA * g_current + BETA * (g_i_minus_1 + g_i_plus_1)
        
        # Calculate g_{t+1}
        g_next = np.tanh(h_t)
        
        # Add the new state to our temporal integral
        temporal_accumulator += g_next
        
        # Update the current state for the next iteration
        g_current = g_next
        
    return temporal_accumulator

# --- 2. Define our Two Micro-Causes (Inputs a and b) ---
POKE_A_POS = LATTICE_SIZE // 3  # Approx i=33
POKE_B_POS = (LATTICE_SIZE * 2) // 3 # Approx i=66
POKE_VALUE = 1.0

# --- 3. Run the Four Tests for Finite Differences ---
#

print("Running baseline simulation (no pokes)...")
Y_base = run_simulation(pokes={})

print("Running simulation for Poke A...")
Y_a = run_simulation(pokes={POKE_A_POS: POKE_VALUE})

print("Running simulation for Poke B...")
Y_b = run_simulation(pokes={POKE_B_POS: POKE_VALUE})

print("Running simulation for Poke A + B...")
Y_ab = run_simulation(pokes={
    POKE_A_POS: POKE_VALUE,
    POKE_B_POS: POKE_VALUE
})

# --- 4. Calculate First and Second-Order Kernels ---

# First-Order K (Linear Influence)
# This is the "ripple" from A alone and B alone
K_a = Y_a - Y_base
K_b = Y_b - Y_base

# Expected Linear Sum
Y_linear_sum = K_a + K_b

# Actual Measured Result
Y_actual = Y_ab - Y_base

# Second-Order H (The Synergy Term)
# H = (Actual Result) - (Expected Linear Sum)
H_ab = Y_actual - Y_linear_sum


# --- 5. Plot the Results ---
fig, (ax1, ax2) = plt.subplots(
    2, 1, 
    figsize=(12, 8), 
    sharex=True
)

# Plot 1: The First-Order Kernels (Linear Ripples)
ax1.plot(K_a, label=f'K(i, a) - 1st Order from Poke A (i={POKE_A_POS})', linestyle=':')
ax1.plot(K_b, label=f'K(i, b) - 1st Order from Poke B (i={POKE_B_POS})', linestyle=':')
ax1.plot(Y_linear_sum, label='Y_linear (K_a + K_b)', color='grey', alpha=0.7)
ax1.set_title("First-Order Influence (Linear Ripples)")
ax1.set_ylabel("Total Accumulated Influence")
ax1.legend()

# Plot 2: The Second-Order Kernel (Synergy)
ax2.plot(H_ab, label=f'H(i; a, b) - Synergy Term', color='red')
ax2.axhline(0, color='black', linestyle='--', linewidth=0.5)
ax2.set_title("Second-Order Hessian Kernel (The Synergy)")
ax2.set_xlabel("Lattice Position ($i$)")
ax2.set_ylabel("Synergistic Influence")
ax2.legend()

plt.tight_layout()
plt.show()