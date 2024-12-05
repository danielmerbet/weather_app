from flask import Flask, render_template
from apscheduler.schedulers.background import BackgroundScheduler
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for Matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates  # Import for date formatting
import requests
from datetime import datetime
import pandas as pd
import os
from matplotlib.ticker import MultipleLocator
from matplotlib.ticker import FuncFormatter

app = Flask(__name__)
scheduler = BackgroundScheduler()

lat = 41.97
lon = 2.38
model = "gfs_seamless" #"icon_seamless" # "gfs_seamless"
if model == "gfs_seamless":
  members = 31
if model == "icon_seamless":
  members = 40
def fetch_data():
    # Step 1: Fetch data from the API
    url = "https://ensemble-api.open-meteo.com/v1/ensemble"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,precipitation,relative_humidity_2m,wind_speed_10m,cloud_cover,surface_pressure,shortwave_radiation,et0_fao_evapotranspiration",
        "timezone": "Europe/Berlin", #auto
        "models": model
    }
    response = requests.get(url, params=params)
    data = response.json()

    # Step 2: Extract timestamps
    timestamps = [datetime.fromisoformat(t) for t in data["hourly"]["time"]]
    
    # Step 3: Prepare data for all ensemble members
    ensemble_data = {"Time": timestamps}  # Start with the timestamps
    
    for variable in ["temperature_2m", "precipitation", "relative_humidity_2m",
                     "wind_speed_10m", "cloud_cover", "surface_pressure",
                     "shortwave_radiation", "et0_fao_evapotranspiration"]:
        for member in range(members):  # ensemble members
            member_key = f"{variable}_member{str(member).zfill(2)}"
            #member 0 is not called the same way
            if member == 0:
              member_key = f"{variable}"
              ensemble_data[f"{variable}_member{member}"] = data["hourly"][member_key]
            if member_key in data["hourly"]:  # Check if the member exists
                ensemble_data[f"{variable}_member{member}"] = data["hourly"][member_key]
    
    # Step 4: Convert to DataFrame in one go
    df = pd.DataFrame(ensemble_data)
    df.set_index("Time", inplace=True)

    # Filter to show only data from the current hour onwards
    #current_time = datetime.now()
    #df = df[df.index >= current_time]
    
    return df

# Function to plot weather data
label_sizes = 3
def plot_data(df):
    cm = 1 / 2.54
    now = datetime.now()  # Get the current time
    fig, axs = plt.subplots(4, 1, figsize=(10 * cm, 8 * cm), sharex=True)  # Share x-axis across all subplots
    fig.tight_layout(pad=0.5)
    fig.subplots_adjust(hspace=0.1)

    # Define a function to format y-axis for more values
    def format_y_axis(ax, step):
        #ax.yaxis.set_major_locator(MultipleLocator(step))
        ax.tick_params(axis='y', labelsize=label_sizes, color="gray", width=0.3)  # Reduce font size
        ax.spines['left'].set_visible(False)  # Hide the left axis spine
        ax.spines['top'].set_visible(False)   # Hide the top axis spine
        ax.spines['right'].set_visible(False) # Hide the right axis spine
        ax.spines['bottom'].set_linewidth(0.3)  # Reduce thickness of bottom spine
        ax.spines['bottom'].set_color('gray')   # Change color to gray
        
    def format_y_axis_precipitation(ax):
        #ax.yaxis.set_major_locator(MultipleLocator(step))
        ax.tick_params(axis='y', labelsize=label_sizes, color="gray", width=0.3)  # Reduce font size
        ax.spines['left'].set_visible(False)  # Hide the left axis spine
        ax.spines['top'].set_visible(False)   # Hide the top axis spine
        ax.spines['right'].set_visible(False) # Hide the right axis spine
        ax.spines['bottom'].set_linewidth(0.3)  # Reduce thickness of bottom spine
        ax.spines['bottom'].set_color('gray')   # Change color to gray

    # Custom x-axis formatter function
    def custom_date_formatter(x, pos):
        date = mdates.num2date(x)
        if date.hour == 0 and date.minute == 0:  # Show only the date at midnight
            #return date.strftime('%d-%m') # Format '05-12'
            return date.strftime('%-d %b')  # Format as '5 Dec'
        elif date.hour == 12 and date.minute == 0:  # Show only the time at noon
            return date.strftime('%H:%M')
        else:
            return ""

    # Plot 1: Temperature Ensemble Members
    for member in range(members):
        col_name = f"temperature_2m_member{member}"
        if col_name in df.columns:
            axs[0].plot(df.index, df[col_name], lw=0.5, alpha=0.7, color="black")
    axs[0].axvline(now, color="gray", linestyle="solid", lw=0.5, label="Current Time")  # Vertical line at current time
    axs[0].set_ylabel("Temperature (°C)", fontsize=label_sizes, labelpad=0)
    axs[0].tick_params(axis='x', labelbottom=False, color="gray", width=0.3)
    format_y_axis(axs[0], step=5)  # Increase y-axis resolution
    axs[0].grid(axis='y', linewidth=0.2, color='gray')

    # Plot 2: Precipitation Ensemble Members
    for member in range(members):
        col_name = f"precipitation_member{member}"
        if col_name in df.columns:
            axs[1].plot(df.index, df[col_name], lw=0.5, alpha=0.7, color="blue")
    axs[1].axvline(now, color="gray", linestyle="solid", lw=0.5)
    axs[1].set_ylabel("Precipitation (mm)", fontsize=label_sizes, labelpad=0)
    axs[1].tick_params(axis='x', labelbottom=False, color="gray", width=0.3)
    format_y_axis_precipitation(axs[1])  # Increase y-axis resolution
    axs[1].grid(axis='y', linewidth=0.2, color='gray')

    # Plot 3: Humidity Ensemble Members
    for member in range(members):
        col_name = f"relative_humidity_2m_member{member}"
        if col_name in df.columns:
            axs[2].plot(df.index, df[col_name], lw=0.5, alpha=0.7, color="purple")
    axs[2].axvline(now, color="gray", linestyle="solid", lw=0.5)
    axs[2].set_ylabel("Humidity (%)", fontsize=label_sizes, labelpad=0)
    axs[2].tick_params(axis='x', labelbottom=False, color="gray", width=0.3)
    format_y_axis(axs[2], step=20)  # Increase y-axis resolution
    axs[2].grid(axis='y', linewidth=0.2, color='gray')

    # Plot 4: Wind Speed Ensemble Members
    for member in range(members):
        col_name = f"wind_speed_10m_member{member}"
        if col_name in df.columns:
            axs[3].plot(df.index, df[col_name], lw=0.5, alpha=0.7, color="green")
    axs[3].axvline(now, color="gray", linestyle="solid", lw=0.5)
    axs[3].set_ylabel("Wind Speed (km/h)", fontsize=label_sizes, labelpad=0)
    axs[3].tick_params(axis='x', rotation=0, labelsize=label_sizes, color="gray", width=0.3)
    format_y_axis(axs[3], step=5)  # Increase y-axis resolution
    axs[3].grid(axis='y', linewidth=0.2, color='gray')

    # Apply custom x-axis formatter to the bottom subplot
    axs[3].xaxis.set_major_formatter(FuncFormatter(custom_date_formatter))
    axs[3].xaxis.set_major_locator(mdates.HourLocator(byhour=[0, 12]))  # Major ticks at 00:00 and 12:00
    #axs[3].xaxis.set_minor_locator(mdates.HourLocator(interval=6))  # Minor ticks every hour

    # Add the main x-axis label
    axs[3].set_xlabel("Time (UTC +1)", fontsize=label_sizes, labelpad=1)
    #change y-axis
    axs[3].tick_params(axis='y', labelsize=label_sizes)

    # Save the plot
    plt.savefig("static/plot.png", dpi=300)
    plt.close()

# Fetch and plot data, called every hour by the scheduler
def fetch_and_plot():
    df = fetch_data()
    plot_data(df)

# Run the initial fetch and plot
fetch_and_plot()

# Schedule the fetch_and_plot function to run every hour
scheduler.add_job(fetch_and_plot, "interval", hours=1)
scheduler.start()

# Flask route to display the plot
@app.route("/")
def index():
    # Update plot before rendering
    fetch_and_plot()
    return render_template("index.html")

# Shutdown scheduler gracefully when app context is terminated
@app.teardown_appcontext
def shutdown_scheduler(exception=None):
    try:
        if scheduler.running:
            scheduler.shutdown()
    except SchedulerNotRunningError:
        pass

if __name__ == '__main__':
    #app.run(debug=True)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 3000)), debug=True)
