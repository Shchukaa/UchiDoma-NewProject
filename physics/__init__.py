import re
import difflib
from language import infinitive, inflecting
from config import question_words, synonym_words
from config import db_info


# Выделение физических феличин из текста
async def input_corr(text: str) -> list:
    numbers = re.findall(r'\d+(?:,*\d+)*(?:[\-\+]\d+)*\s[а-яА-Я]+(?:\/(?:[а-я])+)*\d*', text)
    # units_transfrom()
    return numbers


# Проверка совпадения
async def similarity(s1: str, s2: str) -> float:
    normalized1 = s1.lower()
    normalized2 = s2.lower()
    matcher = difflib.SequenceMatcher(None, normalized1, normalized2)
    return matcher.ratio()


"""
# Доделать функцию перевода единиц измерения
def units_tranfrom(numbers: list) -> list:
    for i in range(len(numbers)):
        number = numbers[i].split()[0]
        unit = numbers[i].split()[1]
        for un in ci_units:
            if un in unit and (unit.replace(un, '') in units or len(unit.replace(un, '')) == 0):
                if un == 'с' and unit[2] != 'м':
                    pass
                else:
                    unit = unit.replace(un, '')
                    number = int(number) * ci_units[un]
                print(un, unit, number)
"""


# Основная функция
async def physics_calc(text: str) -> list:
    units = map(lambda x: x.split()[1], await input_corr(text))
    print(*units)

    """
    # Можно сделать из этого дополнительную проверку
    # Не работает, т.к. есть разные величины с одними и теми же единицами измерения
    # Добавление формул по совпадениям единиц измерений
    res = []
    for elem in units:
        for unit in result:
            if unit[3] == elem:
                if unit[1] is not None:
                    res.append(unit[0] + ' = ' + unit[1])
                if unit[2] is not None:
                    res.append(unit[0] + ' = ' + unit[2])
    """

    # Вычисление совпадений

    # Для начала создаем список из инфинитивов слов запроса и их склоненией
    inf_l = []
    infl_l = []
    text = text.replace('.', ' ').replace(',', ' ').lower().split()
    print(text)
    for i in range(len(text) - 1):
        inf = infinitive(text[i])
        inf_l.append(inf)
        infl = inflecting(text[i], text[i + 1])
        infl_l.append(infl)
    inf_l.append(infinitive(text[-1]))
    print(inf_l)
    print(infl_l)
    """ 
    # Можно сделать проверку из этого на человеческий фактор(неправильное написание 1-2 букв)
    cursor.execute('''SELECT name FROM "values"''')
    names = tuple(map(lambda x: x[0], cursor.fetchall()))

    sims = []
    for word in inf_l:
        pairs_sim = tuple(filter(lambda x: x[2] >= 0.95,
                                 [(name, word, await similarity(name, word)) for name in names]))
        if pairs_sim:
            print(pairs_sim)
            sims.append(pairs_sim[0][0])
    """

    # Добавление формул по совпадениям слов + поиск спрашиваемой величины
    # Важно проверять не пару предыдущий+текущий, а пару текущий+следующий, чтобы избежать лишних физических величин
    # Пример:
    # Сила упругости -> сила, сила упругости.
    # Переложить всю обработку в модуль math
    res = []

    # Идентификация спрашиваемых величин(identification requested values)
    irv = False

    # Индикатор отработки двойного запроса
    # (Очевидно, что если в цикле нашлась физическая величина с именем текущее слово + следующее слово, то
    # следующее слово отдельно нам не нужно проверять как одиночный запрос, например:
    # Текущее слово средняя, следующее слово скорость
    # Найдено: средняя скорость -> пропуск следующего цикла со словом скорость
    double_value = False

    requested_values = []
    print(*db_info, sep='\n')
    required_values = {}

    for i in range(len(inf_l)):
        if double_value:
            double_value = False
        elif len(inf_l[i]) > 3 and not inf_l[i].isdigit():
            print('-' + inf_l[i] + '-')

            # Индикатор вопроса
            if inf_l[i] in question_words:
                print('------------')
                print('irv')
                print('------------')
                irv = True

            # Проверка на синонимичную идентичность с последующей заменой слова на аналог, представленный в базе данных
            if inf_l[i] in ';'.join(synonym_words):
                for elem in synonym_words:
                    if inf_l[i] in elem:
                        inf_l[i] = elem.split(';')[0]

            # Выделение формул из текста путем проверки совпадения для всех значений из базы данных
            for value in db_info:
                print('Cycle:', value[3], '-', inf_l[i])
                if i != len(inf_l) - 1:
                    print(text[i], inf_l[i + 1])
                    # Проверка на составной запрос (текущее слово + следующее слово)
                    if infl_l[i] and (infl_l[i] + ' ' + inf_l[i + 1] == value[3]
                                      or inf_l[i] + ' ' + text[i + 1] == value[3]
                                      or text[i] + ' ' + text[i + 1] == value[3]):
                        print('Составной запрос:', text[i] + ' ' + inf_l[i + 1])
                        double_value = True
                        if irv:
                            requested_values.append(value)
                            print('------------')
                            print(requested_values)
                            print('------------')
                        if value[0] in required_values:
                            required_values[value[0]].append(value[1])
                        else:
                            required_values[value[0]] = [value[1]]

                        res.append(value[0] + ' = ' + value[1])

                    # Проверка на одиночный запрос (текущее слово)
                    elif inf_l[i] == value[3]:
                        print('Одиночный запрос:', inf_l[i])
                        if irv:
                            requested_values.append(value)
                            print('------------')
                            print(requested_values)
                            print('------------')
                        if value[0] in required_values:
                            required_values[value[0]].append(value[1])
                        else:
                            required_values[value[0]] = [value[1]]

                        res.append(value[0] + ' = ' + value[1])
                else:
                    # В последнем цикле делаем проверку только на одиночный запрос
                    if inf_l[i] == value[3]:
                        print('Одиночный запрос:', inf_l[i])
                        if irv:
                            requested_values.append(value)
                            print('------------')
                            print(requested_values)
                            print('------------')
                        if value[0] in required_values:
                            required_values[value[0]].append(value[1])
                        else:
                            required_values[value[0]] = [value[1]]

                        res.append(value[0] + ' = ' + value[1])
            # irv = False

    if requested_values:
        required_values = list(dict.fromkeys(requested_values))
        print('Найти:')
        for elem in required_values:
            print(elem[0] + ' - ' + elem[3])
    else:
        print('Не могу определить вопрос')

    for key in required_values:
        required_values[key] = list(dict.fromkeys(required_values[key]))
    print(f'required_values: {required_values}')
    res = list(dict.fromkeys(res))

    return res
