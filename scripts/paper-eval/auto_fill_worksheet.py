#!/usr/bin/env python3
"""
Auto-fill worksheet.csv from Claude verification results

Takes the results from claude_verify.py and fills the worksheet.csv
with bucket, gold_provisions, verified_by, verified_date, etc.

Usage:
  python auto_fill_worksheet.py --paper 2
"""

import json
import csv
import sys
import argparse
from pathlib import Path
from datetime import datetime

DRAFTLY_ROOT = Path(__file__).parent.parent.parent
RESULTS_DIR = Path(__file__).parent
WORKSHEET_PATH = DRAFTLY_ROOT / "data/evaluvation/pastpaper-triage/worksheet.csv"

def load_claude_results(paper_num):
    """Load Claude verification results"""
    results_file = RESULTS_DIR / f"paper_{paper_num:02d}_claude_results.json"
    
    if not results_file.exists():
        print(f"ERROR: {results_file} not found")
        print(f"Run: python claude_verify.py --paper {paper_num}")
        sys.exit(1)
    
    with open(results_file, 'r') as f:
        return json.load(f)

def load_worksheet():
    """Load current worksheet.csv"""
    rows = []
    with open(WORKSHEET_PATH, 'r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    return rows

def update_worksheet_row(row, paper_num, part_id, claude_result):
    """Update a worksheet row with Claude's verification result"""
    
    # Check if this is the right row
    if row.get('paper_no') != str(paper_num) or row.get('part_id') != part_id:
        return row
    
    node_ids = claude_result['node_ids']
    method = claude_result['method']
    
    # Determine bucket
    if method == 'unsure':
        bucket = ''  # Leave unbucketed
    elif method == 'skipped_no_acts':
        bucket = 'C-not-retrieval'  # No act mentioned, probably not retrieval
    elif node_ids:
        bucket = 'A-retrievable'
    else:
        bucket = ''
    
    # Fill in fields
    row['bucket'] = bucket
    row['gold_provisions'] = '; '.join(node_ids) if node_ids else ''
    row['verified_by'] = 'Praveen De Silva'
    row['verified_date'] = datetime.now().strftime('%Y-%m-%d')
    
    # Add notes
    notes = []
    if method == 'manual':
        notes.append('Manually corrected by user')
    elif method == 'unsure':
        notes.append('Claude uncertain; flagged for manual review')
    elif method == 'skipped_no_acts':
        notes.append('No statute named in question')
    
    if notes:
        row['notes'] = '; '.join(notes)
    
    # Add corpus_coverage
    if node_ids:
        row['corpus_coverage'] = 'complete'
    else:
        row['corpus_coverage'] = 'absent'
    
    return row

def save_worksheet(rows):
    """Save updated worksheet.csv"""
    # Get fieldnames from first row
    if not rows:
        print("ERROR: No rows to save")
        sys.exit(1)
    
    fieldnames = list(rows[0].keys())
    
    # Write
    with open(WORKSHEET_PATH, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"✓ Worksheet saved: {WORKSHEET_PATH}")

def main():
    parser = argparse.ArgumentParser(description='Auto-fill worksheet from Claude results')
    parser.add_argument('--paper', type=int, required=True, help='Paper number')
    args = parser.parse_args()
    
    paper_num = args.paper
    
    print(f"\nLoading Claude results for Paper {paper_num}...")
    claude_results = load_claude_results(paper_num)
    
    print(f"Loading worksheet...")
    rows = load_worksheet()
    
    print(f"Updating rows...")
    updated_count = 0
    
    for part_id, result in claude_results.items():
        for i, row in enumerate(rows):
            if (row.get('paper_no') == str(paper_num) and 
                row.get('part_id') == part_id):
                rows[i] = update_worksheet_row(row, paper_num, part_id, result)
                updated_count += 1
                print(f"  ✓ Q{part_id}: {result['method'].upper()}")
                if result['node_ids']:
                    print(f"    → {'; '.join(result['node_ids'])}")
    
    print(f"\nUpdated {updated_count} rows")
    
    print(f"\nSaving worksheet...")
    save_worksheet(rows)
    
    print(f"\n✓ Paper {paper_num} auto-filled!")
    print(f"\nNext steps:")
    print(f"  1. Review worksheet.csv for any unexpected results")
    print(f"  2. Run: uv run python pastpaper_triage.py build")
    print(f"  3. Run: uv run python validate_dataset.py ...")
    print(f"  4. Run: uv run python hirec_evaluate.py ...")

if __name__ == '__main__':
    main()