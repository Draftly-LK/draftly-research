#!/usr/bin/env python3
"""
Batch process all 16 papers (or specify range).

Claude-assisted verification workflow for Papers 2-16:
1. Claude verifies statute sections
2. User reviews (5 min per paper)
3. Auto-fill worksheet
4. Build + score

Paper 1 already done manually.

Usage:
  python batch_all_papers.py                    # Papers 2-16
  python batch_all_papers.py --start 2 --end 5  # Papers 2-5
"""

import subprocess
import sys
import argparse
from pathlib import Path

def run_paper(paper_num):
    """Run Claude verification for one paper"""
    
    print(f"\n{'='*80}")
    print(f"PAPER {paper_num}")
    print(f"{'='*80}\n")
    
    # Step 1: Claude verification
    print(f"Step 1: Claude-assisted verification...")
    result = subprocess.run(
        [sys.executable, "claude_verify.py", f"--paper", str(paper_num)],
        cwd=str(Path(__file__).parent)
    )
    
    if result.returncode != 0:
        print(f"✗ Claude verification failed for Paper {paper_num}")
        return False
    
    # Step 2: Auto-fill worksheet
    print(f"\nStep 2: Auto-filling worksheet...")
    result = subprocess.run(
        [sys.executable, "auto_fill_worksheet.py", f"--paper", str(paper_num)],
        cwd=str(Path(__file__).parent)
    )
    
    if result.returncode != 0:
        print(f"✗ Auto-fill failed for Paper {paper_num}")
        return False
    
    print(f"\n✓ Paper {paper_num} ready for build + score")
    return True

def main():
    parser = argparse.ArgumentParser(description='Batch process papers 2-16 with Claude-assisted verification')
    parser.add_argument('--start', type=int, default=2, help='Start paper number (default: 2)')
    parser.add_argument('--end', type=int, default=16, help='End paper number (default: 16)')
    parser.add_argument('--skip-verify', action='store_true', help='Skip Claude verification, only auto-fill')
    args = parser.parse_args()
    
    start = args.start
    end = args.end
    
    print(f"\n{'='*80}")
    print(f"BATCH PROCESSING PAPERS {start}-{end}")
    print(f"{'='*80}")
    print(f"\nWorkflow:")
    print(f"1. Claude verifies statute sections for each question")
    print(f"2. You review Claude's suggestions (5 min per paper)")
    print(f"3. Auto-fill worksheet.csv")
    print(f"4. Build + score")
    print(f"\nEstimated time: {(end - start + 1) * 0.5:.1f} hours")
    
    input("\nPress Enter to start...")
    
    failed = []
    completed = []
    
    for paper_num in range(start, end + 1):
        try:
            if run_paper(paper_num):
                completed.append(paper_num)
            else:
                failed.append(paper_num)
        except Exception as e:
            print(f"✗ Exception processing Paper {paper_num}: {e}")
            failed.append(paper_num)
    
    # Summary
    print(f"\n{'='*80}")
    print(f"BATCH COMPLETE")
    print(f"{'='*80}\n")
    
    print(f"Completed: {len(completed)} papers")
    if completed:
        print(f"  Papers: {', '.join(map(str, completed))}")
    
    if failed:
        print(f"\nFailed: {len(failed)} papers")
        print(f"  Papers: {', '.join(map(str, failed))}")
    
    print(f"\nNext steps:")
    print(f"1. Review any failed papers manually")
    print(f"2. Run: cd ../.. (go to Draftly root)")
    print(f"3. Run: uv run python experiments/HiREC-inspired-retrieval/pastpaper_triage.py build")
    print(f"4. Run: uv run python experiments/HiREC-inspired-retrieval/validate_dataset.py ...")
    print(f"5. Run: uv run python experiments/HiREC-inspired-retrieval/run_hierarchy_ceiling.py ...")
    print(f"6. Run: uv run python experiments/HiREC-inspired-retrieval/hirec_evaluate.py ...")

if __name__ == '__main__':
    main()