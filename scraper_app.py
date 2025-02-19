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

st.title("🌐 LinkedIn Contribution Questions Scraper AI Agent BY Lindsey")

# 1️⃣ Read `Link.csv` Automatically
csv_path = "Link.csv"  # ✅ Directly read from the project folder

# ========= 2. Define a helper function to convert time strings into numeric days =========
def convert_time_to_days(time_str):
    """
    Converts strings like '3 days ago', '5 hours ago' into numeric day values.
    Lower day values mean more recent (e.g., 1 day vs. 7 days).
    """
    parts = time_str.split()
    if len(parts) < 2:
        return 9999  # Default large number for unknown times

    try:
        num = int(parts[0])  # e.g. '3' in '3 days ago'
    except ValueError:
        return 9999

    unit = parts[1].lower()  # e.g. 'days', 'hours', etc.
    if "day" in unit:
        return num
    elif "hour" in unit:
        # 24 hours in a day => each hour is ~0.0417 days
        # We'll use 0.04 for simplicity
        return num * 0.04
    elif "week" in unit:
        return num * 7
    elif "month" in unit:
        return num * 30
    elif "year" in unit:
        return num * 365
    else:
        return 9999


if os.path.exists(csv_path):
    df_csv = pd.read_csv(csv_path)

        
    # ✅ Use columns with tighter spacing to bring them closer
    col1, col2 = st.columns([0.5, 0.6])  # Reduce spacing between title & button

   
    with col1:
        st.markdown(
            "<h4 style='font-size:24px;'>✅ Topics Loaded from File:</h4>",
            unsafe_allow_html=True
        )

    with col2:
        csv_file = open(csv_path, "rb").read()
        st.download_button(
            label="📥 Download `Link.csv`",
            data=csv_file,
            file_name="Link.csv",
            mime="text/csv",
        )

    #st.dataframe(df_csv[["Topic", "Link"]])  # Show topics and links
    # ✅ Define a unique section name (so it does not affect other checkboxes)
    section_key = "topic_selection"

    # ✅ Initialize session state for "Select All"
    if section_key not in st.session_state:
        st.session_state[section_key] = True  # Default is Select All enabled

    # ✅ "Select All" Checkbox (controls all other checkboxes)
    select_all = st.checkbox("📌 Select All Topics", value=st.session_state[section_key])

    # ✅ If toggled, update session state
    if select_all != st.session_state[section_key]:
        st.session_state[section_key] = select_all  # Update session state

    # ✅ Create checkboxes in a grid format (3 checkboxes per row)
    cols = st.columns(3)  # Arrange checkboxes in 3 columns
    topic_selection = {}

    for i, topic in enumerate(df_csv["Topic"]):
        col = cols[i % 3]  # Rotate checkboxes through the 3 columns
        # ✅ Ensure each checkbox is updated when "Select All" is toggled
        topic_selection[topic] = col.checkbox(topic, value=st.session_state[section_key], key=f"topic_{i}")

    # ✅ Get selected topics (Only include topics that were checked)
    selected_topics = [topic for topic, selected in topic_selection.items() if selected]



    if st.button("🚀 Start Scraping"):
        st.write("⏳ Setting up browser...")
        
        # 2️⃣ Cache Selenium Driver to Avoid Multiple Downloads
        @st.cache_resource
        def get_driver():
            options = Options()
            options.add_argument("--headless")  # Run in headless mode (no UI)
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")

            service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
            return webdriver.Chrome(service=service, options=options)

        driver = get_driver()  # ✅ Use cached WebDriver
        all_dataframes = []
        selected_rows = len(selected_topics)  # ✅ Count selected topics

        # ✅ Prevent division by zero (Ensure at least 1 topic is selected)
        if selected_rows == 0:
            st.error("⚠️ Please select at least one topic before scraping!")
            st.stop()  # 🚫 Stop execution if no topics are selected


        # Progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()  # Create an empty placeholder for dynamic updates
        scraped_count = 0  # ✅ Tracks only processed topics

        for i, row in df_csv.iterrows():
            topic_name = row["Topic"]
            url = row["Link"]
            
            if topic_name not in selected_topics:
                continue  # ⛔ Skip topics that were not selected

            scraped_count += 1
            progress_percent = scraped_count / selected_rows  # Correctly track selected topics only
            #status_text.text(f"🔍 Scraping: {topic_name} ({scraped_count}/{selected_rows})")
            status_text.markdown(f"🔍 Scraping: **{topic_name}** ({scraped_count}/{selected_rows})  \n🔗 [Open URL]({url})")

            progress_bar.progress(min(1.0, progress_percent))  # ✅ Ensure it stays in range [0,1]

            driver.get(url)
            time.sleep(5)  # Wait for JavaScript to load

            soup = BeautifulSoup(driver.page_source, "html.parser")
            articles = soup.find_all("div", class_="ml-1")

            data = []
            for article in articles:
                try:
                    title_tag = article.find("h2")
                    title = title_tag.text.strip() if title_tag else "No Title"

                    contributions_tag = article.find("span", string=lambda text: "contributions" in text.lower() if text else False)
                    contributions = contributions_tag.text.strip() if contributions_tag else "0 contributions"

                    time_tag = article.find("span", class_="before:middot pt-0.5")
                    time_posted = time_tag.text.strip() if time_tag else "Unknown time"

                    link_tag = article.find("a", class_="content-hub-entities")
                    link = link_tag["href"] if link_tag else "No Link"

                    data.append([title, contributions, time_posted, link])

                except Exception as e:
                    st.write(f"⚠️ Error scraping {topic_name}: {e}")

            # Create DataFrame for this topic
            df = pd.DataFrame(data, columns=["Title", "Contributions", "Time Posted", "Link"])
            df["Days"] = df["Time Posted"].apply(convert_time_to_days)
            df = df.sort_values(by="Days", ascending=True)  # ✅ Sort, but don't drop "Days" yet

            # Save DataFrame
            df.insert(0, "Topic", topic_name)
            all_dataframes.append(df)

            # Update progress bar
            # progress_bar.progress((i + 1) / selected_rows)

        driver.quit()
        st.write("🎉 Scraping completed!")

        # 3️⃣ Merge & Provide Download
        if all_dataframes:
            final_df = pd.concat(all_dataframes, ignore_index=True)

            # ✅ Ensure "Days" exists before sorting
            if "Days" in final_df.columns:
                final_df = final_df.sort_values(by="Days", ascending=True).drop(columns=["Days"])

            st.write("✅ Merged Data Preview:")
            st.dataframe(final_df.head(100))  # Preview first 10 rows

            # Provide CSV Download
            csv = final_df.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Download Scraped Latest Questions", csv, "latest question .csv", "text/csv")
        else:
            st.write("⚠️ No data scraped. Check website structure!")

else:
    st.error("⚠️ `Link.csv` not found! Please ensure the file exists in the project folder.")
