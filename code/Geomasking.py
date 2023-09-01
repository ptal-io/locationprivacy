#!/usr/bin/env python
# coding: utf-8

# # Geomasking
# 
# *Author: Grant McKenzie [grant.mckenzie@mcgill.ca | https://grantmckenzie.com]*
# 
# This tutorial presents an introduction to geomasking, an obfuscation technique used for preserving the privacy of geographic data.  Through this tutorial we will explore two forms of geomasking, one using point geometries and the other using buffers.

# ## Modules
# 
# First, we require a number of python modules in order to run this tutorial.  We will use `GeoPandas` for handling all of our geospatial objects, `Shapely` for our geometries, and `Folium` for interactive geovisualization.

# In[ ]:


# These will do the heavy lifting
# Make sure to install the modules if they don't already exist
import sys
get_ipython().system('{sys.executable} -m pip install geopandas')
get_ipython().system('{sys.executable} -m pip install shapely')
get_ipython().system('{sys.executable} -m pip install folium')

import geopandas as gpd
from shapely import Point
import folium

# These are important for a few small tasks
import pandas as pd
from datetime import datetime
import math
import random


# ## Data
# Let's load some data.  Our dataset for this tutorial is a sample of 10 points.  These points are the origins of e-scooter trips in the Brussels, Belgium.  We will read the CSV into a dataframe using `pandas`.

# In[ ]:


trip_origins = pd.read_csv("../data/Brussels_Jump10.csv")


# Take a look at the first few records in the dataset.

# In[ ]:


trip_origins.head()


# The current data is not 'spatial,' so lets convert to a GeoDataFrame by converting our latitude and longitude columns to a geometry using `GeoPandas`.

# In[ ]:


geometry = gpd.points_from_xy(trip_origins.Longitude, trip_origins.Latitude)
trip_origins_geo = gpd.GeoDataFrame(trip_origins, geometry=geometry)
trip_origins_geo = trip_origins_geo.set_crs("EPSG:4326")  # Specify our coordinate reference system as WGS84 (lat/lng)

trip_origins_geo.head()    # Look at the first few rows.


# ## Visualization
# Next we will use `folium` to view our data on a map.  We start by loading a blank map.

# In[ ]:


# set up the basemap with a Latitude, Longitude, Zoom, and Tile type.
map = folium.Map(location=[50.84, 4.39],
           zoom_start=13,
           tiles='CartoDB positron')
map


# Then we add our points by creating a list of points from our dataset.  We add them as marker in `folium` and include the attribute information in the marker popups.

# In[ ]:


trip_geom_list = [[point.xy[1][0], point.xy[0][0]] for point in trip_origins_geo.geometry]

# Iterate through list and add a marker for each trip origin
i = 0

for coordinates in trip_geom_list:
    # Place the markers with popup labels
    map.add_child(
        folium.Marker(
            location=coordinates,
            popup="<b>ID</b>: "
            + str(trip_origins_geo.Plate[i])  # Get the license plate column as the ID
            + "<br>"
            + "<b>Start Time:</b><br/>"
            + str(datetime.fromtimestamp(trip_origins_geo.Timestamp[i]))   # Convert the timestamp to something readable
            + "<br>"
            + "<b>Distance (m):</b><br/>"
            + str(trip_origins_geo.Distance[i])
            + "<br>"
            + "<b>Duration (s):</b><br/>"
            + str(trip_origins_geo.Duration[i]),
            icon=folium.Icon(color="green")   # Make the Icon green
        )
    )
    i = i + 1

map


# ## Basic Buffer
# One very basic approach to geomasking a point geometry is to simply create a buffer around the point and return the buffer geometry to the user instead of the exact location.

# In[ ]:


# Specify our Buffer radius in meters
buffer = 500

# Copy our original trip origins dataset 
trip_origins_geo_m = trip_origins_geo.copy()

# Project the geometry from WGS84 (units: degrees) to Spherical Mercator (units: meters)
# Note: Spherical Mercator is not a great option here as it is a global projection and assumes the earth is a Sphere.  
# For demo purposes this work work though.  In practice, make sure to choice a region-specific CRS.
trip_origins_geo_m.geometry = trip_origins_geo_m.geometry.to_crs(epsg=3857)

# Buffer our geometry by the specified buffer amount and update our geometry
trip_origins_geo_m.geometry = trip_origins_geo_m.geometry.buffer(buffer)

# Reproject our data back to WGS84 (units: degrees) as that is what folium expects.
trip_origins_geo_m.geometry = trip_origins_geo_m.geometry.to_crs(epsg=4326)

# Loop through each row (object) in our data
for i, row in trip_origins_geo_m.iterrows():
    
    # Create a geoseries and convert to JSON (this is what folium expects)
    geo_j = gpd.GeoSeries(row.geometry).to_json()
    
    # Massage our json object into a GeoJSON object that folium needs and set style
    folium_j = folium.GeoJson(data=geo_j, style_function=lambda x: {"fillColor": "green"})
    
    # Add the object to the map
    folium_j.add_to(map)
    
# View the map
map


# ## What is wrong with this?
# While we did create buffers around our points, it is still quite easy to identify the exact origin location since we know that the circle geometries were generated using a radius from the center point.  Any *attacker* could simply identify the actual locations as the center of each circle.  Let's take care of this.
# 
# Our first approach will be to generate random point geometries within a specific distance of our actual locations.  We will then replace our known locations with these random locations when sharing our data.  The assumption here is that the random points will be at a distance from the original point that preserves our privacy, but not so much that it makes the data completely useless.  There is a trade off.
# 
# We will start by writing a function that generates a random point given an existing point and a maximum radius.

# In[ ]:


# This function expects a Shapely Point geometry and Buffer radius as input.
def randPoint(pt, buff):
    
    # Determine radius as the buffer multiplied by a random decimal value between 0 and 1
    r = buff * random.random()
    
    # Generate a random angle (in radians)
    theta = math.degrees(random.random() * 2 * math.pi)
    
    # The random longitude and latitude can then be calculated
    long_rand = pt.x + r * math.cos(theta)
    lat_rand = pt.y + r * math.sin(theta)
    
    # Return the random Point geometry
    return Point(long_rand, lat_rand)


# Next, we will loop through our known trip origins and generate a new point using our function.

# In[ ]:


# copy our original points to a new GeoDataFrame and reproject to Spherical Mercator (units: meters)
trip_origins_geo_m = trip_origins_geo.copy()
trip_origins_geo_m.geometry = trip_origins_geo_m.geometry.to_crs(epsg=3857)

# Loop through each point
for i, row in trip_origins_geo_m.iterrows():
    
    # Generate a random point given the geometry of our original point and our buffer (meters)
    randpt = randPoint(gpd.GeoSeries(row.geometry), buffer)
    
    # Create a geodataframe from that new geometry and reproject back to WGS84 (units: degrees)
    randgpd = gpd.GeoDataFrame(geometry=[randpt], crs="EPSG:3857").to_crs(epsg=4326)

    # Get the geometry as JSON
    geo_j = randgpd.geometry.to_json()
    
    # Massage our json object into a GeoJSON object that folium needs
    folium_j = folium.GeoJson(data=geo_j)
    
    # Add the object to the map
    folium_j.add_to(map)

#View Map
map



# The map above (after running the code in the cell) shows our original point geometries (trip origins), our buffers, and our new randomized points that are guranteed to be a maximum of *buffer distance* away from the actual trip origin.
# 
# While this is good, we can make it even more private, by setting a minimum distance from the actual location as well.  This ensures that the randomized location is never the same as the actual location.  To do this create a new minimum radius variable, e.g. `minrad = 10` and then change the `randomPoint` function slightly.  First add a third input parameter for the minimum radius, then change the line:
# 
# `r = buff * random.random()`
# 
# to
# 
# `r = (buff-minbuff) * random.random() + minbuff`

# ## Randomized Buffers
# 
# Our last step in this geomasking example is to generate randomized buffers instead of randomized points.  While arguably not more private than the points, it is a more *truthful* representation of the data location as the actual trip origin is guaranteed to exist within the circle geometry.  
# 
# We will start with a blank map again.

# In[ ]:


map = folium.Map(location=[50.84, 4.39],
           zoom_start=13,
           tiles='CartoDB positron')

map


# Then we will add our original trip origin point geometries.

# In[ ]:


for i, row in trip_origins_geo.iterrows():
    geo_j = gpd.GeoSeries(row.geometry).to_json()
    folium_j = folium.GeoJson(data=geo_j)
    folium_j.add_to(map)

map


# Next we generate random points around the known points, and buffer those to generate circle polygons around the randomized centers.  If you get an error after running those code, it is likely that you need to add a third `minbuff` parameter when calling your function.

# In[ ]:


# Make a copy of our original data and reproject to Spherical Mercator (units: meters)
trip_origins_geo_m = trip_origins_geo.copy()
trip_origins_geo_m.geometry = trip_origins_geo_m.geometry.to_crs(epsg=3857)

# Loop through all points (rows in our GeoDataFrame)
for i, row in trip_origins_geo_m.iterrows():

    # Generate a random point
    randgeom = randPoint(gpd.GeoSeries(row.geometry), buffer)
    
    # Generate a GeoDataFrame with that random point geometry
    randgpd = gpd.GeoDataFrame(geometry=[randgeom], crs="EPSG:3857")
    
    # Buffer the random point by the buffer radius and assign to geometry property.
    randgpd.geometry = randgpd.geometry.buffer(buffer)
    
    # Reproject back to WGS84 (units: degrees)
    randgpd = randgpd.to_crs(epsg=4326)
    
    # to JSON
    geo_j = randgpd.geometry.to_json()
    
    # to Folium GeoJSON
    foliumgeom = folium.GeoJson(data=geo_j, style_function=lambda x: {"fillColor": "red"})
    
    # Add to map
    foliumgeom.add_to(map)

# View Map
map


# The map shown above (after running the code in the cell) shows the original point geometries as blue markers and the random circle regions.  Note that the circle regions always contain the original markers which is important for maintaining a useful dataset.  

# ## The End
