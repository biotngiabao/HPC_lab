# analysis/module/datastore.py
from collections import defaultdict, deque
from typing import Any, Dict, Deque, Tuple

# (hostname, metric) -> deque
HISTORY: Dict[Tuple[str, str], Deque[Dict[str, Any]]] = defaultdict(
    lambda: deque(maxlen=15)
)

# (hostname, metric) -> unit string
UNITS: Dict[Tuple[str, str], str] = {}
