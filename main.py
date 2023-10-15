import os
from datetime import datetime
import mysql
from flask import Flask, render_template, request, jsonify, session, json

from MySqlRun import MySqlRun

# Создаем Flask приложение
app = Flask(__name__)
app.secret_key = 'YOUR_SECRET_KEY'  # Секретный ключ для сессий


# # Определение имени хоста для подключения к базе данных
# if os.environ.get('DOCKERIZED'):
#     db_host = "db"  # Имя сервиса базы данных из docker-compose.yml
# else:
#     db_host = "localhost"  # Имя хоста локальной базы данных

db_config = {
    "host": "localhost",
    'user': 'YOUR_DB_USER',
    'password': 'YOUR_DB_PASSWORD',
    'database': 'vtbsc'
}

# Функция для нахождения времени ожидания в очереди
def find_times():
    # Подключаемся к базе данных
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    table_name = 'QueueData'
    # Выполняем SQL-запрос для нахождения всех записей, отсортированных по времени окончания операции
    cursor.execute(f"SELECT * FROM {table_name} ORDER BY end_time")
    # Получаем результаты запроса в виде списка кортежей
    results = cursor.fetchall()
    # Закрываем соединение с базой данных
    conn.close()
    # Получаем текущее время
    current_time = datetime.now()
    # Создаем словарь с оставшимся временем для каждой записи
    total_remaining_times = {}
    for record_info in results:
        record_id, bank_id, service_id, start_time, end_time = record_info
        # Проверяем, что запись является активной
        if end_time > current_time:
            remaining_time_minutes = (end_time - current_time).total_seconds() / 60
        else:
            remaining_time_minutes = 0
        total_remaining_times[f"{bank_id},{service_id}"] = int(round(remaining_time_minutes))
    # Печатаем результаты
    for key, value in total_remaining_times.items():
        bank_id, service_id = key.split(',')
        print(f"Bank {bank_id}, Service {service_id}: Remaining time - {value:.2f} minutes")
    return total_remaining_times

# Функция для получения категорий услуг и отделений
def get_branches_servicecat():
    # Подключаемся к базе данных MySQL
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    # Извлекаем данные из базы данных
    cursor.execute('SELECT * FROM ServiceCategories')
    # Делаем запрос категорий услуг
    service = cursor.fetchall()
    # Делаем запрос отделений
    cursor.execute('SELECT * FROM Branches')
    branch = cursor.fetchall()
    # Закрываем соединение с базой данных
    cursor.close()
    conn.close()
    # Возвращаем данные категорий услуг и отделений
    return service, branch

# Обработчик маршрута '/'
@app.route('/')
def index():
    # Отображаем главную страницу
    return render_template('index.html')

# Обработчик формы для ввода данных
@app.route('/content_one', methods=['POST'])
def content_one():
    # Получаем данные из формы
    input_data = request.form['user_input']
    if input_data != '' and input_data is not None:
        ms = MySqlRun(input_data)
        # Создаем записи в базе данных
        ms.run_creater()
    print("Полученные данные:", input_data)
    return render_template('content_one.html')

# Обработчик для отображения таблиц
@app.route('/show_table', methods=['GET'])
def show_table():
    # Подключаемся к базе данных MySQL
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    # Извлекаем данные из базы данных
    cursor.execute('SELECT * FROM ServiceCategories')
    table1_data = cursor.fetchall()
    cursor.execute('SELECT * FROM Branches')
    table2_data = cursor.fetchall()
    cursor.execute('SELECT * FROM QueueData')
    table3_data = cursor.fetchall()
    # Закрываем соединение с базой данных
    cursor.close()
    conn.close()
    response_data = {
        'table1_data': table1_data,
        'table2_data': table2_data,
        'table3_data': table3_data
    }
    # Отображаем страницу show_table
    return render_template('show_table.html', data=response_data)

# Обработчик маршрута '/content_two'
@app.route('/content_two')
def content_two():
    # Отображаем страницу content_two
    return render_template('content_two.html')

# Обработчик для загрузки данных
@app.route('/service_load', methods=['POST'])
def service_load():
    # Получаем данные из POST-запроса
    #data = request.form.to_dict()
    #data = request.get_json()
    data1 = request.form
    data = data1.get('selectedValue')
    print("************!!!!!!!!!!!!!!!!!!!!", data)
    if (data!= None) and (data!=''):
        print("???????????", data)
    # Сохраняем данные в сессии
        session['data_find'] = data

    # Получаем данные времени ожидания
    total_time = find_times()
    print('TOTAL TIME',total_time)
    # Получаем данные категорий услуг и отделений
    service, branch = get_branches_servicecat()
    response_data = {
        'total_time': total_time,
        'service': service,
        'branch': branch
    }
    print(data)
    # Отправляем результат обратно в виде JSON
    return jsonify(response_data)

# Обработчик маршрута '/page_map'
@app.route('/page_map', methods=['GET'])
def page_map():
    # Готовим данные для заполнения карты и маршрута
    dataMap = session.get('data_map')
    print('dataMap',dataMap)
    services,branches = get_branches_servicecat()
    response={
        'branches':branches,
        'dataMap':dataMap
    }
    json_data = json.dumps(response)
    # Отображаем страницу page_map и передаем данные для отображения карты
    return render_template('page_map.html', dataMap=json_data)

# Обработчик для сохранения данных карты в сессии
@app.route('/save_data_map', methods=['POST'])
def save_data_map():
    # Получаем данные из запроса
    data = request.get_json()
    # Сохраняем данные в сессии
    session['data_map'] = data
    return jsonify({'message': 'Данные успешно сохранены в сессии'}), 200

@app.route('/get_session_data', methods=['GET'])
def get_session_data():
    data = session.get('data_find')
    return jsonify({'data': data})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
