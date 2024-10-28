$(document).ready(function() {
    // Initialize the map once the DOM is fully loaded
    var map = L.map('map').setView([45.5236, -122.6750], 13); // Default location (centered on Portland, OR)

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 18,
    }).addTo(map);

    var polyline; // Global variable to store the polyline
    window.dots = []; // Global variable to store dot markers

    // Unified function to load and display the selected run with polyline and individual dots
    window.loadRun = function(filename) {
        $.getJSON(`/view_run/${filename}`, function(data) {
            // Clear previous layers
            if (polyline) {
                map.removeLayer(polyline);
                polyline = null;
            }
            if (window.dots) {
                window.dots.forEach(dot => map.removeLayer(dot));
            }
            window.dots = [];
    
            function getColor(speed) {
                if (speed > 80) return '#32CD32'; // High speed - Lime Green
                else if (speed > 60) return '#90EE90'; // Slightly lower high speed - Light Green
                else if (speed > 35) return '#FFD700'; // Moderate speed - Gold
                else if (speed > 15) return '#FFA500'; // Slightly lower moderate speed - Orange
                else return '#FF6347'; // Low speed - Tomato
            }
            
    
            // Array to hold latlngs for the polyline
            var latlngs = [];
    
            // Add individual dots with speed tooltips and colors
            data.coordinates.forEach(coord => {
                const color = getColor(coord.speed); // Determine color based on speed
                const dot = L.circleMarker([coord.latitude, coord.longitude], {
                    radius: 5,
                    color: color,
                    fillColor: color,
                    fillOpacity: 0.7
                }).addTo(map);
    
                // Tooltip shows speed on hover
                const tooltipText = coord.speed ? `Speed: ${coord.speed} km/h` : 'Speed unavailable';
                dot.bindTooltip(tooltipText, { permanent: false, direction: 'top' });
    
                window.dots.push(dot);
                latlngs.push([coord.latitude, coord.longitude]); // Add to latlngs array
            });
    
            // Create a polyline using the latlngs array to connect the dots
            if (latlngs.length > 0) {
                polyline = L.polyline(latlngs, { color: 'black', weight: 2 }).addTo(map);
                map.fitBounds(polyline.getBounds()); // Adjust map view to fit the polyline
            }
    
            // Display run details and elevation plot
            displayRunDetails(data);
            $('#elevation-plot').attr('src', `/elevation_plot/${filename}`);
            $('#elevationModal').modal('show');
        }).fail(function(err) {
            alert('Error loading run: ' + err.responseJSON.error);
        });
    };
    
    
    
    

    // Function to handle the file upload
    $('#upload-form').submit(function(event) {
        event.preventDefault();
        var formData = new FormData(this);

        $.ajax({
            url: '/upload_gpx',
            type: 'POST',
            data: formData,
            contentType: false,
            processData: false,
            success: function(data) {
                $('#gpx-list').append(`
                    <li>
                        <a href="#" onclick="loadRun('${data.filename}')">${data.filename}</a>
                        <button onclick="deleteRun('${data.filename}')">Delete</button>
                    </li>
                `);
            },
            error: function(err) {
                alert('Error uploading file: ' + (err.responseJSON ? err.responseJSON.error : err.statusText));
            }
        });
    });

    // Function to delete the selected run
    window.deleteRun = function(filename) {
        if (confirm(`Are you sure you want to delete the run: ${filename}?`)) {
            $.ajax({
                url: `/delete_run/${filename}`,
                type: 'DELETE',
                success: function(response) {
                    alert(response.message);
                    $(`#gpx-list li:contains('${filename}')`).remove();
                },
                error: function(err) {
                    alert('Error deleting run: ' + (err.responseJSON ? err.responseJSON.error : err.statusText));
                }
            });
        }
    };

    // Function to display run details
    function displayRunDetails(data) {
        const detailsContainer = $('#run-details');
        detailsContainer.empty(); // Clear previous details

        const startPoint = data.start_point ? `Start: ${data.start_point[0]}, ${data.start_point[1]}` : 'No start point';
        const endPoint = data.end_point ? `End: ${data.end_point[0]}, ${data.end_point[1]}` : 'No end point';
        const duration = `Duration: ${data.duration} Minutes`;
        const distance = `Distance: ${data.distance} Kilometers`; // Adjust as needed

        detailsContainer.append(`
            <h3>Run Details</h3>
            <p>${startPoint}</p>
            <p>${endPoint}</p>
            <p>${duration}</p>
            <p>${distance}</p>
        `);
    }

    // Toggle details container
    $('#toggle-details').click(function() {
        $('#details-container').toggle();
        const buttonText = $('#details-container').is(':visible') ? 'Hide Details' : 'Show Details';
        $(this).text(buttonText);
    });

    // Toggle elevation plot container
    $('#toggle-elevation').click(function() {
        $('#elevation-plot-container').toggle();
        const buttonText = $('#elevation-plot-container').is(':visible') ? 'Hide Elevation Plot' : 'Show Elevation Plot';
        $(this).text(buttonText);
    });
});
