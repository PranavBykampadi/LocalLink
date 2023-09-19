# app/routes.py

from flask import render_template, request, jsonify
from app import app
from app.config import google_maps_api_key, google_maps_directions_url, uber_estimate_url, uber_server_token
import requests


# Define your routes and logic here

# Define your routes and logic here
@app.route('/')
def index():
    return render_template('index.html')

def select_best_transit_option(transit_data):
    # Initialize variables to track the best option
    best_option = None
    best_duration = float('inf')  # Set to positive infinity initially

    # Loop through each available transit option
    for route in transit_data['routes']:
        # Calculate the total duration for this option
        total_duration = 0
        for step in route['legs']:
            total_duration += step['duration']['value']  # Duration in seconds

        # Check if this option has a shorter duration
        if total_duration < best_duration:
            best_duration = total_duration
            best_option = route

    return best_option

def get_transit_and_uber_directions(start_location, end_location):
    # Make a request to Google Maps Directions API for transit directions
    params = {
        'origin': start_location,
        'destination': end_location,
        'mode': 'transit',
        'key': google_maps_api_key
    }
    response = requests.get(google_maps_directions_url, params=params)
    transit_data = response.json()

    # Analyze the transit_data and choose the best option
    transit_data = select_best_transit_option(transit_data)

    # Estimate Uber rides for the first and last mile
    uber_estimate_start_to_transit = estimate_uber_ride(start_location, transit_data['legs'][0]['start_location'])
    uber_estimate_transit_to_end = estimate_uber_ride(transit_data['legs'][-1]['end_location'], end_location)

    # Return the complete itinerary
    complete_itinerary = {
        'transit_data': transit_data,
        'start_to_transit_uber': uber_estimate_start_to_transit,
        'transit_to_end_uber': uber_estimate_transit_to_end
    }
    return complete_itinerary

def estimate_uber_ride(start_location, end_location):
    # Use the Uber API to estimate rides from start_location to end_location
    headers = {
        'Authorization': f'Bearer {uber_server_token}',
        'Content-Type': 'application/json'
    }
    data = {
        'start_latitude': start_location['lat'],
        'start_longitude': start_location['lng'],
        'end_latitude': end_location['lat'],
        'end_longitude': end_location['lng']
    }
    response = requests.post(uber_estimate_url, headers=headers, json=data)
    uber_estimate = response.json()
    return uber_estimate


@app.route('/calculate', methods=['POST'])
def calculate():
    start_location = request.form['start_location']
    end_location = request.form['end_location']

    # Make a request to Google Maps Directions API for transit directions
    params = {
        'origin': start_location,
        'destination': end_location,
        'mode': 'transit',
        'key': google_maps_api_key
    }
    response = requests.get(google_maps_directions_url, params=params)
    transit_data = response.json()

    # Use the select_best_transit_option function to find the best transit route
    best_transit_option = select_best_transit_option(transit_data)

    # Implement the logic to estimate Uber rides here
    # You can use the code from the previous responses here
    
    return jsonify(complete_itinerary)  # Return the itinerary as JSON
def book_uber_ride(uber_estimate):
    # use uber api to book here
    ride_details = {
        'user_id': '12345',
        'ride_id': '54321',
        'status': 'Booked'
    }
    
    return ride_details

# Main Program
if __name__ == '__main__':
    # Collect user input for start and end locations
    start_location = {
        'lat': 37.7749,
        'lng': -122.4194  # Replace with user input or use a geocoding API to convert address to coordinates
    }
    end_location = {
        'lat': 37.8049,
        'lng': -122.4154  # Replace with user input or use a geocoding API to convert address to coordinates
    }

    # Get the complete itinerary with transit and Uber rides
    complete_itinerary = get_transit_and_uber_directions(start_location, end_location)

    # Book Uber rides based on the estimated fares
    start_to_transit_uber = complete_itinerary['start_to_transit_uber']
    transit_to_end_uber = complete_itinerary['transit_to_end_uber']
    
    ride_start = book_uber_ride(start_to_transit_uber)
    ride_end = book_uber_ride(transit_to_end_uber)
    
    # Now, you can display or use the complete itinerary as needed
    print(complete_itinerary)
    print(f'Start Uber Ride Details: {ride_start}')
    print(f'End Uber Ride Details: {ride_end}')