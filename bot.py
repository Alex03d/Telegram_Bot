import telebot
import config
import requests
from typing import Union
bot = telebot.TeleBot(config.TOKEN)


class InputData:
    """
    Класс информации, приходящей с сайта ФНС в ответ на запрос.
    """

    def __init__(self,
                 name: Union[str, int],
                 ogrn: str,
                 inn: str,
                 kpp: str,
                 address: str
                 ) -> None:
        self.name = name,
        self.ogrn = ogrn,
        self.inn = inn,
        self.kpp = kpp,
        self.address = address

    def get_final_name(self) -> str:
        """
        Полное наименование приходит кортежем заглавными
        буквами. Приводим в формат:
        "общество с ограниченной ответственностью «РОМАШКА»".
        """

        pre_name = ''.join(self.name)
        name_split = pre_name.split(sep='"')
        company_form = name_split[0].lower()
        name_short = ''.join(name_split[1:])
        self.final_name = f'{company_form}«{name_short}» '
        return self.final_name

    def get_final_numbers(self) -> str:
        """
        Тут так же методом join() пробразуем каскады в строку.
        Иначе потом информация выводится в квадратных скобках.
        """

        self.final_numbers = '(ОГРН ' + ''.join(self.ogrn) + ', ' \
                             + 'ИНН ' + ''.join(self.inn) + ', ' \
                             + 'КПП ' + ''.join(self.kpp) + ')' + '\n' + '\n'
        return ''.join(self.final_numbers)

    def get_final_address(self) -> str:
        """
        Манипуляции с каскадами, содержащими информацию по адресам.
        """

        pre_split_string = self.address.split(', ')
        if 'РОССИЯ' in pre_split_string:
            split_string = pre_split_string[:1] + pre_split_string[2:]
        else:
            split_string = pre_split_string

        index = split_string[0]
        if 'МОСКВА' in split_string[1]:
            pre_city = split_string[1].title()
            city = pre_city.replace('Город', '')
            address_street = "".join(split_string[2]).title()
            address_house = " ".join(split_string[3:]).lower()
            address_stage_1 = f'Адрес: {address_street}, ' \
                              f'{address_house}, '\
                              f' город {city}, {index}'

        elif 'САНКТ-ПЕТЕРБУРГ' in split_string[1]:
            pre_city = split_string[1].title()
            city = pre_city.replace('Город', '')
            address_street = "".join(split_string[2]).title()
            address_house = " ".join(split_string[3:]).lower()
            address_stage_1 = f'Адрес: {address_street}, {address_house}, '\
                              f' город {city}, {index}'

        elif 'СЕВАСТОПОЛЬ' in split_string[1]:
            pre_city = split_string[1].title()
            city = pre_city.replace('Город', '')
            address_street = "".join(split_string[2]).title()
            address_house = " ".join(split_string[3:]).lower()
            address_stage_1 = f'Адрес: {address_street}, {address_house}, '\
                              f' город {city}, {index}'

        else:
            region = split_string[1].title()
            pre_city = split_string[2].title()
            city = pre_city.replace('Город', '')
            address_street = "".join(split_string[3]).title()
            address_house = "".join(split_string[4]).lower()
            address_stage_1 = f'Адрес: {address_street}, {address_house}, '\
                              f' город {city}, {region}, {index}'

        if 'Улица' in address_stage_1:
            address_stage_2 = address_stage_1.replace('Улица', 'улица')

        elif 'Проспект' in address_stage_1:
            address_stage_2 = address_stage_1.replace('Проспект', 'проспект')

        elif 'Набережная' in address_stage_1:
            address_stage_2 = address_stage_1.replace('Набережная', 'набережная')

        elif 'Переулок' in address_stage_1:
            address_stage_2 = address_stage_1.replace('Переулок', 'переулок')

        else:
            address_stage_2 = address_stage_1

        self.final_address = address_stage_2
        return self.final_address


class ReceivedMessage:
    """
    Класс сообщений, полученных от пользователя.
    Сейчас сделал только под ИНН. Поэтому в родительском
    классе пока pass.
    """

    pass


class ReceivedInn(ReceivedMessage):
    """
    Класс сообщений с номерами ИНН, полученных от пользователя
    """

    def __init__(self,
                 text: str
                 ) -> None:
        self.text = text

    def request_data(self) -> InputData:
        """
        Запрос данных с сайта ФНС. Возвращается экземпляр
        класса InputData
        """

        inn = self.text
        url = 'https://egrul.nalog.ru'
        url_1 = 'https://egrul.nalog.ru/search-result/'
        s = requests.Session()
        s.get(url + '/index.html')
        r = s.post(url, data={'query': inn}, cookies=s.cookies)
        r1 = s.get(url_1 + r.json()['t'], cookies=s.cookies)
        self.name = r1.json()['rows'][0]['n']
        self.ogrn = r1.json()['rows'][0]['o']
        self.inn = r1.json()['rows'][0]['i']
        self.kpp = r1.json()['rows'][0]['p']
        self.address = r1.json()['rows'][0]['a']
        return InputData(self.name,
                         self.ogrn,
                         self.inn,
                         self.kpp,
                         self.address
                         )


@bot.message_handler(func=lambda message: True)
def echo_message(message) -> None:
    """
    Вывод информации в ответ на запрос
    """

    if message.text == "Привет":
        bot.send_message(message.from_user.id, "Привет, введи ИНН")
    elif len(message.text) == 10:
        received_inn = ReceivedInn(message.text)
        requested_data = received_inn.request_data()
        final_name = requested_data.get_final_name()
        final_numbers = requested_data.get_final_numbers()
        final_address = requested_data.get_final_address()
        final_message = final_name + final_numbers + final_address
        bot.send_message(message.from_user.id, final_message)
    else:
        bot.send_message(message.from_user.id, "Я тебя не понимаю. \n"
                                               "Нужно ввести ИНН.")


bot.polling()
