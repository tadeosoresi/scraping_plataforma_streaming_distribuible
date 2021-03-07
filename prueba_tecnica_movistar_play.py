#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
import re
from bs4 import BeautifulSoup
import pandas as pd

'''PRUEBA TECNICA MOVISTAR PLAY'''

def connect(url):
    
    '''Esta función hace la conexion a las apis principales y arroja los errores en caso de haberlos. 
    Si request.status_code == 200 pasa a la funcion get_info()'''
    
    request = requests.get(url)
    
    if request.status_code == 200:
        get_info(request)

    elif request.status_code == 301:
        print(f'Error {request.status_code}, el servidor esta tratando de redirigirte hacia otra URL. Quizas haya cambiado de dominio.')
        
    elif request.status_code == 400:
        print(f'Error {request.status_code}, request erroneo, por favor verificar sintaxis y url escrita.')
        
    elif request.status_code == 401:
        print(f'Error {request.status_code}, autenticación incorrecta, verifica credenciales o token.')
        
    elif request.status_code == 403:
        print(f'Error {request.status_code}, no tienes permiso para ver el/los recurso/s.')
        
    elif request.status_code == 404:
        print(f'Error {request.status_code}, recurso no encontrado.')

    elif request.status_code == 503:
        print(f'Error {request.status_code}, el servidor no pudo procesar la petición.')

    else:
        print(f'Error {request.status_code}.')

def get_info(url):
    
    '''Función que extrae el id, titulo y 
    distribuidora. Luego crea un dataframe global con estos datos, copia la columna ID y esta la utiliza como parametro
    la función rest_of_info (movies o series) para hacer consultas a las distintas URLs que contienen mas datos'''
    
    print('Descargando información primaria...')
    
    url = url.json()
    content = url['Content']['List']
    
    lista = []
    for n, t in enumerate(content):
        try:
            lista.append([n, t['Pid'], t['Title'], t['Distributor']])
        except KeyError:
            pass
            
    global dataframe
    dataframe = pd.DataFrame(lista, columns=['Numero', 'ID', 'Titulo', 'Distribuidor'])
    identifier = dataframe['ID']
    rest_of_info(identifier)

def rest_of_info(ids):
    
    '''Función que toma como parametro los ids y extrae información sobre el productor/a, año, sinopsis, capitulos, actores,
    duración y genero de las peliculas'''
    
    print('Descargando información secundaria, esto puede tardar unos minutos...')
    lista = []
    for i in ids:
        try:
            url = requests.get(f'https://contentapi-ar.cdn.telefonica.com/29/default/es-AR/content/{i}?ca_deviceTypes=null%7C401&fields=producerName,pid,title,year,description,distributor,shortDescription,duration,year,ageRatingpid,childrenCount,images.videoFrame,images.landscapeCover,images.banner,images.cover,images.portraitArt,commercializationType&relatedContents=true&includeAttributes=ca_requiresPin,ca_descriptors&includeRelations=Genre,Actor,Director,ProductDependencies,Provider&contentPid={i}')
            url = url.json()
            content = url['Content']
            try:
                lista.append([content[0]['Pid'], 
                                content[0]['ProducerName'], 
                                content[0]['Year'], 
                                content[0]['Description'], 
                                int(content[0]['Duration']/60),
                                content[0]['ChildrenCount'],
                                content[1]['Title'], 
                                [content[4]['Title'], content[5]['Title'], content[6]['Title']]]) 
                                #Estos datos los extraemos como lista, ya que el JSON contiene data de cada actor en cada indice
            except KeyError:
                try:
                    lista.append([content[0]['Pid'], 
                                    content[0]['ProducerName'], 
                                    content[0]['Year'], 
                                    content[0]['Description'], 
                                    int(content[0]['Duration']/60),
                                    'Sin capitulos',
                                    content[1]['Title'], 
                                    [content[4]['Title'], content[5]['Title']]])
                except KeyError:
                    lista.append([content[0]['Pid'], 
                                    content[0]['ProducerName'], 
                                    content[0]['Year'], 
                                    content[0]['Description'], 
                                    int(content[0]['Duration']/60),
                                    'Sin capitulos',
                                    content[1]['Title'], 
                                    ['Sin info', 'Cast']])
        except:
            pass
     
    dataframe_rest_info = pd.DataFrame(lista, columns=['ID', 'Productor/a', 
                                                        'Año', 'Descripción', 
                                                        'Duración(pelicula/capitulo)',
                                                        'Capitulos', 
                                                        'Genero', 
                                                        'Cast'])
                                                        
    dataframe_rest_info['Cast'] = [' '.join(map(str, l)) for l in dataframe_rest_info['Cast']] #Convertimos columna compuesta por lista de actores a strings
    
    global final_dataframe
    final_dataframe = pd.merge(dataframe, dataframe_rest_info, on='ID', how='outer')
    if choice == '1':
        save_to(final_dataframe)
    elif choice == '2':
        identifier = final_dataframe['ID']
        get_seasons_episodes(identifier)
    
def get_seasons_episodes(ids):
     
    '''La cantidad de capitulos esta disponible en otra api, 
        por lo tanto vamos a loopear para visitar cada una y extraer la cantidad de capitulos'''
        
    print('Descargando ultimos datos...')
    lista = []
    for i in ids:
        try:
            url = requests.get(f'https://contentapi-ar.cdn.telefonica.com/29/default/es-AR/content/{i}/children?ca_deviceTypes=null%7C401&fields=pid,title,seasonNumber,childrenCount,commercializationType,availableUntil&includeRelations=Episode,Media&includeAttributes=ca_devicetypes_qualities&contentPid={i}&cachetime=202103041800')
            url = url.json()
            content = url['Content']['List']
            leng_json = len(content) #Cada indice es una temporada con sus datos
            try:
                lista.append([i, sum([content[i]['ChildrenCount'] for i in range(leng_json)])])
            except KeyError:
                lista.append([i, 'No info'])
            except IndexError:
                lista.append([i, 'No info'])
        except:
            pass
            
    dataframe_seasons_episodes = pd.DataFrame(lista, columns=['ID', 'Capitulos_total'])
    final_dataframe_series = pd.merge(final_dataframe, dataframe_seasons_episodes, on='ID', how='outer')
    save_to(final_dataframe_series)

def save_to(data):

    '''Funcion que guarda los dataframes combinados en JSON o EXCEL'''
    
    choice_save = str(input('Guardar datos como (seleccione numero): \n \ 1-JSON. \n \ 2-Excel. \n \ 3-Ambos. \n \ 4-Salir y no guardar. \n'))
    if choice_save == '1':
        name_file = str(input('Ingrese nombre del archivo con el cual quiere guardar: ')).split()
        try:
            data.to_json(f'{name_file}.json', orient='index')
            print('Datos guardados correctamente.')
        except:
            print('Ocurrio un error al guardar.')
            pass
    elif choice_save == '2':
        name_file = str(input('Ingrese nombre del archivo con el cual quiere guardar: ')).split()
        try:
            data.to_excel(f'{name_file}.xlsx', sheet_name='datos')
            print('Datos guardados correctamente.')
        except:
            print('Ocurrio un error al guardar.')
            pass
    elif choice_save == '3':
        name_file = str(input('Ingrese nombre del archivo con el cual quiere guardar: ')).split()
        try:
            data.to_json(f'{name_file}.json', orient='index')
            data.to_excel(f'{name_file}.xlsx', sheet_name='datos')
            print('Datos guardados correctamente.')
        except:
            print('Ocurrio un error al guardar.')
            pass
    elif choice_save == '4':
        pass
    else:
        print('Seleccione una opción valida (1, 2, 3, 4)')
        
'''
En caso de que movistar play comience a agregar series y peliculas seguid deberemos automatizar
la consulta a la cantidad disponible para luego pasarla en la url (va a ser el max_number of series o movies)

def get_number_of(web_url):
    from selenium.webdriver.chrome.options import Options 
    from selenium import webdriver
    
    webdriver.ChromeOptions()

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(r"C:\Users\tadeo\OneDrive\Escritorio\Curso Data Analyst\Python 0\chromedriver.exe", 
                                    chrome_options=chrome_options) #PATH de chromedriver   
    response = driver.get(web_url)
    
    body = driver.execute_script("return document.body")
    html = body.get_attribute('innerHTML')
    
    soup = BeautifulSoup(html, "html.parser")
    resultado = soup.find("span", { "class" : "textBrackets__3x96A" }).get_text()
    
    return resultado
'''

def main():
    
    '''Programa principal con menu interactivo, las dos url son la api principal de las peliculas y series. 
    Pasandole por parametro el maximo numero de series y peliculas disponibles en la plataforma (esto se cambia manualmente ya 
    que puede verse facilmente en movistar play)'''
    
    max_number_of_movies = 7000
    max_number_of_series = 550
    
    url_movies = f'https://nrs-a.cdn.telefonica.com/rec_search/29/default/es-AR/content/CHA3439/children?ca_deviceTypes=null%7C401&includeAttributes=ca_requiresPin,ca_blackout_target,ca_blackout_areas&includeRelations=ProductDependencies,Genre,Provider&fields=pid,title,callLetter,channelName,duration,start,end,epgChannelId,channelId,programId,commercializationType,distributor,releaseDate,forbiddenTechnology,images.videoFrame,images.cover,images.landscapeCover,images.banner,images.portraitArt&contentPid=CHA3439&ca_requiresPin=false&orderBy=CONTENT_ORDER&offset=16&limit={max_number_of_movies}&contentTypes=MOV,SER&ca_commercializationType=CATCHUP%7CExternalCATCHUP%7CFreeVOD%7CSVOD%7CTransparentCatchup%7CTVOD%7CUnknown&px_device_type=401&px_is_anonym=true&px_uxr=29.PC.TA_PAGE&px_channel=CHA3439&px_filter=1'
    url_series = f'https://nrs-a.cdn.telefonica.com/rec_search/29/default/es-AR/content/CHA3440/children?ca_deviceTypes=null%7C401&includeAttributes=ca_requiresPin,ca_blackout_target,ca_blackout_areas&includeRelations=ProductDependencies,Genre,Provider&fields=pid,title,callLetter,channelName,duration,start,end,epgChannelId,channelId,programId,commercializationType,distributor,releaseDate,forbiddenTechnology,images.videoFrame,images.cover,images.landscapeCover,images.banner,images.portraitArt&contentPid=CHA3440&ca_requiresPin=false&orderBy=CONTENT_ORDER&offset=16&limit={max_number_of_series}&contentTypes=MOV,SER&ca_commercializationType=CATCHUP%7CExternalCATCHUP%7CFreeVOD%7CSVOD%7CTransparentCatchup%7CTVOD%7CUnknown&px_device_type=401&px_is_anonym=true&px_uxr=29.PC.TA_PAGE&px_channel=CHA3440&px_filter=1'
    
    while True:
        global choice
        choice = str(input(' \n \n Seleccione una opción: \n \ 1-Descargar datos de peliculas. \n \ 2-Descargar datos de series. \n \ 3-Exit \n\n'))
        if choice == '1':
            connect(url_movies)
        
        elif choice == '2':
            connect(url_series)
            
        elif choice == '3':
            break
        else:
            print('Por favor, selecciona una opcion correcta (1, 2 o 3)')
    

if __name__ == '__main__':
    main()
