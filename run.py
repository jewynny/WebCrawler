"""
Continuously rerun your Scrapy spider into JSON-Lines
and write each run results as a JSON-line file `output.jl`.
Inside a designated output directory.
If interrupted (Ctrl+C), any partially written JSON-Lines will be saved as `{timestamp}_partial.jl`.
"""

import subprocess
import time
import os
import argparse
import sys

def run_scrapy(temp_path: str):
    """
    Run the scrapy command, suppressing its own output,
    and write to temp_path.
    """
    cmd = ["scrapy", "crawl", "redditor", "-O", temp_path]
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Starting crawl...")
    subprocess.run(cmd, check=True)
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Crawl finished.")

def append_to_main(temp_path: str, main_path: str):
    """
    Append contents of temp_path to main_path and remove temp_path.
    """
    with open(temp_path, 'r') as src, open(main_path, 'a') as dst:
        for line in src:
            dst.write(line)
    os.remove(temp_path)
    print(f"  Appended crawl output to {main_path}")

def save_partial(temp_path: str, out_dir: str):
    """
    Move temp_path to a timestamped partial file in out_dir.
    """
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    filename = f"{timestamp}_partial.jl"
    dest = os.path.join(out_dir, filename)
    os.replace(temp_path, dest)
    print(f"  Saved partial crawl output to {dest}")

def main(interval: int, out_dir: str, main_filename: str):
    os.makedirs(out_dir, exist_ok=True)
    temp_name = "temp.jl"
    temp_path = os.path.join(out_dir, temp_name)
    main_file = os.path.join(out_dir, main_filename)

    while True:
        try:
            run_scrapy(temp_path)
            append_to_main(temp_path, main_file)
        except subprocess.CalledProcessError as e:
            print(f"  Scrapy exited with code {e.returncode}")
        except KeyboardInterrupt:
            print("\nInterrupted by user; saving partial results...")
            if os.path.exists(temp_path):
                save_partial(temp_path, out_dir)
            print("Done. Exiting.")
            sys.exit(0)
        except Exception as e:
            print(f"  Unexpected error: {e}", file=sys.stderr)

        print(f"Sleeping for {interval} seconds...\n")
        time.sleep(interval)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Continuously run the 'redditor' spider and save each run as its own file."
    )
    parser.add_argument(
        "--interval", "-i", type=int, default=1,
        help="Seconds to wait between runs (default: 1)"
    )
    parser.add_argument(
        "--output-dir", "-o", type=str, default="data",
        help="Directory in which to place all run files (default: data)"
    )
    parser.add_argument(
        "--output-file", "-f", type=str, default="output.jl",
        help="Name of the main output file in output-dir (default: output.jl)"
    )
    args = parser.parse_args()
    main(args.interval, args.output_dir, args.output_file)
