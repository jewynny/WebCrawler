# WebCrawler
## Requirements

```bash
pip install scrapy
pip install praw
```

## Usage

To continuously run scraper:
```bash
python run.py
```

To run scraper once:
```bash
scrapy crawl redditor -O 'output.json'
```