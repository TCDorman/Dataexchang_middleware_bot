"""
==================================================
API Response Mapper
==================================================

Purpose:
    Maps customer REST API responses into normalized
    Modula WMS-style order dictionaries.

Responsibilities:
    - Read response root
    - Apply generated mapping.json
    - Normalize order header fields
    - Normalize order line fields
"""

# ==================================================
# Imports
# ==================================================

from typing import Any, Dict, List


# ==================================================
# API Response Mapper
# ==================================================

class ApiResponseMapper:
    """
    Maps API response JSON into normalized order records.
    """

    def map_response(
        self,
        api_response: Dict,
        mapping_config: Dict,
    ) -> List[Dict]:
        """
        Map an API response into normalized orders.

        Args:
            api_response:
                Raw JSON response from customer API.
            mapping_config:
                Contents of generated mapping.json.

        Returns:
            List of normalized order dictionaries.
        """

        response_root = mapping_config.get(
            "response_root",
            "",
        )

        suggested_mapping = mapping_config.get(
            "suggested_mapping",
            {},
        )

        source_orders = self._extract_orders(
            api_response,
            response_root,
        )

        normalized_orders = []

        for source_order in source_orders:
            normalized_orders.append(
                self._map_order(
                    source_order,
                    suggested_mapping,
                )
            )

        return normalized_orders

    def _extract_orders(
        self,
        api_response: Dict,
        response_root: str,
    ) -> List[Dict]:
        """
        Extract source order list from the API response.
        """

        if response_root:
            orders = api_response.get(response_root, [])

            if isinstance(orders, list):
                return orders

            return []

        if isinstance(api_response, list):
            return api_response

        return [api_response]

    def _map_order(
        self,
        source_order: Dict,
        mapping: Dict,
    ) -> Dict:
        """
        Map one source order into normalized order format.
        """

        lines_mapping = mapping.get(
            "lines",
            {},
        )

        source_lines_key = self._guess_lines_key(
            source_order
        )

        source_lines = source_order.get(
            source_lines_key,
            [],
        )

        return {
            "order_number": self._get_nested_value(
                source_order,
                mapping.get("order_number", ""),
            ),
            "description": self._get_nested_value(
                source_order,
                mapping.get("description", ""),
            ),
            "operation_type": self._get_nested_value(
                source_order,
                mapping.get("operation_type", ""),
            ),
            "lines": [
                self._map_line(
                    source_line,
                    lines_mapping,
                )
                for source_line in source_lines
            ],
        }

    def _map_line(
        self,
        source_line: Dict,
        mapping: Dict,
    ) -> Dict:
        """
        Map one source line into normalized line format.
        """

        return {
            "item_code": self._get_nested_value(
                source_line,
                mapping.get("item_code", ""),
            ),
            "quantity": self._get_nested_value(
                source_line,
                mapping.get("quantity", ""),
            ),
        }

    def _guess_lines_key(
        self,
        source_order: Dict,
    ) -> str:
        """
        Guess which source field contains order lines.
        """

        possible_keys = [
            "lines",
            "items",
            "orderLines",
            "order_lines",
            "details",
        ]

        for key in possible_keys:
            if isinstance(source_order.get(key), list):
                return key

        return "lines"

    def _get_nested_value(
        self,
        data: Dict,
        path: str,
    ):
        """
        Read a simple or dotted path from a dictionary.

        Examples:
            orderNo
            customer.name
        """

        if not path:
            return None

        current_value: Any = data

        for part in path.split("."):
            if not isinstance(current_value, dict):
                return None

            current_value = current_value.get(part)

        return current_value