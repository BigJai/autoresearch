"""
Knowledge Ingestion Pipeline.

Processes all source materials into structured knowledge for hypothesis generation:
- PDFs → text extraction
- Videos → transcription (via youtube-transcriber MCP)
- Ebooks → rule extraction
- Web pages → structured content

Usage:
    python src/ingest.py --all
    python src/ingest.py --youtube
    python src/ingest.py --extract-rules
"""
import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime

KNOWLEDGE_DIR = Path(__file__).parent.parent / 'knowledge'
RULES_DIR = KNOWLEDGE_DIR / 'rules-extracted'


def extract_rules_from_text(text: str, source: str) -> list[dict]:
    """Extract potential trading rules from text content.

    Looks for patterns like:
    - "when X happens, Y follows"
    - specific degree/angle mentions
    - cycle length mentions (N days/weeks/months)
    - planet + aspect + market mentions
    """
    rules = []

    # Pattern 1: Degree mentions (e.g., "17°18'27" or "161 degrees")
    degree_pattern = r'(\d{1,3})[°]\s*(\d{1,2})[\']?\s*(\d{1,2})?["\"]?'
    for match in re.finditer(degree_pattern, text):
        deg = int(match.group(1))
        minutes = int(match.group(2)) if match.group(2) else 0
        context = text[max(0, match.start() - 100):match.end() + 100]
        rules.append({
            'type': 'degree',
            'value': deg + minutes / 60,
            'raw': match.group(0),
            'context': context.strip(),
            'source': source,
        })

    # Pattern 2: Cycle mentions (e.g., "90 days", "7 years", "49 weeks")
    cycle_pattern = r'(\d{1,4})\s*(days?|weeks?|months?|years?)'
    for match in re.finditer(cycle_pattern, text, re.IGNORECASE):
        value = int(match.group(1))
        unit = match.group(2).lower().rstrip('s')
        # Convert to days
        days = value
        if unit == 'week':
            days = value * 7
        elif unit == 'month':
            days = value * 30
        elif unit == 'year':
            days = value * 365
        context = text[max(0, match.start() - 100):match.end() + 100]
        rules.append({
            'type': 'cycle',
            'value_days': days,
            'value_raw': f'{value} {match.group(2)}',
            'context': context.strip(),
            'source': source,
        })

    # Pattern 3: Planet mentions with aspects
    planets = ['Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn',
               'Uranus', 'Neptune', 'Pluto', 'Sun', 'Moon']
    aspects = ['conjunction', 'opposition', 'square', 'trine', 'sextile',
               'retrograde', 'station', 'ingress']

    for planet in planets:
        for aspect in aspects:
            pattern = rf'{planet}\s+\w*\s*{aspect}'
            for match in re.finditer(pattern, text, re.IGNORECASE):
                context = text[max(0, match.start() - 150):match.end() + 150]
                rules.append({
                    'type': 'planetary_aspect',
                    'planet': planet,
                    'aspect': aspect,
                    'context': context.strip(),
                    'source': source,
                })

    # Pattern 4: Biblical number references
    biblical = ['7', '12', '30', '40', '49', '50', '70', '144', '360', '490',
                'seven', 'twelve', 'forty', 'seventy']
    for num in biblical:
        pattern = rf'\b{num}\b'
        for match in re.finditer(pattern, text):
            context = text[max(0, match.start() - 100):match.end() + 100]
            # Only include if context mentions trading/market/price/time
            if any(w in context.lower() for w in ['market', 'price', 'trade',
                                                     'cotton', 'wheat', 'gold',
                                                     'stock', 'cycle', 'time',
                                                     'turn', 'change']):
                rules.append({
                    'type': 'biblical_number',
                    'value': num,
                    'context': context.strip(),
                    'source': source,
                })

    return rules


def process_ebooks():
    """Extract rules from all ebook text files."""
    ebook_dir = KNOWLEDGE_DIR / 'ebooks'
    all_rules = []

    for f in ebook_dir.glob('*.txt'):
        print(f'Processing {f.name}...')
        text = f.read_text(errors='replace')
        rules = extract_rules_from_text(text, f.name)
        all_rules.extend(rules)
        print(f'  Found {len(rules)} potential rules')

    # Save
    output = RULES_DIR / 'ebook_rules.json'
    with open(output, 'w') as fp:
        json.dump(all_rules, fp, indent=2)
    print(f'\nTotal: {len(all_rules)} rules extracted → {output}')
    return all_rules


def process_decoded():
    """Extract rules from decoded Tunnel data."""
    decoded_dir = KNOWLEDGE_DIR / 'decoded'
    all_rules = []

    for f in decoded_dir.glob('*.md'):
        print(f'Processing {f.name}...')
        text = f.read_text(errors='replace')
        rules = extract_rules_from_text(text, f.name)
        all_rules.extend(rules)
        print(f'  Found {len(rules)} potential rules')

    for f in decoded_dir.glob('*.json'):
        print(f'Processing {f.name}...')
        data = json.loads(f.read_text())
        text = json.dumps(data, indent=2)
        rules = extract_rules_from_text(text, f.name)
        all_rules.extend(rules)
        print(f'  Found {len(rules)} potential rules')

    output = RULES_DIR / 'decoded_rules.json'
    with open(output, 'w') as fp:
        json.dump(all_rules, fp, indent=2)
    print(f'\nTotal: {len(all_rules)} decoded rules → {output}')
    return all_rules


def create_rule_summary():
    """Create a human-readable summary of all extracted rules."""
    all_rules = []
    for f in RULES_DIR.glob('*.json'):
        with open(f) as fp:
            all_rules.extend(json.load(fp))

    # Group by type
    by_type = {}
    for r in all_rules:
        t = r['type']
        if t not in by_type:
            by_type[t] = []
        by_type[t].append(r)

    summary = f'# Extracted Rules Summary\n\nGenerated: {datetime.now().isoformat()}\n'
    summary += f'Total rules found: {len(all_rules)}\n\n'

    for rule_type, rules in sorted(by_type.items()):
        summary += f'## {rule_type.replace("_", " ").title()} ({len(rules)} found)\n\n'
        # Show unique values
        if rule_type == 'cycle':
            values = sorted(set(r['value_days'] for r in rules))
            summary += f'Unique cycle lengths (days): {values[:30]}\n\n'
        elif rule_type == 'degree':
            values = sorted(set(round(r['value'], 2) for r in rules))
            summary += f'Unique degrees: {values[:30]}\n\n'
        elif rule_type == 'planetary_aspect':
            combos = sorted(set(f"{r['planet']}-{r['aspect']}" for r in rules))
            summary += f'Unique combos: {combos}\n\n'

        # Show top examples
        for r in rules[:5]:
            summary += f'- **{r.get("value", r.get("value_raw", r.get("planet", "")))}**'
            summary += f' ({r["source"]})\n'
            ctx = r['context'][:200].replace('\n', ' ')
            summary += f'  > {ctx}\n\n'

    output = KNOWLEDGE_DIR / 'RULES-SUMMARY.md'
    with open(output, 'w') as fp:
        fp.write(summary)
    print(f'Summary written to {output}')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Knowledge Ingestion Pipeline')
    parser.add_argument('--all', action='store_true', help='Process everything')
    parser.add_argument('--ebooks', action='store_true', help='Process ebooks')
    parser.add_argument('--decoded', action='store_true', help='Process decoded data')
    parser.add_argument('--extract-rules', action='store_true', help='Extract rules')
    parser.add_argument('--summary', action='store_true', help='Generate summary')
    args = parser.parse_args()

    if args.all or args.ebooks:
        process_ebooks()
    if args.all or args.decoded:
        process_decoded()
    if args.all or args.summary:
        create_rule_summary()
    if args.extract_rules:
        process_ebooks()
        process_decoded()
        create_rule_summary()

    if not any(vars(args).values()):
        print('Usage: python src/ingest.py --all')
        print('  --ebooks     Process ebook text files')
        print('  --decoded    Process decoded Tunnel data')
        print('  --extract-rules  Extract all rules + summary')
        print('  --summary    Generate rules summary')
