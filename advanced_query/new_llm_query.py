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
    "lbl/cborg-chat:latest",       # LBL-hosted Llama with custom system prompt
    "lbl/cborg-coder:latest",      # LBL-hosted Llama with custom system prompt
    "lbl/cborg-vision:latest",     # LBL-hosted Llama with custom system prompt
    "lbl/llama",                   # LBL-hosted Chat model
    "lbl/qwen-coder",              # LBL-hosted Coding model
    "lbl/qwen-vision",             # LBL-hosted Vision model
    "openai/gpt-4o",
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
    "aws/command-r-v1"
]

# --- Core Functions ---

def get_all_summaries(db_path):
    """
    Fetches ALL summaries, filepaths, and titles from the database.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT openai_summary, filepath, title FROM pdfs")
        summaries = cursor.fetchall()
        if not summaries:
            print("Warning: No summaries found in the database.")
            return ""
        formatted_summaries = ""
        for summary, filepath, title in summaries:
            formatted_summaries += f"Summary: {summary}\nFilePath: {filepath}\nTitle: {title}\n\n"
        return formatted_summaries
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        conn.close()

def get_recommendation(prompt, model_name, num_recommendations, temperature, db_path=DB_PATH):
    """
    Gets paper recommendations by sending all summaries to a specified LLM.
    """
    print("\nFetching all summaries from the database...")
    all_summaries = get_all_summaries(db_path)
    if all_summaries is None:
        return "Could not retrieve summaries due to a database error."
    if not all_summaries:
        return "The database is empty. No summaries to process."

    prompt_with_summaries = f"""
    Based on the following user query: "{prompt}"

    And the following complete list of research paper summaries from my database:
    ---
    {all_summaries}
    ---
    Please analyze all the summaries provided and recommend the top {num_recommendations} papers that best match the user query.
    For each recommendation, provide its FilePath and Title.
    If no papers are a good match, respond with "No matching papers found."
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
        recommendation = response.choices[0].message.content
        return recommendation
    except Exception as e:
        return f"An error occurred while calling model {model_name}: {e}"

# --- Main Execution Block ---

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Get paper recommendations from a database using an LLM in an interactive session.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("-p", "--prompt", required=True, help="The initial user prompt or research query.")
    parser.add_argument("-m", "--model", default="anthropic/claude-sonnet", choices=AVAILABLE_MODELS,
                        help="The model to use for the recommendation.\n(default: %(default)s)")
    parser.add_argument("-n", "--num", type=int, default=3, help="Number of recommendations to ask for.\n(default: %(default)s)")
    parser.add_argument("-t", "--temp", type=float, default=0.5, help="The initial temperature for the LLM.\n(default: %(default)s)")
    
    args = parser.parse_args()

    # Initialize state variables for the session
    current_prompt = args.prompt
    current_model = args.model
    current_temperature = args.temp

    # Start the interactive loop
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
            # The menu now has four options
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
                current_temperature = args.temp # Reset temperature on prompt change
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
                        current_temperature = args.temp # Reset temperature on model change
                        print(f"\nModel changed to: {current_model}. Rerunning query...")
                        break
                    else:
                        print("Invalid number. Please choose from the list.")
                except ValueError:
                    print("Invalid input. Please enter a number.")
            # After changing the model, the main loop will automatically rerun the query
