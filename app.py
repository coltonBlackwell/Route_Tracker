from flask import Flask, render_template, request, jsonify, send_file
import os
import xml.etree.ElementTree as ET
import gpxpy
from datetime import datetime
from math import radians, sin, cos, sqrt, atan2
from matplotlib.figure import Figure
import io

app = Flask(__name__)

# Directory to store uploaded GPX files
UPLOAD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), '../gpx_files'))
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def haversine(coord1, coord2):
    """Calculate the Haversine distance between two latitude/longitude points."""
    R = 6371.0  # Earth radius in kilometers
    lat1, lon1 = radians(coord1[0]), radians(coord1[1])
    lat2, lon2 = radians(coord2[0]), radians(coord2[1])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c  # returns distance in kilometers

def calculate_distance(gpx_data):
    """Calculate the total distance from the GPX data."""
    coordinates = []

    # Extracting coordinates from the GPX data
    for track in gpx_data.tracks:
        for segment in track.segments:
            for point in segment.points:
                coordinates.append((point.latitude, point.longitude))
    
    # Calculate the total distance
    total_distance = 0.0
    for i in range(1, len(coordinates)):
        total_distance += haversine(coordinates[i - 1], coordinates[i])

    return round(total_distance, 2)  # Returns total distance in kilometers

@app.route('/')
def index():
    # Get the list of saved GPX files
    gpx_files = os.listdir(app.config['UPLOAD_FOLDER'])
    
    # Render the page with a placeholder for the map and controls
    return render_template('index.html', gpx_files=gpx_files)

@app.route('/upload_gpx', methods=['POST'])
def upload_gpx():
    # Handle file upload
    if 'gpx_file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    gpx_file = request.files['gpx_file']
    
    # Sanitize the new filename or use timestamp
    new_filename = request.form.get('new_filename', None)
    if new_filename:
        new_filename = new_filename.strip().replace(" ", "_") + '.gpx'
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_filename = f"{timestamp}_{gpx_file.filename}"

    # Save the GPX file
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
    gpx_file.save(filepath)
    
    return jsonify({'filename': new_filename}), 200

@app.route('/delete_run/<filename>', methods=['DELETE'])
def delete_run(filename):
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        os.remove(file_path)  # Delete the file
        return jsonify({'message': 'Run deleted successfully!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
from datetime import datetime

@app.route('/view_run/<filename>')
def view_run(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    if not os.path.exists(filepath):
        return jsonify({'error': 'GPX file not found'}), 404
    
    with open(filepath, 'r') as gpx_file:
        gpx = gpxpy.parse(gpx_file)

    coordinates = []
    previous_point = None
    
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                if previous_point:
                    # Calculate the time difference in seconds
                    time_diff = (point.time - previous_point.time).total_seconds() if point.time and previous_point.time else 0
                    if time_diff > 0:
                        # Calculate distance and speed in km/h
                        distance_km = haversine((previous_point.latitude, previous_point.longitude), (point.latitude, point.longitude))
                        speed_kmh = (distance_km / (time_diff / 3600))  # km/h
                    else:
                        speed_kmh = None  # No speed if no time difference
                else:
                    speed_kmh = None  # No speed for the first point

                # Store latitude, longitude, and calculated speed
                coordinates.append({
                    'latitude': point.latitude,
                    'longitude': point.longitude,
                    'speed': round(speed_kmh, 2) if speed_kmh is not None else None
                })
                previous_point = point

    if not coordinates:
        return jsonify({'error': 'No coordinates found in GPX file'}), 400

    start_point = coordinates[0] if coordinates else None
    end_point = coordinates[-1] if coordinates else None
    duration_seconds = gpx.get_duration()
    duration_minutes = round(duration_seconds / 60, 2) if duration_seconds else None
    distance = calculate_distance(gpx)

    return jsonify({
        'coordinates': coordinates,
        'start_point': [start_point['latitude'], start_point['longitude']] if start_point else None,
        'end_point': [end_point['latitude'], end_point['longitude']] if end_point else None,
        'duration': duration_minutes,
        'distance': distance,
    }), 200



@app.route('/elevation_plot/<filename>')
def elevation_plot(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    if not os.path.exists(filepath):
        return jsonify({'error': 'GPX file not found'}), 404

    # Parse GPX file for elevation and time data
    with open(filepath, 'r') as gpx_file:
        gpx = gpxpy.parse(gpx_file)
    
    times = []
    elevations = []

    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                times.append(datetime.fromisoformat(point.time.isoformat()))
                elevations.append(point.elevation)
    
    # Plot elevation over time
    fig = Figure()
    ax = fig.subplots()
    ax.plot(times, elevations, label="Elevation (m)", color="blue")
    ax.set_title("Elevation Over Time")
    ax.set_xlabel("Time")
    ax.set_ylabel("Elevation (m)")
    ax.legend()

    # Save the plot to a BytesIO object and serve as a response
    img_bytes = io.BytesIO()
    fig.savefig(img_bytes, format='png')
    img_bytes.seek(0)

    return send_file(img_bytes, mimetype='image/png')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
