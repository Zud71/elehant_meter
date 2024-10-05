# elehant_meter
Компонент интеграции счётчиков ресурсов от Элехант с Home Assistant.

Подробнее можно почитать [тут](https://orycan.ru/blog/post/elehant_meter)

## Требования
* Для интеграции требуется наличие Bluetooth модуля в сервере HA.
* Модуль тестировался при использовании esphome esp32-bluetooth-proxy, так же должен работать с физическим адаптером bluetooth
* Код для работы с известными счетчиками добавлен, но не проверялся т.к. у автора нет этих счетчиков 

## Поддерживаются
### Газовые счётчики:
* СГБД-1.8 - работает
* СГБД-3.2 - не тестировался
* СГБД-4.0 - работает
* СГБД-4.0 ТК - не тестировался
* СОНИК G4TK - не тестировался

### Счётчики воды:
* СВД-15 - работает
* СВД-20 - не тестировался
* СВТ-15 - работает
* СВТ-20 - не тестировался



## Установка
### В ручную
1. Скопируйте папку **elehant_meter** в **custom_components** в корне конфигурации Home Assistant
2. В **configuration.yaml** добавьте следующие строки:

    ```yaml
    sensor:
      - platform: elehant_meter
        
    ```
### Через HACS
HACS > Интеграции > 3 точки (правый верхний угол) > Пользовательские репозитории > Вводим: Zud71/elehant_meter, Категория: Интеграция > Добавить > подождать > elehant_meter > Установить

* Для меня это первая разработка интеграции для  Home Assistant и первое знакомство с языком Python так, что не судите строго. Данная интеграция это «я его слепила из того что было» )))
* Изобретать свой велосипед пришлось из-за того, что имеющиеся интеграции не поддерживают esp32-bluetooth-proxy

  ____

## Скриншоты

![Screenshot status](images/img1.png)
