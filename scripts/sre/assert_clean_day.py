#!/usr/bin/env python3
import argparse, json, sys, os

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    args = ap.parse_args()

    if not os.path.exists(args.input):
        print(f"Missing SRE health file: {args.input}", file=sys.stderr)
        sys.exit(2)

    with open(args.input, "r") as f:
        data = json.load(f)

    verdict = data.get("verdict")
    if verdict != "PASS":
        print(f"SRE assert failed: verdict={verdict}", file=sys.stderr)
        sys.exit(3)

    print("SRE assert: PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
