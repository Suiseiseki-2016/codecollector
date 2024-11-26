#!/usr/bin/env python3
import os
import json
from glob import glob
from collections import Counter

def merge_and_deduplicate_json(input_pattern, output_json, output_txt):
    """
    Merge JSON files matching input_pattern, deduplicate entries by repository URL,
    and save sorted results by stargazers_count.
    """
    all_repos = Counter()
    lists = {}

    # Process all JSON files matching the input pattern
    for path in sorted(glob(input_pattern)):
        list_id = os.path.basename(path).split('.')[0]
        print(f"Processing {list_id}...")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Collect repository full_name, URL, and stargazers_count
        name_url_stars = [(d["full_name"], d["clone_url"], d["stargazers_count"]) for d in data]
        print(f"Top 10 from {list_id}: {name_url_stars[:10]}")

        # Add repositories to the global counter
        for name, url, stars in name_url_stars:
            all_repos[url] = max(all_repos[url], stars)  # Use the maximum stars if duplicates exist

        # Save the list of full names for comparison
        lists[list_id] = [d["full_name"] for d in data]

    # Sort all repositories by stargazers_count
    sorted_repos = all_repos.most_common()

    # Save to JSON
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump({url: stars for url, stars in sorted_repos}, f, indent=2)

    # Save to TXT
    with open(output_txt, "w", encoding="utf-8") as f:
        for url, stars in sorted_repos:
            f.write(f"{url} ({stars} stars)\n")

    print(f"Merged {len(all_repos)} repositories. Results saved to {output_json} and {output_txt}.")

if __name__ == "__main__":
    # Define input pattern and output files
    input_pattern = "results/github/results_*.json"  # Adjust the pattern if necessary
    output_json = "results/github/merged_repos.json"
    output_txt = "results/github/merged_repos.txt"

    merge_and_deduplicate_json(input_pattern, output_json, output_txt)