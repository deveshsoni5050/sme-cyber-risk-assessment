#!/usr/bin/env python3
"""SME Cybersecurity Risk Assessment tool.

Risk Score = Likelihood (1-5) x Impact (1-5)
Bands: 1-5 Low, 6-11 Medium, 12-19 High, 20-25 Critical

Commands:
  rank       rank a risk register CSV (id,threat,likelihood,impact)
  cases      compare before/after scores for case studies
  checklist  interactive 10-question self-assessment
"""
import argparse
import csv
import sys
from collections import OrderedDict

BANDS = [(20, "Critical"), (12, "High"), (6, "Medium"), (1, "Low")]
ACTIONS = {
    "Critical": "Fix immediately",
    "High": "Fix within 30 days",
    "Medium": "Plan within the quarter",
    "Low": "Accept and monitor",
}
COLORS = {"Critical": "#C8372D", "High": "#EE8434", "Medium": "#F2C14E", "Low": "#7FB77E"}

CHECKLIST = [
    "Is MFA enabled on email and admin accounts?",
    "Are backups stored offsite and restore-tested in the last 3 months?",
    "Are devices set to update automatically?",
    "Has staff received security training in the last 12 months?",
    "Does each person have their own account (no sharing)?",
    "Are laptops and phones encrypted?",
    "Is there a firewall and endpoint protection on all devices?",
    "Is the guest Wi-Fi separate from the business network?",
    "Is there a written incident response contact list?",
    "Are vendor and former-employee accesses reviewed regularly?",
]


def validate(value, name):
    value = int(value)
    if not 1 <= value <= 5:
        raise ValueError(f"{name} must be between 1 and 5, got {value}")
    return value


def score(likelihood, impact):
    return validate(likelihood, "likelihood") * validate(impact, "impact")


def band(value):
    for threshold, name in BANDS:
        if value >= threshold:
            return name
    raise ValueError(f"score must be at least 1, got {value}")


def read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def rank_rows(rows):
    out = []
    for r in rows:
        s = score(r["likelihood"], r["impact"])
        out.append({**r, "score": s, "band": band(s), "action": ACTIONS[band(s)]})
    return sorted(out, key=lambda x: (-x["score"], x["id"]))


def cmd_rank(args):
    ranked = rank_rows(read_csv(args.file))
    print(f"{'ID':<5}{'Threat':<34}{'L':>2}{'I':>3}{'Score':>7}  {'Band':<9}Action")
    for r in ranked:
        print(f"{r['id']:<5}{r['threat']:<34}{r['likelihood']:>2}{r['impact']:>3}{r['score']:>7}  {r['band']:<9}{r['action']}")
    if args.out:
        with open(args.out, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(ranked[0].keys()))
            w.writeheader()
            w.writerows(ranked)
        print(f"\nSaved ranked register to {args.out}")
    if args.heatmap:
        heatmap(ranked, args.heatmap)


def summarize_cases(rows):
    cases = OrderedDict()
    for r in rows:
        c = cases.setdefault(r["case"], {"before": 0, "after": 0})
        c["before"] += score(r["likelihood_before"], r["impact_before"])
        c["after"] += score(r["likelihood_after"], r["impact_after"])
    for c in cases.values():
        c["reduction_pct"] = round(100 * (c["before"] - c["after"]) / c["before"], 1)
    return cases


def cmd_cases(args):
    cases = summarize_cases(read_csv(args.file))
    print(f"{'Case':<32}{'Before':>8}{'After':>8}{'Reduction':>11}")
    for name, c in cases.items():
        print(f"{name:<32}{c['before']:>8}{c['after']:>8}{c['reduction_pct']:>10}%")
    if args.chart:
        chart(cases, args.chart)


def cmd_checklist(_args):
    nos = 0
    for i, q in enumerate(CHECKLIST, 1):
        ans = input(f"{i:>2}. {q} [y/n]: ").strip().lower()
        nos += ans not in ("y", "yes")
    level = "Good posture" if nos <= 2 else "Moderate: fix within 30 days" if nos <= 5 else "High exposure: act immediately"
    print(f"\nNo answers: {nos}/10 -> {level}")


def _plt():
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        return plt
    except ImportError:
        sys.exit("matplotlib is required for charts: pip install matplotlib")


def heatmap(ranked, path):
    plt = _plt()
    fig, ax = plt.subplots(figsize=(5, 5))
    for L in range(1, 6):
        for I in range(1, 6):
            ax.add_patch(plt.Rectangle((I - 0.5, L - 0.5), 1, 1, color=COLORS[band(L * I)], ec="white"))
            ax.text(I, L, L * I, ha="center", va="center", fontsize=9, alpha=0.5)
    for r in ranked:
        ax.text(int(r["impact"]), int(r["likelihood"]), r["id"], ha="center", va="center", fontweight="bold", fontsize=8)
    ax.set_xlim(0.5, 5.5); ax.set_ylim(0.5, 5.5)
    ax.set_xlabel("Impact"); ax.set_ylabel("Likelihood"); ax.set_title("Risk heatmap")
    fig.tight_layout(); fig.savefig(path, dpi=150); plt.close(fig)
    print(f"Saved heatmap to {path}")


def chart(cases, path):
    plt = _plt()
    names = list(cases)
    x = range(len(names))
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar([i - 0.2 for i in x], [cases[n]["before"] for n in names], 0.4, label="Before", color="#C8372D")
    ax.bar([i + 0.2 for i in x], [cases[n]["after"] for n in names], 0.4, label="After", color="#0E7C86")
    ax.set_xticks(list(x)); ax.set_xticklabels([n.split(" (")[0] for n in names])
    ax.set_ylabel("Total risk score"); ax.set_title("Risk before vs after controls"); ax.legend()
    fig.tight_layout(); fig.savefig(path, dpi=150); plt.close(fig)
    print(f"Saved chart to {path}")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("rank"); a.add_argument("file"); a.add_argument("--out"); a.add_argument("--heatmap")
    a.set_defaults(fn=cmd_rank)
    b = sub.add_parser("cases"); b.add_argument("file"); b.add_argument("--chart")
    b.set_defaults(fn=cmd_cases)
    c = sub.add_parser("checklist"); c.set_defaults(fn=cmd_checklist)
    args = p.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
