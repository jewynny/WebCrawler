"""
Continuously rerun your Scrapy spider into JSON-Lines
and write each run results as a one-item-per-line JSON array in `<subreddit>.json`.
Inside a designated output directory.
If interrupted (Ctrl+C), any partially written JSON-Lines will be saved as `<subreddit>_partial.json`.
"""

import subprocess
import time
import json
import os
import argparse
import sys

def run_scrapy(output_file: str):
    """
    Run the scrapy command, suppressing its own output,
    and write to output_file (full path).
    """
    cmd = ["scrapy", "crawl", "redditor", "-O", output_file]
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Starting crawl...")
    subprocess.run(cmd, check=True,
                   stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL)
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Crawl finished.")

def split_and_write(input_file: str, out_dir: str, partial=False):
    """
    Read JSON-Lines from input_file, group by item['subreddit'],
    and write each group as a one-item-per-line JSON array in <subreddit>.json.
    If partial=True, append '_partial' to each filename.
    """
    if not os.path.exists(input_file):
        print(f"  {input_file} not found, skipping split.")
        return

    suffix = "_partial" if partial else ""
    groups = {}
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            sub = obj.get("subreddit", "unknown")
            groups.setdefault(sub, []).append(obj)

    for sub, items in groups.items():
        fname = f"{sub}{suffix}.json"
        out_path = os.path.join(out_dir, fname)
        with open(out_path, 'w', encoding='utf-8') as fout:
            fout.write('[\n')
            for i, it in enumerate(items):
                line = json.dumps(it, ensure_ascii=False)
                fout.write(f"{line}" + (",\n" if i < len(items)-1 else "\n"))
            fout.write(']')
        print(f"  Wrote {len(items)} items to {out_path}")

def main(interval: int, out_dir: str):
    tmp_name = "temp.jl"
    tmp_path = os.path.join(out_dir, tmp_name)

    os.makedirs(out_dir, exist_ok=True)

    while True:
        try:
            run_scrapy(tmp_path)
            split_and_write(tmp_path, out_dir)
        except subprocess.CalledProcessError as e:
            print(f"  Scrapy exited with code {e.returncode}")
        except KeyboardInterrupt:
            print("\nInterrupted by user; saving partial results…")
            # If anything was written to tmp_path, split & save it as partial
            if os.path.exists(tmp_path):
                split_and_write(tmp_path, out_dir, partial=True)
                # clean up the temp file
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass
            print("Done. Exiting.")
            sys.exit(0)
        except Exception as e:
            print(f"  Unexpected error: {e}", file=sys.stderr)
        else:
            # Only delete the tmp file if we completed the run normally
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

        print(f"Sleeping for {interval} seconds…\n")
        time.sleep(interval)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Continuously run the 'redditor' spider into JSON-Lines and dump by-subreddit files."
    )
    parser.add_argument(
        "--interval", "-i", type=int, default=1,
        help="Seconds to wait between runs (default: 1)"
    )
    parser.add_argument(
        "--output-dir", "-o", type=str, default="data",
        help="Directory in which to place all JSON files (default: data)"
    )
    args = parser.parse_args()
    main(args.interval, args.output_dir)
