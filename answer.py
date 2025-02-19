import os
import csv
import openai
import streamlit as st

# OpenAI API


openai.api_key = openai_api
client = openai.OpenAI(api_key=openai_api)

INPUT_CSV = "latest question.csv"
OUTPUT_CSV = "latest_answers.csv"
MAX_ROWS = 100

# Check question relevancy
def check_relevancy(topic: str, title: str) -> str:
    prompt = f"""
You are an assistant. Determine if the question is relevant to financial education & banking simulations.
If highly relevant, output "High". Otherwise, "Medium" or "Low".

Topic: {topic}
Title: {title}

Output only one word: High, Medium, or Low.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return "Low"

# Generate answer if relevancy is High
def generate_answer(topic: str, title: str) -> str:
    prompt = f"""
At excelerateconsulting.co, we specialize in financial training for banking professionals.

Topic: {topic}
Title: {title}

Generate a short LinkedIn-style post.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content.strip()[:750]
    except Exception:
        return ""

# Process CSV
def process_questions():
    if not os.path.exists(INPUT_CSV):
        return "⚠️ No data found!"

    rows_with_output = []
    with open(INPUT_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        if "Relevance" not in fieldnames:
            fieldnames.append("Relevance")
        if "Answer" not in fieldnames:
            fieldnames.append("Answer")

        all_rows = [row for i, row in enumerate(reader) if i < MAX_ROWS]

    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, row in enumerate(all_rows):
        topic = row.get("Topic", "")
        title = row.get("Title", "")

        row["Relevance"] = check_relevancy(topic, title)
        row["Answer"] = generate_answer(topic, title) if row["Relevance"] == "High" else ""

        rows_with_output.append(row)
        progress_bar.progress((i + 1) / len(all_rows))
        status_text.text(f"Processing {i+1}/{len(all_rows)}")

    with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as wf:
        writer = csv.DictWriter(wf, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows_with_output)

    return "✅ Processing Complete!"
