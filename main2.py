import pandas as pd
import plotly.express as px
import requests
from bs4 import BeautifulSoup
import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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

# ✅ 1. Function to fetch data (merged version)
def fetch_car_data_bs(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch data: {e}")
        return pd.DataFrame()

    soup = BeautifulSoup(response.content, 'html.parser')
    car_data = []
    listings = soup.find_all('div', class_='listing-item')

    for listing in listings:
        try:
            name = listing.find('h2').text.strip() if listing.find('h2') else "Unknown"
            price = listing.find('span', class_='price')
            price = price.text.strip().replace('₦', '').replace(',', '') if price else "0"
            location = listing.find('span', class_='location')
            location = location.text.strip() if location else "Unknown"
            year = listing.find('span', class_='year')
            year = int(year.text.strip()) if year and year.text.strip().isdigit() else 0
            car_data.append({"name": name, "price": float(price), "location": location, "year": year})
        except Exception as e:
            st.warning(f"Error processing listing: {e}")
            continue

    return pd.DataFrame(car_data)

# ✅ Selenium function for JS-heavy pages (modified for Streamlit Cloud)
def fetch_car_data_selenium(url):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    try:
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        
        # Wait for elements to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "listing-item"))
        
        listings = driver.find_elements(By.CLASS_NAME, "listing-item")
        car_data = []

        for listing in listings:
            try:
                name = listing.find_element(By.TAG_NAME, "h2").text.strip()
                price = listing.find_element(By.CLASS_NAME, "price").text.strip().replace('₦', '').replace(',', '')
                location = listing.find_element(By.CLASS_NAME, "location").text.strip()
                year = listing.find_element(By.CLASS_NAME, "year").text.strip()
                car_data.append({
                    "name": name, 
                    "price": float(price), 
                    "location": location, 
                    "year": int(year) if year.isdigit() else 0
                })
            except Exception as e:
                st.warning(f"Error processing listing: {e}")
                continue

        driver.quit()
        return pd.DataFrame(car_data)
        
    except Exception as e:
        st.error(f"Selenium error: {e}")
        return pd.DataFrame()

# ✅ Data cleaning
def clean_car_data(df):
    if df.empty:
        return df
    
    try:
        df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0)
        df['year'] = pd.to_numeric(df['year'], errors='coerce').fillna(0).astype(int)
        df = df.dropna()
        return df
    except Exception as e:
        st.error(f"Data cleaning error: {e}")
        return df

# ✅ UI Layout
st.title("🚘 Abtech Car Analytic System 🇳🇬")
car_websites = {
    "Jiji.ng": "https://www.jiji.ng/cars",
    "Cheki Nigeria": "https://www.cheki.com.ng",
    "Cars45": "https://www.cars45.com",
    "Autochek": "https://autochek.africa/ng"
}

selected_site_name = st.selectbox("Choose a website to fetch car data:", list(car_websites.keys()))
selected_site = car_websites[selected_site_name]

if st.button("Fetch and Analyze Data"):
    with st.spinner("⏳ Fetching car data... Please wait"):
        if "jiji" in selected_site.lower():
            df_raw = fetch_car_data_bs(selected_site)
        else:
            df_raw = fetch_car_data_selenium(selected_site)

    if df_raw.empty:
        st.warning("No data fetched. The website structure may have changed or the site may be blocking requests.")
    else:
        df_clean = clean_car_data(df_raw)
        st.session_state.df_clean = df_clean  # Store for CSV export

        st.subheader("🔎 Sample Data")
        st.dataframe(df_clean.head(10))

        st.subheader("🚗 Top 10 Most Listed Cars")
        popular_cars = df_clean['name'].value_counts().head(10)
        st.bar_chart(popular_cars)

        st.subheader("💰 Average Price by Car Model")
        avg_price_by_car = df_clean.groupby('name')['price'].mean().sort_values(ascending=False).head(10)
        st.bar_chart(avg_price_by_car)

        st.subheader("📅 Car Listings by Year")
        if df_clean['year'].nunique() > 1:
            cars_by_year = df_clean['year'].value_counts().sort_index()
            st.line_chart(cars_by_year)
        else:
            st.write("Not enough year data to display")

        st.subheader("📍 Car Listings by Location")
        if df_clean['location'].nunique() > 1:
            cars_by_location = df_clean['location'].value_counts().head(10)
            st.bar_chart(cars_by_location)
        else:
            st.write("Not enough location data to display")

# ✅ Export CSV
if "df_clean" in st.session_state:
    st.download_button(
        label="Download Data as CSV",
        data=st.session_state.df_clean.to_csv(index=False).encode('utf-8'),
        file_name="Abtech_Car_Data.csv",
        mime="text/csv"
    )
