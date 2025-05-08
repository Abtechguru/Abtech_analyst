import pandas as pd
import plotly.express as px
import requests
from bs4 import BeautifulSoup
import streamlit as st
from urllib.parse import urljoin

st.set_page_config(page_title="Abtech Car Analytics", layout="wide")

# 🎨 Custom CSS
st.markdown("""
    <style>
        .main { background-color: #f4f4f4; padding: 20px; }
        .block-container { padding: 2rem; }
        h1 { color: orange; }
        .stButton button { background-color: orange; color: white; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# Function to fetch data with improved error handling
def fetch_car_data(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch data: {e}")
        return pd.DataFrame()

    soup = BeautifulSoup(response.content, 'html.parser')
    car_data = []
    
    # Try different selectors for different websites
    if "jiji.ng" in url:
        listings = soup.find_all('div', class_='b-list-advert__item')
    elif "cheki" in url:
        listings = soup.find_all('div', class_='listing-unit')
    elif "cars45" in url:
        listings = soup.find_all('div', class_='vehicle-card')
    else:
        listings = soup.find_all('div', class_=lambda x: x and 'listing' in x.lower())
    
    for listing in listings:
        try:
            # Name extraction
            name = listing.find('h2') or listing.find('h3') or listing.find(class_=lambda x: x and 'name' in x.lower())
            name = name.text.strip() if name else "Unknown"
            
            # Price extraction
            price = (listing.find(class_='price') or 
                     listing.find(class_=lambda x: x and 'price' in x.lower()) or
                     listing.find('span', class_=lambda x: x and 'amount' in x.lower()))
            price = price.text.strip() if price else "0"
            price = ''.join(c for c in price if c.isdigit() or c == '.')
            
            # Location extraction
            location = (listing.find(class_='location') or 
                       listing.find(class_=lambda x: x and 'location' in x.lower()) or
                       listing.find('span', class_=lambda x: x and 'area' in x.lower()))
            location = location.text.strip() if location else "Unknown"
            
            # Year extraction
            year = (listing.find(class_='year') or 
                    listing.find(class_=lambda x: x and 'year' in x.lower()) or
                    listing.find('span', class_=lambda x: x and 'yr' in x.lower()))
            year = year.text.strip() if year else "0"
            year = ''.join(c for c in year if c.isdigit())
            
            car_data.append({
                "name": name,
                "price": float(price) if price else 0,
                "location": location,
                "year": int(year) if year and year.isdigit() else 0
            })
        except Exception as e:
            st.warning(f"Skipped a listing due to error: {str(e)}")
            continue

    return pd.DataFrame(car_data)

# Data cleaning function
def clean_car_data(df):
    if df.empty:
        return df
    
    # Convert price and year to numeric
    df['price'] = pd.to_numeric(df['price'], errors='coerce')
    df['year'] = pd.to_numeric(df['year'], errors='coerce')
    
    # Remove rows with invalid prices
    df = df[df['price'] > 0]
    
    # Fill missing years with median
    if 'year' in df.columns:
        median_year = df['year'].median()
        df['year'] = df['year'].fillna(median_year).astype(int)
    
    return df.dropna()

# UI Layout
st.title("🚘 Abtech Car Analytic System 🇳🇬")

car_websites = {
    "Jiji.ng Cars": "https://www.jiji.ng/cars",
    "Cheki Nigeria": "https://www.cheki.com.ng/vehicles",
    "Cars45 Nigeria": "https://www.cars45.com/listing",
    "Autochek Africa": "https://autochek.africa/ng/cars-for-sale"
}

selected_site_name = st.selectbox("Choose a website to fetch car data:", list(car_websites.keys()))
selected_site = car_websites[selected_site_name]

if st.button("Fetch and Analyze Data"):
    with st.spinner("⏳ Fetching car data... Please wait (this may take a minute)"):
        df_raw = fetch_car_data(selected_site)

    if df_raw.empty:
        st.warning("No data fetched. The website structure may have changed or the site may be blocking requests.")
    else:
        df_clean = clean_car_data(df_raw)
        st.session_state.df_clean = df_clean  # Store for CSV export

        st.subheader("🔎 Sample Data (10 rows)")
        st.dataframe(df_clean.head(10))

        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🚗 Top 10 Car Models")
            popular_cars = df_clean['name'].value_counts().head(10)
            st.bar_chart(popular_cars)
            
            st.subheader("💰 Price Distribution")
            fig = px.histogram(df_clean, x='price', nbins=20, 
                              title="Distribution of Car Prices")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("📅 Cars by Year")
            if df_clean['year'].nunique() > 1:
                fig = px.histogram(df_clean, x='year', 
                                  title="Cars by Manufacturing Year")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Insufficient year data")
            
            st.subheader("📍 Top Locations")
            if df_clean['location'].nunique() > 1:
                top_locations = df_clean['location'].value_counts().head(10)
                st.bar_chart(top_locations)
            else:
                st.warning("Insufficient location data")

# Export CSV
if "df_clean" in st.session_state:
    st.download_button(
        label="📥 Download Data as CSV",
        data=st.session_state.df_clean.to_csv(index=False).encode('utf-8'),
        file_name="car_data_analysis.csv",
        mime="text/csv"
    )
