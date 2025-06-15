import json
import requests
import time
import os
import glob
from typing import List, Dict

def load_json_file(filepath: str) -> Dict:
    """Load JSON data from file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Error: File {filepath} not found")
        return {}
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in {filepath}")
        return {}

def save_json_file(data: List[Dict], filepath: str, append: bool = False) -> None:
    """Save data to JSON file, optionally appending to existing data"""
    try:
        if append and os.path.exists(filepath):
            # Load existing data
            existing_data = load_json_file(filepath)
            if isinstance(existing_data, list):
                # Merge new data with existing data
                merged_data = existing_data + data
                # Remove duplicates based on 'id' field
                seen_ids = set()
                unique_data = []
                for item in merged_data:
                    if item.get('id') not in seen_ids:
                        seen_ids.add(item.get('id'))
                        unique_data.append(item)
                data = unique_data
            else:
                print(f"Warning: Existing file {filepath} is not a list, overwriting")
        
        with open(filepath, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
        print(f"Successfully saved {filepath}")
    except Exception as e:
        print(f"Error saving {filepath}: {e}")

def get_market_data_batch(coin_ids: List[str], api_key: str) -> List[Dict]:
    """Fetch market data for a batch of coin IDs"""
    # Join coin IDs with comma
    ids_param = ','.join(coin_ids)
    
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        'vs_currency': 'usd',
        'ids': ids_param,
        'per_page': 500,
        'page': 1
    }
    
    headers = {
        'accept': 'application/json',
        'x-cg-demo-api-key': api_key
    }
    
    try:
        print(f"Fetching data for {len(coin_ids)} coins: {ids_param[:100]}{'...' if len(ids_param) > 100 else ''}")
        response = requests.get(url, params=params, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print(f"Successfully fetched {len(data)} coins data")
            return data
        else:
            print(f"API Error: {response.status_code} - {response.text}")
            return []
            
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return []

def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """Split list into chunks of specified size"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def cleanup_batch_files(output_dir: str) -> None:
    """Clean up individual batch files after successful processing"""
    try:
        # Find all list*.json files
        batch_files = glob.glob(os.path.join(output_dir, "list*.json"))
        for file in batch_files:
            os.remove(file)
            print(f"Cleaned up: {file}")
        print(f"Cleaned up {len(batch_files)} batch files")
    except Exception as e:
        print(f"Error during cleanup: {e}")

def main():
    # Configuration
    projects_file = "projectslist-coingecko.json"
    output_dir = "."
    api_key = os.getenv('COINGECKO_API_KEY')
    batch_size = 100
    
    if not api_key:
        print("Error: COINGECKO_API_KEY environment variable not set")
        return

    # Load projects file
    print("Loading projectslist-coingecko.json...")
    projects_data = load_json_file(projects_file)
    
    if not projects_data or 'projects' not in projects_data:
        print("No projects data found in file")
        return
    
    projects = projects_data['projects']
    
    # Extract coin IDs and check for duplicates
    all_coin_ids = []
    unique_coin_ids = []
    duplicate_ids = {}
    project_lookup = {}  # Map coin_id to project info for missing projects tracking
    
    for project in projects:
        coin_id = project.get('id', '').strip()
        if coin_id:
            all_coin_ids.append(coin_id)
            
            # Store project info for later use
            project_lookup[coin_id] = {
                'id': coin_id,
                'title': project.get('title', ''),
                'filename': project.get('filename', '')
            }
            
            if coin_id not in unique_coin_ids:
                unique_coin_ids.append(coin_id)
            else:
                if coin_id in duplicate_ids:
                    duplicate_ids[coin_id] += 1
                else:
                    duplicate_ids[coin_id] = 2  # First duplicate occurrence
    
    coin_ids = unique_coin_ids
    
    print(f"Total projects in file: {len(projects)}")
    print(f"Total coin IDs found: {len(all_coin_ids)}")
    print(f"Unique coin IDs: {len(coin_ids)}")
    
    # Show duplicates if any
    if duplicate_ids:
        print(f"Duplicate coin IDs found: {len(duplicate_ids)}")
        print("List of duplicate coin IDs:")
        for dup_id, count in duplicate_ids.items():
            print(f"  - '{dup_id}' appears {count} times")
        
        # Save duplicates to file
        duplicate_filepath = os.path.join(output_dir, "duplicate_coin_ids.json")
        duplicate_data = [{"id": dup_id, "count": count} for dup_id, count in duplicate_ids.items()]
        save_json_file(duplicate_data, duplicate_filepath)
        print(f"Duplicate coin IDs saved to: duplicate_coin_ids.json")
    else:
        print("No duplicate coin IDs found")
    
    if not coin_ids:
        print("No valid coin IDs found")
        return
    
    print(f"\nProceeding to fetch market data for {len(coin_ids)} unique coins...")
    
    # Split into batches
    batches = chunk_list(coin_ids, batch_size)
    print(f"Created {len(batches)} batches of max {batch_size} coins each")
    
    # Fetch data for each batch
    all_market_data = []
    
    for i, batch in enumerate(batches, 1):
        print(f"\n--- Processing Batch {i}/{len(batches)} ---")
        print(f"Batch contains {len(batch)} coin IDs")
        
        # Fetch market data for this batch
        batch_data = get_market_data_batch(batch, api_key)
        
        if batch_data:
            all_market_data.extend(batch_data)
            
            # Save individual batch file
            batch_filename = f"list{i}.json"
            batch_filepath = os.path.join(output_dir, batch_filename)
            save_json_file(batch_data, batch_filepath)
            
        # Rate limiting - wait between requests to avoid hitting API limits
        if i < len(batches):  # Don't wait after the last batch
            print("Waiting 2 seconds before next batch...")
            time.sleep(2)
    
    # Save combined data
    if all_market_data:
        combined_filepath = os.path.join(output_dir, "all_market_data.json")
        save_json_file(all_market_data, combined_filepath)
        
        print(f"\n=== Summary ===")
        print(f"Total projects in file: {len(projects)}")
        print(f"Total coin IDs (including duplicates): {len(all_coin_ids)}")
        print(f"Unique coin IDs to fetch: {len(coin_ids)}")
        if duplicate_ids:
            print(f"Duplicate coin IDs: {len(duplicate_ids)} (saved to duplicate_coin_ids.json)")
        print(f"Total batches processed: {len(batches)}")
        print(f"Market data entries successfully fetched: {len(all_market_data)}")
        
        # Clean up individual batch files
        cleanup_batch_files(output_dir)
        
        print(f"Combined data saved: all_market_data.json")
        
        # Show missing coins (if any)
        fetched_ids = {coin['id'] for coin in all_market_data}
        missing_ids = [coin_id for coin_id in coin_ids if coin_id not in fetched_ids]
        
        if missing_ids:
            print(f"\nMissing coins (not found in CoinGecko): {len(missing_ids)}")
            print("Full list of missing coin IDs:")
            for i, missing_id in enumerate(missing_ids, 1):
                print(f"  {i:3d}. {missing_id}")
            
            # Create missing projects data with id, title, and filename
            missing_projects = []
            for missing_id in missing_ids:
                if missing_id in project_lookup:
                    missing_projects.append({
                        'id': missing_id,
                        'title': project_lookup[missing_id]['title'],
                        'filename': project_lookup[missing_id]['filename']
                    })
                else:
                    missing_projects.append({
                        'id': missing_id,
                        'title': 'Unknown',
                        'filename': 'Unknown'
                    })
            
            # Save missing projects to coingecko-now-missing.json (append mode)
            missing_filepath = os.path.join(output_dir, "coingecko-now-missing.json")
            save_json_file(missing_projects, missing_filepath, append=True)
            print(f"\nMissing projects appended to: coingecko-now-missing.json")
            
            # Also save the old format for compatibility
            missing_old_format = [{"id": coin_id, "reason": "not_found_in_coingecko"} for coin_id in missing_ids]
            missing_old_filepath = os.path.join(output_dir, "missing_coin_ids.json")
            save_json_file(missing_old_format, missing_old_filepath)
            print(f"Missing coin IDs (old format) saved to: missing_coin_ids.json")
            
            # Also create a detailed comparison
            print(f"\n=== Detailed Analysis ===")
            print(f"Expected unique coins to fetch: {len(coin_ids)}")
            print(f"Actually fetched from CoinGecko: {len(all_market_data)}")
            print(f"Missing/Not found: {len(missing_ids)}")
            print(f"Success rate: {len(all_market_data)/len(coin_ids)*100:.1f}%")
            
            if duplicate_ids:
                total_duplicates = sum(count - 1 for count in duplicate_ids.values())
                print(f"Note: {total_duplicates} duplicate entries were removed before fetching")
            
        else:
            print("\nAll coins successfully found in CoinGecko!")
            # Create an empty missing file to indicate no missing projects
            missing_filepath = os.path.join(output_dir, "coingecko-now-missing.json")
            save_json_file([], missing_filepath)
            print(f"Empty missing projects file created: coingecko-now-missing.json")
    else:
        print("\nNo market data was fetched")
        # If no data was fetched, all projects are missing
        missing_projects = []
        for coin_id in coin_ids:
            if coin_id in project_lookup:
                missing_projects.append({
                    'id': coin_id,
                    'title': project_lookup[coin_id]['title'],
                    'filename': project_lookup[coin_id]['filename']
                })
        
        missing_filepath = os.path.join(output_dir, "coingecko-now-missing.json")
        save_json_file(missing_projects, missing_filepath, append=True)
        print(f"All projects appended to: coingecko-now-missing.json")

if __name__ == "__main__":
    main()
