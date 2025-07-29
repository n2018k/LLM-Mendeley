import requests
import json, re
import PyPDF2, sys, os
from openai import OpenAI
import sqlite3

def get_mendeley_data(mendeley_id, api_key):
    """Retrieves data from the Mendeley API for a given Mendeley ID."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/vnd.mendeley-document.1+json"
    }
    url = f"https://api.mendeley.com/folders?limit=150" # use this to scan all folders
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Mendeley data: {e}")
        return None

def get_mendeley_file_from_folder(mendeley_id, api_key, ident=None):
    """Retrieves data from the Mendeley API for a given Mendeley ID."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/vnd.mendeley-document.1+json"
    }
    url = f"https://api.mendeley.com/folders/{ident}/documents?limit=150" # use this to scan all files in a folder, but it only returns id
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Mendeley data: {e}")
        return None

def get_mendeley_file_data(mendeley_id, api_key, ident=None):
    """Retrieves data from the Mendeley API for a given Mendeley ID."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/vnd.mendeley-document.1+json"
    }
    url = f"https://api.mendeley.com/files?document_id={ident}"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes
        data_file = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Mendeley data: {e}")
        return None
    url = f"https://api.mendeley.com/documents/{ident}"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes
        data_doc = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Mendeley data: {e}")
        return None
    return data_file, data_doc



# Example usage:
api_key = 'put api key here'
mendeley_id = 'put mendeley project id here'
mendeley_data = get_mendeley_data(mendeley_id, api_key)
for dat in mendeley_data:
    if dat['name']=='need sorting':
        identification = dat['id']

files = get_mendeley_file_from_folder(mendeley_id, api_key, ident=identification)
file_data, title_data = [], []
for f in files:
    one_id = f['id']
    data_file, data_doc = get_mendeley_file_data(mendeley_id, api_key, one_id)
    file_data.append(data_file)
    title_data.append(data_doc)


def extract_main_body(text):
    """Extracts the text between specified section markers.

    Args:
        text: The full text extracted from the PDF.

    Returns:
        The text between the section markers, or None if no match is found.
    """
    # Define the section markers
    markers = [
        ("Abstract", "References"),
        ("Abstract", "Acknowledgments"),
        ("Introduction", "References"),
        ("Introduction", "Acknowledgments"),
        ("Introduction", "Acknowledgment"),
        ("Introduction", "Acknowledgement"),
        ("Introduction", "Acknowledgements"),
        ("Abstract", "Acknowledgment"),
        ("Abstract", "Acknowledgement"),
        ("Abstract", "Acknowledgements"),
        ("Results", "Acknowledgements"),
        ("Results", "Acknowledgement"),
        ("Results", "Acknowledgment"),
        ("Results", "Acknowledgments"),
        ("Results", "References"),
    ]

    for start_marker, end_marker in markers:
        match = re.search(rf"{start_marker}(.*?){end_marker}", text, re.IGNORECASE | re.DOTALL)
        if match:
            main_body = match.group(1).strip()
            return main_body
    return None 


# Example usage (assuming 'text' is already extracted from the PDF using PyPDF2):

# add the path where pdfs are stored
path_prefix = 'path to mendeley userfiles'

models = [ 
            "lbl/cborg-deepthought:latest",       # LBL-hosted Llama with custom system prompt
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
            "aws/command-r-v1",
            "google/gemini-flash",
            "google/gemini-pro"
        ]

def summarize_text(text):
    for m in models[24:25]:
        print(f"Using model: {m}")
        try:
            response = client.chat.completions.create(
                model=m,
                messages = [
                    {
                        "role": "user",
                        "content": f"Summarize the following text in less than 200 words:\n\n{text}",
                    }
                ],
                temperature=0.0
            )
            summary = response.choices[-1].message.content
            return summary
        except:
            print(f"Error calling model {m}")
            return None

client = OpenAI(api_key=os.environ.get('CBORG_API_KEY'),
                        base_url="https://api.cborg.lbl.gov")

def create_pdf_table(db_path="pdf_database.db"):
    """Creates the PDF table in the SQLite database if it doesn't exist."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pdfs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filepath TEXT UNIQUE,
            title TEXT,
            openai_summary TEXT
        )
    ''')
    conn.commit()
    conn.close()

def insert_pdf_data(filepath, title, summary, db_path="pdf_database.db"):
    """Inserts PDF data into the database.  Handles potential errors."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO pdfs (filepath, title, openai_summary) VALUES (?, ?, ?)",
                       (filepath, title, summary))
        conn.commit()
        print(f"Data for '{filepath}' inserted successfully.")
    except sqlite3.IntegrityError:
        print(f"Error: PDF '{filepath}' already exists in the database.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        conn.close()

def get_pdf_data(filepath, db_path="pdf_database.db"):
    """Retrieves PDF data from the database based on filepath."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pdfs WHERE filepath = ?", (filepath,))
    data = cursor.fetchone()
    conn.close()
    return data

def check_title_exists(title, db_path="pdf_database.db"):
    """Checks if a title already exists in the database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM pdfs WHERE title = ?", (title,))
        count = cursor.fetchone()[0]
        return count > 0
    except sqlite3.Error as e:
        print(f"Database error during title check: {e}")
        return False  # Assume it doesn't exist if there's an error
    finally:
        conn.close()

create_pdf_table()

for data_file, title in zip(file_data, title_data):
    pdf_path = path_prefix + data_file[0]['id'] + '.pdf'   # Replace with your PDF file path

    title = title['title']

    if not check_title_exists(title):

        try:
            with open(pdf_path, 'rb') as pdf_file:
                reader = PyPDF2.PdfReader(pdf_file)
                text = ""
                for page_num in range(len(reader.pages)):
                    page = reader.pages[page_num]
                    text += page.extract_text()

            main_body_text = extract_main_body(text)

        except FileNotFoundError:
            print(f"Error: File not found at '{pdf_path}'")
            continue
        except PyPDF2.errors.PdfReadError:
            print(f"Error: Could not read PDF file '{pdf_path}'")
            continue
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            continue
        if main_body_text:
            print(len(main_body_text))
        else:
            print("Could not find 'Abstract' or 'Acknowledgments' in the text.")
            continue
        
        summary = summarize_text(main_body_text)
        if summary:
            print("summary", summary)
            insert_pdf_data(pdf_path, title, summary)
        else:
            print("Could not get any summary from the text, check model problem.")
              

    else:
        print(f"The '{title}' of the path already exists.")

