import numpy as np

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, distinct

from flask import Flask, jsonify

# Database Setup
engine = create_engine("sqlite:///hawaii.sqlite")
Base = automap_base()
Base.prepare(engine, reflect=True)

# Save reference to the table
measurement = Base.classes.measurement
station = Base.classes.station

# Flask Setup
app = Flask(__name__)

# Flask Routes

@app.route("/")
def welcome():
    """List all available api routes."""
    return (
        f"Available Routes for Hawaii Weather Data:<br/><br>"
        f"-- Daily Precipitation Totals for Last Year: <a href=\"/api/v1.0/precipitation\">/api/v1.0/precipitation<a><br/>"
        f"-- Active Weather Stations: <a href=\"/api/v1.0/stations\">/api/v1.0/stations<a><br/>"
        f"-- Daily Temperature Observations for Station USC00519281 for Last Year: <a href=\"/api/v1.0/tobs\">/api/v1.0/tobs<a><br/>"
        f"-- Min, Average & Max Temperatures for Date Range: /api/v1.0/trip/yyyy-mm-dd/yyyy-mm-dd<br>"
        f"NOTE: If no end-date is provided, the trip api calculates stats through 08/23/17<br>" 
    )

# Precipitation query function
@app.route("/api/v1.0/precipitation")
def precipitation():
    # Create session
    session = Session(engine)

    """Return a list of all daily precipitation totals for the last year"""
    # Query and summarize daily precipitation across all stations for the last year of available data
    # Start date is one year prior to the most recent date in the db
    start_date = '2016-08-23'
    sel = [measurement.date, 
        func.sum(measurement.prcp)]
    precipitation = session.query(*sel).\
            filter(measurement.date >= start_date).\
            group_by(measurement.date).\
            order_by(measurement.date).all()
   
    session.close()

    # Create dictionary with the date as key and the daily precipitation total as value
    precipitation_dates = []
    precipitation_totals = []

    # Loop to append dates and precpitation totals
    for date, dailytotal in precipitation:
        precipitation_dates.append(date)
        precipitation_totals.append(dailytotal)
    
    precipitation_dict = dict(zip(precipitation_dates, precipitation_totals))

    # Return JSON for API query
    return jsonify(precipitation_dict)

#Stations query function
@app.route("/api/v1.0/stations")
def stations():
    # Create session
    session = Session(engine)

    """Return a list of all the active Weather stations in Hawaii"""
    # Return list of active weather stations
    sel = [measurement.station]
    active_stations = session.query(*sel).\
        group_by(measurement.station).all()
    session.close()

    # Return a dictionary with the date as key and the daily precipitation total as value
    # Convert list of tuples into normal list and return the JSON for query
    list_of_stations = list(np.ravel(active_stations)) 
    return jsonify(list_of_stations)

#Station temperatures query function
@app.route("/api/v1.0/tobs")
def tobs():
    # Create session (link)
    session = Session(engine)
    # Query the last 12 months of temperatures based on end date in data for the most active station
    start_date = '2016-08-23'
    sel = [measurement.date, 
        measurement.tobs]
    station_temps = session.query(*sel).\
            filter(measurement.date >= start_date, measurement.station == 'USC00519281').\
            group_by(measurement.date).\
            order_by(measurement.date).all()

    session.close()

    # Return a dictionary with the date as key and the daily temperature observation as value
    observation_dates = []
    temperature_observations = []

    # Loop to append dates and temperature observations
    for date, observation in station_temps:
        observation_dates.append(date)
        temperature_observations.append(observation)
    
    most_active_tobs_dict = dict(zip(observation_dates, temperature_observations))

    # Return JSON for API query
    return jsonify(most_active_tobs_dict)

#Function to calculate the min/max/avg temperatures in last 12 months
def calculate_trip(start_date, end_date='2017-08-23'):
    
    #Open session
    session = Session(engine)
    query_result = session.query(func.min(measurement.tobs), func.avg(measurement.tobs), func.max(measurement.tobs)).\
        filter(measurement.date >= start_date).filter(measurement.date <= end_date).all()
    session.close()

    # Create dictionary in list
    trip_stats = []
    for min_temp, avg_temp, max_temp in query_result:
        trip_dict = {
            "Min": min_temp,
            "Average": avg_temp,
            "Max": max_temp
        }
        trip_stats.append(trip_dict)
    return trip_stats

# Function to return the caculated trip
@app.route("/api/v1.0/trip/<start_date>/<end_date>")

def combined_trip(start_date, end_date='2017-8-23'):
    trip_stats = calculate_trip(start_date, end_date)

    if trip_stats:
        return jsonify(trip_stats)
    else:
        return jsonify({"error":"Invalid date range or dates not formatted as YYYY-MM-DD."}), 404

# Debug
if __name__ == '__main__':
    app.run(debug=True)