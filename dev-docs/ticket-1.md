# feat: Use sqlite database instead of file for system settings and business models

## background

Currently system configurations are stored partially in a local yaml file config.yaml and partially in a local json file
called state.json, which makes application state read and write inconvenient, and makes it impossible to scale the data or introduce more models when new features come.

## goal

Replace local files with lightweight database, so that we can save business models and system configuation settings into the database, making it easy to do read and write. And this will pave the way for new features like storing action histories and managing user's parking data.

## design

### database

use sqlite as the database

### ORM

use SQLModel library as the ORM level

### DAO

there should be a DAO interfaces between ORM manipulation and business logics, the interfaces should be written purely using python. The purpose is that even if later we migrate to other databases or maybe memory-only, high-level logic (business logics) will not be impacted. And this is also helpful to unit-testing business logics where we can easily replace databases with file or memory implementations.

## todo

Above is a pre-mature plan and arch. design for the database and models design, but these are basic context. Below are the detail todo list you should begin with.

### new packages and principles
- [ ] A new custom Error class should be defined based on Exception. And more business related sub-class can inherit from this Error class so later we can catch explicit ones for special handling logic.
- [ ] create orm and dao interface packages in the src codebase, but below are the rules:
    - because we believe moduler design principle, so each business module or package should have its own dao interface module/package, which means each separated/isolated module/package should capture its dao layer. This is flexible for later data storage implementations as we can change the dao implemenation code outside the module/package, e.g., in src/ level, so that module/package inner logic won't be affected.
    - orm module/packages are highly depending on database implementation choices, they are implementation level code modules, so they should be defined in /src level, i.e. outside the business module/packages.
    - The relationship between orm, dao, dao implementations is: dao defines interface how business codes interact with model storage; dao implementation implements the retrieval method of model and the model conversion between orm models to business models; while orm models defines the the representation of models as to a specific database.

### config module changes
- [ ] remove src/config/defaults.py, the object in it is used as a default config data when there is no config.yaml in the app folder when app is initializing. This is not good design because it is hard for users to set manually. So we should alway use use config file as a fallback method for app config data. So in `__init__.py` file, if CONFIG_PATH does not exist, exception should be raised.
- [ ] redesign config data model
    - create a model class called AppConfig
    - use popluar data class libs such as pydantic, attrs or python dataclass
    - the AppConfig should in-turn be composed of 2 class instances: MonitorSettings and InternalSettings
- [ ] MonitorSettings Class
    - patterns: a list of regex patterns
    - reaction_emoji: the emoji string to reply to the message matching the pattern, it must be from a list of pre-defined list
    - check_interval: in seconds, interval between each message check, range 1-3s
    - message_number_per_check: during each check cycle, how many messages monitor will check from the latest one to the oldest one. This is highly depending on the messaging speed in that chat group. For now just let user manually set a number.
    - for the MVP version, we don't need notification params, or anti_detect params
- [ ] InternalSettings Class
    - browser_user_data_dir: has default file path "./feishu_browser_data"
    - browser_win_width
    - browser_win_height
    - don't need headless param
    - logging_level: system logging level
    - logging_dir: where log file is written to , default file name is "rpa_bot.log" in the app folder

- [ ] AppConfig data storage (MonitorSettings and InternalSettings)
    - MonitorSettings may be changed dynamically by user more often than InternalSettings, so it should be saved into database instead of a file
    - InternalSettings  technical settings tuned by engineer, so better saved in a file like yaml.
    - design dao interfaces in AppConfig level which  serves business logic code. but as for dao implementations, use database and file as above mentioned
- [ ]  use SQLite as the RDB solution, use yaml as the file solution. their data/file are both saved in the app folder.
- [ ] use SQLModel(by fastapi) for models in SQLite, and use addict lib to load and use yaml data as object
- [ ] rename the config.example.yaml to config.default.yaml, it contains both monitor settings and internal settings currently, but it's fine, those monitor settings are default values if no data saved in db for the first time.
- [ ] since there are many unused setting params to be removed, make sure their usage in the business code are also properly changed or removed. Their corresponding unittests should be properly modified as well.

### Exta-Note-1.
- [ ] There should be a monitor-default-settings.yaml storing default monitor configs at the beginning, because db has no data initially. Every time the app starts, it tries to load monitor settings form db, if no data, tries to load default settings from the yaml file.
- [ ] each package should have its own dao interface, rather than put dao in the core/ folder. For example, config/ package should have dao module/package itself. While dao implementations should be in the src/ folder, the same level as top-level packages, i.e., src/dao/impl/. this is because this level is the correct place the application decides how to implement each package's data storage details.
    - for naming convensions, here is an example: config/dao.py (if design as a module), class AppConfigRepository, which may have get_monitor_settings(), get_internal_settings(), save_monitor_settings(...), save_internal_settings(xxxx), etc.). src/dao/<business-package-name>/ e.g. src/dao/config/SQLiteAppConfigRepository, or InMemoryAppConfigRepository, YamlAppConfigRepository, so that it can have flexibility to use different implementations with dependency injection tech.
    - No not put read/write interfaces of other packages' models, e.g., in config/dao, it should not contain read/write interfaces like group status/history like save_group_state(xxxx)
- [ ] in the ticket, let's only do the migration for config/ package, do not touch group state (state.json).

### Extra-Note-2
- for dao interface and implementations
    - interface use IMonitorSettingsRepository, IInternalSettingsRepository, AppConfigRespository expose all interfaces as a facade pattern.
    - use SqliteMonitorSettingsRepository, YamlMonitorSettingsRepository for IMonitorSettingsRepository
    - use YamlInternalSettingsRepository for IInternalSettingsRepository

### Extra-Note-3
- The config/models.py class definitions are incorrect, some attributes or even classes should be deprecated, please check [[config module changes]] section details and fix .

### Extra-Note-4
- model classes in config/models.py should not define default hard-coded values, these values should be initialized from yamls (as mentioned previously)
- src/dao/config/ package, the implementation classes should be grouped by model not by implementation method, e.g. YamlMonitorSettingsRepository and SqliteMonitorRespository should be in the same module(src/dao/config/monitor_settings_repos.py) or package(src/dao/config/monitor_settings/yaml_repo, sql_repo ), while YamlInternalSettingsRepository should be in the src/dao/config/internal_settings_repos.py or src/dao/config/internal_settings/yaml_repo.py
- in sqlite_repository.py -> get(): when db_model is None, it returns model with hard-coded default attributes values, which is wrong. The correct design is defining another wrapping repository class that implementing IMonitorSettingsRepository, whose get() first try SqliteMonitorSettingsRepository, when get None return then try Yaml version as a default. And the Yaml version if file does not exist, raise exception with proper indication contexts and kindly block the app from continue so that user can have a check to the default setting yaml. Note that the wrapping class's save() will only call Sqlite version's save()
