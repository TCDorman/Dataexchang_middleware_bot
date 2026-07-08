from dataclasses import dataclass
from typing import Any, Callable, Dict, List


@dataclass
class RuleResult:
    rule_name: str
    passed: bool
    message: str


class BusinessRuleEngine:
    def __init__(self):
        self.rules: List[Callable[[Dict[str, Any]], RuleResult]] = []

    def add_rule(self, rule: Callable[[Dict[str, Any]], RuleResult]):
        self.rules.append(rule)

    def validate(self, order: Dict[str, Any]) -> List[RuleResult]:
        results = []

        for rule in self.rules:
            results.append(rule(order))

        return results

    def is_valid(self, order: Dict[str, Any]) -> bool:
        return all(result.passed for result in self.validate(order))