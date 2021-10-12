# -*- coding: utf-8 -*-
from selenium.webdriver import Chrome,ChromeOptions
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC 
import time 
import re
import pandas as pd


# driverのオプション設定
def getInfoFromUnipa(UserID:str,PassWord:str):
   options = ChromeOptions()
   driver_path = './chromedriver'
   options.headless = True
   # ポップアップメッセージを削除するため
   options.add_experimental_option('excludeSwitches', ['enable-logging'])
   # chromedriverを作成
   driver = Chrome(options=options, executable_path=driver_path)
   # unipaのURL
   URL = "https://unipa.u-hyogo.ac.jp/uprx/"
   driver.get(URL)
   WebDriverWait(driver, 15).until(EC.presence_of_all_elements_located((By.XPATH,'//*[@id="loginForm:userId"]')))

   # UserIDやPasswordの入力及び送信
   input_element_key1 = driver.find_element_by_xpath('//*[@id="loginForm:userId"]')
   input_element_key2 = driver.find_element_by_xpath('//*[@id="loginForm:password"]')
   botton = driver.find_element_by_xpath('//*[@id="loginForm:loginButton"]')
   input_element_key1.send_keys(UserID)
   input_element_key2.send_keys(PassWord)
   botton.send_keys(Keys.RETURN)
   time.sleep(1)

   # 曜日を取得
   week = driver.find_element_by_class_name('dateDisp').text
   week = re.search(r'\((.+)\)', week).group(1)

   # クラスプロファイルを探索しに行く
   WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR,".infoIcon.infoClassprofile"))).click()

   # 課題提出状況を確認する
   elements = driver.find_elements_by_css_selector(".ui-button-text.ui-c")
   # もっとスマートな方法があれば...
   # 課題提出のところを変えればほかのところにもいけるのでこのままでいいかも
   for element in elements:
      if element.text == '課題提出':
            element.click()
            break
   # 前の授業へのボタンを押す
   while True:
      if driver.find_elements_by_css_selector('.ui-button-icon-left.ui-icon.ui-c.fa.fa-fw.fa-caret-left') == []:
         break
      time.sleep(0.5)
      WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR,".ui-button-icon-left.ui-icon.ui-c.fa.fa-fw.fa-caret-left"))).click()

   # それぞれの講義の課題情報を格納する
   dfs = []

   # 次の授業が押せなくなったら終了
   while True:
      time.sleep(1)
      # 講義名を取得する
      lecture = driver.find_element_by_class_name('cpTgtName').text
      lecture = re.search(r'[0-9]+(.+) ((.+))', lecture).group(1)
      # 何の科目か知りたい場合
      # subject = re.search(r'[0-9]+(.+) ((.+))', lecture).group(2)

      # 2ページ以上の可能性があるので考慮する必要がある
      i = 1
      df_list = []
      while True:
         # 選択した講義の課題が残っているのかを調べるためにデータフレームにする
         time.sleep(1)
         table = driver.find_element_by_css_selector("#funcForm\:gakKdiTstList > div.ui-datatable-tablewrapper > table")
         html = table.get_attribute('outerHTML')
         df_table = pd.read_html(html)
         df_list.append(df_table[0])
         try:
               driver.find_element_by_xpath(f'//*[@id="funcForm:gakKdiTstList_paginator_bottom"]/span[4]/span[{i}]').click()
               i += 1
         except:
               break
      # データフレームから必要な情報を取得する
      if len(df_list) >= 2:
         df = pd.concat(df_list)
         df['講義名']=lecture
      elif len(df_list) == 1:
         df = df_list[0]
         df['講義名']=lecture
      else:
         df = pd.DataFrame(columns = ['課題グループ名', '課題名', '種別', '承認状態', 'コース', '目次', '課題提出開始日時', '課題提出終了日時',
       '提出方法', 'ステータス', '未提出', '提出回数', '再提出回数', '再提出期限', '提出日時', '点数', '未確認',
       'Good', 'No good', '他の提出者', '講義名'], index=[0])
         df['講義名']=lecture
      dfs.append(df)
    
      #　次の授業があるかを判定
      if driver.find_elements_by_css_selector('.ui-button-icon-left.ui-icon.ui-c.fa.fa-fw.fa-caret-right') == []:
         break
      # 次の授業を押す
      driver.find_element_by_css_selector('.ui-button-icon-left.ui-icon.ui-c.fa.fa-fw.fa-caret-right').click()
   
   df_all = pd.concat(dfs)
   df_all = df_all[~df_all.duplicated()]
   df_all = df_all.reset_index(drop=True)
   # ブラウザを終了する
   driver.quit()
   return df_all

def check_login(userID:str,PassWord:str)->bool:
   try:
      options = ChromeOptions()
      # chromedriverを作成
      options.headless = True
      driver = Chrome(options=options)
      URL = "https://unipa.u-hyogo.ac.jp/uprx/"
      driver.get(URL)
      WebDriverWait(driver, 15).until(EC.presence_of_all_elements_located((By.XPATH,'//*[@id="loginForm:userId"]')))

      # UserIDやPasswordの入力及び送信
      input_element_key1 = driver.find_element_by_xpath('//*[@id="loginForm:userId"]')
      input_element_key2 = driver.find_element_by_xpath('//*[@id="loginForm:password"]')
      botton = driver.find_element_by_xpath('//*[@id="loginForm:loginButton"]')
      input_element_key1.send_keys(userID)
      input_element_key2.send_keys(PassWord)
      botton.send_keys(Keys.RETURN)
      time.sleep(2)
      # クラスプロファイルを探索しに行く
      driver.find_element_by_xpath('//*[@id="funcForm:j_idt361:j_idt518:j_idt524"]/p').click()
      return True
   except:
      return False
   
   



