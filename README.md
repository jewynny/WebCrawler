# WebCrawler

A multi-threaded Scrapy-based Reddit crawler that continuously fetches subreddit posts, crawls authors' recent submissions, and manages output in a threaded pipeline.

## Features

* **`authors_spider.py`**: Scrapy spider (`redditor`) that:

  * Fetches top posts from each subreddit (default `n_posts = 1000`).
  * Extracts post data (`subreddit`, `title`, `author`, `id`, `score`, `url`, `selftext`, `inner_urls`).
  * Tracks unique authors and fetches their recent submissions (default `n_submissions = 3`).
  * Maintains `visited_authors.jsonl` and `visited_subreddits.jsonl` for incremental crawling.
  * Saves newly discovered subreddits to `new_subreddits.json`.

* **`multi_thread_runner.py`**: Orchestrates multi-threaded crawling:

  * Splits the subreddit list (from `new_subreddits.json`) into `NUM_THREADS` chunks.
  * Writes sublists to `temp/temp_subreddits_{index}.json`.
  * Runs multiple `redditor` spider instances in parallel, each outputting to `temp/output_{index}.jsonl`.
  * Merges thread outputs into `final/output_{index}.jsonl`.
  * Handles `Ctrl+C` gracefully: cleans up temp files on interruption.

## Repository Structure

```
WebCrawler/
├── scrapy.cfg                  # Scrapy project config
├── multi_thread_runner.py      # Multi-threaded crawl orchestrator
└── RedditCrawler/
    └── spiders/
        └── authors_spider.py   # Spider implementation
```

## Prerequisites

```bash
pip install scrapy praw
```

## Configuration

* **Threads (`NUM_THREADS`)**: Number of parallel spider instances (default `8`, defined in `multi_thread_runner.py`).
* **Temporary Directory (`TEMP_DIR`)**: Directory for intermediate JSONL outputs (default `temp`).
* **Final Directory (`FINAL_DIR`)**: Directory for merged outputs (default `final`).
* **Posts per Subreddit (`n_posts`)**: Number of top posts to fetch per subreddit (default `1000`, defined in `authors_spider.py`).
* **Submissions per Author (`n_submissions`)**: Number of recent submissions to fetch per author (default `3`, defined in `authors_spider.py`).
* **Subreddit Seed File**: Use `new_subreddits.json` to seed the initial list of subreddits. The spider will also update this file with newly discovered subreddits.
* **Visited Maps**: `visited_authors.jsonl` and `visited_subreddits.jsonl` track already crawled authors and subreddits to avoid reprocessing.

## Usage

1. **Seed initial subreddits** (optional):

   ```bash
   echo '["subreddit1","subreddit2"]' > new_subreddits.json
   ```

2. **Run the crawler**:

   ```bash
   python multi_thread_runner.py
   ```

3. **Interrupt & Recover**: Press `Ctrl+C` to stop. Temporary files in `temp/` will be cleaned up, and all finalized outputs remain in `final/`.

## Output Files

* **Intermediate**: `temp/output_{index}.jsonl` for each thread.
* **Final**: `final/output_{index}.jsonl` combining each thread's results.
