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

app = Flask(__name__)
scheduler = BackgroundScheduler()

def fetch_data():
      # Step 1: Fetch data from the API
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": 41.97,
        "longitude": 2.38,
        "hourly": "temperature_2m,precipitation,relative_humidity_2m,wind_speed_10m,cloud_cover,surface_pressure,shortwave_radiation,et0_fao_evapotranspiration,evapotranspiration",
        "timezone": "auto"
    }
    response = requests.get(url, params=params)
    data = response.json()

    # Step 2: Extract and prepare data
    timestamps = [datetime.fromisoformat(t) for t in data["hourly"]["time"]]
    temperature = data["hourly"]["temperature_2m"]
    precipitation = data["hourly"]["precipitation"]
    humidity = data["hourly"]["relative_humidity_2m"]
    wind_speed = data["hourly"]["wind_speed_10m"]
    cloud_cover = data["hourly"]["cloud_cover"]
    surface_pressure = data["hourly"]["surface_pressure"]
    shortwave_radiation = data["hourly"]["shortwave_radiation"]
    potential_evaporation = data["hourly"]["et0_fao_evapotranspiration"]
    evaporation = data["hourly"]["evapotranspiration"]
    
    # Convert to pandas DataFrame
    df = pd.DataFrame({
        "Time": timestamps,
        "Temperature (°C)": temperature,
        "Precipitation (mm)": precipitation,
        "Relative Humidity (%)": humidity,
        "Wind Speed (km/h)": wind_speed,
        "Solar Radiation (W/m²)": shortwave_radiation,
        "Cloud Cover (%)": cloud_cover,
        "Surface Pressure (hPa)": surface_pressure,
        "Potential Evaporation (mm)": potential_evaporation,
        "Evaporation (mm)": evaporation
    })
    df.set_index("Time", inplace=True)
    
    # Filter the DataFrame to show only data from the current hour onwards
    current_time = datetime.now()
    df = df[df.index >= current_time]
    
    return df

# Function to plot weather data
cm = 1 / 2.54
def plot_data(df):
    # Create a figure for multiple plots
    fig, axs = plt.subplots(4, 1, figsize=(12*cm, 10*cm))
    fig.tight_layout(pad=2.0)  # Reduce padding to make use of more space
    fig.subplots_adjust(hspace=0.1)  # Adjust margins
    
    # Plot 1: Temperature and Precipitation
    axs[0].plot(df.index, df["Temperature (°C)"], color="red", lw=1, label="Temperature (°C)")
    axs2 = axs[0].twinx()
    axs2.bar(df.index, df["Precipitation (mm)"], width=0.05, color="blue", alpha=0.6, label="Precipitation (mm)")
    axs[0].set_ylabel("Temp (°C)", fontsize=6, color="red")
    axs2.set_ylabel("Precipitation (mm)", fontsize=6, color="blue")
    axs[0].tick_params(axis='y', labelsize=6, labelcolor="red")
    axs2.tick_params(axis='y', labelsize=6, labelcolor="blue")
    axs[0].tick_params(axis='x', labelbottom=False)
    #axs[0].tick_params(axis='x', rotation=45, labelsize=6)
    axs[0].grid(True)

    # Plot 2: Relative Humidity and Wind Speed
    axs[1].plot(df.index, df["Relative Humidity (%)"], color="purple", lw=1, label="Relative Humidity (%)")
    axs2 = axs[1].twinx()
    axs2.plot(df.index, df["Wind Speed (km/h)"], color="green", lw=1, linestyle="--", label="Wind Speed (km/h)")
    axs[1].set_ylabel("Humidity (%)", fontsize=6, color="purple")
    axs2.set_ylabel("Wind Speed (km/h)", fontsize=6, color="green")
    axs[1].tick_params(axis='y', labelsize=6, labelcolor="purple")
    axs2.tick_params(axis='y', labelsize=6, labelcolor="green")
    axs[1].tick_params(axis='x', labelbottom=False)
    axs[1].grid(True)

    # Plot 3: Solar Radiation and Cloud Cover
    axs[2].plot(df.index, df["Solar Radiation (W/m²)"], color="orange", lw=1, label="Solar Radiation (W/m²)")
    axs2 = axs[2].twinx()
    axs2.plot(df.index, df["Cloud Cover (%)"], color="gray", lw=1, linestyle="--", label="Cloud Cover (%)")
    axs[2].set_ylabel("Solar Rad. (W/m²)", fontsize=6, color="orange")
    axs2.set_ylabel("Cloud Cover (%)", fontsize=6, color="gray")
    axs[2].tick_params(axis='y', labelsize=6, labelcolor="orange")
    axs2.tick_params(axis='y', labelsize=6, labelcolor="gray")
    axs[2].tick_params(axis='x', labelbottom=False)
    axs[2].grid(True)

    # Plot 4: Surface Pressure and Evaporation
    axs[3].plot(df.index, df["Surface Pressure (hPa)"], color="brown", lw=1, label="Surface Pressure (hPa)")
    axs2 = axs[3].twinx()
    axs2.plot(df.index, df["Potential Evaporation (mm)"], color="magenta", lw=1, linestyle="-.", label="Pot. Evap. (mm)")
    axs2.plot(df.index, df["Evaporation (mm)"], color="pink", lw=1, linestyle="--", label="Evaporation (mm)")
    axs[3].set_ylabel("Pressure (hPa)", fontsize=6, color="brown")
    axs2.set_ylabel("Evap./Pot. Evap. (mm)", fontsize=6, color="magenta")
    axs[3].tick_params(axis='y', labelsize=6, labelcolor="brown")
    axs2.tick_params(axis='y', labelsize=6, labelcolor="magenta")
    axs[3].tick_params(axis='x', rotation=45, labelsize=6)
    axs[3].grid(True)

    # Set x-axis formatting for all subplots
    for ax in axs:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=6))
        
    # Adjust x-axis limits to make sure all plots align
    axs[0].set_xlim([df.index.min(), df.index.max()])  # Set the same x-limits for all plots
    axs[1].set_xlim([df.index.min(), df.index.max()])
    axs[2].set_xlim([df.index.min(), df.index.max()])
    axs[3].set_xlim([df.index.min(), df.index.max()])

    # Save the plot to static folder
    plot_path = os.path.join("static", "plot.png")
    plt.savefig(plot_path, dpi=300)
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
