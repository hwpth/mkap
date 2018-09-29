#!/usr/bin/python
#coding: utf-8

import os, sys, io, requests
from lxml import html, etree

# alfa = ''.join([chr(x + ord('а')) for x in range(32)]) + 'ё'

is_debug = False
# is_debug = True

proxy_url = 'http://www.ip-adress.com/proxy_list/'
proxy_list = list()
len_proxy_list = 0

search_str = 'Программист'
search_query = search_str

vacancy_list = list()

db_name = "mkap.xml"

valid_struc = '''
<!ELEMENT root (a)*>
<!ELEMENT a ANY>
<!ATTLIST a name CDATA #REQUIRED
            href CDATA #REQUIRED>
'''

# new_struc = '''
# <root>
# <a name = "test" href = "http://test.org">test element</a>
# </root>
# '''

new_struc = '''
<root>
</root>
'''

def getProxyList():
    global proxy_list
    print('Получение списка прокси-серверов с', proxy_url)
    proxy_set = set()
    response = requests.get(proxy_url)
    if response.status_code == 200:
        page = html.fromstring(response.text)
        elements = page.xpath('//tr/td[1]/.')
        for elem in elements:
            s = elem.xpath('./a/text()')[0] + elem.xpath('./text()')[0]
            if s not in proxy_set:
                proxy_set.add(s)
        if len(proxy_set) > 0:
            proxy_list = list(proxy_set)
            return 200
        else:
            return 0
    return 0

def getVacancyList(proxy):
    global vacancy_list
    parse_url = 'http://www.mkap.ru'
    query_url = '/jobs?category=5&city=1264&schedule=0&experience=0&priceMin=0&priceMax=0'
    print('\nПоиск: "' + search_query + '" на сайте ', parse_url)
    if len(proxy) > 0:
        print('Обращение через прокси-сервер:', proxy, 'к узлу', parse_url, '\n')
    else:
        print('Обращение напрямую к узлу', parse_url, '\n')

    response = requests.get(parse_url + query_url, proxies = proxy)
    if response.status_code == 200:
        if is_debug:
            try:
                f = open(os.path.join(curDir, 'content.html'), 'wb')
                f.write(response.content)
                f.close
            except Exception:
                print('Не удалось сохранить результаты запроса в файл\n')
        page = html.fromstring(response.text)
        elements = page.xpath('//*/div/a/div/h4/strong/text()')
        if (len(elements) == 0):
            print('Возможно изменена структура страницы, не найдено ни одного структурного элемента\n')
            return -1
        elements = page.xpath('//*/div/a/div/h4/strong[contains(translate(text(), "' + search_query.upper() + '", "' + search_query.lower() + '"), "' + search_query.lower() + '")]/../../..')
        for element in elements:
            vacancy_list.append([element.xpath('./div/h4/strong/text()')[0],
                                parse_url + element.xpath('./@href')[0],
                                element.xpath('./div/h4/small/text()')[0].strip(),
                                parse_url])
        return 200
    else:
        return 0

# point of entry
curDir = os.path.dirname(sys.argv[0])
if curDir != '':
    os.chdir(curDir)
curDir = os.getcwd()
print('Установлена рабочая директория:', curDir, '\n')

search_query = input('строка поиска: ')
if search_query == '':
    search_query = search_str

stat = getVacancyList({})

if stat != 200 and stat >= 0:
    stat = getProxyList()
    if stat == 200:
        print('Список прокси-серверов:', proxy_list, '\n')
        len_proxy_list = len(proxy_list)
    else:
        print('Неудача статус:', stat, '\n')

    flag = True
    i = 0
    while flag and (i < len_proxy_list):
        # time.sleep(1)
        proxy = {'http' : proxy_list[i]}
        stat = getVacancyList(proxy)
        if stat == 200:
            flag = False
        else:
            print('Неудача статус:', stat, '\n')
            i += 1

if len(vacancy_list) > 0:
    dtd = etree.DTD(io.StringIO(valid_struc))
    try: # попытка открыть xml файл, или создать его. Создание структуры ElementTree
        tree = etree.parse(os.path.join(curDir, db_name))
        if dtd.validate(tree):
            print('\nВалидация успешна\n')
        else:
            print(dtd.error_log.filter_from_errors()[0], '\n')
    except Exception:
        if is_debug:
            print(sys.exc_info()[0])
        elem = etree.fromstring(new_struc)
        tree = etree.ElementTree(elem)
        try:
            tree.write(os.path.join(curDir, db_name), encoding = "utf-8")
            print('Создан новый файл\n')
        except Exception:
            quit('Ошибка при создании файла')
    root = tree.getroot()
    flag_modif = False
    for s in vacancy_list:
        s0 = s[0].replace('"', '')
        print(s[2] + ": " + s0)
        if not tree.xpath('//a[@href = "' + s[1] + '"]'):
            item = etree.SubElement(root, 'a', href = s[1], name = s0)
            item.text = s[2]
            flag_modif = True
    if flag_modif:
        tree.write(os.path.join(curDir, db_name), encoding = "utf-8")
    else:
        print('\nПо запросу "' + search_query + '" ничего нового')
else:
    print('Ничего не нашли')

# rSr4r