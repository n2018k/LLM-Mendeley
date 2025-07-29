# LLM-Mendeley
Maintaining a LLM based Mendeley database connected to Mendeley Web+Desktop for pdf analyzer and recommender 


1. execeute.py script will find your Mendeley directory, web interface and read all pdfs from a chosen directory of your choice.
From there, it will pass each pdf one by one to a pdf reader to extract text between Abstract/Introduction up to Acknowledgment/References
Then, it will pass that extracted text to chosen LLM model (here gemini-flash) for a 200 word summary which will be stored in a sqlite database
along with file path and title. 

2. query.py script will access all your summaries from database and upon a prompt, will suggest you papers which are extremely relevant for you from the database
along with suggestions about why its good for you. It uses Claude Sonnet for recommendation

3. delete.py script will delete any title from the database.


<img width="3014" height="2664" alt="graphviz" src="https://github.com/user-attachments/assets/e5d563ab-eaf9-4d47-8a76-c5b4b137100c" />


<img width="6026" height="3002" alt="graphviz (1)" src="https://github.com/user-attachments/assets/3ba7fcae-e325-4864-b1ee-ee1d5892e829" />
