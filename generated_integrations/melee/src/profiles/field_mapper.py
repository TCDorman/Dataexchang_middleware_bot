"""
field_mapper.py

Maps customer-specific field names into the
internal Modula order format.
"""

from typing import Dict


class FieldMapper:
    """
    Applies customer field mappings.
    """

    def map_row(
        self,
        row: Dict,
        profile: Dict,
    ) -> Dict:
        """
        Map a customer row using the profile.

        Args:
            row: Original customer data row.
            profile: Customer profile.

        Returns:
            Mapped row.
        """

        mapping = profile["field_mapping"]

        mapped_row = {}

        for source_field, target_field in mapping.items():

            if source_field in row:
                mapped_row[target_field] = row[source_field]

        return mapped_row