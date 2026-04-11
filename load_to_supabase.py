import os
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client, Client
import requests

load_dotenv()

import datetime

#STEP 1: GET A FRESH ACCESS TOKEN
print("🔄 Fetching fresh Strava access token...")
auth_url = "https://www.strava.com/oauth/token"
payload = {
    'client_id': os.getenv('STRAVA_CLIENT_ID'),
    'client_secret': os.getenv('STRAVA_CLIENT_SECRET'),
    'refresh_token': os.getenv('STRAVA_REFRESH_TOKEN'),
    'grant_type': 'refresh_token'
}

res = requests.post(auth_url, data=payload)
access_token = res.json().get('access_token')
if not access_token:
    raise Exception("❌ Failed to get access token. Check your Strava credentials.")
print("✅ Token received!")

# Get the exact start of 2026 in UTC
start_2026 = datetime.datetime(2026, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)

# Convert to the integer "Epoch" timestamp Strava needs
after_timestamp = int(start_2026.timestamp())

print(f"⏰ Filtering for activities after Epoch: {after_timestamp} (Jan 1, 2026)")

header = {'Authorization': 'Bearer ' + access_token}

# Fetch ALL activities from 2026 with pagination
my_dataset = []
page = 1
while True:
    params = {
        'after': after_timestamp,
        'per_page': 200,
        'page': page
    }
    
    page_data = requests.get(
        "https://www.strava.com/api/v3/athlete/activities", 
        headers=header, 
        params=params
    ).json()
    
    if not page_data:
        break  # No more activities
    
    my_dataset.extend(page_data)
    print(f"📄 Fetched page {page} ({len(page_data)} activities, total so far: {len(my_dataset)})")
    page += 1

print(f"✅ Found {len(my_dataset)} activities from 2026.")

# Check if first activity has moving_time field
if my_dataset and 'moving_time' not in my_dataset[0]:
    print("⚠️  WARNING: Strava list endpoint doesn't include moving_time. Fetching full details for each activity...")

# --- PART 2: CONNECT TO SUPABASE ---
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# --- PART 3: PUSH DATA ---
print("🚀 Uploading to Supabase...")

for activity in my_dataset:
    activity_id = activity['id']
    
    # If moving_time is missing, fetch full activity details
    if 'moving_time' not in activity:
        detail_response = requests.get(
            f"https://www.strava.com/api/v3/activities/{activity_id}",
            headers=header
        ).json()
        activity = detail_response
    
    # We only pick the columns that match our SQL table
    data_to_save = {
        "id": activity['id'],
        "name": activity['name'],
        "distance": activity['distance'],
        "moving_time": activity.get('moving_time', 0),
        "type": activity['type'],
        "start_date": activity['start_date']
    }
    
    # This 'upsert' command means: "Insert if new, update if already exists"
    # This prevents errors if you run the script twice!
    response = supabase.table("activities").upsert(data_to_save).execute()

print("✅ All done! Check your Supabase dashboard.")