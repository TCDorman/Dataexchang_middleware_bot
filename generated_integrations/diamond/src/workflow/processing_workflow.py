"""
processing_workflow.py

Main workflow orchestration for the Modula WMS Data Integration Agent.

This module connects the validation pieces of the processing pipeline:

1. Run business rule validation
2. Run data quality checks
3. Return one combined validation report

Later, this same workflow will also connect parsing, customer profile loading,
field mapping, and XML generation.
"""

from typing import Any, Dict, List

from src.validation.business_rule_engine import BusinessRuleEngine, RuleResult
from src.validation.data_quality_checker import DataQualityChecker
from src.validation.rules import (
    order_has_id,
    order_has_lines,
    quantities_are_positive,
)


class ProcessingWorkflow:
    """
    Coordinates the full order processing workflow.

    This class acts as the main connector between parsing, mapping,
    validation, data quality checks, and output generation.
    """

    def __init__(self):
        """
        Initialize the workflow and register the default validation tools.
        """

        # Create one business rule engine for this workflow instance.
        self.business_rule_engine = BusinessRuleEngine()

        # Create one data quality checker for this workflow instance.
        self.data_quality_checker = DataQualityChecker()

        # Register default order-level validation rules.
        self.business_rule_engine.add_rule(order_has_id)
        self.business_rule_engine.add_rule(order_has_lines)
        self.business_rule_engine.add_rule(quantities_are_positive)

    def validate_orders(self, orders: List[Dict[str, Any]]) -> List[RuleResult]:
        """
        Run business rule validation against a list of orders.

        Args:
            orders: List of transformed order dictionaries.

        Returns:
            A flat list of RuleResult objects from all orders.
        """

        all_results = []

        # Validate each order individually so we can catch bad records
        # before generating XML output.
        for order in orders:
            results = self.business_rule_engine.validate(order)
            all_results.extend(results)

        return all_results

    def check_data_quality(self, orders: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Run data quality checks against a list of orders.

        Args:
            orders: List of transformed order dictionaries.

        Returns:
            Dictionary containing errors, warnings, and quality score.
        """

        return self.data_quality_checker.check_orders(orders)

    def run_validation_report(self, orders: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Run both business rules and data quality checks.

        Args:
            orders: List of transformed order dictionaries.

        Returns:
            Combined validation report for the workflow.
        """

        business_rule_results = self.validate_orders(orders)
        data_quality_results = self.check_data_quality(orders)

        business_rule_errors = [
            result.message
            for result in business_rule_results
            if not result.passed
        ]

        return {
            "business_rules_passed": len(business_rule_errors) == 0,
            "business_rule_errors": business_rule_errors,
            "data_quality_errors": data_quality_results["errors"],
            "data_quality_warnings": data_quality_results["warnings"],
            "quality_score": data_quality_results["quality_score"],
            "ready_for_xml": (
                len(business_rule_errors) == 0
                and len(data_quality_results["errors"]) == 0
            ),
        }
    def process_transformed_orders(self, orders: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process transformed orders through the validation pipeline.

        This method serves as the primary entry point for the workflow.
        Future versions will also perform XML generation, archiving,
        logging, and notification handling.

        Args:
            orders: List of transformed order dictionaries.

        Returns:
            Dictionary containing workflow results and validation report.
        """

        # Generate a complete validation report.
        report = self.run_validation_report(orders)

        # Build a workflow result object that future pipeline stages
        # can consume.
        return {
            "status": "success" if report["ready_for_xml"] else "validation_failed",
            "ready_for_xml": report["ready_for_xml"],
            "validation_report": report,
            "orders_processed": len(orders),
        }
    def orders_are_valid(self, orders: List[Dict[str, Any]]) -> bool:
        """
        Check whether all orders pass all blocking validation checks.

        Args:
            orders: List of transformed order dictionaries.

        Returns:
            True if business rules pass and no data quality errors exist.
            False if any blocking issue is found.
        """

        report = self.run_validation_report(orders)

        return report["ready_for_xml"]