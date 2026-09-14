"""Exact illustrative supply arithmetic. No inventory mutation or agent tool."""
from datetime import datetime, timedelta
from fractions import Fraction


def eligible_inventory(physical: int, held: int, allocated_elsewhere: int) -> int:
    """The fixture defines held and allocated buckets as disjoint."""
    if any(type(n) is not int or n < 0 for n in (physical, held, allocated_elsewhere)):
        raise ValueError('Nonnegative integer counts required')
    if held + allocated_elsewhere > physical:
        raise ValueError('Disjoint inventory buckets exceed physical inventory')
    return physical - held - allocated_elsewhere


def yield_impact(tested: int, passed: int, baseline_passed: int, baseline_tested: int) -> dict:
    if any(type(n) is not int or n < 0 for n in (tested, passed, baseline_passed, baseline_tested)):
        raise ValueError('Integer counts required')
    if not tested or not baseline_tested or passed > tested or baseline_passed > baseline_tested:
        raise ValueError('Invalid yield denominators/counts')
    expected = Fraction(baseline_passed, baseline_tested) * tested
    shortfall = expected - passed
    if shortfall.denominator != 1:
        raise ValueError('Fixture requires a whole-unit expected supply impact')
    return {'yield_basis_points': int(Fraction(passed, tested) * 10000),
            'baseline_basis_points': int(Fraction(baseline_passed, baseline_tested) * 10000),
            'supply_shortfall_units': int(shortfall)}


def schedule(start: str, setup: int, suite: int, review: int, deadline: str) -> dict:
    if any(type(n) is not int or n < 0 for n in (setup, suite, review)):
        raise ValueError('Nonnegative integer minutes required')
    def utc(value):
        if not value.endswith('Z'):
            raise ValueError('Explicit UTC required')
        return datetime.fromisoformat(value.replace('Z', '+00:00'))
    ready = utc(start) + timedelta(minutes=setup + suite + review)
    return {'review_ready_at': ready.isoformat().replace('+00:00', 'Z'),
            'deadline_slack_minutes': int((utc(deadline) - ready).total_seconds() // 60)}


def cost_difference(standard: int, priority: int) -> int:
    if any(type(n) is not int or n < 0 for n in (standard, priority)):
        raise ValueError('USD must be nonnegative integer cents')
    return priority - standard
