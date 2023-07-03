import streamlit as st
import helpers

# Ensure the entire page is loaded
st.set_page_config(layout="wide")

# Add title to sidebar
st.sidebar.title("San Francisco business App Scan Tracker")

# Add a separator
my_separator = "---"
st.sidebar.markdown(my_separator, unsafe_allow_html=False)

"""Search by free text"""
############################################
text = st.sidebar.text_input("Free text search")

# add the link to the map below the code
st.sidebar.markdown("### [Map](https://www.google.com/maps/search/?api=1&query=37.76,-122.4)")

# Add a separator
my_separator = "---"
st.sidebar.markdown(my_separator, unsafe_allow_html=False)

if text:
    df, free_text_df = helpers.free_text_search(text)
    
    # Add table with  a headline and print the table
    st.subheader("Businesses for search term: " + text)
    free_text_table = st.dataframe(data=free_text_df)
    
    # Print the folium map
    try:
        helpers.get_folium_map(df)
    except IndexError:
        st.error(f"Search term '{text}' not found")

"""Search By Postal Code"""
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
    df, postal_code_df = helpers.postal_code_search(postal_code)
    
    
    # Add table with  a headline and print the table
    st.subheader("Businesses in postal code: " + postal_code)
    postal_code_table = st.dataframe(data=postal_code_df)
    
    # Print the folium map
    try:
        helpers.get_folium_map(df)
    except IndexError:
        st.error("Invalid postal code")
    
"""Search by Business ID"""
############################################
# Add the input field on the sidebar
business_id = st.sidebar.text_input("Business ID")

# Add a separator
my_separator = "---"
st.sidebar.markdown(my_separator, unsafe_allow_html=False)

if business_id:
    try:
        # Check if the business id is valid
        business_id_df = helpers.business_id_search(business_id)
    except KeyError:
        st.error("Invalid business ID")
        business_id_df = None
    
    # Add table with  a headline and print the table
    st.subheader("Users scanned at this business: " + business_id)
    business_id_table = st.dataframe(data=business_id_df)
    
"""Search by Device ID"""
############################################
device_id = st.sidebar.text_input("Device ID")

if device_id:
    try:
        df, device_id_df = helpers.device_id_search(device_id)
    except KeyError:
        st.error("Invalid device ID")
        device_id_df = None
    
    # Add a table with the headline and print the table
    st.header("Scans from device: " + device_id)
    device_id_table = st.dataframe(data=device_id_df)
    
    # add the folium maps
    if device_id_df is not None:
        helpers.get_folium_map(df)