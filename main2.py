import pandas as pd
import plotly.express as px
import requests
from bs4 import BeautifulSoup
import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

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
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch data: {e}")
        return pd.DataFrame()

    soup = BeautifulSoup(response.content, 'lxml')
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
            continue

    return pd.DataFrame(car_data)

# ✅ Selenium function for JS-heavy pages
def fetch_car_data_selenium(url):
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    driver.get(url)
    car_data = []

    listings = driver.find_elements(By.CLASS_NAME, "listing-item")

    for listing in listings:
        try:
            name = listing.find_element(By.TAG_NAME, "h2").text.strip()
            price = listing.find_element(By.CLASS_NAME, "price").text.strip().replace('₦', '').replace(',', '')
            location = listing.find_element(By.CLASS_NAME, "location").text.strip()
            year = listing.find_element(By.CLASS_NAME, "year").text.strip()
            car_data.append({"name": name, "price": float(price), "location": location, "year": int(year)})
        except Exception:
            continue

    driver.quit()
    return pd.DataFrame(car_data)

# ✅ Data cleaning
def clean_car_data(df):
    df['price'] = df['price'].astype(float)
    df['year'] = df['year'].astype(int)
    return df

# ✅ UI Layout
st.title("🚘 Abtech Car Analytic System 🇳🇬")
car_websites = [
    "https://www.mini.com.ng",
    "https://www.cars4.com",
    "https://www.jiji.ng/cars",
    "https://www.cheki.com.ng",
]
selected_site = st.selectbox("Choose a website to fetch car data:", car_websites)

if st.button("Fetch and Analyze Data"):
    with st.spinner("⏳ Fetching car data... Please wait"):
        if "jiji" in selected_site:
            df_raw = fetch_car_data_bs(selected_site)
        else:
            df_raw = fetch_car_data_selenium(selected_site)

    if df_raw.empty:
        st.warning("No data fetched. Check the site or structure.")
    else:
        df_clean = clean_car_data(df_raw)
        st.session_state.df_clean = df_clean  # Store for CSV export

        st.subheader("🔎 Sample Data")
        st.dataframe(df_clean.head(10))

        st.subheader("🚗 Top 10 Most Listed Cars")
        popular_cars = df_clean['name'].value_counts().head(10)
        st.bar_chart(popular_cars)

        st.subheader("💰 Average Price of Popular Cars")
        avg_price_by_car = df_clean.groupby('name')['price'].mean().sort_values(ascending=False).head(10)
        st.bar_chart(avg_price_by_car)

        st.subheader("📅 Car Listings by Year")
        cars_by_year = df_clean['year'].value_counts().sort_index()
        st.line_chart(cars_by_year)

# ✅ Export CSV
if "df_clean" in st.session_state and st.button("Download Data as CSV"):
    st.session_state.df_clean.to_csv("Abtech_Car_Data.csv", index=False)
    st.success("✅ Data saved as Abtech_Car_Data.csv")
