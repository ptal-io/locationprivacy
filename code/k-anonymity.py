
import anonypy
import pandas as pd
import geopandas as gpd
import folium


df = pd.read_csv('/home/grantmckenzie/Dropbox/LISER_GeoPrivacy_Workshop/Brussels_Jump100.csv')
df.head()
df.groupby(['Age','Gender']).size().reset_index(name='Count')

df['Age_Group'] = pd.cut(df['Age'], bins=4)

df.groupby(['Age_Group','Gender']).size().reset_index(name='Count')


k = 2

df_count = df.groupby(['Age_Group','Gender']).size().reset_index(name='Count')

df_count[df_count['Count'] < k]




me = 'A1091'

trip_origins = pd.read_csv('/home/grantmckenzie/Dropbox/LISER_GeoPrivacy_Workshop/Brussels_Jump100.csv')
geometry = gpd.points_from_xy(trip_origins.Longitude, trip_origins.Latitude)
trip_origins_geo = gpd.GeoDataFrame(trip_origins, geometry=geometry)
trip_origins_geo = trip_origins_geo.set_crs("EPSG:4326")  # Specify our coordinate reference system as WGS84 (lat/lng)
trip_origins_geo.head()


import folium

map = folium.Map(location=[50.83, 4.37],
           zoom_start=13,
           tiles='CartoDB positron')

for i, row in trip_origins_geo.iterrows():
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

import shapely as shp

me_row = trip_origins_geo.loc[trip_origins_geo['Plate'] == me]

me_row_m = me_row.copy()
me_row_m.geometry = me_row.geometry.to_crs(epsg=3857)

trip_origins_geo_m = trip_origins_geo.copy()
trip_origins_geo_m.geometry = trip_origins_geo.geometry.to_crs(epsg=3857)

distances = []

for i, row in trip_origins_geo_m.iterrows():
    dist = me_row_m.geometry.distance(row.geometry)
    distances.append(float(dist))

trip_origins_geo_m['dist'] = distances


sorted = trip_origins_geo.sort_values(by=['dist'])

k = 5

g = sorted.head(k)

map = folium.Map(location=[50.83, 4.37],
           zoom_start=15,
           tiles='CartoDB positron')

for i, row in g.iterrows():
    # Place the markers with popup labels
    map.add_child(
        folium.Marker(
            location=[row.geometry.y, row.geometry.x],
            icon = folium.Icon(color="green") if row.Plate == me else folium.Icon(color="blue"),
            popup="<b>ID</b>: " + str(trip_origins_geo.Plate[i]),
        )
    )
    i = i + 1



# CONVEX HULL

a = g.geometry.unary_union.convex_hull
folium.GeoJson(a, style_function=lambda x: {"fillColor": "blue"}).add_to(map)



# BBOX
a = g.geometry.unary_union.envelope
folium.GeoJson(a, style_function=lambda x: {"fillColor": "green"}).add_to(map)

# circle
#sorted = trip_origins_geo_m.sort_values(by=['dist'])
#g_m = sorted.head(k)

#maxdist = g_m['dist'].max()
#a = me_row_m.geometry.buffer(maxdist)
#b = gpd.GeoSeries(b.geometry).to_crs(epsg=4326)
#folium.GeoJson(b, style_function=lambda x: {"fillColor": "red"}).add_to(map)
map



# CENTER OF REGION ATTACK

focal = g.iloc[[3]]
map.add_child(
    folium.Marker(
        location=[focal.geometry.y, focal.geometry.x],
        icon = folium.Icon(color="red"),
    )
)


distances = []

for i, row in trip_origins_geo.iterrows():
    dist = focal.geometry.distance(row.geometry)
    distances.append(float(dist))

trip_origins_geo['dist_focal'] = distances


sorted = trip_origins_geo.sort_values(by=['dist_focal'])

g = sorted.head(5)


map = folium.Map(location=[50.83, 4.37],
           zoom_start=15,
           tiles='CartoDB positron')

for i, row in g.iterrows():
    # Place the markers with popup labels
    map.add_child(
        folium.Marker(
            location=[row.geometry.y, row.geometry.x],
            icon = folium.Icon(color="green") if row.Plate == me else folium.Icon(color="blue"),
            popup="<b>ID</b>: " + str(trip_origins_geo.Plate[i]),
        )
    )
    i = i + 1

a = g.geometry.unary_union.convex_hull
folium.GeoJson(a, style_function=lambda x: {"fillColor": "blue"}).add_to(map)
map



### KNOW SOMETHING ELSE

We know you are female or under 30

me_row

g

k = 5

temp = sorted

temp = temp.reset_index(drop=True)

counter = 0
for i, row in temp.iterrows():
    if row.Gender == 'Female':
        counter = counter + 1
    if counter == k:
        break

gg = temp[0:i+1]


map = folium.Map(location=[50.83, 4.37],
           zoom_start=14,
           tiles='CartoDB positron')

for i, row in gg.iterrows():
    # Place the markers with popup labels
    map.add_child(
        folium.Marker(
            location=[row.geometry.y, row.geometry.x],
            icon = folium.Icon(color="green") if row.Plate == me else folium.Icon(color="blue"),
            popup="<b>ID</b>: " + str(trip_origins_geo.Plate[i]),
        )
    )
    i = i + 1

a = gg.geometry.unary_union.convex_hull
folium.GeoJson(a, style_function=lambda x: {"fillColor": "blue"}).add_to(map)
map

map.add_child(
    folium.Marker(
        location=[focal.geometry.y, focal.geometry.x],
        icon = folium.Icon(color="red"),
    )
)