$(document).ready(function() {
    // Initialize the map once the DOM is fully loaded
    var map = L.map('map').setView([45.5236, -122.6750], 13); // Default location (centered on Portland, OR)

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 18,
    }).addTo(map);

    var polyline; // Global variable to store the polyline

    // Function to load and display the selected run
    window.loadRun = function(filename) {
        $.getJSON(`/view_run/${filename}`, function(data) {
            if (polyline) {
                map.removeLayer(polyline); // Remove previous polyline if it exists
            }
            var latlngs = data.coordinates.map(coord => [coord[0], coord[1]]);
            polyline = L.polyline(latlngs, {color: 'blue'}).addTo(map);
            map.fitBounds(polyline.getBounds()); // Adjust map view to fit the run

            // Display run details
            displayRunDetails(data);
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
                alert('Error uploading file: ' + err.responseJSON.error);
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
                    // Remove the run from the list in the UI
                    $(`#gpx-list li:contains('${filename}')`).remove();
                },
                error: function(err) {
                    alert('Error deleting run: ' + err.responseJSON.error);
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
        const duration = `Duration: ${data.duration} seconds`;
        const distance = `Distance: ${data.distance} meters`; // Adjust as needed

        detailsContainer.append(`
            <h3>Run Details</h3>
            <p>${startPoint}</p>
            <p>${endPoint}</p>
            <p>${duration}</p>
            <p>${distance}</p>
        `);
    }
});
