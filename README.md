# LLM-Mendeley
Maintaining a LLM based Mendeley database connected to Mendeley Web+Desktop for pdf analyzer and recommender 


1. execeute.py script will find your Mendeley directory, web interface and read all pdfs from a chosen directory of your choice.
From there, it will pass each pdf one by one to a pdf reader to extract text between Abstract/Introduction up to Acknowledgment/References
Then, it will pass that extracted text to chosen LLM model (here gemini-flash) for a 200 word summary which will be stored in a sqlite database
along with file path and title. 

2. query.py script will access all your summaries from database and upon a prompt, will suggest you papers which are extremely relevant for you from the database
along with suggestions about why its good for you. It uses Claude Sonnet for recommendation

3. delete.py script will delete any title from the database.


