# Reddit Search Web Interface

This is a Flask web application that uses **Apache Lucene** to search and rank Reddit post data. It reads from a pre-built Lucene index and displays the top-ranked results based on textual relevance and Reddit upvotes.

## Features

- Full-text search using Lucene's BM25 algorithm  
- Ranking options:  
  - Relevance (Lucene score)  
  - Upvotes  
  - Combined: 0.8 * relevance + 0.2 * log(1 + upvotes)
- Clean Bootstrap UI for inputs and results
- Displays top 10 results with:  
  - Title (linked)  
  - Subreddit  
  - Author  
  - Final score

## Repository Structure

Part B Relevant Repository Are Only Shown

```
WebCrawler/
├── app.py
├── templates/
    └── results.html
    └── search.html
├── RedditCrawler/
    └── indexing/
        └── reddit_index/
                └── Index Files #1    There Are A Ton Of Index Files,
                └── Index Files #2    All Would Be Located Here
                └── Index Files #...
```

## Prerequisites

Install Python dependencies:  
pip install flask

You must also install and build **PyLucene** manually:  
https://lucene.apache.org/pylucene/

## Running the App

1. Make sure the Lucene index exists at:  
RedditCrawler/indexing/reddit_index

2. Run the web server:  
cd WebCrawler  
python app.py

3. Open your browser and visit:  
http://localhost:5000

##  Scoring Logic

Scoring logic is implemented in `app.py`. It uses one of the following methods based on user input:

- Relevance only: final_score = lucene_score  
- Upvotes only: final_score = upvotes  
- Combined (default): final_score = 0.8 * lucene_score + 0.2 * math.log1p(upvotes)

## Templates

- search.html: Renders the search bar and ranking dropdown using Bootstrap  
- results.html: Displays the top 10 results in a styled list with title, URL, subreddit, author, and score
