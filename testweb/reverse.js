ymaps.ready(function () {
    var myMap = new ymaps.Map('map', {
            center: [43.7931, 131.9514],
            zoom: 12,
            controls: ['zoomControl','fullscreenControl']
        }, {
            searchControlProvider: 'yandex#search'
        });
});