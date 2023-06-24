import numpy as np
import pandas as pd
import json

def convert_json(value):
    try:
        return json.loads(value)
    except:
        return np.NaN

def run():
    # Create a converter that makes a json out of the string in 'Business Location', using double quotes instead of single quotes
    converter = {"Business Location": lambda x: x.replace("\'", "\"")}

    # Read the csv file, using the converter and  apply the convert_json function to the 'Business Location' column
    input_df = pd.read_csv("./data/registered-business-locations-san-francisco.csv", converters=converter)
    input_df["Business Location"] = input_df["Business Location"].map(lambda x: convert_json(x))

    # Filter out the columns we don't need
    filtered_df = input_df[["Location Id", "DBA Name", "Street Address", "City", "Source Zipcode", "Business Location"]]

    cleaned_df = filtered_df.dropna().reset_index()
    normalized = pd.json_normalize(cleaned_df["Business Location"], max_level=1)
    print(normalized.dtypes, normalized.head())

    # Create dataframe with longitude and latitude
    enriched_df = pd.DataFrame(normalized["coordinates"].to_list(), columns=["longitude", "latitude"])
    print(enriched_df.dtypes, enriched_df.head())

    # Merge the two dataframes and filter out the columns we don't need
    merged_df = pd.merge(cleaned_df, enriched_df, left_index=True, right_index=True)
    filtered_df = merged_df[["Location Id", "DBA Name", "Street Address", "City", "Source Zipcode", "longitude", "latitude"]]
    print(filtered_df["City"].value_counts())

    sf_data = filtered_df.loc[filtered_df["City"] == "San Francisco"]
    sf_data = sf_data.sample(n=100000)

    output_df = sf_data.rename(columns={
        "Location Id": "business_id",
        "DBA Name": "business_name", 
        "Street Address": "business_address",
        "City": "city",
        "Source Zipcode": "zip"
        })

    print(output_df.head())

    output_df.to_json("data/businesses.json", orient="records", lines=True)
    print(len(output_df))

if __name__ == "__main__":
    run()