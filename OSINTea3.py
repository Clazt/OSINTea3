import requests
from bs4 import BeautifulSoup
import argparse
import shodan
import time

apiShodan=shodan.Shodan('') #add your shodan key here
url='https://dnsdumpster.com/'

#armo un arreglo para la tabla de input, con diccionarios por cada fila de la tabla
def table_info (table):
    trs = table.find_all('tr')
    infoTable = []
    for tr in trs:
        tds = tr.find_all('td')
        dominio = list(tds[0].children)[0]
        ip = list(tds[1].children)[0]
        descripcion = list(tds[2].children)[0]
        res = {'dominio' : dominio, 'ip' : ip, 'descripcion' : descripcion}
        infoTable.append(res)     
    return infoTable   
       

#utiliza el dominio o ip ingresada como input en el comando para realizar la busqueda
def parse_arguments (): 
    parser = argparse.ArgumentParser()
    parser.add_argument("dom")
    args = parser.parse_args()
    return args


#consigue el CSRFtoken ya que es necesario para realizar el request
def get_csrftoken(): 
    req = requests.get(url)
    soup = BeautifulSoup(req.content, 'html.parser')
    csrf_middleware = soup.findAll('input', attrs={'name': 'csrfmiddlewaretoken'})[0]['value']
    return csrf_middleware


#utilizando el csrftoken y el referer (es argumento necesario para el request) armo la peticion a dnsdumpster de el dominio target
#y la respuesta es un objeto tipo soup con toda la informacion de las tablas
def get_target_info(csrf_middleware, target): 
    header = {'Referer': url}
    data = {'csrfmiddlewaretoken' : csrf_middleware, 'targetip' : target } 
    response = requests.post(url, data=data, headers = header, cookies={'csrftoken' : csrf_middleware})
    soup = BeautifulSoup(response.content, 'html.parser')
    return soup

#obtiene el objeto de tipo soup traido desde get_target_info y lo categoriza en un diccionario que 
#contiene listas(una lista por categoria) de diccionarios
def parse_results(tables, target): 
    result={}
    result['image'] = 'https://dnsdumpster.com/static/map/' + target + '.png'
    result['mx'] = table_info (tables[1])
    result['dns'] = table_info (tables[0])
    result['hosts'] = table_info (tables[3])
    return result

#realiza toda la obtención de la información de dns_dumpster 
def target_json_data(target): 
    csrf_middleware = get_csrftoken()
    tables = get_target_info(csrf_middleware, target).findAll('table')
    domainData= parse_results(tables, target)
    return domainData

def main ():
    target = parse_arguments().dom 
    #print (target_json_data(target)) #-- check
    return target_json_data(target)

#main ()


dns_dumpster_output = main()
hosts_shodan= []
for i in range(len(dns_dumpster_output['hosts'])):
    hosts_shodan.append(dns_dumpster_output['hosts'][i]['ip'])
#print (hosts_shodan) #-- check

info_shodan={}
for i in range(0, len(hosts_shodan)):
    #info_shodan[hosts_shodan[i]] = apiShodan.host('170.239.168.72')
    try:
        info_shodan[hosts_shodan[i]] = apiShodan.host(hosts_shodan[i])
        time.sleep(1) #la key free deja hacer requests cada 1 segundo.
    except:
        print ("No hay informacion disponible de Shodan para el host %s." % hosts_shodan[i])
        pass
print (info_shodan)

