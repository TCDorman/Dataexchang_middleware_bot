import argparse

from agents.master_agent import (
    run_customer_import,
    run_wms_export,
)

from agents.history_agent import show_integration_history


def main():
    parser = argparse.ArgumentParser(
        description="Modula WMS Integration Agent"
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    import_parser = subparsers.add_parser(
        "import",
        help="Convert customer ERP data into Modula WMS XML",
    )

    import_parser.add_argument(
        "--customer",
        required=True,
        help="Customer name",
    )

    import_parser.add_argument(
        "--files",
        nargs="+",
        required=True,
        help="Input customer files",
    )

    export_parser = subparsers.add_parser(
        "export",
        help="Convert Modula WMS export XML into customer format",
    )

    export_parser.add_argument(
        "--wms-file",
        required=True,
        help="WMS export XML file",
    )

    export_parser.add_argument(
        "--output",
        default="data/output/customer_export.csv",
        help="Customer output file",
    )

    history_parser = subparsers.add_parser(
        "history",
        help="Show integration history",
    )

    history_parser.add_argument(
        "--customer",
        required=False,
        help="Optional customer filter",
    )

    args = parser.parse_args()

    if args.command == "import":
        result = run_customer_import(
            args.customer,
            args.files,
        )

        print("\nIMPORT COMPLETE")
        print(result)

    elif args.command == "export":
        result = run_wms_export(
            args.wms_file,
            args.output,
        )

        print("\nEXPORT COMPLETE")
        print(result)

    elif args.command == "history":
        history = show_integration_history(args.customer)

        print("\nINTEGRATION HISTORY")

        for entry in history:
            print(
                f"{entry['timestamp']} | "
                f"{entry['customer_name']} | "
                f"{entry['direction']} | "
                f"{entry['status']} | "
                f"{entry['output_file']}"
            )


if __name__ == "__main__":
    main()