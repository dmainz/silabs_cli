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
                # Only search the main 'simplicity-sdk' extension for .slcc files
                for extension in sdk.get('extensions', []):
                    if extension.get('id') != 'simplicity-sdk':
                        continue
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
    print("Getting component IDs using SLC-CLI and building file mappings...")

    # Try to get component IDs from SLC; fall back to parsing .slcc files if SLC fails.
    component_ids = []
    try:
        cmd = ["slc", "show-available", "id"]
        print("Using configured SDK...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            # Parse the output
            lines = result.stdout.strip().split('\n')
            parsing = False
            for line in lines:
                line = line.strip()
                if line.startswith("Defined values for id:"):
                    parsing = True
                    continue
                if parsing and line:
                    component_ids.append(line)
            print(f"Found {len(component_ids)} component IDs from SLC")
        else:
            print(f"Warning: slc show-available id failed: {result.stderr}")
    except subprocess.TimeoutExpired:
        print("Timeout running slc show-available id")
    except FileNotFoundError:
        print("SLC command not found; falling back to .slcc file scanning")
    except Exception as e:
        print(f"Error running slc show-available id: {e}")

    if not component_ids:
        print("Falling back to extracting component IDs from .slcc files")

    # Now build id_to_file by finding and parsing .slcc files
    if sdk_id:
        search_paths = get_sdk_paths(sdk_id)
        if not search_paths:
            return component_ids, {}
    else:
        search_paths = [os.path.expanduser("~/.silabs")]
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
            else:
                print(f"Warning: find command failed in {search_path}: {result.stderr}")

        except subprocess.TimeoutExpired:
            print(f"Timeout searching {search_path}")
        except Exception as e:
            print(f"Error searching {search_path}: {e}")

    print(f"Found {len(slcc_files)} .slcc files")

    id_to_file = {}
    seen_ids = set(component_ids)

    for idx, slcc_file in enumerate(slcc_files, start=1):
        # Print a simple progress indicator every 200 files
        if idx % 200 == 0:
            print(f"Parsing .slcc files: {idx}/{len(slcc_files)}")

        try:
            with open(slcc_file, 'r', encoding='utf-8') as f:
                # Read only the first few lines where the id is expected
                lines = [next(f, "") for _ in range(30)]

            comp_id = None
            for line in lines:
                line = line.strip()
                # Support both 'id: ...' and '- id: ...' YAML styles
                if line.startswith('id:') or line.startswith('- id:'):
                    parts = line.split(':', 1)
                    if len(parts) > 1:
                        comp_id = normalize_component_id(parts[1])
                    break

            if not comp_id:
                continue

            if comp_id not in seen_ids:
                component_ids.append(comp_id)
                seen_ids.add(comp_id)

            if comp_id not in id_to_file:
                id_to_file[comp_id] = slcc_file

        except Exception:
            continue

    print(f"Mapped {len(id_to_file)} component IDs to files")
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

        # Some .slcc files store metadata as a list of dicts (e.g. - category: ...)
        def find_field(key: str, default=None):
            # YAML can parse !!omap as a list of (key, value) tuples.
            if isinstance(slcc_data, dict):
                return slcc_data.get(key, default)
            if isinstance(slcc_data, list):
                for item in slcc_data:
                    if isinstance(item, dict) and key in item:
                        return item.get(key, default)
                    if isinstance(item, (list, tuple)) and len(item) >= 2 and item[0] == key:
                        return item[1]
            return default

        component_info = {
            'id': comp_id,
            'description': str(find_field('description', '')).strip(),
            'category': str(find_field('category', '')).strip(),
            'quality': str(find_field('quality', '')).strip(),
            'provides': find_field('provides', []) or [],
            'requires': find_field('requires', []) or [],
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
    parsing = False
    for line in output.split('\n'):
        line = line.strip()
        if line.startswith("Defined values for category:"):
            parsing = True
            continue
        if parsing and line:
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
        if not category:
            print(f"Dropping {comp_id} with empty category")
            dropped += 1
            continue

        # Skip components with empty category
        if not category:
            print(f"Dropping {comp_id} with empty category")
            dropped += 1
            continue

        components[comp_id] = comp_info

    # Build category mappings from the discovered components
    categories = sorted({comp_info.get('category', '') for comp_info in components.values() if comp_info.get('category')})
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
        'category_components': category_components
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