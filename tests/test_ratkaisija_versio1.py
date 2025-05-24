from dotenv import load_dotenv
load_dotenv()
import sys, os
sys.path.insert(0, os.getenv('PYTHONPATH', 'src'))
import pytest
from ratkaisija import lue_ruudukko, onko_laillinen_paikka, TYHJA

def test_lue_ruudukko():
    data = """
    1 2 3 4 5 6 7 8 9
    - - - - - - - - -
    - - - - - - - - -
    - - - - - - - - -
    - - - - - - - - -
    - - - - - - - - -
    - - - - - - - - -
    - - - - - - - - -
    - - - - - - - - -
    """
    ruudukko = lue_ruudukko(data)
    assert len(ruudukko) == 9
    assert len(ruudukko[0]) == 9
    assert ruudukko[0][0] == 1
    assert ruudukko[1][0] == TYHJA

def test_onko_laillinen_paikka():
    data = """
    1 2 3 4 5 6 7 8 9
    - - - - - - - - -
    - - - - - - - - -
    - - - - - - - - -
    - - - - - - - - -
    - - - - - - - - -
    - - - - - - - - -
    - - - - - - - - -
    - - - - - - - - -
"""
    ruudukko = lue_ruudukko(data)
    # Test placing 1 in first row (should be illegal)
    assert not onko_laillinen_paikka(ruudukko, 1, 0, 0)
    # Test placing 2 in first row (should be illegal)
    assert not onko_laillinen_paikka(ruudukko, 2, 0, 1)
    # Test placing 1 in empty spot (should be legal)
    assert onko_laillinen_paikka(ruudukko, 1, 1, 0) 