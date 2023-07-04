# contact-tracing

This is a simple application that performs Contact Tracing using an <b>Elasticsearch</b> backend written in Python, and a Streamlit Frontend.

---

![image]()

---

## Goal of project 
Monitoring individuals' movements, based on how they scan their devices in various Business Locations within the City of San Fransisco.

---

## Dataset
The dataset used for this project is the [San Fransisco Registered Business Locations Dataset in Kaggle](https://www.kaggle.com/datasets/san-francisco/sf-registered-business-locations-san-francisco), which was sourced originally from the  [DataSF website](https://data.sfgov.org/Economy-and-Community/Registered-Business-Locations-San-Francisco/g8m3-pdis).

## Why Elasticsearch, instead of a Relational Database?
Elasticsearch is an open-source, distributed search and analytics engine built on top of Apache Lucene. It is designed to handle large volumes of data and provide real-time search, analysis, and visualization capabilities. Elasticsearch is part of the Elastic Stack, which includes other components like Kibana, Logstash, and Beats, providing a comprehensive solution for data ingestion, storage, analysis, and visualization.

![image]()

Key features and advantages of Elasticsearch that makes it preferrable to a traditional Relational Database Management System (RDBMS) are given below:

### Full-Text Search
Elasticsearch is designed specifically for full-text search use cases. It excels at indexing and searching large volumes of unstructured or semi-structured text data. If your application requires powerful and fast search capabilities, Elasticsearch provides features like relevance scoring, stemming, tokenization, faceted search, fuzzy matching, and more. 

### Scalability and Performance
Elasticsearch is built to handle massive amounts of data and scale horizontally across multiple nodes. It distributes data across the cluster, allowing you to add or remove nodes easily to handle increasing or decreasing data loads. Elasticsearch's distributed architecture and sharding provide high availability and improved performance, making it suitable for applications that require fast and efficient search and analytics.

### Realtime Analytics
Elasticsearch supports real-time data ingestion and analysis. It allows you to index and search data in near real-time, making it suitable for applications that require up-to-date information, such as log analysis, monitoring, and real-time analytics. Elasticsearch also integrates well with other tools in the Elastic Stack, such as Kibana for visualization and Logstash for data ingestion, enabling powerful analytics workflows.

### Schemaless and Flexible Data Model
Elasticsearch follows a schemaless data model, allowing you to index and search documents with varying structures and fields. This flexibility makes it easy to accommodate evolving data structures without the need to modify the database schema. It is particularly beneficial in scenarios where data is heterogeneous or changes frequently.

### Geospatial Capabilities
Elasticsearch has built-in support for geospatial data and offers advanced geospatial search capabilities. It allows you to index and search for documents based on their geographic coordinates, perform distance-based queries, and aggregate geospatial data. This makes Elasticsearch well-suited for applications that require location-based services, geospatial analysis, or geolocation data processing.

### Distributed Document Store in JSON format
Elasticsearch can function as a distributed document store, similar to NoSQL databases. It stores data as JSON documents, providing a flexible and schemaless data storage mechanism. You can perform CRUD operations on individual documents, retrieve data by unique identifiers, and leverage Elasticsearch's powerful search and aggregation capabilities.

---

## Project Setup and requirements for local development
1. Requires a Machine with at least 8GB of RAM
2. WSL for windows, and other Unix (MacOS, Linux) Operating systems
3. Docker and Docker Compose, with Elasticsearch Image version 7.17.1
4. Python packages as listed in `requirements.txt`

# Configure WSL2 to use max only 4GB of ram
```
wsl --shutdown
notepad "$env:USERPROFILE/.wslconfig"
```
.wslconfig file:
```
[wsl2]
memory=4GB   # Limits VM memory in WSL 2 up to 4GB
```

### Enter in WSL before Start
sudo sysctl -w vm.max_map_count=262144

### Use parquet loader for elasticsearch
install the loader
```bash
pip install elasticsearch-loader[parquet]
```

### Dataset Preparation
We begin with writing in the source dataset from a csv file, with some preprocessing transformations that saves the data into a json format. The `Business Location` column is loaded into a JSON format and json-normalized, in the script [`process-data.py`]()

After that, the data is enriched by the generation of User data using the python [`faker`]() package. This generated data is now merged with the SF Business Locations data, and app scan timestamp values are generated and added to the merged dataframe, which is then saved as a compressed parquet file (to save storage space) before it is fed into Elasticsearch.

```python
# merge the two dataframes
merged_df =  businesses.merge(faker_data, on="user_id", how="left")
print(merged_df.head())
print(merged_df.dtypes)
merged_df.to_parquet("data/app-scans.parquet.gzip", compression="gzip", use_dictionary=False)
```

---

### Preparing Elasticsearch and loading the data
Start the Elasticsearch by running the docker image using the command

```bash
docker compose up
```

Then run the Elasticsearch loader to load the data into Elasticsearch, and create an index - `my_app_scans`

```bash
elasticsearch_loader --index my_app_scans --type scans parquet ~/contact-tracing/data/app-scans.parquet.gzip
```

Elasticsearch UI showing the Index created
![image]()

A view of the data in Elasticsearch
![image]()

### Creating the streamlit application
A streamlit application is written with helper functions that process the data from within Elasticsearch, modularized and abstracted for proper organization. Various search parameters were created. We can search by Free Text, Postal Code, Business ID or Device ID of the users, at the various locations, which are rendered in a table as well as a folium map, which leverages Elasticsearch's ability to support geospatial data.

Here is an example of the Free Text Search created in `app.py` and it's use of wrappers that query Elasticsearch from within `helpers.py`

`app.py`
```python
import streamlit as st
import src.helpers as helpers

...

""":violet[Search by Free Text]"""
############################################
text = st.sidebar.text_input(":orange[Free text search]")

# add the link to the map below the code
st.sidebar.markdown("### [Map](https://www.google.com/maps/search/?api=1&query=37.76,-122.4)")

# Add a separator
my_separator = "---"
st.sidebar.markdown(my_separator, unsafe_allow_html=False)

if text:
    df, free_text_df = helpers.free_text_search(text)
    
    # Add table with  a headline and print the table
    st.subheader(":green[Businesses for search term:] " + text)
    free_text_table = st.dataframe(data=free_text_df, width=1200)
    
    # Print the folium map
    try:
        helpers.get_folium_map(df)
    except IndexError:
        st.error(f"Search term '{text}' not found")
```

`src/helpers.py`
```python
import streamlit as st
import pandas as pd
from elasticsearch import Elasticsearch
from streamlit_folium import folium_static
import folium
from datetime import datetime

...

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
def get_folium_map(df):
    # Print the folium map
    map = folium.Map(location=[df.iloc[0]['latitude'],
                     df.iloc[0]['longitude']], zoom_start=15)

    # Add the markers to the map
    for _, row in df.iterrows():
        folium.Marker([row['latitude'], row['longitude']],
                      popup=f"{row['_source.business_name']} <br> ID= {row['_source.business_id']}").add_to(map)
    folium_static(map)
```

Then the streamlit app is fired up with the command:

```bash
streamlit run app.py
```

Streamlit app UI
![image]()

![image]()

### Summary and next steps
1. Create a client that writes new scans (a scanning plugin) into Elasticsearch to update the database
2. New search parameters to track users movements within the City.
3. Deployment of Web Application in a cloud server with a CI/CD process in place
4. Create a dashboard on Kibana, showing stats about individuals and their locations, movement patterns.