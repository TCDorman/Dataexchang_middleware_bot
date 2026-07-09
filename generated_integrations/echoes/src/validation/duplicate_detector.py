"""
==================================================
Duplicate Detector
==================================================

Purpose:
    Detects duplicate records before data is exported
    or sent to Modula WMS.

Responsibilities:
    - Detect duplicate order IDs
    - Detect duplicate order lines
    - Support both dictionaries and WMSOrder objects
    - Return a clear duplicate detection report
"""

# ==================================================
# Imports
# ==================================================

from typing import Any, Dict, List, Tuple


# ==================================================
# Duplicate Detector
# ==================================================

class DuplicateDetector:
    """
    Detects duplicate orders and duplicate order lines.
    """

    def detect_duplicates(
        self,
        orders: List[Any],
    ) -> Dict:
        """
        Detect duplicate records in normalized orders.

        Args:
            orders:
                List of order dictionaries or WMSOrder objects.

        Returns:
            Duplicate detection report.
        """

        duplicate_order_ids = self._find_duplicate_order_ids(orders)
        duplicate_lines = self._find_duplicate_order_lines(orders)

        return {
            "has_duplicates": bool(
                duplicate_order_ids or duplicate_lines
            ),
            "duplicate_order_ids": duplicate_order_ids,
            "duplicate_lines": duplicate_lines,
            "summary": {
                "orders_checked": len(orders),
                "duplicate_order_id_count": len(duplicate_order_ids),
                "duplicate_line_count": len(duplicate_lines),
            },
        }

    def _get_value(
        self,
        obj: Any,
        field_name: str,
        default=None,
    ):
        """
        Read a value from either a dictionary or an object.

        Args:
            obj:
                Dictionary or object.
            field_name:
                Field or attribute name.
            default:
                Default value if missing.

        Returns:
            Field value.
        """

        if isinstance(obj, dict):
            return obj.get(field_name, default)

        return getattr(obj, field_name, default)

    def _find_duplicate_order_ids(
        self,
        orders: List[Any],
    ) -> List[str]:
        """
        Find duplicate order IDs.
        """

        seen_order_ids = set()
        duplicate_order_ids = set()

        for order in orders:
            order_id = self._get_value(order, "order_id")

            if not order_id:
                continue

            if order_id in seen_order_ids:
                duplicate_order_ids.add(order_id)

            seen_order_ids.add(order_id)

        return sorted(duplicate_order_ids)

    def _find_duplicate_order_lines(
        self,
        orders: List[Any],
    ) -> List[Dict]:
        """
        Find duplicate lines within each order.

        A duplicate line is currently defined as the same item
        and same quantity appearing more than once under the
        same order.
        """

        duplicate_lines = []

        for order in orders:
            order_id = self._get_value(order, "order_id")
            lines = self._get_value(order, "lines", [])

            seen_line_keys = set()
            duplicate_line_keys = set()

            for line in lines:
                line_key = self._build_line_key(line)

                if line_key in seen_line_keys:
                    duplicate_line_keys.add(line_key)

                seen_line_keys.add(line_key)

            for line_key in sorted(duplicate_line_keys):
                duplicate_lines.append(
                    {
                        "order_id": order_id,
                        "duplicate_line_key": line_key,
                    }
                )

        return duplicate_lines

    def _build_line_key(
        self,
        line: Any,
    ) -> Tuple:
        """
        Build a unique key for an order line.

        Args:
            line:
                Dictionary or line object.

        Returns:
            Tuple used for duplicate comparison.
        """

        return (
            self._get_value(line, "item"),
            self._get_value(line, "quantity"),
        )