from flask import Flask
from app.config import google_maps_api_key

app = Flask(__name__)
app.config.from_object('app.config')  # Corrected import path

# Add any necessary extensions or configuration here
