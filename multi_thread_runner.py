import json
import math
import subprocess
import threading
import os
import time
import signal
import sys

# Global Varaibles
NUM_THREADS = 8
TEMP_DIR = "temp"
FINAL_DIR = "final"

# Creates Directories Based on Temp / Final
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(FINAL_DIR, exist_ok=True)

# Used to Handle Ctrl+C Interruptions
stop_signal_received = threading.Event()

# Triggered When User Presses Ctrl+C
def handle_interrupt(signal_received, frame):
    print("\n[!] KeyboardInterrupt received. Cleaning up temp files...")
    stop_signal_received.set()

signal.signal(signal.SIGINT, handle_interrupt)

# Deletes All Temp Output and Subreddit Files
def cleanup_temp_outputs():
    for fname in os.listdir(TEMP_DIR):
        if fname.endswith(".jsonl") or fname.startswith("temp_subreddits_"):
            try:
                os.remove(os.path.join(TEMP_DIR, fname))
                print(f"[x] Deleted: {fname}")
            except Exception as e:
                print(f"[!] Failed to remove {fname}: {e}")

# Attempts To Load The New_Subbredit File
def load_and_split_subreddits(path="new_subreddits.json"):
    if not os.path.exists(path):
        print("[WARNING] new_subreddits.json not found. Running default scraper.")
        return None
    # File Doesnt Exisit Return None
    with open(path, "r") as f:
        try:
            all_subreddits = json.load(f)
            # Tries To Parse The File
        except json.JSONDecodeError:
            print("[WARNING] new_subreddits.json is not valid JSON. Running default scraper.")
            return None
    # If Invalid File Return None
    if not isinstance(all_subreddits, list) or len(all_subreddits) == 0:
        print("[WARNING] new_subreddits.json is empty or not a list. Running default scraper.")
        return None

    # Splits The Entire To Visit File To Smaller Files For Each Thread
    chunk_size = math.ceil(len(all_subreddits) / NUM_THREADS)
    return [all_subreddits[i:i + chunk_size] for i in range(0, len(all_subreddits), chunk_size)]

# For Each Thread We Make It A File With The Subreddits That It Needs To Run
def write_temp_file(subreddits, index):
    filename = os.path.join(TEMP_DIR, f"temp_subreddits_{index}.json")
    with open(filename, "w") as f:
        json.dump(subreddits, f)
    return filename

# Only Runs This If Temp Ouput File Exisit
def move_to_final_output(output_file, index):
    if not os.path.exists(output_file):
        return

    # Final Location For The Data
    final_path = os.path.join(FINAL_DIR, f"output_{index}.jsonl")

    # Appends The Lines From Temp To Final
    with open(output_file, "r") as f_in, open(final_path, "a") as f_out:
        for line in f_in:
            try:
                data = json.loads(line)
                f_out.write(json.dumps(data) + "\n")
            except json.JSONDecodeError:
                continue

    # Deletes Temp After
    os.remove(output_file)

# Runs The Scrapy Crawler
def run_crawler(index, temp_file=None):
    output_file = os.path.join(TEMP_DIR, f"output_{index}.jsonl")
    if temp_file:
        cmd = ["scrapy", "crawl", "redditor", "-o", output_file, "-a", f"subfile={temp_file}"]
    else:
        cmd = ["scrapy", "crawl", "redditor", "-o", output_file]

    subprocess.run(cmd)
    # We no longer push to final here; we delay it until all threads finish

# Infinitely Runs The Thread When They Finish, Only Happens When All Threads Finish
def thread_loop():
    try:
        while not stop_signal_received.is_set():

            # Splits The Total Subreddit File List
            subreddit_chunks = load_and_split_subreddits()
            threads = []

            # If No Subreddit IS Avaliable Run Default Option
            if subreddit_chunks is None:
                t = threading.Thread(target=run_crawler, args=(0,))
                threads.append(t)
                t.start()
                # Runs The Split Up Verision
            else:
                for i, chunk in enumerate(subreddit_chunks):
                    temp_file = write_temp_file(chunk, i)
                    t = threading.Thread(target=run_crawler, args=(i, temp_file))
                    threads.append(t)
                    t.start()

            # Joins The Threads Together
            for t in threads:
                t.join()

            # Once All Threads Are Done, Then Push Temp Outputs to Final
            for i in range(len(threads)):
                output_file = os.path.join(TEMP_DIR, f"output_{i}.jsonl")
                move_to_final_output(output_file, i)

            print("All threads finished. Sleeping before next round...\n")
            time.sleep(5)

    # If Interrupted, We Delete All Remaining Temp Files
    finally:
        if stop_signal_received.is_set():
            cleanup_temp_outputs()
            print("[x] Cleanup complete. Temp files deleted.")

def main():
    thread_loop()

if __name__ == "__main__":
    main()
