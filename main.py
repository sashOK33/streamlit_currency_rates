import streamlit as st
import requests as r
from bs4 import BeautifulSoup
import re
from datetime import datetime, date
import pandas as pd
from prophet import Prophet

# Настройка заголовка и текста
st.title("Прогноз на заданный интервал курса рубля")
st.write("""Чуть ниже график. А слева боковая панель настроек""")

# Настройка боковой панели
st.sidebar.title("Настройки")
st.sidebar.info(
    """
    Тут бы мог быть ваша реклама
    """
)
st.sidebar.info("Рекламы нет. Но зато есть "
                "[ссылка на мем с дракончиком](https://www.youtube.com/watch?v=K4K3wn9k7vk).")


def get_currency_dictionary():
    response = r.get('''
        https://cbr.ru/currency_base/dynamics/?UniDbQuery.Posted=True&UniDbQuery.so=1&UniDbQuery.mode=1&UniDbQuery.date_req1=&UniDbQuery.date_req2=&UniDbQuery.VAL_NM_RQ=R01010&UniDbQuery.From=01.01.2019&UniDbQuery.To=30.12.2023''')
    # print(response.text)
    soup = BeautifulSoup(response.text, "html.parser")
    currency_list = soup.find_all(class_='select')
    currency_list = str(currency_list).replace('  ', '').replace('selected="" ', '')
    currency_list = currency_list.split('<option value="')[1:]
    currency_dictionary = {}
    for item in currency_list:
        code, currency_name, *other = item.split('\r\n')
        currency_dictionary.update({currency_name: code[:-2]})
    return currency_dictionary


currency_dictionary = get_currency_dictionary()


def get_df_from_site(start_date, end_date, currency):
    response = r.get(f'''https://cbr.ru/currency_base/dynamics/?UniDbQuery.Posted=True&UniDbQuery.so=1&UniDbQuery.mode=1&UniDbQuery.date_req1=&UniDbQuery.date_req2=&UniDbQuery.VAL_NM_RQ={currency_dictionary[currency]}&UniDbQuery.From={start_date}&UniDbQuery.To={end_date}''')
    # print(response.text)
    currency_data = {}
    soup = BeautifulSoup(response.text, "html.parser")
    data = soup.find_all('td')
    for d in data:
        if re.fullmatch(r'\d\d\.\d\d\.\d\d\d\d', d.text):
            date = datetime.strptime(d.text, '%d.%m.%Y')
        elif re.fullmatch(r'\d\d\,\d\d\d\d', d.text):
            currency_data.update({date: float(d.text.replace(',', '.'))})
    # pprint(currency_data)

    s = pd.Series(currency_data, name='DateValue')
    df = s.reset_index()
    df.columns = ['ds', 'y']
    return df


def get_prophet_plot(currency, start_date, end_date, period, period_type):
    df = get_df_from_site(start_date, end_date, currency)
    model = Prophet()
    model.fit(df)
    future = model.make_future_dataframe(periods=period, freq=period_type)
    forecast = model.predict(future)
    plot = model.plot(forecast, xlabel='Время', ylabel='Руб')
    # plot = model.plot_components(forecast)
    return plot


col1, col2 = st.columns(2)
with st.sidebar.form(key="Form1"):
    currency = st.selectbox('Выберите валюту', list(currency_dictionary.keys()),
                                    key='currency', index=list(currency_dictionary.keys()).index('Доллар США'))
    start_date = st.date_input("Начальная дата", date(2023, 1, 1), key='start_date')
    end_date = st.date_input("Конечная дата", date(2024, 6, 14), key='end_date')
    c1, c2 = st.columns(2)
    with c1:
        period = st.number_input("Период для построение", value=14, placeholder="Type a period...")
    with c2:
        period_type = st.selectbox('Разрешение периода', ['h', 'd', 'm', 'y'], key='period_type', index=1)
    st.form_submit_button('Построить', use_container_width=True)

st.plotly_chart(get_prophet_plot(currency, start_date.strftime('%d.%m.%Y'), end_date.strftime('%d.%m.%Y'), period, period_type),
                    use_container_width=True)
