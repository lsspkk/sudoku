import uuid
import json
from ratkaisija import lue_ruudukko, ratkaise_sudoku, viivoita_ruudukko, sudoku_valmis


# tiedosto jossa sudoku ruudukot formaatissa 2, mukana reunat
tiedosto = "logs/grids.txt"


# JSON-tiedosto, johon lokitetaan sudoku ja sen ratkaisuyritys
ratkaisu_tiedosto = "logs/ratkaisut.json" 

debug_tiedosto = "logs/syottaja_debug.txt" 
info_tiedosto = "logs/syottaja_info.txt"



def debug(msg):
    with open(debug_tiedosto, "a") as f:
        f.write(msg + "\n")
        f.flush()

def info(msg):
    with open(info_tiedosto, "a") as f:
        f.write(msg + "\n")
        f.flush()


# sudoku on luokka jossa on kentät 
# ruudukko
# nimi
# ratkaisu: sudoku ratkaistuna niin pitkälle kuin on pystytty
# ratkaisun_kierrokset: kuinka monta numeroa on lisätty
# valmis: onko sudoku valmis
class Sudoku:
    def __init__(self, ruudukko, nimi, tiedosto):
        self.id = uuid.uuid4().hex[:8]
        self.ruudukko = ruudukko
        self.tiedosto = tiedosto
        self.nimi = nimi
        self.ratkaisu = None
        self.ratkaisun_kierrokset = 0
        self.valmis = False

    @classmethod
    def from_json(cls, d):
        obj = cls(d['ruudukko'], d['nimi'], d['tiedosto'])
        obj.id = d.get('id', uuid.uuid4().hex[:8])
        obj.ratkaisu = d.get('ratkaisu')
        obj.ratkaisun_kierrokset = d.get('ratkaisun_kierrokset', 0)
        obj.valmis = d.get('valmis', False)
        return obj

    def __str__(self):
        return f"({self.nimi},\n{viivoita_ruudukko(self.ruudukko)})"


# lukee sudokun riveistä, joissa on tiedosto ja nimi sekä ruudukko
# ruudukon formaatti on kuvattu tiedostossa sudoku_definition.md
# otsikolla ## Format With Borders
def parsi_sudoku(lines):

    nimi = None
    tiedosto = None
    try:
        nimi = lines[1].replace("Ruudukko: ", "").strip()
        tiedosto = lines[0].replace("Tiedosto: ", "").strip()
        if tiedosto.startswith("Source file: "):
            tiedosto = tiedosto.replace("Source file: ", "").strip()
        ruudukko_lines = []
        for line in lines[2:]:
            line = line.strip()
            if line.startswith("Tiedosto") or line.startswith("Source file") or line.startswith("Nimi"):
                continue
            if line.startswith("+"):
                continue
            rivi = line.replace("|", "").replace("  ", " ").strip()
            if rivi == "":
                continue
            ruudukko_lines.append(rivi)

        ruudukko_data = "\n".join(ruudukko_lines)


        ruudukko = lue_ruudukko(ruudukko_data)    

        sudoku = Sudoku(ruudukko, nimi, tiedosto)
        # kopioi ruudukko myös ratkaisuun, koska ratkaisu tapahtuu paikallaan
        sudoku.ratkaisu = []
        for rivi in ruudukko:
            sudoku.ratkaisu.append(rivi.copy())

        return sudoku
    except Exception as e:
        info("Virhe parsimisessa sudokua " + nimi + ": " + str(e))
        return None

def lue_sudokut():
    sudokut = []
    joukot = []
    lines = []

    with open(tiedosto, "r") as f:
        lines = f.readlines()

    info("Luettu tiedosto: " + tiedosto + " rivit: " + str(len(lines)))

    alkurivinumero = 0
    loppurivinumero = 0
    # järjestä rivit joukkoihin siten että joukko alkaa rivillä, joka alkaa sanalla "Tiedosto"
    for i, line in enumerate(lines):
        debug(str(i) + ": " + line.strip())
        if line.strip().startswith("Tiedosto") or line.strip().startswith("Source file") and loppurivinumero > 0:
            joukot.append(lines[alkurivinumero:loppurivinumero])
            # alkurivinumero on rivin numero, jossa joukko alkaa
            alkurivinumero = i
            loppurivinumero = i
            #print(joukot[len(joukot)-1])
            #input("haloo")
        else:
            loppurivinumero += 1
    # lisää viimeinen joukko
    if loppurivinumero > alkurivinumero:
        joukot.append(lines[alkurivinumero:loppurivinumero])

    info("Löydetty " + str(len(joukot)) + " joukkoa, joista luetaan sudokut")

    for i, j in enumerate(joukot):
        sudoku = parsi_sudoku(j)
        if sudoku is not None:
            sudokut.append(sudoku)

    return sudokut


def printtaa_json(tiedosto, sudokut):
    out = {"sudokut": []}
    for sudoku in sudokut:
        obj = {
            "id": sudoku.id,
            "nimi": sudoku.nimi,
            "tiedosto": sudoku.tiedosto,
            "ratkaisun_kierrokset": sudoku.ratkaisun_kierrokset,
            "valmis": sudoku.valmis,
            "ruudukko": sudoku.ruudukko,
            "ratkaisu": sudoku.ratkaisu
        }
        out["sudokut"].append(obj)
    with open(tiedosto, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    sudokut = lue_sudokut()
    for index, sudoku in enumerate(sudokut):

        kierroksia = ratkaise_sudoku(sudoku.ratkaisu)
        sudoku.ratkaisun_kierrokset = kierroksia
        sudoku.valmis = sudoku_valmis(sudoku.ratkaisu)

    printtaa_json(ratkaisu_tiedosto, sudokut)
