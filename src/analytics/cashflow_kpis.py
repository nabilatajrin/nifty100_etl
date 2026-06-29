"""Cash-flow KPIs + capital allocation classifier (Sprint 2, Day 11)."""


def free_cash_flow(operating_activity: float, investing_activity: float):
    """FCF = CFO + CFI. Negative values are allowed (returned as-is)."""
    return (operating_activity or 0) + (investing_activity or 0)


def cfo_quality_score(cfo_values: list, pat_values: list):
    """Average CFO/PAT over the supplied years -> (ratio, label).

    >1.0 = High Quality, 0.5-1.0 = Moderate, <0.5 = Accrual Risk.
    Returns (None, None) if there is no usable year (all PAT == 0).
    """
    ratios = []
    for cfo, pat in zip(cfo_values, pat_values):
        if pat in (None, 0):
            continue
        ratios.append(cfo / pat)
    if not ratios:
        return None, None
    avg = sum(ratios) / len(ratios)
    if avg > 1.0:
        label = "High Quality"
    elif avg >= 0.5:
        label = "Moderate"
    else:
        label = "Accrual Risk"
    return avg, label


def capex_intensity(investing_activity: float, sales: float):
    """CapEx intensity = |CFI| / sales * 100 -> (value, label). None if sales == 0."""
    if sales in (None, 0):
        return None, None
    value = abs(investing_activity or 0) / sales * 100
    if value < 3:
        label = "Asset Light"
    elif value <= 8:
        label = "Moderate"
    else:
        label = "Capital Intensive"
    return value, label


def fcf_conversion_rate(fcf: float, operating_profit: float):
    """FCF conversion = FCF / operating_profit * 100. None if operating_profit == 0."""
    if operating_profit in (None, 0):
        return None
    return fcf / operating_profit * 100


def _sign(x: float) -> str:
    """'+' if x > 0, '-' if x < 0, '0' if zero/None."""
    if x is None or x == 0:
        return "0"
    return "+" if x > 0 else "-"


def capital_allocation_pattern(cfo: float, cfi: float, cff: float,
                               cfo_pat_ratio: float = None):
    """Classify the (CFO, CFI, CFF) sign pattern into one of 8 labels.

    Returns (cfo_sign, cfi_sign, cff_sign, label).
    """
    so, si, sf = _sign(cfo), _sign(cfi), _sign(cff)
    key = (so, si, sf)

    labels = {
        ("+", "-", "-"): "Reinvestor",
        ("+", "+", "-"): "Liquidating Assets",
        ("-", "+", "+"): "Distress Signal",
        ("-", "-", "+"): "Growth Funded by Debt",
        ("+", "+", "+"): "Cash Accumulator",
        ("-", "-", "-"): "Pre-Revenue",
        ("+", "-", "+"): "Mixed",
    }
    label = labels.get(key, "Mixed")

    # Sub-classify the classic (+,-,-) when CFO/PAT is high -> Shareholder Returns
    if key == ("+", "-", "-") and cfo_pat_ratio is not None and cfo_pat_ratio > 1.5:
        label = "Shareholder Returns"

    return so, si, sf, label
