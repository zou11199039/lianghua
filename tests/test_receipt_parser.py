# -*- coding: utf-8 -*-
from src.trading.receipt_parser import parse_receipt


def test_parse_tuple_receipt():
    res = parse_receipt(('ORD-1', 'filled', {'x':1}))
    assert res == ('ORD-1', 'filled', {'x':1})


def test_parse_dict_receipt_order_id_status():
    raw = {'orderId':'ABC123', 'status':'filled', 'extra':42}
    res = parse_receipt(raw)
    assert res[0] == 'ABC123'
    assert res[1] == 'filled'
    assert isinstance(res[2], dict)


def test_parse_string_receipt():
    res = parse_receipt('ORD-2:filled')
    assert res == ('ORD-2','filled',None)


def test_unknown_format_returns_none():
    assert parse_receipt(12345) is None
