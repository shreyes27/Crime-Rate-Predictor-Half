from flask import Flask, request, render_template 
import pickle 
import math
import os
import requests
from markdown import markdown
import folium
from folium.plugins import HeatMap
import random


city_coordinates = {
    '0': [23.0225, 72.5714],   # Ahmedabad
    '1': [12.9716, 77.5946],   # Bengaluru
    '2': [13.0827, 80.2707],   # Chennai
    '3': [11.0168, 76.9558],   # Coimbatore
    '4': [28.7041, 77.1025],   # Delhi
    '5': [28.6692, 77.4538],   # Ghaziabad
    '6': [17.3850, 78.4867],   # Hyderabad
    '7': [22.7196, 75.8577],   # Indore
    '8': [26.9124, 75.7873],   # Jaipur
    '9': [26.4499, 80.3319],   # Kanpur
    '10': [9.9312, 76.2673],   # Kochi
    '11': [22.5726, 88.3639],  # Kolkata
    '12': [11.2588, 75.7804],  # Kozhikode
    '13': [26.8467, 80.9462],  # Lucknow
    '14': [19.0760, 72.8777],  # Mumbai
    '15': [21.1458, 79.0882],  # Nagpur
    '16': [25.5941, 85.1376],  # Patna
    '17': [18.5204, 73.8567],  # Pune
    '18': [21.1702, 72.8311],  # Surat
}

 
model = pickle.load (open ('Model/crime.pkl', 'rb'))
 
app = Flask (__name__)


def generate_random_points(center, count=10, spread=0.02):
    """
    center = [lat, lon]
    spread = max distance for variation
    """
    lat, lon = center
    points = []

    for _ in range(count):
        rnd_lat = lat + random.uniform(-spread, spread)
        rnd_lon = lon + random.uniform(-spread, spread)
        points.append([rnd_lat, rnd_lon])

    return points


def generate_heatmap(city_code, intensity):
    center = city_coordinates[city_code]

    # Generate 10 random points around the city
    random_points = generate_random_points(center, count=10, spread=0.03)

    # Add intensity for each point
    heat_data = [[lat, lon, intensity] for lat, lon in random_points]

    # Create Map
    m = folium.Map(location=center, zoom_start=11)

    # Add Heatmap layer
    HeatMap(heat_data, radius=25).add_to(m)

    filepath = "static/heatmap.html"
    m.save(filepath)
    return filepath

def get_crime_insights(city, crime_type, year):
    try:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": "Bearer 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",

            "Content-Type": "application/json"
        }
        data = {
            "model": "amazon/nova-2-lite-v1:free",   # You can change model here
            "messages": [
                {
                    "role": "system",
                    "content": "You are an AI assistant specializing in crime analysis."
                },
                {
                    "role": "user",
                    "content": (
                        f"City: {city}\n"
                        f"Crime Type: {crime_type}\n"
                        f"Year: {year}\n\n"
                        "Please explain the most common causes of this crime in this city "
                        "and list practical steps to prevent it. Keep the answer short and clear."
                    )
                }
            ]
        }

        response = requests.post(url, headers=headers, json=data)
        result = response.json()

        # Extract message
        return result["choices"][0]["message"]["content"]

    except Exception as e:
        return f"Error generating insights: {str(e)}"

 
@app.route ('/') 
def index (): 
    return render_template ("index.html") 
 
 
@app.route ('/predict', methods =['POST']) 
def predict_result (): 
    
    city_names = { '0': 'Ahmedabad', '1': 'Bengaluru', '2': 'Chennai', '3': 'Coimbatore', '4': 'Delhi', '5': 'Ghaziabad', '6': 'Hyderabad', '7': 'Indore', '8': 'Jaipur', '9': 'Kanpur', '10': 'Kochi', '11': 'Kolkata', '12': 'Kozhikode', '13': 'Lucknow', '14': 'Mumbai', '15': 'Nagpur', '16': 'Patna', '17': 'Pune', '18':'Surat'}
    
    crimes_names = { '0': 'Crime Committed by Juveniles', '1': 'Crime against SC', '2': 'Crime against ST', '3': 'Crime against Senior Citizen', '4': 'Crime against children', '5': 'Crime against women', '6': 'Cyber Crimes', '7': 'Economic Offences', '8': 'Kidnapping', '9':'Murder'}
    
    population = { '0': 63.50, '1': 85.00, '2': 87.00, '3': 21.50, '4': 163.10, '5': 23.60, '6': 77.50, '7': 21.70, '8': 30.70, '9': 29.20, '10': 21.20, '11': 141.10, '12': 20.30, '13': 29.00, '14': 184.10, '15': 25.00, '16': 20.50, '17': 50.50, '18':45.80}
    
    city_code = request.form["city"] 
    crime_code = request.form['crime'] 
    year = request.form['year'] 
    pop = population[city_code] 

    # Here increasing / decreasing the population as per the year.
    # Assuming that the population growth rate is 1% per year.
    year_diff = int(year) - 2011;
    pop = pop + 0.01*year_diff*pop

    
    crime_rate = model.predict ([[year, city_code, pop, crime_code]])[0] 
    
    city_name = city_names[city_code] 
    
    crime_type =  crimes_names[crime_code] 
    
    if crime_rate <= 1:
        crime_status = "Very Low Crime Area" 
    elif crime_rate <= 5:
        crime_status = "Low Crime Area"
    elif crime_rate <= 15:
        crime_status = "High Crime Area"
    else:
        crime_status = "Very High Crime Area" 
    
    cases = math.ceil(crime_rate * pop)
    heatmap_path = generate_heatmap(city_code, crime_rate)

    raw_ai = get_crime_insights(city_name, crime_type, year)
    ai_insights = markdown(raw_ai)

    return render_template('result.html', city_name=city_name, crime_type=crime_type, year=year, crime_status=crime_status, crime_rate=crime_rate, cases=cases, population=pop, ai_insights=ai_insights, heatmap=heatmap_path)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)


