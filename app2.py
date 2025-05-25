
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import random

st.set_page_config(page_title="排班神器", layout="centered")

st.title("🧾 排班神器 by 小雀")

# 日期選擇
start_date = st.date_input("開始日期", datetime(2025, 6, 9))
end_date = st.date_input("結束日期", datetime(2025, 7, 6))

if end_date <= start_date:
    st.warning("結束日期需晚於開始日期")
    st.stop()

# 員工名單
raw_fulltime = st.text_area("正職員工名單（逗號分隔）", "Mark,博堯,Ten,Sam,Eason,Ssumday,Flora,Luna,阿邱,Bendy,阿凱,Adam")
raw_pt = st.text_area("PT 員工名單（逗號分隔）", "Hunter,Rosi,喻,隱搞,Murray,偉哥,Ruru")

fulltime_employees = [e.strip() for e in raw_fulltime.split(",") if e.strip()]
pt_employees = [e.strip() for e in raw_pt.split(",") if e.strip()]

# 職能設定
supervisors = {"Mark", "博堯", "Ten", "Sam", "Eason"}
front_desk = {"Mark", "Flora", "Sam", "Eason", "Luna"}
kitchen = {"博堯", "Ten", "Hunter", "Murray"}
kitchen_back = {"Ssumday", "阿邱", "Bendy", "隱搞"}

# 初始化休假輸入
st.markdown("### 正職員工預排休假")
vacations = {}
for name in fulltime_employees:
    vac_days = st.multiselect(f"{name} 的休假日", pd.date_range(start_date, end_date), key=f"vac_{name}")
    vacations[name] = set(vac_days)

if st.button("生成排班表！"):
    dates = pd.date_range(start_date, end_date)
    final_assignment = pd.DataFrame(index=fulltime_employees + pt_employees, columns=dates)
    final_assignment[:] = ""

    # 建立每位正職的可出勤表
    availability = {}
    for name in fulltime_employees:
        work_streak = 0
        rest_count = 0
        used_add = False
        available = []

        for i, day in enumerate(dates):
            if day in vacations[name]:
                available.append(False)
                work_streak = 0
            elif (i // 7) * 2 > rest_count:
                available.append(False)
                rest_count += 1
                work_streak = 0
            elif not used_add and i > 21:
                available.append(True)
                used_add = True
                work_streak += 1
            elif work_streak >= 6:
                available.append(False)
                rest_count += 1
                work_streak = 0
            else:
                available.append(True)
                work_streak += 1
        availability[name] = available

    # 開始每日排班
    for i, day in enumerate(dates):
        today_needed = 5
        available_today = [name for name in fulltime_employees if availability[name][i]]

        selected = set()
        # 職能優先
        sups = [n for n in available_today if n in supervisors and n not in selected]
        if sups: selected.add(random.choice(sups))
        fds = [n for n in available_today if n in front_desk and n not in selected]
        if fds: selected.add(random.choice(fds))
        kts = [n for n in available_today if n in kitchen and n not in selected]
        if kts: selected.add(random.choice(kts))
        kbs = [n for n in available_today if n in kitchen_back and n not in selected]
        if kbs: selected.add(random.choice(kbs))

        others = [n for n in available_today if n not in selected]
        remaining = today_needed - len(selected)
        if remaining > 0:
            if len(others) >= remaining:
                selected.update(random.sample(others, remaining))
            else:
                selected.update(others)

        # 補 PT
        if len(selected) < today_needed:
            pt_add = today_needed - len(selected)
            selected.update(random.sample(pt_employees, min(pt_add, len(pt_employees))))

        for name in selected:
            final_assignment.at[name, day] = "班"

    # 標註休假狀態
    display_df = final_assignment.copy()
    for name in fulltime_employees:
        work_streak = 0
        used_add = False
        updated = []
        for i, day in enumerate(dates):
            if final_assignment.at[name, day] == "班":
                updated.append("")
                work_streak += 1
            elif not used_add and i > 21:
                updated.append("加")
                used_add = True
                work_streak = 0
            elif work_streak >= 6:
                updated.append("例休")
                work_streak = 0
            elif day in vacations[name]:
                updated.append("休")
                work_streak = 0
            else:
                updated.append("休")
                work_streak = 0
        display_df.loc[name] = updated

    st.success("✅ 完成排班，以下為最終表：")
    st.dataframe(display_df)

    csv = display_df.to_csv().encode('utf-8-sig')
    st.download_button("下載班表 CSV", csv, "最終排班表.csv", "text/csv")
