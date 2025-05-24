
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import random

st.set_page_config(page_title="排班神器", layout="centered")

st.title("🧾 排班神器 by 小雀")

st.markdown("請先選擇排班區間，輸入員工名單與預排休假，再點擊下方按鈕生成班表。")

# 日期範圍選擇
start_date = st.date_input("開始日期", datetime.today())
end_date = st.date_input("結束日期", start_date + timedelta(days=27))

if end_date <= start_date:
    st.warning("⚠️ 結束日期必須晚於開始日期")
    st.stop()

# 輸入員工名單
raw_names = st.text_area("輸入正職員工名單（用逗號分隔）", "Mark,博堯,Ten,Sam,Eason,Ssumday,Flora,Luna,阿邱,Bendy,阿凱,Adam")
employees = [name.strip() for name in raw_names.split(",") if name.strip()]

# 預排休假輸入
st.markdown("### 員工預排休假")
vacations = {}
for name in employees:
    dates = st.multiselect(f"{name} 的休假日", pd.date_range(start_date, end_date), key=f"vac_{name}")
    vacations[name] = set(dates)

# 排班按鈕
if st.button("生成排班表！"):
    date_range = pd.date_range(start_date, end_date)
    schedule = {}

    for name in employees:
        schedule[name] = []
        # 每週排班邏輯
        weeks = [date_range[i:i + 7] for i in range(0, len(date_range), 7)]
        week_for_overtime = random.choice(range(len(weeks)))

        for i, week in enumerate(weeks):
            days = list(week)
            non_vac = [d for d in days if d not in vacations[name]]
            if len(non_vac) >= 2:
                rest = random.sample(non_vac, 2)
                for d in days:
                    if d in vacations[name]:
                        schedule[name].append("休")
                    elif i == week_for_overtime and d == rest[0]:
                        schedule[name].append("加")
                    elif d == rest[1]:
                        schedule[name].append("例休")
                    else:
                        schedule[name].append("")
            else:
                schedule[name].extend(["休" if d in vacations[name] else "" for d in days])

    df = pd.DataFrame(schedule, index=date_range).T

    # 人力統計
    daily_counts = (df != "休") & (df != "例休") & (df != "加")
    count_series = daily_counts.sum(axis=1)
    count_df = pd.DataFrame({"上班人數": count_series})
    count_df.index.name = "日期"

    # 美化樣式
    def highlight_shifts(val):
        color = ""
        if val == "休":
            color = "#a3d2ff"
        elif val == "例休":
            color = "#dddddd"
        elif val == "加":
            color = "#ffa3a3"
        return f"background-color: {color}"

    st.success("✅ 排班完成！以下是排班結果（含休假標示與人力統計）")
    st.dataframe(df.style.applymap(highlight_shifts))

    st.markdown("### 每日上班人數統計")
    st.dataframe(count_df)

    csv = df.to_csv().encode('utf-8-sig')
    st.download_button("下載班表（CSV）", data=csv, file_name="排班表.csv", mime="text/csv")
