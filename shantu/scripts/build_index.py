import re
import shutil

from datetime import datetime, timezone, timedelta
from pathlib import Path

import fitz  # PyMuPDF



# =====================
# 基础路径
# =====================

BASE_DIR = Path(__file__).resolve().parent.parent

PDF_PATH = BASE_DIR / "山图集.pdf"

OUTPUT_DIR = BASE_DIR / "result"




# =====================
# 获取北京时间
# =====================

def get_beijing_time():

    beijing = timezone(
        timedelta(hours=8)
    )

    return datetime.now(beijing)





# =====================
# 清理输出目录
# =====================

def clean_output():


    if OUTPUT_DIR.exists():

        shutil.rmtree(
            OUTPUT_DIR
        )


    OUTPUT_DIR.mkdir(
        exist_ok=True
    )





# =====================
# 日期匹配
# =====================

def build_date_regex(month, day):


    pattern = (
        rf"{month}\s*月\s*{day}\s*日"
    )


    return re.compile(pattern)





# =====================
# 搜索PDF
# =====================

def search_pdf(date_regex, month, day):


    result_images = []


    doc = fitz.open(
        PDF_PATH
    )


    for page_index, page in enumerate(doc):


        text = page.get_text()


        clean_text = re.sub(
            r"\s+",
            "",
            text
        )


        if (
            date_regex.search(text)
            or
            date_regex.search(clean_text)
        ):


            print(
                "找到日期页面:",
                page_index + 1
            )


            pix = page.get_pixmap(
                dpi=180
            )


            image_name = (
                f"shantu-{month:02d}-{day:02d}"
                f"-page-{page_index+1}.jpg"
            )


            image_path = (
                OUTPUT_DIR /
                image_name
            )


            pix.save(
                str(image_path)
            )


            result_images.append(
                image_name
            )


            print(
                "生成图片:",
                image_name
            )



    doc.close()


    return result_images






# =====================
# 生成HTML
# =====================

def create_html(month, day, images):


    now = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )



    html = f"""
<!DOCTYPE html>

<html>

<head>

<meta charset="utf-8">


<meta name="viewport"
content="width=device-width, initial-scale=1">



<title>
🌄 山图集 {month}月{day}日
</title>


<style>


body {{

    margin:0;

    padding:20px;

    background:#f5f5f5;

    font-family:

    -apple-system,

    BlinkMacSystemFont,

    "Microsoft YaHei",

    Arial;

}}



.container {{

    max-width:900px;

    margin:auto;

    background:white;

    padding:25px;

    border-radius:16px;

    box-shadow:
    0 4px 20px rgba(0,0,0,.08);

}}



h1 {{

    text-align:center;

    font-size:32px;

    margin-bottom:10px;

}}



.info {{

    text-align:center;

    color:#888;

    line-height:1.8;

    margin-bottom:30px;

}}



.image-box {{

    margin-bottom:35px;

}}



img {{

    width:100%;

    border-radius:12px;

    cursor:pointer;

    transition:.3s;

}}



img:hover {{

    opacity:.85;

}}



.footer {{

    text-align:center;

    color:#999;

    margin-top:30px;

    font-size:14px;

}}



.top {{

    position:fixed;

    right:20px;

    bottom:20px;

    background:#333;

    color:white;

    width:45px;

    height:45px;

    border-radius:50%;

    display:flex;

    align-items:center;

    justify-content:center;

    text-decoration:none;

}}



</style>


</head>



<body>



<div class="container">



<h1>
🌄 山图集 {month}月{day}日
</h1>



<div class="info">


图片数量：
{len(images)} 张


<br>


生成时间：
{now}


<br>


来源：
山图集.pdf


</div>


"""



    for index, img in enumerate(images,1):


        html += f"""


<div class="image-box">


<a href="./{img}" target="_blank">


<img

src="./{img}"

loading="lazy"

alt="山图集第{index}张">


</a>


</div>


"""



    html += f"""


<div class="footer">


GitHub Actions 自动生成


<br>


点击图片查看高清版本


</div>



</div>



<a class="top" href="#">
↑
</a>



</body>


</html>

"""



    index_file = (
        OUTPUT_DIR /
        "index.html"
    )


    index_file.write_text(
        html,
        encoding="utf-8"
    )


    return index_file






# =====================
# 主程序
# =====================

def main():



    today = get_beijing_time()



    month = today.month

    day = today.day



    print("=====================")

    print(
        "日期:",
        month,
        "月",
        day,
        "日"
    )

    print("=====================")




    if not PDF_PATH.exists():


        raise FileNotFoundError(
            f"找不到PDF:{PDF_PATH}"
        )





    clean_output()





    regex = build_date_regex(
        month,
        day
    )



    print(
        "匹配:",
        regex.pattern
    )




    images = search_pdf(
        regex,
        month,
        day
    )




    # =====================
    # 没找到
    # =====================

    if not images:


        print(
            "没有找到对应日期"
        )


        # 生成提示页面

        OUTPUT_DIR.mkdir(
            exist_ok=True
        )


        create_html(
            month,
            day,
            []
        )


        return





    # =====================
    # 生成网页
    # =====================


    index = create_html(
        month,
        day,
        images
    )



    status = (
        OUTPUT_DIR /
        "status.txt"
    )


    status.write_text(
        "FOUND",
        encoding="utf-8"
    )



    print("=====================")

    print(
        "完成"
    )

    print(
        "图片:",
        images
    )


    print(
        "网页:",
        index
    )

    print("=====================")





if __name__ == "__main__":

    main()
