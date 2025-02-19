import streamlit as st
import scraper_app
import answer

st.title("🤖 LinkedIn Scraper & Answer Generator")

# ========== Scraper Section ==========
st.subheader("🔍 Scrape LinkedIn Data")
if st.button("🚀 Start Scraping"):
    with st.spinner("Scraping LinkedIn data..."):
        result = scraper_app.scrape_questions()
    st.success(result)

    # Provide Download Button for Scraped Data
    with open(scraper_app.INPUT_CSV, "rb") as file:
        st.download_button("📥 Download Scraped Data", file, scraper_app.INPUT_CSV, "text/csv")

# ========== Answer Generator Section ==========
st.subheader("📝 Generate Answers for Questions")
if st.button("📝 Generate Answers"):
    with st.spinner("Processing questions..."):
        result = answer.process_questions()
    st.success(result)

    # Provide Download Button for Processed Answers
    if os.path.exists(answer.OUTPUT_CSV):
        with open(answer.OUTPUT_CSV, "rb") as file:
            st.download_button("📥 Download Processed Answers", file, answer.OUTPUT_CSV, "text/csv")
