import streamlit as st
import pandas as pd 
from elasticsearch import Elasticsearch
from streamlit_folium import folium_static
import folium
from datetime import datetime

# Connect to 
es = Elasticsearch("http://localhost:9200")

# Ensure the entire page is loaded
st.set_page_config(layout="wide")

# Add title to sidebar
st.sidebar.title("San Francisco business App Scan Tracker")


"""Search by free text"""
############################################
text = st.sidebar.text_input("Free text search")

# add the link to the map below the code
st.sidebar.markdown("### [Map](https://www.google.com/maps/search/?api=1&query=37.76,-122.4)")


if text:
    query_body = {
        "query": {
            "simple_query_string": {
                "query": text
            }
        }
    }
    
    # Search the index. We are using the index called "my_app_scans"
    res = es.search(index="my_app_scans", body=query_body, size=1000)
    
    # obtain results and put them in a dataframe
    df = pd.json_normalize(res["hits"]["hits"])
    
    # Drop duplicates
    df = df.drop_duplicates(subset=["_source.business_id"])
    
    # rename latitude and longitude columns so they have the correct names for the map function
    df = df.rename(columns={"_source.latitude": "latitude", "_source.longitude": "longitude"})
    df = df.filter(items = ["_source.business_id", "_source.business_name", "_source.business_address", "_source.city", "_source.zip", "latitude", "longitude"], axis=1)
    
    # Add table with  a headline
    st.subheader("Businesses for search term: " + text)
    
    # Show data as table
    table_df = df.filter(items = ["_source.business_id", "_source.business_name", "_source.business_address", "_source.zip"], axis=1)
    # rename columns before rendering the table
    table_df = table_df.rename(columns={"_source.business_id": "Business ID", "_source.business_name": "Business Name", "_source.business_address": "Business Address", "_source.zip": "Postal Code"})
    
    # Print the table
    postal_code_table = st.dataframe(data=table_df)
    
    # Print the folium map
    map = folium.Map(location=[df.iloc[0]['latitude'], df.iloc[0]['longitude']], zoom_start=12)
    
    # Add the markers to the map
    for index, row in df.iterrows():
        folium.Marker([row['latitude'], row['longitude']], popup=f"{row['_source.business_name']} <br> ID= {row['_source.business_id']}").add_to(map)
    
    folium_static(map)


"""search for postal code"""
############################################