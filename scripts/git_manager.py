import os
import git
import gitlab
from git import Repo

class GitManager:
    def __init__(self, repo_url, repo_path, token, gitlab_url):
        self.repo_url = repo_url
        self.repo_path = repo_path
        self.token = token
        self.gitlab_url = gitlab_url
        self.gl = gitlab.Gitlab(url=gitlab_url, private_token=token)

    def set_git_config(self, user_name, user_email):
        repo = Repo.init(self.repo_path)
        with repo.config_writer() as git_config:
            git_config.set_value('user', 'email', user_email)
            git_config.set_value('user', 'name', user_name)

    def clone_repo(self):
        if os.path.exists(self.repo_path):
            print(f"Repo path {self.repo_path} exists. Pulling latest...")
            repo = Repo(self.repo_path)
            # Update remote URL with token if provided (to handle token rotation/updates)
            if self.token and "oauth2" not in self.repo_url and "://" in self.repo_url:
                auth_url = self.repo_url.replace("://", f"://oauth2:{self.token}@", 1)
                repo.git.remote("set-url", "origin", auth_url)
            repo.remotes.origin.pull()
        else:
            # Inject token into URL for authentication
            auth_url = self.repo_url
            if self.token and "oauth2" not in self.repo_url and "://" in self.repo_url:
                auth_url = self.repo_url.replace("://", f"://oauth2:{self.token}@", 1)

            print(f"Cloning repo to {self.repo_path}...")
            Repo.clone_from(auth_url, self.repo_path)
        return Repo(self.repo_path)

    def create_branch(self, branch_name):
        repo = Repo(self.repo_path)
        current = repo.active_branch
        print(f"Current branch: {current.name}")

        try:
            new_branch = repo.create_head(branch_name)
            new_branch.checkout()
            print(f"Switched to new branch: {branch_name}")
        except OSError:
             print(f"Branch {branch_name} might already exist. Checking out...")
             repo.git.checkout(branch_name)

    def commit_changes(self, message):
        repo = Repo(self.repo_path)
        if repo.is_dirty(untracked_files=True):
            repo.git.add(A=True)
            repo.index.commit(message)
            print(f"Committed changes with message: {message}")
        else:
            print("No changes to commit.")

    def push_changes(self, branch_name):
        repo = Repo(self.repo_path)
        origin = repo.remote(name='origin')
        origin.push(branch_name)
        print(f"Pushed branch {branch_name} to origin.")

    def create_merge_request(self, project_id, source_branch, target_branch, title):
        project = self.gl.projects.get(project_id)
        mr = project.mergerequests.create({
            'source_branch': source_branch,
            'target_branch': target_branch,
            'title': title
        })
        print(f"Merge Request created: {mr.web_url}")
        return mr.web_url

import argparse
import sys

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Git Manager CLI")
    parser.add_argument("action", choices=["clone", "push", "mr"], help="Action to perform")
    parser.add_argument("--repo-url", help="Repository URL")
    parser.add_argument("--repo-path", help="Local repository path")
    parser.add_argument("--token", help="GitLab Token")
    parser.add_argument("--gitlab-url", help="GitLab URL")
    parser.add_argument("--branch", help="Branch name")
    parser.add_argument("--user-name", help="Git User Name")
    parser.add_argument("--user-email", help="Git User Email")
    parser.add_argument("--message", help="Commit message")
    parser.add_argument("--project-id", help="GitLab Project ID")
    parser.add_argument("--target-branch", default="main", help="Target branch for MR")
    parser.add_argument("--title", help="MR Title")

    args = parser.parse_args()

    # Environment variable fallback
    token = args.token or os.environ.get("GITLAB_TOKEN")
    gitlab_url = args.gitlab_url or os.environ.get("GITLAB_URL")
    repo_url = args.repo_url or os.environ.get("REPO_URL")

    if not token or not gitlab_url:
        print("Error: GITLAB_TOKEN and GITLAB_URL must be provided.")
        sys.exit(1)

    manager = GitManager(repo_url, args.repo_path, token, gitlab_url)

    if args.action == "clone":
        if args.user_name and args.user_email:
            manager.set_git_config(args.user_name, args.user_email)
        manager.clone_repo()
        if args.branch:
            manager.create_branch(args.branch)

    elif args.action == "push":
        if not args.message:
            print("Error: --message is required for push action")
            sys.exit(1)
        manager.commit_changes(args.message)
        if args.branch:
            manager.push_changes(args.branch)

    elif args.action == "mr":
        if not args.project_id or not args.branch or not args.title:
            print("Error: --project-id, --branch, and --title are required for mr action")
            sys.exit(1)
        manager.create_merge_request(args.project_id, args.branch, args.target_branch, args.title)
