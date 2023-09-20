# Imports
# Main python file
from flask import Flask, render_template, request, jsonify
import http.client 
import json
import os
import sys
import logging  

# Adding the project root directory to the Python path
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

# Configuration
# Import configuration from config.py
from config import google_maps_api_key, google_maps_directions_url, uber_estimate_url, uber_server_token, uber_client_id
#config.py has not been pushed to the repo as it contains sensitive api keys, and this repo is to be made public. The remaining functionality has all been added to a single file to ensure simplicity
# Create a Flask app
app = Flask(__name__)
app.config.from_object('config')

# Setting up logging
logging.basicConfig(level=logging.DEBUG)  # Set the logging level to DEBUG

# Importing urllib.parse for URL encoding
import urllib.parse

# Function to reverse geocode a location
def reverse_geocode(lat, lng):
    conn = http.client.HTTPSConnection("maps.googleapis.com")
    path = "/maps/api/geocode/json"
    params = {
        "latlng": f"{lat},{lng}",
        "key": f"{google_maps_api_key}"
    }

    # Encode the parameters into a query string
    encoded_params = urllib.parse.urlencode(params)
    full_url = f"{path}?{encoded_params}"
    logging.debug(f"Request URL (Reverse Geocode): {full_url}")

    conn.request("GET", full_url)
    response = conn.getresponse()

    if response.status == 200:
        data = response.read()
        geocode_data = json.loads(data.decode("utf-8"))
        
        if geocode_data.get("status") == "OK" and geocode_data.get("results"):
            # Extract the formatted address from the first result
            return geocode_data["results"][0]["formatted_address"]
    
    return None

# Function to select the best transit option from transit data
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

#function to select cheapest transit data
def select_cheapest_transit_option(transit_data):

        cheapest_option = None
        cheapest_cost = float('inf')  # Set to positive infinity initially

        for route in transit_data['routes']:
            cost = route.get('cost', float('inf'))  # You should replace 'cost' with the actual field name

            # Check if this option has a lower cost
            if cost < cheapest_cost:
                cheapest_cost = cost
                cheapest_option = route

        return cheapest_option

# Function to get transit data from Google Maps Directions API
def get_transit_data(origin, destination, mode):
    try:
        # Create an HTTP connection to Google Maps Directions API
        connection = http.client.HTTPSConnection("maps.googleapis.com")

        # Build the request URL for transit data with the specified mode
        request_url = (f"{google_maps_directions_url}?origin={origin}&destination={destination}"
                       f"&mode={mode}&key={google_maps_api_key}")

        logging.debug(f"Request URL (Transit Data): {request_url}")

        # Send an HTTP GET request
        connection.request("GET", request_url)

        # Get the response
        response = connection.getresponse()

        # Check for HTTP errors
        if response.status != 200:
            raise Exception(f"Google Maps Directions API returned an error: {response.status}")

        # Read and parse the response data
        data = response.read()
        json_data = json.loads(data.decode("utf-8"))

        return json_data

    except Exception as e:
        logging.error(f"An error occurred in get_transit_data: {str(e)}")
        raise

# Function to get transit and Uber directions
def get_transit_and_uber_directions(start_location, end_location):
    try:
        # Get the best transit option
        transit_data = select_best_transit_option(get_transit_data(
            start_location['place'].replace(' ', '+'),
            end_location['place'].replace(' ', '+'),
            mode='transit'
        ))

        # Get the start and end points of the transit route
        start_point = transit_data['legs'][0]['start_location']
        end_point = transit_data['legs'][-1]['end_location']

        # Reverse geocode to get human-readable location names
        start_point_place = reverse_geocode(start_point['lat'], start_point['lng'])
        end_point_place = reverse_geocode(end_point["lat"], end_point["lng"])
        
        # Get transit data for first mile to start point and last mile from end point
        transit_data_start_to_start_point = select_best_transit_option(get_transit_data(
            start_location['place'].replace(' ', '+'),
            start_point_place.replace(' ','+'),
            mode='driving'
        ))

        transit_data_end_point_to_end = select_best_transit_option(get_transit_data(
            end_point_place.replace(' ','+'),
            end_location['place'].replace(' ', '+'),
            mode='driving'
        ))

        # Estimate Uber rides for the first and last mile
        uber_estimate_start_to_transit = estimate_uber_ride(start_location, transit_data['legs'][0]['start_location'])
        uber_estimate_transit_to_end = estimate_uber_ride(transit_data['legs'][-1]['end_location'], end_location)

        # Return the complete itinerary
        complete_itinerary = {
            'transit_data': transit_data,
            'start_to_transit_uber': transit_data_start_to_start_point,
            'transit_to_end_uber': transit_data_end_point_to_end
        }
        return complete_itinerary

    except Exception as e:
        logging.error(f"An error occurred in get_transit_and_uber_directions: {str(e)}")
        raise

# Function to estimate an Uber ride
def estimate_uber_ride(start_location, end_location):
    try:
        '''# Creating an HTTP connection to Uber Estimate API (assuming proper setup)
        connection = http.client.HTTPSConnection("api.uber.com")

        request_url = f"{uber_estimate_url}"

        headers = {
            'Authorization': f'Bearer {uber_server_token}',
            'Content-Type': 'application/json'
        }

        # Define the request data
        data = {
            'start_latitude': start_location['lat'],
            'start_longitude': start_location['lng'],
            'end_latitude': end_location['lat'],
            'end_longitude': end_location['lng']
        }

        # Send an HTTP POST request to Uber Estimate API
        connection.request("POST", request_url, body=json.dumps(data), headers=headers)

        # Get the response
        response = connection.getresponse()

        # Check for HTTP errors
        if response.status != 200:
            raise Exception(f"Uber Estimate API returned an error: {response.status}")

        # Read and parse the response data
        data = response.read()
        uber_estimate = json.loads(data.decode("utf-8"))'''
        #we still haven't been given the scope based access for the above code to work, so we are using a place holder estimate function based on distance between start and end location
        connection = http.client.HTTPSConnection("maps.googleapis.com")
            
        # Building the request URL for distance matrix data
        request_url = (f"/maps/api/distancematrix/json?"
                        f"origins={start_location['lat']},{start_location['lng']}"
                        f"&destinations={end_location['lat']},{end_location['lng']}"
                        f"&key={google_maps_api_key}")
            
        logging.debug(f"Request URL (Distance Matrix): {request_url}")
        
        # Send an HTTP GET request
        connection.request("GET", request_url)
            
        response = connection.getresponse()
            
        if response.status != 200:
            raise Exception(f"Google Maps Distance Matrix API returned an error: {response.status}")
                    
        data = response.read()
        distance_matrix_data = json.loads(data.decode("utf-8"))
            
        
        road_distance_meters = distance_matrix_data['rows'][0]['elements'][0]['distance']['value']
            
        road_distance_km = road_distance_meters / 1000.0
            
        # random rate defined
        rate_per_km = 0.5  
            
        uber_estimate = road_distance_km * rate_per_km

        return {'start_location' : start_location, 'end_location' : end_location, 'estimated_cost' : uber_estimate }

    except Exception as e:
        logging.error(f"An error occurred in estimate_uber_ride: {str(e)}")
        raise

# Function to book an Uber ride (replace with actual Uber API call)
def book_uber_ride(uber):
    try:
        ''' # Define the Uber API endpoint for requesting a ride
        api_url = "https://api.uber.com/v1.2/requests"

        # Define the headers for the API request
        headers = {
            "Authorization": f"Bearer {uber_server_token}",
            "Content-Type": "application/json"
        }

        # Define the request data
        request_data = {
            "product_id": "{uber_client_id}",  # Replace with the actual product ID
            "start_latitude": uber_estimate['start_location']['lat'],
            "start_longitude": uber_estimate['start_location']['lng'],
            "end_latitude": uber_estimate['end_location']['lat'],
            "end_longitude": uber_estimate['end_location']['lng']
        }

        # Make a POST request to request an Uber ride
        response = requests.post(api_url, headers=headers, json=request_data)

        # Check if the request was successful
        if response.status_code == 202:
            # Ride request was successful
            ride_details = response.json()
            return ride_details
        else:
            # Ride request failed
            error_message = response.text
            logging.error(f"Uber API error: {error_message}")
            return None'''
        #We haven't yet received the authorisation to do the above, so we are giving place holder values for now.

        ride_details = {
            'transit_data': uber,
            'user_id': '12345',
            'ride_id': '54321',
            'status': 'Booked'
        }
        return ride_details

    except Exception as e:
        logging.error(f"An error occurred in book_uber_ride: {str(e)}")
        raise

# Routes

# Route for the main page
@app.route('/')
def index():
    return render_template('index.html')

# Route to calculate transit and Uber options
@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        data = request.json
        start_location = data.get('start_location')
        end_location = data.get('end_location')
        logging.debug(f"start location: {start_location}")

        # Get the complete itinerary with transit and Uber rides
        complete_itinerary = get_transit_and_uber_directions(start_location, end_location)

        # Book Uber rides based on the estimated fares
        start_to_transit_uber = book_uber_ride(complete_itinerary['start_to_transit_uber'])
        transit_to_end_uber = book_uber_ride(complete_itinerary['transit_to_end_uber'])
        logging.debug(f"start to transit uber{start_to_transit_uber}")

        # Return a JSON response indicating success
        return jsonify({
            'message': 'Success',
            'transit_data': complete_itinerary['transit_data'],
            'start_to_transit_uber': start_to_transit_uber,
            'transit_to_end_uber': transit_to_end_uber
        })

    except Exception as e:
        error_message = str(e) if str(e) else 'An error occurred'
        logging.error(f"An error occurred in calculate: {error_message}")
        return jsonify({'message': 'Error', 'error_details': error_message}), 500  # 500 is the HTTP status code for internal server error

# Route to calculate the cheapest transit and Uber options
@app.route('/calculate_cheapest', methods=['POST'])
def calculate_cheapest():
    try:
        data = request.json
        start_location = data.get('start_location')
        end_location = data.get('end_location')
        logging.debug(f"start location: {start_location}")

        # Get transit data for all available options
        transit_data = get_transit_data(
            start_location['place'].replace(' ', '+'),
            end_location['place'].replace(' ', '+'),
            mode='transit'
        )

        
        cheapest_option = select_cheapest_transit_option(transit_data)

        # Booking Uber rides based on the estimated fares for the cheapest transit option
        start_to_transit_uber = book_uber_ride(select_cheapest_transit_option(
            get_transit_data(start_location['place'].replace(' ', '+'),
                             cheapest_option['legs'][0]['start_location']['lat'],
                             cheapest_option['legs'][0]['start_location']['lng'],
                             mode='driving')
        ))
        transit_to_end_uber = book_uber_ride(select_cheapest_transit_option(
            get_transit_data(cheapest_option['legs'][-1]['end_location']['lat'],
                             cheapest_option['legs'][-1]['end_location']['lng'],
                             end_location['place'].replace(' ', '+'),
                             mode='driving')
        ))

        # Returning a JSON response indicating success
        return jsonify({
            'message': 'Success',
            'cheapest_transit_data': cheapest_option,
            'start_to_transit_uber': start_to_transit_uber,
            'transit_to_end_uber': transit_to_end_uber
        })

    except Exception as e:
        error_message = str(e) if str(e) else 'An error occurred'
        logging.error(f"An error occurred in calculate_cheapest: {error_message}")
        return jsonify({'message': 'Error', 'error_details': error_message}), 500  # 500 is the HTTP status code for internal server error

# Runing the Flask app
if __name__ == '__main__':
    app.run(debug=True)
