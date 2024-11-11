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

def fetch():
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

# Function to fetch and plot weather data
def plot_data(df):
    # Create a figure for multiple plots
    fig, axs = plt.subplots(4, 1, figsize=(15, 12))
    fig.tight_layout(pad=4.0)  # Adjust spacing between plots
    
    # Reduce the spacing between subplots
    fig.subplots_adjust(hspace=0.1)  # Adjust vertical spacing
    
    # Plot 1: Temperature and Precipitation
    axs[0].plot(df.index, df["Temperature (°C)"], color="red", lw=2, label="Temperature (°C)")
    axs2 = axs[0].twinx()
    axs2.bar(df.index, df["Precipitation (mm)"], width=0.05, color="blue", alpha=0.6, label="Precipitation (mm)")
    #axs[0].set_title("Temperature and Precipitation", fontsize=16)
    #axs[0].set_xlabel("Time", fontsize=14)
    axs[0].set_ylabel("Temperature (°C)", fontsize=14, color="red")
    axs2.set_ylabel("Precipitation (mm)", fontsize=14, color="blue")
    axs[0].tick_params(axis='y', labelcolor="red")
    axs2.tick_params(axis='y', labelcolor="blue")
    axs[0].grid(True)
    #axs[0].tick_params(axis='x', rotation=45)
    axs[0].tick_params(axis='x', labelbottom=False) #this remove the x-labels

    # Plot 2: Relative Humidity and Wind Speed
    axs[1].plot(df.index, df["Relative Humidity (%)"], color="purple", lw=2, label="Relative Humidity (%)")
    axs2 = axs[1].twinx()
    axs2.plot(df.index, df["Wind Speed (km/h)"], color="green", lw=2, label="Wind Speed (km/h)", linestyle="--")
    #axs[1].set_title("Relative Humidity and Wind Speed", fontsize=16)
    #axs[1].set_xlabel("Time", fontsize=14)
    axs[1].set_ylabel("Relative Humidity (%)", fontsize=14, color="purple")
    axs2.set_ylabel("Wind Speed (km/h)", fontsize=14, color="green")
    axs[1].tick_params(axis='y', labelcolor="purple")
    axs2.tick_params(axis='y', labelcolor="green")
    axs[1].grid(True)
    #axs[1].tick_params(axis='x', rotation=45)
    axs[1].tick_params(axis='x', labelbottom=False)

    # Plot 3: Solar Radiation and Cloud Cover
    axs[2].plot(df.index, df["Solar Radiation (W/m²)"], color="orange", lw=2, label="Solar Radiation (W/m²)")
    axs2 = axs[2].twinx()
    axs2.plot(df.index, df["Cloud Cover (%)"], color="gray", lw=2, label="Cloud Cover (%)", linestyle="--")
    #axs[2].set_title("Solar Radiation and Cloud Cover", fontsize=16)
    #axs[2].set_xlabel("Time", fontsize=14)
    axs[2].set_ylabel("Solar Radiation (W/m²)", fontsize=14, color="orange")
    axs2.set_ylabel("Cloud Cover (%)", fontsize=14, color="grey")
    axs[2].tick_params(axis='y', labelcolor="orange")
    axs2.tick_params(axis='y', labelcolor="grey")
    axs[2].grid(True)
    #axs[2].tick_params(axis='x', rotation=45)
    axs[2].tick_params(axis='x', labelbottom=False)

    # Plot 4: Surface Pressure and Evaporations
    axs[3].plot(df.index, df["Surface Pressure (hPa)"], color="brown", lw=2, label="Surface Pressure (hPa)")
    axs2 = axs[3].twinx()
    axs2.plot(df.index, df["Potential Evaporation (mm)"], color="magenta", lw=2, label="Potential Evaporation (mm)", linestyle="-.")
    axs2.plot(df.index, df["Evaporation (mm)"], color="pink", lw=2, label="Evaporation (mm)", linestyle="--")
    #axs[3].set_title("Surface Pressure and Evaporations", fontsize=16)
    #axs[3].set_xlabel("Time", fontsize=14)
    axs[3].set_ylabel("Surface Pressure (hPa)", fontsize=14, color="brown")
    axs2.set_ylabel("Evaporat./Pot.Evaporat. (mm)", fontsize=14, color="magenta")
    axs[3].tick_params(axis='y', labelcolor="brown")
    axs2.tick_params(axis='y', labelcolor="magenta")
    axs[3].grid(True)
    axs[3].tick_params(axis='x', rotation=45)

    # Format x-axis for all subplots to display month-day hour
    for ax in axs:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))  # Format as Month-Day Hour
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=6))  # Set major ticks every hour

    # Save the plot to static folder
    plot_path = os.path.join("static", "plot.png")
    plt.savefig(plot_path, dpi=300)  # Save with higher DPI for better quality
    plt.close()


#Run for the first time
df = fetch()
plot_data(df)

# Schedule the fetch_and_plot function to run every hour
#scheduler = BackgroundScheduler()
#scheduler.add_job(lambda: plot_data(fetch()), "interval", hours=1)
#scheduler.start()

# Route to display the plot
#@app.route("/")
#def index():
  # Call the function initially to generate the plot
#  plot_data(fetch())
#  return render_template("index.html")

#@app.teardown_appcontext
#def shutdown_scheduler(exception=None):
#  try:
#      if scheduler.running:
#          scheduler.shutdown()
#  except SchedulerNotRunningError:
#      pass

#if __name__ == '__main__':
#  app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
