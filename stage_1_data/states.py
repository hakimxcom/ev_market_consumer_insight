"""
states.py — one shared crosswalk for the 50 states + DC: two-letter code, full name, Census FIPS.

WHY: sources name states differently (Alliance uses "MI", Census and Google Trends use
"Michigan", Census also uses FIPS "26"). Every script converts through this table so a
misspelled or extra name fails loudly instead of silently dropping a row in a join.

USE      from states import to_abbr, STATES
OUTPUTS  none (imported by other scripts)
"""
import pandas as pd

_ROWS = [
    ("AL", "Alabama", 1), ("AK", "Alaska", 2), ("AZ", "Arizona", 4), ("AR", "Arkansas", 5),
    ("CA", "California", 6), ("CO", "Colorado", 8), ("CT", "Connecticut", 9), ("DE", "Delaware", 10),
    ("DC", "District of Columbia", 11), ("FL", "Florida", 12), ("GA", "Georgia", 13), ("HI", "Hawaii", 15),
    ("ID", "Idaho", 16), ("IL", "Illinois", 17), ("IN", "Indiana", 18), ("IA", "Iowa", 19),
    ("KS", "Kansas", 20), ("KY", "Kentucky", 21), ("LA", "Louisiana", 22), ("ME", "Maine", 23),
    ("MD", "Maryland", 24), ("MA", "Massachusetts", 25), ("MI", "Michigan", 26), ("MN", "Minnesota", 27),
    ("MS", "Mississippi", 28), ("MO", "Missouri", 29), ("MT", "Montana", 30), ("NE", "Nebraska", 31),
    ("NV", "Nevada", 32), ("NH", "New Hampshire", 33), ("NJ", "New Jersey", 34), ("NM", "New Mexico", 35),
    ("NY", "New York", 36), ("NC", "North Carolina", 37), ("ND", "North Dakota", 38), ("OH", "Ohio", 39),
    ("OK", "Oklahoma", 40), ("OR", "Oregon", 41), ("PA", "Pennsylvania", 42), ("RI", "Rhode Island", 44),
    ("SC", "South Carolina", 45), ("SD", "South Dakota", 46), ("TN", "Tennessee", 47), ("TX", "Texas", 48),
    ("UT", "Utah", 49), ("VT", "Vermont", 50), ("VA", "Virginia", 51), ("WA", "Washington", 53),
    ("WV", "West Virginia", 54), ("WI", "Wisconsin", 55), ("WY", "Wyoming", 56),
]
STATES = pd.DataFrame(_ROWS, columns=["state", "state_name", "fips"])
_NAME_TO_ABBR = dict(zip(STATES.state_name, STATES.state))
assert len(STATES) == 51 and STATES.state.is_unique and STATES.fips.is_unique


def to_abbr(names: pd.Series, source: str) -> pd.Series:
    """Map full state names to two-letter codes; raise if any name is unknown."""
    out = names.map(_NAME_TO_ABBR)
    unknown = names[out.isna()].unique().tolist()
    if unknown:
        raise ValueError(f"{source}: unrecognized state names {unknown}")
    return out
