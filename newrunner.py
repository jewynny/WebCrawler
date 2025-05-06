import json
import math
import os
import subprocess
import threading
import time
import signal
import sys

# Global Variables
NUM_THREADS = 8
OUTPUT_DIR = "final_outputs"
TEMP_DIR = "temp_runs"
SPIDER_NAME = "redditor"
VISITED_PATH = "visited_subreddits.jsonl"

# Create necessary directories if not already present
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

# Used to handle graceful shutdown on Ctrl+C
stop_signal_received = threading.Event()

def handle_interrupt(signal_received, frame):
    print("\n[!] KeyboardInterrupt received. Cleaning up...")
    stop_signal_received.set()

signal.signal(signal.SIGINT, handle_interrupt)

# Loads the set of already visited subreddits from a .jsonl file
def load_visited_subreddits(path=VISITED_PATH):
    visited = set()
    if os.path.exists(path):
        with open(path, "r") as f:
            for line in f:
                try:
                    sub = json.loads(line.strip())
                    if isinstance(sub, str):
                        visited.add(sub)
                except json.JSONDecodeError:
                    continue
    return visited

# Appends newly visited subreddits to the .jsonl file
def append_visited_subreddits(new_subs, path=VISITED_PATH):
    with open(path, "a") as f:
        for sub in sorted(new_subs):
            f.write(json.dumps(sub) + "\n")

# Loads the new subreddits list
def load_new_subreddits(path="new_subreddits.json"):
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

# Saves the updated new subreddits list (with already-visited ones removed)
def save_new_subreddits(subs, path="new_subreddits.json"):
    with open(path, "w") as f:
        json.dump(sorted(list(subs)), f)

# Writes temporary subfile for each thread to use as input
def write_temp_subfile(subreddits, thread_id):
    path = os.path.join(TEMP_DIR, f"subfile_{thread_id}.json")
    with open(path, "w") as f:
        json.dump(subreddits, f)
    return path

# Runs the crawler in a subprocess and handles temp output
def run_crawler(thread_id, subfile_path):
    temp_output = os.path.join(TEMP_DIR, f"output_{thread_id}.jsonl")
    final_output = os.path.join(OUTPUT_DIR, f"output_{thread_id}.jsonl")

    try:
        cmd = [
            "scrapy", "crawl", SPIDER_NAME,
            "-o", temp_output,
            "-a", f"subfile={subfile_path}"
        ]
        print(f"[Thread {thread_id}] Starting crawl...")
        subprocess.run(cmd, check=True)

        # If not interrupted, move temp output to final output
        if not stop_signal_received.is_set():
            print(f"[Thread {thread_id}] Completed. Appending to {final_output}")
            with open(temp_output, "r", encoding="utf-8") as tf, open(final_output, "a", encoding="utf-8") as ff:
                for line in tf:
                    ff.write(line)
        else:
            print(f"[Thread {thread_id}] Interrupted. Discarding temp output.")

    except subprocess.CalledProcessError:
        print(f"[Thread {thread_id}] Scrapy failed.")

    finally:
        # Cleanup temp files regardless of success or failure
        for f in [temp_output, subfile_path]:
            if os.path.exists(f):
                os.remove(f)

# Main loop that handles multi-threaded crawling
def main():
    print("[*] Starting threaded crawler...")
    visited_subs = load_visited_subreddits()

    while not stop_signal_received.is_set():
        all_subs = load_new_subreddits()

        # Filter out already visited subreddits
        to_crawl = [sub for sub in all_subs if sub not in visited_subs]

        if not to_crawl:
            print("[!] No subreddits to crawl. Sleeping 60s...")
            time.sleep(60)
            continue

        # Splits the remaining subreddits across NUM_THREADS
        chunk_size = math.ceil(len(to_crawl) / NUM_THREADS)
        chunks = [to_crawl[i:i + chunk_size] for i in range(0, len(to_crawl), chunk_size)]

        new_visited = set()
        threads = []

        for i, chunk in enumerate(chunks):
            subfile = write_temp_subfile(chunk, i)
            new_visited.update(chunk)
            t = threading.Thread(target=run_crawler, args=(i, subfile))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Append newly visited subs to jsonl log and update filtered state
        append_visited_subreddits(new_visited)
        visited_subs.update(new_visited)

        # Update the new_subreddits list by removing visited
        remaining_subs = [sub for sub in all_subs if sub not in visited_subs]
        save_new_subreddits(remaining_subs)

        print("[*] Crawl Cycle Complete. Restarting in 10s...\n")
        time.sleep(10)

    print("[x] Stopped")

if __name__ == "__main__":
    main()
