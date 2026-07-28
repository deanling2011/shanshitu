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

    # 测试日期
    # 测试完成后删除这一行
    return datetime(
        2026,
        7,
        24,
        tzinfo=beijing
    )

    # 正式使用：
    # return datetime.now(beijing)



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
# PDF搜索
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


            # 图片质量优化
            pix = page.get_pixmap(
                dpi=150
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


    html = f"""
<!DOCTYPE html>

<html>

<head>

<meta charset="utf-8">

<title>
山图集 {month}月{day}日
</title>


<style>

body {{

    font-family:
    Arial,
    "Microsoft YaHei";

    padding:20px;

}}


h1 {{

    font-size:32px;

}}


img {{

    max-width:95%;

    margin-bottom:30px;

    border:1px solid #ddd;

}}

</style>


</head>


<body>


<h1>
山图集 {month}月{day}日
</h1>

"""


    for img in images:


        html += f"""

<img 
src="./{img}"
loading="lazy">


"""


    html += """

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


    # ===== 正式使用 =====

    today = get_beijing_time()


    # ===== 测试7月24日打开下面两行 =====
    # today = datetime(
    #     2026,
    #     7,
    #     24,
    #     tzinfo=timezone(timedelta(hours=8))
    # )


    month = today.month
    day = today.day


    print("=====================")

    print(
        "今天日期:",
        month,
        "月",
        day,
        "日"
    )

    print("=====================")



    if not PDF_PATH.exists():

        raise FileNotFoundError(
            f"找不到PDF文件:{PDF_PATH}"
        )



    clean_output()



    regex = build_date_regex(
        month,
        day
    )


    print(
        "匹配规则:",
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


        print("=====================")

        print(
            "没有找到:",
            f"{month}月{day}日"
        )


        print(
            "不生成结果"
        )


        print("=====================")


        shutil.rmtree(
            OUTPUT_DIR
        )


        return



    # =====================
    # 找到
    # =====================

    index = create_html(
        month,
        day,
        images
    )


    # 状态文件
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
        "处理完成"
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
