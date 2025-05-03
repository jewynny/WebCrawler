import scrapy
import praw
import re

# Used To Track Visited Items
import json
import os

class RedditSpider(scrapy.Spider):
    name = "redditor"

    # Information Required To Access Reddit
    def __init__(self):
        self.reddit = praw.Reddit(
            client_id="UNOl9Xj48ouJr9Lul6WbhQ",
            client_secret="VngShcJvHzj66J3chWlj-ZgMb7Q3Sg",
            user_agent="script:Crawler:1.0 (by u/Mean-Food8584)",
            username="Mean-Food8584",
            password="Hassan123*"
        )

        # Load Subreddit From new_subreddits.json if it exists
        if os.path.exists("new_subreddits.json"):
            try:
                with open("new_subreddits.json", "r") as f:
                    self.subreddits_to_crawl = json.load(f)
                    self.logger.info(f"Loaded {len(self.subreddits_to_crawl)} new_subreddits.json")
            except Exception as e:
                self.logger.warning(f"Couldn't load new_subreddits.json: {e}")
                self.subreddits_to_crawl = ["AmItheAsshole"]
        else:
            # If No File start With This
            self.subreddits_to_crawl = ["AmItheAsshole"]

        # Subreddits That Need To Be Crawled
        #self.subreddits_to_crawl = [
            #"AmItheAsshole",
            # "todayilearned",
            # "AskReddit",
            # "funny",
            # "worldnews",
            # "gaming",
            # "technology",
            # "interestingasfuck",
            # "NoStupidQuestions",
            #"janellesuckshassanroc"
        #]

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

        self.visited_authors = set(self.subreddits_to_crawl)
        for sublist in self.visited_map.values():
            self.visited_authors.update(sublist)

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
            for post in subreddit.hot(limit=2):
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
                submissions = self.reddit.redditor(author).submissions.new(limit=5)
                subreddits = [s.subreddit.display_name for s in submissions]

                # Collect new subreddits not yet crawled
                for sub in subreddits:
                    if sub not in self.visited_authors:
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

        # Updates Visited Authors Json File
        try:
            with open("visited_authors.json", "w") as f:
                json.dump(self.visited_map, f, indent=2)
            self.logger.info("Saved Successfully.")
        except Exception as e:
            self.logger.warning(f"Failed To Save: {e}")

        # Updated Visited Subreddit File
        try:
            with open("visited_subreddits.json", "w") as f:
                json.dump(sorted(list(self.visited_subreddits)), f, indent=2)
            self.logger.info("Saved visited_subreddits.json")
        except Exception as e:
            self.logger.warning(f"Failed to save visited_subreddits.json: {e}")

        # Save Newly Discovered Subreddits To File
        try:
            with open("new_subreddits.json", "w") as f:
                json.dump(sorted(list(self.new_subreddits)), f, indent=2)
            self.logger.info("New Subreddits Saved")
        except Exception as e:
            self.logger.warning(f"Failed To Save: {e}")
