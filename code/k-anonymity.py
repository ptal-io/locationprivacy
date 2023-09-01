#!/usr/bin/env python
# coding: utf-8

# # *k*-anonymity
# 
# 
# *Author: Grant McKenzie [grant.mckenzie@mcgill.ca | https://grantmckenzie.com]*
# 
# This tutorial presents an introduction to (spatial) k-anonymity, a data anonymization technique that is used to protect individuals' privacy in a dataset.  Through this tutorial we will explore both non-spatial and spatial k-anonymity.

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
import shapely as shp
import folium

# These are important for a few small tasks
import pandas as pd


# ## Data
# 
# Let's load some data. Our dataset for this tutorial is a sample of 100 points. These points are the origins of e-scooter trips in the Brussels, Belgium. We will read the CSV into a dataframe using pandas.

# In[ ]:


trip_origins = pd.read_csv('../data/Brussels_Jump100.csv')


# Take a look at the first few records in the dataset.

# In[ ]:


trip_origins.head()


# Note that this data includes columns `Gender` and `Age.` We will use these as our pseudo-sensative attributes.  Let's start by seeing how distinctive these two columns are in combination.  For instance, how many 23 year old males are in the dataset?

# In[ ]:


trip_origins.groupby(['Age','Gender']).size().reset_index(name='Count')


# It looks like there are a total of four 23 year old males in the dataset.  If you identify as a 23 year old male with a record in this dataset, then we would say this dataset has a `k = 4` for you.  On the other hand, if you identify as a 25 year old female, this view of the dataset does not preserve your privacy at all.  We can manipulate the data to increase its *k*-anonymity by grouping or "binning" the Age attribute.

# In[ ]:


# Create a new column called Age_Group and bin all ages into four groups.
trip_origins['Age_Group'] = pd.cut(trip_origins['Age'], bins=4)


# Let's see what that does for the *k*-anonymity property of the data.

# In[ ]:


trip_origins.groupby(['Age_Group','Gender']).size().reset_index(name='Count')


# Let's step back for a moment and approach this from a different perspective.  Let's set a value for *k* and then figure out if our data set meets this requirement.

# In[ ]:


k = 5

# Count number of combinations of these two columns
to_count = trip_origins.groupby(['Age_Group','Gender']).size().reset_index(name='Count')

# Does that data set meet our requirment for k?
to_count[to_count['Count'] < k]


# Since no results are returned, we can say that our data set is *5*-anonymized.

# # Individual level spatial *k*-anonymity
# 
# We will switch gears and take a look at a geospatial approach to *k*-anonymity.  In this example we imagine that our personal trip origin exists in the dataset.  Our trip is `Plate = A1091`.

# In[ ]:


me = 'A1091'


# Let's convert our Latitude and Longitude values to geometries in a GeoDataFrame.

# In[ ]:


geometry = gpd.points_from_xy(trip_origins.Longitude, trip_origins.Latitude)
trip_origins_geo = gpd.GeoDataFrame(trip_origins, geometry=geometry)
trip_origins_geo = trip_origins_geo.set_crs("EPSG:4326")  # Specify our coordinate reference system as WGS84 (lat/lng)

trip_origins_geo.head()  # Let's double check to make sure we have a geometry column


# ## Visualization
# Next we will use `folium` to view our data on a map.  We start by loading a blank map.

# In[ ]:


# set up the basemap with a Latitude, Longitude, Zoom, and Tile type.
map = folium.Map(location=[50.83, 4.37],
           zoom_start=13,
           tiles='CartoDB positron')
map


# Then we add our points by creating a list of points from our dataset.  We add them as marker in `folium` and include the attribute information in the marker popups.  We will add a conditional statement so that *our* trip origin is given a green marker.  All others will be blue.

# In[ ]:


for i, row in trip_origins_geo.iterrows():
    # Place the markers with popups
    map.add_child(
        folium.Marker(
            # The location from latitude and longitude
            location=[row.geometry.y, row.geometry.x],
            # Conditional statement to set icons (me variable is declared earlier)
            icon = folium.Icon(color="green") if row.Plate == me else folium.Icon(color="blue"),
            # Pop-up to show Plate (ID)
            popup="<b>ID</b>: " + str(trip_origins_geo.Plate[i]),
        )
    )
    i = i + 1

map


# Let's get all the details for *our* trip origin.

# In[ ]:


me_row = trip_origins_geo.loc[trip_origins_geo['Plate'] == me]


# ## What are we trying to do?
# We are trying to anonymize our specific trip origin by reporting a **set** of trip origins rather than our location alone.  The first step in doing this is to calculate the distance between each trip_origin and *our* trip origin.

# In[ ]:


# Empty list for storing all distances
distances = []

# Loop through all trip origins
for i, row in trip_origins_geo.iterrows():
    # Calculate the distance between our trip_origin and each trip_origin in our dataset.
    # Note that if we actually cared about the distances, we would project our data to a metric projection first.
    # In this case we only care about the relative distances so leaving in angular units is fine.
    # YOU WILL LIKELY GET A WARNING MESSAGE THOUGH (and rightly so)
    dist = me_row.geometry.distance(row.geometry)
    # Append the distance to the list
    distances.append(float(dist))

# Add a new column to our GeoDataFrame that contains all the distances.
trip_origins_geo['dist'] = distances

trip_origins_geo.head()


# Next, we sort our GeoDataFrame based on distance.  Remember that our trip origin will also be in this dataset so the first row should have a distance of 0.

# In[ ]:


sorted = trip_origins_geo.sort_values(by=['dist'])
sorted.head()


# Let's set our value of *k*.  If we set this to 5, that means we want to report 5 trip_origins such that we cannot be differentiated from 4 others.  Then we take the 5 nearest neighbors (which includes our trip origin).

# In[ ]:


k = 5
trip_origins_k5 = sorted.head(k)
trip_origins_k5.head()


# Let's visualize the set of trip_origins you would return if you set your spatial *k* to 5.

# In[ ]:


map = folium.Map(location=[50.83, 4.37],
           zoom_start=15,
           tiles='CartoDB positron')

for i, row in trip_origins_k5.iterrows():
    # Place the markers with popup labels
    map.add_child(
        folium.Marker(
            location=[row.geometry.y, row.geometry.x],
            icon = folium.Icon(color="green") if row.Plate == me else folium.Icon(color="blue"),
            popup="<b>ID</b>: " + str(trip_origins_geo.Plate[i]),
        )
    )
    i = i + 1

map


# Rather than returning a set of point geometries, many prefer to return a polygon that contains these points.  First let's try a `Convex Hull`.

# In[ ]:


# Build a polygon using Shapely functions
hull_polygon = trip_origins_k5.geometry.unary_union.convex_hull
folium.GeoJson(hull_polygon, style_function=lambda x: {"fillColor": "blue"}).add_to(map)
map


# A `Bounding Box` is also an option.

# In[ ]:


map = folium.Map(location=[50.83, 4.37],
           zoom_start=15,
           tiles='CartoDB positron')

for i, row in trip_origins_k5.iterrows():
    # Place the markers with popup labels
    map.add_child(
        folium.Marker(
            location=[row.geometry.y, row.geometry.x],
            icon = folium.Icon(color="green") if row.Plate == me else folium.Icon(color="blue"),
            popup="<b>ID</b>: " + str(trip_origins_geo.Plate[i]),
        )
    )
    i = i + 1
    
# BBOX
bbox_polygon = trip_origins_k5.geometry.unary_union.envelope
folium.GeoJson(bbox_polygon, style_function=lambda x: {"fillColor": "green"}).add_to(map)
map


# ## There is a major privacy issue here
# 
# From an anonymity perspective, this approach falls victim to a **center-of-anonymized spatial region attack**, where an attacker would assume, given the geometry and centroid, that the actual location of an individual is the center most trip_origin.  To avoid this, many current approaches offset the centroid of the region by taking the
# *n*<sup>th</sup>-nearest neighbor. 
# 
# Let's choose the 4<sup>th</sup> nearest neighbor as our *focal* point that will be the center of our set and any subsequent geometries.

# In[ ]:


# Get the 3rd index of our set of 5 nearest (including our trip origin)
focal = trip_origins_k5.iloc[[3]]

map = folium.Map(location=[50.83, 4.37], zoom_start=15, tiles='CartoDB positron')

for i, row in trip_origins_k5.iterrows():
    # Place the markers with popup labels
    map.add_child(
        folium.Marker(
            location=[row.geometry.y, row.geometry.x],
            icon = folium.Icon(color="green") if row.Plate == me else folium.Icon(color="blue"),
            popup="<b>ID</b>: " + str(trip_origins_geo.Plate[i]),
        )
    )
    i = i + 1

# Test visualization
map.add_child(
    folium.Marker(
        location=[focal.geometry.y, focal.geometry.x],
        # color our focal geometry red
        icon = folium.Icon(color="red"),
    )
)
map


# Then we redo all our previous analysis with this new start location.  Importantly our value of *k* needs to be greater than or equal to *n* (of our n<sup>th</sup>-nearest neighbor.)

# In[ ]:


distances = []

for i, row in trip_origins_geo.iterrows():
    dist = focal.geometry.distance(row.geometry)
    distances.append(float(dist))

trip_origins_geo['dist_focal'] = distances

sorted = trip_origins_geo.sort_values(by=['dist_focal'])

trip_origins_k5 = sorted.head(5)

map = folium.Map(location=[50.83, 4.37], zoom_start=15, tiles='CartoDB positron')

# Show markers on the map.  Our trip origin is in green.
for i, row in trip_origins_k5.iterrows():
    map.add_child(
        folium.Marker(
            location=[row.geometry.y, row.geometry.x],
            icon = folium.Icon(color="green") if row.Plate == me else folium.Icon(color="blue"),
        )
    )
    i = i + 1

# Show our Focal point on the map (red marker)
map.add_child(
    folium.Marker(
        location=[focal.geometry.y, focal.geometry.x],
        icon = folium.Icon(color="red"),
    )
)

# Show the Convex Hull
hull_polygon = trip_origins_k5.geometry.unary_union.convex_hull
folium.GeoJson(hull_polygon, style_function=lambda x: {"fillColor": "blue"}).add_to(map)

map


# # What if an attacker has some attribute information?
# 
# This is all well and good assuming everyone is just a point on the map, but what if an attacker has more identifiable information on you.  Say for example, it is known that I am *Female.*  What do we need to do to ensure that my prefered level of *k*-anonymity is preserved?

# In[ ]:


k = 5

# Reset the index 
sorted = sorted.reset_index(drop=True)

counter = 0

# Loop through the "distance" sorted GeoDataFrame containing trip_origins
for i, row in sorted.iterrows():
    
    # If the e-scooter user's gender is reported as Female, increase the counter
    if row.Gender == 'Female':
        counter = counter + 1
        
    # If the counter is equal to k, exit the loop and hold on to the index.
    if counter == k:
        break

trip_origins_k5f = sorted[0:i+1]

# Count the number of records
len(trip_origins_k5f.index)


# Wow, so in order to ensure that I cannot be identified in a dataset (from 4 others), and it is known that I am female, I need to report 16 trip_origins. Let's visualize this. We don't need to stop with Gender either... we could redo this analysis for `Age < 30`, for example.

# In[ ]:


map = folium.Map(location=[50.83, 4.37], zoom_start=14, tiles='CartoDB positron')

for i, row in trip_origins_k5f.iterrows():
    # Place the markers with popup labels
    map.add_child(
        folium.Marker(
            location=[row.geometry.y, row.geometry.x],
            icon = folium.Icon(color="green") if row.Plate == me else folium.Icon(color="blue"),
        )
    )
    i = i + 1

hull_polygon = trip_origins_k5f.geometry.unary_union.convex_hull
folium.GeoJson(hull_polygon, style_function=lambda x: {"fillColor": "blue"}).add_to(map)
map

map.add_child(
    folium.Marker(
        location=[focal.geometry.y, focal.geometry.x],
        icon = folium.Icon(color="red"),
    )
)

map


# ## The End
