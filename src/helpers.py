# import re
# from turtle import window_height
import streamlit as st
import pandas as pd
from elasticsearch import Elasticsearch
from streamlit_folium import folium_static
import folium
from datetime import datetime

# Connect to Elasticsearch
es = Elasticsearch("http://localhost:9200")


@st.cache_data
def query_data(query_body):
    # Search the index. We are using the index called "my_app_scans"
    res = es.search(index="my_app_scans", body=query_body, size=1000)

    # obtain results and put them in a dataframe and drop duplicates
    df = pd.json_normalize(res["hits"]["hits"])
    df = df.drop_duplicates(subset=["_source.business_id"])
    return df

@st.cache_data
def common_data_process(df):
    # rename latitude and longitude columns so they have the correct names for the map function
    df = df.rename(columns={"_source.latitude": "latitude",
                   "_source.longitude": "longitude"})
    df = df.filter(items=["_source.business_id", "_source.business_name",
                   "_source.business_address", "_source.city", "_source.zip", "latitude", "longitude"], axis=1)

    # Show data as table
    table_df = df.filter(items=["_source.business_id", "_source.business_name",
                         "_source.business_address", "_source.zip"], axis=1)
    # rename columns before rendering the table
    table_df = table_df.rename(columns={"_source.business_id": "Business ID", "_source.business_name": "Business Name",
                               "_source.business_address": "Business Address", "_source.zip": "Postal Code"})
    print(table_df.dtypes)
    return df, table_df
    

@st.cache_data
def epoch_to_timestamp(df):
    # turn the epochs into timestamps
    df['_source.user_birth_date'] = df['_source.user_birth_date'].apply(
        lambda x: datetime.fromtimestamp(x/1000000000000).strftime('%Y-%m-%d'))
    df['_source.scan_timestamp'] = df['_source.scan_timestamp'].apply(
        lambda x: datetime.fromtimestamp(x/1000000000).strftime('%Y-%m-%d %H:%M:%S'))

    # sort values by timestamp
    df = df.sort_values(
        by=['_source.scan_timestamp'], ascending=False)
    
    return df

@st.cache_data
def get_folium_map(df):
    # Print the folium map
    map = folium.Map(location=[df.iloc[0]['latitude'],
                     df.iloc[0]['longitude']], zoom_start=15)

    # Add the markers to the map
    for _, row in df.iterrows():
        folium.Marker([row['latitude'], row['longitude']],
                      popup=f"{row['_source.business_name']} <br> ID= {row['_source.business_id']}").add_to(map)
    folium_static(map)


@st.cache_data
def free_text_search(text):
    query_body = {
        "query": {
            "simple_query_string": {
                "query": text
            }
        }
    }
    df = query_data(query_body)
    # rename latitude and longitude columns so they have the correct names for the map function
    df, table_df = common_data_process(df)
    return df, table_df


@st.cache_data
def postal_code_search(postal_code):
    query_body = {
        "query": {
            "match": {
                "zip": postal_code
            }
        }
    }
    df = query_data(query_body)

    # rename latitude and longitude columns so they have the correct names for the map function
    df, table_df = common_data_process(df)
    return df, table_df


@st.cache_data
def business_id_search(business_id):
    # build the search query for Elasticsearch
    query_body = {
        "query": {
            "simple_query_string": {
                "query": business_id,
                "fields": ["business_id"],
                "default_operator": "AND"
            }
        }
    }
    df = query_data(query_body)
    
    # filter the columns
    table_df = df.filter(items=['_source.scan_timestamp', '_source.deviceID',
                         '_source.user_name', '_source.user_birth_date'], axis=1)

    # turn the epochs into timestamps
    table_df = epoch_to_timestamp(table_df)

    # fix names before rendering the table
    table_df = table_df.rename(columns={"_source.scan_timestamp": "Scan Timestamp", "_source.deviceID": "Device ID",
                               "_source.user_name": "User Name", "_source.user_birth_date": "Birth Date"})
    return table_df


@st.cache_data
def device_id_search(device_id):
    # build the search query for Elasticsearch
    query_body = {
        "query": {
            "match": {
                "deviceID": device_id
            }
        }
    }
    df = query_data(query_body)

    # rename latitude and longitude columns so they have the correct names for the map function
    df = df.rename(columns={"_source.latitude": "latitude",
                   "_source.longitude": "longitude"})

    # Turn the epochs into timestamps
    df = epoch_to_timestamp(df)

    # filter the columns
    table_df = df.filter(items=['_source.scan_timestamp', '_source.business_id',
                         '_source.business_name', '_source.business_address', 'longitude', 'latitude'], axis=1)

    # fix names before rendering the table
    table_df = table_df.rename(columns={"_source.scan_timestamp": "Scan Timestamp", "_source.business_id": "Business ID",
                               "_source.business_name": "Business Name", "_source.business_address": "Business Address"})
    return df, table_df
