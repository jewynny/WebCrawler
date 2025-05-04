# WebCrawler
A Scrapy-based Reddit crawler for continuously fetching subreddit posts and organizing output by subreddit. Includes a `run.py` script to automate crawling at regular intervals, handle interruptions gracefully, and store partial results.

## Features

* **`authors_spider.py`**: Scrapy spider that fetches posts from a specified subreddit using the Reddit JSON API.
* **`run.py`**: Wrapper script to continuously execute the spider, suppress its console output, split output into per-subreddit files, and save partial results on interruption.

## Repository Structure

```
WebCrawler/
├── scrapy.cfg                # Scrapy project config
├── run.py                    # Continuous crawl orchestration
└── RedditCrawler/            # Scrapy project folder
    └── spiders/
        └── authors_spider.py # Spider implementation
```

## Prerequisites

```bash
pip install scrapy
pip install praw
```

## Configuration

* **Posts per Subreddit to crawl (`n_posts`)**: Number of hot posts to fetch per subreddit (default: `10`, defined in `authors_spider.py`).
* **Submissions per Author to crawl (`n_submissions`)**: Number of newest submissions to fetch per author (default: `5`, defined in `authors_spider.py`).
* **Subreddit**: Modify the `subreddits_to_crawl` in `authors_spider.py` to target your desired subreddit(s) to start the crawling.
* **Output Directory**: By default, `run.py` writes JSON files into a folder named `data/`. Use the `-o` flag to change:

  ```bash
  python run.py -o path/to/output_dir
  ```
* **Interval**: Control the delay between successive crawls (in seconds) with the `-i` flag (default `1` second):

  ```bash
  python run.py -i 10
  ```

## Usage

1. **To run scraper once**:
```bash
scrapy crawl redditor -O 'output.json'
```

2. **To continuously run scraper**:
```bash
python run.py
```

3. **Interrupt & Recover**: Press `Ctrl+C` during a crawl run; the script will:

   * Split any scraped items in progress
   * Save them into `<subreddit>_partial.json` files in the output directory
   * Exit cleanly without losing data

## Output Files

* On successful runs: `data/<subreddit>.json` (one-item-per-line JSON array)
* On interruption: `data/<subreddit>_partial.json`



