#!/usr/bin/env python3
"""
Component Database Builder for Silabs CLI

This script builds a comprehensive database of available Silabs components
by parsing SLC-CLI output. The database can be used for enhanced component
browsing and filtering capabilities in the CLI.

Usage:
    python build_component_db.py [--output FORMAT] [--cache FILE]

Output formats: json, yaml
"""

import subprocess
import json
import yaml
import argparse
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import re


def get_sdk_paths(sdk_id: str) -> List[str]:
    """Get the installation paths for a specific SDK ID."""
    sdks_json_path = os.path.expanduser("~/.silabs/sdks.json")
    
    try:
        with open(sdks_json_path, 'r', encoding='utf-8') as f:
            sdks = json.load(f)
        
        # Find the SDK with the matching ID
        for sdk in sdks:
            if sdk.get('id') == sdk_id:
                paths = []
                for extension in sdk.get('extensions', []):
                    path = extension.get('path')
                    if path:
                        paths.append(path)
                return paths
        
        # If SDK ID not found, show available SDKs
        available_sdks = [sdk.get('id') for sdk in sdks if sdk.get('id')]
        print(f"SDK '{sdk_id}' not found. Available SDKs: {', '.join(available_sdks)}")
        return []
        
    except FileNotFoundError:
        print(f"SDK configuration file not found: {sdks_json_path}")
        return []
    except json.JSONDecodeError as e:
        print(f"Error parsing SDK configuration: {e}")
        return []
    except Exception as e:
        print(f"Error reading SDK configuration: {e}")
        return []


def run_slc_command(cmd: List[str], cwd: Optional[str] = None) -> str:
    """Run an SLC command and return stdout."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=30
        )
        if result.returncode != 0:
            print(f"Warning: SLC command failed: {' '.join(cmd)}")
            print(f"Error: {result.stderr}")
            return ""
        return result.stdout
    except subprocess.TimeoutExpired:
        print(f"Timeout running SLC command: {' '.join(cmd)}")
        return ""
    except FileNotFoundError:
        print("Error: SLC command not found. Make sure SLC-CLI is installed and in PATH.")
        sys.exit(1)


def normalize_component_id(comp_id: str) -> str:
    """Normalize component IDs by stripping surrounding quotes."""
    if comp_id is None:
        return ''
    comp_id = comp_id.strip()
    if (comp_id.startswith('"') and comp_id.endswith('"')) or (comp_id.startswith("'") and comp_id.endswith("'")):
        return comp_id[1:-1]
    return comp_id


def get_all_component_ids(sdk_id: Optional[str] = None) -> Tuple[List[str], Dict[str, str]]:
    """Get all available component IDs and their .slcc file mappings."""
    print("Finding and parsing all .slcc files in SDK...")

    # Determine search paths
    if sdk_id:
        print(f"Searching SDK '{sdk_id}' only...")
        search_paths = get_sdk_paths(sdk_id)
        if not search_paths:
            return [], {}
    else:
        print("Searching all SDKs...")
        search_paths = [os.path.expanduser("~/.silabs")]

    # Find all .slcc files in the specified paths
    import subprocess
    slcc_files = []
    
    for search_path in search_paths:
        try:
            result = subprocess.run(
                ["find", search_path, "-name", "*.slcc", "-type", "f"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                path_files = result.stdout.strip().split('\n')
                path_files = [f for f in path_files if f.strip()]
                slcc_files.extend(path_files)
                print(f"Found {len(path_files)} .slcc files in {search_path}")
            else:
                print(f"Warning: find command failed in {search_path}: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            print(f"Timeout searching {search_path}")
        except Exception as e:
            print(f"Error searching {search_path}: {e}")

    print(f"Total .slcc files found: {len(slcc_files)}")

    component_ids = []
    id_to_file = {}

    for slcc_file in slcc_files:
        try:
            # Parse the YAML content to extract the id
            with open(slcc_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Simple YAML parsing for id field (first line should be "id: <component_id>")
            lines = content.split('\n')
            for line in lines[:10]:  # Check first 10 lines
                line = line.strip()
                if line.startswith('id:'):
                    comp_id = normalize_component_id(line.split(':', 1)[1])
                    if comp_id and comp_id not in id_to_file:
                        component_ids.append(comp_id)
                        id_to_file[comp_id] = slcc_file
                    break

        except Exception as e:
            # Skip files that can't be parsed
            continue

    # Remove duplicates and sort
    component_ids = sorted(list(set(component_ids)))

    print(f"Extracted {len(component_ids)} unique component IDs")
    return component_ids, id_to_file


def examine_component(comp_id: str, id_to_file: Dict[str, str]) -> Optional[Dict[str, Any]]:
    """Examine a single component by parsing its .slcc file directly."""
    comp_id = normalize_component_id(comp_id)

    # Find the .slcc file for this component
    slcc_file = id_to_file.get(comp_id)
    if not slcc_file:
        return None

    try:
        # Parse the .slcc YAML file
        with open(slcc_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Use YAML parser to extract component info
        import yaml
        slcc_data = yaml.safe_load(content)

        component_info = {
            'id': comp_id,
            'description': slcc_data.get('description', '').strip(),
            'category': slcc_data.get('category', ''),
            'quality': slcc_data.get('quality', ''),
            'provides': slcc_data.get('provides', []) or [],
            'requires': slcc_data.get('requires', []) or [],
            'sources': [],
            'includes': [],
            'location': slcc_file
        }

        # Extract sources from the source section
        if 'source' in slcc_data:
            sources = slcc_data['source']
            if isinstance(sources, list):
                for source in sources:
                    if isinstance(source, dict) and 'path' in source:
                        component_info['sources'].append(source['path'])

        # Extract includes
        if 'include' in slcc_data:
            includes = slcc_data['include']
            if isinstance(includes, list):
                for include in includes:
                    if isinstance(include, dict) and 'path' in include:
                        component_info['includes'].append(include['path'])

        return component_info

    except Exception as e:
        print(f"Error parsing .slcc file for {comp_id}: {e}")
        return None


def get_categories() -> List[str]:
    """Get all available categories."""
    print("Getting available categories...")
    try:
        output = run_slc_command(["slc", "show-available", "category"])
    except subprocess.TimeoutExpired:
        print("Category discovery timed out, using empty list")
        return []

    categories = []
    for line in output.split('\n'):
        line = line.strip()
        if line and not line.startswith('-'):
            categories.append(line)

    print(f"Found {len(categories)} categories")
    return categories


def build_component_database(limit: int = None, sdk_id: Optional[str] = None) -> Dict[str, Any]:
    """Build the complete component database."""
    print("Building Silabs component database...")

    # Get all component IDs and their file mappings
    component_ids, id_to_file = get_all_component_ids(sdk_id)

    if limit:
        component_ids = component_ids[:limit]
        print(f"Limited to first {limit} components for testing")

    # Get categories for reference
    categories = get_categories()

    # Examine each component
    components = {}
    total = len(component_ids)
    dropped = 0

    for i, comp_id in enumerate(component_ids):
        print(f"Examining component {i+1}/{total}: {comp_id}")
        comp_info = examine_component(comp_id, id_to_file)
        if not comp_info:
            continue

        category = comp_info.get('category', '')
        if not category or category not in categories:
            dropped += 1
            continue

        components[comp_id] = comp_info

    # Build category mappings using only SLC categories
    # Each entry contains id+location so we don't need to lookup separately.
    category_components = {category: [] for category in categories}

    for comp_id, comp_info in components.items():
        category = comp_info.get('category', '')
        if category in category_components:
            category_components[category].append({
                'id': comp_id,
                'location': comp_info.get('location', '')
            })

    # Create the database structure
    database = {
        'metadata': {
            'version': '1.0',
            'generated_by': 'build_component_db.py',
            'total_components': len(components),
            'total_categories': len(categories),
            'components_dropped': dropped
        },
        'categories': categories,
        'category_components': category_components,
        'components': components
    }

    print(f"Database built with {len(components)} components across {len(categories)} categories (dropped {dropped} components)")
    return database


def save_database(database: Dict[str, Any], output_file: str, format_type: str):
    """Save the database to a file."""
    print(f"Saving database to {output_file}...")

    if format_type.lower() == 'json':
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(database, f, indent=2, ensure_ascii=False)
    elif format_type.lower() == 'yaml':
        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(database, f, default_flow_style=False, allow_unicode=True)
    else:
        raise ValueError(f"Unsupported format: {format_type}")

    print(f"Database saved ({len(str(database))} characters)")


def main():
    parser = argparse.ArgumentParser(description="Build Silabs component database")
    parser.add_argument(
        '--output', '-o',
        default='components.json',
        help='Output file path (default: components.json)'
    )
    parser.add_argument(
        '--format', '-f',
        choices=['json', 'yaml'],
        default='json',
        help='Output format (default: json)'
    )
    parser.add_argument(
        '--cache',
        help='Cache file to avoid re-examining components'
    )
    parser.add_argument(
        '--limit', '-l',
        type=int,
        help='Limit number of components to examine (for testing)'
    )
    parser.add_argument(
        '--sdk', '-s',
        help='Build database only for specified SDK ID (e.g., "2025.12.1")'
    )

    args = parser.parse_args()

    # Check if SLC is available
    try:
        result = subprocess.run(['slc', '--version'], capture_output=True, text=True)
        if result.returncode != 0:
            print("Error: SLC-CLI not found or not working")
            sys.exit(1)
    except FileNotFoundError:
        print("Error: SLC-CLI not found. Make sure it's installed and in PATH.")
        sys.exit(1)

    # Build the database
    database = build_component_database(limit=args.limit, sdk_id=args.sdk)

    # Save to file
    save_database(database, args.output, args.format)

    print("Component database build complete!")


if __name__ == '__main__':
    main()