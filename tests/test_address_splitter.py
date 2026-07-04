import pytest
from app import split_address

def test_split_address_slashed_house_no():
    # Slashed house numbers
    res = split_address("113/110 AGARWAL FARM MANSAROVAR JAIPUR 302020")
    assert res["house_no"] == "113/110"
    assert "113/110" not in res["colony"]
    assert res["area"] == "MANSAROVAR"
    assert res["city"] == "JAIPUR"
    assert res["pincode"] == "302020"

def test_split_address_hyphenated_house_no():
    # Hyphenated house numbers
    res = split_address("A-45 PATRAKAR COLONY SANGANER JAIPUR 302029")
    assert res["house_no"] == "A-45"
    assert "A-45" not in res["colony"]
    assert res["area"] == "PATRAKAR COLONY"
    assert res["pincode"] == "302029"

def test_split_address_no_house_no():
    # Address with no clear house number
    res = split_address("AGARWAL FARM MANSAROVAR JAIPUR")
    assert res["house_no"] == "00"
    assert res["area"] == "MANSAROVAR"
    assert "MANSAROVAR" not in res["colony"]

def test_split_address_standard_plot():
    # Standard format with keyword plot
    res = split_address("PLOT NO 45, PATRAKAR COLONY, JAIPUR")
    assert res["house_no"] == "45"
    assert "PLOT" not in res["colony"]
    assert "45" not in res["colony"]
