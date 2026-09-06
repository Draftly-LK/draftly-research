#!/usr/bin/env python3
"""
Statute Section Lookup Helper

Builds a searchable index of ALL statute sections (including subsections + paragraphs).
For Paper X, quickly find candidate sections matching keywords.
User does the judgment (which ones actually answer the question).

Usage:
  python lookup_helper.py --build              # Build index once
  python lookup_helper.py --paper 2            # Search interactively for Paper 2
  python lookup_helper.py --act 21-1998        # Search one act
  python lookup_helper.py --search "testator"  # Search by keyword
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime

DRAFTLY_ROOT = Path(__file__).parent.parent.parent
STATUTE_FILE = DRAFTLY_ROOT / "experiments/koblex-inspired-retrieval/data/statute.jsonl"
INDEX_FILE = Path(__file__).parent / "statute_index.json"

def build_index():
    """
    Build searchable index of ALL statute nodes (sections + subsections + paragraphs).
    Save as JSON for fast lookup.
    """
    
    print("Building statute index...")
    print(f"Reading: {STATUTE_FILE}\n")
    
    index = {}
    act_counts = {}
    
    with open(STATUTE_FILE, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            record = json.loads(line)
            
            act_id = record.get('act_id')
            node_id = record.get('node_id')
            node_type = record.get('node_type')
            
            # Only index sections, subsections, paragraphs (skip act-level)
            if node_type not in ['section', 'subsection', 'paragraph']:
                continue
            
            # Track by act
            if act_id not in act_counts:
                act_counts[act_id] = 0
            act_counts[act_id] += 1
            
            # Store full text (not truncated)
            entry = {
                'node_id': node_id,
                'node_type': node_type,
                'heading': record.get('heading') or '',
                'text': record.get('text') or '',  # FULL TEXT
                'act_id': act_id,
            }
            
            if node_id not in index:
                index[node_id] = entry
    
    # Save index
    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2)
    
    print(f"✓ Index built\n")
    print(f"Stats:")
    for act_id in sorted(act_counts.keys()):
        print(f"  {act_id}: {act_counts[act_id]} nodes")
    
    print(f"\nTotal: {len(index)} searchable nodes")
    print(f"Saved to: {INDEX_FILE}\n")

def load_index():
    """Load cached index"""
    if not INDEX_FILE.exists():
        print(f"ERROR: Index not found at {INDEX_FILE}")
        print(f"Run: python lookup_helper.py --build")
        sys.exit(1)
    
    with open(INDEX_FILE, 'r') as f:
        return json.load(f)

def search_index(index, **criteria):
    """
    Search index by:
    - act_id: Search one act
    - keywords: Search heading + text for keywords
    - node_type: Filter by type (section/subsection/paragraph)
    
    Returns list of matching entries
    """
    
    results = []
    
    for node_id, entry in index.items():
        match = True
        
        # Filter by act_id
        if 'act_id' in criteria and entry['act_id'] != criteria['act_id']:
            match = False
        
        # Filter by keywords (in heading or text)
        if 'keywords' in criteria and match:
            keywords = criteria['keywords']
            text_to_search = (entry['heading'] + ' ' + entry['text']).lower()
            
            # ALL keywords must be present
            if not all(kw.lower() in text_to_search for kw in keywords):
                match = False
        
        # Filter by node_type
        if 'node_type' in criteria and entry['node_type'] != criteria['node_type']:
            match = False
        
        if match:
            results.append(entry)
    
    return results

def display_results(results, max_results=20):
    """Display search results in readable format"""
    
    print(f"\nFound {len(results)} matches\n")
    
    for i, entry in enumerate(results[:max_results], 1):
        print(f"{i}. {entry['node_id']}")
        print(f"   Type: {entry['node_type']}")
        print(f"   Heading: {entry['heading']}")
        print(f"   Text: {entry['text'][:150]}...")
        print()
    
    if len(results) > max_results:
        print(f"... and {len(results) - max_results} more (showing first {max_results})")

def interactive_search(index):
    """Interactive search loop for a paper"""
    
    print("\n" + "="*80)
    print("INTERACTIVE SEARCH")
    print("="*80)
    print("\nCommands:")
    print("  act <act_id>           - Search one act (e.g., 'act 21-1998')")
    print("  keyword <word1> <word2> - Search by keywords (e.g., 'keyword intestate heir')")
    print("  both <act> <kw1> <kw2> - Search act for keywords")
    print("  show <node_id>         - Show full text of a node")
    print("  quit                   - Exit")
    print()
    
    while True:
        command = input("\n> ").strip().lower()
        
        if command == 'quit':
            break
        
        elif command.startswith('act '):
            act_id = command.replace('act ', '').strip()
            results = search_index(index, act_id=act_id)
            display_results(results)
        
        elif command.startswith('keyword '):
            keywords = command.replace('keyword ', '').strip().split()
            results = search_index(index, keywords=keywords)
            display_results(results)
        
        elif command.startswith('both '):
            parts = command.replace('both ', '').strip().split()
            if len(parts) < 2:
                print("Usage: both <act_id> <keyword1> [keyword2] ...")
                continue
            act_id = parts[0]
            keywords = parts[1:]
            results = search_index(index, act_id=act_id, keywords=keywords)
            display_results(results)
        
        elif command.startswith('show '):
            node_id = command.replace('show ', '').strip()
            if node_id in index:
                entry = index[node_id]
                print(f"\n{node_id}")
                print(f"Heading: {entry['heading']}")
                print(f"\nFull text:\n{entry['text']}")
            else:
                print(f"Node not found: {node_id}")
        
        else:
            print("Unknown command. Try: act, keyword, both, show, quit")

def paper_workflow(index, paper_num):
    """Guided workflow for a single paper"""
    
    print(f"\n{'='*80}")
    print(f"PAPER {paper_num} LOOKUP HELPER")
    print(f"{'='*80}\n")
    
    print("For each question in Paper {}, use this tool to find candidate sections:\n")
    print("Example workflow:")
    print("  Q6/i: 'What class of title would Kamal be eligible?'")
    print("  → Act: 21-1998 (Registration of Title Act)")
    print("  → Keywords: class, title, possessory, prescription")
    print("  → Search: 'both 21-1998 class possessory'")
    print("  → Results: 21-1998/section-14/paragraph-b ✓\n")
    
    print("Start interactive search:\n")
    interactive_search(index)

def main():
    parser = argparse.ArgumentParser(description='Statute section lookup helper')
    parser.add_argument('--build', action='store_true', help='Build index (run once)')
    parser.add_argument('--paper', type=int, help='Interactive search for paper')
    parser.add_argument('--act', type=str, help='Search one act (e.g., 21-1998)')
    parser.add_argument('--search', type=str, nargs='+', help='Search keywords (e.g., --search intestate heir)')
    
    args = parser.parse_args()
    
    # Build index
    if args.build:
        build_index()
        return
    
    # Load index
    index = load_index()
    print(f"✓ Loaded {len(index)} searchable nodes\n")
    
    # Paper workflow
    if args.paper:
        paper_workflow(index, args.paper)
    
    # Search by act
    elif args.act:
        results = search_index(index, act_id=args.act)
        print(f"Sections in {args.act}:\n")
        display_results(results, max_results=50)
    
    # Search by keywords
    elif args.search:
        results = search_index(index, keywords=args.search)
        print(f"Sections matching: {', '.join(args.search)}\n")
        display_results(results)
    
    # Default: interactive
    else:
        print("Interactive search mode\n")
        interactive_search(index)

if __name__ == '__main__':
    main()
