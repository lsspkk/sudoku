# ratkaisija versio 2
#
# sudoku ruudukko on sellainen, jossa on 9 riviä ja 9 saraketta
# käytämme koordinaatteja x ja y
# x = rivi
# y = sarake
# jokaisessa ruudussa on numero 1-9 tai tyhjää
# ruudukko jakautuu osiin, joiden koko on 3x3
# jokaisessa osassa on 9 ruutua
# jokaisessa rivissä, sarakkeessa ja osassa on oltava kaikki numerot 1-9



def log(message):
    with open("log.txt", "a", encoding="utf-8") as f:
        f.write(str(message) + "\n")
    print(message)  # Keep console output for debugging

def clear_log():
    with open("log.txt", "w", encoding="utf-8") as f:
        f.write("")

data1 = """
7 - 4 5 - - 3 - -
9 - 6 7 - - - - 2 
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

    # transponoi ruudukon x ja y -akselit
    return list(zip(*ruudukko))


VIIVA = " +-------+-------+-------+"
KESKI = " |-------+-------+-------|"
# tulosta ruudukko siten että tulostat myös reunaviivat
# lisää tähän myös ullkokehys
def tulosta_ruudukko(ruudukko):
    log(VIIVA)
    for i in range(9):
        if i % 3 == 0 and i != 0:
            log(KESKI)
        rivi = " | "
        for j in range(9):
            if j % 3 == 0 and j != 0:
                rivi += "| "
            rivi += f"{ruudukko[i][j]} "
        rivi += "|"
        log(rivi)    
    log(VIIVA)


def viivoita_ruudukko(ruudukko):
    vastaus = VIIVA + "\n"
    for i in range(9):
        if i % 3 == 0 and i != 0:
            vastaus += KESKI + "\n"
        rivi = " | "
        for j in range(9):
            if j % 3 == 0 and j != 0:
                rivi += "| "
            rivi += f"{ruudukko[i][j]} "
        rivi += "|"
        vastaus += rivi + "\n"
    vastaus +=  VIIVA + "\n"
    return vastaus


def sudoku_valmis(ruudukko):
    for i in range(9):
        for j in range(9):
            if ruudukko[i][j] == TYHJA:
                return False
    return True


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
            print(f"x: {x} y: {y} arvo: {ruudukko[x][y]} laillinen: {onko_laillinen_paikka(ruudukko, numero, y, x)}")
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
                    log(f"numero {numero} löytyi paikka {paikka} viereisistä osista")
                    # lisätään paikka ja numero listaan
                    lisaykset.append((paikka[0], paikka[1], numero))
                    kaytetyt_paikat.add(paikka)
                    return  # vain yksi paikka kerrallaan


def etsi_joka_osasta_paikkaa_joka_numerolle(ruudukko, lisaykset, kaytetyt_paikat):
    for osa_x in range(3):
        for osa_y in range(3):
            for numero in range(1, 10):
                paikka = etsi_paikkaa_osassa(ruudukko, numero, (osa_x, osa_y))
                if paikka:
                    log(f"numero {numero} löytyi paikka {paikka} kokeilemalla jokaista numeroa osiin")
                    # lisätään paikka ja numero listaan
                    lisaykset.append((paikka[0], paikka[1], numero))
                    kaytetyt_paikat.add(paikka)
                    return  # vain yksi paikka kerrallaan





def suodata_lailliset_numerot(ruudukko, x, y, numerot):
    lailliset_numerot_paikkaan = []
    for numero in numerot:
        if onko_laillinen_paikka(ruudukko, numero, x, y):
            lailliset_numerot_paikkaan.append(numero)
    return lailliset_numerot_paikkaan


def poimi_rivilta_puuttuvat_numerot(ruudukko, y):
    puuttuvat_numerot = set(range(1, 10))
    for x in range(9):
        numero = ruudukko[x][y]
        if numero != TYHJA:
            puuttuvat_numerot.discard(numero)
    return puuttuvat_numerot


def poimi_rivilta_vapaat_paikat(ruudukko, y):
    vapaat_paikat = []
    for x in range(9):
        if ruudukko[x][y] == TYHJA:
            vapaat_paikat.append((x, y))
    return vapaat_paikat

def etsi_joka_vaakarivilta_paikkaa(ruudukko, lisaykset, kaytetyt_paikat):
    for y in range(9):
        puuttuvat_numerot = poimi_rivilta_puuttuvat_numerot(ruudukko, y)
        vapaat_paikat = poimi_rivilta_vapaat_paikat(ruudukko, y)
        if len(puuttuvat_numerot) > 4:
            continue

        #log(f"vaakarivillä {y} puuttuvat numerot {puuttuvat_numerot} vapaat paikat {vapaat_paikat}")
        for numero in puuttuvat_numerot:
            lailliset_paikat = etsi_paikkaa_listasta(ruudukko, numero, vapaat_paikat)
            #log(f"numero {numero} löytyi paikkoja {lailliset_paikat} vaakariviltä")
            if len(lailliset_paikat) != 1:
                continue

            (x, y) = lailliset_paikat[0]
            log(f"numero {numero} löytyi paikka {x}, {y} vaakariviltä")
            # lisätään paikka ja numero listaan
            lisaykset.append((x, y, numero))
            kaytetyt_paikat.add((x, y))
            return

def poimi_pystyrivilta_vapaat_paikat(ruudukko, x):
    vapaat_paikat = []
    for y in range(9):
        if ruudukko[x][y] == TYHJA:
            vapaat_paikat.append((x, y))
    return vapaat_paikat

def poimi_pystyrivilta_puuttuvat_numerot(ruudukko, x):
    puuttuvat_numerot = set(range(1, 10))
    for y in range(9):
        numero = ruudukko[x][y] # miksi näin päin
        if numero != TYHJA:
            puuttuvat_numerot.discard(numero)
    return puuttuvat_numerot

def etsi_paikkaa_listasta(ruudukko, numero, vapaat_paikat):
    lailliset_paikat = []
    for paikka in vapaat_paikat:
        if onko_laillinen_paikka(ruudukko, numero, paikka[0], paikka[1]):
            lailliset_paikat.append(paikka)
    return lailliset_paikat

def etsi_joka_pystyrivilta_paikkaa(ruudukko, lisaykset, kaytetyt_paikat):
    for x in range(9):
        puuttuvat_numerot = poimi_pystyrivilta_puuttuvat_numerot(ruudukko, x)
        vapaat_paikat = poimi_pystyrivilta_vapaat_paikat(ruudukko, x)
        if len(puuttuvat_numerot) > 4:
            continue

        #log(f"pystysarakkeella {x} puuttuvat numerot {puuttuvat_numerot} vapaat paikat {vapaat_paikat}")
        for numero in puuttuvat_numerot:
            lailliset_paikat = etsi_paikkaa_listasta(ruudukko, numero, vapaat_paikat)
            # log(f"numero {numero} löytyi paikkoja {lailliset_paikat} pystysarakkeelta")
            if len(lailliset_paikat) != 1:
                continue

            (x, y) = lailliset_paikat[0]
            log(f"numero {numero} löytyi paikka {x}, {y} pystysarakkeelta")
            # lisätään paikka ja numero listaan
            lisaykset.append((x, y, numero))
            kaytetyt_paikat.add((x, y))
            return


def osa(ruutu):
    osa_x = ruutu[0] // 3
    osa_y = ruutu[1] // 3
    return (osa_x, osa_y)

# Nuppu keksi Pallon käsitteen
#
# Pallo on sellainen pysty tai vaaka-alue yhden osan sisällä, josta tiedetään, 
# että sen ruudoissa on tiettyjä numeroita. Pallon koko voi olla 2 tai 3 ruutua.
# Kun pallo on täynnä numeroita, sitä voidaan hyödyntää sudokun ratkaisemiseen.
# Riviltä tai sarakkeelta voidaan pallon avulla poissulkea pallon numerot, 
# vaikka niiden tarkka sijainti ei ole tiedossa.
# Pallon numeroista voi myös päätellä, että pallon numeroita ei tule saman osan
# sisällä oleviin muihin riveihin tai sarakkeisiin.
class Pallo:
    osa: tuple
    numerot: list
    ruudut: list
    vaakasuunta: bool

    def __init__(self, osa, numero, ruudut, vaakasuunta):
        self.osa = osa
        self.numerot = [numero]
        self.ruudut = ruudut
        self.vaakasuunta = vaakasuunta

    def __str__(self):
        return f"Pallon vaakasuunta {self.vaakasuunta} osa {self.osa[0]} {self.osa[1]} numero {self.numerot} ruudut {self.ruudut}"

    def taynna(self):
        return len(self.ruudut) == len(self.numerot)
    
    def lisaa_numero(self, numero, ruutu):
        if numero in self.numerot:
            return
        self.numerot.append(numero)

    def on_numero(self, numero):
        return numero in self.numerot
    
    def voiko_ruudun_lisata(self, ruutu):
        if ruutu in self.ruudut:
            return False
        ruutuOsa = osa(ruutu)
        if ruutuOsa != self.osa:
            return False
        if len(self.ruudut) == 3:
            return False
        if self.vaakasuunta:
            y = ruutu[1]
            x = ruutu[0]
            for i in range(3):
                xx = self.osa[0]*3 + i
                mukana = False
                for n in self.ruudut:
                    if n[0] == xx:
                        mukana = True
                        break
                if not mukana:
                    return True
        if not self.vaakasuunta:
            y = ruutu[1]
            x = ruutu[0]
            for i in range(3):
                yy = self.osa[1]*3 + i
                mukana = False
                for n in self.ruudut:
                    if n[1] == yy:
                        mukana = True
                        break
                if not mukana:
                    return True
        return False
    
    def lisaa_numero(self, numero, ruudut):
        print(f"lisataan numero {numero} palloon jonka ruudut ovat {self.ruudut}")  
        for ruutu in ruudut:
            if self.voiko_ruudun_lisata(ruutu):
                self.ruudut.append(ruutu)
            else:
                print(f"ruutua {ruutu} ei voi lisata palloon jonka ruudut ovat {self.ruudut}")
        self.numerot.append(numero)

    def samat_rivit(self, ruudut):
        for ruutu in ruudut:
            ruutu_y = ruutu[1]
            for pallo_ruutu in self.ruudut:
                if pallo_ruutu[1] != ruutu_y:
                    return False
        return True


# pitäisi käydä osan joka ruutu, ja jos on eri vaakarivi ja laillinen paikka, niin ei sovi
# return false
# jos on sama vaakarivi, ja laillinen paikka, niin sopii
# kun kaikki osan numerot on käyty läpi, return true
def numero_sopii_yhteen_vaakaan_osassa(ruudukko, numero, osa_x, osa_y):
    ruudut = []
    vaaka_y = None
    for i in range(3):
        y = osa_y*3 + i
        for j in range(3):
            x = osa_x*3 + j
            print(f"vaaka_y: {vaaka_y} y: {y} x: {x} merkki: {ruudukko[x][y]}")
            if ruudukko[x][y] == TYHJA:
                laillinen = onko_laillinen_paikka(ruudukko, numero, x, y) 
                if laillinen and vaaka_y is None or vaaka_y == y:
                    print(f"laillinen vaaka_y: {vaaka_y} y: {y} x: {x}")
                    vaaka_y = y
                    ruudut.append((x, y))
                    print(f"ruudut: {ruudut}")               

                elif laillinen:
                    # ei sovi, koska toiseen vaakariviin löytyi laillinen paikka
                    return None
    if len(ruudut) < 2:
        return None
    return Pallo((osa_x, osa_y), numero, ruudut, vaakasuunta=True)

def numero_sopii_yhteen_pystyyn_osassa(ruudukko, numero, osa_x, osa_y):
    ruudut = []
    pysty_x = None
    for i in range(3):
        x = osa_x*3 + i
        for j in range(3):
            y = osa_y*3 + j
            if ruudukko[x][y] == TYHJA:
                laillinen = onko_laillinen_paikka(ruudukko, numero, x, y) 
                if laillinen and pysty_x is None or pysty_x == x:
                    pysty_x = x
                    ruudut.append((x, y))
                elif laillinen:
                    # ei sovi, koska toiseen pystysarakkeeseen löytyi laillinen paikka
                    return None
    if len(ruudut) < 2:
        return None
    return Pallo((osa_x, osa_y), numero, ruudut, vaakasuunta=False)


def etsi_pallot(ruudukko):
    pallot = []
    for osa_x in range(3):
        for osa_y in range(3):
            for numero in range(1, 10):
                vaaka_pallo = numero_sopii_yhteen_vaakaan_osassa(ruudukko, numero, osa_x, osa_y)

                if vaaka_pallo:
                    sopiva = poimi_vanha_sopiva_pallo(numero, pallot, vaaka_pallo)
                    if sopiva and not sopiva.on_numero(numero):
                        sopiva.lisaa_numero(numero, vaaka_pallo.ruudut)
                    else:
                        pallot.append(vaaka_pallo)

                pysty_pallo = numero_sopii_yhteen_pystyyn_osassa(ruudukko, numero, osa_x, osa_y)
                if pysty_pallo:
                    sopiva = poimi_vanha_sopiva_pallo(numero, pallot, pysty_pallo)
                    if sopiva and not sopiva.on_numero(numero):
                        sopiva.lisaa_numero(numero, pysty_pallo.ruudut)
                    else:
                        pallot.append(pysty_pallo)
    return pallot

def poimi_vanha_sopiva_pallo(numero, pallot, uusi_pallo):
    for pallo in pallot:
        if pallo.vaakasuunta == uusi_pallo.vaakasuunta and pallo.osa == uusi_pallo.osa:
            if pallo.samat_rivit(uusi_pallo.ruudut) and not pallo.on_numero(numero):
                return pallo
    return None

def kokeile_rivi_kerrallaan_numeroita(ruudukko):

    # etene rivi kerrallaan, jos numero on numero,
    # kutsu etsi_paikkaa(ruudukko, rivi, sarake, numero)

    lisaykset = []
    kaytetyt_paikat = set() 

    etsi_joka_osasta_paikkaa_joka_numerolle(ruudukko, lisaykset, kaytetyt_paikat)
    
    if len(lisaykset) == 0: etsi_joka_vaakarivilta_paikkaa(ruudukko, lisaykset, kaytetyt_paikat)
    if len(lisaykset) == 0: etsi_joka_pystyrivilta_paikkaa(ruudukko, lisaykset, kaytetyt_paikat)
    if len(lisaykset) == 0: etsi_joka_numerolle_paikkaa_viereisista_osista(ruudukko, lisaykset, kaytetyt_paikat)
    if len(lisaykset) == 0: 
        pallot = etsi_pallot(ruudukko) 
    if len(lisaykset) == 0:
        return 0
    
    log(f"Lisätään {len(lisaykset)} numeroa ruudukkoon")
    for lisays in lisaykset:
        x, y, numero = lisays
        if ruudukko[x][y] == TYHJA:  # Only place if the position is empty
            ruudukko[x][y] = numero
            log(f"Lisätty numero {numero} paikkaan ({x}, {y})")

    return len(lisaykset)


def ratkaise_sudoku(ruudukko):
    kierrokset = 0
    loytyi_paikkoja = 1
    while loytyi_paikkoja > 0:
        log(f"\nKierros {kierrokset + 1}:")
        tulosta_ruudukko(ruudukko)
        loytyi_paikkoja = kokeile_rivi_kerrallaan_numeroita(ruudukko)
        # log(f"Löydettiin {loytyi_paikkoja} paikkaa")
        kierrokset += 1

    log(f"\nLopullinen tulos:")
    log(f"kierroksia: {kierrokset}")

    return kierrokset


# testaa ohjelma    
if __name__ == "__main__":

    clear_log()

    ruudukko = lue_ruudukko(data1)

    ratkaise_sudoku(ruudukko)
    tulosta_ruudukko(ruudukko)

