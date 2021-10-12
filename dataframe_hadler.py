import datetime
import pandas as pd
from datetime import timedelta
import time

# 締め切りが近い課題を文字列として返す
def make_deadline_str(df):
    df["deadline"]=df['課題提出終了日時'].replace({r'\(.\)': '', "対象データがありません。": "2250/07/08 14:25"}, regex=True)
    df['deadline']=pd.to_datetime(df['deadline'], format="%Y/%m/%d %H:%M")
    today = datetime.datetime.fromtimestamp(time.time())
    df_deadline = df[(df["課題名"]!="対象データがありません。") & ((df['deadline']-timedelta(days=3))<today.strftime('%Y/%m/%d %H:%M')) & (df['deadline']>today.strftime('%Y/%m/%d %H:%M'))]
    deadline_homework=["締め切りが近い課題は"]
    for work_name in df_deadline['講義名'].unique():
        deadline_homework.append(f"===={work_name}====")
        for _, v in df_deadline[df_deadline['講義名']==work_name].iterrows():
            deadline_homework.append("課題名：" + v["課題名"])
            deadline_homework.append("締切日：" + v["課題提出終了日時"])
            deadline_homework.append("ステータス：" + v["ステータス"])
            deadline_homework.append(']')
    deadline_homework = "\n".join(deadline_homework)
    return deadline_homework

# 提出していない課題を文字列として返す
def make_not_submmit_str(df):
    df_submit=df[(df["課題名"]!="対象データがありません。")&(df["未提出"]=="○")&(df['ステータス']!='受付終了')]
    not_submit_homework=["未提出の課題は"]
    for work_name in df_submit['講義名'].unique():
        not_submit_homework.append(f"===={work_name}====")
        for _, v in df_submit[df_submit['講義名']==work_name].iterrows():
            not_submit_homework.append("課題名：" + v["課題名"])
            not_submit_homework.append("締切日：" + v["課題提出終了日時"])
            not_submit_homework.append("ステータス：" + v["ステータス"])
            not_submit_homework.append(']')
    not_submit_homework = "\n".join(not_submit_homework)
    return not_submit_homework

# 出し忘れた課題を文字列として返す
def make_forget_homework_str(df):
    df_rest=df[(df["課題名"]!="対象データがありません。")&(df["未提出"]=="○")&(df['ステータス']=='受付終了')]
    rest_homework=["出し忘れた課題は"]
    for work_name in df_rest['講義名'].unique():
        rest_homework.append(f"===={work_name}====")
        for _, v in df_rest[df_rest['講義名']==work_name].iterrows():
            rest_homework.append("課題名：" + v["課題名"])
            rest_homework.append("締切日：" + v["課題提出終了日時"])
            rest_homework.append("ステータス：" + v["ステータス"])
            rest_homework.append(']')
    rest_homework = "\n".join(rest_homework)
    return rest_homework

