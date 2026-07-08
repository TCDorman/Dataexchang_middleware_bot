"""
report_formatter.py

Formats workflow validation reports into readable terminal output.

The workflow creates structured Python dictionaries.
This formatter turns those dictionaries into text that a user can easily read.
"""


from typing import Any, Dict


class ReportFormatter:
    """
    Converts validation report dictionaries into human-readable text.
    """

    def format_validation_report(self, report: Dict[str, Any]) -> str:
        """
        Format a validation report for terminal or CLI display.

        Args:
            report: Validation report created by ProcessingWorkflow.

        Returns:
            A readable string summary of the validation results.
        """

        lines = []

        lines.append("=" * 50)
        lines.append("MODULA INTEGRATION VALIDATION REPORT")
        lines.append("=" * 50)

        lines.append(f"Business Rules Passed: {report['business_rules_passed']}")
        lines.append(f"Quality Score: {report['quality_score']}%")
        lines.append(f"Ready for XML: {report['ready_for_xml']}")
        lines.append("")

        if report["business_rule_errors"]:
            lines.append("Business Rule Errors:")
            for error in report["business_rule_errors"]:
                lines.append(f"  - {error}")
            lines.append("")

        if report["data_quality_errors"]:
            lines.append("Data Quality Errors:")
            for error in report["data_quality_errors"]:
                lines.append(f"  - {error}")
            lines.append("")

        if report["data_quality_warnings"]:
            lines.append("Data Quality Warnings:")
            for warning in report["data_quality_warnings"]:
                lines.append(f"  - {warning}")
            lines.append("")

        if report["ready_for_xml"]:
            lines.append("Result: File is ready for XML generation.")
        else:
            lines.append("Result: File is NOT ready for XML generation.")

        lines.append("=" * 50)

        return "\n".join(lines)