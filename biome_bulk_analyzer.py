#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path
from biome_core import BIOMEAnalyzer


def main():
    parser = argparse.ArgumentParser(description='BIOME Stream Analyzer v1/v2 (Bulk version)')
    parser.add_argument('folder', help='BIOME folder')
    parser.add_argument('--frames', default='5', help='Max frames (number or "all")')
    parser.add_argument('--version', type=int, choices=[1, 2], help='Force version')
    parser.add_argument('--min-binary-size', type=int, default=100, help='Min binary size (bytes)')
    parser.add_argument('--output-dir', '-o', type=Path, help='Output directory for reports (required)', required=True)
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--full', action='store_true', default=True, help='Full protobuf values')
    parser.add_argument('--no-html', action='store_true', help='Skip HTML report')
    args = parser.parse_args()

    print("=" * 60)
    print("BIOME Stream Analyzer v3.5.4")
    print("Author: Marc Brandt (mb4n6)")
    print("=" * 60)

    base_folder = Path(args.folder)
    if not base_folder.exists():
        print(f"Error: Folder not found: {args.folder}")
        return 1
    if (base_folder / "streams").is_dir():
        base_folder = base_folder / "streams"

    max_frames = float('inf') if args.frames.lower() == 'all' else int(args.frames)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    biome_paths = [p for f in ("public", "restricted") for p in base_folder.glob(f"{f}/*") if p.is_dir()]
    for i, biome_path in enumerate(biome_paths):
        print(f"[{i+1:0{len(str(len(biome_paths)))}}/{len(biome_paths)}] Parsing biome {biome_path.name}")
        biome_files = [
            (f"local.{b.name}", b)
            for b in biome_path.glob("local/*")
            if b.is_file() and b.name.isdigit()
        ] + [
            (f"local.tombstone.{b.name}", b)
            for b in biome_path.glob("local/tombstone/*")
            if b.is_file() and b.name.isdigit()
        ] + [
            (f"remote.{b.parent.name}.{b.name}", b)
            for b in biome_path.glob("remote/*/*")
            if b.is_file() and b.name.isdigit()
        ] + [
            (f"remote.{b.parent.name}.tombstone.{b.name}", b)
            for b in biome_path.glob("remote/*/tombstone/*")
            if b.is_file() and b.name.isdigit()
        ]
        if not biome_files:
            print("No biome files found")
            continue

        biome_output = args.output_dir / f"{biome_path.parent.name}_{biome_path.name}"
        biome_output.mkdir(parents=True, exist_ok=True)

        for output_name, file_path in biome_files:

            print(f"File: {file_path.name} ({file_path.stat().st_size:,} bytes)")
            print(f"Frames: {max_frames if max_frames != float('inf') else 'ALL'}")
            print("-" * 60)

            try:
                analyzer = BIOMEAnalyzer(
                    str(file_path),
                    max_frames=max_frames,
                    verbose=args.verbose,
                    full_output=args.full,
                    min_binary_size=args.min_binary_size,
                    force_version=args.version,
                    output_dir=biome_output,
                )

                if not analyzer.analyze():
                    print("Analysis failed!")
                    return 1

                print(f"\nVersion: {analyzer.version}")
                print(f"Frames: {len(analyzer.frames)}")
                print(f"Binary objects: {sum(len(f.binary_objects) for f in analyzer.frames)}")
                print(f"Hash: {analyzer.file_hash}")
                print(f"\nOutput directory: {analyzer.output_dir}")

                json_path = analyzer.export_json(biome_output / f"{output_name}.json")
                csv_path = analyzer.export_csv(biome_output / f"{output_name}.csv")
                print(f"✓ JSON: {json_path.name}")
                print(f"✓ CSV: {csv_path.name}")

                if not args.no_html:
                    from biome_reports import HTMLReport
                    html_path = HTMLReport(analyzer).generate(biome_output / f"{output_name}.html")
                    print(f"✓ HTML: {html_path.name}")

                print("=" * 60)

            except KeyboardInterrupt:
                print("\nInterrupted")
                return 130
            except Exception as e:
                print(f"Error: {e}")
                if args.verbose:
                    import traceback
                    traceback.print_exc()
                return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
