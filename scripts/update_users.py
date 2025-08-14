import os
import pandas as pd
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def update_users_from_csv():
    """
    Wipes the 'users' collection and repopulates it from a CSV file.
    The CSV file must contain a column named 'user'.
    """
    # Get MongoDB URI from environment variables
    mongodb_uri = os.getenv('MONGODB_URI')
    if not mongodb_uri:
        print("Error: MONGODB_URI not found in .env file.")
        return

    # Connect to MongoDB
    try:
        client = MongoClient(mongodb_uri)
        db = client['study_chatbot']
        users_collection = db['users']
        print("Successfully connected to MongoDB.")
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        return

    # Get CSV file path from user
    csv_path = input("Enter the path to the CSV file: ")

    # Check if the file exists
    if not os.path.exists(csv_path):
        print(f"Error: File not found at '{csv_path}'")
        return

    # Read the CSV file
    try:
        df = pd.read_csv(csv_path)
        print(f"Successfully read {len(df)} rows from CSV.")
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return

    # Check for 'user' column
    if 'user' not in df.columns:
        print("Error: CSV file must have a column named 'user'.")
        return

    # Wipe the existing users collection
    try:
        delete_result = users_collection.delete_many({})
        print(f"Cleared {delete_result.deleted_count} existing users from the database.")
    except Exception as e:
        print(f"Error clearing users collection: {e}")
        return

    # Prepare the new users for insertion
    new_users = [{'username': username} for username in df['user'].dropna().unique()]

    # Insert new users into the collection
    if new_users:
        try:
            insert_result = users_collection.insert_many(new_users)
            print(f"Successfully inserted {len(insert_result.inserted_ids)} new users.")
        except Exception as e:
            print(f"Error inserting new users: {e}")
            return
    else:
        print("No new users to insert.")

    print("User database update complete.")

if __name__ == "__main__":
    update_users_from_csv()
