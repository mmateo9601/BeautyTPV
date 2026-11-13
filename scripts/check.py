import argparse
import subprocess
import sys

from runtime import ROOT, load_instance


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--instance", required=True)
    args = parser.parse_args()
    load_instance(args.instance)
    for command in [["check"], ["makemigrations", "--check", "--dry-run"], ["check", "--deploy"]]:
        subprocess.run([sys.executable, str(ROOT / "manage.py"), *command], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
