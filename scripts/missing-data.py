#!/usr/bin/env python3
"""
Script to update markdown files with manual data for coins missing from CoinGecko
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any

def load_json_file(filepath: str) -> Any:
    """Load JSON data from file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File {filepath} not found")
        return None
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {filepath}: {e}")
        return None

def format_value(value: Any) -> str:
    """Format value for YAML output"""
    if value is None:
        return "null"
    elif isinstance(value, str):
        return f'"{value}"'
    elif isinstance(value, (int, float)):
        return str(value)
    else:
        return str(value)

def update_markdown_file(filepath: str, coin_data: Dict) -> bool:
    """Update markdown file with manual data for missing coins"""
    try:
        # Read existing file
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if file already has miscellaneous data
        if 'mis-data-source:' in content:
            print(f"Skipping {filepath} - already contains miscellaneous data")
            return True
        
        # Split content into frontmatter and body
        if not content.startswith('---'):
            print(f"Error: {filepath} doesn't start with frontmatter")
            return False
        
        # Find the end of frontmatter
        frontmatter_end = content.find('---', 3)
        if frontmatter_end == -1:
            print(f"Error: Invalid frontmatter in {filepath}")
            return False
        
        frontmatter = content[3:frontmatter_end].strip()
        body = content[frontmatter_end + 3:].strip()
        
        # Prepare manual data for missing coins
        misc_data = {
            'coingecko_id': coin_data['id'],
            'current_price': 0,
            'market_cap': 0,
            'market_cap_rank': 0,
            'fully_diluted_valuation': 0,
            'circulating_supply': 0,
            'total_supply': 0,
            'max_supply': 0,
            'ath': 0,
            'ath_change_percentage': 0,
            'ath_date': "null",
            'atl': 0,
            'atl_change_percentage': 0,
            'atl_date': "null"
        }
        
        # Build new frontmatter with miscellaneous data
        new_frontmatter_lines = frontmatter.split('\n')
        
        # Add mis-data-source
        new_frontmatter_lines.append('mis-data-source: "manual"')
        
        # Add last updated timestamp in UTC
        current_utc = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        new_frontmatter_lines.append(f'last_updated: "{current_utc}"')
        
        # Add comment
        new_frontmatter_lines.append('# miscellaneous data source section')
        
        # Add all miscellaneous data fields
        for key, value in misc_data.items():
            formatted_value = format_value(value)
            new_frontmatter_lines.append(f'{key}: {formatted_value}')
        
        # Reconstruct the file
        new_content = '---\n' + '\n'.join(new_frontmatter_lines) + '\n---\n\n' + body
        
        # Write updated content back to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✅ Updated {filepath} with manual data")
        return True
        
    except Exception as e:
        print(f"❌ Error updating {filepath}: {e}")
        return False

def main():
    """Main function to process missing coins"""
    # File paths
    posts_path = "../archviedProjects"
    missing_file = "coingecko-now-missing.json"
    
    # Load missing data file
    print("Loading missing data file...")
    missing_data = load_json_file(missing_file)
    
    if not missing_data:
        print("❌ Failed to load missing data file")
        return
    
    print(f"📊 Found {len(missing_data)} missing coins")
    
    # Process missing coins
    success_count = 0
    error_count = 0
    
    for missing_coin in missing_data:
        filename = missing_coin.get('filename')
        title = missing_coin.get('title')
        ticker = missing_coin.get('ticker')
        
        if not filename:
            print(f"⚠️ Invalid missing entry (no filename): {missing_coin}")
            continue
        
        # Create a synthetic ID from the title or ticker for missing coins
        synthetic_id = title.lower().replace(' ', '-') if title else ticker.lower() if ticker else 'unknown'
        missing_coin['id'] = synthetic_id
        
        # Full path to markdown file
        md_filepath = os.path.join(posts_path, filename)
        
        # Check if file exists
        if not os.path.exists(md_filepath):
            print(f"⚠️ File not found: {md_filepath}")
            error_count += 1
            continue
        
        print(f"📝 Processing {filename} with manual data (missing from CoinGecko)")
        
        # Update the file with manual data
        if update_markdown_file(md_filepath, missing_coin):
            success_count += 1
        else:
            error_count += 1
    
    # Summary
    print(f"\n📊 Processing complete!")
    print(f"✅ Successfully updated: {success_count} files")
    print(f"❌ Errors: {error_count} files")
    print(f"📂 Total processed: {success_count + error_count} files")

if __name__ == "__main__":
    main() 