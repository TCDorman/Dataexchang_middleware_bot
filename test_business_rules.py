from src.validation.business_rule_engine import BusinessRuleEngine
from src.validation.rules import (
    order_has_id,
    order_has_lines,
    quantities_are_positive,
)


engine = BusinessRuleEngine()

engine.add_rule(order_has_id)
engine.add_rule(order_has_lines)
engine.add_rule(quantities_are_positive)

test_order = {
    "order_id": "ORD-1001",
    "lines": [
        {"item": "ABC123", "quantity": 5},
        {"item": "XYZ789", "quantity": 2},
    ],
}

results = engine.validate(test_order)

for result in results:
    print(result)

print("Valid:", engine.is_valid(test_order))