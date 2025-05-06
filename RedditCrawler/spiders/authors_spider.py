import scrapy
import praw
import re
import json
import os

class RedditSpider(scrapy.Spider):
    # crawler name (to be used in `scrapy crawl [name] -O 'output.json'`)
    name = "redditor"
    # number of hot posts per subreddit
    n_posts = 1000
    # number of newest submissions per user (to find their submissions)
    n_submissions = 3

    # Information Required To Access Reddit
    def __init__(self, subfile=None, **kwargs):
        super().__init__(**kwargs)

        self.reddit = praw.Reddit(
            client_id="UNOl9Xj48ouJr9Lul6WbhQ",
            client_secret="VngShcJvHzj66J3chWlj-ZgMb7Q3Sg",
            user_agent="script:Crawler:1.0 (by u/Mean-Food8584)",
            username="Mean-Food8584",
            password="Hassan123*"
        )

        # Load subreddits from the temp file passed via -a subfile=...
        if subfile and os.path.exists(subfile):
            try:
                with open(subfile, "r") as f:
                    self.subreddits_to_crawl = json.load(f)
                    self.logger.info(f"Loaded {len(self.subreddits_to_crawl)} subreddits from {subfile}")
            except Exception as e:
                self.logger.warning(f"Couldn't load {subfile}: {e}")
                self.subreddits_to_crawl = ["AmItheAsshole"]
        else:
            # If no file provided or file is missing, fallback
            if os.path.exists("new_subreddits.json"):
                try:
                    with open("new_subreddits.json", "r") as f:
                        self.subreddits_to_crawl = json.load(f)
                        self.logger.info(f"Loaded {len(self.subreddits_to_crawl)} new_subreddits.json")
                except Exception as e:
                    self.logger.warning(f"Couldn't load new_subreddits.json: {e}")
                    self.subreddits_to_crawl = ["AmItheAsshole"]
            else:
                self.subreddits_to_crawl = ["AmItheAsshole"]

        # Stores Post Temp
        self.collected_items = []     
        # Tracks All Unique Authors
        self.unique_authors = set()   
        # Indicator When Intially Subreddit Is Finished Crawling
        self.crawling_done = False   

        self.visited_map = {}
        if os.path.exists("visited_authors.json"):   
            try:
                with open("visited_authors.json", "r") as f:
                    content = f.read().strip()
                    if content:
                        self.visited_map = json.loads(content)
            except Exception as e:
                self.logger.warning(f"Couldn't load visited_authors.json: {e}")
                self.visited_map = {}

        # Tracks Visit Subreddits, Later To Push To File
        self.visited_subreddits = set()
        if os.path.exists("visited_subreddits.json"):
            try:
                with open("visited_subreddits.json", "r") as f:
                    self.visited_subreddits = set(json.load(f))
            except Exception as e:
                self.logger.warning(f"Couldn't load visited_subreddits.json: {e}")

        self.visited_authors = set(self.visited_map.keys())
        self.new_subreddits = set()

    # Goes Through Post Body And Extracts Link That Starts With Https
    def extract_all_links(self, text):
        # Only Extract Real Links From Markdown
        return re.findall(r'\[.*?\]\((https?://\S+?)\)', text)

    # Initalizes Set To Track Subreddit Visited
    def start_requests(self):
        for sub_name in self.subreddits_to_crawl:
            self.visited_subreddits.add(sub_name)
            subreddit = self.reddit.subreddit(sub_name)
            seen_ids = set()

            # Grabs The Number Of Posts Specified
            for post in subreddit.top(limit=3, time_filter='all'):
                # Checks If Subreddit Has Been Visited Or not
                if post.id in seen_ids:
                    continue
                seen_ids.add(post.id)

                # Information Logged From Each Post
                self.logger.info(f"Title: {post.title}")
                item = {
                    "subreddit": post.subreddit.display_name,
                    "title": post.title,
                    "author": post.author.name if post.author else None,
                    "id": post.id,
                    "score": post.score,
                    "url": post.url,
                    "selftext": post.selftext,
                }

                all_links = self.extract_all_links(post.selftext)
                if all_links:
                    # List All URLs
                    item["inner_urls"] = all_links  

                # Tracks Unique Authors 
                if item["author"]:
                    self.unique_authors.add(item["author"])

                # Collect Item, To Later Append When We Visit Author Posts
                self.collected_items.append(item)

        # Inital Subreddit Done
        self.crawling_done = True
        yield from self.next_request()

    # Fetch Author Post History And Obtains Item
    def next_request(self):
        author_sub_map = {}

        for author in self.unique_authors:
            try:
                # Skip Authors If In Visited Section
                if author in self.visited_map:
                    author_sub_map[author] = self.visited_map[author]
                    continue

                # Fetch Their Recent Submission
                submissions = self.reddit.redditor(author).submissions.new(limit=self.n_submissions)
                subreddits = [s.subreddit.display_name for s in submissions]

                # Collect new subreddits not yet crawled or queued
                for sub in subreddits:
                    if sub not in self.visited_subreddits and sub not in self.new_subreddits:
                        self.new_subreddits.add(sub)

                # Save In Memory And In Visited Map
                author_sub_map[author] = subreddits
                self.visited_map[author] = subreddits

            # Incase Error Occurs
            except Exception as e:
                self.logger.warning(f"Couldn't Fetch Posts For Author {author}: {e}")
                author_sub_map[author] = []
                self.visited_map[author] = []

        # Updates Output Json Files
        for item in self.collected_items:
            author = item.get("author")
            if author and author in author_sub_map:
                item["author_recent_subreddits"] = author_sub_map[author]
            else:
                item["author_recent_subreddits"] = []

            yield item

        # Append Visited Authors to visited_authors.jsonl
        try:
            with open("visited_authors.jsonl", "a") as f:
                for author, subs in self.visited_map.items():
                    line = json.dumps({"author": author, "subreddits": subs})
                    f.write(line + "\n")
            self.logger.info("Appended to visited_authors.jsonl")
        except Exception as e:
            self.logger.warning(f"Failed to append visited_authors.jsonl: {e}")

        # Append Visited Subreddits to visited_subreddits.jsonl
        try:
            with open("visited_subreddits.jsonl", "a") as f:
                for sub in self.visited_subreddits:
                    f.write(json.dumps(sub) + "\n")
            self.logger.info("Appended to visited_subreddits.jsonl")
        except Exception as e:
            self.logger.warning(f"Failed to append visited_subreddits.jsonl: {e}")


        # Save Newly Discovered Subreddits To File
        try:
            with open("new_subreddits.json", "w") as f:
                json.dump(sorted(list(self.new_subreddits)), f, indent=2)
            self.logger.info("New Subreddits Saved")
        except Exception as e:
            self.logger.warning(f"Failed To Save: {e}")
