"""YQL Command Line Interface."""

import argparse
import sys
from pathlib import Path

from . import __version__, parse_file, generate_sql, Dialect
from .parser import ParseError


def format_error(error: Exception) -> str:
    """Format error message for better readability."""
    if isinstance(error, ParseError):
        # ParseErrorは既に分かりやすいメッセージを含んでいる
        category_emoji = {
            "syntax_error": "📝",
            "security_error": "🔒",
            "logic_error": "🔗",
        }.get(error.category, "❌")
        
        result = f"{category_emoji} {error.category.replace('_', ' ').title()}: {error.message}"
        
        # デバッグ情報を追加
        if error.details:
            if "import_chain" in error.details and error.details["import_chain"]:
                result += f"\n\n📋 Import chain: {' -> '.join(error.details['import_chain'])}"
            if "file" in error.details and error.details["file"]:
                result += f"\n📄 File: {error.details['file']}"
            if "circular_path" in error.details:
                result += f"\n🔄 Circular path: {' -> '.join(error.details['circular_path'])}"
        
        return result
    else:
        # その他のエラーは詳細を表示
        import traceback
        tb_lines = traceback.format_exception(type(error), error, error.__traceback__)
        # 重要な行だけを抽出
        important_lines = []
        for line in tb_lines:
            if any(keyword in line for keyword in ['Error:', 'ParseError', 'File "', 'yql/']):
                important_lines.append(line.rstrip())
        
        if important_lines:
            return f"❌ Error: {error}\n\n" + "\n".join(important_lines[-5:])
        else:
            return f"❌ Error: {error}"


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
        # エラーメッセージを整形して表示
        error_msg = format_error(e)
        print(error_msg, file=sys.stderr)
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

