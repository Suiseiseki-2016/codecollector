import os
from git import Repo, GitCommandError

# Read the repository list from the file
with open('./results/github/merged_repos.txt', 'r') as file:
    repos = file.read().strip().splitlines()

# Initialize counter
i = 0

# Loop through the repository list
for repo in repos:
    i += 1
    print(f"Cloning {repo} (#{i})...")

    # Clean the repository URL (optional, if annotations exist in the file)
    repo = repo.split(' ')[0]  # Remove anything after a space, e.g., "https://... (49402 stars)"

    # Extract username
    try:
        user = repo.split('/')[3]
    except IndexError:
        print(f"Invalid repository URL: {repo}. Skipping...")
        continue

    # Create user directory
    user_dir = os.path.join('repos', user)
    os.makedirs(user_dir, exist_ok=True)

    # Extract repository name
    repo_name = repo.split('/')[-1].replace('.git', '')  # Remove ".git" from the name
    target_path = os.path.join(user_dir, repo_name)

    # Clone the repository if not already cloned
    if not os.path.exists(target_path):
        try:
            Repo.clone_from(repo, target_path, depth=1)
        except GitCommandError as e:
            print(f"Error cloning {repo}: {e}")
    else:
        print(f"Repository {repo_name} already exists. Skipping...")

print("All repositories cloned.")