import requests
from bs4 import BeautifulSoup
from datetime import datetime
from ftplib import FTP


def upload_to_ftp(filename):
    # Чтение данных для подключения к FTP из файла
    with open("ftp_credentials.txt", "r") as file:
        host = file.readline().strip()
        username = file.readline().strip()
        password = file.readline().strip()

    # Подключение к FTP
    with FTP(host) as ftp:
        ftp.login(username, password)

        # Переход к нужной директории
        ftp.cwd("/new.ofme.ru/public_html/YML_feed/")

        # Загрузка файла
        with open(filename, "rb") as file:
            ftp.storbinary(f"STOR {filename}", file)

    print(f"Файл {filename} успешно загружен на FTP!")

def parse_page(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Извлечение данных
    product_name = soup.find('h1', itemprop='name').text.strip()
    main_image_url = "https://www.ofme.ru" + soup.find('img', itemprop='image')['src']
    width = soup.find('div', class_='block8_r2').find('p', string='Ширина:').find_next_sibling('p').text.strip()
    depth = soup.find('div', class_='block8_r2').find('p', string='Глубина:').find_next_sibling('p').text.strip()
    height = soup.find('div', class_='block8_r2').find('p', string='Высота:').find_next_sibling('p').text.strip()
    brand = soup.find('p', itemprop='brand').text.strip()
    price = soup.find('p', itemprop='price')['content'].strip()
    description_section = soup.find('div', itemprop='description')
    description = description_section.text.strip()

    # Извлечение всех изображений из раздела description
    description_images = description_section.find_all('img')
    image_urls = [img['src'] for img in description_images if 'src' in img.attrs]
    image_urls = ["https://www.ofme.ru" + img_url for img_url in image_urls]

    # Добавление основного изображения в начало списка
    image_urls.insert(0, main_image_url)

    # Создание YML
    yml = f"""
    <offer>
        <name>{product_name}</name>
        <url>{url}</url>
        <price>{price}</price>
        <currencyId>RUR</currencyId>
        <categoryId>1</categoryId>
    """
    for img_url in image_urls:
        yml += f"<picture>{img_url}</picture>\n"

    yml += f"""
        <width>{width}</width>
        <depth>{depth}</depth>
        <height>{height}</height>
        <vendor>{brand}</vendor>
        <description>{description}</description>
    </offer>
    """
    return yml


# Чтение ссылок из файла
with open("links.txt", "r") as file:
    urls = [line.strip() for line in file.readlines()]

# Парсинг каждой ссылки
offers = []
for url in urls:
    offers.append(parse_page(url))

# Сохранение всех товаров в одном YML файле
current_date = datetime.now().strftime("%Y-%m-%d")
filename = f"Ofme - {current_date}.yml"

header = """<?xml version="1.0" encoding="UTF-8"?>
<yml_catalog date="{current_date}">
<shop>
<name>Ofme</name>
<company>Ofme</company>
<url>https://www.ofme.ru/</url>
<currencies>
<currency id="RUR" rate="1"/>
</currencies>
<categories>
<category id="1">Furniture</category>
</categories>
<offers>
"""

footer = """
</offers>
</shop>
</yml_catalog>
"""

with open(filename, "w", encoding="utf-8") as file:
    file.write(header)
    for offer in offers:
        file.write(offer)
    file.write(footer)

print(f"YML файл {filename} сохранен!")
# Загрузка файла на FTP сервер
upload_to_ftp(filename)