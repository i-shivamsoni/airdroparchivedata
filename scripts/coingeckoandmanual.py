#!/usr/bin/env python3
import os
import json
import yaml
import re
from pathlib import Path

def extract_yaml_frontmatter(content):
    """Extract YAML frontmatter from markdown content."""
    # Look for YAML frontmatter between --- delimiters
    pattern = r'^---\s*\n(.*?)\n---\s*\n'
    match = re.match(pattern, content, re.DOTALL)

    if match:
        yaml_content = match.group(1)
        try:
            return yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            print(f"Error parsing YAML: {e}")
            return None
    return None

def process_markdown_files(directory_path):
    """Process all markdown files in the directory and extract project data."""
    coingecko_projects = []
    manual_projects = []

    directory = Path(directory_path)

    if not directory.exists():
        print(f"Directory not found: {directory_path}")
        return coingecko_projects, manual_projects

    # Find all markdown files
    markdown_files = list(directory.glob("*.md"))

    if not markdown_files:
        print(f"No markdown files found in {directory_path}")
        return coingecko_projects, manual_projects

    print(f"Found {len(markdown_files)} markdown files")

    for file_path in markdown_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()

            # Extract frontmatter
            frontmatter = extract_yaml_frontmatter(content)

            if frontmatter:
                mis_data_source = frontmatter.get("mis-data-source", "").lower()

                project = {
                    "filename": file_path.name,
                    "title": frontmatter.get("title", ""),
                    #"mis-data-source": frontmatter.get("mis-data-source", "")
                }

                if mis_data_source == "coingecko":
                    project["id"] = frontmatter.get("coingecko_id", "")
                    coingecko_projects.append(project)
                    print(f"Processed (CoinGecko): {file_path.name} - {project['title']} - ID: {project['id']}")

                elif mis_data_source == "manual":
                    project["manual_id"] = frontmatter.get("manual_id", "")
                    manual_projects.append(project)
                    print(f"Processed (Manual): {file_path.name} - {project['title']} - ID: {project['manual_id']}")

                else:
                    print(f"Skipped: {file_path.name} - Unknown or missing mis-data-source: '{mis_data_source}'")

            else:
                print(f"No valid frontmatter found in: {file_path.name}")

        except Exception as e:
            print(f"Error processing {file_path.name}: {e}")

    return coingecko_projects, manual_projects

def create_json_file(projects, file_path, data_source_type):
    """Create JSON file for the given projects."""
    output_data = {
        "projects": projects,
        "total_count": len(projects),
        "data_source": data_source_type
    }

    with open(file_path, 'w', encoding='utf-8') as json_file:
        json.dump(output_data, json_file, indent=2, ensure_ascii=False)

    return output_data

def main():
    # Set the directory path
    directory_path = "_posts/archviedProjects"
    output_path    = "_posts/scripts"
    # Process all markdown files
    coingecko_projects, manual_projects = process_markdown_files(directory_path)

    # Create output file paths
    coingecko_output_file = os.path.join(output_path, "projectslist-coingecko.json")
    manual_output_file = os.path.join(output_path, "projectslist-manual.json")

    # Create CoinGecko projects file
    if coingecko_projects:
        create_json_file(coingecko_projects, coingecko_output_file, "coingecko")
        print(f"\n✅ Successfully created {coingecko_output_file}")
        print(f"📊 Total CoinGecko projects: {len(coingecko_projects)}")

        # Show sample of CoinGecko projects
        print("\n📋 Sample CoinGecko projects:")
        for i, project in enumerate(coingecko_projects[:3]):
            print(f"  {i+1}. {project['filename']} - {project['title']} (ID: {project['id']})")

        if len(coingecko_projects) > 3:
            print(f"  ... and {len(coingecko_projects) - 3} more")
    else:
        print("❌ No CoinGecko projects found")

    # Create Manual projects file
    if manual_projects:
        create_json_file(manual_projects, manual_output_file, "manual")
        print(f"\n✅ Successfully created {manual_output_file}")
        print(f"📊 Total Manual projects: {len(manual_projects)}")

        # Show sample of Manual projects
        print("\n📋 Sample Manual projects:")
        for i, project in enumerate(manual_projects[:3]):
            print(f"  {i+1}. {project['filename']} - {project['title']} (ID: {project['manual_id']})")

        if len(manual_projects) > 3:
            print(f"  ... and {len(manual_projects) - 3} more")
    else:
        print("❌ No Manual projects found")

    # Summary
    total_processed = len(coingecko_projects) + len(manual_projects)
    print(f"\n🎉 Processing complete!")
    print(f"📈 Total projects processed: {total_processed}")
    print(f"🦎 CoinGecko projects: {len(coingecko_projects)}")
    print(f"📝 Manual projects: {len(manual_projects)}")

if __name__ == "__main__":
    main()
