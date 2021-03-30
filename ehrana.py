from bs4 import BeautifulSoup
import requests
import matplotlib.pyplot as plt
import numpy as np

#za bazo podatkov bomo ustvarili slovar, ki bo kot ključe shranil imena restavracij
#kot vrednost pa objekte z njenimi podatki
vse_restavracije = dict()

#ustvarimo razred
class Restavracija:
    def __init__(self, ime, mesto, ocena = 0, st_bon = 'Ne', cena_st_bon = 0, ponudba = []):
        self.ime = ime
        self.mesto = mesto
        self.ocena = ocena
        self.st_bon = st_bon
        self.cena_st_bon = cena_st_bon
        self.ponudba = ponudba
    
    def __str__(self):
        if self.st_bon == 'Ne':
            return f'| {self.ime:<10s} | {self.mesto:2s} | {self.ocena:2f} | {", ".join(self.ponudba)} |'
        return f'| {self.ime:<10s} | {self.mesto:2s} | {self.ocena:2f} | {self.cena_st_bon:2f} | {", ".join(self.ponudba)} |'
    
    def __repr__(self):
        if self.st_bon == 'Ne':
            return f'Restavracija({self.ime}, {self.mesto}, {self.ocena}, {self.ponudba})'
        return f'Restavracija({self.ime}, {self.mesto}, {self.cena_st_bon}, {self.ocena}, {self.ponudba})'
    
    def dodaj_kategorijo(self, kategorija):
        ponudba = self.ponudba
        ponudba.append(kategorija)
        self.ponudba = ponudba

#dostopamo do prvotne strani
r = requests.get('https://www.ehrana.si/')
soup = BeautifulSoup(r.content, 'lxml')

#če želimo lep izpis naslova
match = soup.title.text
print(match)
#izpiše: ehrana.si - Dostava hrane na dom


#najprej bomo ustvarili slovar, ki bo kot ključe vseboval vsa mesta po Sloveniji
#pod vrednosti ključa pa bo število restavracij v tem mestu
#pri tem odbijemo zadnji element 'Vsa mesta'

vsa_mesta = dict()
for mesto in soup.find('ul', class_='mesta-list').find_all('li'):
    ime_mesta = mesto.text #razberemo ime mesta
    if ime_mesta == 'Vsa mesta': #če so vsa združena preskočimo
        continue
    vsa_mesta[ime_mesta] = 0 #naredimo element slovarja
    url_mesta = 'https://www.ehrana.si/' + mesto.a['href'] #zapišemo link do restavracij v tem mestu
    
    #zdaj bomo za vsako mesto odprli novo spletno stran
    r2 = requests.get(url_mesta)
    soup2 = BeautifulSoup(r2.content, 'lxml')
    
    #za vsako restavracijo v tem mestu bomo izpisali njene podatke

    for restavracija in soup2.find_all('div', class_ = 'seznam-rest-data'):
        #dodamo jo k številu restavracij v tem mestu
        vsa_mesta[ime_mesta] += 1
        #razberemo ime restavracije
        ime_restavracije = restavracija.find('div', class_ = 'seznam-rest-levo-top').h3.text
        #razberemo oceno restavracije
        ocena_restavracije = float(restavracija.find('div', class_ = 'rating text-right').find('input')['value'])
        #razberemo ali omogoča študentski bon
        stud_bon = restavracija.find('div', class_ = 'seznam-rest-levo-bottom')        
        if 'Štud. doplačilo:' in stud_bon.text: #omogoča bon
            #razberemo ceno doplačila
            cena = float(stud_bon.find('span', class_ = 'text-rumena text-black').text[:-1])
            #naredimo objekt restavracije
            vse_restavracije[ime_restavracije] = Restavracija(ime_restavracije, ime_mesta, ocena_restavracije, 'Da', cena, [])
        else: #ne omogoča bon
            #naredimo objekt restavracije
            vse_restavracije[ime_restavracije] = Restavracija(ime_restavracije, ime_mesta, ocena_restavracije, 'Ne', 0, [])


#podobno naredimo za kategorije hrane
#pri tem bo ključ slovarja ime kategorije
#vrednost pa nov slovar z imeni mest
#dodamo še en slovar, kamor bomo dodali število restavracij s to ponudbo po mestih
kategorije = dict()
vse_kategorije = dict()
kategorije_po_mestih = {key : dict() for key in list(vsa_mesta.keys())}

for kategorija in soup.find('div', class_= 'col-sm-12 col-md-12 kuhinje-wrapper').find_all('a'):
    ime_kategorije = kategorija.text
    if ime_kategorije == 'Vse kuhinje':
        continue
    kategorije[ime_kategorije] = 0
    
    #dodamo kategorijo k vsakemu mestu
    for mesto in kategorije_po_mestih:
        kategorije_po_mestih[mesto][ime_kategorije]=0
    
    vse_kategorije[ime_kategorije] = {key : 0 for key in list(vsa_mesta.keys())}
        
    url_kategorije = 'https://www.ehrana.si/' + kategorija['href']
    r3 = requests.get(url_kategorije)
    soup3 = BeautifulSoup(r3.content, 'lxml')
    
    for restavracija in soup3.find_all('div', class_ = 'seznam-rest-levo-top'):
        ime_restavracije = restavracija.h3.text
        if ime_restavracije not in vse_restavracije:
            continue
        
        #dodamo kategorijo k restavraciji
        vse_restavracije[ime_restavracije].dodaj_kategorijo(ime_kategorije)
        kategorije[ime_kategorije] += 1
        
        #dodamo +1 h kategoriji v ustreznem mestu
        mesto = vse_restavracije[ime_restavracije].mesto
        kategorije_po_mestih[mesto][ime_kategorije] += 1
        vse_kategorije[ime_kategorije][mesto] += 1
   

mesta = list(vsa_mesta.keys())
kategorije = list(vse_kategorije.keys())
podatki = [np.array(list(vse_kategorije[mesto].values())) for mesto in vse_kategorije]

j=0
plt.bar(mesta, podatki[0], label=kategorije[j])
for i in range(1,len(podatki)):
    plt.bar(mesta, podatki[i], bottom = sum(podatki[:i]), label = kategorije[j+1])
    j+=1
plt.xlabel("Mesta")
plt.ylabel("Število restavracij")
plt.title("Ponudba različne hrane po Sloveniji")
plt.legend()
plt.show()



