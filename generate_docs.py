import os
import re
import shutil
import subprocess
import sys

import toml


MD_ANCHOR_LINKS = r"\[(.+)\]\(#.+\)"

def find_file(directory, filename):
    """Find a file in the given directory regardless of case."""
    lower_filename = filename.lower()
    for file in os.listdir(directory):
        if file.lower() == lower_filename:
            return file  # Return the correctly-cased filename
    return None  # File not found

def slugify(s):
    """
    From: http://blog.dolphm.com/slugify-a-string-in-python/

    Simplifies ugly strings into something URL-friendly.
    >>> print slugify("[Some] _ Article's Title--")
    some-articles-title
    """
    s = s.lower()
    for c in [' ', '-', '.', '/']:
        s = s.replace(c, '_')
    s = re.sub('\W', '', s)
    s = s.replace('_', ' ')
    s = re.sub('\s+', ' ', s)
    s = s.strip()
    return s.replace(' ', '-')

# Store errors to print them at the end.
errors = []

class Theme(object):
    def __init__(self, name, path):
        print("Loading %s" % name)
        self.name = name
        self.path = path

        try:
            with open(os.path.join(self.path, "theme.toml")) as f:
                self.metadata = toml.load(f)
        except Exception as e:
            error_message = f"Theme '{self.name}' encountered a TOML parsing issue: {str(e)}"
            errors.append(error_message)
            self.metadata = None
            return  # exit the constructor early


        with open(os.path.join(self.path, find_file(self.path, "README.md"))) as f:
            self.readme = f.read()
            self.readme = self.readme.replace("{{", "{{/*").replace("}}", "*/}}").replace("{%", "{%/*").replace("%}", "*/%}")
            self.readme = re.sub(MD_ANCHOR_LINKS, r"\1", self.readme)
        self.repository = self.get_repository_url()
        self.initial_commit_date, self.last_commit_date = self.get_commit_dates()

    def get_repository_url(self):
        command = "git -C {} remote -v".format(self.path)
        (_, git_remotes) = subprocess.getstatusoutput(command)
        cleaned = (
            git_remotes
            .split("\n")[0]
            .split("\t")[1]
            .replace(" (fetch)", "")
        )
        if cleaned.startswith("git@"):
            cleaned = cleaned.replace("git@github.com:", "https://github.com/").replace(".git", "")
        return cleaned

    def get_commit_dates(self):
        command = f'git -C {self.name} log --reverse --format=%aI'
        (_, date) = subprocess.getstatusoutput(command)
        dates = date.split("\n")

        # last, first
        return dates[0], dates[len(dates) - 1]

    def to_zola_content(self):
        """
        Returns the page content for Zola
        """
        return """
+++
title = "{title}"
description = "{description}"
template = "theme.html"
date = {updated}

[taxonomies]
theme-tags = {tags}

[extra]
created = {created}
updated = {updated}
repository = "{repository}"
homepage = "{homepage}"
minimum_version = "{min_version}"
license = "{license}"
demo = "{demo}"

[extra.author]
name = "{author_name}"
homepage = "{author_homepage}"
+++        

{readme}
        """.format(
            title=self.metadata["name"],
            description=self.metadata["description"],
            created=self.initial_commit_date,
            updated=self.last_commit_date,
            repository=self.repository,
            homepage=self.metadata.get("homepage", self.repository),
            min_version=self.metadata["min_version"],
            license=self.metadata["license"],
            tags=self.metadata.get("tags", "[]"),
            author_name=self.metadata["author"]["name"],
            author_homepage=self.metadata["author"].get("homepage", ""),
            demo=self.metadata.get("demo", ""),
            readme=self.readme,
        )

    def to_zola_folder(self, container):
        """
        Creates the page folder containing the screenshot and the info in
        content/themes
        """
        page_dir = os.path.join(container, self.name)
        os.makedirs(page_dir)

        with open(os.path.join(page_dir, "index.md"), "w") as f:
            print("Writing theme info as zola content: {}".format(self.name))
            f.write(self.to_zola_content())

        shutil.copyfile(
            os.path.join(self.path, find_file(self.path, "screenshot.png")),
            os.path.join(page_dir, "screenshot.png"),
        )


def read_themes():
    base = "./"
    themes = []

    for item in sorted(os.listdir(base)):
        full_path = os.path.join(base, item)
        if item == "env" or item == "venv":
            continue
        # themes is the name i'm giving locally when building in this folder
        if item.startswith(".") or not os.path.isdir(full_path) or item == "themes":
            continue

        if find_file(full_path, "README.md") == None:
            error_message = f"Theme '{item}' is missing README.md."
            errors.append(error_message)
            continue

        if find_file(full_path, "screenshot.png") == None:
            error_message = f"Theme '{item}' is missing screenshot.png."
            errors.append(error_message)
            continue

        theme = Theme(item, full_path)

        # Check if metadata was successfully loaded.
        if theme.metadata is None:
            continue

        required_metadata = ['name']
        metadata_check = [required for required in required_metadata if required not in theme.metadata]
        if len(metadata_check) > 0:
            error_message = f"Theme '{theme.name}' is missing required metadata: {', '.join(metadata_check)}."
            errors.append(error_message)
            continue

        themes.append(theme)

    return themes


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise Exception("Missing destination folder as argument!")

    destination = sys.argv[1]
    all_themes = read_themes()

    # Delete everything first in this folder
    if os.path.exists(destination):
        shutil.rmtree(destination)
    os.makedirs(destination)

    with open(os.path.join(destination, "_index.md"), "w") as f:
        f.write("""
+++
template = "themes.html"
sort_by = "date"
+++        
        """)

    for t in all_themes:
        t.to_zola_folder(destination)

    # Display errors.
    if errors:
        print("\n\n" + "="*60)
        print("ERROR SUMMARY:")
        print("-"*60)
        for error in errors:
            print(error)
            print("-"*60)
        print("="*60 + "\n")

    # Print summary of themes processed.
    print(f"\nThemes successfully processed: {len(all_themes)}")
    print(f"Themes with errors: {len(errors)}")
