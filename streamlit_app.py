# -*- coding: utf-8 -*-
"""二十四史 · 全文统计看板（Streamlit 版）· 支持《三国志》《史记》
数据：stats.json（三国志，analyze.js）/ stats_shiji.json（史记，analyze_shiji.js）
"""
import json
import os
from pathlib import Path

import pandas as pd
import streamlit as st
from streamlit_echarts import st_echarts

st.set_page_config(page_title="史部 · 统计志林", page_icon="⚔", layout="wide")

HERE = Path(__file__).parent
FMT = lambda n: f"{n:,}"
PALETTE = ["#8c2f23", "#3b6b9b", "#3e8e4d", "#a67c00", "#6b5f4e", "#7a4b8f"]
AXIS = {"axisLine": {"lineStyle": {"color": "#6b5f4e"}}, "splitLine": {"lineStyle": {"color": "#e7ddc8"}}}

# ------------------ 每本书的展示配置 ------------------
BOOKS = {
    "三国志": {
        "stats_file": "stats.json",
        "h1": "三 国 志",
        "sub": "陈寿 撰 · 六十五卷 · 全文语料精确统计 · 365,797 汉字",
        "cat_color": {"魏": "#3b6b9b", "蜀": "#3e8e4d", "吴": "#b03a2e"},
        "cat_order": ["魏", "蜀", "吴"],
        "cat_label": "国别",
        "book_suffix": "书",
        "total_juan": "65",
        "juan_note": "魏30 · 蜀15 · 吴20",
        "juan_sub": "魏书三十卷 · 蜀书十五卷 · 吴书二十卷",
        "len_sub": "六十五卷逐卷字数，按魏蜀吴着色；悬停查看篇名",
        # 卷帙结构堆叠柱：x 轴 + 各堆叠层
        "structure": {
            "x": ["魏书", "蜀书", "吴书"], "stacked": True,
            "series": [
                {"name": "纪 / 帝传", "data": [4, 3, 2], "color": "#8c2f23"},
                {"name": "列传", "data": [25, 12, 17], "color": "#a67c00"},
                {"name": "族传 / 外传", "data": [1, 0, 1], "color": "#6b5f4e"},
            ],
        },
        "cmp_title": "魏蜀吴高频字对比",
        "cmp_sub": "各书前十高频字（次数为绝对值，反映叙事重心差异）",
        "guo_title": "国号与正统用字",
        "guo_sub": "魏 / 蜀 / 吴 / 汉 / 晋 等字在陈寿笔下的出现频次",
        "type_title": "立传人物类型（样本归类）",
        "type_pie": [("武将", 38), ("谋臣·政务", 30), ("君主·宗室", 16),
                     ("文士·儒林", 9), ("后妃·外戚", 4), ("方术·他传", 3)],
        "timeline": [
            (184, "黄巾之乱爆发"), (190, "关东联军讨董卓"), (200, "官渡之战"), (208, "赤壁之战"),
            (214, "刘备取益州"), (219, "关羽襄樊 / 孙权袭荆州"), (220, "曹丕代汉"), (221, "刘备称帝"),
            (222, "夷陵之战"), (223, "白帝托孤"), (227, "出师表"), (234, "星落五丈原"),
            (249, "高平陵之变"), (263, "蜀汉亡"), (265, "晋代魏"), (280, "吴亡·天下归晋"),
        ],
        "type_options": ["君主", "谋臣", "武将", "文士"],
        # 传记一览：姓名, 字, 所属, 类型, 卷次, 传记篇名
        "bios": [
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
        ],
        "bios_note": "立传人物类型、大事年表、传记一览为整理样本",
        "persons_caption": "姓名带 * 者全文几乎只以单名称呼，计数取其本传内该字出现次数，为近似值。",
        "persons_extract": "按列传起首笔法（某某字某某 / 姓X讳X字Y / 某某，某地人也）识别",
        "source": "陈寿《三国志》白文全文（六十五卷，不含裴松之注），语料取自 GitHub 开源仓库 program-in-chinese/npm-chinese-history-classics-sanguozhi；统计脚本对简繁混排文本做常用字归一后逐字计数，多字词条为精确子串匹配。「立传人物类型」「大事年表」为整理样本；「肆 · 全量人物」由脚本按列传起首笔法自动识别，未经人工校勘，或有讹漏。",
    },
    "史记": {
        "stats_file": "stats_shiji.json",
        "h1": "史 记",
        "sub": "司马迁 撰 · 一百三十卷 · 全文语料精确统计 · 576,579 汉字",
        "cat_color": {"本纪": "#8c2f23", "表": "#6b5f4e", "书": "#7a4b8f", "世家": "#3b6b9b", "列传": "#3e8e4d"},
        "cat_order": ["本纪", "表", "书", "世家", "列传"],
        "cat_label": "所属体",
        "book_suffix": "",
        "total_juan": "130",
        "juan_note": "本纪12 · 表10 · 书8 · 世家30 · 列传70",
        "juan_sub": "本纪十二 · 表十 · 书八 · 世家三十 · 列传七十",
        "len_sub": "一百三十卷逐卷字数，按五体着色；悬停查看篇名",
        "structure": {
            "x": ["本纪", "表", "书", "世家", "列传"], "stacked": False,
            "series": [{"name": "卷数", "data": [12, 10, 8, 30, 70], "color": None}],
        },
        "cmp_title": "五体高频字对比",
        "cmp_sub": "本纪 / 世家 / 列传三大叙事体前十高频字对比",
        "guo_title": "朝代与正统用字",
        "guo_sub": "周 / 秦 / 汉 / 楚 / 齐 等字与「天下」「天子」在太史公笔下的频次",
        "type_title": "立传人物类型（样本归类）",
        "type_pie": [("将相·功臣", 30), ("谋臣·纵横", 20), ("帝王·霸主", 16),
                     ("名臣·直谏", 16), ("刺客·游侠", 12), ("文士·儒林", 12), ("方技·货殖", 8)],
        "timeline": [
            ("前771", "西周亡·平王东迁，春秋始"), ("前679", "齐桓公首霸"), ("前632", "城濮之战，晋文公称霸"),
            ("前557", "鄢陵之战，晋楚争霸"), ("前496", "吴越争霸·夫差即位"), ("前473", "越灭吴"),
            ("前453", "三家分晋，战国始"), ("前356", "商鞅变法"), ("前312", "楚怀王丹阳之败"),
            ("前278", "白起破郢，屈原投江"), ("前260", "长平之战，坑赵卒四十万"), ("前227", "荆轲刺秦"),
            ("前221", "秦并天下，称始皇帝"), ("前209", "陈胜吴广起义"), ("前207", "秦亡"),
            ("前202", "垓下之围，项羽乌江自刎，汉兴"), ("前154", "七国之乱"), ("前138", "张骞凿空西域"),
            ("前119", "卫青霍去病漠北之战"), ("约前91", "司马迁《史记》成书"),
        ],
        "type_options": ["帝王", "将相", "谋臣", "名将", "名臣", "文士", "刺客", "游侠", "酷吏", "后妃"],
        "bios": [
            ("黄帝", "轩辕", "本纪", "帝王", 1, "五帝本纪"), ("秦始皇", "政", "本纪", "帝王", 6, "秦始皇本纪"),
            ("项羽", "籍", "本纪", "帝王", 7, "项羽本纪"), ("刘邦", "季", "本纪", "帝王", 8, "高祖本纪"),
            ("吕太后", "娥姁", "本纪", "后妃", 9, "吕太后本纪"), ("周文王", "昌", "本纪", "帝王", 4, "周本纪"),
            ("齐太公", "尚", "世家", "将相", 32, "齐太公世家"), ("周公", "旦", "世家", "将相", 33, "鲁周公世家"),
            ("孔子", "仲尼", "世家", "文士", 47, "孔子世家"), ("陈涉", "涉", "世家", "游侠", 48, "陈涉世家"),
            ("张良", "子房", "世家", "谋臣", 55, "留侯世家"), ("萧何", "何", "世家", "将相", 53, "萧相国世家"),
            ("曹参", "敬伯", "世家", "将相", 54, "曹相国世家"), ("周勃", "仲威", "世家", "将相", 57, "绛侯周勃世家"),
            ("平原君", "胜", "世家", "将相", 76, "平原君虞卿列传"), ("信陵君", "无忌", "列传", "将相", 77, "魏公子列传"),
            ("春申君", "歇", "列传", "将相", 78, "春申君列传"), ("孟尝君", "文", "列传", "将相", 75, "孟尝君列传"),
            ("孙武", "长卿", "列传", "名将", 65, "孙子吴起列传"), ("伍子胥", "员", "列传", "名臣", 66, "伍子胥列传"),
            ("范蠡", "少伯", "列传", "谋臣", 41, "越王句践世家"), ("商鞅", "公孙", "列传", "谋臣", 68, "商君列传"),
            ("张仪", "", "列传", "谋臣", 70, "张仪列传"), ("苏秦", "季子", "列传", "谋臣", 69, "苏秦列传"),
            ("白起", "", "列传", "名将", 73, "白起王翦列传"), ("廉颇", "", "列传", "名将", 81, "廉颇蔺相如列传"),
            ("蔺相如", "", "列传", "名臣", 81, "廉颇蔺相如列传"), ("屈原", "平", "列传", "文士", 84, "屈原贾生列传"),
            ("荆轲", "", "列传", "刺客", 86, "刺客列传"), ("李斯", "", "列传", "谋臣", 87, "李斯列传"),
            ("蒙恬", "", "列传", "名将", 88, "蒙恬列传"), ("韩信", "", "列传", "名将", 92, "淮阴侯列传"),
            ("樊哙", "", "列传", "名将", 95, "樊郦滕灌列传"), ("李广", "", "列传", "名将", 109, "李将军列传"),
            ("张汤", "", "列传", "酷吏", 122, "酷吏列传"), ("郭解", "", "列传", "游侠", 124, "游侠列传"),
            ("扁鹊", "", "列传", "文士", 105, "扁鹊仓公列传"), ("司马迁", "子长", "列传", "文士", 130, "太史公自序"),
        ],
        "bios_note": "立传人物类型、大事年表、传记一览为整理样本",
        "persons_caption": "姓名带 * 者全文几乎只以单名称呼，计数取其本传内该字出现次数，为近似值。",
        "persons_extract": "按列传/世家起首判断句（某某者，某地/某国人也，字某某 / 某某字某某 / 姓X讳X字Y）识别",
        "source": "司马迁《史记》白文全文（一百三十卷，含本纪·表·书·世家·列传，不含三家注），语料取自 GitHub 开源仓库 baojie/shiji-kb；统计脚本对零星繁体做常用字归一后逐字计数，多字词条为精确子串匹配。「立传人物类型」「大事年表」为整理样本；「肆 · 全量人物」由脚本按传记起首笔法自动识别，未经人工校勘，或有讹漏。",
    },
    "红楼梦": {
        "stats_file": "stats_hlm.json",
        "h1": "红 楼 梦",
        "sub": "曹雪芹 著 · 一百二十回 · 全文语料精确统计 · 733,553 汉字",
        "cat_color": {"风月情浓": "#8c2f23", "烈火烹油": "#a67c00", "盛筵必散": "#b03a2e",
                      "忽剌葳蕤": "#7a4b8f", "落片归大荒": "#6b5f4e"},
        "cat_order": ["风月情浓", "烈火烹油", "盛筵必散", "忽剌葳蕤", "落片归大荒"],
        "cat_label": "所属情局",
        "book_suffix": "",
        "unit": "回",
        "total_juan": "120",
        "juan_note": "风月情浓16 · 烈火烹油38 · 盛筵必散24 · 忽剌葳蕤22 · 落片归大荒20",
        "struct_title": "五段情局结构",
        "juan_sub": "以情节单元划分：顽石入世 · 省亲建园 · 抄检败象 · 黛玉夭逝 · 家亡人散",
        "len_sub": "一百二十回逐回字数，按五段着色；悬停查看回目",
        "structure": {
            "x": ["风月情浓", "烈火烹油", "盛筵必散", "忽剌葳蕤", "落片归大荒"], "stacked": False,
            "series": [{"name": "回数", "data": [16, 38, 24, 22, 20], "color": None}],
        },
        "cmp_title": "前八十回 / 后四十回 用字密度",
        "cmp_color": {"前八十回": "#8c2f23", "后四十回": "#3b6b9b"},
        "cmp_sub": "各部分前十高频字，单位「次/千字」，消除 80 回与 40 回的篇幅差异",
        "guo_title": "主题字与关键概念",
        "guo_sub": "玉 / 梦 / 情 / 泪 / 花 / 月 与「大观园」「太虚幻境」在全书的频次",
        "type_title": "人物身份构成（样本归类）",
        "type_pie": [("主子·爷奶", 14), ("奶奶·太太", 12), ("小姐·姑娘", 14),
                     ("丫鬟·婢妾", 20), ("门客·清客", 8), ("庄仆·小厮", 10), ("僧道·方技", 6), ("乡宦·官员", 4)],
        "timeline": [
            ("第1回", "女娲补天遗石下凡，甄士隐梦中见通灵"), ("第3回", "林黛玉进京入荣国府，宝黛初见"),
            ("第5回", "贾宝玉神游太虚幻境，阅金陵十二钗册"), ("第6回", "刘姥姥一进荣国府"),
            ("第15回", "王熙凤弄权铁槛寺"), ("第17回", "大观园试才题对额"),
            ("第18回", "元妃省亲，大观园极盛之始"), ("第23回", "共读西厢，牡丹亭曲警芳心"),
            ("第27回", "黛玉葬花，吟《葬花吟》"), ("第33回", "宝玉挨打"),
            ("第37回", "秋爽斋结海棠诗社"), ("第40回", "史太君两宴大观园"),
            ("第45回", "金兰契互剖金兰语，钗黛冰释"), ("第46回", "鸳鸯女誓绝鸳鸯偶"),
            ("第52回", "勇晴雯病补雀金裘"), ("第55回", "探春理家，兴利除弊"),
            ("第63回", "寿怡红群芳开夜宴"), ("第64—66回", "贾琏偷娶尤二姨，尤三姐耻情归柳湘莲"),
            ("第74回", "抄检大观园，司棋被逐"), ("第77回", "俏丫鬟抱屈夭风流，晴雯之死"),
            ("第78回", "杜撰《芙蓉女儿诔》"), ("第83回", "元妃染恙"),
            ("第90回", "薛姨妈作媒，宝蟾撒帐"), ("第94回", "贾母赏花妖，宝玉失落通灵玉"),
            ("第97回", "林黛玉焚稿断痴情，薛宝钗出闺成大礼"), ("第98回", "苦绛珠魂归离恨天"),
            ("第101回", "大观园查赌，贾府被议罪"), ("第103回", "贾雨村获罪，甄家被抄"),
            ("第105回", "锦衣军查抄宁国府"), ("第107回", "宁国府抄家，贾母散余资"),
            ("第110回", "史太君寿终归地府"), ("第113回", "妙玉遭劫，惜春决意出家"),
            ("第118回", "贾兰中举，宝玉却尘缘"), ("第120回", "贾雨村归结红楼梦，甄士隐详说太虚情"),
        ],
        "tl_col": "回数",
        "type_options": ["主角", "主子", "奶奶·太太", "小姐", "丫鬟", "优伶", "门客", "庄仆", "僧道", "乡宦·官员"],
        "bios": [
            ("贾宝玉", "怡红公子", "风月情浓", "主角", 2, "贾夫人仙逝扬州城 冷子兴演说荣国府"),
            ("林黛玉", "潇湘妃子", "风月情浓", "小姐", 3, "金陵城起复贾雨村 荣国府收养林黛玉"),
            ("薛宝钗", "蘅芜君", "烈火烹油", "小姐", 4, "薄命女偏逢薄命郎 葫芦僧乱判葫芦案"),
            ("王熙凤", "凤辣子", "风月情浓", "奶奶·太太", 3, "金陵城起复贾雨村 荣国府收养林黛玉"),
            ("贾母", "史太君", "风月情浓", "奶奶·太太", 3, "金陵城起复贾雨村 荣国府收养林黛玉"),
            ("贾政", "存周", "风月情浓", "主子", 2, "贾夫人仙逝扬州城 冷子兴演说荣国府"),
            ("元春", "贤德妃", "风月情浓", "主子", 17, "大观园试才题对额 怡红院迷路探曲折"),
            ("探春", "蕉下客", "烈火烹油", "小姐", 3, "金陵城起复贾雨村 荣国府收养林黛玉"),
            ("史湘云", "枕霞旧友", "烈火烹油", "小姐", 20, "王熙凤正言弹妒意 林黛玉俏语谑娇音"),
            ("妙玉", "畸人", "烈火烹油", "僧道", 17, "大观园试才题对额 怡红院迷路探曲折"),
            ("迎春", "二木头", "烈火烹油", "小姐", 3, "金陵城起复贾雨村 荣国府收养林黛玉"),
            ("惜春", "藕榭", "烈火烹油", "小姐", 3, "金陵城起复贾雨村 荣国府收养林黛玉"),
            ("王夫人", "太太", "风月情浓", "奶奶·太太", 3, "金陵城起复贾雨村 荣国府收养林黛玉"),
            ("薛姨妈", "", "烈火烹油", "奶奶·太太", 4, "薄命女偏逢薄命郎 葫芦僧乱判葫芦案"),
            ("李纨", "稻香老农", "烈火烹油", "奶奶·太太", 4, "薄命女偏逢薄命郎 葫芦僧乱判葫芦案"),
            ("秦可卿", "兼美", "风月情浓", "奶奶·太太", 5, "开生面梦演红楼梦 立新场情传幻境情"),
            ("晴雯", "", "烈火烹油", "丫鬟", 31, "撕扇子作千金一笑 因麒麟伏白首双星"),
            ("袭人", "珍珠", "风月情浓", "丫鬟", 6, "贾宝玉初试云雨情 刘姥姥一进荣国府"),
            ("麝月", "", "烈火烹油", "丫鬟", 21, "贤袭人娇嗔箴宝玉 俏平儿软语救贾琏"),
            ("紫鹃", "", "烈火烹油", "丫鬟", 57, "慧紫鹃情辞试忙玉 慈姨妈爱语慰痴颦"),
            ("平儿", "", "风月情浓", "丫鬟", 21, "贤袭人娇嗔箴宝玉 俏平儿软语救贾琏"),
            ("鸳鸯", "", "烈火烹油", "丫鬟", 24, "醉金刚轻财尚义侠 痴女儿遗帕惹相思"),
            ("香菱", "秋菱", "烈火烹油", "丫鬟", 1, "甄士隐梦幻识通灵 贾雨村风尘怀闺秀"),
            ("芳官", "", "盛筵必散", "优伶", 36, "绣鸳鸯梦兆绛芸轩 识分定情悟梨香院"),
            ("刘姥姥", "", "风月情浓", "庄仆", 6, "贾宝玉初试云雨情 刘姥姥一进荣国府"),
            ("贾琏", "二爷", "风月情浓", "主子", 2, "贾夫人仙逝扬州城 冷子兴演说荣国府"),
            ("贾珍", "", "风月情浓", "主子", 7, "送宫花周瑞叹英莲 谈肆业秦钟结宝玉"),
            ("薛蟠", "呆霸王", "烈火烹油", "主子", 4, "薄命女偏逢薄命郎 葫芦僧乱判葫芦案"),
            ("贾雨村", "时飞", "风月情浓", "乡宦·官员", 1, "甄士隐梦幻识通灵 贾雨村风尘怀闺秀"),
            ("柳湘莲", "冷二郎", "盛筵必散", "门客", 66, "情小妹耻情归地府 冷二郎一冷入空门"),
            ("贾瑞", "天祥", "风月情浓", "门客", 11, "庆寿辰宁府排家宴 见熙凤贾瑞起淫心"),
            ("秦钟", "鲸卿", "风月情浓", "门客", 7, "送宫花周瑞叹英莲 谈肆业秦钟结宝玉"),
            ("尤二姐", "二姨", "盛筵必散", "小姐", 63, "寿怡红群芳开夜宴 死金丹独艳理亲丧"),
            ("尤三姐", "", "盛筵必散", "小姐", 63, "寿怡红群芳开夜宴 死金丹独艳理亲丧"),
            ("甄士隐", "名费", "风月情浓", "乡宦·官员", 1, "甄士隐梦幻识通灵 贾雨村风尘怀闺秀"),
            ("跛足道人", "", "风月情浓", "僧道", 1, "甄士隐梦幻识通灵 贾雨村风尘怀闺秀"),
        ],
        "len_label": "该回字数",
        "zi_col": "别称·诗号", "pian_col": "相关回目", "person_pian_col": "相关回目",
        "bios_head": "人物一览", "cat_head": "五段人物数 / 见「小名·表字」",
        "sn_note": "仅计以姓相称者：{withSurname} / {total} 人。丫鬟、优伶（袭人、晴雯、紫鹃）首字是名而非姓，不入此图。",
        "bios_note": "「五段情局」为情节单元划分；身份构成、大事年表、人物一览为整理样本",
        "name_sub": "主要人物称名统计（姓名 / 别称·小名 / 诗号·尊称 堆叠，精确子串计数）",
        "name_caption": "注：白话小说中「太太」「姑娘」一类尊称与常用词同形，堆叠段仅作称名口径参考；「凤姐儿」为「凤姐」的儿化形，悬停可见各变体明细。",
        "zi_label": "见「小名·表字」", "zi_series_label": "其中见「小名·表字」",
        "persons_extract": "按对话引导词（X笑道／说道／问道）回溯 2—4 字，以姓氏与红楼称名用字白名单锚定识别",
        "persons_caption": "本书无「本传」概念：已并入「叁 · 称名统计」的主要人物不再重列，此处为其外的中次要人物。",
        "source": "曹雪芹《红楼梦》白文全文（一百二十回，程甲本系，不含脂批与评点），语料取自 GitHub 开源仓库 xuyao00/hongloumeng；"
                  "统计脚本逐字计数，多字词条为精确子串匹配。「五段情局」「人物身份构成」「大事年表」为整理样本；"
                  "「肆 · 全量人物」由脚本按对话引导词与人名用字白名单自动识别，未经人工校勘，或有讹漏。",
    },
}

_book_keys = list(BOOKS.keys())
book = st.radio("书籍", _book_keys, index=_book_keys.index(os.environ.get("SHIBU_BOOK", "三国志")),
                horizontal=True, label_visibility="collapsed")
C = BOOKS[book]
S = json.loads((HERE / C["stats_file"]).read_text(encoding="utf-8"))
CC = C["cat_color"]
CMP_C = {**CC, **C.get("cmp_color", {})}   # 对比图分组可与分类不同（红楼梦为前八十/后四十回）
U = C.get("unit", "卷")          # 分篇单位：三国志/史记为「卷」，红楼梦为「回」
ZI = C.get("zi_col", "字")       # 人物第二列：史书为「字」，白话小说为别称·诗号
PIAN = C.get("pian_col", "传记篇名")
PIAN2 = C.get("person_pian_col", "本传篇名")
csuffix = lambda b: b + C["book_suffix"]

st.markdown(
    f"<h1 style='text-align:letter-spacing:8px'>{C['h1']} <span style='font-size:.5em;color:#8c2f23'>统 计 志 林</span></h1>"
    f"<p style='text-align:center;color:#6b5f4e'>{C['sub']}</p>",
    unsafe_allow_html=True,
)


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


TABS = ["壹 · 全书概览", "贰 · 字词频率", "叁 · 人物与传记", "肆 · 全量人物"]
page = st.radio("章节", TABS, horizontal=True, label_visibility="collapsed")
_SHOW = TABS if os.environ.get("SHIBU_ALL") else [page]

# ============ 壹 概览 ============
if TABS[0] in _SHOW:
    m = S["meta"]
    c = st.columns(7)
    c[0].metric("汉字总数", FMT(m["totalChars"]), help="全文精确计数（不含标点）")
    c[1].metric("不同单字", FMT(m["uniqChars"]), help="字种数")
    c[2].metric("仅出现一次", FMT(m["hapax"]), help="生僻字/专名用字")
    c[3].metric(f"总{U}数", C["total_juan"], help=C["juan_note"])
    c[4].metric("句子总数", FMT(m["sentCount"]), help="按句读切分")
    c[5].metric("平均句长", m["avgSent"], help="字 / 句")
    c[6].metric("自动提取人物", FMT(S["personStats"]["total"]), help="见「肆 · 全量人物」")

    st.caption(C["bios_note"])
    left, right = st.columns([1, 2])
    st_ = C["structure"]
    with left:
        st.subheader(C.get("struct_title", "卷帙结构"))
        if st_["stacked"]:
            series = [{"name": s["name"], "type": "bar", "stack": "t", "barWidth": 50,
                       "data": s["data"], "itemStyle": {"color": s["color"]},
                       "label": {"show": True, "color": "#fff"}} for s in st_["series"]]
        else:
            series = [{"name": s["name"], "type": "bar", "barWidth": 50, "label": {"show": True},
                       "data": [{"value": v, "itemStyle": {"color": CC[x]}}
                                for x, v in zip(st_["x"], s["data"]) ]} for s in st_["series"]]
        st_echarts({
            "backgroundColor": "transparent",
            "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
            "legend": {"bottom": 0},
            "grid": {"left": 50, "right": 20, "top": 30, "bottom": 50},
            "xAxis": {"type": "category", "data": st_["x"], **AXIS},
            "yAxis": {"type": "value", "name": U, **AXIS},
            "series": series,
        }, height="360px")
    with right:
        st.subheader(f"{U}幅分布（逐{U}精确字数）")
        st.caption(C["len_sub"])
        pl = S["pianLens"]
        pl_js = json.dumps([{"j": U + str(p["juan"]), "t": p["title"], "l": p["len"]} for p in pl], ensure_ascii=False)
        st_echarts({
            "backgroundColor": "transparent",
            "tooltip": {"trigger": "axis", "formatter":
                        "function(p){var d=" + pl_js + "[p[0].dataIndex];return d.j+'《'+d.t+'》<br>'+d.l.toLocaleString()+' 字';}"},
            "grid": {"left": 60, "right": 20, "top": 30, "bottom": 40},
            "xAxis": {"type": "category", "data": [p["juan"] for p in pl], "name": U + "次", **AXIS},
            "yAxis": {"type": "value", "name": "字数", **AXIS},
            "series": [{"type": "bar", "barWidth": "70%",
                        "data": [{"value": p["len"], "itemStyle": {"color": CC[p["book"]]}} for p in pl]}],
        }, height="360px")

# ============ 贰 字词 ============
if TABS[1] in _SHOW:
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
        st.subheader(C["cmp_title"])
        st.caption(C["cmp_sub"])
        st_echarts({
            "backgroundColor": "transparent",
            "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
            "legend": {"bottom": 0},
            "grid": {"left": 50, "right": 20, "top": 30, "bottom": 50},
            "xAxis": {"type": "category", "data": S["cmpChars"], "axisLabel": {"fontSize": 16}},
            "yAxis": {"type": "value", "name": S.get("cmpUnits", "次数"), **AXIS},
            "series": [{"name": csuffix(s["book"]), "type": "bar", "data": s["data"],
                        "itemStyle": {"color": CMP_C.get(s["book"], "#6b5f4e")}} for s in S["cmpSeries"]],
        }, height="480px")

    c5, c6 = st.columns(2)
    with c5:
        st.subheader(C["guo_title"])
        st_echarts({
            "backgroundColor": "transparent",
            "tooltip": {"trigger": "axis"},
            "grid": {"left": 50, "right": 20, "top": 30, "bottom": 30},
            "xAxis": {"type": "category", "data": [g[0] for g in S["GUOHao"]], **AXIS},
            "yAxis": {"type": "value", **AXIS},
            "series": [{"type": "bar", "barWidth": 36, "label": {"show": True, "position": "top"},
                        "data": [{"value": g[1], "itemStyle": {"color": CC.get(g[0], "#6b5f4e")}}
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

    st.subheader(f"逐{U}下钻 · 各{U}自己的高频字")
    titles = [f"{U}{p['juan']}《{p['title']}》（{FMT(p['len'])}字）" for p in S["pianLens"]]
    i = st.selectbox(f"选择{U}次", range(len(titles)), format_func=lambda x: titles[x], label_visibility="collapsed")
    p = S["pianLens"][i]
    st_echarts(hbar(p["top"], color=CC[p["book"]], height=440, fontsize=15), height="460px")

# ============ 叁 人物 ============
if TABS[2] in _SHOW:
    st.subheader(C.get("name_sub", "人名出现统计（姓名 / 字 / 庙号·尊称 别名堆叠，精确子串计数）"))
    rows = sorted(
        [{"name": n, "total": sum(d[1] for d in det), "detail": det} for n, det in S["nameCounts"]],
        key=lambda r: -r["total"])
    maxseg = max(len(r["detail"]) for r in rows)
    colors = ["#8c2f23", "#3b6b9b", "#a67c00", "#3e8e4d", "#7a4b8f"]
    series = []
    for seg in range(maxseg):
        series.append({
            "name": C.get("name_segs", ["姓名", "别称"])[min(seg, 1)],
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
    st.caption(C.get("name_caption", "注：单字别称为全文子串口径，含同字非人名用例，仅供参考；悬停可见各变体明细。"))

    c7, c8 = st.columns([1, 1])
    with c7:
        st.subheader(C["type_title"])
        st_echarts({
            "backgroundColor": "transparent",
            "tooltip": {"trigger": "item", "formatter": "{b}：{c} 人（{d}%）"},
            "legend": {"bottom": 0},
            "color": PALETTE,
            "series": [{"type": "pie", "radius": ["28%", "62%"], "center": ["50%", "45%"],
                        "roseType": "radius", "itemStyle": {"borderColor": "#fff", "borderWidth": 2},
                        "label": {"formatter": "{b}\n{d}%"},
                        "data": [{"name": n, "value": v} for n, v in C["type_pie"]]}],
        }, height="400px")
    with c8:
        st.subheader("大事年表")
        st.dataframe(pd.DataFrame(C["timeline"], columns=[C.get("tl_col", "年份"), "事件"]), hide_index=True, height=380)

    st.subheader(C.get("bios_head", "传记一览"))
    LEN = {p["title"]: p["len"] for p in S["pianLens"]}
    df = pd.DataFrame(C["bios"], columns=["姓名", ZI, C["cat_label"], "类型", U + "次", PIAN])
    df[C.get("len_label", "本传字数")] = df[PIAN].map(LEN)
    f1, f2 = st.columns(2)
    sel_cat = f1.multiselect(C["cat_label"], C["cat_order"], C["cat_order"], key="bio_cat")
    sel_type = f2.multiselect("类型", C["type_options"], C["type_options"], key="bio_type")
    view = df[df[C["cat_label"]].isin(sel_cat) & df["类型"].isin(sel_type)]
    st.dataframe(view.sort_values(U + "次"), hide_index=True, use_container_width=True,
                 column_config={U + "次": st.column_config.NumberColumn(format=U + "%d")})

# ============ 肆 全量人物 ============
if TABS[3] in _SHOW:
    P = S["persons"]
    PS = S["personStats"]
    c = st.columns(4)
    c[0].metric("自动提取人物", FMT(PS["total"]), help=C["persons_extract"])
    c[1].metric(C.get("zi_label", "见「字」记载"), FMT(PS["withZi"]), help=f"占 {PS['withZi'] * 100 // max(PS['total'],1)}%")
    c[2].metric(" · ".join(csuffix(b) for b, _ in PS["byBook"]), " · ".join(FMT(v) for _, v in PS["byBook"]))
    c[3].metric("第一大姓", f"{PS['surnames'][0][0]} 氏", help=f"{PS['surnames'][0][1]} 人")

    lft, rgt = st.columns(2)
    with lft:
        st.subheader("姓氏分布 Top 18")
        st_echarts({
            "backgroundColor": "transparent",
            "tooltip": {"trigger": "axis"},
            "grid": {"left": 50, "right": 20, "top": 20, "bottom": 70},
            "xAxis": {"type": "category", "data": [x[0] for x in PS["surnames"]],
                      "axisLabel": {"interval": 0, "rotate": 40}, **AXIS},
            "yAxis": {"type": "value", "name": "人数", **AXIS},
            "series": [{"type": "bar", "barWidth": "62%", "data": [x[1] for x in PS["surnames"]],
                        "itemStyle": {"color": "#a67c00", "borderRadius": [6, 6, 0, 0]},
                        "label": {"show": True, "position": "top", "fontSize": 11}}],
        }, height="440px")
        if C.get("sn_note") and PS.get("withSurname") is not None:
            st.caption(C["sn_note"].format(**PS))
    with rgt:
        st.subheader(C.get("cat_head", f"分{C['cat_label']}人物数"))
        st_echarts({
            "backgroundColor": "transparent",
            "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
            "legend": {"bottom": 0},
            "grid": {"left": 50, "right": 20, "top": 20, "bottom": 50},
            "xAxis": {"type": "category", "data": [csuffix(x[0]) for x in PS["byBook"]], **AXIS},
            "yAxis": {"type": "value", "name": "人数", **AXIS},
            "series": [
                {"name": "提取人物", "type": "bar", "barWidth": 44, "label": {"show": True, "position": "top"},
                 "data": [{"value": x[1], "itemStyle": {"color": CC[x[0]]}} for x in PS["byBook"]]},
                {"name": C.get("zi_series_label", "其中见「字」"), "type": "line", "symbol": "circle", "symbolSize": 8,
                 "lineStyle": {"color": "#6b5f4e"}, "itemStyle": {"color": "#6b5f4e"},
                 "data": [sum(1 for p in P if p["book"] == b and p["zi"]) for b, _ in PS["byBook"]]},
            ],
        }, height="440px")

    st.subheader("出现频次 Top 30 人物")
    top = P[:30]
    tip = json.dumps([{"n": p["name"], "z": p["zi"], "j": U + str(p["juan"]), "t": p["title"],
                       "c": p["count"], "a": bool(p["approx"])} for p in top], ensure_ascii=False)
    st_echarts({
        "backgroundColor": "transparent",
        "tooltip": {"trigger": "axis", "formatter":
                    "function(p){var d=" + tip + "[p[0].dataIndex];"
                    "return '<b>'+d.n+'</b>'+(d.z?'，字'+d.z:'')+'<br>出现 '+d.c+' 次'"
                    "+(d.a?'（含本传内单名称呼）':'')+'<br>'+d.j+'《'+d.t+'》';}"},
        "grid": {"left": 90, "right": 70, "top": 10, "bottom": 30},
        "xAxis": {"type": "value", **AXIS},
        "yAxis": {"type": "category", "inverse": True,
                  "data": [p["name"] + ("*" if p["approx"] else "") for p in top], **AXIS},
        "series": [{"type": "bar", "barWidth": 13,
                    "data": [{"value": p["count"], "itemStyle": {"color": CC[p["book"]],
                                                                "borderRadius": [0, 6, 6, 0]}} for p in top],
                    "label": {"show": True, "position": "right", "fontSize": 11}}],
    }, height="620px")
    st.caption(C["persons_caption"])

    st.subheader(f"人物索引（{FMT(PS['total'])} 人）")
    pdf = pd.DataFrame(P)[["name", "zi", "book", "juan", "title", "count"]]
    cols = ["姓名", ZI, C["cat_label"], U + "次", PIAN2, "出现次数"]
    has_approx = any(bool(p["approx"]) for p in P)
    if has_approx:                      # 近似计数仅对史书「单名称呼」口径有意义
        pdf["approx"] = [bool(p["approx"]) for p in P]
        cols.append("本传单名计数")
    pdf.columns = cols
    q1, q2 = st.columns([2, 1])
    kw = q1.text_input("搜索", placeholder=f"姓名 / {ZI} / {PIAN}", label_visibility="collapsed", key="person_q")
    bk = q2.multiselect(C["cat_label"], C["cat_order"], C["cat_order"], key="person_cat")
    pv = pdf[pdf[C["cat_label"]].isin(bk)]
    if kw:
        mask = pv["姓名"].str.contains(kw, na=False) | pv[ZI].str.contains(kw, na=False) \
            | pv[PIAN].str.contains(kw, na=False)
        pv = pv[mask]
    st.caption(f"共 {len(pv)} 人")
    cfg = {U + "次": st.column_config.NumberColumn(format=U + "%d")}
    if has_approx:
        cfg["本传单名计数"] = st.column_config.CheckboxColumn(width="small")
    st.dataframe(pv.sort_values("出现次数", ascending=False), hide_index=True,
                 use_container_width=True, height=560, column_config=cfg)

st.divider()
st.caption("数据来源：" + C["source"])
