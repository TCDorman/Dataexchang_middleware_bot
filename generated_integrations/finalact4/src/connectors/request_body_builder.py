"""
request_body_builder.py

Builds REST API request bodies from WMS data and field mappings.

Supports:
1. Nested object paths: customer.name
2. Array paths: lines[0].sku
3. Flat fields: orderId
"""


class RequestBodyBuilder:
    """
    Converts flat WMS records into customer-specific REST JSON payloads.
    """

    def build_body(
        self,
        source_record: dict,
        field_mapping: dict,
    ) -> dict:
        body = {}

        for source_field, target_path in field_mapping.items():
            value = source_record.get(source_field)

            if value is None:
                continue

            self._set_nested_value(
                body=body,
                path=target_path,
                value=value,
            )

        return body

    def build_batch_body(
        self,
        source_records: list[dict],
        field_mapping: dict,
        batch_key: str | None = None,
    ):
        records = [
            self.build_body(
                source_record=record,
                field_mapping=field_mapping,
            )
            for record in source_records
        ]

        if batch_key:
            return {batch_key: records}

        return records

    def _set_nested_value(
        self,
        body,
        path: str,
        value,
    ) -> None:
        parts = self._parse_path(path)
        current = body

        for index, part in enumerate(parts):
            is_last = index == len(parts) - 1

            key = part["key"]
            array_index = part["array_index"]

            if array_index is None:
                if is_last:
                    current[key] = value
                else:
                    next_part = parts[index + 1]
                    should_be_list = next_part["array_index"] is not None

                    if key not in current:
                        current[key] = [] if should_be_list else {}

                    current = current[key]

            else:
                if key not in current:
                    current[key] = []

                while len(current[key]) <= array_index:
                    current[key].append({})

                if is_last:
                    current[key][array_index] = value
                else:
                    current = current[key][array_index]

    def _parse_path(self, path: str) -> list[dict]:
        parts = []

        for raw_part in path.split("."):
            if "[" in raw_part and raw_part.endswith("]"):
                key = raw_part.split("[")[0]
                index_text = raw_part.split("[")[1].replace("]", "")

                parts.append(
                    {
                        "key": key,
                        "array_index": int(index_text),
                    }
                )
            else:
                parts.append(
                    {
                        "key": raw_part,
                        "array_index": None,
                    }
                )

        return parts