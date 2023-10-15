function service_load() {
   // Определяем текущую страницу
var currentPage = window.location.pathname;

// Переменная для данных, которые будем отправлять на сервер
var formData;

// Проверяем текущую страницу и собираем данные в зависимости от нее
if (currentPage === "/content_two") {
    // Если на странице "content_two", собираем данные из формы
   var form = document.getElementById("service-form");
   formData = new FormData(form);
   // Получаем id выбранной категории услуги из выпадающего списка
    var selectedCategoryId = parseInt(document.getElementById("bank_services_list").value);
} else if (currentPage === "/page_map") {
    // Если на странице "page_map", собираем данные из select меню
    var selectedValueP=parseInt(document.getElementById("bank_services_list_map").value)
    // Получаем id выбранной категории услуги из выпадающего списка
    var selectedCategoryId = parseInt(document.getElementById("bank_services_list_map").value);
    // Создаем объект с данными
    formData = { selectedValue: selectedValueP };
}

// Определяем URL вашего Flask-приложения, куда будет отправляться запрос
var url = "/service_load"; // Замените на реальный путь к вашему Flask-приложению
// Создаем объект XMLHttpRequest для отправки запроса на сервер
var xhr = new XMLHttpRequest();
// Настраиваем запрос
xhr.open("POST", url, true);
xhr.setRequestHeader("X-Requested-With", "XMLHttpRequest");

// Преобразуем объект с данными в JSON, если это необходимо
var jsonData = JSON.stringify(formData);

// Определяем обработчик события, который будет выполняться после завершения запроса
xhr.onload = function () {
    if (xhr.status === 200) {
        // Обрабатываем ответ от сервера
        var response = JSON.parse(xhr.responseText);
            // Получаем данные о времени ожидания и отделениях из ответа
            var timeData = response['total_time'];

            var branchData = response['branch'];


            // Вычисляем и отображаем маршрут
            calculateAndPrintRoute(branchData)
                .then(function (result) {
                    // Обрабатываем результат функции calculateAndPrintRoute()
                    var waitingTimes = {};

                    // Обрабатываем объект timeData
                    for (var key in timeData) {
                        if (timeData.hasOwnProperty(key)) {
                            var ids = key.split(',');
                            var idBranch = parseInt(ids[0]);
                            var idService = parseInt(ids[1]);
                            var timeInMinutes = parseFloat(timeData[key]);

                            // Проверяем, соответствует ли idService выбранной категории
                            if (idService === selectedCategoryId) {
                                // Если да, сохраняем время ожидания для отделения
                                waitingTimes[idBranch] = timeInMinutes;
                            }
                        }
                    }

                    // Формируем информацию о отделениях
                    var branchesInfo = result.map(function(branch) {
                        var idBranch = branch.idBranch;
                        var totalTime = branch.totalTime;
                        var travelTime = branch.totalTime; // Пока используем общее время как время в пути
                        var waitingTime = waitingTimes[idBranch] || 0; // Получаем время ожидания из waitingTimes, если нет, то 0
                        var totalMinutes = totalTime + waitingTime; // Общее время (в минутах)
                        var coordinatesStart = branch.coordinatesStart;
                        var coordinatesEnd = branch.coordinatesEnd;
                        var modeOfTransport = branch.modeOfTransport;

                        return {
                            idBranch: idBranch,
                            totalTime: totalTime,
                            travelTime: travelTime,
                            waitingTime: waitingTime,
                            totalMinutes: totalMinutes,
                            coordinatesStart: coordinatesStart,
                            coordinatesEnd: coordinatesEnd,
                            modeOfTransport: modeOfTransport
                        };
                    });

                    // Находим отделение с минимальным временем и получаем информацию о нем
                    var minBranch = branchesInfo.reduce(function(prev, current) {
                        return (prev.totalMinutes < current.totalMinutes) ? prev : current;
                    });

                    // Получаем данные о минимальном отделении
                    var minBranchId = minBranch.idBranch;
                    var minTravelTime = minBranch.travelTime || 0; // Если нет данных, выводим "Н/Д"
                    var minWaitingTime = minBranch.waitingTime || 0; // Если нет данных, выводим "Н/Д"
                    var minTotalMinutes = minBranch.totalMinutes;
                    var minBranchCoordStart = minBranch.coordinatesStart;
                    var minBranchCoordEnd = minBranch.coordinatesEnd;
                    var minBranchmodeOfTransport = minBranch.modeOfTransport;

                    // Выводим информацию о минимальном отделении в консоль
                    console.log(`Выбранное отделение: ${minBranchId}`);
                    console.log(`Время в пути: ${minTravelTime} мин`);
                    console.log(`Время в очереди: ${minWaitingTime} мин`);
                    console.log(`Общее время: ${minTotalMinutes} мин`);
                    console.log(`Мое местоположение: ${minBranchCoordStart}`);
                    console.log(`Банка местоположения: ${minBranchCoordEnd}`);
                    console.log(`Способ передвижения: ${minBranchmodeOfTransport}`);

                    // Сохраняем данные для передачи и передаем их на страницу карты
                    var sendDataToMap = {
                        'myCoord': minBranchCoordStart,
                        'branchCoord': minBranchCoordEnd,
                        'modeOfTransport': minBranchmodeOfTransport
                    };

                    // Отправляем данные на сервер для сохранения в сессии
                    fetch('/save_data_map', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(sendDataToMap)
                    })
                    .then(response => response.json())
                    .then(data => {
                        console.log(data.message); // Должно вывести "Данные успешно сохранены в сессии!"
                    })
                    .catch(error => {
                        console.error('Произошла ошибка:', error);
                    });

                    // Перенаправляем пользователя на страницу с картой
                    window.location.href = "/page_map";
                })
                .catch(function (error) {
                    // Обрабатываем ошибки, если что-то пошло не так в calculateAndPrintRoute()
                    console.error("Произошла ошибка:", error);
                });
        } else {
            // Выводим ошибку, если статус ответа не 200
            console.error("Произошла ошибка:", xhr.status, xhr.statusText);
        }
    };

    // Отправляем данные формы на сервер
    xhr.send(formData);

    // Предотвращаем стандартное поведение формы (перезагрузку страницы)
    event.preventDefault();
}

// Функция для рассчета маршрута с использованием API Yandex Maps
function calculateRoute(startPoint, endPoint, modeOfTransport) {
    // Возвращаем новый Promise, который разрешается, когда маршрут будет успешно рассчитан, или отклоняется в случае ошибки.
    return new Promise(function (resolve, reject) {
        // Используем ymaps.ready, чтобы удостовериться, что API Yandex Maps загружено.
        ymaps.ready(function () {
            // Создаем экземпляр маршрута.
            var multiRoute = new ymaps.multiRouter.MultiRoute({
                referencePoints: [
                    startPoint,
                    endPoint
                ],
                params: {
                    // Тип маршрута (пешком, на общественном транспорте и т. д.).
                    routingMode: modeOfTransport,
                    // Учитывать пробки
                    avoidTrafficJams: true
                }
            }, {
                // Автоматически устанавливать границы карты так,
                // чтобы маршрут был виден целиком.
                boundsAutoApply: true
            });

            // Добавляем маршрут на карту.
            multiRoute.model.events.add("requestsuccess", function () {
                // Получаем информацию о маршруте после успешного запроса.
                var routes = multiRoute.getActiveRoute();
                var totalWay = routes.properties.get("distance").text;
                var totalTime = routes.properties.get("duration").text;

                // Преобразуем время в минуты
                var parts = totalTime.split(/\s+/);
                var totalDurationInMinutes = 0;
                for (var i = 0; i < parts.length; i += 2) {
                    var value = parseInt(parts[i]);
                    var unit = parts[i + 1].toLowerCase();
                    // Преобразуем значение в минуты в зависимости от единицы измерения
                    switch (unit) {
                        case "дн.":
                        case "дни":
                            totalDurationInMinutes += value * 24 * 60; // дни в минуты
                            break;
                        case "нед.":
                        case "нед":
                        case "недель":
                            totalDurationInMinutes += value * 7 * 24 * 60; // недели в минуты
                            break;
                        case "ч":
                        case "час":
                        case "час.":
                            totalDurationInMinutes += value * 60; // часы в минуты
                            break;
                        case "мин":
                        case "мин.":
                        case "минут":
                            totalDurationInMinutes += value; // минуты
                            break;
                        default:
                            // Неизвестная единица времени
                            break;
                    }
                }

                // Создаем объект с результатами маршрута.
                var result = {
                    totalWay: totalWay,
                    totalTime: totalDurationInMinutes
                };

                // Разрешаем Promise с результатами маршрута.
                resolve(result);
            });

            multiRoute.model.events.add("requestfail", function (error) {
                // Если произошла ошибка при построении маршрута, отклоняем Promise с ошибкой.
                reject(error);
            });
        });
    });
}

// Асинхронная функция для расчета и вывода маршрута
async function calculateAndPrintRoute(coordinatesList) {
fetch('/get_session_data')
          .then(response => response.json())
          .then(data => {
            if (data.data) {
              // Данные из сессии доступны в переменной data.data
              console.log('Данные из сессии:', data.data);
            } else {
              console.log('Нет данных в сессии.');
            }
          })
          .catch(error => {
            console.error('Произошла ошибка:', error);
          });
    // Переменная для хранения начальной точки маршрута
    try{
        var startPoint;
        // Получаем элементы из DOM
        var checkbox = document.getElementById('my_location_checkbox');
        var inputText = document.getElementById('address').value;
        var selectedTextBranch = document.getElementById("service_type").options[document.getElementById("service_type").selectedIndex].text;
        var modeOfTransport = document.getElementById("go").value;
        // Проверяем, отмечен ли чекбокс "Мое местоположение"
    if (checkbox.checked) {
        try {
            // Получаем координаты местоположения пользователя с помощью асинхронной функции getGeolocation()
            startPoint = await getGeolocation();
            console.log("Координаты местоположения:", startPoint);
        } catch (error) {
            // Если произошла ошибка при получении местоположения, выводим сообщение об ошибке в консоль
            console.error("Ошибка получения местоположения:", error);
        }
    } else {
        try {
            // Пытаемся получить координаты из введенного адреса с помощью асинхронной функции ymaps.geocode()
            var res = await ymaps.geocode(inputText, { results: 1 });
            var firstGeoObject = res.geoObjects.get(0);
            var coordinates = firstGeoObject.geometry.getCoordinates();
            startPoint = coordinates[0] + ',' + coordinates[1];
            console.log('Координаты местоположения:', startPoint);
        } catch (error) {
            // Если произошла ошибка при геокодировании адреса, выводим сообщение об ошибке в консоль
            console.error("Ошибка при геокодировании адреса:", error);
        }
    }
    }catch(error){
        var checkbox ;
        checkbox=true;
        fetch('/get_session_data')
          .then(response => response.json())
          .then(data => {
            if (data.data) {
              // Данные из сессии доступны в переменной data.data
              console.log('Данные из сессии:', data.data);
            } else {
              console.log('Нет данных в сессии.');
            }
          })
          .catch(error => {
            console.error('Произошла ошибка:', error);
          });
    }




    // Создаем пустой массив для хранения результатов маршрутов
    var results = [];

    // Итерируемся по списку координат
    for (var i = 0; i < coordinatesList.length - 1; i++) {
        // Проверяем, соответствует ли текущая категория услуги выбранной категории в выпадающем списке
        if (coordinatesList[i][3] == selectedTextBranch) {
            // Формируем конечную точку маршрута в формате "широта,долгота" на основе текущей координаты
            var endPoint = coordinatesList[i][5] + ',' + coordinatesList[i][6];
            try {
                // Вызываем асинхронную функцию calculateRoute с параметрами startPoint, endPoint и modeOfTransport.
                // Функция возвращает объект с информацией о маршруте.
                var routeResult = await calculateRoute(startPoint, endPoint, modeOfTransport);
                // Извлекаем данные о протяженности и времени маршрута из результата функции
                var totalWay = routeResult.totalWay;
                var totalTime = routeResult.totalTime;
                // Добавляем данные о маршруте в массив results
                results.push({
                    idBranch: coordinatesList[i][0],
                    modeOfTransport: modeOfTransport,
                    coordinatesStart: startPoint,
                    coordinatesEnd: endPoint,
                    totalWay: totalWay,
                    totalTime: totalTime
                });

                // Выводим протяженность и время маршрута в консоль (можно закомментировать в финальной версии)
//                console.log("Протяженность маршрута км:", totalWay);
//                console.log("Время в пути мин:", totalTime);
            } catch (error) {
                // Если произошла ошибка при расчете маршрута, выводим сообщение об ошибке в консоль
                console.error("Ошибка при построении маршрута:", error.message);
                // Добавляем пустой результат в массив results, чтобы сохранить структуру данных даже в случае ошибки
                results.push({
                    idBranch: coordinatesList[i][0],
                    coordinatesStart: startPoint,
                    coordinatesEnd: endPoint,
                    totalWay: null,
                    totalTime: null
                });
            }
        }
    }

    // Сортируем массив results по возрастанию totalTime
    results.sort(function(a, b) {
        // Сравниваем totalTime для каждого объекта в массиве
        // Используем a - b для сортировки по возрастанию
        return a.totalTime - b.totalTime;
    });

    // Возвращаем отсортированный массив с результатами маршрутов
    return results;
}

// Функция для получения местоположения пользователя
function getGeolocation() {
    // Возвращаем новый Promise, который разрешается, когда местоположение будет успешно получено, или отклоняется в случае ошибки.
    return new Promise(function(resolve, reject) {
        // Используем ymaps.ready, чтобы удостовериться, что API Yandex Maps загружено.
        ymaps.ready(function() {
            // Получаем объект geolocation
            var geolocation = ymaps.geolocation;

            // Пытаемся получить местоположение от провайдера 'yandex'
            geolocation.get({
                provider: 'yandex',
                mapStateAutoApply: true
            }).then(function(result) {
                // Если успешно, извлекаем координаты и разрешаем Promise с этими координатами
                var yandexCoords = result.geoObjects.get(0).geometry.getCoordinates();
                resolve(yandexCoords);
            }).catch(function(error) {
                // Если не удалось получить от 'yandex', пытаемся получить от провайдера 'browser'
                geolocation.get({
                    provider: 'browser',
                    mapStateAutoApply: true
                }).then(function(result) {
                    // Если успешно, извлекаем координаты и разрешаем Promise с этими координатами
                    var browserCoords = result.geoObjects.get(0).geometry.getCoordinates();
                    resolve(browserCoords);
                }).catch(function(error) {
                    // Если произошла ошибка при получении местоположения, отклоняем Promise с этой ошибкой
                    reject(error);
                });
            });
        });
    });
}
