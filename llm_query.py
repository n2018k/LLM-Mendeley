import requests
import json, re
import PyPDF2, sys, os
from openai import OpenAI
import sqlite3

client = OpenAI(api_key=os.environ.get('CBORG_API_KEY'),
                        base_url="https://api.cborg.lbl.gov")

models = [
            "lbl/cborg-deepthought:latest",       # LBL-hosted Llama with custom system prompt
            "lbl/cborg-coder:latest",      # LBL-hosted Llama with custom system prompt
            "lbl/cborg-vision:latest",     # LBL-hosted Llama with custom system prompt
            "lbl/llama",                   # LBL-hosted Chat model
            "lbl/qwen-coder",              # LBL-hosted Coding model
            "lbl/qwen-vision",             # LBL-hosted Vision model
            "openai/gpt-4o",
            "openai/o3",
            "openai/gpt-4o-mini",
            "openai/o1",
            "openai/o1-mini",
            "openai/o3-mini",
            "anthropic/claude-haiku",
            "anthropic/claude-sonnet",
            "anthropic/claude-opus",
            "google/gemini-pro",
            "google/gemini-flash",
            "google/gemini-flash-lite",
            "xai/grok",
            "xai/grok-mini",
            "aws/llama-3.1-405b",
            "aws/llama-3.1-70b",
            "aws/llama-3.1-8b",
            "aws/command-r-plus-v1",
            "aws/command-r-v1",
            "google/gemini-pro-preview"
        ]

def get_recommendation(prompt, db_path="pdf_database.db"):
    """Gets a paper recommendation from the database using an LLM."""
    all_summaries = get_all_summaries(db_path)  # Function to fetch all summaries from the database
    if all_summaries is None:
        return None

    prompt_with_summaries = f"""
    I want to read a paper about {prompt}.  Here are some summaries of research papers:

    {all_summaries}

    Based on the prompt and the summaries, recommend 3 papers with its filepath and title.  If no paper matches, return "No match found".
    """
    for m in models[13:14]:
        print(f"Using model: {m}")
        try:
            response = client.chat.completions.create(
                model=m,
                messages = [
                    {
                        "role": "user",
                        "content": f"{prompt_with_summaries}",
                    }
                ],
                temperature = 0.6
            )
#            print(response)
            recommendation = response.choices[0].message.content
            return recommendation

        except:
            return f"Error calling model {m}"

def get_all_summaries(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT openai_summary, filepath, title FROM pdfs")
        summaries = cursor.fetchall()
        formatted_summaries = ""
        for summary, filepath, title in summaries:
            formatted_summaries += f"Summary: {summary}\nFilePath: {filepath}\nTitle: {title}\n\n"
        return formatted_summaries
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        conn.close()

# Example usage:
user_prompt = sys.argv[1]
recommendation = get_recommendation(user_prompt)
print(f"Recommendation: {recommendation}")
