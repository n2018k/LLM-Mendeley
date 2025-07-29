import sys
import os
import sqlite3
import argparse
from openai import OpenAI

# --- Configuration ---
DB_PATH = "pdf_database.db"
CLIENT = OpenAI(api_key=os.environ.get('CBORG_API_KEY'),
                base_url="https://api.cborg.lbl.gov")

AVAILABLE_MODELS = [
    "lbl/cborg-deepthought:latest", "lbl/cborg-coder:latest", "lbl/cborg-vision:latest",
    "lbl/llama", "lbl/qwen-coder", "lbl/qwen-vision", "openai/gpt-4o",
    "openai/o3", "openai/gpt-4o-mini", "openai/o1", "openai/o1-mini",
    "openai/o3-mini", "anthropic/claude-haiku", "anthropic/claude-sonnet",
    "anthropic/claude-opus", "google/gemini-pro", "google/gemini-flash",
    "google/gemini-flash-lite", "xai/grok", "xai/grok-mini", "aws/llama-3.1-405b",
    "aws/llama-3.1-70b", "aws/llama-3.1-8b", "aws/command-r-plus-v1",
    "aws/command-r-v1", "google/gemini-pro-preview"
]

# --- Core Functions ---

def get_all_summaries(db_path):
    """Fetches ALL summaries from the database, returning them as a single string."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT openai_summary FROM pdfs")
        summaries = cursor.fetchall()
        if not summaries:
            print("Warning: No summaries found in the database.")
            return ""
        all_summary_texts = [s[0] for s in summaries if s[0]]
        return "\n\n---\n\n".join(all_summary_texts)
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        conn.close()

def create_html_report(markdown_table, filename="theme_analysis.html"):
    """Converts a markdown table into a polished, standalone HTML file."""
    html_rows = []
    lines = markdown_table.strip().split('\n')
    
    # Skip non-table lines and the markdown separator line
    table_lines = [line for line in lines if '|' in line and '---' not in line]
    if not table_lines:
        print("Warning: Could not find a valid markdown table in the LLM's response.")
        return False

    # Process header
    header_cells = [h.strip() for h in table_lines[0].strip('|').split('|')]
    header_html = "<thead>\n<tr>\n"
    for cell in header_cells:
        header_html += f"<th>{cell}</th>\n"
    header_html += "</tr>\n</thead>"

    # Process body rows
    body_html = "<tbody>\n"
    for line in table_lines[1:]:
        body_html += "<tr>\n"
        cells = [c.strip() for c in line.strip('|').split('|')]
        for cell in cells:
            body_html += f"<td>{cell}</td>\n"
        body_html += "</tr>\n"
    body_html += "</tbody>"

    # --- HTML & CSS Template ---
    html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Database Theme Analysis</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
        body {{
            font-family: 'Inter', sans-serif;
            background-color: #f4f7f6;
            color: #333;
            margin: 0;
            padding: 2rem;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: #ffffff;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        }}
        h1 {{
            color: #2c3e50;
            text-align: center;
            margin-bottom: 2rem;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
        }}
        th, td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #e0e0e0;
        }}
        thead th {{
            background-color: #34495e;
            color: #ffffff;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        tbody tr:nth-of-type(even) {{
            background-color: #f8f9fa;
        }}
        tbody tr:hover {{
            background-color: #e9ecef;
            cursor: pointer;
        }}
        td:first-child {{
            font-weight: 600;
            color: #2980b9;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Research Theme Analysis</h1>
        <table>
            {header_html}
            {body_html}
        </table>
    </div>
</body>
</html>
"""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html_template)
        return True
    except IOError as e:
        print(f"Error writing to file {filename}: {e}")
        return False

def generate_theme_analysis(model_name):
    """Analyzes all summaries to generate a table of research themes."""
    print("Fetching all summaries for theme analysis...")
    all_summaries = get_all_summaries(DB_PATH)
    if all_summaries is None or not all_summaries:
        return "Could not generate themes because no summaries were found in the database."

    theme_prompt = f"""
    Based on the following collection of research paper summaries:
    ---
    {all_summaries}
    ---
    Your task is to analyze this collection and identify the overarching research themes.
    Generate a summary of the database's contents with the following strict formatting requirements:
    1.  Identify **up to 10** distinct research themes.
    2.  For each theme, provide **exactly 8** representative keywords.
    3.  The final output **MUST** be a single markdown table and nothing else.
    The table structure must have two columns: `Research Theme` and `Keywords`.
    **Do not** include any text outside of the markdown table.
    """
    system_message = "You are a research data analyst specializing in synthesizing scientific literature. Your entire response should be only the markdown table."

    print(f"Sending request to model '{model_name}' to generate theme table...")
    try:
        response = CLIENT.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": theme_prompt}
            ],
            temperature=0.2
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"An error occurred while calling model {model_name}: {e}"

def get_recommendation(prompt, model_name, num_recommendations, temperature):
    """Gets paper recommendations by sending all summaries to a specified LLM."""
    print("\nFetching all summaries from the database...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT openai_summary, filepath, title FROM pdfs")
    summaries = cursor.fetchall()
    conn.close()

    if not summaries:
        return "The database is empty. No summaries to process."

    formatted_summaries = ""
    for summary, filepath, title in summaries:
        formatted_summaries += f"Summary: {summary}\nFilePath: {filepath}\nTitle: {title}\n\n"

    prompt_with_summaries = f"""
    Based on the following user query: "{prompt}"
    And the following complete list of research paper summaries from my database:
    ---
    {formatted_summaries}
    ---
    Please analyze all the summaries and recommend the top {num_recommendations} papers that best match the query. Provide the FilePath and Title for each. If no papers match, respond with "No matching papers found."
    """

    print(f"Sending request to model: {model_name} (Temperature: {temperature:.1f})...")
    try:
        response = CLIENT.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a helpful research assistant that recommends papers from a provided list."},
                {"role": "user", "content": prompt_with_summaries}
            ],
            temperature=temperature
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"An error occurred while calling model {model_name}: {e}"

# --- Main Execution Block ---

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Get paper recommendations or analyze database themes.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--themes", action="store_true",
                        help="Analyze all papers to generate a visually styled HTML report of research themes.")
    parser.add_argument("-p", "--prompt", help="The user prompt or research query for finding papers.")
    parser.add_argument("-m", "--model", default="anthropic/claude-sonnet", choices=AVAILABLE_MODELS,
                        help="The model to use for the task.\n(default: %(default)s)")
    parser.add_argument("-n", "--num", type=int, default=3, help="Number of recommendations to ask for.\n(default: %(default)s)")
    parser.add_argument("-t", "--temp", type=float, default=0.5, help="The initial temperature for the LLM.\n(default: %(default)s)")
    
    args = parser.parse_args()

    # MODE 1: Theme Analysis
    if args.themes:
        markdown_response = generate_theme_analysis(model_name=args.model)
        
        # Check if the response is an error message before proceeding
        if "An error occurred" in markdown_response or "Could not generate" in markdown_response:
            print(f"\nError: {markdown_response}")
            sys.exit(1)
            
        print("\nReceived analysis from model. Generating HTML report...")
        if create_html_report(markdown_response):
            print("\n---------------------------------")
            print("✅ Success! Report created.")
            print("Open 'theme_analysis.html' in your browser to view the results.")
            print("---------------------------------")
        else:
            print("\n---------------------------------")
            print("❌ Failed to create HTML report.")
            print("---------------------------------")
            print("Raw markdown from model:\n")
            print(markdown_response)
        sys.exit(0)

    # Check for prompt in recommendation mode
    if not args.prompt:
        parser.error("A prompt is required for recommendation mode. Use -p 'your query' or use --themes to see an overview.")

    # MODE 2: Interactive Recommendation Session
    current_prompt = args.prompt
    current_model = args.model
    current_temperature = args.temp

    while True:
        final_recommendation = get_recommendation(
            prompt=current_prompt,
            model_name=current_model,
            num_recommendations=args.num,
            temperature=current_temperature
        )
        
        print("\n--- LLM Recommendation ---")
        print(final_recommendation)
        print("--------------------------")

        while True:
            choice = input(f"""
What would you like to do next? (Current Model: {current_model})
  1. These recommendations are good. Exit.
  2. Refine the prompt with more information.
  3. Try again with the same prompt (for different results).
  4. Change the model.

Enter your choice (1, 2, 3, or 4): """).strip()
            
            if choice in ['1', '2', '3', '4']:
                break
            else:
                print("Invalid input. Please enter 1, 2, 3, or 4.")

        if choice == '1':
            print("\nGreat! Ending session.")
            break
        
        elif choice == '2':
            additional_info = input("\nPlease enter additional details to add to your prompt: ").strip()
            if additional_info:
                current_prompt += f". Also, specifically look for papers related to: {additional_info}"
                current_temperature = args.temp
                print("\nOkay, I've updated the prompt. Rerunning query...")
            else:
                print("\nNo additional information provided. Keeping the prompt as is.")
        
        elif choice == '3':
            current_temperature = min(current_temperature + 0.2, 1.2)
            print(f"\nOkay, trying again with a higher temperature ({current_temperature:.1f})...")

        elif choice == '4':
            print("\n--- Change Model ---")
            for i, model in enumerate(AVAILABLE_MODELS, 1):
                print(f"  {i}. {model}")
            
            while True:
                try:
                    model_choice = int(input(f"Enter the number of the model you want to use (1-{len(AVAILABLE_MODELS)}): ").strip())
                    if 1 <= model_choice <= len(AVAILABLE_MODELS):
                        current_model = AVAILABLE_MODELS[model_choice - 1]
                        current_temperature = args.temp
                        print(f"\nModel changed to: {current_model}. Rerunning query...")
                        break
                    else:
                        print("Invalid number. Please choose from the list.")
                except ValueError:
                    print("Invalid input. Please enter a number.")
