#!/usr/bin/env python
# -*- coding: utf-8 -*-

from selenium.webdriver.chrome.options import Options 
from selenium import webdriver
from bs4 import BeautifulSoup
import time
import re


webdriver.ChromeOptions()

chrome_options = Options()
chrome_options.add_argument("--headless") #La primera vez debe estar disabled para ver si el scroll efectivamente es lento.
chrome_options.add_argument("--incognito")
driver = webdriver.Chrome(r"C:\Users\tadeo\OneDrive\Escritorio\Curso Data Analyst\Python 0\chromedriver.exe", 
                                        options=chrome_options) #PATH de chromedriver

def get_urls(main_web):
    driver.get(main_web)
    time.sleep(20)

    iter=1
    while True:
            scrollHeight = driver.execute_script("return document.documentElement.scrollHeight") #Obtenemos el size del documento
            Height=250*iter
            driver.execute_script("window.scrollTo(0, " + str(Height) + ");")
            if Height > scrollHeight:
                print('End of page')
                break
            time.sleep(1)
            iter+=1
        
        
    body = driver.execute_script("return document.body")
    html = body.get_attribute('innerHTML')
        
    soup = BeautifulSoup(html, "html.parser")
    global list_webs
    list_webs = []
    
    for link in soup.find_all('a', {"class": "placard__3GNdg"}):
        list_webs.append('https://www.play.movistar.com.ar/' + link.get('href'))
    
    get_info(list_webs)
    

def get_info(urls):
    info = []
    method = '.get_text()'
    for u in urls:
        try:
            driver.get(u)
            body = driver.execute_script("return document.body")
            html = body.get_attribute('innerHTML')
            
            soup = BeautifulSoup(html, "html.parser")
            try:
                info.append([soup.find('h1', {"class": "go-details-title ng-binding"}).get_text() if soup.find('h1', {"class": "go-details-title ng-binding"}) else 'Sin info',
                soup.find('span', {"class": "go-details--spec ng-binding ng-scope"}).get_text() if soup.find('span', {"class": "go-details--spec ng-binding ng-scope"}) else 'Sin info',
                soup.find('a', {"class": "go-details--spec-value go-details--spec__genre ng-binding ng-scope"}).get_text() if soup.find('a', {"class": "go-details--spec-value go-details--spec__genre ng-binding ng-scope"}) else 'Sin info',
                soup.find('span', {"class": "go-details--spec ng-scope"}).get_text() if soup.find('span', {"class": "go-details--spec ng-scope"}) else 'Sin info',
                soup.find('a', {"class": "go-details--spec-value go-details--spec__cast ng-binding ng-scope"}).get_text() if soup.find('a', {"class": "go-details--spec-value go-details--spec__cast ng-binding ng-scope"}) else 'Sin info',
                soup.find('div', {"class": "go-details-description ps-container ps-theme-default ps-active-y"}).get_text() if soup.find('div', {"class": "go-details-description ps-container ps-theme-default ps-active-y"}) else 'Sin info'])
            except:
                pass
        except:
            print(f'Error al conectar a {u}')
            pass
            
    driver.close()
    print(info)
        
def main():
    
    '''Programa principal con menu interactivo, las dos url son la api principal de las peliculas y series. 
    Pasandole por parametro el maximo numero de series y peliculas disponibles en la plataforma (esto se cambia manualmente ya 
    que puede verse facilmente en movistar play)'''
    
    while True:
        global choice
        print('Iniciando programa... \n \n')
        
        choice = str(input(' \n Seleccione una opción: \n \ 1-Descargar datos de peliculas. \n \ 2-Descargar datos de series. \n \ 3-Exit \n\n'))
        if choice == '1':
            connect(url_movies)
        
        elif choice == '2':
            get_urls('https://www.play.movistar.com.ar/catalog/series-619/todas-3440')
            
        elif choice == '3':
            break
        else:
            print('Por favor, selecciona una opcion correcta (1, 2 o 3)')
    

if __name__ == '__main__':
    main()
