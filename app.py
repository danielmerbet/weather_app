from flask import Flask, render_template
from apscheduler.schedulers.background import BackgroundScheduler
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for Matplotlib
import matplotlib.pyplot as plt
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
    
    return df

# Function to fetch and plot weather data
def plot_data(df):

    # Step 3: Plot each variable
    plt.figure(figsize=(15, 10))

    # Plot Temperature
    plt.subplot(8, 1, 1)
    plt.plot(df.index, df["Temperature (°C)"], color="red")
    plt.title("Temperature")
    plt.ylabel("°C")
    plt.grid()
    
    # Plot Precipitation
    plt.subplot(8, 1, 2)
    plt.bar(df.index, df["Precipitation (mm)"], width=0.05, color="blue")
    plt.title("Precipitation")
    plt.ylabel("mm")
    plt.grid()

    # Plot Relative Humidity
    plt.subplot(8, 1, 3)
    plt.plot(df.index, df["Relative Humidity (%)"], color="blue")
    plt.title("Relative Humidity")
    plt.ylabel("%")
    plt.grid()

    # Plot Wind Speed
    plt.subplot(8, 1, 4)
    plt.plot(df.index, df["Wind Speed (km/h)"], color="green")
    plt.title("Wind Speed")
    plt.ylabel("km/h")
    plt.xlabel("Time")
    plt.grid()
    
    # Plot Solar Radiation
    plt.subplot(8, 1, 5)
    plt.plot(df.index, df["Solar Radiation (W/m²)"], color="yellow")
    plt.title("Solar Radiation")
    plt.ylabel("W/m²")
    plt.xlabel("Time")
    plt.grid()
    
    # Plot Cloud Cover
    plt.subplot(8, 1, 6)
    plt.plot(df.index, df["Cloud Cover (%)"], color="grey")
    plt.title("Cloud Cover")
    plt.ylabel("%")
    plt.xlabel("Time")
    plt.grid()
    
    # Plot Surface Pressure (hPa)
    plt.subplot(8, 1, 7)
    plt.plot(df.index, df["Surface Pressure (hPa)"], color="violet")
    plt.title("Surface Pressure")
    plt.ylabel("hPa")
    plt.xlabel("Time")
    plt.grid()
    
    # Plot Evaporations (mm)
    plt.subplot(8, 1, 8)
    plt.plot(df.index, df["Potential Evaporation (mm)"], color="magenta")
    plt.plot(df.index, df["Evaporation (mm)"], color="pink")
    plt.title("Potential Evaporation and Evaporation")
    plt.ylabel("mm")
    plt.xlabel("Time")
    plt.grid()
    
    #plt.subplot(9, 1, 9)
    #plt.plot(df.index, df["Evaporation (mm)"], color="pink")
    #plt.title("Evaporation")
    #plt.ylabel("mm")
    #plt.xlabel("Time")
    #plt.grid()

    # Save plot to static folder
    plt.tight_layout()
    plot_path = os.path.join("static", "plot.png")
    plt.savefig(plot_path)
    plt.close()

#Run for the first time
df = fetch()
plot_data(df)

# Schedule the fetch_and_plot function to run every hour
scheduler = BackgroundScheduler()
scheduler.add_job(plot_data, "interval", hours=1)
scheduler.start()

# Route to display the plot
@app.route("/")
def index():
  # Call the function initially to generate the plot
  plot_data()
  return render_template("index.html")

@app.teardown_appcontext
def shutdown_scheduler(exception=None):
  try:
      if scheduler.running:
          scheduler.shutdown()
  except SchedulerNotRunningError:
      pass

if __name__ == '__main__':
  app.run(debug=True)
