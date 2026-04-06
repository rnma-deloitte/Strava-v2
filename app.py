import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
import requests
import os
import calendar
from datetime import datetime

st.set_page_config(page_title="My Strava Dashboard", layout="wide")

# 1. Connect to Supabase
conn = st.connection("supabase", type=SupabaseConnection)

# 2. Function to fetch data from Strava (The "Refresh" Logic)
def refresh_strava_data():
    with st.spinner("🔄 Fetching new activities from Strava..."):
        # This is the same logic we used in your script
        auth_url = "https://www.strava.com/oauth/token"
        payload = {
            'client_id': st.secrets["connections"]["supabase"]["STRAVA_CLIENT_ID"],
            'client_secret': st.secrets["connections"]["supabase"]["STRAVA_CLIENT_SECRET"],
            'refresh_token': st.secrets["connections"]["supabase"]["STRAVA_REFRESH_TOKEN"],
            'grant_type': 'refresh_token'
        }
        res = requests.post(auth_url, data=payload).json()
        access_token = res['access_token']
        
        header = {'Authorization': 'Bearer ' + access_token}
        activities = requests.get("https://www.strava.com/api/v3/athlete/activities", headers=header).json()
        
        for act in activities:
            data = {"id": act['id'], "name": act['name'], "distance": act['distance'], 
                    "type": act['type'], "start_date": act['start_date']}
            conn.table("activities").upsert(data).execute()
        
        st.success("✅ Dashboard Updated!")

# --- DASHBOARD UI ---

# Side bar for the refresh button
with st.sidebar:
    if st.button("🔄 Sync with Strava"):
        refresh_strava_data()

# 3. Pull data from Supabase to show on screen
df_data = conn.table("activities").select("*").execute()
df = pd.DataFrame(df_data.data)

if not df.empty:
    df['start_date'] = pd.to_datetime(df['start_date'])
    df_2026 = df[df['start_date'].dt.year == 2026]

    # Calculate for each activity type
    swim_df = df_2026[df_2026['type'] == 'Swim']
    bike_df = df_2026[df_2026['type'] == 'Ride']  # Assuming 'Ride' for bike
    run_df = df_2026[df_2026['type'] == 'Run']
    
    swim_km = swim_df['distance'].sum() / 1000
    bike_km = bike_df['distance'].sum() / 1000
    run_km = run_df['distance'].sum() / 1000
    
    # KPI boxes
    st.subheader("2026 Activity KPIs")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Swim Distance", f"{swim_km:.1f} km")
    
    with col2:
        st.metric("Bike Distance", f"{bike_km:.1f} km")
    
    with col3:
        st.metric("Run Distance", f"{run_km:.1f} km")
    
    # Quick calculations
    total_distance = df['distance'].sum() / 1000  # Convert meters to km
    
    # Create Columns for "Key Metrics"
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Distance", f"{total_distance:.1f} km")
    col2.metric("Total Activities", len(df))
    col3.metric("Favorite Sport", df['type'].mode()[0])

    # Activity Calendar
    
    # Get unique activity dates
    if not df.empty:
        activity_dates = pd.to_datetime(df['start_date']).dt.date.unique()
        activity_dates_set = set(activity_dates)
        
        # Create calendar for 2026 up to current month
        current_year = 2026
        current_month = datetime.now().month  # This will be 4 for April
        months = ['January', 'February', 'March', 'April', 'May', 'June', 
                 'July', 'August', 'September', 'October', 'November', 'December']
        
        # Display months in a grid (3 months per row), but only up to current month
        months_to_show = months[:current_month]  # Only show months up to current month
        
        for row in range(0, len(months_to_show), 3):
            cols = st.columns(3)
            for i, month_name in enumerate(months_to_show[row:row+3]):
                month_idx = months.index(month_name)  # Get the month index (0-based)
                with cols[i]:
                    st.write(f"**{month_name} {current_year}**")
                    
                    # Get calendar for this month
                    cal = calendar.monthcalendar(current_year, month_idx + 1)
                    
                    # Create a simple text calendar with dots for active days
                    calendar_text = ""
                    for week in cal:
                        week_str = ""
                        for day in week:
                            if day == 0:
                                week_str += "   "  # Empty space for days not in month
                            else:
                                date_obj = datetime(current_year, month_idx + 1, day).date()
                                if date_obj in activity_dates_set:
                                    week_str += f" {day}•"  # Dot next to activity day
                                else:
                                    week_str += f" {day:2d} "  # Regular day
                        calendar_text += week_str + "\n"
                    
                    st.code(calendar_text, language="text")
    
    # Show the raw data
    st.subheader("Recent Sessions")
    st.dataframe(df)
else:
    st.warning("No data found. Click the Sync button in the sidebar!")