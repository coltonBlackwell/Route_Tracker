import os
from flask import Flask, render_template, request, jsonify
import folium
import gpxpy
from datetime import datetime

app = Flask(__name__)

# Directory to store uploaded GPX files
UPLOAD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), '../gpx_files'))
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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

@app.route('/view_run/<filename>')
def view_run(filename):
    # Load the selected GPX file
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    # Ensure the file exists
    if not os.path.exists(filepath):
        return jsonify({'error': 'GPX file not found'}), 404
    
    # Parse the GPX file
    with open(filepath, 'r') as gpx_file:
        gpx = gpxpy.parse(gpx_file)

    # Extract coordinates (latitude, longitude) from GPX file
    coordinates = []
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                coordinates.append([point.latitude, point.longitude])

    if not coordinates:
        return jsonify({'error': 'No coordinates found in GPX file'}), 400

    # Return the coordinates as JSON to be plotted on the map
    return jsonify({'coordinates': coordinates}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
