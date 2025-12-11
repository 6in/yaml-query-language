"""YQL Command Line Interface."""

import argparse
import sys
from pathlib import Path

from . import __version__, parse_file, generate_sql, Dialect


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        prog="yql",
        description="YQL (YAML Query Language) Parser and SQL Generator",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Parse command
    parse_parser = subparsers.add_parser("parse", help="Parse YQL file and show AST")
    parse_parser.add_argument("file", type=Path, help="YQL file to parse")
    
    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Generate SQL from YQL file")
    gen_parser.add_argument("file", type=Path, help="YQL file to convert")
    gen_parser.add_argument(
        "-d", "--dialect",
        type=str,
        choices=["postgresql", "mysql", "sqlserver", "oracle"],
        default="postgresql",
        help="Target database dialect (default: postgresql)",
    )
    gen_parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Output file (default: stdout)",
    )
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    
    try:
        if args.command == "parse":
            cmd_parse(args)
        elif args.command == "generate":
            cmd_generate(args)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_parse(args):
    """Parse command handler."""
    yql = parse_file(args.file)
    print(f"Operation: {yql.operation}")
    print(f"Query: {yql.query}")


def cmd_generate(args):
    """Generate command handler."""
    yql = parse_file(args.file)
    dialect = Dialect(args.dialect)
    sql = generate_sql(yql, dialect)
    
    if args.output:
        args.output.write_text(sql, encoding="utf-8")
        print(f"SQL written to {args.output}")
    else:
        print(sql)


if __name__ == "__main__":
    main()

