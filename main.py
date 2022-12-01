import pandas as pd
import numpy as np

# Постройте список уникальных типов самолетов зарегистрированных в России

aircrafts = pd.read_csv('data/aircraft.csv',
                        sep=';',
                        parse_dates=['дата действующего свидетельства о регистрации'],
                        dayfirst=True,)

unique_types = pd.unique(aircrafts['Тип (наименование) воздушного судна'])

print(f'Список уникальных типов самолётов:\n'
      f'{unique_types}\n'
      f'Всего типов:{len(unique_types)}\n')

# Какой тип самолета имеет самую раннюю дату выдачи сертификата?

earliest_plane_type = aircrafts[aircrafts['дата действующего свидетельства о регистрации'] ==
                                min(aircrafts['дата действующего свидетельства о регистрации'])]

print(f'Самолёт с самой ранней датой выдачи сертификата:\n'
      f'{earliest_plane_type.iloc[0]["Тип (наименование) воздушного судна"]}\n'
      f'Выдан {earliest_plane_type.iloc[0]["дата действующего свидетельства о регистрации"]}\n')


# Постройте запрос: Владелец аэропорта, Аэропорт,
# Пассажиропоток суммарный за 2018 год, Грузопоток суммарный за 2018 год


def read_airports(string):
    """My best attempt at formating column 0 in 'airports.csv'"""
    string = string.strip()
    if '(' in string:
        string = '('.join([x.strip() for x in string.split(' (')])
    if ' – ' in string:
        string = string.replace(' – ', '-')
    return string


airports = pd.read_csv('data/airports.csv',
                       names=['Наименование аэропорта РФ', 'Сертификат',
                              'Владелец', 'Тип'],
                       converters={0: read_airports,
                                   1: lambda x: x.strip(),
                                   2: lambda x: x.strip(),
                                   3: lambda x: x.split()[0]})

cargo = pd.read_csv('data/cargo transportation.csv',
                    sep=';',
                    na_values='***',
                    thousands=' ',
                    decimal=',')

passengers = pd.read_csv('data/passenger transportation.csv',
                         sep=';',
                         na_values='***',
                         thousands=' ',
                         decimal=',')

cargo_pass_2018 = pd.DataFrame()
cargo_pass_2018['Наименование аэропорта РФ'] = cargo[cargo['Год периода данных'] == 2018]['Наименование аэропорта РФ']
cargo_pass_2018['Грузопоток суммарный'] = cargo[cargo['Год периода данных'] == 2018].iloc[:, 2:15].sum(axis=1)
cargo_pass_2018['Пассажиропоток суммарный'] = passengers[passengers['Год периода данных'] == 2018].iloc[:, 2:15].sum(axis=1)
df = pd.merge(cargo_pass_2018, airports, on='Наименование аэропорта РФ').drop(labels=['Сертификат', 'Тип'], axis=1)

print('Результат запроса:\n',
      df,
      '\n')


# Перечислите аэропорты, где пассажиропоток меньше медианы, а  грузопоток больше медианы

pass_median = np.median(cargo_pass_2018['Пассажиропоток суммарный'].unique())
cargo_median = np.median(cargo_pass_2018['Грузопоток суммарный'].unique())
airports_query = cargo_pass_2018.query('`Пассажиропоток суммарный` < @pass_median &'
                                       ' `Грузопоток суммарный` > @cargo_median')

print('Список аэропортов:\n',
      *airports_query['Наименование аэропорта РФ'],
      f"\nВсего аэропортов:{len(airports_query['Наименование аэропорта РФ'])}\n")

# Перечислите авиакомпании у которых нет типов воздушных судов зарегистрированных в России


def read_planes(lst):
    """Formating last column in 'airlines.csv' """
    return [x.lstrip().split('(')[0] for x in lst.split(',')]


airlines = pd.read_csv('data/airlines.csv',
                       sep=',',
                       names=['Компания', 'Полное название',
                              'Аэропорты', 'Тип (наименование) воздушного судна'],
                       index_col=0,
                       converters={3: lambda x: x.split(),
                                   4: read_planes})

avia_types = set(item for lst in airlines['Тип (наименование) воздушного судна'] for item in lst)
rus_types = avia_types.intersection(set(unique_types))
airlines['found_planes'] = [' '.join(rus_types.intersection(lst)) for lst in airlines['Тип (наименование) воздушного судна']]
non_rus_airlines = airlines[airlines['found_planes'].astype(bool)]['Компания']
airlines.drop(labels=['found_planes'], axis=1)

print('Авиакомпании у которых нет типов воздушных судов зарегистрированных в России:\n',
      ', '.join(non_rus_airlines), '\n',
      f'Количество авиакомпаний:{len(non_rus_airlines)}\n')

# Выведите таблицу: Месяц, суммарный пассажиропоток за данный месяц,
# аэропорт в котором пассажиропоток в данном месяце максимальный

year = 2017
passenger_year = passengers[passengers['Год периода данных'] == year]
passenger_year = passenger_year.drop(['Год периода данных', 'Январь - Декабрь'], axis=1)
passenger_year = passenger_year.dropna(axis=0, thresh=7).T
passenger_year.columns = passenger_year.loc['Наименование аэропорта РФ']
passenger_year = passenger_year.drop('Наименование аэропорта РФ', axis=0).astype(int)
month_sum = pd.DataFrame(passenger_year.sum(axis=1)).set_axis(['Средний пассажиропоток'], axis=1)
month_sum['Аэропорт'] = passenger_year.idxmax(axis=1)
print(month_sum, '\n')

# Выведите таблицу: Тип аэропорта, средний грузопоток в месяц в аэропортах данного типа

year = 2017
cargo_year = cargo[cargo['Год периода данных'] == year]
merged_cargo = pd.merge(cargo_year, airports).drop(labels=['Сертификат', 'Владелец', 'Год периода данных'], axis=1)
print(merged_cargo.groupby('Тип').median(numeric_only=True).dropna(axis=0, thresh=7))
