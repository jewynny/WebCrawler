import scrapy
import praw
import re
import json
import os

class RedditSpider(scrapy.Spider):
    name = "redditor"
    n_posts = 1000

    def __init__(self, subfile=None, **kwargs):
        super().__init__(**kwargs)

        self.reddit = praw.Reddit(
            client_id="UNOl9Xj48ouJr9Lul6WbhQ",
            client_secret="VngShcJvHzj66J3chWlj-ZgMb7Q3Sg",
            user_agent="script:Crawler:1.0 (by u/Mean-Food8584)",
            username="Mean-Food8584",
            password="Hassan123*"
        )

        if subfile and os.path.exists(subfile):
            try:
                with open(subfile, "r") as f:
                    self.subreddits_to_crawl = json.load(f)
            except Exception as e:
                self.logger.warning(f"Couldn't load {subfile}: {e}")
                self.subreddits_to_crawl = ["AmItheAsshole"]
        elif os.path.exists("new_subreddits.json"):
            try:
                with open("new_subreddits.json", "r") as f:
                    self.subreddits_to_crawl = json.load(f)
            except Exception as e:
                self.logger.warning(f"Couldn't load new_subreddits.json: {e}")
                self.subreddits_to_crawl = ["AmItheAsshole"]
        else:
            self.subreddits_to_crawl = ["AmItheAsshole"]

    def extract_all_links(self, text):
        return re.findall(r'\[.*?\]\((https?://\S+?)\)', text)

    def start_requests(self):
        for sub_name in self.subreddits_to_crawl:
            subreddit = self.reddit.subreddit(sub_name)
            seen_ids = set()

            for post in subreddit.hot(limit=self.n_posts):
                if post.id in seen_ids:
                    continue
                seen_ids.add(post.id)

                item = {
                    "subreddit": post.subreddit.display_name,
                    "title": post.title,
                    "id": post.id,
                    "score": post.score,
                    "url": post.url,
                    "selftext": post.selftext,
                }

                all_links = self.extract_all_links(post.selftext)
                if all_links:
                    item["inner_urls"] = all_links

                yield item
