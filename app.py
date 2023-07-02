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
    free_text_table = st.dataframe(data=table_df)
    
    # Print the folium map
    map = folium.Map(location=[df.iloc[0]['latitude'], df.iloc[0]['longitude']], zoom_start=12)
    
    # Add the markers to the map
    for index, row in df.iterrows():
        folium.Marker([row['latitude'], row['longitude']], popup=f"{row['_source.business_name']} <br> ID= {row['_source.business_id']}").add_to(map)
    
    folium_static(map)


"""search for postal code"""
############################################
# Add the input field for postal code
postal_code = st.sidebar.text_input("Postal Code")

# Add the link to the map below the code
link = "[All San Fransisco Zip Codes](https://www.usmapguide.com/california/san-francisco-zip-code-map/)"
st.sidebar.markdown("### " + link, unsafe_allow_html=False)

# Add a separator
my_separator = "---"
st.sidebar.markdown(my_separator, unsafe_allow_html=False)

# search for postal code
if postal_code:
    query_body = {
        "query": {
            "match": {
                "_source.zip": postal_code
            }
        }
    }
    
    # Search the index. 1k is enough to get all the results. The problem is that it wants to return all the results.
    # There is no groupby query for strings in elasticsearch.
    res = es.search(index="my_app_scans", body=query_body, size=1000)
    
    # obtain results and put them in a dataframe
    df = pd.json_normalize(res["hits"]["hits"])
    
    # Drop duplicates
    df = df.drop_duplicates(subset=["_source.business_id"])
    
    # rename latitude and longitude columns so they have the correct names for the map function
    df = df.rename(columns={"_source.latitude": "latitude", "_source.longitude": "longitude"})
    df = df.filter(items = ["_source.business_id", "_source.business_name", "_source.business_address", "_source.city", "_source.zip", "latitude", "longitude"], axis=1)
    
    # Add table with  a headline
    st.subheader("Businesses in postal code: " + postal_code)
    
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
    
    """Search by Business ID"""
    ############################################
    # Add the input field on the sidebar
    business_id = st.sidebar.text_input("Business ID")
    
    if business_id:
        # build the search query for Elasticsearch
        query_body = {
            "query": {
                "match": {
                    "_source.business_id": business_id
                }
            }
        }
            
        # Search the index
        res = es.search(index="my_app_scans", body=query_body, size=1000)
        
        # obtain results and put them in a dataframe
        df = pd.json_normalize(res["hits"]["hits"])
        
        table_df = df.filter(items = ["_source.business_id", "_source.business_name", "_source.business_address", "_source.zip"], axis=1)
        
        # turn the epochs into timestamps
        table_df['_source.user_birth_date'] = table_df['_source.user_birth_date'].apply(lambda x: datetime.fromtimestamp(x/1000000).strftime('%Y-%m-%d'))
        table_df['_source.scan_timestamp'] = table_df['_source.scan_timestamp'].apply(lambda x: datetime.fromtimestamp(x/1000000).strftime('%Y-%m-%d %H:%M:%S'))
        
        # sort values by timestamp
        table_df = table_df.sort_values(by=['_source.scan_timestamp'], ascending=False)
        
        # fix names before rendering the table
        table_df = table_df.rename(columns={"_source.deviceID": "Device ID", "_source.user_name": "User Name", "_source.user_birth_date": "Birth Date", "_source.scan_timestamp": "Scan Timestamp"})
        
        # Add table with  a headline
        st.subheader("Users scanned at this business: " + business_id)
        
        # Print the table
        business_id_table = st.dataframe(data=table_df)
        
        """Search by Device ID"""
        ############################################
        device_id = st.sidebar.text_input("Device ID")
        
        if device_id:
            query_body = {
                "query": {
                    "match": {
                        "_source.deviceID": device_id
                    }
                }
            }
            
            res = es.search(index="my_app_scans", body=query_body, size=1000)