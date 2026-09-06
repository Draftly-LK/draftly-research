#!/usr/bin/env python3
"""
Claude-Assisted Statute Section Verification

For each question in a paper, Claude reads:
1. The exam question
2. Candidate statute sections from statute.jsonl
3. Returns: "Yes this answers it" / "No" / "Partial"

User reviews Claude's suggestions (5 min), confirms or corrects.
Then auto-fills worksheet.

Usage:
  python claude_verify.py --paper 2
"""

import json
import sys
import argparse
from pathlib import Path
from anthropic import Anthropic

# Setup paths
DRAFTLY_ROOT = Path(__file__).parent.parent.parent
STATUTE_FILE = DRAFTLY_ROOT / "experiments/koblex-inspired-retrieval/data/statute.jsonl"
QUESTIONS_DIR = DRAFTLY_ROOT / "data/evaluvation/parsed-pastpapers/questions"

# Initialize Claude
client = Anthropic()
conversation_history = []

def load_statute_data():
    """Load all statute sections"""
    print("Loading statute.jsonl...")
    sections = {}
    with open(STATUTE_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            record = json.loads(line)
            if record.get('node_type') == 'section':
                act_id = record['act_id']
                if act_id not in sections:
                    sections[act_id] = []
                sections[act_id].append({
                    'node_id': record['node_id'],
                    'heading': record.get('heading', ''),
                    'text': record.get('text', '')[:500]  # Truncate for Claude
                })
    print(f"✓ Loaded {sum(len(v) for v in sections.values())} sections from {len(sections)} acts\n")
    return sections

def load_questions(paper_num):
    """Load questions for a paper"""
    questions_file = QUESTIONS_DIR / f"paper-{paper_num:02d}.questions.json"
    
    if not questions_file.exists():
        print(f"ERROR: {questions_file} not found")
        sys.exit(1)
    
    with open(questions_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"Loaded {len(data.get('parts', []))} questions from Paper {paper_num}\n")
    return data

def extract_acts_from_question(question_text):
    """Extract act names/numbers mentioned in question"""
    # Look for patterns like "Act No. 38 of 2014" or "Ordinance 1876"
    import re
    
    acts_mentioned = re.findall(
        r'(?:Act|Ordinance|Law)\s+(?:No\.)?\s*(\d+)\s+(?:of\s+)?(\d{4})?',
        question_text,
        re.IGNORECASE
    )
    
    # Convert to act_id format (e.g., "38-2014")
    act_ids = []
    for match in acts_mentioned:
        act_num = match[0]
        year = match[1] if match[1] else "unknown"
        act_id = f"{act_num}-{year}"
        act_ids.append(act_id)
    
    return act_ids

def get_candidate_sections(question_text, all_sections):
    """Get candidate statute sections for a question"""
    # If question names an act, get sections from that act
    act_ids = extract_acts_from_question(question_text)
    
    candidates = {}
    for act_id in act_ids:
        if act_id in all_sections:
            candidates[act_id] = all_sections[act_id]
    
    return candidates

def verify_with_claude(question_text, act_id, sections):
    """Ask Claude if sections answer the question"""
    
    # Format sections for Claude
    sections_formatted = "\n".join([
        f"- {s['node_id']}: {s['heading']}\n  Text: {s['text']}"
        for s in sections[:10]  # Limit to top 10 to avoid token overload
    ])
    
    prompt = f"""You are a legal statute verification assistant.

Question from exam:
"{question_text}"

Available statute sections from {act_id}:
{sections_formatted}

For EACH section listed above, determine:
1. Does this section directly answer the question? (Yes/No/Partial)
2. Why or why not?

Format your response as JSON:
[
  {{
    "node_id": "X-YYYY/section-N",
    "heading": "section heading",
    "verdict": "Yes" | "No" | "Partial",
    "reason": "brief explanation"
  }},
  ...
]

Be strict: Only mark "Yes" if the section DIRECTLY states the rule being asked about.
Mark "Partial" if it answers part of the question but not all.
Mark "No" if it's tangential or doesn't apply.
"""
    
    # Add to conversation
    conversation_history.append({
        "role": "user",
        "content": prompt
    })
    
    # Call Claude
    response = client.messages.create(
        model="claude-opus-4-1",
        max_tokens=2000,
        messages=conversation_history
    )
    
    assistant_message = response.content[0].text
    conversation_history.append({
        "role": "assistant",
        "content": assistant_message
    })
    
    # Parse response
    try:
        # Extract JSON from response
        import re
        json_match = re.search(r'\[.*\]', assistant_message, re.DOTALL)
        if json_match:
            results = json.loads(json_match.group())
            return results
        else:
            print("⚠ Could not parse Claude's JSON response")
            return []
    except json.JSONDecodeError as e:
        print(f"⚠ JSON parse error: {e}")
        print("Claude response:", assistant_message[:200])
        return []

def present_results(question_num, question_text, claude_results):
    """Present Claude's verification results to user"""
    
    print(f"\n{'='*80}")
    print(f"Question: {question_num}")
    print(f"{'='*80}\n")
    
    print(f"Question text:\n{question_text}\n")
    
    print("Claude's Analysis:")
    print("-" * 80)
    
    yes_sections = []
    partial_sections = []
    no_sections = []
    
    for result in claude_results:
        verdict = result.get('verdict', 'UNKNOWN')
        node_id = result.get('node_id', 'unknown')
        heading = result.get('heading', '')
        reason = result.get('reason', '')
        
        status = "✓ YES" if verdict == "Yes" else ("⚠ PARTIAL" if verdict == "Partial" else "✗ NO")
        print(f"\n{status}: {node_id}")
        print(f"  Heading: {heading}")
        print(f"  Reason: {reason}")
        
        if verdict == "Yes":
            yes_sections.append(node_id)
        elif verdict == "Partial":
            partial_sections.append(node_id)
    
    print("\n" + "-" * 80)
    print("\nSummary:")
    if yes_sections:
        print(f"✓ YES sections: {'; '.join(yes_sections)}")
    if partial_sections:
        print(f"⚠ PARTIAL sections: {'; '.join(partial_sections)}")
    if not yes_sections and not partial_sections:
        print("✗ No good sections found")
    
    return yes_sections, partial_sections

def get_user_confirmation(yes_sections, partial_sections):
    """Ask user to confirm/override Claude's suggestions"""
    
    print("\n" + "="*80)
    print("USER REVIEW")
    print("="*80)
    
    while True:
        choice = input("\nAccept Claude's suggestion? (yes/no/manual): ").strip().lower()
        
        if choice == 'yes':
            return yes_sections + partial_sections, "auto"
        
        elif choice == 'partial':
            # Accept only YES, not PARTIAL
            return yes_sections, "partial"
        
        elif choice == 'no':
            print("\nEnter correct node_ids (semicolon-separated, or 'UNSURE'): ")
            manual_input = input("> ").strip()
            
            if manual_input.upper() == 'UNSURE':
                return [], "unsure"
            else:
                return [nid.strip() for nid in manual_input.split(';')], "manual"
        
        elif choice == 'manual':
            print("\nEnter correct node_ids (semicolon-separated, or 'UNSURE'): ")
            manual_input = input("> ").strip()
            
            if manual_input.upper() == 'UNSURE':
                return [], "unsure"
            else:
                return [nid.strip() for nid in manual_input.split(';')], "manual"
        
        else:
            print("Invalid choice. Enter 'yes', 'partial', 'no', or 'manual'.")

def main():
    parser = argparse.ArgumentParser(description='Claude-assisted statute verification')
    parser.add_argument('--paper', type=int, required=True, help='Paper number (1-16)')
    args = parser.parse_args()
    
    paper_num = args.paper
    
    print(f"\n{'='*80}")
    print(f"CLAUDE-ASSISTED VERIFICATION - PAPER {paper_num}")
    print(f"{'='*80}\n")
    
    # Load data
    all_sections = load_statute_data()
    questions_data = load_questions(paper_num)
    
    # Process each question
    results = {}
    
    for question in questions_data.get('parts', []):
        question_id = question['part_id']
        question_text = question['text']
        
        # Get candidate sections
        candidates = get_candidate_sections(question_text, all_sections)
        
        if not candidates:
            print(f"\n⚠ Q{question_id}: No acts mentioned in question (skip to manual)")
            results[question_id] = {
                'text': question_text,
                'node_ids': [],
                'method': 'skipped_no_acts'
            }
            continue
        
        # Verify with Claude
        print(f"Verifying Q{question_id}...", end=" ", flush=True)
        
        all_verdicts = []
        for act_id, sections in candidates.items():
            verdicts = verify_with_claude(question_text, act_id, sections)
            all_verdicts.extend(verdicts)
        
        print("✓")
        
        # Present & get confirmation
        yes_sections, partial_sections = present_results(
            question_id, question_text, all_verdicts
        )
        
        final_nodeids, method = get_user_confirmation(yes_sections, partial_sections)
        
        results[question_id] = {
            'text': question_text,
            'node_ids': final_nodeids,
            'method': method,
            'claude_yes': yes_sections,
            'claude_partial': partial_sections
        }
        
        print(f"\n✓ Confirmed: {method}")
        if final_nodeids:
            print(f"  Node_ids: {'; '.join(final_nodeids)}")
        else:
            print(f"  (No sections)")
    
    # Save results
    results_file = Path(__file__).parent / f"paper_{paper_num:02d}_claude_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✓ Results saved to: {results_file}")
    print(f"\nNext: Fill worksheet.csv with results above")
    print(f"Or run: python auto_fill_worksheet.py --paper {paper_num}")

if __name__ == '__main__':
    main()