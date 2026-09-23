# CI
Здесь указана информация о ci сервиса с прогонами тестов, билда образа и деплоя. Ci написан в файле ci.yml. Тесты прогоняются при pull request в ветку main. Тесты вместе с билдом образа и деплоем прогоняются после слияния с веткой main. Дополнительно в /health сервиса добавили информацию о конфигах из configmap, интеграционный тест с проверкой кода ответа сервиса при Post запросе и полями блока features, которые пришли в бд при логировании предсказаний модели. Также в пайплайне реализован smoke, который проверяет, что возвращаемое значение во входной поток находится в диапазоне от 0.0 до 1.0 (вероятность оттока клиента)


## базовый пайплайн
Успешный пайплайн со всеми этапами тестов, сборки, деплоя доступен по ссылке: https://github.com/Npudov/ML-Service-Telecom-Churn-Prediction/actions/runs/35922134182 
Образ сервиса с sha коммита находится в packages по ссылке: https://github.com/Npudov/ML-Service-Telecom-Churn-Prediction/pkgs/container/ml-service-telecom-churn-prediction/1286714715?tag=sha-2f07b1325037f6dc6f480ce2b232cc9d9705e4bf

## Возможные ошибки в пайплайне

### Сломанные тесты
Давайте сломаем наши тесты и увидим, что пайплайн с тестами не проходит pull request, а затем починим тесты
Ссылка на pull request: https://github.com/Npudov/ML-Service-Telecom-Churn-Prediction/pull/12

### Сломанный configMap
Давайте неверно укажем путь к модели в configMap и посмотрим,что произойдет с нашим пайплайном при Pull request и при деплое. Затем починим ошибку

Ссылка на неуспешный job: https://github.com/Npudov/ML-Service-Telecom-Churn-Prediction/actions/runs/35906034595/job/107334260005
Ссылка на успешный job: https://github.com/Npudov/ML-Service-Telecom-Churn-Prediction/actions/runs/35907191847

В логах увидим, что при job deploy наш пайплайн не нашёл нашу модель на шаге `сервис` и выкинет исключение FileNotFoundError: [Errno 2] No such file or directory: 'artifacts/baseline_logreg.joblib'


### Неверное имя secrets по сравнению с именем в кластере
Давайте неверно укажем имя секрета в secretRef, чтобы оно не совпало с именем churn-secrets, которое задает пайплайн и узнаем,что будет с нашим деплоем. Затем починим ошибку.

Ссылка на неуспешный job: https://github.com/Npudov/ML-Service-Telecom-Churn-Prediction/actions/runs/35907747729/job/107339949353
Ссылка на успешный job: https://github.com/Npudov/ML-Service-Telecom-Churn-Prediction/actions/runs/35908828263

В логах увидим, что при job deploy наш пайплайн упал на шаге `сервис` и в нём увидим, что наш под churn-service в статусе CreateContainerConfigError и также информация, что в нашем container с именем api Error from server (BadRequest): container "api" in pod "churn-service-5c49dc95cd-dxj7s" is waiting to start: trying and failing to pull image

### Неверное указание requests
Давайте неверно укажем requests (зададим значение таким (1000000Mi), которое превышает физически доступное) и посмотрим, что будет с деплоем. Затем починим ошибку

Ссылка на неуспешный job: https://github.com/Npudov/ML-Service-Telecom-Churn-Prediction/actions/runs/35909343894
Ссылка на успешный job: https://github.com/Npudov/ML-Service-Telecom-Churn-Prediction/actions/runs/35910795237

В логах увидим, что при job deploy наш пайплайн упал на шаге `сервис` и в нём увидим, что The Deployment "churn-service" is invalid: spec.template.spec.containers[0].resources.requests: Invalid value: "9223372036854775807": must be less than or equal to memory limit of 512Mi
service/churn-service created . Это означает, что ресурсов для пода не хватило и он не создался. Логи подов показали, что пода нет - Error from server (NotFound): deployments.apps "churn-service" not found
error: error from server (NotFound): deployments.apps "churn-service" not found in namespace "default"



### Важные моменты
1. Job Build в первом прогоне шёл 52 секунды (https://github.com/Npudov/ML-Service-Telecom-Churn-Prediction/actions/runs/35791632962), во втором - 47 секунд (https://github.com/Npudov/ML-Service-Telecom-Churn-Prediction/actions/runs/35794830076/job/106971718706). Из Dockerfile кэшировались слои с установкой uv, переход в рабочую директорию /app, и установка зависимостей по файлу uv.lock. Данные слои кэшировались поскольку в нижние слои мы положили реже изменяющийся набор зависимостей и если изменились верхние слои (например код, а зависимости нет), то на нижних слоях будет использоваться кэширование поскольку зависимости там не менялись, а вот тому,что завязано на изменившимся коде придется пересобираться. Поэтому то, что меняется редко класть первым вниз, а то,что чаще - наверх.
2. Поды при успешных прогонах находятся в ImagePullBackOff поскольку kubernetes не мог их скачать из реестра поскольку данные образа не были загружены в kind через load docker-image (при применении манифестов образы недоступны в кластере вот Kind И создал под них поды со статусом ImagePullBackOff, далее уэе загружается конкретный образ с хэш коммита)
3. Пароль от базы помещается в переменную контейнера postgres с именем переменной POSTGRES_PASSWORD,туда он приходит из churn-secrets кластера kind по ключу POSTGRES_PASSWORD. В кластере Kind в churn-secrets по literal POSTGRES_PASSWORD значение приходит из secrets Github с ключом DB_PASSWORD, там пароль находится в зашифрованном виде. Поэтому путь это Secrets Github - secrets kind churn-secrets - переменная окружения POSTGRES_PASSWORD контейнера postgres. У Database_url путь аналогичен, только там из Github приходит только пароль, далее эта конфигурация попадает в виде переменной окружения DATABASE_URL в churn-service с контейнером api и уже далее pydantic_settings по имени вытаскивает database_url в конфиг приложения и он используется уже самим сервисом внутри себя.
4. Build делается после test благодаря конструкции needs в ci.yml. Это необходимо для того,чтобы избежать негативного сценария, когда мы запушили образ раньше, чем успешно прошли тесты, в результате deploy будет идти без предварительной проверки и приложение выкатится с ошибками тестирования (сломанным), а образ в регистре контейнеров будет с кодом сломанного приложения
5. В Pull request проверяются только тесты поскольку это предложение на слияние с веткой и на этом этапе достаточно проверить, что код не ломает существующую функциональность. Проверять build и deploy на каждом PR избыточно и регистр контейнеров будет забиваться множеством лишних образов
6. pg_advisory_xact_lock необходимо,чтобы одна из реплик получила лок на ресурсы, сделала свои операции,далее лок получает вторая реплика и продолжает выполнение своего кода. Это полезно, поскольку обе реплики могут попытаться создать одновременно таблицы и одна будет постоянно падать с ошибкой так как таблица уже создана. pg_advisory_xact_lock является транзакционным локом и снимается, когда происходит commit транзакции или rollback  
7.  Поды churn-service были в статусе churn-service not found (при неверном requests), ErrImagePull (ошибка при скачивании образа) и СreateContainerConfigError (ошибка конфига контейнера) (при невреном имени secrets в deployment churn-service), CrashLoopBackOff (бесконечно стартует и падает по кругу, неверное указание пути в configMap для модели)


### Возникшие проблемы
Также ещё отмечу ошибку, что в ходе написания ci сервиса возникла проблема, что забыл указать в deployment откуда брать для переменных окружения контейнера значения (не указал secretRef), в результате на job deploy на шаге smoke при проверке числа записей в логах предсказания окажется, что таблица не создана поскольку именно из secretRef мы бы получили database_url (строка соединения к бд с паролем к базе), а поскольку мы не получили эти значения, то и соединиться не смогли. 