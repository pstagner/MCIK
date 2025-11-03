import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.animation as animation
import matplotlib.colors as mcolors

# --- 1. Define Model Parameters (Same as 2D Example) ---
NUM_ZIPS = 20
NUM_TYPES = 5
NUM_MONTHS = 120

TYPE_LABELS = ['1. Condo', '2. Small SFH', '3. Med SFH', '4. Large SFH', '5. Luxury']

base_type_prices = np.array([350000, 450000, 550000, 750000, 950000])

data_cube = np.zeros((NUM_ZIPS, NUM_TYPES, NUM_MONTHS))

# --- 2. Create the Baseline "Moving Dataset" (Same as 2D Example) ---
zip_gradient = np.linspace(1.2, 0.8, NUM_ZIPS)
market_growth_rate = 1.003

for t in range(NUM_MONTHS):
    for i in range(NUM_ZIPS):
        base_price = base_type_prices * zip_gradient[i] * (market_growth_rate**t)
        noise = np.random.randn(NUM_TYPES) * 2000
        data_cube[i, :, t] = base_price + noise

# --- 3. ADD THE 2D "MICRO-CAUSE" (Same as 2D Example) ---
SHOCK_MONTH = 20
SHOCK_ZIP = 5
SHOCK_TYPE_MED = 2
SHOCK_TYPE_LUXURY = 4
SHOCK_AMOUNT_MED = 150000
SHOCK_AMOUNT_LUXURY = 250000

data_cube[SHOCK_ZIP, SHOCK_TYPE_MED, SHOCK_MONTH:] += SHOCK_AMOUNT_MED
data_cube[SHOCK_ZIP, SHOCK_TYPE_LUXURY, SHOCK_MONTH:] += SHOCK_AMOUNT_LUXURY

# --- 4. ADD THE "RIPPLE" (Same as 2D Example) ---
SPATIAL_DELAY = 6
SPATIAL_RIPPLE_AMOUNT = 0.5
data_cube[SHOCK_ZIP-1, SHOCK_TYPE_MED, SHOCK_MONTH + SPATIAL_DELAY:] += SHOCK_AMOUNT_MED * SPATIAL_RIPPLE_AMOUNT
data_cube[SHOCK_ZIP+1, SHOCK_TYPE_MED, SHOCK_MONTH + SPATIAL_DELAY:] += SHOCK_AMOUNT_MED * SPATIAL_RIPPLE_AMOUNT
data_cube[SHOCK_ZIP-1, SHOCK_TYPE_LUXURY, SHOCK_MONTH + SPATIAL_DELAY:] += SHOCK_AMOUNT_LUXURY * SPATIAL_RIPPLE_AMOUNT
data_cube[SHOCK_ZIP+1, SHOCK_TYPE_LUXURY, SHOCK_MONTH + SPATIAL_DELAY:] += SHOCK_AMOUNT_LUXURY * SPATIAL_RIPPLE_AMOUNT

TYPE_DELAY = 9
TYPE_RIPPLE_AMOUNT = 0.3
data_cube[SHOCK_ZIP, SHOCK_TYPE_MED-1, SHOCK_MONTH + TYPE_DELAY:] += SHOCK_AMOUNT_MED * TYPE_RIPPLE_AMOUNT
data_cube[SHOCK_ZIP, SHOCK_TYPE_MED+1, SHOCK_MONTH + TYPE_DELAY:] += SHOCK_AMOUNT_MED * TYPE_RIPPLE_AMOUNT

# --- 5. Create the 3D "Tower" Visualization ---

fig = plt.figure(figsize=(14, 10))
ax = fig.add_subplot(111, projection='3d')

# Define the X, Y coordinates for the bars
# We create a "meshgrid" to give (x,y) for each bar
x_pos, y_pos = np.meshgrid(np.arange(NUM_TYPES), np.arange(NUM_ZIPS))
x_pos = x_pos.flatten()
y_pos = y_pos.flatten()
z_pos = np.zeros(NUM_ZIPS * NUM_TYPES) # All bars start at z=0

# Define the bar dimensions
dx = 0.8 # Bar width (for Type)
dy = 0.8 # Bar depth (for Zip)

# Set up colormap for the tower heights
# We fix the min/max so the colors are consistent across all frames
vmin = data_cube.min()
vmax = data_cube.max()
norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
cmap = plt.get_cmap('viridis')

# This text object will show the current month
time_text = ax.text2D(0.05, 0.95, '', transform=ax.transAxes, fontsize=14,
                     bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))

# The "update" function that "refreshes" the plot for each frame
def update(frame):
    ax.clear() # Clear all old bars from the plot
    
    # Get the 2D data slice for the current month
    data_slice = data_cube[:, :, frame].flatten() # 'dz' (height) of bars
    
    # Get normalized colors for the current data
    colors = cmap(norm(data_slice))
    
    # Draw all the 3D bars (towers)
    ax.bar3d(x_pos, y_pos, z_pos, dx, dy, data_slice, color=colors)
    
    # --- Re-set all labels and titles (since ax.clear() removes them) ---
    ax.set_title(f"3D Price Ripple (Zip x Type)", fontsize=16)
    ax.set_xlabel("Home Type")
    ax.set_ylabel("Zip Code")
    ax.set_zlabel("Median Home Value ($)")
    
    # Set the X-axis ticks to be the Home Type labels
    ax.set_xticks(np.arange(NUM_TYPES))
    ax.set_xticklabels(TYPE_LABELS, rotation=-15, ha='left', fontsize=8)

    # Format Z-axis as dollars
    ax.get_zaxis().set_major_formatter(
        plt.FuncFormatter(lambda z, p: f'${int(z/1000)}k')
    )
    
    # Set a good viewing angle
    ax.view_init(elev=40, azim=-60)
    
    # Update the time text
    year = frame // 12
    month = (frame % 12) + 1
    time_text.set_text(f'Month: {frame}\n(Year {year})')
    
    print(f"Rendering frame {frame+1}/{NUM_MONTHS}")
    return fig,

# Create the animation
# NOTE: blit=False is required for most 3D animations
ani = animation.FuncAnimation(
    fig,
    update,
    frames=NUM_MONTHS,
    interval=150, # 150ms per frame
    blit=False
)

# Save the animation as a GIF
print("Saving 3D lattice animation... This will take a few minutes.")
ani.save('real_estate_ripple_3D_animation.gif', writer='pillow')
print("Animation saved as 'real_estate_ripple_3D_animation.gif'")