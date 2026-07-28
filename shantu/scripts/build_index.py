import re
from datetime import datetime, timezone, timedelta
from pathlib import Path

import fitz


# =====================
# 路径
# =====================

BASE_DIR = Path(__file__).resolve().parent.parent


PDF_PATH = BASE_DIR / "山图集.pdf"


RESULT_DIR = BASE_DIR / "result"


HISTORY_DIR = BASE_DIR / "history"



# =====================
# 北京时间
# =====================

def get_beijing_time():

    return datetime.now(
        timezone(timedelta(hours=8))
    )



# =====================
# 初始化
# =====================

def init_dir():

    RESULT_DIR.mkdir(
        exist_ok=True
    )

    HISTORY_DIR.mkdir(
        exist_ok=True
    )



# =====================
# 日期匹配
# =====================

def build_date_regex(month, day):

    return re.compile(
        rf"{month}\s*月\s*{day}\s*日"
    )



# =====================
# 搜索PDF
# =====================

def search_pdf(regex, save_dir, month, day):


    images=[]


    doc = fitz.open(
        PDF_PATH
    )


    for index,page in enumerate(doc):


        text = page.get_text()


        clean = re.sub(
            r"\s+",
            "",
            text
        )


        if (
            regex.search(text)
            or
            regex.search(clean)
        ):


            print(
                "找到页面:",
                index+1
            )


            pix = page.get_pixmap(
                dpi=180
            )


            name = (
                f"shantu-{month:02d}-{day:02d}"
                f"-page-{index+1}.jpg"
            )


            pix.save(
                str(
                    save_dir/name
                )
            )


            images.append(name)



    doc.close()


    return images



# =====================
# 生成HTML
# =====================

def create_html(
    path,
    title,
    images
):


    html=f"""
<html>

<head>

<meta charset="utf-8">

<meta name="viewport"
content="width=device-width,initial-scale=1">


<title>{title}</title>


<style>

body{{
background:#f5f5f5;
font-family:Microsoft YaHei;
padding:20px;
}}

.box{{
max-width:900px;
margin:auto;
background:white;
padding:25px;
border-radius:16px;
}}


h1{{
text-align:center;
}}


img{{
width:100%;
margin-top:30px;
border-radius:12px;
}}

a{{
text-decoration:none;
}}

</style>


</head>


<body>


<div class="box">


<h1>
{title}
</h1>

"""


    for img in images:

        html+=f"""

<img src="./{img}">

"""


    html+="""


</div>

</body>

</html>

"""


    path.write_text(
        html,
        encoding="utf-8"
    )



# =====================
# 历史首页
# =====================

def create_history_index():


    items=[]


    for d in sorted(
        HISTORY_DIR.iterdir(),
        reverse=True
    ):


        if d.is_dir():

            items.append(
                f"""
<li>
<a href="./{d.name}/">
{d.name}
</a>
</li>
"""
            )



    html=f"""

<html>

<head>

<meta charset="utf-8">

<title>
山图集历史
</title>


</head>


<body>


<h1>
🌄 山图集历史
</h1>


<ul>

{"".join(items)}

</ul>


</body>

</html>

"""


    (HISTORY_DIR/"index.html").write_text(
        html,
        encoding="utf-8"
    )



# =====================
# 主程序
# =====================

def main():


    init_dir()


    today=get_beijing_time()


    year=today.year
    month=today.month
    day=today.day



    print(
        "日期:",
        today
    )



    regex=build_date_regex(
        month,
        day
    )



    today_dir = (
        HISTORY_DIR /
        f"{year}-{month:02d}-{day:02d}"
    )


    today_dir.mkdir(
        exist_ok=True
    )



    images=search_pdf(
        regex,
        today_dir,
        month,
        day
    )



    if not images:

        print(
            "今天没有图片"
        )


        return



    # 今日页面

    create_html(
        today_dir/"index.html",
        f"🌄 山图集 {month}月{day}日",
        images
    )



    # 首页复制

    create_html(
        RESULT_DIR/"index.html",
        f"🌄 山图集 {month}月{day}日",
        images
    )



    # 历史入口

    create_history_index()



    # 状态

    (RESULT_DIR/"status.txt").write_text(
        "FOUND",
        encoding="utf-8"
    )


    print(
        "完成"
    )



if __name__=="__main__":

    main()
