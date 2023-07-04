import faker
import pandas as pd
import numpy as np
from random import randrange
from datetime import datetime, timedelta



Faker = faker.Factory().create
fake = Faker()

n = 200000

def random_date():
    """This function will return a random datetime between two datetime objects"""
    """https://stackoverflow.com/questions/553303/generate-a-random-date-between-two-other-dates"""
    start = datetime.strptime('2022-01-01 4:50AM', '%Y-%m-%d %I:%M%p')
    end = datetime.strptime('2022-01-03 10:50PM', '%Y-%m-%d %I:%M%p')
    
    delta = end - start
    int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
    random_second = randrange(int_delta)
    return start + timedelta(seconds=random_second)

def run():
    # Create a fictional dataset for 200000 users with name, state, birth date and device id
    faker_data = pd.DataFrame([[fake.name(),
                                fake.state(),
                                fake.date_of_birth(minimum_age=18, maximum_age=90),
                                fake.msisdn()
                                ]
                            for _ in range(n)],
                            columns = ['user_name', 'user_state', 'user_birth_date', 'deviceID'])

    faker_data['user_id'] = range(1, 1+len(faker_data))

    print(faker_data.head(30))
    print(faker_data.dtypes)

    # Convert the data types to the correct ones
    faker_data = faker_data.convert_dtypes()

    faker_data = faker_data.astype({'user_id': 'int64'})
    faker_data['user_birth_date'] = pd.to_datetime(faker_data['user_birth_date'])
    print(faker_data.dtypes)

    businesses = pd.read_json("data/businesses.json", lines=True)
    businesses['user_id'] = np.random.randint(1, 200000, businesses.shape[0])
    print(businesses.head())
    print(businesses.dtypes)

    # merge the two dataframes
    merged_df =  businesses.merge(faker_data, on="user_id", how="left")
    print(merged_df.head())
    print(merged_df.dtypes)
    
    # Create a new column using lambda function
    merged_df['scan_timestamp'] = businesses['business_name'].apply(lambda x: random_date())
    print(merged_df.head())
    
    # drop the user id column
    merged_df = merged_df.drop(columns=['user_id'])
    
    print(merged_df.head(1).to_json())
    
    merged_df.to_parquet("data/app-scans.parquet.gzip", compression="gzip", use_dictionary=False)
    # JSON export for visual analysis and testing
    merged_df.to_json("data/app-scans.json", orient="records", lines=True)
    
if __name__ == "__main__":
    run()