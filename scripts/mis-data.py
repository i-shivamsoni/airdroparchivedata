#!/usr/bin/env python3
"""
Script to update markdown files with market data from CoinGecko
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

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

def find_market_data(market_data: List[Dict], coin_id: str) -> Optional[Dict]:
    """Find market data for a specific coin ID"""
    for coin in market_data:
        if coin.get('id') == coin_id:
            return coin
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

def update_markdown_file(filepath: str, coin_data: Dict, market_data: Dict) -> bool:
    """Update markdown file with CoinGecko market data"""
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
        
        # Prepare market data from CoinGecko
        misc_data = {
            'coingecko_id': market_data['id'],
            'current_price': market_data.get('current_price'),
            'market_cap': market_data.get('market_cap'),
            'market_cap_rank': market_data.get('market_cap_rank'),
            'fully_diluted_valuation': market_data.get('fully_diluted_valuation'),
            'circulating_supply': market_data.get('circulating_supply'),
            'total_supply': market_data.get('total_supply'),
            'max_supply': market_data.get('max_supply'),
            'ath': market_data.get('ath'),
            'ath_change_percentage': market_data.get('ath_change_percentage'),
            'ath_date': market_data.get('ath_date'),
            'atl': market_data.get('atl'),
            'atl_change_percentage': market_data.get('atl_change_percentage'),
            'atl_date': market_data.get('atl_date')
        }
        
        # Build new frontmatter with miscellaneous data
        new_frontmatter_lines = frontmatter.split('\n')
        
        # Add mis-data-source
        new_frontmatter_lines.append('mis-data-source: "coingecko"')
        
        # Add last updated timestamp from market data
        last_updated = market_data.get('last_updated')
        if last_updated:
            new_frontmatter_lines.append(f'last_updated: "{last_updated}"')
        else:
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
        
        print(f"✅ Updated {filepath} with CoinGecko data")
        return True
        
    except Exception as e:
        print(f"❌ Error updating {filepath}: {e}")
        return False

def main():
    """Main function to process all files"""
    # File paths
    posts_path = "../archviedProjects"
    mapping_file = "projectslist-coingecko.json"
    market_data_file = "all_market_data.json"
    
    # Load data files
    print("Loading data files...")
    mapping_data = load_json_file(mapping_file)
    market_data = load_json_file(market_data_file)
    
    if not mapping_data or 'projects' not in mapping_data:
        print("❌ Failed to load mapping data or invalid format")
        return
    
    if not market_data:
        print("❌ Failed to load market data")
        return
    
    print(f"📊 Processing {len(mapping_data['projects'])} mapped coins...")
    print(f"📊 Found {len(market_data)} coins in market data")
    
    # Process coins from mapping file
    success_count = 0
    error_count = 0
    
    for coin_mapping in mapping_data['projects']:
        filename = coin_mapping.get('filename')
        coin_id = coin_mapping.get('id')
        
        if not filename or not coin_id:
            print(f"⚠️ Invalid mapping entry: {coin_mapping}")
            continue
        
        # Full path to markdown file
        md_filepath = os.path.join(posts_path, filename)
        
        # Check if file exists
        if not os.path.exists(md_filepath):
            print(f"⚠️ File not found: {md_filepath}")
            error_count += 1
            continue
        
        # Find market data for this coin
        market_coin_data = find_market_data(market_data, coin_id)
        if market_coin_data:
            print(f"📈 Processing {filename} with CoinGecko data")
            # Update the file with CoinGecko data
            if update_markdown_file(md_filepath, coin_mapping, market_coin_data):
                success_count += 1
            else:
                error_count += 1
        else:
            print(f"⚠️ No market data found for {coin_id} in mapping file")
            error_count += 1
    
    # Summary
    print(f"\n📊 Processing complete!")
    print(f"✅ Successfully updated: {success_count} files")
    print(f"❌ Errors: {error_count} files")
    print(f"📂 Total processed: {success_count + error_count} files")

if __name__ == "__main__":
    main()
