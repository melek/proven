"""Generate oracle test results table across all conditions."""
import subprocess
import sys
import re

BENCHMARKS = [
    'bounded_counter', 'stack', 'priority_queue', 'sorted_list',
    'unique_set', 'pipeline_state', 'binary_search', 'ring_buffer',
    'balanced_parentheses',
]

CONDITIONS = [
    ('Proven(local)',   '--formal-dir', 'runs/h2h/proven_local_v2'),
    ('Proven(Son.)',    '--formal-dir', 'runs/h2h/proven_sonnet'),
    ('Freestyle(Son.)', '--formal-dir', 'runs/h2h/sonnet_freestyle'),
    ('TDD(local)',      '--tdd-dir',    'runs/tdd/local'),
    ('TDD(Son.)',       '--tdd-dir',    'runs/tdd/sonnet'),
]

W = 15  # column width


def run_oracle(flag, path, problem):
    r = subprocess.run(
        [sys.executable, '-m', 'pytest', 'research/oracle_tests/',
         flag, path, '-k', problem, '-q', '--tb=no', '--no-header'],
        capture_output=True, text=True, timeout=30,
    )
    last = r.stdout.strip().split('\n')[-1] if r.stdout.strip() else ''
    m_pass = re.search(r'(\d+) passed', last)
    m_fail = re.search(r'(\d+) failed', last)
    passed = int(m_pass.group(1)) if m_pass else 0
    failed = int(m_fail.group(1)) if m_fail else 0
    return passed, failed


def main():
    header = "{:<24}".format("Problem")
    for name, _, _ in CONDITIONS:
        header += "{:>{}s}".format(name, W)
    print(header)
    print("-" * (24 + W * len(CONDITIONS)))

    totals = {c[0]: [0, 0] for c in CONDITIONS}

    for problem in BENCHMARKS:
        row = "{:<24}".format(problem)
        for cond_name, flag, path in CONDITIONS:
            passed, failed = run_oracle(flag, path, problem)
            total = passed + failed
            if total == 0:
                cell = "skip"
            else:
                cell = "{}/{}".format(passed, total)
            row += "{:>{}s}".format(cell, W)
            totals[cond_name][0] += passed
            totals[cond_name][1] += total
        print(row)

    print("-" * (24 + W * len(CONDITIONS)))
    row = "{:<24}".format("TOTAL")
    for cond_name, _, _ in CONDITIONS:
        p, t = totals[cond_name]
        cell = "{}/{}".format(p, t)
        row += "{:>{}s}".format(cell, W)
    print(row)


if __name__ == "__main__":
    main()
