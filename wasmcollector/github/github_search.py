from utils.config import config

import os
import json
import time
from github import Github

# Load GitHub API key
GITHUB_KEY = os.getenv("GITHUB_KEY")
if not GITHUB_KEY:
    raise EnvironmentError("GITHUB_KEY environment variable not set")

g = Github(GITHUB_KEY)

STATE_FILE_TEMPLATE = "states/github/state_{key}.json"
OUTPUT_FILE_TEMPLATE = "results/github/results_{key}.json"

def load_state(key):
    """Load the last state for resuming if the script is interrupted."""
    state_file = STATE_FILE_TEMPLATE.format(key=key)
    if os.path.exists(state_file):
        with open(state_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"page": 1, "results_count": 0}

def save_state(key, page, results_count):
    """Save the current state for resuming later."""
    state_file = STATE_FILE_TEMPLATE.format(key=key)
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump({"page": page, "results_count": results_count}, f)

def save_results(key, results):
    """Save the fetched results to a JSON file incrementally."""
    output_file = OUTPUT_FILE_TEMPLATE.format(key=key)
    if not os.path.exists(output_file):
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump([], f)

    with open(output_file, "r+", encoding="utf-8") as f:
        existing_data = json.load(f)
        f.seek(0)
        json.dump(existing_data + results, f, indent=2)
        f.truncate()

def search_repos(query, key, per_page=100, max_results=1000):
    """Search repositories and save results incrementally."""
    state = load_state(key)
    page = state["page"]
    results_count = state["results_count"]

    print(f"Resuming from page {page} ({key}), total results so far: {results_count}")

    while results_count < max_results:
        print(f"Fetching page {page} for {key}...")
        try:
            repos = g.search_repositories(query=query, sort=key, order="desc")
            page_results = repos.get_page(page - 1)  # PyGithub uses zero-based indexing
        except Exception as e:
            print(f"Error fetching page {page} for {key}: {e}")
            time.sleep(10)
            continue  # Retry the same page

        if not page_results:
            print(f"No more results for {key}. Exiting.")
            break

        # Save results incrementally
        save_results(key, [repo.raw_data for repo in page_results])

        results_count += len(page_results)
        print(f"Fetched {len(page_results)} repositories on page {page} for {key}. Total so far: {results_count}")

        # Save state after processing each page
        save_state(key, page + 1, results_count)

        page += 1
        time.sleep(1)  # To avoid rate-limiting

    print(f"Finished fetching all results for {key}. Total: {results_count}")
    return results_count

def workflow():
    query = config['GITHUB']['KEYWORD']
    sorting_keys = config['GITHUB']['SORTLIST']  # Add more keys if needed

    for key in sorting_keys:
        print(f"Starting search for {key}...")
        search_repos(query, key)

if __name__ == "__main__":
    workflow()