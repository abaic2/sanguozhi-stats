# -*- coding: utf-8 -*-
"""《三国志》全文统计看板 · Streamlit 版
数据：stats.json —— 由 analyze.js 对陈寿《三国志》白文六十五卷全文精确统计生成
"""
import json
from pathlib import Path

import pandas as pd
import streamlit as st
from streamlit_echarts import st_echarts

st.set_page_config(page_title="三国志 · 统计志林", page_icon="⚔", layout="wide")

S = json.loads((Path(__file__).parent / "stats.json").read_text(encoding="utf-8"))
FMT = lambda n: f"{n:,}"
BOOK_COLOR = {"魏": "#3b6b9b", "蜀": "#3e8e4d", "吴": "#b03a2e"}
PALETTE = ["#8c2f23", "#3b6b9b", "#3e8e4d", "#a67c00", "#6b5f4e", "#7a4b8f"]

st.markdown(
    "<h1 style='text-align:letter-spacing:8px'>三 国 志 <span style='font-size:.5em;color:#8c2f23'>统 计 志 林</span></h1>"
    "<p style='text-align:center;color:#6b5f4e'>陈寿 撰 · 六十五卷 · 全文语料精确统计 · 365,797 汉字</p>",
    unsafe_allow_html=True,
)

AXIS = {"axisLine": {"lineStyle": {"color": "#6b5f4e"}}, "splitLine": {"lineStyle": {"color": "#e7ddc8"}}}


def hbar(pairs, color="#a67c00", height=420, fontsize=12):
    return {
        "backgroundColor": "transparent",
        "tooltip": {"trigger": "axis"},
        "grid": {"left": 90, "right": 70, "top": 10, "bottom": 30},
        "xAxis": {"type": "value", **AXIS},
        "yAxis": {"type": "category", "inverse": True,
                  "data": [p[0] for p in pairs],
                  "axisLabel": {"fontSize": fontsize}},
        "series": [{"type": "bar", "data": [p[1] for p in pairs], "barWidth": 12,
                    "label": {"show": True, "position": "right"},
                    "itemStyle": {"color": color, "borderRadius": [0, 6, 6, 0]}}],
    }


TABS = ["壹 · 全书概览", "贰 · 字词频率", "叁 · 人物与传记"]
page = st.radio("章节", TABS, horizontal=True, label_visibility="collapsed")

# ============ 壹 概览 ============
if page == TABS[0]:
    m = S["meta"]
    c = st.columns(6)
    c[0].metric("汉字总数", FMT(m["totalChars"]), help="全文精确计数（不含标点）")
    c[1].metric("不同单字", FMT(m["uniqChars"]), help="字种数")
    c[2].metric("仅出现一次", FMT(m["hapax"]), help="生僻字/专名用字")
    c[3].metric("总卷数", "65", help="魏30 · 蜀15 · 吴20")
    c[4].metric("句子总数", FMT(m["sentCount"]), help="按句读切分")
    c[5].metric("平均句长", m["avgSent"], help="字 / 句")

    left, right = st.columns([1, 2])
    with left:
        st.subheader("卷帙结构")
        st_echarts({
            "backgroundColor": "transparent",
            "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
            "legend": {"bottom": 0},
            "grid": {"left": 50, "right": 20, "top": 30, "bottom": 50},
            "xAxis": {"type": "category", "data": ["魏书", "蜀书", "吴书"], **AXIS},
            "yAxis": {"type": "value", "name": "卷", **AXIS},
            "series": [
                {"name": "纪 / 帝传", "type": "bar", "stack": "t", "barWidth": 50,
                 "data": [4, 3, 2], "itemStyle": {"color": "#8c2f23"}, "label": {"show": True, "color": "#fff"}},
                {"name": "列传", "type": "bar", "stack": "t",
                 "data": [25, 12, 17], "itemStyle": {"color": "#a67c00"}, "label": {"show": True, "color": "#fff"}},
                {"name": "族传/外传", "type": "bar", "stack": "t",
                 "data": [1, 0, 1], "itemStyle": {"color": "#6b5f4e"}, "label": {"show": True, "color": "#fff"}},
            ],
        }, height="360px")
    with right:
        st.subheader("卷幅分布（逐卷精确字数）")
        pl = S["pianLens"]
        pl_js = json.dumps([{"j": p["juan"], "t": p["title"], "l": p["len"]} for p in pl], ensure_ascii=False)
        st_echarts({
            "backgroundColor": "transparent",
            "tooltip": {"trigger": "axis", "formatter":
                        "function(p){var d=" + pl_js + "[p[0].dataIndex];return '卷'+d.j+'《'+d.t+'》<br>'+d.l.toLocaleString()+' 字';}"},
            "grid": {"left": 60, "right": 20, "top": 30, "bottom": 40},
            "xAxis": {"type": "category", "data": [p["juan"] for p in pl], "name": "卷次", **AXIS},
            "yAxis": {"type": "value", "name": "字数", **AXIS},
            "series": [{"type": "bar", "barWidth": "70%",
                        "data": [{"value": p["len"], "itemStyle": {"color": BOOK_COLOR[p["book"]]}} for p in pl]}],
        }, height="360px")

# ============ 贰 字词 ============
if page == TABS[1]:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("单字频率 Top 30")
        st_echarts(hbar(S["topChars"], color="#8c2f23", height=640, fontsize=15), height="660px")
    with c2:
        st.subheader("词云（高频字 + 多字词）")
        cloud = ([{"name": k, "value": v} for k, v in S["topChars"][:50]]
                 + [{"name": k, "value": v} for k, v in S["termCounts"] if len(k) > 1][:40])
        st_echarts({
            "backgroundColor": "transparent",
            "tooltip": {"show": True, "formatter": "{b}：{c} 次"},
            "series": [{"type": "wordCloud", "gridSize": 12, "sizeRange": [12, 76],
                        "shape": "circle", "width": "94%", "height": "94%",
                        "textStyle": {"fontFamily": "serif", "fontWeight": "bold",
                                      "color": "function(){return ['#8c2f23','#3b6b9b','#3e8e4d','#a67c00','#6b5f4e','#7a4b8f'][Math.floor(Math.random()*6)]}"},
                        "data": cloud}],
        }, height="660px")

    c3, c4 = st.columns(2)
    with c3:
        st.subheader("多字词语 Top 20")
        terms2 = [t for t in S["termCounts"] if len(t[0]) > 1][:20]
        st_echarts(hbar(terms2, color="#a67c00", height=460), height="480px")
    with c4:
        st.subheader("魏蜀吴高频字对比")
        st_echarts({
            "backgroundColor": "transparent",
            "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
            "legend": {"bottom": 0},
            "grid": {"left": 50, "right": 20, "top": 30, "bottom": 50},
            "xAxis": {"type": "category", "data": S["cmpChars"], "axisLabel": {"fontSize": 16}},
            "yAxis": {"type": "value", **AXIS},
            "series": [{"name": s["book"] + "书", "type": "bar", "data": s["data"],
                        "itemStyle": {"color": BOOK_COLOR[s["book"]]}} for s in S["cmpSeries"]],
        }, height="480px")

    c5, c6 = st.columns(2)
    with c5:
        st.subheader("国号与正统用字")
        st_echarts({
            "backgroundColor": "transparent",
            "tooltip": {"trigger": "axis"},
            "grid": {"left": 50, "right": 20, "top": 30, "bottom": 30},
            "xAxis": {"type": "category", "data": [g[0] for g in S["GUOHao"]], **AXIS},
            "yAxis": {"type": "value", **AXIS},
            "series": [{"type": "bar", "barWidth": 36, "label": {"show": True, "position": "top"},
                        "data": [{"value": g[1], "itemStyle": {"color": BOOK_COLOR.get(g[0], "#6b5f4e")}}
                                 for g in S["GUOHao"]]}],
        }, height="360px")
    with c6:
        st.subheader("句长分布")
        st_echarts({
            "backgroundColor": "transparent",
            "tooltip": {"trigger": "axis"},
            "grid": {"left": 55, "right": 20, "top": 30, "bottom": 30},
            "xAxis": {"type": "category", "data": [f"{b[0]} 字" for b in S["sentHist"]], **AXIS},
            "yAxis": {"type": "value", "name": "句数", **AXIS},
            "series": [{"type": "bar", "barWidth": "60%", "data": [b[1] for b in S["sentHist"]],
                        "itemStyle": {"color": "#8c2f23", "borderRadius": [6, 6, 0, 0]},
                        "label": {"show": True, "position": "top", "fontSize": 11}}],
        }, height="360px")

    st.subheader("逐卷下钻 · 各卷自己的高频字")
    titles = [f"卷{p['juan']}《{p['title']}》（{FMT(p['len'])}字）" for p in S["pianLens"]]
    i = st.selectbox("选择卷次", range(len(titles)), format_func=lambda x: titles[x], label_visibility="collapsed")
    p = S["pianLens"][i]
    st_echarts(hbar(p["top"], color=BOOK_COLOR[p["book"]], height=440, fontsize=15), height="460px")

# ============ 叁 人物 ============
if page == TABS[2]:
    st.subheader("人名出现统计（姓名 / 字 / 庙号·尊称 别名堆叠，精确子串计数）")
    rows = sorted(
        [{"name": n, "total": sum(d[1] for d in det), "detail": det} for n, det in S["nameCounts"]],
        key=lambda r: -r["total"])
    maxseg = max(len(r["detail"]) for r in rows)
    colors = ["#8c2f23", "#3b6b9b", "#a67c00", "#3e8e4d", "#7a4b8f"]
    series = []
    for seg in range(maxseg):
        series.append({
            "name": "姓名" if seg == 0 else "别称",
            "type": "bar", "stack": "n", "barWidth": 15,
            "itemStyle": {"color": colors[seg % len(colors)]},
            "label": {"show": False},
            "data": [r["detail"][seg][1] if seg < len(r["detail"]) else 0 for r in rows],
        })
    st_echarts({
        "backgroundColor": "transparent",
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}, "formatter":
                    "function(p){var d=" + json.dumps(
                        [{"n": r["name"], "t": r["total"], "x": r["detail"]} for r in rows], ensure_ascii=False)
                    + "[p[0].dataIndex];return '<b>'+d.n+'</b>（合计 '+d.t+'）<br>'+d.x.map(function(a){return a[0]+'：'+a[1];}).join('<br>');}"},
        "legend": {"bottom": 0},
        "grid": {"left": 80, "right": 80, "top": 10, "bottom": 50},
        "xAxis": {"type": "value", **AXIS},
        "yAxis": {"type": "category", "inverse": True, "data": [r["name"] for r in rows], **AXIS},
        "series": series,
    }, height="560px")
    st.caption("注：单字别称（如「权」「亮」「备」）为全文子串口径，含同字非人名用例，仅供参考；悬停可见各变体明细。")

    c7, c8 = st.columns([1, 1])
    with c7:
        st.subheader("立传人物类型（样本归类）")
        st_echarts({
            "backgroundColor": "transparent",
            "tooltip": {"trigger": "item", "formatter": "{b}：{c} 人（{d}%）"},
            "legend": {"bottom": 0},
            "color": PALETTE,
            "series": [{"type": "pie", "radius": ["28%", "62%"], "center": ["50%", "45%"],
                        "roseType": "radius", "itemStyle": {"borderColor": "#fff", "borderWidth": 2},
                        "label": {"formatter": "{b}\n{d}%"},
                        "data": [{"name": "武将", "value": 38}, {"name": "谋臣·政务", "value": 30},
                                 {"name": "君主·宗室", "value": 16}, {"name": "文士·儒林", "value": 9},
                                 {"name": "后妃·外戚", "value": 4}, {"name": "方术·他传", "value": 3}]}],
        }, height="400px")
    with c8:
        st.subheader("大事年表 184 — 280")
        tl = [(184, "黄巾之乱爆发"), (190, "关东联军讨董卓"), (200, "官渡之战"), (208, "赤壁之战"),
              (214, "刘备取益州"), (219, "关羽襄樊 / 孙权袭荆州"), (220, "曹丕代汉"), (221, "刘备称帝"),
              (222, "夷陵之战"), (223, "白帝托孤"), (227, "出师表"), (234, "星落五丈原"),
              (249, "高平陵之变"), (263, "蜀汉亡"), (265, "晋代魏"), (280, "吴亡·天下归晋")]
        st.dataframe(pd.DataFrame(tl, columns=["年份", "事件"]), hide_index=True, height=380)

    st.subheader("传记一览")
    LEN = {p["title"]: p["len"] for p in S["pianLens"]}
    BIOS = [
        ("曹操", "孟德", "魏", "君主", 1, "武帝纪"), ("曹丕", "子桓", "魏", "君主", 2, "文帝纪"),
        ("曹叡", "元仲", "魏", "君主", 3, "明帝纪"), ("曹植", "子建", "魏", "文士", 19, "任城陈萧王传"),
        ("荀彧", "文若", "魏", "谋臣", 10, "荀彧荀攸贾诩传"), ("贾诩", "文和", "魏", "谋臣", 10, "荀彧荀攸贾诩传"),
        ("郭嘉", "奉孝", "魏", "谋臣", 14, "程郭董刘蒋刘传"), ("张辽", "文远", "魏", "武将", 17, "张乐于张徐传"),
        ("夏侯惇", "元让", "魏", "武将", 9, "诸夏侯曹传"), ("夏侯渊", "妙才", "魏", "武将", 9, "诸夏侯曹传"),
        ("刘备", "玄德", "蜀", "君主", 32, "先主传"), ("刘禅", "公嗣", "蜀", "君主", 33, "后主传"),
        ("诸葛亮", "孔明", "蜀", "谋臣", 35, "诸葛亮传"), ("关羽", "云长", "蜀", "武将", 36, "关张马黄赵传"),
        ("张飞", "益德", "蜀", "武将", 36, "关张马黄赵传"), ("马超", "孟起", "蜀", "武将", 36, "关张马黄赵传"),
        ("赵云", "子龙", "蜀", "武将", 36, "关张马黄赵传"), ("魏延", "文长", "蜀", "武将", 40, "刘彭廖李刘魏杨传"),
        ("姜维", "伯约", "蜀", "武将", 44, "蒋琬费祎姜维传"), ("庞统", "士元", "蜀", "谋臣", 37, "庞统法正传"),
        ("法正", "孝直", "蜀", "谋臣", 37, "庞统法正传"), ("孙坚", "文台", "吴", "武将", 46, "孙破虏讨逆传"),
        ("孙策", "伯符", "吴", "君主", 46, "孙破虏讨逆传"), ("孙权", "仲谋", "吴", "君主", 47, "吴主传"),
        ("周瑜", "公瑾", "吴", "谋臣", 54, "周瑜鲁肃吕蒙传"), ("鲁肃", "子敬", "吴", "谋臣", 54, "周瑜鲁肃吕蒙传"),
        ("吕蒙", "子明", "吴", "武将", 54, "周瑜鲁肃吕蒙传"), ("陆逊", "伯言", "吴", "谋臣", 58, "陆逊传"),
        ("甘宁", "兴霸", "吴", "武将", 55, "程黄韩蒋周陈董甘凌徐潘丁传"), ("太史慈", "子义", "吴", "武将", 52, "刘繇太史慈士燮传"),
        ("孙皓", "元宗", "吴", "君主", 48, "三嗣主传"),
    ]
    df = pd.DataFrame(BIOS, columns=["姓名", "字", "国别", "类型", "卷次", "传记篇名"])
    df["本传字数"] = df["传记篇名"].map(LEN)
    f1, f2 = st.columns(2)
    st_state = f1.multiselect("国别", ["魏", "蜀", "吴"], ["魏", "蜀", "吴"])
    st_type = f2.multiselect("类型", ["君主", "谋臣", "武将", "文士"], ["君主", "谋臣", "武将", "文士"])
    view = df[df["国别"].isin(st_state) & df["类型"].isin(st_type)]
    st.dataframe(view.sort_values("卷次"), hide_index=True, use_container_width=True,
                 column_config={"卷次": st.column_config.NumberColumn(format="卷%d")})

st.divider()
st.caption(
    "数据来源：陈寿《三国志》白文全文（六十五卷，不含裴松之注），语料取自 GitHub 开源仓库 "
    "program-in-chinese/npm-chinese-history-classics-sanguozhi；统计脚本对简繁混排文本做常用字归一后逐字计数，"
    "多字词条为精确子串匹配。「立传人物类型」「大事年表」为整理样本。"
)
