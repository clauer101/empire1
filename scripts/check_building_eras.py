#!/usr/bin/env python3
"""
Check that every building has at least one knowledge requirement from the same era.
Run from repo root: python3 scripts/check_building_eras.py
"""
import re
import sys
import yaml

ERAS = ['STEINZEIT', 'NEOLITHIKUM', 'BRONZEZEIT', 'EISENZEIT',
        'MITTELALTER', 'RENAISSANCE', 'INDUSTRIELLE REVOLUTION', 'MODERNE ERA', 'ZUKUNFT']

ERA_RE = re.compile(r'^#\s+(' + '|'.join(ERAS) + ')', re.IGNORECASE)
ITEM_RE = re.compile(r'^([A-Z][A-Z0-9_]+):')


def parse_eras(path):
    era_map = {}
    current_era = None
    with open(path) as f:
        for line in f:
            m = ERA_RE.match(line)
            if m:
                current_era = m.group(1).upper()
                continue
            m = ITEM_RE.match(line)
            if m:
                era_map[m.group(1)] = current_era
    return era_map


def main():
    buildings = parse_eras('python_server/config/buildings.yaml')
    knowledge = parse_eras('python_server/config/knowledge.yaml')

    with open('python_server/config/buildings.yaml') as f:
        bdata = yaml.safe_load(f)

    problems = []
    for bname, bval in bdata.items():
        bera = buildings.get(bname, '?')
        reqs = bval.get('requirements', []) or []
        kreqs = [r for r in reqs if r in knowledge]
        same_era_k = [r for r in kreqs if knowledge.get(r) == bera]
        if not same_era_k:
            problems.append((bname, bera, kreqs))

    if not problems:
        print("All buildings have a same-era knowledge requirement.")
        return

    current_era = None
    for bname, bera, kreqs in problems:
        if bera != current_era:
            current_era = bera
            print(f"\n── {bera} ──")
        kreqs_str = ', '.join(f"{k} ({knowledge.get(k, '?')})" for k in kreqs) if kreqs else '—'
        print(f"  {bname:<30} req: {kreqs_str}")

    sys.exit(1)


if __name__ == '__main__':
    main()
