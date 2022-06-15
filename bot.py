import telebot
import config
import requests
from typing import Union
bot = telebot.TeleBot(config.TOKEN)


class InputData:
    """
    "Это класс информации, приходящей с сайта ФНС
    в ответ на запрос, который содержит данные,
    введенные пользователем.

    На данный момент:
        1) прописал только вариант поиска по ИНН,
        2) выводится информация, отображаемая на
        сайте ФНС (то есть программа сам pdf файл
        с выпиской из ЕГРЮЛ не открывает).
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
        Полное наименование приходит в формате tuple CAPSLOCK-ом,
        из него нужно выделить организационно-правовоую форму,
        которая должна выводиться строчными буквами (метод lower()).

        Для этого сначала методом join() пробразуем tuple
        в строку. После этого - строку разбиваем на две части
        по "границе" открывающих кавычек. Так наименование
        делится на организационно-правовую форму и собственно
        название. Последнее остается прописными буквами.
        """
        pre_name = ''.join(self.name)
        name_split = pre_name.split(sep='"')
        company_form = name_split[0].lower()
        name_short = ''.join(name_split[1:])
        self.final_name = f'{company_form}«{name_short}» '
        return self.final_name

    def get_final_numbers(self) -> str:
        """
        Так же методом join() пробразуем tuple в строку.
        Иначе информация выводится в квадратных скобках.
        """
        self.final_numbers = '(ОГРН ' + ''.join(self.ogrn) + ', ' \
                             + 'ИНН ' + ''.join(self.inn) + ', ' \
                             + 'КПП ' + ''.join(self.kpp) + ')' + '\n' + '\n'
        return ''.join(self.final_numbers)

    def get_final_address(self) -> str:
        """
        В адресе нужно поменять следующее:
            1) индекс переместить в конец,
            2) добавить страну,
            3) город поставить перед страной,
            4) слова "город", "улица" и тп сделать
            строчными буквами,
            5) имена улиц - с прописных букв.

        По п. 4 пока не нашел лучшего варианта:
        просто перечисляю слова "Улица", "Набережная",
        "Проспект" и тп. Потом выхватываю их из строк
        и меняю на вариант написания со строчной буквы.

        Плюс пока не дошли руки до изменения слов "Дом",
        "Корпус", "Офис" и тп. Тут проблема в том, что эти
        слова могут быть в адресе одновременно. Соответсвенно,
        менять их через обычное ветвление не получается.
        """
        split_string = self.address.split(', ')
        index = split_string[0]
        pre_city = split_string[1].title()
        city = pre_city.replace('Город', 'город')
        pre_address = " ".join(split_string[2:]).title()
        if 'Улица' in pre_address:
            pre_final_address = pre_address.replace('Улица', ' ')
            self.final_address = f'Адрес: улица {pre_final_address}, ' \
                                 f'{city}, Россия, {index}'
        elif 'Набережная' in pre_address:
            pre_final_address = pre_address.replace('Набережная', 'набережная')
            self.final_address = f'Адрес: {pre_final_address}, ' \
                                 f'{city}, Россия, {index}'
        elif 'Переулок' in pre_address:
            pre_final_address = pre_address.replace('Переулок', 'переулок')
            self.final_address = f'Адрес: {pre_final_address}, ' \
                                 f'{city}, Россия, {index}'
        else:
            self.final_address = f'Адрес:{pre_address}, ' \
                                 f'{city}, Россия, {index}'

        return self.final_address


class ReceivedMessage:
    """
    Класс сообщений, полученных от пользователя.
    Сейчас сделал только под ИНН. Поэтому в родительском
    классе пока pass.
    """
    pass


class ReceivedInn(ReceivedMessage):
    """Класс сообщений с номерами ИНН, полученных от пользователя"""
    def __init__(self,
                 text: str
                 ) -> None:
        self.text = text

    """
    Собственно, метод запроса данных с сайта ФНС.
    Возвращает объект класса InputData
    """
    def request_data(self) -> InputData:
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


    """
    Далее сам метод ответа на введенное сообщение
    пользователя. Пока ветвление в таком примитивном виде.
    Еще не разобрался, как определить, что ИНН введен с ошибкой.
    Пока программа реагирует только если введены данные
    длиной более или менее, чем 10 символов.
    
    Если пользователь присылает корректный ИНН, программа выполняет
    следующие функции:
        1) request_data() - делает запрос на сайт ФНС,
        2) get_final_name() - редактирует наименование,
        3) get_final_numbers() - редактирует ОГРН, ИНН и КПП,
        4) get_final_address() - редактирует адрес,
    После этого полученные данные объединяются в итоговое
    сообщение, которое и отправляется в чат.
    """
@bot.message_handler(func=lambda message: True)
def echo_message(message) -> None:
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
        bot.send_message(message.from_user.id, "Нужно ввести именно ИНН")


bot.polling()
