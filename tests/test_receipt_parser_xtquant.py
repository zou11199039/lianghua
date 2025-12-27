import pytest
from src.trading.receipt_parser import parse_receipt


def test_numeric_status_int():
    raw = {'orderId': '123', 'status': 1}
    parsed = parse_receipt(raw)
    assert parsed is not None
    oid, status, info = parsed
    assert oid == '123'
    assert status == 'filled'
    assert info == raw


def test_numeric_status_string():
    raw = {'orderId': '234', 'status': '1'}
    parsed = parse_receipt(raw)
    assert parsed is not None
    assert parsed[1] == 'filled'


def test_nested_status_and_order():
    raw = {'data': {'order_no': 'ord-345', 'statusCode': 2}}
    parsed = parse_receipt(raw)
    assert parsed is not None
    oid, status, info = parsed
    assert oid == 'ord-345'
    assert status == 'partial'


def test_tuple_input():
    raw = ('abc', 'filled')
    parsed = parse_receipt(raw)
    assert parsed == ('abc', 'filled', None)


def test_string_input():
    raw = 'ord-1:filled'
    parsed = parse_receipt(raw)
    assert parsed == ('ord-1', 'filled', None)


def test_fallback_order_in_values():
    raw = {'meta': 'received ord-987 at 10:00', 'status': 'unknown'}
    parsed = parse_receipt(raw)
    assert parsed is not None
    oid, status, info = parsed
    assert 'ord-987' in oid
    assert status == 'unknown'


def test_no_order_id_returns_none():
    raw = {'status': 1}
    assert parse_receipt(raw) is None
