import re

from datetime import datetime, timezone, timedelta

from pathlib import Path

import fitz



# =====================
# 配置
# =====================


TEST_MODE = True


TEST_DATE = (
    2026,
    7,
    31
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
# PDF解析
# 历史上的今天
# 支持多个年份
# =====================


def search_pdf(

        target_month,

        target_day,

        save_dir

):


    images = []


    doc = fitz.open(

        PDF_PATH

    )


    # 日期格式

    date_pattern = re.compile(

        r"(\d{4})\s*年\s*(\d+)\s*月\s*(\d+)\s*日"

    )



    collecting = False


    count = 1



    for index, page in enumerate(doc):


        text = page.get_text()



        dates = date_pattern.findall(text)



        page_is_target = False


        page_has_other_date = False




        for year, month, day in dates:


            year = int(year)

            month = int(month)

            day = int(day)



            # 找目标日期

            if (

                month == target_month

                and

                day == target_day

            ):


                page_is_target = True


                print(

                    "发现目标日期:",

                    year,

                    "年",

                    month,

                    "月",

                    day,

                    "页:",

                    index + 1

                )



            else:


                page_has_other_date = True





        # 开始收集

        if page_is_target:


            collecting = True




        # 遇到其它日期

        # 暂停当前段

        elif collecting and page_has_other_date:


            collecting = False





        if collecting:


            pix = page.get_pixmap(

                dpi=180

            )



            name = (

                f"shantu-"

                f"{target_month:02d}-"

                f"{target_day:02d}-"

                f"{count:03d}.jpg"

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

                "保存:",

                name,

                "来源页:",

                index + 1

            )



            count += 1





    doc.close()



    return images
    # =====================
# HTML生成
# =====================


def create_html(

        path,

        title,

        images,

        image_prefix="./"

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

font-family:Microsoft YaHei;

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

font-size:32px;

white-space:nowrap;

overflow:hidden;

text-overflow:ellipsis;

}}



.info{{

text-align:center;

color:#777;

line-height:2;

font-size:18px;

}}



img{{

width:100%;

margin-top:25px;

border-radius:14px;

display:block;

}}



@media(max-width:600px){{


body{{

padding:10px;

}}



.box{{

padding:15px;

}}



h1{{

font-size:26px;

}}



.info{{

font-size:16px;

}}



img{{

margin-top:18px;

}}



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


⏰ 更新时间：

{now}



</div>



"""



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


    cards=[]



    history=sorted(

        [

            x.name

            for x in HISTORY_DIR.iterdir()

            if x.is_dir()

        ],

        reverse=True

    )




    for item in history:


        folder = HISTORY_DIR / item


        images=list(

            folder.glob("*.jpg")

        )


        if not images:

            continue



        cover=(

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

山图集

</title>



<style>


body{{

background:#f5f5f5;

font-family:Microsoft YaHei;

padding:15px;

}}



h1{{

text-align:center;

white-space:nowrap;

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

🌄 山图集

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


    today_date=(

        f"{year}-{month:02d}-{day:02d}"

    )



    today_url=(

        f"{SITE_URL}/history/"

        f"{today_date}/"

    )



    home_url=SITE_URL




    cover_url=(

        today_url + images[0]

        if images

        else ""

    )




    now=get_beijing_time().strftime(

        "%Y-%m-%d %H:%M:%S"

    )





    notify=f"""

## 🏔 今日封面


![]({cover_url})



---



⏰ **生成时间**

{now}



🏠 **山图集主页**

{home_url}

"""



    (

        RESULT_DIR/"notify.txt"

    ).write_text(

        notify,

        encoding="utf-8"

    )





    (

        RESULT_DIR/"cover.txt"

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



    today=get_beijing_time()



    year=today.year

    month=today.month

    day=today.day




    print(

        "当前日期:",

        today

    )





    if not PDF_PATH.exists():


        raise FileNotFoundError(

            f"找不到PDF:{PDF_PATH}"

        )





    today_dir=(

        HISTORY_DIR /

        f"{year}-{month:02d}-{day:02d}"

    )



    today_dir.mkdir(

        exist_ok=True

    )





    # 新版调用方式

    images=search_pdf(

        month,

        day,

        today_dir

    )






    if not images:


        print(

            "今天没有内容"

        )


        create_history_index()


        return







    title=(

        f"🌄 山图集 {month}月{day}日"

    )






    # 今日页面

    create_html(

        today_dir/"index.html",

        title,

        images

    )






    # 网站首页

    create_html(

        RESULT_DIR/"index.html",

        title,

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

        RESULT_DIR/"status.txt"

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






if __name__=="__main__":


    main()
