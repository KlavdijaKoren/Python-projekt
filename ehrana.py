from bs4 import BeautifulSoup
import requests
import matplotlib.pyplot as plt
import numpy as np
import cartopy.crs as crs
import cartopy.feature as cfeature

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
            return f'Restavracija: {self.ime} v mestu {self.mesto} z oceno {self.ocena} in ponudbo: {", ".join(self.ponudba)}.'
        return f'Restavracija: {self.ime} v mestu {self.mesto} omogoča bone z doplačilom {self.cena_st_bon} in oceno {self.ocena} ter ponudbo: {", ".join(self.ponudba)}.'
    
    def __repr__(self):
        if self.st_bon == 'Ne':
            return f'Restavracija({self.ime}, {self.mesto}, {self.ocena}, {self.ponudba})'
        return f'Restavracija({self.ime}, {self.mesto}, {self.cena_st_bon}, {self.ocena}, {self.ponudba})'
    
    def dodaj_kategorijo(self, kategorija):
        ponudba = self.ponudba
        ponudba.append(kategorija)
        self.ponudba = ponudba

#####################################################################################

#za bazo podatkov bomo ustvarili slovar, ki bo kot ključe shranil imena restavracij
#kot vrednost pa objekte z njenimi podatki
vse_restavracije = dict()

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
        #razberemo število glasov - ljudi ki so podali oceno restavraciji
        stevilo_glasov = int(restavracija.find('span', class_='rating-glasov rest-podatki-siva').text[1:-1])
        #razberemo oceno restavracije
        if stevilo_glasov < 50: #če je oceno podalo manj kot 50 ljudi se ocena ne upošteva
            ocena_restavracije = None
        else:
            #razberemo oceno restavracije
            ocena_restavracije = float(restavracija.find('div', class_ = 'rating text-right').find('input')['value'])
        #razberemo ali omogoča doplačilo s študentskimi boni
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

####################################################################################
#ANALIZA IN GRAFI
####################################################################################

#graf1 - število restvracij po mestih in koliko izmed njih omogoča študentske bone

#definirati moramo nov slovar, ki bo šel po vseh restavracijah in pod ključe z imeni mest shranjeval število
#restavracij, ki omogočajo študentske bone
mesta = list(vsa_mesta.keys())
studentski_boni = dict.fromkeys(mesta, 0)
for restavracija in vse_restavracije.values():
    if restavracija.st_bon == 'Ne':
        continue
    studentski_boni[restavracija.mesto] += 1 #dodamo restavracijo

y1 = list(vsa_mesta.values())
y2 = list(studentski_boni.values())

x = np.arange(len(mesta))
fig, ax = plt.subplots()
rects1 = ax.bar(x-0.2, y1, 0.4, edgecolor = 'black', label = 'Vse restavracije')
rects2 = ax.bar(x+0.2, y2, 0.4, edgecolor = 'black', label = 'Študentski boni')

ax.set_ylabel('Število restavracij')
ax.set_title('Število vseh restavracij po posameznih mestih in število restavracij, ki sprejemajo študentske bone')
ax.set_xticks(x)
ax.set_xticklabels(mesta)
ax.legend()

#naslednja dva label-a sta nekje delala, nekje pa ne, zato sem ju zakomentirala
#ax.bar_label(rects1, padding=3)
#ax.bar_label(rects2, padding=3)

fig.tight_layout()
plt.show()

#################################################################################
#graf2 - prikaže števio vseh restavracij, ki ponujajo določeno ponudbo hrane

kategorije_ = list(kategorije.keys())
podatki = [np.array(list(kategorije_po_mestih[kategorija].values())) for kategorija in kategorije_po_mestih]
stolpci = []

j=0
plt.barh(kategorije_, podatki[0], edgecolor = 'black', label = mesta[j])
for i in range(1, len(podatki)):
    j+=1
    stolpec = plt.barh(kategorije_, podatki[i], left = sum(podatki[:i]), edgecolor = 'black', label = mesta[j])
    stolpci.append(stolpec)
plt.legend()
plt.xlabel("Število restavracij")
plt.ylabel("Vrsta hrane")
plt.title("Število restavracij po posameznih krajih, ki ponujajo določeno kategorijo hrane")

for kategorija in kategorije:
    stevilo = kategorije[kategorija]
    plt.text(stevilo + 1, kategorija, str(stevilo), va = 'center',fontsize=10)

plt.show()

##################################################################################
#graf 3 - analiza ocen restavracij

#analiza ocen restavracije
ocene = dict()
for restavracija in vse_restavracije:
    ocena = vse_restavracije[restavracija].ocena
    if ocena == None:
        continue
    ocene[restavracija] = ocena
x_os = list(ocene.keys())
y_os = list(ocene.values())

plt.plot(x_os, y_os, 'o-', color = 'darkblue', label = 'Ocene')

#nariši minimum
ymin = min(y_os)
xpos = y_os.index(ymin)
xmin = x_os[xpos]

plt.annotate("{}: {}".format(xmin, ymin), xy=(xmin, ymin), xytext=(xpos+10, ymin),
            arrowprops=dict(facecolor='green', shrink=0.1),)

#nariši maksimum
ymax = max(y_os)
xpos2 = y_os.index(ymax)
xmax = x_os[xpos2]

plt.annotate("{}: {}".format(xmax, ymax), xy=(xmax, ymax), xytext=(xpos2+10, ymax),
            arrowprops=dict(facecolor='red', shrink=0.1),)

#nariši povprečje
povprečje = np.mean(y_os)
y_povprečje = [povprečje]*len(x_os) #nov vektor
povprečnica = plt.plot(x_os, y_povprečje, label='Povprečje', linestyle='--', color = 'orange')
plt.annotate("{}".format(round(povprečje,4)), xy=(len(x_os)-2, povprečje), xytext=(len(x_os)-2, 3),
            arrowprops=dict(facecolor='orange', shrink=0.02),)

plt.title('Ocene restavracij')
plt.xlabel('Restavracije')
plt.ylabel('Ocene')
plt.xticks([]) #x os nima oznak
plt.legend()
plt.show()

################################################################################
#bubble map

#najprej ustvarimo zemljevid Slovenije
fig = plt.figure(figsize=(6,6))
ax = fig.add_subplot(1,1,1, projection=crs.Mercator())

ax.add_feature(cfeature.COASTLINE, alpha=0.5)
ax.add_feature(cfeature.LAND, color="lightgrey", alpha=0.5)
ax.add_feature(cfeature.LAKES, color="lime")
ax.add_feature(cfeature.BORDERS, linestyle="-", alpha=0.5)
ax.add_feature(cfeature.OCEAN, color="skyblue", alpha=0.4)
ax.set_title("Število restavracij po posameznih krajih")

#slovarju vsa_mesta dodamo koordinate mest
vsa_mesta['Ljubljana'] = (14.504700, 46.053220, 275)
vsa_mesta['Maribor'] = (15.644630, 46.566891, 82)
vsa_mesta['Kranj'] = (14.354324, 46.249674, 26)
vsa_mesta['Celje'] = (15.262413, 46.232578, 24)
vsa_mesta['Koper'] = (13.730078, 45.548438, 24)

transform = crs.PlateCarree()._as_mpl_transform(ax)

mesta_size = []
koordinate_mest = []
for i in vsa_mesta.keys():
    mesta_size.append(vsa_mesta[i][2])
    koordinate_mest.append((vsa_mesta[i][0],vsa_mesta[i][1]))
    ax.annotate(i + ' ({})'.format(vsa_mesta[i][2]), xy=(vsa_mesta[i][0],vsa_mesta[i][1]), xycoords=transform, ha='center', va='top')
    
lat1, lon1, lat2, lon2 = 13, 17, 45.1, 47
ax.set_extent([lat1, lon1, lat2, lon2], crs=crs.PlateCarree())

mesta_barve = ['red', 'orange', 'yellow', 'green', 'blue']
for i in range(5):
    plt.scatter(x=koordinate_mest[i][0], y=koordinate_mest[i][1],c=mesta_barve[i],s=mesta_size[i]*2, alpha=0.5, transform=crs.PlateCarree())

plt.show()
