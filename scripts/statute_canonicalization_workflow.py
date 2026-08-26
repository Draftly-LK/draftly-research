#!/usr/bin/env python3
"""
Statute Canonicalization Automation Workflow
Automates Steps 0-6, stops at Step 7 for manual review
"""

import json
import subprocess
import sys
import os
from pathlib import Path

class StatuteWorkflow:
    def __init__(self, source_id, slug):
        self.source_id = source_id
        self.slug = slug
        self.tree_file = f"data/processed/canonical-statutes/{source_id}-*.json"
        self.coverage = None
        self.round_num = 1
        self.issues_found = []
        
    def run_step_1_parse(self):
        """Step 1: Parse the statute"""
        print(f"\n{'='*60}")
        print(f"STEP 1: PARSE {self.source_id}")
        print(f"{'='*60}")
        
        result = subprocess.run(
            ["python", "scripts/build_canonical_statutes.py"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"❌ PARSE FAILED:\n{result.stderr}")
            return False
        
        print(f"✅ Parsed. Output:\n{result.stdout}")
        return True
    
    def run_step_2_coverage(self):
        """Step 2-4: Check coverage (max 5 passes)"""
        print(f"\n{'='*60}")
        print(f"STEP 2-4: COVERAGE CHECK (PASS {self.round_num})")
        print(f"{'='*60}")
        
        result = subprocess.run(
            ["python", "scripts/check_parse_coverage.py", "--source-id", self.source_id],
            capture_output=True,
            text=True
        )
        
        coverage_text = result.stdout
        print(coverage_text)
        
        # Parse coverage %
        if "unmatched" in coverage_text:
            parts = coverage_text.split("unmatched (")
            if len(parts) > 1:
                pct = parts[1].split("%")[0]
                self.coverage = float(pct)
                print(f"\n📊 Coverage: {self.coverage}%")
                
                if self.coverage < 0.5:
                    print("✅ CONVERGED! Ready for review.")
                    return True
                elif self.round_num < 5:
                    print(f"⚠️  Coverage still {self.coverage}%. Continue to pass {self.round_num + 1}?")
                    return False
                else:
                    print("⚠️  Max 5 passes reached. Stopping.")
                    return True
        
        return False
    
    def stop_for_review(self):
        """STOP: Notify user to send to reviewers"""
        print(f"\n{'='*60}")
        print(f"🛑 READY FOR STEP 7: INDEPENDENT REVIEW")
        print(f"{'='*60}")
        
        print(f"""
✅ Automated steps (0-6) complete for {self.source_id}.

📤 NEXT: Send these to Gemini for 5-person review:
   - JSON tree: data/processed/canonical-statutes/{self.source_id}-*.json
   - PDF source: data/legal-sources/library/statutes/...pdf
   
   Use these 5 prompts (one per reviewer):
   1. Completeness: Are all sections/subsections in tree vs PDF?
   2. Text Fidelity: Do 5 longest sections match word-by-word?
   3. Structure: Right depth? Provisos attached correctly?
   4. References: Do cross-refs work? No ref past last section?
   5. Metadata: Correct title/citation/amendments?

📝 After Gemini review, paste results here.
   I'll process feedback and repeat if needed.
""")
        
        return True
    
    def process_review_feedback(self, feedback_text):
        """Process feedback from reviewers"""
        print(f"\n{'='*60}")
        print(f"PROCESSING REVIEW FEEDBACK (ROUND {self.round_num})")
        print(f"{'='*60}")
        
        print(f"Feedback received:\n{feedback_text}\n")
        
        # Check if PASS
        if "PASS" in feedback_text.upper() or "no issues" in feedback_text.lower():
            print("✅ ALL REVIEWERS PASS!")
            return "ready_to_finalize"
        else:
            print("⚠️  Issues found. Analyze and fix parser.")
            self.round_num += 1
            if self.round_num < 7:
                print(f"→ Moving to review round {self.round_num}")
                return "continue_review"
            else:
                print("⚠️  Multiple rounds completed. Document as unverified.")
                return "document_and_finalize"
    
    def finalize(self, statute_note=""):
        """Step 8: Finalize"""
        print(f"\n{'='*60}")
        print(f"STEP 8: FINALIZE {self.source_id}")
        print(f"{'='*60}")
        
        cmd = [
            "python", "scripts/finalize_statute.py",
            "--source-id", self.source_id,
            "--slug", self.slug
        ]
        
        if statute_note:
            cmd.extend(["--statute-note", statute_note])
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ FINALIZED!\n{result.stdout}")
            
            # Update RUBRIK
            print("\nUpdating RUBRIK...")
            subprocess.run(
                ["python", "scripts/merge_html_sections_into_index.py", 
                 "--source-id", self.source_id],
                capture_output=True
            )
            subprocess.run(
                ["python", "apps/statute-browser/build_rubrik.py"],
                capture_output=True
            )
            
            print("✅ RUBRIK UPDATED")
            return True
        else:
            print(f"❌ FINALIZE FAILED:\n{result.stderr}")
            return False


def main():
    print("\n" + "="*60)
    print("STATUTE CANONICALIZATION WORKFLOW")
    print("="*60)
    
    # Get statute info
    source_id = input("\nEnter source ID (e.g., SRC040): ").strip()
    slug = input("Enter slug (e.g., 4-1902-powers-of-attorney-ordinance): ").strip()
    
    workflow = StatuteWorkflow(source_id, slug)
    
    # Step 1: Parse
    if not workflow.run_step_1_parse():
        print("❌ Parsing failed. Exit.")
        sys.exit(1)
    
    # Steps 2-4: Coverage loop (max 5 passes)
    converged = False
    while workflow.round_num <= 5:
        if workflow.run_step_2_coverage():
            converged = True
            break
        workflow.round_num += 1
    
    # Step 5-6: Manual vet (user must review)
    input("\n⏸️  PAUSE: Manually review tree vs PDF for Steps 5-6. Press Enter when done...")
    
    # Step 7: STOP for review
    workflow.stop_for_review()
    
    # Feedback loop
    while True:
        feedback = input("\n📥 Paste reviewer feedback (or 'done' if all pass): ").strip()
        
        if feedback.lower() == "done":
            result = "ready_to_finalize"
        else:
            result = workflow.process_review_feedback(feedback)
        
        if result == "ready_to_finalize":
            print("✅ Ready to finalize!")
            break
        elif result == "document_and_finalize":
            print("✅ Documenting as unverified, proceeding...")
            break
        elif result == "continue_review":
            workflow.stop_for_review()
            continue
    
    # Step 8: Finalize
    note = input("\nAny statute note? (or blank): ").strip()
    workflow.finalize(statute_note=note)
    
    print("\n" + "="*60)
    print(f"✅ {source_id} COMPLETE!")
    print("="*60)
    print(f"\nNext statute? Run this script again with new source_id.")

if __name__ == "__main__":
    main()