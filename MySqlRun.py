import csv
import datetime
import random
import mysql.connector
import requests
import json
from urllib.parse import quote

class MySqlRun:
    def __init__(self,city='Уссурийск', host='localhost', user='YOUR_DB_USER', password='YOUR_DB_PASSWORD', database='vtbsc', scripts=[
        'vtb/ServiceCategory.sql',
        'vtb/Branches.sql',
        'vtb/QueueBank.sql'
    ]):
        """
        Инициализация объекта DatabaseManager.
        :arg
            city (str) : Название города для поиска отделений
            host (str): Хост базы данных MySQL.
            user (str): Имя пользователя для подключения к базе данных.
            password (str): Пароль для подключения к базе данных.
            database (str): Имя базы данных, по умолчанию 'vtbsc'.
            scripts (list): Список файлов со скриптами для выполнения.
        """
        self.city=city
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.scripts = scripts or []
self.YANDEX_MAPS_API_KEY = 'YOUR_YANDEX_API_KEY'
self.YANDEX_MAPS_API_KEY_GEOCODER = 'YOUR_YANDEX_GEOCODER_KEY'

    def run_creater(self):
        self.create_bd_tables()
        self.add_categories()
        self.find_vtb_branches()
        self.add_branches()
        self.generate_queuedata()
    def get_coordinates(self,city_name, api_key):
        '''
        Получаем координаты города используя Яндекс Геокодер API.
        :param
            city_name (str): Название города для которого нужно получить координаты.
            api_key (str): Ключ для доступа к Yandex Maps API.
        :return
            tuple: Кортеж с координатами (широта, долгота).
            Пример: (56.009031, 92.852732)
        '''
        # делаем запрос к Yandex Maps API для получения координат города
        base_url = "https://geocode-maps.yandex.ru/1.x/"
        params = {
            'apikey': api_key,
            'geocode': city_name,
            'format': 'json'
        }
        response = requests.get(base_url, params=params)
        if response.status_code == 200:
            # используем JSON для получения координат из ответа
            data = response.json()
            coordinates = data['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['Point']['pos']
            # преобразуем координаты из строки в числа
            latitude, longitude = map(float, coordinates.split())
            print("Координаты города:", longitude,latitude )
            return latitude, longitude
        else:
            print("Ошибка при получении координат.")
            return None
    def find_vtb_branches(self,city=None):
        '''
        Ищем отделения банка ВТБ в указанном городе и сохраняем результаты в JSON файл.
        :param:
            city (str): Название города для поиска отделений банка ВТБ.
        :return
            list: Список словарей с информацией об отделениях банка ВТБ.
            Пример: [{'name': 'Отделение 1', 'address': 'ул. Примерная, 123', 'latitude': 56.009031, 'longitude': 92.852732}]
        '''
        # заполняем значением переменную в записимости от передачи аргумента.
        if city==None:
            city=self.city
        # делаем запрос к Yandex Maps API для получения координат города
        city_coordinates = self.get_coordinates(city, self.YANDEX_MAPS_API_KEY_GEOCODER)
        if city_coordinates:
            latitude, longitude = city_coordinates
            bank_encoded = quote('ВТБ', safe='')
            # формируем URL для запроса к Yandex Maps API для поиска отделений банка ВТБ
url = f"https://search-maps.yandex.ru/v1/?text={bank_encoded}&ll={longitude},{latitude}&spn=0.1,0.1&lang=ru_RU&apikey={self.YANDEX_MAPS_API_KEY}"
            # делаем запрос к API для получения информации о банковских отделениях
            response = requests.get(url)
            print("**** ", response," ****\n ",url)
            if response.status_code == 200:
                data = response.json()
                branches = []
                # используем полученные данные для формирования списка отделений
                for feature in data['features']:
                    branch_data = feature['properties']
                    address = branch_data.get('description', '')
                    name = branch_data.get('name', '')
                    longitude_b, latitude_b, = feature["geometry"]["coordinates"]
                    # Пытаемся получить рабочие часы, если они доступны
                    try:
                        working_hours = feature["properties"]["CompanyMetaData"]["Hours"]
                    except KeyError:
                        # Если рабочие часы недоступны, вставляем пустую строку
                        working_hours = ''
                    category = feature["properties"]["CompanyMetaData"]["Categories"][0]["name"]
                    branches.append(
                        {'name': name, 'address': address,'category': category, 'latitude': latitude_b, 'longitude': longitude_b,'working_hours':working_hours})
                # сохраняем результаты в JSON файл
                with open('vtb/vtb_branches.json', 'w', encoding='utf-8') as json_file:
                    json.dump(branches, json_file, ensure_ascii=False, indent=4)
                return branches
            else:
                print(f"Ошибка при выполнении запроса: {response.status_code}")
                return None
        else:
            print(f"Не удалось получить координаты для города: {city}")
            return None

    def add_categories(self, csv_file='vtb/category.csv'):
        """
        Добавляет данные из CSV файла в таблицу servicecategories.
        Делаем:
            - Подключаемся к базе данных MySQL.
            - Открываем CSV файл и читаем данные.
            - Читаем данные и добавляем их в таблицу servicecategories.
        """
        try:
            # Подключаемся к базе данных MySQL
            with mysql.connector.connect(
                    host=self.host,
                    user=self.user,
                    password=self.password,
                    database=self.database
            ) as connection:
                print("Успешно подключено к базе данных.")

                cursor = connection.cursor()

                # Открываем CSV файл и читаем данные
                with open(csv_file, 'r', encoding='utf-8') as file:
                    csv_reader = csv.reader(file)
                    next(csv_reader)  # Пропускаем заголовок

                    # Парсим данные и добавляем их в таблицу servicecategories
                    for row in csv_reader:
                        name, time = row
                        cursor.execute("INSERT INTO ServiceCategories (name, service_time_minutes) VALUES (%s, %s)", (name, time))
                        print(f"Данные '{name}', '{time}' успешно добавлены в таблицу servicecategories.")

                # Применяем изменения
                connection.commit()
                print("Изменения успешно применены в базе данных.")
                return True

        except Exception as e:
            print(f"Произошла ошибка: {e}")
            return False
        finally:
            print("Соединение с базой данных закрыто.")

    def create_bd_tables(self):
        """
        Создает базу данных и выполняет SQL скрипты для создания таблиц.
        Делаем:
            - Подключаемся к серверу MySQL.
            - Создаем базу данных, если она не существует.
            - Подключаемся к созданной базе данных.
            - Выполняем SQL скрипты для создания таблиц.
        """
        try:
            # Подключаемся к базе данных MySQL для создания базы данных
            with mysql.connector.connect(
                    host=self.host,
                    user=self.user,
                    password=self.password
            ) as connection:
                print("Успешно подключено к серверу MySQL.")
                cursor = connection.cursor()

                # Удаляем базу данных, если она существует
                cursor.execute(f"DROP DATABASE IF EXISTS {self.database}")
                print(f"База данных '{self.database}' удалена успешно.")
                # Создаем базу данных, если она не существует
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
                print(f"База данных '{self.database}' создана успешно.")

            # Подключаемся к созданной базе данных
            with mysql.connector.connect(
                    host=self.host,
                    user=self.user,
                    password=self.password,
                    database=self.database
            ) as connection:
                print(f"Успешно подключено к базе данных '{self.database}'.")
                cursor = connection.cursor()

                # Выполняем SQL скрипты из файлов
                for script_file in self.scripts:
                    with open(script_file, 'r') as script:
                        script_content = script.read()
                        cursor.execute(script_content)
                        print(f"SQL скрипт из файла {script_file} выполнен успешно.")

                # Применяем изменения
                connection.commit()
                print("Изменения успешно применены в базе данных.")

        except Exception as e:
            print(f"Произошла ошибка: {e}")
        finally:
            print("Соединение с базой данных закрыто.")

    def add_categories(self, csv_file='vtb/category.csv'):
        """
        Добавляет данные из CSV файла в таблицу servicecategories.
        Делаем:
            - Подключаемся к базе данных MySQL.
            - Открываем CSV файл и читаем данные.
            - Читаем данные и добавляем их в таблицу servicecategories.
        """
        try:
            # Подключаемся к базе данных MySQL
            with mysql.connector.connect(
                    host=self.host,
                    user=self.user,
                    password=self.password,
                    database=self.database
            ) as connection:
                print("Успешно подключено к базе данных.")

                cursor = connection.cursor()

                # Открываем CSV файл и читаем данные
                with open(csv_file, 'r', encoding='utf-8') as file:
                    csv_reader = csv.reader(file)
                    next(csv_reader)  # Пропускаем заголовок

                    # Парсим данные и добавляем их в таблицу servicecategories
                    for row in csv_reader:
                        name, time = row
                        cursor.execute("INSERT INTO ServiceCategories (name, service_time_minutes) VALUES (%s, %s)",
                                       (name, time))
                        print(f"Данные '{name}', '{time}' успешно добавлены в таблицу ServiceCategories.")

                # Применяем изменения
                connection.commit()
                print("Изменения успешно применены в базе данных.")
                return True

        except Exception as e:
            print(f"Произошла ошибка: {e}")
            return False
        finally:
            print("Соединение с базой данных закрыто.")
    def add_branches(self, json_file='vtb/vtb_branches.json'):
        """
        Добавляет данные из JSON файла в таблицу branches.
        Делаем:
            - Подключаемся к базе данных MySQL.
            - Открываем JSON файл и читаем данные.
            - Парсим данные и добавляем их в таблицу branches.
        :param
            json_file (str): Путь к JSON файлу.
        :return
            bool: Возвращает True, если данные успешно добавлены, иначе False.
        """
        try:
            # Подключаемся к базе данных MySQL
            with mysql.connector.connect(
                    host=self.host,
                    user=self.user,
                    password=self.password,
                    database=self.database
            ) as connection:
                print("Успешно подключено к базе данных.")

                cursor = connection.cursor()

                # Открываем JSON файл и читаем данные
                with open(json_file, 'r', encoding='utf-8') as file:
                    data = json.load(file)

                    # Парсим данные и добавляем их в таблицу branches
                    for branch in data:
                        name = branch['name']
                        address = branch['address']
                        category = branch['category']
                        city = address.split(',')[
                            -2].strip()  # Получаем город из предпоследней позиции в строке address
                        latitude = branch['latitude']
                        longitude = branch['longitude']
                        working_hours=branch['working_hours']
                        cursor.execute(
                            "INSERT INTO Branches (name, address, city,category, latitude, longitude , work_time) VALUES (%s, %s,%s, %s, %s, %s,%s)",
                            (name, address, city, category, latitude, longitude,json.dumps(working_hours)))
                        print(
                            f"Данные '{name}', '{address}', '{city}', '{latitude}', '{longitude}' успешно добавлены в таблицу branches.")

                # Применяем изменения
                connection.commit()
                print("Изменения успешно применены в базе данных.")
                return True

        except Exception as e:
            print(f"Произошла ошибка: {e}")
            return False
        finally:
            print("Соединение с базой данных закрыто.")
    def generate_queuedata(self):
        """
        Генерирует данные для таблицы queuedata.
        :return
            bool: Возвращает True, если данные успешно добавлены, иначе False.
        """
        try:
            # Подключаемся к базе данных MySQL
            with mysql.connector.connect(
                    host=self.host,
                    user=self.user,
                    password=self.password,
                    database=self.database
            ) as connection:
                print("Успешно подключено к базе данных.")
                cursor = connection.cursor()

                # Получаем все branch_id из таблицы branches, где category = 'банк' (независимо от регистра)
                cursor.execute("SELECT id FROM Branches WHERE LOWER(category) = LOWER('банк')")
                branch_ids = [row[0] for row in cursor.fetchall()]

                # Получаем все category_id из таблицы servicecategories
                cursor.execute("SELECT id FROM ServiceCategories")
                category_ids = [row[0] for row in cursor.fetchall()]

                # Получаем данные о времени обслуживания из таблицы servicecategory для каждой категории
                service_time_dict = {}
                for category_id in category_ids:
                    cursor.execute("SELECT service_time_minutes FROM ServiceCategories WHERE id = %s", (category_id,))
                    service_time_minutes = cursor.fetchone()[0]
                    service_time_dict[category_id] = service_time_minutes

                # Генерируем данные и добавляем их в таблицу queuedata
                for branch_id in branch_ids:
                    for category_id in category_ids:
                        # Получаем случайное начальное время для каждой категории
                        current_time = datetime.datetime.now()
                        random_offset = random.randint(-30, 30)  # случайное количество минут от -30 до 30
                        offset = datetime.timedelta(minutes=random_offset)
                        start_time = current_time + offset
                       # start_time = datetime.datetime.now().replace(microsecond=0, second=0, minute=)

                        # Генерируем время обслуживания на основе данных из таблицы servicecategory
                        service_time_minutes = service_time_dict[category_id]
                        end_time = start_time + datetime.timedelta(minutes=service_time_minutes)

                        for _ in range(random.randint(1, 7)):  # Рандомное количество записей от 1 до 7
                            cursor.execute("INSERT INTO QueueData (branch_id, category_id, start_time, end_time) VALUES (%s, %s, %s, %s)",
                                           (branch_id, category_id, start_time, end_time))
                            print(f"Запись с branch_id={branch_id}, category_id={category_id}, start_time={start_time}, end_time={end_time} добавлена успешно.")

                            # Увеличиваем текущее время для следующей записи
                            start_time = end_time
                            end_time = start_time + datetime.timedelta(minutes=service_time_minutes)

                # Применяем изменения
                connection.commit()
                print("Изменения успешно применены в базе данных.")
                return True

        except Exception as e:
            print(f"Произошла ошибка: {e}")
            return False
        finally:
            print("Соединение с базой данных закрыто.")




