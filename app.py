import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
import requests
import os
import calendar
from datetime import datetime

# Strava-inspired page config
st.set_page_config(
    page_title="2026 Activity Stats",
    page_icon="🏃",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Strava-like styling
st.markdown("""
<style>
    /* Strava color scheme */
    :root {
        --strava-orange: #FC4C02;
        --strava-orange-light: #FF6B35;
        --strava-gray: #6B7280;
        --strava-gray-light: #F3F4F6;
        --strava-white: #FFFFFF;
        --strava-black: #111827;
    }
    
    /* Main background */
    .main {
        background-color: var(--strava-white);
    }
    
    /* Sidebar styling */
    .sidebar .sidebar-content {
        background-color: var(--strava-gray-light);
    }
    
    /* Metric cards styling */
    .metric-container {
        background: linear-gradient(135deg, var(--strava-orange) 0%, var(--strava-orange-light) 100%);
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
        color: white;
        box-shadow: 0 4px 6px rgba(252, 76, 2, 0.1);
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 5px;
    }
    
    .metric-label {
        font-size: 1rem;
        opacity: 0.9;
    }
    
    /* KPI boxes styling */
    .kpi-container {
        background: white;
        border: 2px solid var(--strava-gray-light);
        border-radius: 12px;
        padding: 20px;
        margin: 10px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        transition: all 0.3s ease;
    }
    
    .kpi-container:hover {
        border-color: var(--strava-orange);
        box-shadow: 0 4px 8px rgba(252, 76, 2, 0.15);
    }
    
    .kpi-value {
        font-size: 2rem;
        font-weight: bold;
        color: var(--strava-black);
        margin-bottom: 5px;
    }
    
    .kpi-label {
        font-size: 0.9rem;
        color: var(--strava-gray);
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Button styling */
    .stButton>button {
        background: linear-gradient(135deg, var(--strava-orange) 0%, var(--strava-orange-light) 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(252, 76, 2, 0.3);
    }
    
    /* Calendar styling */
    .calendar-month {
        background: white;
        border-radius: 12px;
        padding: 15px;
        margin: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    
    .calendar-title {
        color: var(--strava-black);
        font-weight: bold;
        text-align: center;
        margin-bottom: 10px;
        font-size: 1.2rem;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--strava-gray-light);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--strava-orange);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--strava-orange-light);
    }
</style>
""", unsafe_allow_html=True)

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
    st.markdown("### 🔄 Sync Data")
    if st.button("Sync with Strava", key="sync_button"):
        refresh_strava_data()

# Main content
st.markdown("""
<div style="margin-bottom: 30px;">
</div>
""", unsafe_allow_html=True)

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
    
    # KPI boxes with Strava styling
    st.markdown("### 📊 2026 Activity Summary")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="kpi-container">
            <div class="kpi-value">{swim_km:.1f} km</div>
            <div class="kpi-label">Swim Distance</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="kpi-container">
            <div class="kpi-value">{bike_km:.1f} km</div>
            <div class="kpi-label">Bike Distance</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="kpi-container">
            <div class="kpi-value">{run_km:.1f} km</div>
            <div class="kpi-label">Run Distance</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Quick calculations
    total_distance = df['distance'].sum() / 1000  # Convert meters to km
    
    # Overall metrics with Strava styling
    st.markdown("### 📈 Overall Statistics")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-value">{total_distance:.1f} km</div>
            <div class="metric-label">Total Distance</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-value">{len(df)}</div>
            <div class="metric-label">Total Activities</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        favorite_sport = df['type'].mode()[0] if not df['type'].empty else "None"
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-value">{favorite_sport}</div>
            <div class="metric-label">Favorite Sport</div>
        </div>
        """, unsafe_allow_html=True)

    # Activity Calendar
    st.markdown("### 📅 Activity Calendar")
    
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
                    st.markdown(f"""
                    <div class="calendar-month">
                        <div class="calendar-title">{month_name} {current_year}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
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
else:
    st.markdown("""
    <div style="text-align: center; padding: 50px;">
        <h3 style="color: #6B7280;">No activities found</h3>
        <p style="color: #9CA3AF;">Click the "Sync with Strava" button in the sidebar to load your data.</p>
    </div>
    """, unsafe_allow_html=True)