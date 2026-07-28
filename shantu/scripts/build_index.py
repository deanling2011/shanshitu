import re
import shutil

from datetime import datetime, timezone, timedelta
from pathlib import Path

import fitz



# =====================
# 配置
# =====================


# 测试模式
# 发布前改 False

TEST_MODE = False


TEST_DATE = (
    2026,
    7,
    24
)



# =====================
# 路径
# =====================


BASE_DIR = Path(__file__).resolve().parent.parent


PDF_PATH = BASE_DIR / "山图集.pdf"


RESULT_DIR = BASE_DIR / "result"


HISTORY_DIR = RESULT_DIR / "history"




# =====================
# 北京时间
# =====================


def get_beijing_time():

    tz = timezone(
        timedelta(hours=8)
    )


    if TEST_MODE:

        return datetime(
            TEST_DATE[0],
            TEST_DATE[1],
            TEST_DATE[2],
            tzinfo=tz
        )


    return datetime.now(tz)




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
# 清理当天目录
# =====================


def clean_today_dir(path):

    if path.exists():

        shutil.rmtree(
            path
        )


    path.mkdir(
        exist_ok=True
    )




# =====================
# 历史列表
# =====================


def get_history():

    return sorted(

        [

            x.name

            for x in HISTORY_DIR.iterdir()

            if x.is_dir()

        ],

        reverse=True

    )




# =====================
# 日期匹配
# =====================


def build_date_regex(month, day):

    return re.compile(

        rf"{month}\s*月\s*{day}\s*日"

    )




# =====================
# PDF解析
# =====================


def search_pdf(
        regex,
        save_dir,
        month,
        day
):


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


            name=(

                f"shantu-{month:02d}-{day:02d}"

                f"-page-{index+1}.jpg"

            )


            pix.save(

                str(
                    save_dir / name
                )

            )


            images.append(
                name
            )


            print(
                "生成图片:",
                name
            )


    doc.close()


    return images
    # =====================
# HTML生成
# =====================


def create_html(
        path,
        title,
        images,
        image_prefix="./",
        show_history=False
):


    now = get_beijing_time().strftime(
        "%Y-%m-%d %H:%M:%S"
    )


    history = get_history()



    html = f"""
<!DOCTYPE html>

<html>

<head>


<meta charset="utf-8">


<meta name="viewport"

content="width=device-width,initial-scale=1">


<title>
{title}
</title>



<style>


body{{

    background:#f5f5f5;

    font-family:

    Microsoft YaHei;

    padding:20px;

}}



.container{{

    max-width:900px;

    margin:auto;

}}



.box{{

    background:white;

    padding:25px;

    border-radius:18px;

    box-shadow:

    0 5px 20px rgba(0,0,0,.08);

}}



h1{{

    text-align:center;

    font-size:34px;

}}



.info{{

    text-align:center;

    color:#777;

    line-height:2;

}}



img{{

    width:100%;

    margin-top:30px;

    border-radius:14px;

}}



.button{{

    display:block;

    margin-top:30px;

    padding:14px;

    background:#333;

    color:white;

    text-align:center;

    border-radius:12px;

    text-decoration:none;

}}



.history-card{{

    background:#f7f7f7;

    margin-top:10px;

    padding:15px;

    border-radius:12px;

    text-align:center;

}}



a{{

    text-decoration:none;

    color:#333;

}}


</style>


</head>



<body>



<div class="container">


<div class="box">



<h1>

{title}

</h1>




<div class="info">


📅 日期：

{title}


<br>


🖼 图片数量：

{len(images)} 张


<br>


⏰ 更新时间：

{now}


<br>


📚 历史记录：

{len(history)} 期



</div>


"""



    # 图片


    for img in images:


        html += f"""

<img

src="{image_prefix}{img}"

loading="lazy"

>

"""



    # 首页增加历史


    if show_history:


        html += """

<a class="button"

href="./history/">

查看全部历史山图集

</a>



<h2>

最近记录

</h2>

"""



        for item in history[:5]:


            html += f"""

<div class="history-card">


<a href="./history/{item}/">


📅 {item}


</a>


</div>

"""



    html += """

</div>


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


    cards=[]


    history=get_history()



    for item in history:


        folder = HISTORY_DIR / item


        images=list(

            folder.glob("*.jpg")

        )


        cover=""


        if images:

            cover=(

                f"./{item}/{images[0].name}"

            )



        cards.append(

f"""

<div class="card">


<a href="./{item}/">


<img src="{cover}">



<h2>

📅 {item}

</h2>



<p>

🖼 图片数量：

{len(images)} 张

</p>


</a>


</div>

"""

        )



    html=f"""

<!DOCTYPE html>

<html>


<head>


<meta charset="utf-8">


<meta name="viewport"

content="width=device-width,initial-scale=1">


<title>

山图集历史

</title>


<style>


body{{

background:#f5f5f5;

font-family:

Microsoft YaHei;

padding:20px;

}}



.container{{

max-width:900px;

margin:auto;

}}



.card{{

background:white;

padding:20px;

margin-bottom:25px;

border-radius:18px;

box-shadow:

0 5px 20px rgba(0,0,0,.08);

}}



.card img{{

width:100%;

border-radius:14px;

}}



a{{

text-decoration:none;

color:#333;

}}


</style>


</head>


<body>


<div class="container">


<h1>

🌄 山图集历史

</h1>



{"".join(cards)}



</div>


</body>


</html>

"""


    (
        HISTORY_DIR / "index.html"

    ).write_text(

        html,

        encoding="utf-8"

    )
    # =====================
# 主程序
# =====================


def main():


    print("====================")
    print("山图集开始运行")
    print("====================")



    # 初始化目录

    init_dir()



    # 获取日期


    today = get_beijing_time()



    year = today.year

    month = today.month

    day = today.day



    print(
        "当前日期:",
        today
    )



    # PDF检查


    if not PDF_PATH.exists():


        raise FileNotFoundError(

            f"找不到PDF文件:{PDF_PATH}"

        )




    # 日期匹配


    regex = build_date_regex(

        month,

        day

    )



    print(

        "匹配规则:",

        regex.pattern

    )





    # 创建当天历史目录


    today_dir = (

        HISTORY_DIR /

        f"{year}-{month:02d}-{day:02d}"

    )



    today_dir.mkdir(

        exist_ok=True

    )





    # 搜索PDF


    images = search_pdf(

        regex,

        today_dir,

        month,

        day

    )





    # =====================
    # 没找到
    # =====================


    if not images:


        print(
            "今天没有找到山图"
        )


        print(
            "保留已有历史数据"
        )



        # 重新生成历史首页

        create_history_index()



        return






    # =====================
    # 找到图片
    # =====================



    print(

        "找到图片:",

        len(images)

    )





    # 生成当天页面


    create_html(

        today_dir / "index.html",

        f"🌄 山图集 {month}月{day}日",

        images

    )






    # 历史数量


    history_count = len(

        [

            x

            for x in HISTORY_DIR.iterdir()

            if x.is_dir()

        ]

    )






    # 生成首页


    create_html(

        RESULT_DIR / "index.html",

        f"🌄 山图集 {month}月{day}日",

        images,

        f"./history/{year}-{month:02d}-{day:02d}/",

        True

    )







    # 更新历史首页


    create_history_index()






    # 状态文件


    (
        RESULT_DIR / "status.txt"

    ).write_text(

        "FOUND",

        encoding="utf-8"

    )






    print("====================")

    print("生成完成")

    print(

        "日期:",

        f"{year}-{month:02d}-{day:02d}"

    )


    print(

        "图片数量:",

        len(images)

    )


    print("====================")






# =====================
# 程序入口
# =====================


if __name__ == "__main__":


    main()
