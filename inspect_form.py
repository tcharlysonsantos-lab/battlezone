import requests
from bs4 import BeautifulSoup

session = requests.Session()
r = session.get('http://192.168.0.100:5000/auth/login')
soup = BeautifulSoup(r.text, 'html.parser')

print('Campos do formulário encontrados:')
form = soup.find('form')
if form:
    for input_field in form.find_all('input'):
        name = input_field.get('name', 'SEM NOME')
        type_ = input_field.get('type', 'text')
        value = input_field.get('value', '')[:30] if input_field.get('value') else ''
        print(f'  - name="{name}" type="{type_}" value="{value}..."')
else:
    print("Nenhum formulário encontrado!")
