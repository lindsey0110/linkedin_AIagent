import os
import time
import pandas as pd
import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
from bs4 import BeautifulSoup

INPUT_CSV = "latest question.csv"

# Function to setup WebDriver
@st.cache_resource
def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
    return webdriver.Chrome(service=service, options=options)

# Scraper function
def scrape_questions():
    driver = get_driver()
    all_dataframes = []
    
    # Load links from CSV
    if not os.path.exists("Link.csv"):
        return "⚠️ `Link.csv` not found!"
    
    df_csv = pd.read_csv("Link.csv")
    selected_topics = df_csv["Topic"].tolist()

    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, row in df_csv.iterrows():
        topic = row["Topic"]
        url = row["Link"]

        driver.get(url)
        time.sleep(5)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        articles = soup.find_all("div", class_="ml-1")

        data = []
        for article in articles:
            title_tag = article.find("h2")
            title = title_tag.text.strip() if title_tag else "No Title"
            link_tag = article.find("a", class_="content-hub-entities")
            link = link_tag["href"] if link_tag else "No Link"
            data.append([topic, title, link])

        df = pd.DataFrame(data, columns=["Topic", "Title", "Link"])
        all_dataframes.append(df)
        progress_bar.progress((i + 1) / len(df_csv))
        status_text.text(f"🔍 Scraping: {topic} ({i+1}/{len(df_csv)})")

    driver.quit()
    final_df = pd.concat(all_dataframes, ignore_index=True)
    final_df.to_csv(INPUT_CSV, index=False)
    return "✅ Scraping Complete!"
