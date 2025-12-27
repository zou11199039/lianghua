# -*- coding: utf-8 -*-
"""ReceiptParser: normalize various broker/trader receipt formats into a canonical tuple
(order_id, status, info).

Supported heuristics for xtquant-like dicts and simple tuples.
"""
from typing import Any, Tuple, Optional


def _status_map(s: str) -> str:
    if s is None:
        return 'unknown'

    # numeric codes mapping (heuristic for some brokers): accept ints, floats, and numeric strings
    try:
        mapping = {
            0: 'rejected',
            1: 'filled',
            2: 'partial',
            3: 'canceled',
            4: 'failed'
        }
        if isinstance(s, (int, float)):
            return mapping.get(int(s), str(int(s)))
        # numeric string like '1' or ' 2 '
        if isinstance(s, str):
            s_str = s.strip()
            if s_str.isdigit():
                return mapping.get(int(s_str), s_str)
    except Exception:
        pass

    s_norm = str(s).strip().lower()
    if s_norm in ('filled', 'fill', 'filled_all', 'allfilled', 'filled_all'):
        return 'filled'
    if s_norm in ('partial', 'partial_fill'):
        return 'partial'
    if s_norm in ('reject', 'rejected', 'refuse', 'rej'):
        return 'rejected'
    if s_norm in ('fail', 'failed', 'error'):
        return 'failed'
    if s_norm in ('cancel', 'canceled', 'cancelled'):
        return 'canceled'
    # fallback: return normalized string
    return s_norm


def parse_receipt(raw: Any) -> Optional[Tuple[str, str, Optional[dict]]]:
    """Parse a raw receipt into (order_id, status, info).

    Returns None if cannot parse.
    """
    # If already a tuple (order_id, status, info)
    if isinstance(raw, tuple) and len(raw) >= 2:
        order_id = str(raw[0])
        status = _status_map(str(raw[1]))
        info = raw[2] if len(raw) >= 3 else None
        return order_id, status, info

    # If it's a dict, try to extract common fields
    if isinstance(raw, dict):
        # common keys for order id
        candidates = ['order_id', 'orderId', 'order_id', 'order_no', 'orderNo', 'orderno', 'orderNo', 'id', 'orderid', 'orderId']
        order_id = None
        for k in candidates:
            if k in raw:
                order_id = raw[k]
                break

        # check nested structures commonly used by xtquant or broker callbacks
        if order_id is None:
            for nest in ('order', 'data', 'body'):
                if nest in raw and isinstance(raw[nest], dict):
                    for k in candidates:
                        if k in raw[nest]:
                            order_id = raw[nest][k]
                            break
                    if order_id is not None:
                        break

        # status keys
        status_candidates = ['status', 'state', 'tradeStatus', 'order_status', 'statusCode', 'trade_status']
        status = None
        for k in status_candidates:
            if k in raw:
                status = raw[k]
                break
        # try nested status as well
        if status is None:
            for nest in ('order', 'data', 'body'):
                if nest in raw and isinstance(raw[nest], dict):
                    for k in status_candidates:
                        if k in raw[nest]:
                            status = raw[nest][k]
                            break
                    if status is not None:
                        break

        # map numeric codes or textual codes
        status = _status_map(status) if status is not None else 'unknown'

        # best-effort fallback: sometimes full JSON contains an 'orderno' inside strings
        if order_id is None:
            for v in raw.values():
                try:
                    s = str(v)
                    if 'ORD' in s or 'ord' in s:
                        # crude heuristic
                        order_id = s
                        break
                except Exception:
                    pass

        if order_id is None:
            return None
        info = raw
        return str(order_id), status, info

    # If it's a simple string containing id:status
    if isinstance(raw, str):
        if ':' in raw:
            order_id, st = raw.split(':', 1)
            return order_id.strip(), _status_map(st.strip()), None
    return None