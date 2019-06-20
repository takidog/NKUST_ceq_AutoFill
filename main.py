import datetime
import sys
import time

import requests
from bs4 import BeautifulSoup


class ceqSystem:
    def __init__(self, account, password):
        self.main_session = requests.session()

        self.course_data = []
        self.login_status = False
        self.csrf_key = ""

        self.main_session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7,ja;q=0.6'
        })

        if self.init_base_cookie():
            self.log('base cookie get.')
        else:
            self.log('hmm something error ?')

        if self.login(account=account, password=password):
            self.login_status = True
            self.log('Login success!')
        else:
            self.log('Login fail QQ')
            sys.exit()

    def init_base_cookie(self):
        """get base cooke and csrf token

        Returns:
            [bool]
        """
        url = 'https://ceq.nkust.edu.tw/'
        try:
            res = self.main_session.get(url=url)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, 'html.parser')

                self.csrf_key = soup.find(
                    'input', {'name': '__RequestVerificationToken'}).get('value')
                if self.csrf_key != "":
                    return True
        except:
            return False
        return False

    def login(self, account, password):
        """[login Ceq system ]
        Args:
            account ([type:string]): webap system account .
            password ([type:string]): webap system password.
        """
        url = 'https://ceq.nkust.edu.tw/Login'

        data = {
            '__RequestVerificationToken': self.csrf_key,
            'UserAccount': account,
            'Password': password,
        }
        res = self.main_session.post(url=url, data=data, allow_redirects=False)
        if res.status_code == 302:
            soup = BeautifulSoup(res.text, 'html.parser')
            status = soup.find('a')['href']
            if status == '/StuFillIn':
                return True
        return False

    def course_parser(self):
        url = 'https://ceq.nkust.edu.tw/StuFillIn'
        html = self.main_session.get(url=url).text
        soup = BeautifulSoup(html, 'html.parser')

        for cource in soup.find('tbody').find_all('tr'):
            td_data = cource.find_all('td')

            cource_data_cell = {
                'name': td_data[0].text,
                'teacher': td_data[1].text,
                'status': (td_data[2].text.find('未填') < 0),
                'url': ''
            }
            if cource_data_cell['status'] == False:
                cource_data_cell.update({'url': td_data[3].find('a')['href']})

            self.course_data.append(cource_data_cell)

    def fill_all(self, course_data):
        base_url = 'https://ceq.nkust.edu.tw'
        for course_cell in course_data:
            if course_cell['status'] == False:
                core.log("開始填寫 : %s" % course_cell['name'])

                html = self.main_session.get(base_url+course_cell['url']).text
                soup = BeautifulSoup(html, 'html.parser')
                input_data = soup.find_all('input')
                question_list = []
                for i in input_data[1:-1]:
                    question_list.append(i['name'])
                textarea_data = soup.find_all('textarea')
                for i in textarea_data:
                    question_list.append(i['name'])
                question_list = list(set(question_list))
                question_list.sort()
                csrf_value = input_data[0].get('value')
                hidden_value = input_data[-1].get('value')

                Answer_list = [1, 1, 1, 1, 1, 1, 5, 5, 1, 1, 5,
                               5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, '', '', '']

                answer_url = 'https://ceq.nkust.edu.tw/StuFillIn/Insert'
                data = dict(zip(question_list, Answer_list))
                data.update({
                    '__RequestVerificationToken': csrf_value,
                    'Hidden1': hidden_value
                })

                res = self.main_session.post(
                    url=answer_url, data=data, allow_redirects=False)
                if res.status_code == 302:
                    soup = BeautifulSoup(res.text, 'html.parser')
                    status = soup.find('a')['href']
                    if status == '/StuFillIn':
                        core.log('%s 填寫成功' % course_cell['name'])

    def log(self, text):
        print("[ %s ] : " % datetime.datetime.now().isoformat(), text)


if __name__ == "__main__":
    account = input('帳號 : ')
    password = input('密碼 : ')
    core = ceqSystem(account=account, password=password)
    core.course_parser()
    for i in core.course_data:
        core.log("課程: %s  狀態: %s" % (i['name'], i['status']))

    if input('全部填寫 ? (y/n) ') == 'y':
        core.fill_all(core.course_data)
