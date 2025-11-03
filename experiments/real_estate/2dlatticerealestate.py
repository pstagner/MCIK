import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# --- 1. Define Model Parameters ---
NUM_ZIPS = 20     # Y-Axis: 1D Lattice of Zip Codes
NUM_TYPES = 5     # X-Axis: 1D Lattice of Home Types
NUM_MONTHS = 120  # Time (animation frames)

# Home Type labels for the plot
TYPE_LABELS = ['1. Condo (<2 Bed)', '2. Small SFH (2-3 Bed)', 
               '3. Medium SFH (3-4 Bed)', '4. Large SFH (4+ Bed)', 
               '5. Luxury (5+ Bed)']

# Define the baseline price for each type. Based on Austin data.
base_type_prices = np.array([350000, 450000, 550000, 750000, 950000])

# Create a 3D "Data Cube" to hold all data: (Zip, Type, Month)
data_cube = np.zeros((NUM_ZIPS, NUM_TYPES, NUM_MONTHS))

# --- 2. Create the Baseline "Moving Dataset" ---
# Create a price gradient (cheaper farther from city)
zip_gradient = np.linspace(1.2, 0.8, NUM_ZIPS) # 20% premium near city
market_growth_rate = 1.003 # 0.3% per month

for t in range(NUM_MONTHS):
    for i in range(NUM_ZIPS):
        # Apply baseline price, zip gradient, and market growth
        base_price = base_type_prices * zip_gradient[i] * (market_growth_rate**t)
        
        # Add a little random noise
        noise = np.random.randn(NUM_TYPES) * 2000
        data_cube[i, :, t] = base_price + noise

# --- 3. ADD THE 2D "MICRO-CAUSE" (Poke) ---
SHOCK_MONTH = 20
SHOCK_ZIP = 5         # Y-coordinate of poke
SHOCK_TYPE_MED = 2    # X-coordinate 1
SHOCK_TYPE_LUXURY = 4 # X-coordinate 2

# Define shock amounts
SHOCK_AMOUNT_MED = 150000
SHOCK_AMOUNT_LUXURY = 250000

# Apply the pokes at t=SHOCK_MONTH
data_cube[SHOCK_ZIP, SHOCK_TYPE_MED, SHOCK_MONTH:] += SHOCK_AMOUNT_MED
data_cube[SHOCK_ZIP, SHOCK_TYPE_LUXURY, SHOCK_MONTH:] += SHOCK_AMOUNT_LUXURY


# --- 4. ADD THE "RIPPLE" (Temporal Propagation) ---

# A. Spatial Ripple (Spreads to adjacent zips)
SPATIAL_DELAY = 6 # 6 months
SPATIAL_RIPPLE_AMOUNT = 0.5 # 50% of original shock

# Ripple for Medium SFH
data_cube[SHOCK_ZIP-1, SHOCK_TYPE_MED, SHOCK_MONTH + SPATIAL_DELAY:] += SHOCK_AMOUNT_MED * SPATIAL_RIPPLE_AMOUNT
data_cube[SHOCK_ZIP+1, SHOCK_TYPE_MED, SHOCK_MONTH + SPATIAL_DELAY:] += SHOCK_AMOUNT_MED * SPATIAL_RIPPLE_AMOUNT
# Ripple for Luxury
data_cube[SHOCK_ZIP-1, SHOCK_TYPE_LUXURY, SHOCK_MONTH + SPATIAL_DELAY:] += SHOCK_AMOUNT_LUXURY * SPATIAL_RIPPLE_AMOUNT
data_cube[SHOCK_ZIP+1, SHOCK_TYPE_LUXURY, SHOCK_MONTH + SPATIAL_DELAY:] += SHOCK_AMOUNT_LUXURY * SPATIAL_RIPPLE_AMOUNT


# B. Type Ripple (Spreads to adjacent types in the *same* zip)
TYPE_DELAY = 9 # 9 months
TYPE_RIPPLE_AMOUNT = 0.3 # 30% of original shock

# Medium SFH shock ripples to Small SFH and Large SFH
data_cube[SHOCK_ZIP, SHOCK_TYPE_MED-1, SHOCK_MONTH + TYPE_DELAY:] += SHOCK_AMOUNT_MED * TYPE_RIPPLE_AMOUNT
data_cube[SHOCK_ZIP, SHOCK_TYPE_MED+1, SHOCK_MONTH + TYPE_DELAY:] += SHOCK_AMOUNT_MED * TYPE_RIPPLE_AMOUNT


# --- 5. Create the Moving Visualization ("Refresh the Page") ---

fig, ax = plt.subplots(figsize=(12, 8))

# Get the initial data (t=0)
initial_data = data_cube[:, :, 0]

# Create the heatmap image object
# We set vmin/vmax to fix the color scale across all frames
vmin = base_type_prices.min() * 0.8
vmax = (base_type_prices.max() * 1.2 * (market_growth_rate**NUM_MONTHS)) + SHOCK_AMOUNT_LUXURY

im = ax.imshow(initial_data.T, aspect='auto', cmap='viridis', 
               origin='lower', vmin=vmin, vmax=vmax,
               extent=[-0.5, NUM_ZIPS-0.5, -0.5, NUM_TYPES-0.5])

# Add a color bar
cbar = fig.colorbar(im, ax=ax)
cbar.set_label('Median Home Value ($)')
cbar.ax.yaxis.set_major_formatter(
    plt.FuncFormatter(lambda x, p: f'${int(x/1000)}k')
)

# Set labels and title
ax.set_xlabel("Zip Code (Sorted by Distance from City)")
ax.set_ylabel("Home Type")
ax.set_yticks(ticks=np.arange(NUM_TYPES), labels=TYPE_LABELS)
ax.set_title("2D Real Estate Price Ripple (Zip x Type) over Time")

# Add a marker for the "shock" location
ax.plot(SHOCK_ZIP, SHOCK_TYPE_MED, 'rX', markersize=15, label='Shock Point (Med SFH)')
ax.plot(SHOCK_ZIP, SHOCK_TYPE_LUXURY, 'rX', markersize=15, label='Shock Point (Luxury)')
ax.legend(loc='upper left')

# This text object will show the current month
time_text = ax.text(0.85, 0.95, '', transform=ax.transAxes, fontsize=12,
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))

# Initialization function for the animation
def init():
    im.set_data(data_cube[:, :, 0].T)
    time_text.set_text('')
    return [im, time_text]

# The "update" function that "refreshes" the plot for each frame
def update(frame):
    # Get the 2D data slice for the current month (frame)
    current_data = data_cube[:, :, frame]
    
    # Update the heatmap data
    im.set_data(current_data.T)
    
    # Update the time text
    year = frame // 12
    month = (frame % 12) + 1
    time_text.set_text(f'Month: {frame}\n(Year {year})')
    
    return [im, time_text]

# Create the animation
ani = animation.FuncAnimation(
    fig,
    update,
    frames=NUM_MONTHS,  # Number of frames = number of months
    init_func=init,
    blit=True,
    interval=100  # 100ms per frame (10 FPS)
)

# Save the animation as a GIF
print("Saving 2D lattice animation... This may take a moment.")
ani.save('real_estate_ripple_2D_animation.gif', writer='pillow')
print("Animation saved as 'real_estate_ripple_2D_animation.gif'")