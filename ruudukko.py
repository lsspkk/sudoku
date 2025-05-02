# sudoku ruudukko on sellainen, jossa on 9 riviä ja 9 saraketta
# käytämme koordinaatteja x ja y
# x = rivi
# y = sarake
# jokaisessa ruudussa on numero 1-9 tai tyhjää
# ruudukko jakautuu osiin, joiden koko on 3x3
# jokaisessa osassa on 9 ruutua
# jokaisessa rivissä, sarakkeessa ja osassa on oltava kaikki numerot 1-9

data1 = """
7 - 4 5 - - 3 - -
8 - 6 7 - - - - 2 
2 1 - 6 9 - - - - 
- 6 - 4 - 5 - 3 9
- 7 8 - - - - - - 
- 3 - - - - 2 4 -
- - - - - - - - 8
8 2 7 1 - 9 5 - - 
- - - - - - - 1 - 
"""

TYHJA = "-"

def lue_ruudukko(data):
    ruudukko = []
    for rivi in data.splitlines():
        if rivi.strip() == "":
            continue
        rivi_lista = []
        for numero in rivi.split():
            if numero == "-":
                rivi_lista.append(TYHJA)
            else:
                rivi_lista.append(int(numero))
        ruudukko.append(rivi_lista)
    return ruudukko


VIIVA = " +-------+-------+-------+"
KESKI = " |-------+-------+-------|"
# tulosta ruudukko siten että tulostat myös reunaviivat
# lisää tähän myös ullkokehys
def tulosta_ruudukko(ruudukko):
    print(VIIVA)
    for i in range(9):
        if i % 3 == 0 and i != 0:
            print(KESKI)
        print(" | ", end="")
        for j in range(9):
            if j % 3 == 0 and j != 0:
                print("| ", end="")
            print(f"{ruudukko[i][j]} ", end="")
        print("|")    
    print(VIIVA)


def onko_numero_rivilla(ruudukko, numero, x):
    for i in range(9):
        if ruudukko[x][i] == numero:
            return True
    return False

def onko_numero_sarakkeella(ruudukko, numero, y):
    for i in range(9):
        if ruudukko[i][y] == numero:
            return True
    return False

def onko_numero_osassa(ruudukko, numero, osa):
    alku_x = osa[0]*3
    alku_y = osa[1]*3
    for i in range(3):
        for j in range(3):
            if ruudukko[alku_x + i][alku_y + j] == numero:
                return True
    return False

def onko_laillinen_paikka(ruudukko, numero, x, y):
    if ruudukko[x][y] != TYHJA:
        return False
    
    # Check row
    if onko_numero_rivilla(ruudukko, numero, x):
        return False
    
    if onko_numero_sarakkeella(ruudukko, numero, y):
        return False
    
    if onko_numero_osassa(ruudukko, numero, (x//3, y//3)):
        return False
    
    return True


def etsi_paikkaa_osassa(ruudukko, numero, osa):

    lailliset_paikat = []

    x_lisays = osa[0]*3
    y_lisays = osa[1]*3
    for xx in range(3):
        x = x_lisays + xx
        for yy in range(3):
            y = y_lisays + yy

            if onko_laillinen_paikka(ruudukko, numero, x, y):
                lailliset_paikat.append((x, y))
            if len(lailliset_paikat) == 2:
                return None

    if len(lailliset_paikat) == 1:
        return lailliset_paikat[0]
    return None


def onko_numero_osassa(ruudukko, numero, osa):

    x_lisays = osa[0]*3
    y_lisays = osa[1]*3
    for xx in range(3):
        for yy in range(3):
            x = x_lisays + xx
            y = y_lisays + yy
            if ruudukko[x][y] == numero:
                return True
    return False


def etsi_paikkaa_viereisista_osien_listasta(ruudukko, numero, osalista):

    osa_ilman_numeroa = []
    for osa in osalista:
        if not onko_numero_osassa(ruudukko, numero, osa):
            osa_ilman_numeroa.append(osa)

    if len(osa_ilman_numeroa) == 1:
        return etsi_paikkaa_osassa(ruudukko, numero, osa_ilman_numeroa[0])
    return None


def etsi_paikkaa_viereisista_osista(ruudukko, numero, x, y):

    # katso missä osassa numero on
    osa_x = x % 3
    osa_y = y % 3

    # selvita viereiset osat listaksi
    viereisten_osien_listat = []

    rivi = []
    sarake = []
    for xx in range(3):
        rivi.append((xx, osa_y))

    for yy in range(3):
        sarake.append((osa_x, yy))

    viereisten_osien_listat.append(rivi)
    viereisten_osien_listat.append(sarake)


    # tulosta numero ja tutkittavat osalistat
    # print(f"numero {numero} osassa {osa_x} {osa_y} tutkitaan osia {viereisten_osien_listat}")
    

    for osalista in viereisten_osien_listat:
        paikka = etsi_paikkaa_viereisista_osien_listasta(ruudukko, numero, osalista)
        if paikka:
            return paikka
    return None

def etsi_joka_numerolle_paikkaa_viereisista_osista(ruudukko, lisaykset, kaytetyt_paikat):
    for x in range(9):
        for y in range(9):            
            numero = ruudukko[x][y]
            if numero != TYHJA:
                paikka = etsi_paikkaa_viereisista_osista(ruudukko, numero, x, y)
                if paikka and paikka not in kaytetyt_paikat:
                    print(f"numero {numero} löytyi paikka {paikka} viereisistä osista")
                    # lisätään paikka ja numero listaan
                    lisaykset.append((paikka[0], paikka[1], numero))
                    kaytetyt_paikat.add(paikka)


def etsi_joka_osasta_paikkaa_joka_numerolle(ruudukko, lisaykset, kaytetyt_paikat):
    for osa_x in range(3):
        for osa_y in range(3):
            for numero in range(1, 10):
                paikka = etsi_paikkaa_osassa(ruudukko, numero, (osa_x, osa_y))
                if paikka:
                    print(f"numero {numero} löytyi paikka {paikka} kokeilemalla jokaista numeroa osiin")
                    # lisätään paikka ja numero listaan
                    lisaykset.append((paikka[0], paikka[1], numero))
                    kaytetyt_paikat.add(paikka)

def kokeile_rivi_kerrallaan_numeroita(ruudukko):

    # etene rivi kerrallaan, jos numero on numero,
    # kutsu etsi_paikkaa(ruudukko, rivi, sarake, numero)

    lisaykset = []
    kaytetyt_paikat = set()  # Keep track of positions we've already found

    etsi_joka_osasta_paikkaa_joka_numerolle(ruudukko, lisaykset, kaytetyt_paikat)
    etsi_joka_numerolle_paikkaa_viereisista_osista(ruudukko, lisaykset, kaytetyt_paikat)

    if len(lisaykset) == 0:
        return 0
    
    print(f"Lisätään {len(lisaykset)} numeroa ruudukkoon")
    for lisays in lisaykset:
        x, y, numero = lisays
        if ruudukko[x][y] == TYHJA:  # Only place if the position is empty
            ruudukko[x][y] = numero
            print(f"Lisätty numero {numero} paikkaan ({x}, {y})")

    return len(lisaykset)


# testaa ohjelma    
if __name__ == "__main__":

    ruudukko = lue_ruudukko(data1)

    kierrokset = 0
    loytyi_paikkoja = 1
    while loytyi_paikkoja > 0:
        print(f"\nKierros {kierrokset + 1}:")
        tulosta_ruudukko(ruudukko)
        loytyi_paikkoja = kokeile_rivi_kerrallaan_numeroita(ruudukko)
        print(f"Löydettiin {loytyi_paikkoja} paikkaa")
        kierrokset += 1

    print(f"\nLopullinen tulos:")
    print(f"kierroksia: {kierrokset}")
    tulosta_ruudukko(ruudukko)

