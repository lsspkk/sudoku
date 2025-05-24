from dotenv import load_dotenv
load_dotenv()
import sys, os
sys.path.insert(0, os.getenv('PYTHONPATH', 'src'))
import pytest
from ratkaisija import lue_ruudukko, numero_sopii_yhteen_vaakaan_osassa, etsi_paikkaa_osassa    

# x-akseli vaakaan, y-akseli pystyyn, origo vasemmassa yläkulmassa
def test_etsi_paikkaa_osassa():
    data = """
    1 - - - - - 4 - -
    2 - - - 3 6 - - -
    3 - 4 5 - - - - -
    6 - - 3 2 1 4 - -
    7 - - - - 4 - - -
    - - - - - - - - -
    - 5 3 - - - - - -
    4 6 2 - - - - - -
    - 7 - - - - - - -
"""
    ruudukko = lue_ruudukko(data)
    assert (1, 5) == etsi_paikkaa_osassa(ruudukko, 4, (0, 1))
    assert (3, 1) == etsi_paikkaa_osassa(ruudukko, 4, (1, 0))

    assert 2 == ruudukko[0][1]
    assert 4 == ruudukko[6][0]


def test_sopiiko_numero_vain_vaakaan_osassa():
    data = """
    1 - - 4 - - 3 - -
    2 - - - 5 3 - - -
    3 - - - - 6 - - 2
    - - - 3 2 1 - - -
    - - - - - - - - -
    - - - 5 - - 2 - -
    - - 3 - - 2 - - -
    6 7 - - - 5 - 2 -
    - - - - - 7 - - -
"""
    ruudukko = lue_ruudukko(data)
    pallo = numero_sopii_yhteen_vaakaan_osassa(ruudukko, 2, 0, 1)
    assert pallo is not None
    assert pallo.vaakasuunta == True
    assert pallo.osa == (0, 1)
    assert pallo.ruudut == [(1, 4), (2, 4)]
    assert pallo.numerot == [2]




