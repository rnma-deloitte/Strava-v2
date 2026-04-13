import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
import requests
import os
import calendar
from datetime import datetime
import matplotlib.pyplot as plt

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
        border-radius: 8px;
        padding: 8px;
        margin: 5px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        text-align: left;
    }
    
    .calendar-title {
        color: var(--strava-black);
        font-weight: bold;
        margin-bottom: 5px;
        font-size: 0.9rem;
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
        import datetime
        
        # Get access token
        auth_url = "https://www.strava.com/oauth/token"
        payload = {
            'client_id': st.secrets["connections"]["supabase"]["STRAVA_CLIENT_ID"],
            'client_secret': st.secrets["connections"]["supabase"]["STRAVA_CLIENT_SECRET"],
            'refresh_token': st.secrets["connections"]["supabase"]["STRAVA_REFRESH_TOKEN"],
            'grant_type': 'refresh_token'
        }
        res = requests.post(auth_url, data=payload).json()
        access_token = res['access_token']
        
        # Filter for 2026 activities only
        start_2026 = datetime.datetime(2026, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
        after_timestamp = int(start_2026.timestamp())
        
        header = {'Authorization': 'Bearer ' + access_token}
        
        # Fetch ALL pages for 2026 activities
        all_activities = []
        page = 1
        while True:
            params = {
                'after': after_timestamp,
                'per_page': 200,
                'page': page
            }
            page_activities = requests.get("https://www.strava.com/api/v3/athlete/activities", 
                                          headers=header, params=params).json()
            if not page_activities:
                break
            all_activities.extend(page_activities)
            page += 1
        
        for act in all_activities:
            # Fetch full details if moving_time is missing
            activity = act
            if 'moving_time' not in act:
                detail_response = requests.get(
                    f"https://www.strava.com/api/v3/activities/{act['id']}",
                    headers=header
                ).json()
                activity = detail_response
            
            data = {
                "id": activity['id'], 
                "name": activity['name'], 
                "distance": activity['distance'],
                "moving_time": activity.get('moving_time', 0),
                "type": activity['type'], 
                "start_date": activity['start_date']
            }
            conn.table("activities").upsert(data).execute()
        
        st.success(f"✅ Dashboard Updated! Found {len(all_activities)} activities from 2026.")

# --- DASHBOARD UI ---

# Side bar for the refresh button
with st.sidebar:
    st.markdown("### 🔄 Sync Data")
    if st.button("Sync with Strava", key="sync_button"):
        refresh_strava_data()

# Main content

# 3. Pull data from Supabase to show on screen
df_data = conn.table("activities").select("*").execute()
df = pd.DataFrame(df_data.data)

if not df.empty:
    df['start_date'] = pd.to_datetime(df['start_date'])
    df_2026 = df[df['start_date'].dt.year == 2026]
    
# --- YOUR WEEK SECTION (TOP OF PAGE) ---
    st.markdown("### 🏃 This Week")
    
    # Calculate the start of the current week (Monday)
    now = datetime.now()
    start_of_week = pd.to_datetime(now.date() - pd.Timedelta(days=now.weekday()))
    
    # Filter for the current week
    this_week_df = df_2026[df_2026['start_date'] >= start_of_week]
    
    week_count = len(this_week_df)
    week_km = this_week_df['distance'].sum() / 1000
    week_hours = this_week_df['moving_time'].sum() / 3600
    
    # Single-row Flexbox container for mobile-friendly layout
    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: center; 
                background: white; border: 2px solid #F3F4F6; border-radius: 12px; 
                padding: 15px; margin: 10px 0; text-align: center;">
        <div style="flex: 1;">
            <div style="font-size: 1.2rem; font-weight: bold; color: #111827;">{week_count}</div>
            <div style="font-size: 0.7rem; color: #6B7280; text-transform: uppercase;">Activities</div>
        </div>
        <div style="flex: 1; border-left: 1px solid #F3F4F6; border-right: 1px solid #F3F4F6;">
            <div style="font-size: 1.2rem; font-weight: bold; color: #111827;">{week_km:.1f}</div>
            <div style="font-size: 0.7rem; color: #6B7280; text-transform: uppercase;">Kilometers</div>
        </div>
        <div style="flex: 1;">
            <div style="font-size: 1.2rem; font-weight: bold; color: #111827;">{week_hours:.1f}</div>
            <div style="font-size: 0.7rem; color: #6B7280; text-transform: uppercase;">Hours</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")

    # Calculate for Swim, Ride, and Run
    swim_df = df_2026[df_2026['type'] == 'Swim']
    ride_df = df_2026[df_2026['type'].isin(['Ride', 'EBikeRide', 'VirtualRide'])]  # All bike types
    run_df = df_2026[df_2026['type'] == 'Run']
    
    swim_km = swim_df['distance'].sum() / 1000
    ride_km = ride_df['distance'].sum() / 1000
    run_km = run_df['distance'].sum() / 1000
    
    # Calculate hours from moving_time (in seconds)
    swim_hours = swim_df['moving_time'].sum() / 3600
    ride_hours = ride_df['moving_time'].sum() / 3600
    run_hours = run_df['moving_time'].sum() / 3600
    
    # KPI boxes with Strava styling
    st.markdown("### 📊 2026 Activity Summary")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="kpi-container" style="display: flex; align-items: center; gap: 15px;">
            <div style="font-size: 3rem;">🏊</div>
            <div>
                <div class="kpi-value">{swim_km:.1f} km</div>
                <div class="kpi-value">{swim_hours:.1f} hours</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="kpi-container" style="display: flex; align-items: center; gap: 15px;">
            <div style="font-size: 3rem;">🚴</div>
            <div>
                <div class="kpi-value">{ride_km:.1f} km</div>
                <div class="kpi-value">{ride_hours:.1f} hours</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="kpi-container" style="display: flex; align-items: center; gap: 15px;">
            <div style="font-size: 3rem;">🏃</div>
            <div>
                <div class="kpi-value">{run_km:.1f} km</div>
                <div class="kpi-value">{run_hours:.1f} hours</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Quick calculations
    total_distance = df_2026['distance'].sum() / 1000  # Convert meters to km
   
    # Overall metrics with Strava styling
    st.markdown("### 📈 2026 Overall Statistics")
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
            <div class="metric-value">{len(df_2026)}</div>
            <div class="metric-label">Total Activities</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        favorite_sport = df_2026['type'].mode()[0] if not df_2026['type'].empty else "None"
        # Map Workout to Basketball for display
        display_sport = "Basketball" if favorite_sport == "Workout" else favorite_sport
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-value">{display_sport}</div>
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
                    # 1. Calculate total km and hours for this month
                    month_activities = df_2026[
                        (df_2026['start_date'].dt.month == month_idx + 1) & 
                        (df_2026['start_date'].dt.year == current_year)
                    ]
                    month_total_km = month_activities['distance'].sum() / 1000
                    month_total_hours = month_activities['moving_time'].sum() / 3600 # New Calculation
                    
                    # 2. Update the display to show both
                    st.markdown(f"""
                    <div class="calendar-month">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div class="calendar-title">{month_name} {current_year}</div>
                            <div style="color: #FC4C02; font-weight: bold; font-size: 0.9rem;">
                                {month_total_km:.1f}km | {month_total_hours:.1f}h
                            </div>
                        </div>
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

# --- 📊 MONTHLY PROGRESS BAR CHART (12 MONTHS, ULTRA THIN) ---
    st.markdown("### 📊 Monthly Progress")
    
    # 1. Prepare data for all 12 months of 2026
    current_month_num = datetime.now().month
    monthly_stats = []
    month_names = []
    
    for m in range(1, 13):  # Always show all 12 months
        m_df = df_2026[df_2026['start_date'].dt.month == m]
        m_hours = m_df['moving_time'].sum() / 3600
        monthly_stats.append(m_hours)
        month_names.append(calendar.month_name[m][:3].upper())

    # 2. Create the Figure
    fig, ax = plt.subplots(figsize=(5, 6))
    
    fig.patch.set_facecolor('#0a0a0a')
    ax.set_facecolor('#0a0a0a')

    # Color Logic: 
    # Past months = White, Current month = Orange, Future = Transparent/None
    colors = []
    for i in range(12):
        month_no = i + 1
        if month_no < current_month_num:
            colors.append('#FFFFFF') # Past
        elif month_no == current_month_num:
            colors.append('#FC4C02') # Current
        else:
            colors.append('#FFFFFF00') # Future (Transparent)

    # 3. Draw Ultra-Thin bars (width=0.15)
    ax.bar(month_names, monthly_stats, color=colors, edgecolor='#E5E7EB', linewidth=0.3, width=0.15)

    # 4. Add Labels (Rotated 90 degrees)
    max_h = max(monthly_stats) if max(monthly_stats) > 0 else 1
    
    for i, name in enumerate(month_names):
        # All 12 month tags at the bottom
        ax.text(i, -(max_h * 0.05), name, 
                ha='center', va='top', rotation=90, 
                fontsize=7, fontweight='bold', color='#E5E7EB')

    # 5. Total hours label on top of the CURRENT month bar only
    curr_idx = current_month_num - 1
    curr_val = monthly_stats[curr_idx]
    if curr_val > 0:
        ax.text(curr_idx, curr_val + (max_h * 0.02), 
                f"{int(curr_val)}HRS", 
                ha='center', va='bottom', rotation=90, 
                fontsize=8, fontweight='bold', color='#FC4C02')

    # 6. Clean up
    ax.axis('off')
    plt.tight_layout()
    
    st.pyplot(fig)

else:
    st.markdown("""
    <div style="text-align: center; padding: 50px;">
        <h3 style="color: #6B7280;">No activities found</h3>
        <p style="color: #9CA3AF;">Click the "Sync with Strava" button in the sidebar to load your data.</p>
    </div>
    """, unsafe_allow_html=True)