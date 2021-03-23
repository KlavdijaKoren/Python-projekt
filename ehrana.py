from bs4 import BeautifulSoup
import requests

vse_restavracije = dict()
r = requests.get('https://www.ehrana.si/')
soup = BeautifulSoup(r.content, 'lxml')

#če želimo lep izpis naslova
match = soup.title.text
print(match)
#izpiše: ehrana.si - Dostava hrane na dom

#najprej bomo v tabelo shranili imena vseh mest po Sloveniji, ki so na voljo
#pri tem odbijemo zadnji element 'Vsa mesta'
vsa_mesta = [mesto.text for mesto in soup.find('ul', class_='mesta-list').find_all('li')][:-1]
#vsa_mesta = ['Ljubljana', 'Maribor', 'Kranj', 'Celje', 'Koper']
kategorije = [kategorija.text for kategorija in soup.find('div', class_= 'col-sm-12 col-md-12 kuhinje-wrapper').find_all('a')]

#zdaj bomo za vsako mesto odprli novo spletno stran
for mesto in vsa_mesta:
    nov_url = 'https://www.ehrana.si/' + mesto.lower()
    r2 = requests.get(nov_url)
    soup2 = BeautifulSoup(r2.content, 'lxml')
    
    #za vsako restavracijo v tem mestu bomo izpisali njene podatke

    for restavracija in soup2.find_all('div', class_ = 'seznam-rest-data'):
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
            vse_restavracije[ime_restavracije] = [mesto, 'Da', cena, ocena_restavracije, []]
        else: #ne omogoča bon
            #naredimo objekt restavracije
            vse_restavracije[ime_restavracije] = [mesto, 'Ne', 0, ocena_restavracije, []]

vse_kategorije = []
for kategorija in soup.find('div', class_= 'col-sm-12 col-md-12 kuhinje-wrapper').find_all('a'):
    ime_kategorije = kategorija.text
    if ime_kategorije == 'Vse kuhinje':
        continue
    vse_kategorije.append(ime_kategorije)
    
    url_kategorije = 'https://www.ehrana.si/' + kategorija['href']
    r3 = requests.get(url_kategorije)
    soup3 = BeautifulSoup(r3.content, 'lxml')
    for restavracija in soup3.find_all('div', class_ = 'seznam-rest-levo-top'):
        ime_restavracije = restavracija.h3.text
        if ime_restavracije not in vse_restavracije:
            continue
        ponudba_restavracije = vse_restavracije[ime_restavracije][4]
        ponudba_restavracije.append(ime_kategorije)
        vse_restavracije[ime_restavracije][4] = ponudba_restavracije

#izpiše vse restavracije    
#for restavracija in vse_restavracije:
#   print('{} -> {}'.format(restavracija, vse_restavracije[restavracija]))



imena_restavracij = vse_restavracije.keys()
print(imena_restavracij)



