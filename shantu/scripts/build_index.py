import re

from datetime import datetime, timezone, timedelta

from pathlib import Path

import fitz



# =====================
# 配置
# =====================


TEST_MODE = False


TEST_DATE = (
    2026,
    7,
    24
)



# =====================
# 网站地址
# =====================


SITE_URL = (
    "https://deanling2011.github.io/shanshitu"
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
# 日期匹配
# =====================


def build_date_regex(month, day):

    return re.compile(

        rf"{month}\s*月\s*{day}\s*日"

    )





# =====================
# PDF解析
# =====================


# =====================
# PDF解析（支持跨页）
# =====================


def search_pdf(

        regex,

        save_dir,

        month,

        day

):


    images = []


    doc = fitz.open(

        PDF_PATH

    )


    # 是否已经找到当天内容

    found_today = False



    # 日期检测

    date_pattern = re.compile(

        r"\d{4}\s*年\s*\d+\s*月\s*\d+\s*日"

    )



    for index, page in enumerate(doc):


        text = page.get_text()



        clean = re.sub(

            r"\s+",

            "",

            text

        )



        # 当前页是否包含目标日期

        current_is_today = (

            regex.search(text)

            or

            regex.search(clean)

        )



        # 当前页是否包含其他日期

        has_other_date = (

            date_pattern.search(text)

        )




        # =====================
        # 找到当天
        # =====================


        if current_is_today:


            found_today = True


            print(

                "找到日期页面:",

                index + 1

            )




        # =====================
        # 已经进入当天内容
        # =====================


        if found_today:



            # 如果不是第一页，
            # 并且出现新的日期
            # 说明进入下一天


            if (

                index > 0

                and

                has_other_date

                and

                not current_is_today

            ):


                print(

                    "发现下一日期，停止抓取:",

                    index + 1

                )


                break




            print(

                "保存页面:",

                index + 1

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

font-size:18px;

}}



img{{

width:100%;

margin-top:30px;

border-radius:14px;

display:block;

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


🖼 今日图片：

{len(images)} 张



<br>


⏰ 更新时间：

{now}



</div>



"""



    # 图片展示

    for img in images:


        html += f"""

<img

src="{image_prefix}{img}"

loading="lazy"

decoding="async"

>

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


    cards = []


    history = sorted(

        [

            x.name

            for x in HISTORY_DIR.iterdir()

            if x.is_dir()

        ],

        reverse=True

    )



    for item in history:


        folder = HISTORY_DIR / item


        images = list(

            folder.glob("*.jpg")

        )


        cover = ""


        if images:

            cover = (

                f"./{item}/{images[0].name}"

            )



        cards.append(

f"""

<div class="box">


<a href="./{item}/">


<img

src="{cover}"

loading="lazy"


>



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



.box{{

background:white;

padding:20px;

border-radius:18px;

margin-bottom:20px;

max-width:900px;

margin-left:auto;

margin-right:auto;

box-shadow:

0 5px 20px rgba(0,0,0,.08);

}}



.box img{{

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



<h1>

🌄 山图集历史

</h1>



{"".join(cards)}



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
# PushDeer通知
# =====================


def create_notify(

        year,

        month,

        day,

        images

):


    today_date = (

        f"{year}-{month:02d}-{day:02d}"

    )



    today_url = (

        f"{SITE_URL}/history/"

        f"{today_date}/"

    )



    home_url = SITE_URL




    # 今日第一张图片作为封面

    cover_url = (

        f"{today_url}"

        f"{images[0]}"

        if images

        else ""

    )




    now = get_beijing_time().strftime(

        "%Y-%m-%d %H:%M:%S"

    )





    notify = f"""
## 🏔 今日封面


![]({cover_url})



---


🖼 **图片数量**

{len(images)} 张



⏰ **生成时间**

{now}



🏠 **山图集主页**

{home_url}
"""



    (

        RESULT_DIR / "notify.txt"

    ).write_text(

        notify,

        encoding="utf-8"

    )




    (

        RESULT_DIR / "cover.txt"

    ).write_text(

        cover_url,

        encoding="utf-8"

    )







# =====================
# 主程序
# =====================


def main():


    print("====================")

    print("山图集开始运行")

    print("====================")



    init_dir()



    today = get_beijing_time()



    year = today.year

    month = today.month

    day = today.day




    print(

        "当前日期:",

        today

    )





    if not PDF_PATH.exists():


        raise FileNotFoundError(

            f"找不到PDF:{PDF_PATH}"

        )





    regex = build_date_regex(

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





    images = search_pdf(

        regex,

        today_dir,

        month,

        day

    )







    if not images:


        print(

            "今天没有山图"

        )


        create_history_index()


        return







    # 今日页面

    create_html(

        today_dir / "index.html",

        f"🌄 山图集 {month}月{day}日",

        images

    )







    # 首页

    create_html(

        RESULT_DIR / "index.html",

        f"🌄 山图集 {month}月{day}日",

        images,

        f"./history/{year}-{month:02d}-{day:02d}/"

    )







    # 历史页面

    create_history_index()






    # PushDeer

    create_notify(

        year,

        month,

        day,

        images

    )






    (

        RESULT_DIR / "status.txt"

    ).write_text(

        "FOUND",

        encoding="utf-8"

    )






    print("====================")

    print("生成完成")

    print(

        "图片数量:",

        len(images)

    )

    print("====================")







if __name__ == "__main__":


    main()
