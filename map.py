from flask import Flask, request, render_template
import overpy
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import folium

app = Flask(__name__)

# Initialize geolocator and Overpass API
geolocator = Nominatim(user_agent="nearest_attraction_finder")
api = overpy.Overpass()

# Function to get coordinates of a place
def get_coordinates(place_name):
    location = geolocator.geocode(place_name)
    if location:
        return (location.latitude, location.longitude)
    else:
        return None

# Route for the home page
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        place_name = request.form.get("place")
        attraction_type = request.form.get("attraction")

        # Validate input and find nearest places
        if place_name and attraction_type:
            user_location = get_coordinates(place_name)
            if user_location:
                attractions_sorted = find_nearest_places(user_location, attraction_type, radius=100000)

                # Create a map centered at the user's location
                map_object = folium.Map(location=user_location, zoom_start=12)
                folium.Marker(user_location, popup="Your Location", icon=folium.Icon(color="blue")).add_to(map_object)

                # Add attractions to the map
                for attraction in attractions_sorted:
                    folium.Marker(
                        attraction['location'],
                        popup=f"{attraction['name']} ({attraction['distance']:.2f} km away)",
                        icon=folium.Icon(color="green")
                    ).add_to(map_object)

                # Render the map as an HTML representation
                map_html = map_object._repr_html_()

                return render_template("index1.html", place_name=place_name, attraction_type=attraction_type, attractions=attractions_sorted, map_html=map_html)
            else:
                return render_template("index1.html", error="Place not found. Please check the name and try again.")
    return render_template("index1.html")

# Function to find nearest places based on user input
def find_nearest_places(user_location, attraction_type, radius=100000):
    # OSM tags for various attraction types
    attraction_types = {
        "tourist_spots": '["tourism"~"attraction|museum|monument|zoo|theme_park|viewpoint"]',
        "restaurants": '["amenity"="restaurant"]',
        "hotels": '["tourism"="hotel"]',
        "hospitals": '["amenity"="hospital"]'
    }

    if attraction_type not in attraction_types:
        return []

    # Overpass query for the given attraction type
    query = f"""
    node{attraction_types[attraction_type]}(around:{radius},{user_location[0]},{user_location[1]});
    out body;
    """
    result = api.query(query)

    # Store attractions with distances, excluding unnamed locations
    attractions = []
    for node in result.nodes:
        if "name" in node.tags:
            attraction_location = (node.lat, node.lon)
            distance = geodesic(user_location, attraction_location).km
            attractions.append({
                'name': node.tags.get("name"),
                'location': attraction_location,
                'distance': distance
            })

    # Sort attractions by distance and return the results
    attractions_sorted = sorted(attractions, key=lambda x: x['distance'])
    
    return attractions_sorted[:20]  # Return top 20 nearest attractions within 50-100 km

if __name__ == "__main__":
    app.run(debug=True)
