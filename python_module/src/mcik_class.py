import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.colors as mcolors
import copy # Needed for estimating kernels

class McikLatticeSimulator:
    """
    A class to simulate dynamics on 1D or 2D lattices and analyze influence
    using the Micro-Cause Influence Kernels (MCIK) framework [cite: MicroCause_Kernels_Paper_Package.md].

    Handles simulation runs, micro-cause perturbations, temporal integration,
    first (K) and second (H) order kernel estimation via finite differences,
    and various visualizations including animations.
    """
    def __init__(self, dimensions, time_steps, update_rule_func, **update_params):
        """
        Initializes the simulator.

        Args:
            dimensions (tuple): Shape of the lattice. (size,) for 1D, (rows, cols) for 2D.
            time_steps (int): Number of simulation steps to run.
            update_rule_func (callable): A function defining the lattice dynamics.
                Signature: update_rule_func(current_state, **update_params) -> next_state
                'current_state' and 'next_state' are numpy arrays of shape 'dimensions'.
            **update_params: Keyword arguments passed directly to the update_rule_func
                             (e.g., alpha=1.0, beta=0.5).
        """
        if not isinstance(dimensions, tuple) or not (1 <= len(dimensions) <= 2):
            raise ValueError("dimensions must be a tuple of length 1 (1D) or 2 (2D)")
        if not callable(update_rule_func):
            raise TypeError("update_rule_func must be a callable function")

        self.dimensions = dimensions
        self.is_1d = len(dimensions) == 1
        self.time_steps = time_steps
        self.update_rule_func = update_rule_func
        self.update_params = update_params

        # Initialize data storage
        self.data_cube = None # Shape: (*dimensions, time_steps)
        self.initial_state = None # User-provided base state (before pokes)
        self.initial_state_with_pokes = None # Actual state at t=0 after pokes
        self.pokes = {} # Store pokes applied at t=0

        print(f"\n--- Initializing McikLatticeSimulator ---")
        print(f"  Dimensions: {self.dimensions} ({'1D' if self.is_1d else '2D'})")
        print(f"  Time Steps: {self.time_steps}")
        print(f"  Update Rule: {update_rule_func.__name__}")
        print(f"  Update Params: {self.update_params}")

    def set_initial_state(self, initial_state=None, pokes=None):
        """
        Sets the initial state of the lattice at t=0.

        Args:
            initial_state (np.ndarray, optional): A numpy array matching self.dimensions.
                                                 If None, defaults to zeros.
            pokes (dict, optional): Dictionary defining micro-causes at t=0.
                                    Keys are position tuples (e.g., (index,) for 1D, (row, col) for 2D).
                                    Values are the poke magnitudes.
        """
        print("\n--- Calling set_initial_state ---")
        if initial_state is None:
            self.initial_state = np.zeros(self.dimensions)
            print("  - initial_state not provided, defaulting to zeros.")
        else:
            if initial_state.shape != self.dimensions:
                raise ValueError(f"initial_state shape {initial_state.shape} must match dimensions {self.dimensions}")
            self.initial_state = initial_state.copy()
            print(f"  - initial_state provided (shape: {self.initial_state.shape}).")

        self.pokes = pokes if pokes else {}
        print(f"  - Pokes to apply: {self.pokes}")

        # Apply pokes to the initial state
        # [cite: MicroCause_Kernels_Paper_Package.md]
        temp_state = self.initial_state.copy()
        for pos, value in self.pokes.items():
            if not isinstance(pos, tuple):
                 pos = (pos,) # Ensure pos is a tuple for indexing
            if len(pos) != len(self.dimensions):
                 raise ValueError(f"Poke position {pos} dimensionality doesn't match lattice dimensions {self.dimensions}")
            try:
                temp_state[pos] += value
                print(f"    - Applied poke {value} at {pos}")
            except IndexError:
                raise IndexError(f"Poke position {pos} is out of bounds for lattice dimensions {self.dimensions}")

        # Store the potentially poked state as the actual t=0 state
        self.initial_state_with_pokes = temp_state
        print(f"  - Final state at t=0 (with pokes): shape {self.initial_state_with_pokes.shape}, min={self.initial_state_with_pokes.min():.2f}, max={self.initial_state_with_pokes.max():.2f}")

        self.data_cube = None # Reset data cube if initial state changes


    def run_simulation(self):
        """
        Runs the temporal propagation simulation.
        Requires set_initial_state to be called first.
        """
        print("\n--- Calling run_simulation ---")
        if self.initial_state_with_pokes is None:
            raise RuntimeError("Initial state not set. Call set_initial_state() before running.")

        # Allocate data cube
        cube_shape = self.dimensions + (self.time_steps,)
        self.data_cube = np.zeros(cube_shape)
        print(f"  - Allocated data_cube with shape: {self.data_cube.shape}")

        # Set t=0 state
        self.data_cube[..., 0] = self.initial_state_with_pokes
        g_current = self.initial_state_with_pokes.copy()

        print("  - Running temporal propagation...")
        # Run temporal propagation [cite: MicroCause_Kernels_Paper_Package.md]
        for t in range(self.time_steps - 1):
            g_next = self.update_rule_func(g_current, **self.update_params)
            self.data_cube[..., t + 1] = g_next
            g_current = g_next
            # Print progress less frequently for faster runs
            # if (t+1) % max(1, (self.time_steps // 5)) == 0:
            #      print(f"    ...step {t+1}/{self.time_steps-1}")

        print("  - Simulation complete.")
        print(f"  - Final data_cube stats: min={self.data_cube.min():.3f}, max={self.data_cube.max():.3f}, mean={self.data_cube.mean():.3f}")
        return self.data_cube

    def get_data_cube(self):
        """Returns the full simulation history (data cube)."""
        print("\n--- Calling get_data_cube ---")
        if self.data_cube is None:
            print("  - Warning: Simulation has not been run yet. Returning None.")
            return None
        else:
            print(f"  - Returning data_cube with shape: {self.data_cube.shape}")
            return self.data_cube

    def calculate_temporal_integral(self):
        """
        Calculates the temporal integral (sum over time) for each lattice point.
        [cite: MicroCause_Kernels_Paper_Package.md]

        Returns:
            np.ndarray: Array matching self.dimensions, containing the sum over time.
        """
        print("\n--- Calling calculate_temporal_integral ---")
        if self.data_cube is None:
            raise RuntimeError("Simulation data not available. Run run_simulation() first.")
        # Sum along the last axis (time)
        integral = np.sum(self.data_cube, axis=-1)
        print(f"  - Calculated temporal integral. Shape: {integral.shape}, min={integral.min():.3f}, max={integral.max():.3f}")
        return integral

    # --- Kernel Estimation Methods ---

    def _run_for_kernel(self, pokes):
        """Helper function to run simulation for kernel estimation."""
        # Intentionally verbose for example output
        print(f"\n  -- Running helper _run_for_kernel with pokes: {pokes} --")
        # Ensure we always start from the *original* base initial state for fair comparison
        if self.initial_state is None:
             # If user never provided one, it's zeros
             base_initial_state_for_kernel = np.zeros(self.dimensions)
             print("     - Using default zero initial state for kernel run.")
        else:
             base_initial_state_for_kernel = self.initial_state.copy()
             print("     - Using provided initial state for kernel run.")

        # Apply *only* the pokes for this specific run
        temp_state = base_initial_state_for_kernel.copy()
        current_pokes = pokes if pokes else {}
        for pos, value in current_pokes.items():
             if not isinstance(pos, tuple): pos = (pos,)
             try:
                  temp_state[pos] += value
             except IndexError:
                  raise IndexError(f"Kernel poke position {pos} out of bounds for {self.dimensions}")

        # Set this specific initial state for the simulation
        self.initial_state_with_pokes = temp_state
        print(f"     - Set initial state for this run (pokes: {current_pokes}).")

        # Run the simulation
        self.run_simulation() # Will print its own messages

        # Calculate the result (temporal integral)
        result = self.calculate_temporal_integral() # Will print its own messages
        print(f"  -- Helper _run_for_kernel finished --")

        # Important: Reset internal state for next kernel run or subsequent user calls
        self.initial_state_with_pokes = None # Ensure next set_initial_state is clean
        self.data_cube = None
        return result


    def estimate_k_kernel(self, poke_pos, poke_value=1.0):
        """
        Estimates the first-order K kernel using finite differences.
        Runs two simulations (baseline, poke A).
        [cite: MicroCause_Kernels_Paper_Package.md]

        Args:
            poke_pos (tuple): Position of the micro-cause 'a'. (index,) or (row, col).
            poke_value (float): Magnitude of the poke (epsilon). Defaults to 1.0.

        Returns:
            np.ndarray: The estimated K kernel (K_a = Y_a - Y_base) as a temporal integral.
                        Shape matches self.dimensions.
        """
        print("\n--- Calling estimate_k_kernel ---")
        # Ensure position is a tuple
        if not isinstance(poke_pos, tuple):
            poke_pos = (poke_pos,)
        print(f"  - Estimating K for poke at {poke_pos} with value {poke_value}")

        # Run Baseline (Y_base)
        print("  - Running Baseline simulation (no pokes)")
        Y_base = self._run_for_kernel(pokes={})
        print(f"    - Baseline result (integral) stats: min={Y_base.min():.3f}, max={Y_base.max():.3f}")

        # Run Poke A (Y_a)
        print(f"  - Running Poke A simulation at {poke_pos}")
        pokes_a = {poke_pos: poke_value}
        Y_a = self._run_for_kernel(pokes=pokes_a)
        print(f"    - Poke A result (integral) stats: min={Y_a.min():.3f}, max={Y_a.max():.3f}")

        # Calculate K_a [cite: MicroCause_Kernels_Paper_Package.md]
        K_a = Y_a - Y_base
        print(f"  - K Kernel (K_a = Y_a - Y_base) calculated.")
        print(f"    - K_a stats: min={K_a.min():.3f}, max={K_a.max():.3f}")
        print("--- K Kernel estimation complete ---")
        return K_a


    def estimate_h_kernel(self, poke_a_pos, poke_b_pos, poke_value=1.0):
        """
        Estimates the second-order H kernel (synergy) using finite differences.
        Runs four simulations (baseline, poke A, poke B, poke A+B).
        [cite: MicroCause_Kernels_Paper_Package.md]

        Args:
            poke_a_pos (tuple): Position of the first micro-cause 'a'.
            poke_b_pos (tuple): Position of the second micro-cause 'b'.
            poke_value (float): Magnitude of pokes (epsilon). Defaults to 1.0.

        Returns:
            tuple: (K_a, K_b, H_ab)
                K_a (np.ndarray): First-order kernel from poke A.
                K_b (np.ndarray): First-order kernel from poke B.
                H_ab (np.ndarray): Second-order synergy kernel H(i; a, b).
                All arrays match self.dimensions and are temporal integrals.
        """
        print("\n--- Calling estimate_h_kernel ---")
         # Ensure positions are tuples
        if not isinstance(poke_a_pos, tuple): poke_a_pos = (poke_a_pos,)
        if not isinstance(poke_b_pos, tuple): poke_b_pos = (poke_b_pos,)
        print(f"  - Estimating H for pokes at A={poke_a_pos}, B={poke_b_pos} with value {poke_value}")

        if poke_a_pos == poke_b_pos:
            print("  - Warning: poke_a_pos and poke_b_pos are the same. H kernel measures interaction between *distinct* pokes.")

        # Run Baseline (Y_base)
        print("  - Running Baseline simulation")
        Y_base = self._run_for_kernel(pokes={})
        print(f"    - Baseline result (integral) stats: min={Y_base.min():.3f}, max={Y_base.max():.3f}")

        # Run Poke A (Y_a)
        print(f"  - Running Poke A simulation")
        pokes_a = {poke_a_pos: poke_value}
        Y_a = self._run_for_kernel(pokes=pokes_a)
        print(f"    - Poke A result (integral) stats: min={Y_a.min():.3f}, max={Y_a.max():.3f}")

        # Run Poke B (Y_b)
        print(f"  - Running Poke B simulation")
        pokes_b = {poke_b_pos: poke_value}
        Y_b = self._run_for_kernel(pokes=pokes_b)
        print(f"    - Poke B result (integral) stats: min={Y_b.min():.3f}, max={Y_b.max():.3f}")

        # Run Poke A + B (Y_ab)
        print(f"  - Running Poke A+B simulation")
        pokes_ab = {poke_a_pos: poke_value, poke_b_pos: poke_value}
        Y_ab = self._run_for_kernel(pokes=pokes_ab)
        print(f"    - Poke A+B result (integral) stats: min={Y_ab.min():.3f}, max={Y_ab.max():.3f}")

        # Calculate Kernels [cite: MicroCause_Kernels_Paper_Package.md]
        K_a = Y_a - Y_base
        K_b = Y_b - Y_base
        Y_actual = Y_ab - Y_base
        Y_linear_sum = K_a + K_b
        H_ab = Y_actual - Y_linear_sum # Synergy term

        print(f"  - Kernels calculated:")
        print(f"    - K_a stats: min={K_a.min():.3f}, max={K_a.max():.3f}")
        print(f"    - K_b stats: min={K_b.min():.3f}, max={K_b.max():.3f}")
        print(f"    - H_ab (Synergy) stats: min={H_ab.min():.3f}, max={H_ab.max():.3f}")
        print("--- H Kernel estimation complete ---")
        return K_a, K_b, H_ab


    # --- Basic Plotting Methods ---
    # These remain largely unchanged, but add print statements

    def plot_spacetime_heatmap(self, ax=None, show=True, filename=None):
        """Plots the 2D space-time heatmap (only for 1D lattices)."""
        print("\n--- Calling plot_spacetime_heatmap ---")
        if not self.is_1d:
            print("  - Error: Spacetime heatmap is only available for 1D lattices.")
            return
        if self.data_cube is None:
            raise RuntimeError("Simulation data not available. Run run_simulation() first.")

        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 6))
        else:
            fig = ax.figure

        im = ax.imshow(
            self.data_cube[..., 0, :], # Access 1D data correctly (index, 0, time) -> (index, time)
            aspect='auto',
            cmap='viridis',
            origin='lower',
            extent=[0, self.time_steps, 0, self.dimensions[0]]
        )
        ax.set_title("Space-Time Heatmap ($g_i^{(t)}$)")
        ax.set_xlabel("Time Step ($t$)")
        ax.set_ylabel("Lattice Position ($i$)")
        fig.colorbar(im, ax=ax, label="State Value")
        print("  - Heatmap configured.")
        if filename:
            print(f"  - Saving heatmap to {filename}")
            fig.savefig(filename)
        if show:
            print("  - Displaying heatmap plot.")
            plt.show()
        else:
             plt.close(fig) # Close if not showing
        return ax

    def plot_temporal_integral(self, temporal_integral_data=None, ax=None, show=True, label="Temporal Integral", filename=None):
        """Plots the 1D or 2D temporal integral."""
        print("\n--- Calling plot_temporal_integral ---")
        if temporal_integral_data is None:
             if self.data_cube is None:
                  raise RuntimeError("Simulation data not available. Run run_simulation() first.")
             print("  - Calculating integral data...")
             temporal_integral_data = self.calculate_temporal_integral()
        else:
            print("  - Using provided integral data.")


        if ax is None:
             fig, ax = plt.subplots(figsize=(10, 6))
             print("  - Created new figure for plot.")
        else:
             fig = ax.figure
             print("  - Using provided axes for plot.")


        if self.is_1d:
             ax.plot(temporal_integral_data, label=label)
             ax.set_title("Temporal Integral (Total Accumulated Influence)")
             ax.set_xlabel("Lattice Position ($i$)")
             ax.set_ylabel("Total Influence ($\sum g_i^{(t)}$)")
             ax.set_xlim(0, self.dimensions[0])
             ax.legend()
             print("  - Configured 1D integral plot.")
        else: # 2D Plot
             im = ax.imshow(
                 temporal_integral_data.T, # Transpose for better axis alignment
                 aspect='auto',
                 cmap='viridis',
                 origin='lower',
                 extent=[-0.5, self.dimensions[0]-0.5, -0.5, self.dimensions[1]-0.5]
             )
             ax.set_title(f"{label} (Total Accumulated Influence over Time)")
             ax.set_xlabel("Dimension 1 (e.g., Zip Code)")
             ax.set_ylabel("Dimension 2 (e.g., Home Type)")
             fig.colorbar(im, ax=ax, label="Total Influence")
             print("  - Configured 2D integral plot (heatmap).")

        if filename:
             print(f"  - Saving integral plot to {filename}")
             fig.savefig(filename)
        if show:
            print("  - Displaying integral plot.")
            plt.show()
        else:
            plt.close(fig) # Close if not showing
        return ax

    def plot_kernels(self, K_a, K_b, H_ab, poke_a_pos, poke_b_pos, show=True, filename=None):
         """
         Plots the estimated 1st and 2nd order kernels (temporal integrals).
         Currently only supports 1D lattices for clear visualization.
         """
         print("\n--- Calling plot_kernels ---")
         if not self.is_1d:
              print("  - Warning: Kernel plotting currently only implemented for 1D lattices.")
              # Could add 2D imshow here later
              return

         if not isinstance(poke_a_pos, tuple): poke_a_pos = (poke_a_pos,)
         if not isinstance(poke_b_pos, tuple): poke_b_pos = (poke_b_pos,)

         fig, (ax1, ax2) = plt.subplots(
             2, 1,
             figsize=(12, 8),
             sharex=True
         )
         print("  - Created figure for kernel plots.")

         # Plot 1: The First-Order Kernels (Linear Ripples)
         ax1.plot(K_a, label=f'K(i, a) - 1st Order from Poke A (i={poke_a_pos[0]})', linestyle=':')
         ax1.plot(K_b, label=f'K(i, b) - 1st Order from Poke B (i={poke_b_pos[0]})', linestyle=':')
         ax1.plot(K_a + K_b, label='Linear Sum (K_a + K_b)', color='grey', alpha=0.7)
         ax1.set_title("First-Order Influence (Temporal Integral)")
         ax1.set_ylabel("Total Accumulated Influence")
         ax1.legend()
         print("  - Configured 1st order kernel plot.")

         # Plot 2: The Second-Order Kernel (Synergy)
         ax2.plot(H_ab, label=f'H(i; a, b) - Synergy Term', color='red')
         ax2.axhline(0, color='black', linestyle='--', linewidth=0.5)
         ax2.set_title("Second-Order Hessian Kernel (Synergy - Temporal Integral)")
         ax2.set_xlabel("Lattice Position ($i$)")
         ax2.set_ylabel("Synergistic Influence")
         ax2.legend()
         print("  - Configured 2nd order kernel plot.")

         plt.tight_layout()
         if filename:
              print(f"  - Saving kernel plot to {filename}")
              fig.savefig(filename)
         if show:
             print("  - Displaying kernel plot.")
             plt.show()
         else:
             plt.close(fig)
         return fig, (ax1, ax2)


    # --- Animation Methods ---
    # Keep these less verbose as they print per frame

    def animate_1d_lattice(self, filename='lattice_1d_animation.gif', interval=100, y_min=None, y_max=None):
        """Animates the evolution of a 1D lattice."""
        print("\n--- Calling animate_1d_lattice ---")
        if not self.is_1d:
            print("  - Error: 1D animation is only available for 1D lattices.")
            return
        if self.data_cube is None:
            raise RuntimeError("Simulation data not available. Run run_simulation() first.")

        fig, ax = plt.subplots(figsize=(10, 6))

        # Determine y-limits
        _min, _max = np.min(self.data_cube), np.max(self.data_cube)
        if y_min is None: y_min = _min - abs(_min)*0.1 if _min !=0 else -0.1
        if y_max is None: y_max = _max + abs(_max)*0.1 if _max !=0 else 0.1
        ax.set_ylim(y_min, y_max)
        ax.set_xlim(0, self.dimensions[0] - 1)
        ax.set_xlabel("Lattice Position ($i$)")
        ax.set_ylabel("State Value ($g_i$)")
        ax.set_title("1D Lattice Evolution")

        line, = ax.plot([], [], lw=2, marker='o', markersize=4)
        time_text = ax.text(0.02, 0.95, '', transform=ax.transAxes, fontsize=12,
                            bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))

        def init():
            line.set_data([], [])
            time_text.set_text('')
            return line, time_text

        def update(frame):
            # Access data correctly for 1D case (index, time) from (size, time_steps) shape
            y_data = self.data_cube[..., frame] 
            x_data = np.arange(self.dimensions[0])
            line.set_data(x_data, y_data)
            time_text.set_text(f'Time Step: {frame}')
            # Reduce print frequency inside animation loop
            # if frame % (self.time_steps // 10) == 0:
            #     print(f"    Rendering 1D frame {frame+1}/{self.time_steps}")
            return line, time_text

        ani = animation.FuncAnimation(fig, update, frames=self.time_steps,
                                    init_func=init, blit=True, interval=interval)
        print(f"  - Saving 1D animation to {filename} (may take a while)...")
        ani.save(filename, writer='pillow', fps=15)
        print("  - Save complete.")
        plt.close(fig) # Close plot window automatically after saving
        return ani


    def animate_2d_heatmap(self, filename='lattice_2d_heatmap_animation.gif', interval=100, vmin=None, vmax=None, cmap='viridis', type_labels=None):
        """Animates the evolution of a 2D lattice as a heatmap."""
        print("\n--- Calling animate_2d_heatmap ---")
        if self.is_1d:
            print("  - Error: 2D heatmap animation is only for 2D lattices.")
            return
        if self.data_cube is None:
            raise RuntimeError("Simulation data not available. Run run_simulation() first.")

        fig, ax = plt.subplots(figsize=(10, 7))

        # Determine color limits
        if vmin is None: vmin = self.data_cube.min()
        if vmax is None: vmax = self.data_cube.max()

        # Get initial data and create image object
        initial_data = self.data_cube[:, :, 0]
        im = ax.imshow(initial_data.T, aspect='auto', cmap=cmap, origin='lower',
                       vmin=vmin, vmax=vmax,
                       extent=[-0.5, self.dimensions[0]-0.5, -0.5, self.dimensions[1]-0.5])

        cbar = fig.colorbar(im, ax=ax)
        cbar.set_label('State Value')

        ax.set_xlabel("Dimension 1 (e.g., Zip Code)")
        ax.set_ylabel("Dimension 2 (e.g., Home Type)")
        if type_labels and len(type_labels) == self.dimensions[1]:
             ax.set_yticks(ticks=np.arange(self.dimensions[1]), labels=type_labels)

        ax.set_title("2D Lattice Evolution (Heatmap)")

        time_text = ax.text(0.85, 0.95, '', transform=ax.transAxes, fontsize=12,
                            bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))

        def init():
            im.set_data(self.data_cube[:, :, 0].T)
            time_text.set_text('')
            return [im, time_text]

        def update(frame):
            current_data = self.data_cube[:, :, frame]
            im.set_data(current_data.T)
            time_text.set_text(f'Time: {frame}')
            # Reduce print frequency
            # if frame % (self.time_steps // 10) == 0:
            #     print(f"    Rendering heatmap frame {frame+1}/{self.time_steps}")
            return [im, time_text]

        ani = animation.FuncAnimation(fig, update, frames=self.time_steps,
                                    init_func=init, blit=True, interval=interval)
        print(f"  - Saving 2D heatmap animation to {filename} (may take a while)...")
        ani.save(filename, writer='pillow', fps=15)
        print("  - Save complete.")
        plt.close(fig)
        return ani


    def animate_3d_bars(self, filename='lattice_3d_bars_animation.gif', interval=150, type_labels=None):
        """Animates the evolution of a 2D lattice as 3D bars (towers)."""
        print("\n--- Calling animate_3d_bars ---")
        if self.is_1d:
            print("  - Error: 3D bars animation is only for 2D lattices.")
            return
        if self.data_cube is None:
             raise RuntimeError("Simulation data not available. Run run_simulation() first.")

        fig = plt.figure(figsize=(14, 10))
        ax = fig.add_subplot(111, projection='3d')

        # X, Y coordinates for bars (Dim1=cols(x), Dim0=rows(y))
        x_pos, y_pos = np.meshgrid(np.arange(self.dimensions[1]), np.arange(self.dimensions[0]))
        x_pos = x_pos.flatten()
        y_pos = y_pos.flatten()
        z_pos = np.zeros_like(x_pos)
        dx = dy = 0.8 # Bar width/depth

        # Setup colormap
        vmin = self.data_cube.min()
        vmax = self.data_cube.max()
        # Adjust slightly to avoid pure white/black at extremes if needed
        vmin -= abs(vmin)*0.01
        vmax += abs(vmax)*0.01
        norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
        cmap = plt.get_cmap('viridis')

        time_text = ax.text2D(0.05, 0.95, '', transform=ax.transAxes, fontsize=14,
                             bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))

        bars = None # Placeholder for bar container

        def update(frame):
            nonlocal bars
            ax.clear()

            data_slice = self.data_cube[:, :, frame].flatten()
            colors = cmap(norm(data_slice))
            
            # Catch potential NaN or Inf values that break bar3d
            if not np.all(np.isfinite(data_slice)):
                 print(f"Warning: Non-finite values detected in data at frame {frame}. Clamping.")
                 data_slice = np.nan_to_num(data_slice, nan=vmin, posinf=vmax, neginf=vmin)


            bars = ax.bar3d(x_pos, y_pos, z_pos, dx, dy, data_slice, color=colors)

            # --- Re-set labels and titles ---
            ax.set_title(f"3D Lattice Evolution (Towers)", fontsize=16)
            ax.set_xlabel("Dimension 2 (e.g., Home Type)")
            ax.set_ylabel("Dimension 1 (e.g., Zip Code)")
            ax.set_zlabel("State Value")

            if type_labels and len(type_labels) == self.dimensions[1]:
                 ax.set_xticks(np.arange(self.dimensions[1]))
                 ax.set_xticklabels(type_labels, rotation=-15, ha='left', fontsize=8)

            # Format Z-axis
            ax.get_zaxis().set_major_formatter(
                plt.FuncFormatter(lambda z, p: f'{z:.2f}') # Simple formatter
            )

            ax.view_init(elev=40, azim=-60)
            ax.set_zlim(vmin, vmax) # Use calculated vmin/vmax

            time_text.set_text(f'Time: {frame}')
            # Reduce print frequency
            # if frame % (self.time_steps // 10) == 0:
            #     print(f"    Rendering 3D frame {frame+1}/{self.time_steps}")
            return fig,

        ani = animation.FuncAnimation(
             fig, update, frames=self.time_steps,
             interval=interval, blit=False
        )

        print(f"  - Saving 3D bars animation to {filename} (will take several minutes)...")
        ani.save(filename, writer='pillow', fps=10) # Slower FPS for complex plots
        print("  - Save complete.")
        plt.close(fig)
        return ani


# --- Example Update Rules ---

def tanh_update_1d(g_t, alpha=1.0, beta=0.5):
    """
    Example 1D update rule from [cite: MicroCause_Kernels_Paper_Package.md].
    g_{t+1} = tanh( alpha*g_t + beta*(neighbors) )
    Uses circular boundary conditions.
    """
    g_i_minus_1 = np.roll(g_t, 1)
    g_i_plus_1 = np.roll(g_t, -1)
    h_t = alpha * g_t + beta * (g_i_minus_1 + g_i_plus_1)
    return np.tanh(h_t)

def tanh_update_2d(g_t, alpha=1.0, beta=0.5):
    """
    Example 2D update rule using tanh and average of 4 neighbors.
    g_{t+1} = tanh( alpha*g_t + beta*(neighbor_avg) )
    Uses circular boundary conditions.
    """
    g_up = np.roll(g_t, 1, axis=0)
    g_down = np.roll(g_t, -1, axis=0)
    g_left = np.roll(g_t, 1, axis=1)
    g_right = np.roll(g_t, -1, axis=1)

    # Simple average of 4 neighbors
    neighbor_avg = (g_up + g_down + g_left + g_right) / 4.0

    h_t = alpha * g_t + beta * neighbor_avg
    g_t_plus_1 = np.tanh(h_t)
    return g_t_plus_1

# --- Example Usage ---
if __name__ == "__main__":
    print("############################################################")
    print("### Running McikLatticeSimulator Full Method Examples ###")
    print("############################################################")

    # --- 1D Example ---
    print("\n\n===== STARTING 1D EXAMPLE =====")
    # 1. Initialize
    sim_1d = McikLatticeSimulator(
        dimensions=(20,),          # SMALLER lattice
        time_steps=30,             # FEWER steps
        update_rule_func=tanh_update_1d,
        alpha=1.0, beta=0.9        # Higher beta for more ripple
    )

    # 2. Set Initial State
    sim_1d.set_initial_state(pokes={(10,): 1.0}) # Poke at index 10

    # 3. Run Simulation
    data_cube_1d = sim_1d.run_simulation()

    # 4. Get Data Cube (Optional Check)
    retrieved_cube_1d = sim_1d.get_data_cube()
    # print(f"First few steps of 1D cube:\n{retrieved_cube_1d[:, :5]}") # Print slice

    # 5. Calculate Temporal Integral
    integral_1d = sim_1d.calculate_temporal_integral()
    # print(f"1D Temporal Integral:\n{integral_1d}")

    # 6. Estimate K Kernel
    poke_k_pos = (5,)
    K_a_1d = sim_1d.estimate_k_kernel(poke_pos=poke_k_pos, poke_value=0.5)
    # print(f"Estimated K Kernel for poke at {poke_k_pos}:\n{K_a_1d}")

    # 7. Estimate H Kernel
    poke_a_pos_h = (5,)
    poke_b_pos_h = (15,)
    K_a_h_1d, K_b_h_1d, H_ab_1d = sim_1d.estimate_h_kernel(
        poke_a_pos=poke_a_pos_h,
        poke_b_pos=poke_b_pos_h,
        poke_value=0.5
    )
    # print(f"Estimated H Kernel for pokes at {poke_a_pos_h}, {poke_b_pos_h}:\n{H_ab_1d}")

    # --- Plotting Examples (Run one by one if desired) ---
    print("\n--- 1D Plotting Examples ---")
    # Make sure simulation was run with a single poke first for heatmap
    sim_1d.set_initial_state(pokes={(10,): 1.0})
    sim_1d.run_simulation()
    # sim_1d.plot_spacetime_heatmap(show=True, filename="example_1d_heatmap.png") # Show or save
    sim_1d.plot_temporal_integral(show=True, filename="example_1d_integral.png")
    # Need K and H results from estimate_h_kernel to plot them
    sim_1d.plot_kernels(K_a_h_1d, K_b_h_1d, H_ab_1d, poke_a_pos_h, poke_b_pos_h, show=True, filename="example_1d_kernels.png")

    # --- Animation Example ---
    print("\n--- 1D Animation Example ---")
    # Re-run with the single poke for a clear animation
    sim_1d.set_initial_state(pokes={(10,): 1.0})
    sim_1d.run_simulation()
    sim_1d.animate_1d_lattice(filename='example_1d_animation.gif', interval=150)


    # --- 2D Example ---
    print("\n\n===== STARTING 2D EXAMPLE =====")
    # Use the tanh update rule for simplicity here
    sim_2d = McikLatticeSimulator(
        dimensions=(10, 5),          # SMALLER 2D lattice (10 rows, 5 cols)
        time_steps=40,               # FEWER steps
        update_rule_func=tanh_update_2d,
        alpha=1.0, beta=0.8          # Parameters for tanh_update_2d
    )

    # Set Initial State with two pokes
    pokes_2d = {(3, 1): 1.0, (7, 3): -0.8}
    sim_2d.set_initial_state(pokes=pokes_2d)

    # Run Simulation
    data_cube_2d = sim_2d.run_simulation()

    # Calculate & Plot Temporal Integral (as heatmap)
    integral_2d = sim_2d.calculate_temporal_integral()
    sim_2d.plot_temporal_integral(integral_2d, show=True, filename="example_2d_integral.png") # Plot the integral

    # Estimate K Kernel for 2D
    poke_k_pos_2d = (2, 2)
    K_a_2d = sim_2d.estimate_k_kernel(poke_pos=poke_k_pos_2d, poke_value=0.5)
    # Optional: Plot K_a_2d as a heatmap
    sim_2d.plot_temporal_integral(K_a_2d, label=f"K Kernel from {poke_k_pos_2d}", show=True, filename="example_2d_K_kernel.png")

    # Estimate H Kernel for 2D
    poke_a_pos_h_2d = (2, 1)
    poke_b_pos_h_2d = (8, 3)
    K_a_h_2d, K_b_h_2d, H_ab_2d = sim_2d.estimate_h_kernel(
        poke_a_pos=poke_a_pos_h_2d,
        poke_b_pos=poke_b_pos_h_2d,
        poke_value=0.5
    )
    # Optional: Plot H_ab_2d as a heatmap
    sim_2d.plot_temporal_integral(H_ab_2d, label=f"H Kernel from {poke_a_pos_h_2d} & {poke_b_pos_h_2d}", show=True, filename="example_2d_H_kernel.png")

    # --- Animation Examples ---
    print("\n--- 2D Animation Examples ---")
    # Re-run with the desired pokes for the animation
    sim_2d.set_initial_state(pokes=pokes_2d)
    sim_2d.run_simulation()
    
    # Example labels for the 2nd dimension
    example_type_labels = [f"Type {i}" for i in range(sim_2d.dimensions[1])]

    sim_2d.animate_2d_heatmap(filename='example_2d_heatmap_animation.gif', interval=150, type_labels=example_type_labels)
    # Comment out the 3D animation if it's too slow for testing
    sim_2d.animate_3d_bars(filename='example_2d_bars_animation.gif', interval=200, type_labels=example_type_labels)

    print("\n\n############################################################")
    print("### McikLatticeSimulator Full Method Examples COMPLETE ###")
    print("############################################################")

