import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# --- 1. Create the "Real" Real Estate Dataset ---

NUM_ZIPS = 20    # Our 1D lattice (i)
NUM_MONTHS = 120 # Our time steps (t)

# Create a baseline price gradient (e.g., cheaper farther from city)
# Based on Austin, TX data, median prices are in the $400k-$700k range
base_prices = np.linspace(700000, 400000, NUM_ZIPS)

# Create our 2D spacetime heatmap (Zip Code vs. Month)
data = np.zeros((NUM_ZIPS, NUM_MONTHS))

# Add some baseline market growth and noise
# We'll use a small, compounding growth factor
market_growth_rate = 1.003
current_prices = base_prices.copy()

for t in range(NUM_MONTHS):
    # Add a little random noise
    noise = np.random.randn(NUM_ZIPS) * 2000
    data[:, t] = current_prices + noise
    
    # Apply baseline market growth
    current_prices *= market_growth_rate

# --- ADD THE "MICRO-CAUSE" (Poke) ---
SHOCK_ZIP = 5
SHOCK_MONTH = 20
SHOCK_AMOUNT = 150000  # A $150k price jump

# The shock hits the target zip code
data[SHOCK_ZIP, SHOCK_MONTH:] += SHOCK_AMOUNT

# --- ADD THE "RIPPLE" (Temporal Propagation) ---
# The ripple hits adjacent zip codes (4 & 6) 6 months later
RIPPLE_1_DELAY = 6
RIPPLE_1_AMOUNT = 75000
data[SHOCK_ZIP - 1, SHOCK_MONTH + RIPPLE_1_DELAY:] += RIPPLE_1_AMOUNT
data[SHOCK_ZIP + 1, SHOCK_MONTH + RIPPLE_1_DELAY:] += RIPPLE_1_AMOUNT

# The ripple hits the next zip codes (3 & 7) 12 months later
RIPPLE_2_DELAY = 12
RIPPLE_2_AMOUNT = 30000
data[SHOCK_ZIP - 2, SHOCK_MONTH + RIPPLE_2_DELAY:] += RIPPLE_2_AMOUNT
data[SHOCK_ZIP + 2, SHOCK_MONTH + RIPPLE_2_DELAY:] += RIPPLE_2_AMOUNT


# --- 2. Create the Moving Visualization ("Refresh the Page") ---

fig, ax = plt.subplots(figsize=(10, 6))

# Set up the plot elements
ax.set_ylim(350000, 950000) # Set Y-axis for price
ax.set_xlim(0, NUM_ZIPS - 1) # Set X-axis for zip codes
ax.set_xlabel("Zip Code (Sorted by Distance from City)")
ax.set_ylabel("Median Home Value ($)")
ax.set_title("Real Estate Price Ripple over Time")

# Format Y-axis as dollars
ax.get_yaxis().set_major_formatter(
    plt.FuncFormatter(lambda x, p: f'${int(x/1000)}k')
)

# This is the line object that will be updated each frame
line, = ax.plot([], [], lw=2, marker='o', markersize=4)

# This text object will show the current month
time_text = ax.text(0.02, 0.95, '', transform=ax.transAxes, fontsize=12,
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))

# This vertical line shows the "shock" location
ax.axvline(SHOCK_ZIP, color='red', linestyle='--', label=f'Zip {SHOCK_ZIP} (Shock Point)')
ax.legend(loc='upper right')

# Initialization function for the animation
def init():
    line.set_data([], [])
    time_text.set_text('')
    return line, time_text

# The "update" function that "refreshes" the plot for each frame
def update(frame):
    # Get the data for the current month (frame)
    y_data = data[:, frame]
    x_data = np.arange(NUM_ZIPS)
    
    # Update the line plot
    line.set_data(x_data, y_data)
    
    # Update the time text
    year = frame // 12
    month = (frame % 12) + 1
    time_text.set_text(f'Month: {frame} (Year {year}, Month {month})')
    
    return line, time_text

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
print("Saving animation... This may take a moment.")
ani.save('real_estate_ripple_animation.gif', writer='pillow')
print("Animation saved as 'real_estate_ripple_animation.gif'")

# To display in environments like Jupyter, you might use:
# from IPython.display import HTML
# HTML(ani.to_jshtml())