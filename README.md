# WebCrawler
A Scrapy-based Reddit crawler for continuously fetching subreddit posts and organizing output by subreddit. Includes a `run.py` script to automate crawling at regular intervals, handle interruptions gracefully, and store partial results.

## Features

* **`authors_spider.py`**: Scrapy spider that fetches posts from a specified subreddit using the Reddit JSON API.
* **`run.py`**: Wrapper script to continuously execute the spider, append each run in to single `*.jl` file, and save partial results on interruption.

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

* **Posts per Subreddit to crawl (`n_posts`)**: Number of hot posts to fetch per subreddit (default: `1000`, defined in `authors_spider.py`).
* **Submissions per Author to crawl (`n_submissions`)**: Number of newest submissions to fetch per author (default: `100`, defined in `authors_spider.py`).
* **Subreddit**: Modify the `subreddits_to_crawl` in `authors_spider.py` to target your desired subreddit(s) to start the crawling.
* **Output Directory**: By default, `run.py` writes JSON-line files into a folder named `data/`. Use the `-o` flag to change:

  ```bash
  python run.py -o path/to/output_dir
  ```
* **Output Filename**: Use `-f` flag to change the name of the main output file:

  ```bash
  python run.py -f output.jl
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

   * Save them into `{timestamp}_partial.jl` files in the output directory
   * On the next rerun, crawler will pick up new subreddits to explore on `new_subreddits.json`. Partial date 

## Output Files

* On successful runs: `data/output.jl` (JSON-line file)
* On interruption: `data/{timestamp}_partial.jl`



