# elehant_meter
Компонент интеграции счётчиков ресурсов от Элехант с Home Assistant.

## Требования
* Для интеграции требуется наличие Bluetooth модуля в сервере HA.
* Модуль тестировался при использовании esphome esp32-bluetooth-proxy, работу с физическим адаптером bluetooth не проверялся.
* Код для работы с известными счетчиками добавлен, но не проверялся т.к. у автора нет этих счетчиков 

## Поддерживаются
### Газовые счётчики:
* СГБД-1.8 - не тестировался
* СГБД-3.2 - не тестировался
* СГБД-4.0 - работает
* СГБД-4.0 ТК - не тестировался
* СОНИК G4TK - не тестировался

### Счётчики воды:
* СВД-15 - не тестировался
* СВД-20 - не тестировался
* СВТ-15 - не тестировался
* СВТ-20 - не тестировался



## Установка
1. Скопируйте папку **elehant_meter** в **custom_components** в корне конфигурации Home Assistant
2. В **configuration.yaml** добавьте следующие строки:

    ```yaml
    sensor:
      - platform: elehant_meter
        
    ```

* Для меня это первая разработка интеграции для  Home Assistant и первое знакомство с языком Python так, что не судите строго. Данная интеграция это «я его слепила из того что было» )))
* Изобретать свой велосипед пришлось из-за того, что имеющиеся интеграции не поддерживают esp32-bluetooth-proxy
