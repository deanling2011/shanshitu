# -*- coding: utf-8 -*-
"""
山师图集「历史上的今天」跨年聚合脚本。

功能：
  1. 解析 山图集.pdf，按「月-日」聚合所有年份的页面（同月日跨年）
  2. 切图为 history/MM-DD/MM-DD-YYYY-NNN.jpg
  3. 生成 history/index.json（月日 -> 年份列表）
  4. 生成日历导航首页 index.html
  5. 生成 PushDeer 通知内容 notify.txt

用法：
  python build_index.py            # 增量：只生成今天月日
  python build_index.py --all      # 全量：生成全部月日
  python build_index.py 10-22      # 指定月日
"""
import sys
import re
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pymupdf

# 1900-2099 每年 24 节气「日」数组（权威历法数据），月份 = index//2+1
TERMS_DATA_JSON = "[[5,20,4,18,5,20,5,20,5,21,5,21,7,23,7,23,7,23,8,23,7,22,7,22],[6,21,4,19,6,21,5,21,6,22,6,22,8,23,8,24,8,24,9,24,8,23,8,22],[6,21,5,19,6,21,6,21,6,22,7,22,8,24,8,24,8,24,9,24,8,23,8,23],[6,21,5,20,7,22,6,21,7,22,7,22,8,24,9,24,9,24,9,24,8,23,8,23],[7,21,5,20,6,21,5,20,6,21,6,22,7,23,8,23,8,23,9,24,8,23,7,22],[6,21,4,19,6,21,5,21,6,22,6,22,8,23,8,24,8,24,9,24,8,23,8,22],[6,21,5,19,6,21,6,21,6,22,6,22,8,24,8,24,8,24,9,24,8,23,8,23],[6,21,5,20,7,22,6,21,7,22,7,22,8,24,9,24,9,24,9,24,8,23,8,23],[7,21,5,20,6,21,5,20,6,21,6,22,7,23,8,23,8,23,9,24,8,23,7,22],[6,21,4,19,6,21,5,21,6,22,6,22,8,23,8,24,8,24,9,24,8,23,8,22],[6,21,5,19,6,21,6,21,6,22,6,22,8,24,8,24,8,24,9,24,8,23,8,23],[6,21,5,20,7,22,6,21,7,22,7,22,8,24,9,24,9,24,9,24,8,23,8,23],[7,21,5,20,6,21,5,20,6,21,6,22,7,23,8,23,8,23,9,24,8,23,7,22],[6,20,4,19,6,21,5,21,6,22,6,22,8,23,8,24,8,24,9,24,8,23,8,22],[6,21,4,19,6,21,5,21,6,22,6,22,8,24,8,24,8,24,9,24,8,23,8,23],[6,21,5,20,6,22,6,21,6,22,7,22,8,24,8,24,9,24,9,24,8,23,8,23],[6,21,5,20,6,21,5,20,6,21,6,22,7,23,8,23,8,23,8,24,8,22,7,22],[6,20,4,19,6,21,5,21,6,21,6,22,8,23,8,24,8,23,9,24,8,23,7,22],[6,21,4,19,6,21,5,21,6,22,6,22,8,24,8,24,8,24,9,24,8,23,8,22],[6,21,5,20,6,22,6,21,6,22,7,22,8,24,8,24,9,24,9,24,8,23,8,23],[6,21,5,20,6,21,5,20,6,21,6,22,7,23,8,23,8,23,8,24,8,22,7,22],[6,20,4,19,6,21,5,20,6,21,6,22,8,23,8,24,8,23,9,24,8,23,7,22],[6,21,4,19,6,21,5,21,6,22,6,22,8,24,8,24,8,24,9,24,8,23,8,22],[6,21,5,19,6,21,6,21,6,22,7,22,8,24,8,24,9,24,9,24,8,23,8,23],[6,21,5,20,6,21,5,20,6,21,6,22,7,23,8,23,8,23,8,24,8,22,7,22],[6,20,4,19,6,21,5,20,6,21,6,22,8,23,8,24,8,23,9,24,8,23,7,22],[6,21,4,19,6,21,5,21,6,22,6,22,8,23,8,24,8,24,9,24,8,23,8,22],[6,21,5,19,6,21,6,21,6,22,7,22,8,24,8,24,8,24,9,24,8,23,8,23],[6,21,5,20,6,21,5,20,6,21,6,21,7,23,8,23,8,23,8,23,7,22,7,22],[6,20,4,19,6,21,5,20,6,21,6,22,7,23,8,23,8,23,9,24,8,23,7,22],[6,21,4,19,6,21,5,21,6,22,6,22,8,23,8,24,8,24,9,24,8,23,8,22],[6,21,5,19,6,21,6,21,6,22,7,22,8,24,8,24,8,24,9,24,8,23,8,23],[6,21,5,20,6,21,5,20,6,21,6,21,7,23,8,23,8,23,8,23,7,22,7,22],[6,20,4,19,6,21,5,20,6,21,6,22,7,23,8,23,8,23,9,24,8,23,7,22],[6,21,4,19,6,21,5,21,6,22,6,22,8,23,8,24,8,24,9,24,8,23,8,22],[6,21,5,19,6,21,6,21,6,22,6,22,8,24,8,24,8,24,9,24,8,23,8,23],[6,21,5,20,6,21,5,20,6,21,6,21,7,23,8,23,8,23,8,23,7,22,7,22],[6,20,4,19,6,21,5,20,6,21,6,22,7,23,8,23,8,23,9,24,8,23,7,22],[6,21,4,19,6,21,5,21,6,22,6,22,8,23,8,24,8,24,9,24,8,23,8,22],[6,21,5,19,6,21,6,21,6,22,6,22,8,24,8,24,8,24,9,24,8,23,8,23],[6,21,5,20,6,21,5,20,6,21,6,21,7,23,8,23,8,23,8,23,7,22,7,22],[6,20,4,19,6,21,5,20,6,21,6,22,7,23,8,23,8,23,9,24,8,23,7,22],[6,21,4,19,6,21,5,21,6,22,6,22,8,23,8,24,8,24,9,24,8,23,8,22],[6,21,5,19,6,21,6,21,6,22,6,22,8,24,8,24,8,24,9,24,8,23,8,23],[6,21,5,20,6,21,5,20,5,21,6,21,7,23,8,23,8,23,8,23,7,22,7,22],[6,20,4,19,6,21,5,20,6,21,6,22,7,23,8,23,8,23,8,24,8,22,7,22],[6,20,4,19,6,21,5,21,6,22,6,22,8,23,8,24,8,23,9,24,8,23,8,22],[6,21,4,19,6,21,5,21,6,22,6,22,8,24,8,24,8,24,9,24,8,23,8,23],[6,21,5,20,5,21,5,20,5,21,6,21,7,23,7,23,8,23,8,23,7,22,7,22],[5,20,4,19,6,21,5,20,6,21,6,22,7,23,8,23,8,23,8,24,8,22,7,22],[6,20,4,19,6,21,5,20,6,21,6,22,8,23,8,24,8,23,9,24,8,23,8,22],[6,21,4,19,6,21,5,21,6,22,6,22,8,24,8,24,8,24,9,24,8,23,8,23],[6,21,5,20,5,21,5,20,5,21,6,21,7,23,7,23,8,23,8,23,7,22,7,22],[5,20,4,19,6,21,5,20,6,21,6,22,7,23,8,23,8,23,8,24,8,22,7,22],[6,20,4,19,6,21,5,20,6,21,6,22,8,23,8,24,8,23,9,24,8,23,7,22],[6,21,4,19,6,21,5,21,6,22,6,22,8,23,8,24,8,24,9,24,8,23,8,22],[6,21,5,20,5,20,5,20,5,21,6,21,7,23,7,23,8,23,8,23,7,22,7,22],[5,20,4,19,6,21,5,20,6,21,6,22,7,23,8,23,8,23,8,24,8,22,7,22],[6,20,4,19,6,21,5,20,6,21,6,22,7,23,8,23,8,23,9,24,8,23,7,22],[6,21,4,19,6,21,5,21,6,22,6,22,8,23,8,24,8,24,9,24,8,23,8,22],[6,21,5,19,5,20,5,20,5,21,6,21,7,23,7,23,7,23,8,23,7,22,7,22],[5,20,4,19,6,21,5,20,6,21,6,21,7,23,8,23,8,23,8,23,7,22,7,22],[6,20,4,19,6,21,5,20,6,21,6,22,7,23,8,23,8,23,9,24,8,23,7,22],[6,21,4,19,6,21,5,21,6,22,6,22,8,23,8,24,8,24,9,24,8,23,8,22],[6,21,5,19,5,20,5,20,5,21,6,21,7,23,7,23,7,23,8,23,7,22,7,22],[5,20,4,19,6,21,5,20,6,21,6,21,7,23,8,23,8,23,8,23,7,22,7,22],[6,20,4,19,6,21,5,20,6,21,6,22,7,23,8,23,8,23,9,24,8,23,7,22],[6,21,4,19,6,21,5,21,6,22,6,22,8,23,8,24,8,24,9,24,8,23,8,22],[6,21,5,19,5,20,5,20,5,21,5,21,7,23,7,23,7,23,8,23,7,22,7,22],[5,20,4,19,6,21,5,20,6,21,6,21,7,23,8,23,8,23,8,23,7,22,7,22],[6,20,4,19,6,21,5,20,6,21,6,22,7,23,8,23,8,23,9,24,8,23,7,22],[6,21,4,19,6,21,5,21,6,22,6,22,8,23,8,24,8,24,9,24,8,23,8,22],[6,21,5,19,5,20,5,20,5,21,5,21,7,23,7,23,7,23,8,23,7,22,7,22],[5,20,4,19,6,21,5,20,5,21,6,21,7,23,8,23,8,23,8,23,7,22,7,22],[6,20,4,19,6,21,5,20,6,21,6,22,7,23,8,23,8,23,9,24,8,23,7,22],[6,21,4,19,6,21,5,21,6,22,6,22,8,23,8,24,8,23,9,24,8,23,8,22],[6,21,5,19,5,20,4,20,5,21,5,21,7,23,7,23,7,23,8,23,7,22,7,22],[5,20,4,19,6,21,5,20,5,21,6,21,7,23,7,23,8,23,8,23,7,22,7,22],[6,20,4,19,6,21,5,20,6,21,6,22,7,23,8,23,8,23,8,24,8,23,7,22],[6,21,4,19,6,21,5,21,6,21,6,22,8,23,8,24,8,23,9,24,8,23,8,22],[6,21,5,19,5,20,4,20,5,21,5,21,7,23,7,23,7,23,8,23,7,22,7,22],[5,20,4,19,6,21,5,20,5,21,6,21,7,23,7,23,8,23,8,23,7,22,7,22],[6,20,4,19,6,21,5,20,6,21,6,22,7,23,8,23,8,23,8,24,8,22,7,22],[6,20,4,19,6,21,5,20,6,21,6,22,8,23,8,24,8,23,9,24,8,23,8,22],[6,21,4,19,5,20,4,20,5,21,5,21,7,22,7,23,7,23,8,23,7,22,7,22],[5,20,4,19,5,21,5,20,5,21,6,21,7,23,7,23,8,23,8,23,7,22,7,22],[5,20,4,19,6,21,5,20,6,21,6,22,7,23,8,23,8,23,8,24,8,22,7,22],[6,20,4,19,6,21,5,20,6,21,6,22,7,23,8,24,8,23,9,24,8,23,7,22],[6,21,4,19,5,20,4,20,5,21,5,21,7,22,7,23,7,23,8,23,7,22,7,21],[5,20,4,19,5,20,5,20,5,21,6,21,7,23,7,23,7,23,8,23,7,22,7,22],[5,20,4,19,6,21,5,20,6,21,6,21,7,23,8,23,8,23,8,24,8,22,7,22],[6,20,4,19,6,21,5,20,6,21,6,22,7,23,8,23,8,23,9,24,8,23,7,22],[6,21,4,19,5,20,4,20,5,21,5,21,7,22,7,23,7,23,8,23,7,22,7,21],[5,20,4,18,5,20,5,20,5,21,6,21,7,23,7,23,7,23,8,23,7,22,7,22],[5,20,4,19,6,21,5,20,6,21,6,21,7,23,8,23,8,23,8,23,7,22,7,22],[6,20,4,19,6,21,5,20,6,21,6,22,7,23,8,23,8,23,9,24,8,23,7,22],[6,21,4,19,5,20,4,20,5,21,5,21,7,22,7,23,7,23,8,23,7,22,7,21],[5,20,4,18,5,20,5,20,5,21,5,21,7,23,7,23,7,23,8,23,7,22,7,22],[5,20,4,19,6,21,5,20,6,21,6,21,7,23,8,23,8,23,8,23,7,22,7,22],[6,20,4,19,6,21,5,20,6,21,6,22,7,23,8,23,8,23,9,24,8,23,7,22],[6,21,4,19,5,20,4,20,5,21,5,21,7,22,7,23,7,23,8,23,7,22,7,21],[5,20,4,18,5,20,5,20,5,21,5,21,7,23,7,23,7,23,8,23,7,22,7,22],[5,20,4,19,6,21,5,20,6,21,6,21,7,23,8,23,8,23,8,23,7,22,7,22],[6,20,4,19,6,21,5,20,6,21,6,22,7,23,8,23,8,23,9,24,8,23,7,22],[6,21,4,19,5,20,4,20,5,21,5,21,7,22,7,23,7,23,8,23,7,22,7,21],[5,20,4,18,5,20,5,20,5,21,5,21,7,23,7,23,7,23,8,23,7,22,7,22],[5,20,4,19,6,21,5,20,5,21,6,21,7,23,7,23,8,23,8,23,7,22,7,22],[6,20,4,19,6,21,5,20,6,21,6,22,7,23,8,23,8,23,9,24,8,23,7,22],[6,21,4,19,5,20,4,20,5,21,5,21,7,22,7,23,7,22,8,23,7,22,7,21],[5,20,4,18,5,20,4,20,5,21,5,21,7,23,7,23,7,23,8,23,7,22,7,22],[5,20,4,19,6,21,5,20,5,21,6,21,7,23,7,23,8,23,8,23,7,22,7,22],[6,20,4,19,6,21,5,20,6,21,6,22,7,23,8,23,8,23,8,24,8,23,7,22],[6,21,4,19,5,20,4,20,5,20,5,21,7,22,7,23,7,22,8,23,7,22,7,21],[5,20,4,18,5,20,4,20,5,21,5,21,7,22,7,23,7,23,8,23,7,22,7,22],[5,20,4,19,6,21,5,20,5,21,6,21,7,23,7,23,8,23,8,23,7,22,7,22],[6,20,4,19,6,21,5,20,6,21,6,22,7,23,8,23,8,23,8,24,8,22,7,22],[6,20,4,19,5,20,4,19,5,20,5,21,7,22,7,23,7,22,8,23,7,22,7,21],[5,20,3,18,5,20,4,20,5,21,5,21,7,22,7,23,7,23,8,23,7,22,7,22],[5,20,4,19,5,21,5,20,5,21,6,21,7,23,7,23,8,23,8,23,7,22,7,22],[5,20,4,19,6,21,5,20,6,21,6,21,7,23,8,23,8,23,8,24,8,22,7,22],[6,20,4,19,5,20,4,19,5,20,5,21,6,22,7,22,7,22,8,23,7,22,7,21],[5,20,3,18,5,20,4,20,5,21,5,21,7,22,7,23,7,23,8,23,7,22,7,21],[5,20,4,19,5,20,5,20,5,21,6,21,7,23,7,23,7,23,8,23,7,22,7,22],[5,20,4,19,6,21,5,20,6,21,6,21,7,23,8,23,8,23,8,24,8,22,7,22],[6,20,4,19,5,20,4,19,5,20,5,21,6,22,7,22,7,22,8,23,7,22,6,21],[5,20,3,18,5,20,4,20,5,21,5,21,7,22,7,23,7,23,8,23,7,22,7,21],[5,20,4,18,5,20,5,20,5,21,5,21,7,23,7,23,7,23,8,23,7,22,7,22],[5,20,4,19,6,21,5,20,6,21,6,21,7,23,8,23,8,23,8,23,7,22,7,22],[6,20,4,19,5,20,4,19,5,20,5,21,6,22,7,22,7,22,8,23,7,22,6,21],[5,20,3,18,5,20,4,20,5,21,5,21,7,22,7,23,7,23,8,23,7,22,7,21],[5,20,4,18,5,20,5,20,5,21,5,21,7,23,7,23,7,23,8,23,7,22,7,22],[5,20,4,19,6,21,5,20,6,21,6,21,7,23,8,23,8,23,8,23,7,22,7,22],[6,20,4,19,5,20,4,19,5,20,5,21,6,22,7,22,7,22,8,23,7,22,6,21],[5,20,3,18,5,20,4,20,5,21,5,21,7,22,7,23,7,23,8,23,7,22,7,21],[5,20,4,18,5,20,5,20,5,21,5,21,7,23,7,23,7,23,8,23,7,22,7,22],[5,20,4,19,6,21,5,20,5,21,6,21,7,23,7,23,8,23,8,23,7,22,7,22],[6,20,4,19,5,20,4,19,5,20,5,21,6,22,7,22,7,22,8,23,7,22,6,21],[5,20,3,18,5,20,4,20,5,21,5,21,7,22,7,23,7,23,8,23,7,22,7,21],[5,20,4,18,5,20,5,20,5,21,5,21,7,23,7,23,7,23,8,23,7,22,7,22],[5,20,4,19,6,21,5,20,5,21,6,21,7,23,7,23,8,23,8,23,7,22,7,22],[6,20,4,19,5,20,4,19,5,20,5,21,6,22,7,22,7,22,8,23,7,22,6,21],[5,20,3,18,5,20,4,20,5,20,5,21,7,22,7,23,7,22,8,23,7,22,7,21],[5,20,4,18,5,20,4,20,5,21,5,21,7,23,7,23,7,23,8,23,7,22,7,22],[5,20,4,19,6,21,5,20,5,21,6,21,7,23,7,23,8,23,8,23,7,22,7,22],[6,20,4,19,5,20,4,19,5,20,5,21,6,22,7,22,7,22,7,23,7,22,6,21],[5,20,3,18,5,20,4,19,5,20,5,21,7,22,7,23,7,22,8,23,7,22,7,21],[5,20,4,18,5,20,4,20,5,21,5,21,7,22,7,23,7,23,8,23,7,22,7,22],[5,20,4,19,6,21,5,20,5,21,6,21,7,23,7,23,8,23,8,23,7,22,7,22],[6,20,4,19,5,20,4,19,5,20,5,20,6,22,7,22,7,22,7,23,7,21,6,21],[5,19,3,18,5,20,4,19,5,20,5,21,6,22,7,22,7,22,8,23,7,22,7,21],[5,20,3,18,5,20,4,20,5,21,5,21,7,22,7,23,7,23,8,23,7,22,7,22],[5,20,4,19,5,20,5,20,5,21,6,21,7,23,7,23,7,23,8,23,7,22,7,22],[5,20,4,19,5,20,4,19,5,20,5,20,6,22,7,22,7,22,7,23,7,21,6,21],[5,19,3,18,5,20,4,19,5,20,5,21,6,22,7,22,7,22,8,23,7,22,7,21],[5,20,3,18,5,20,4,20,5,21,5,21,7,22,7,23,7,23,8,23,7,22,7,22],[5,20,4,19,5,20,5,20,5,21,5,21,7,23,7,23,7,23,8,23,7,22,7,22],[5,20,4,19,5,20,4,19,5,20,5,20,6,22,7,22,7,22,7,23,7,21,6,21],[5,19,3,18,5,20,4,19,5,20,5,21,6,22,7,22,7,22,8,23,7,22,6,21],[5,20,3,18,5,20,4,20,5,21,5,21,7,22,7,23,7,23,8,23,7,22,7,21],[5,20,4,19,5,20,5,20,5,21,5,21,7,23,7,23,7,23,8,23,7,22,7,22],[5,20,4,19,5,20,4,19,5,20,5,20,6,22,7,22,7,22,7,22,6,21,6,21],[5,19,3,18,5,20,4,19,5,20,5,21,6,22,7,22,7,22,8,23,7,22,6,21],[5,20,3,18,5,20,4,20,5,21,5,21,7,22,7,23,7,23,8,23,7,22,7,21],[5,20,4,18,5,20,5,20,5,21,5,21,7,23,7,23,7,23,8,23,7,22,7,22],[5,20,4,19,5,20,4,19,5,20,5,20,6,22,7,22,7,22,7,22,6,21,6,21],[5,19,3,18,5,20,4,19,5,20,5,21,6,22,7,22,7,22,8,23,7,22,6,21],[5,20,3,18,5,20,4,20,5,21,5,21,7,22,7,23,7,23,8,23,7,22,7,21],[5,20,4,18,5,20,5,20,5,21,5,21,7,23,7,23,7,23,8,23,7,22,7,22],[5,20,4,19,5,20,4,19,4,20,5,20,6,22,6,22,7,22,7,22,6,21,6,21],[5,19,3,18,5,20,4,19,5,20,5,21,6,22,7,22,7,22,8,23,7,22,6,21],[5,20,3,18,5,20,4,20,5,20,5,21,7,22,7,23,7,22,8,23,7,22,7,21],[5,20,4,18,5,20,5,20,5,21,5,21,7,23,7,23,7,23,8,23,7,22,7,22],[5,20,4,19,5,20,4,19,4,20,5,20,6,22,6,22,7,22,7,22,6,21,6,21],[5,19,3,18,5,20,4,19,5,20,5,21,6,22,7,22,7,22,7,23,7,22,6,21],[5,20,3,18,5,20,4,20,5,20,5,21,7,22,7,23,7,22,8,23,7,22,7,21],[5,20,4,18,5,20,4,20,5,21,5,21,7,22,7,23,7,23,8,23,7,22,7,22],[5,20,4,19,5,20,4,19,4,20,5,20,6,22,6,22,7,22,7,22,6,21,6,21],[5,19,3,18,5,20,4,19,5,20,5,21,6,22,7,22,7,22,7,23,7,22,6,21],[5,20,3,18,5,20,4,19,5,20,5,21,6,22,7,23,7,22,8,23,7,22,7,21],[5,20,4,18,5,20,4,20,5,21,5,21,7,22,7,23,7,23,8,23,7,22,7,22],[5,20,4,19,5,20,4,19,4,20,5,20,6,22,6,22,7,22,7,22,6,21,6,21],[5,19,3,18,5,20,4,19,5,20,5,20,6,22,7,22,7,22,7,23,7,21,6,21],[5,20,3,18,5,20,4,19,5,20,5,21,6,22,7,22,7,22,8,23,7,22,7,21],[5,20,3,18,5,20,4,20,5,21,5,21,7,22,7,23,7,23,8,23,7,22,7,22],[5,20,4,19,4,19,4,19,4,20,5,20,6,22,6,22,6,22,7,22,6,21,6,21],[4,19,3,18,5,20,4,19,5,20,5,20,6,22,7,22,7,22,7,23,7,21,6,21],[5,19,3,18,5,20,4,19,5,20,5,21,6,22,7,22,7,22,8,23,7,22,7,21],[5,20,3,18,5,20,4,20,5,21,5,21,7,22,7,23,7,23,8,23,7,22,7,22],[5,20,4,19,4,19,4,19,4,20,4,20,6,22,6,22,6,22,7,22,6,21,6,21],[4,19,3,18,5,20,4,19,5,20,5,20,6,22,7,22,7,22,7,23,7,21,6,21],[5,19,3,18,5,20,4,19,5,20,5,21,6,22,7,22,7,22,8,23,7,22,6,21],[5,20,3,18,5,20,4,20,5,21,5,21,7,22,7,23,7,23,8,23,7,22,7,21],[5,20,4,19,4,19,4,19,4,20,4,20,6,22,6,22,6,22,7,22,6,21,6,21],[4,19,3,18,5,20,4,19,5,20,5,20,6,22,7,22,7,22,7,22,6,21,6,21],[5,19,3,18,5,20,4,19,5,20,5,21,6,22,7,22,7,22,8,23,7,22,6,21],[5,20,3,18,5,20,4,20,5,21,5,21,7,22,7,23,7,23,8,23,7,22,7,21],[5,20,4,18,4,19,4,19,4,20,4,20,6,22,6,22,6,22,7,22,6,21,6,21],[4,19,3,18,5,20,4,19,5,20,5,20,6,22,6,22,7,22,7,22,6,21,6,21],[5,19,3,18,5,20,4,19,5,20,5,21,6,22,7,22,7,22,8,23,7,22,6,21],[5,20,3,18,5,20,4,20,5,21,5,21,7,22,7,23,7,23,8,23,7,22,7,21]]"

# ===================== 路径 =====================
BASE_DIR = Path(__file__).resolve().parent.parent
PDF_PATH = BASE_DIR / "山图集.pdf"
RESULT_DIR = BASE_DIR / "result"
HISTORY_DIR = RESULT_DIR / "history"

SITE_URL = "https://deanling2011.github.io/shanshitu"

DATE_PATTERN = re.compile(r"(\d{4})\s*年\s*(\d+)\s*月\s*(\d+)\s*日")


def get_beijing_time():
    tz = timezone(timedelta(hours=8))
    return datetime.now(tz)


def init_dirs():
    RESULT_DIR.mkdir(exist_ok=True)
    HISTORY_DIR.mkdir(exist_ok=True)


# ===================== PDF 解析 =====================
# 日期出现在文本块「开头」才算新微博条目；出现在「（注：...）」等句子中间的
# 日期只是被提及，不能作为分条依据。
BLOCK_DATE_RE = re.compile(r"^\s*(\d{4})\s*年\s*(\d+)\s*月\s*(\d+)\s*日")


def _split_page_segments(page):
    """
    把一页 PDF 按「日期块」切成若干纵向片段，用于一页含多条不同日期微博的情况
    （例如 10-29 页下半部分其实是 11-03 的一条配图微博）。

    返回 [(year, month, day, clip_or_None, text), ...]
      - clip 为 None 表示整页切图（该页只属于一个日期）
      - 否则 clip = (x0, y0, x1, y1)（PDF 坐标，单位 pt）
      - text 为该片段自己的文字（用于判断"配有照片"注解归属）
    没有以日期开头的文本块时返回 []。
    """
    marks = []
    blocks = [(b[1], b[3], b[4] or "") for b in page.get_text("blocks")]
    for y0, y1, txt in blocks:
        m = BLOCK_DATE_RE.match(txt)
        if m:
            marks.append((y0, y1, int(m.group(1)), int(m.group(2)), int(m.group(3))))
    if not marks:
        return []
    marks.sort()  # PDF 文本块顺序可能被页脚等打乱，按 y 排序

    uniq = []
    for _, _, y, mo, d in marks:
        if (y, mo, d) not in uniq:
            uniq.append((y, mo, d))
    if len(uniq) <= 1:
        _, _, y, mo, d = marks[0]
        return [(y, mo, d, None, page.get_text())]

    # 收集所有内容（文本块 + 图片）的纵向范围，用于计算切分边界
    contents = [(y0, y1) for y0, y1, txt in blocks if txt.strip()]
    for img in page.get_images(full=True):
        for r in page.get_image_rects(img[0]):
            contents.append((r.y0, r.y1))

    page_w = page.rect.width
    page_h = page.rect.height
    pad = 12.0

    # 相邻两个日期块之间的边界 = (上一段内容底部 + 下一个日期块顶部) / 2
    bounds = []
    for k in range(1, len(marks)):
        next_top = marks[k][0]
        prev_bottom = max([y1 for y0, y1 in contents if y1 <= next_top] or [next_top - pad * 2])
        bounds.append((prev_bottom + next_top) / 2.0)

    segments = []
    for k, (m_y0, m_y1, y, mo, d) in enumerate(marks):
        top = 0.0 if k == 0 else bounds[k - 1]
        if k < len(bounds):
            bottom = bounds[k]
        else:  # 最后一段：切到内容底部，避免大片空白
            bottom = max([y1 for y0, y1 in contents if y1 >= top] or [m_y1]) + pad
            bottom = min(bottom, page_h)
        if bottom - top < 20:  # 太小视为页脚/页码等噪声
            continue
        seg_text = "\n".join(txt for y0, y1, txt in blocks if top <= y0 < bottom)
        segments.append((y, mo, d, (0.0, top, page_w, bottom), seg_text))
    return segments


def analyze_pdf():
    """
    扫描整个 PDF，返回 md_map: {(month, day): [(year, [segment, ...]), ...]}
    segment = (page_index, clip_or_None)

    归属规则：
      - 有日期文字的页 → 新建一条微博条目（该页该片段为文字说明页）。
      - 一页含多条不同日期的微博（上半页 A 日期、下半页 B 日期）→ 纵向切开，
        各自归属自己的日期，不再把后面的日期吞进前一个日期。
      - 无日期但含图片的页（如纯照片页、紧跟的"注"说明页）→ 归属到
        「紧前一条」微博条目，作为附加图片页，直到遇到下一个日期文字为止。
        若紧前一条没提到"配图/配有照片"，则在同一页的条目里往前找提到的那条
        （例如第75页上半是"取名纸照片"的注解，下半又挤了 01-14 一条，
        照片页应归前者而不是 01-14）。
    """
    doc = pymupdf.open(PDF_PATH)
    md_map = {}
    last_pages = None    # 最近一条微博的片段列表引用（用于追加无日期图片页）
    page_entries = []    # 最近一个文字页上的条目 [(片段列表, 归一化文本), ...]

    def norm(s):
        return re.sub(r"\s+", "", s or "")

    for i, page in enumerate(doc):
        segs = _split_page_segments(page)
        if segs:
            page_entries = []
            # 相邻同日期片段合并为同一条微博，保留条目数语义
            groups = []
            for y, mo, d, clip, txt in segs:
                if groups and groups[-1][0] == (y, mo, d):
                    groups[-1][1].append((i, clip))
                    groups[-1][2] += "\n" + txt
                else:
                    groups.append([(y, mo, d), [(i, clip)], txt])
            for (y, mo, d), seg_list, txt in groups:
                key = (mo, d)
                md_map.setdefault(key, []).append((y, seg_list))
                last_pages = seg_list
                page_entries.append((seg_list, norm(txt)))
        else:
            # 兼容：日期不在文本块开头时，沿用全文首个日期（整页归属）
            text = page.get_text()
            dates = DATE_PATTERN.findall(text)
            if dates:
                y, m, d = dates[0]
                key = (int(m), int(d))
                seg_list = [(i, None)]
                md_map.setdefault(key, []).append((int(y), seg_list))
                last_pages = seg_list
                page_entries = [(seg_list, norm(text))]
                continue
            # 无日期：若该页含图片，则挂到「紧前一条」微博的片段列表末尾
            if last_pages is None:
                continue
            if not page.get_images(full=True):
                continue
            target = None
            for seg_list, txt in reversed(page_entries):
                if "配有照片" in txt or "配图" in txt:
                    target = seg_list
                    break
            if target is None:
                target = last_pages
            target.append((i, None))
    doc.close()
    return md_map


def cut_page_to_jpg(doc, page_index, out_path, dpi=180, clip=None):
    page = doc[page_index]
    if clip:
        pix = page.get_pixmap(dpi=dpi, clip=pymupdf.Rect(*clip))
    else:
        pix = page.get_pixmap(dpi=dpi)
    pix.save(str(out_path))
    return out_path


def build_monthday(md_key, md_map, doc):
    """
    切某个月日的图，返回 (图片文件名列表, 年份列表)。
    doc 为 None 时只统计（用于通知）。

    每条微博可能对应多页（文字页 + 图片页），每页各切一张，连续编号。
    """
    month, day = md_key
    entries = md_map[md_key]  # [(year, [(page_index, clip), ...]), ...]
    folder = HISTORY_DIR / f"{month:02d}-{day:02d}"
    folder.mkdir(exist_ok=True)

    year_counter = {}
    images = []
    years_seen = []
    for year, segments in entries:
        for page_idx, clip in segments:
            year_counter[year] = year_counter.get(year, 0) + 1
            seq = year_counter[year]
            name = f"{month:02d}-{day:02d}-{year}-{seq:03d}.jpg"
            out = folder / name
            if doc is not None:
                if not out.exists():
                    cut_page_to_jpg(doc, page_idx, out, clip=clip)
            images.append(name)
            if year not in years_seen:
                years_seen.append(year)

    return images, years_seen


# ===================== 索引 JSON =====================
def build_index_json(md_map):
    index = {}
    for (month, day), entries in sorted(md_map.items()):
        key = f"{month:02d}-{day:02d}"
        years = sorted({y for y, _ in entries})
        index[key] = {"count": len(entries), "years": years}
    with open(HISTORY_DIR / "index.json", "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False)
    return index


# ===================== 日历导航首页 =====================
def build_calendar_html(index):
    index_json = json.dumps(index, ensure_ascii=False)
    html = CALENDAR_TEMPLATE.replace("__INDEX_JSON__", index_json)
    html = html.replace("__TERMS_DATA__", TERMS_DATA_JSON)
    (RESULT_DIR / "index.html").write_text(html, encoding="utf-8")
    return RESULT_DIR / "index.html"


CALENDAR_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<title>山师图集 · 历史上的今天</title>
<style>
  :root {
    --bg: #0f1115; --bg-soft: #161922; --card: #1b1f2a; --card-hover: #222837;
    --border: #2a3040; --text: #e8eaf0; --text-dim: #9aa3b2;
    --accent: #d4a25a; --accent-soft: rgba(212,162,90,.12); --radius: 14px;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  html { -webkit-text-size-adjust: 100%; }
  body { background: var(--bg); color: var(--text); min-height: 100vh;
    font-family: -apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;
    line-height: 1.7; padding-bottom: env(safe-area-inset-bottom); }
  .wrap { max-width: 760px; margin: 0 auto; padding: 16px 16px 48px; }
  header.top { display:flex; align-items:center; justify-content:space-between; padding:12px 0 20px; }
  .brand { font-size:18px; font-weight:700; letter-spacing:1px; }
  .brand small { display:block; font-size:11px; color:var(--text-dim); font-weight:400; letter-spacing:2px; }
  .switcher { display:flex; align-items:center; gap:3px; padding:3px; background:var(--card);
    border:1px solid var(--border); border-radius:999px; box-shadow:0 4px 16px rgba(0,0,0,.28);
    flex-shrink:0; animation:swIn .5s ease both; }
  @keyframes swIn { from { opacity:0; transform:translateY(-8px); } to { opacity:1; transform:none; } }
  .switcher .sw { display:inline-flex; align-items:center; gap:5px; padding:6px 13px; border-radius:999px;
    font-size:13px; font-weight:600; letter-spacing:.5px; color:var(--text-dim); text-decoration:none;
    cursor:pointer; transition:color .2s,background .2s,box-shadow .2s,transform .2s; white-space:nowrap; position:relative; }
  .switcher .sw:hover { color:var(--text); }
  .switcher .sw:not(.active):hover { transform:translateY(-1px); }
  .switcher .sw.active { background:linear-gradient(135deg,var(--accent),#e6bb7a); color:#1a1408;
    cursor:default; box-shadow:0 2px 10px rgba(212,162,90,.42); }
  .switcher .sw .arrow { font-size:11px; line-height:1; opacity:0; transform:translate(-3px,3px); transition:all .2s ease; }
  .switcher .sw:not(.active):hover .arrow { opacity:1; transform:translate(0,0); }
  @media (max-width:420px) { .switcher .sw { padding:5px 10px; font-size:12px; gap:3px; } .brand { font-size:16px; } }
  .today-card { background:linear-gradient(135deg,#1e2433,#161922); border:1px solid var(--border);
    border-radius:var(--radius); padding:20px; margin-bottom:20px; position:relative; overflow:hidden; }
  .today-card::before { content:''; position:absolute; top:-40px; right:-40px; width:140px; height:140px;
    border-radius:50%; background:var(--accent-soft); filter:blur(30px); }
  .today-label { font-size:12px; color:var(--accent); letter-spacing:3px; margin-bottom:6px; }
  .today-date { font-size:26px; font-weight:700; }
  .today-meta { font-size:13px; color:var(--text-dim); margin-top:4px; }
  .today-actions { margin-top:14px; display:flex; gap:10px; flex-wrap:wrap; }
  .btn { display:inline-block; padding:9px 18px; border-radius:10px; font-size:14px; font-weight:600;
    text-decoration:none; cursor:pointer; border:1px solid var(--border); color:var(--text);
    background:var(--card); transition:all .15s; }
  .btn:hover { background:var(--card-hover); }
  .btn.primary { background:var(--accent); color:#1a1408; border-color:var(--accent); }
  .section-title { font-size:15px; font-weight:700; margin:22px 0 12px; }
  .section-title .hint { font-size:12px; color:var(--text-dim); font-weight:400; margin-left:8px; }
  .nav-month { display:flex; gap:8px; overflow-x:auto; padding-bottom:8px; -webkit-overflow-scrolling:touch; scrollbar-width:none; }
  .nav-month::-webkit-scrollbar { display:none; }
  .nav-month button { flex:0 0 auto; padding:7px 14px; border-radius:20px; border:1px solid var(--border);
    background:var(--card); color:var(--text-dim); font-size:13px; cursor:pointer; white-space:nowrap; transition:all .15s; }
  .nav-month button.active { background:var(--accent); color:#1a1408; border-color:var(--accent); font-weight:600; }
  .week-head { display:grid; grid-template-columns:repeat(7,1fr); gap:6px; margin-bottom:6px; }
  .week-head span { text-align:center; font-size:11px; color:var(--text-dim); padding:3px 0; }
  .day-grid { display:grid; grid-template-columns:repeat(7,1fr); gap:6px; }
  .day-cell { aspect-ratio:1; display:flex; flex-direction:column; align-items:center; justify-content:center;
    border-radius:10px; background:var(--card); border:1px solid var(--border); cursor:pointer; transition:all .12s; position:relative; }
  .day-cell:hover { background:var(--card-hover); }
  .day-cell .d { font-size:16px; font-weight:600; line-height:1.15; }
  .day-cell .lunar { font-size:10px; color:var(--text-dim); margin-top:3px; line-height:1.2; }
  .day-cell .lunar.fest { color:#e0a06a; }
  .day-cell .lunar.fest-red { color:#e05252; }
  .day-cell .term-pill { font-size:10px; color:#6fce9d; background:#1d3a2e; padding:1px 5px; border-radius:8px; margin-top:3px; line-height:1.3; }
  .day-cell .holiday-tag { position:absolute; top:2px; left:2px; font-size:9px; line-height:1; padding:1px 3px; border-radius:4px; }
  .day-cell .holiday-tag.rest { color:#85b7eb; background:#17324a; }
  .day-cell .holiday-tag.work { color:#f0a06a; background:#3a2418; }
  .day-cell .dot-ind { position:absolute; top:6px; right:6px; width:5px; height:5px; border-radius:50%; background:var(--accent); }
  .day-cell.empty { background:transparent; border-color:transparent; cursor:default; }
  .day-cell.no-data { opacity:.35; cursor:default; }
  /* 今天：淡金细圈，只作"今天在哪"的定位参考，不抢视觉 */
  .day-cell.today { border-color:rgba(212,162,90,.42); }
  .day-cell.today .d { color:var(--accent); }
  /* 选中：当前正在看的那天，实心高亮。写在 .today 之后，同时命中时以选中为准 */
  .day-cell.selected { border-color:var(--accent); background:rgba(212,162,90,.13);
    box-shadow:0 0 0 1.5px var(--accent),0 4px 14px rgba(212,162,90,.20); }
  .day-cell.selected .d { color:var(--accent); }
  .collection { display:none; }
  .collection.show { display:block; }
  .coll-head { display:flex; align-items:center; justify-content:space-between; margin-bottom:14px; }
  .coll-title { font-size:18px; font-weight:700; }
  .coll-back { font-size:13px; color:var(--accent); cursor:pointer; }
  .year-group { margin-bottom:20px; }
  .year-tag { display:inline-block; padding:3px 12px; border-radius:8px; font-size:13px; font-weight:700;
    background:var(--accent-soft); color:var(--accent); margin-bottom:10px; }
  .item { background:var(--card); border:1px solid var(--border); border-radius:12px; padding:8px; margin-bottom:10px; }
  .item img { width:100%; border-radius:8px; display:block; }
  .loading { text-align:center; color:var(--text-dim); padding:40px 0; font-size:14px; }
  footer { text-align:center; color:var(--text-dim); font-size:12px; margin-top:40px; }
</style>
</head>
<body>
<div class="wrap">
  <header class="top">
    <div class="brand">山师图集<span style="color:var(--accent)">·</span><small>历史上的今天</small></div>
    <nav class="switcher" aria-label="站点导航">
      <a class="sw" href="https://deanling2011.github.io/shanshiwen/" target="_blank" rel="noopener" title="前往山师文集">📖 文集<span class="arrow">↗</span></a>
      <span class="sw active">🖼️ 图集</span>
    </nav>
  </header>

  <div class="today-card">
    <div class="today-label">TODAY · 今日</div>
    <div class="today-date" id="todayDate"></div>
    <div class="today-meta" id="todayMeta">加载中…</div>
    <div class="today-actions">
      <a class="btn primary" id="todayRead" href="#">查看今日图集</a>
    </div>
  </div>

  <div class="section-title">按月浏览<span class="hint" id="navHint"></span></div>
  <div class="nav-month" id="navMonth"></div>
  <div class="section-title">选择日期<span class="hint">金点 = 有图集 · 休/班 = 法定调休</span></div>
  <div class="week-head" id="weekHead"></div>
  <div class="day-grid" id="dayGrid"></div>

  <div class="collection" id="collection">
    <div class="coll-head">
      <div class="coll-title" id="collTitle"></div>
      <div class="coll-back" id="collBack">← 返回日历</div>
    </div>
    <div id="collBody"></div>
  </div>

  <footer>
    <div>数据区间 <span id="footRange"></span></div>
  </footer>
</div>

<script>
(function(){
  var INDEX = __INDEX_JSON__;
  var curMonth = null;
  var curSelected = null;   // 当前正在查看的 MM-DD

  /* ===== 农历算法（1900-2100） ===== */
  var LUNAR_INFO = [
    0x04bd8,0x04ae0,0x0a570,0x054d5,0x0d260,0x0d950,0x16554,0x056a0,0x09ad0,0x055d2,
    0x04ae0,0x0a5b6,0x0a4d0,0x0d250,0x1d255,0x0b540,0x0d6a0,0x0ada2,0x095b0,0x14977,
    0x04970,0x0a4b0,0x0b4b5,0x06a50,0x06d40,0x1ab54,0x02b60,0x09570,0x052f2,0x04970,
    0x06566,0x0d4a0,0x0ea50,0x06e95,0x05ad0,0x02b60,0x186e3,0x092e0,0x1c8d7,0x0c950,
    0x0d4a0,0x1d8a6,0x0b550,0x056a0,0x1a5b4,0x025d0,0x092d0,0x0d2b2,0x0a950,0x0b557,
    0x06ca0,0x0b550,0x15355,0x04da0,0x0a5b0,0x14573,0x052b0,0x0a9a8,0x0e950,0x06aa0,
    0x0aea6,0x0ab50,0x04b60,0x0aae4,0x0a570,0x05260,0x0f263,0x0d950,0x05b57,0x056a0,
    0x096d0,0x04dd5,0x04ad0,0x0a4d0,0x0d4d4,0x0d250,0x0d558,0x0b540,0x0b6a0,0x195a6,
    0x095b0,0x049b0,0x0a974,0x0a4b0,0x0b27a,0x06a50,0x06d40,0x0af46,0x0ab60,0x09570,
    0x04af5,0x04970,0x064b0,0x074a3,0x0ea50,0x06b58,0x05ac0,0x0ab60,0x096d5,0x092e0,
    0x0c960,0x0d954,0x0d4a0,0x0da50,0x07552,0x056a0,0x0abb7,0x025d0,0x092d0,0x0cab5,
    0x0a950,0x0b4a0,0x0baa4,0x0ad50,0x055d9,0x04ba0,0x0a5b0,0x15176,0x052b0,0x0a930,
    0x07954,0x06aa0,0x0ad50,0x05b52,0x04b60,0x0a6e6,0x0a4e0,0x0d260,0x0ea65,0x0d530,
    0x05aa0,0x076a3,0x096d0,0x04afb,0x04ad0,0x0a4d0,0x1d0b6,0x0d250,0x0d520,0x0dd45,
    0x0b5a0,0x056d0,0x055b2,0x049b0,0x0a577,0x0a4b0,0x0aa50,0x1b255,0x06d20,0x0ada0,
    0x14b63,0x09370,0x049f8,0x04970,0x064b0,0x168a6,0x0ea50,0x06b20,0x1a6c4,0x0aae0,
    0x092e0,0x0d2e3,0x0c960,0x0d557,0x0d4a0,0x0da50,0x05d55,0x056a0,0x0a6d0,0x055d4,
    0x052d0,0x0a9b8,0x0a950,0x0b4a0,0x0b6a6,0x0ad50,0x055a0,0x0aba4,0x0a5b0,0x052b0,
    0x0b273,0x06930,0x07337,0x06aa0,0x0ad50,0x14b55,0x04b60,0x0a570,0x054e4,0x0d160,
    0x0e968,0x0d520,0x0daa0,0x16aa6,0x056d0,0x04ae0,0x0a9d4,0x0a2d0,0x0d150,0x0f252,
    0x0d520
  ];
  var TERM_NAMES = ["小寒","大寒","立春","雨水","惊蛰","春分","清明","谷雨","立夏","小满",
    "芒种","夏至","小暑","大暑","立秋","处暑","白露","秋分","寒露","霜降",
    "立冬","小雪","大雪","冬至"];
  var TERMS_DATA = __TERMS_DATA__;
  var LUNAR_MONTHS = ["","正月","二月","三月","四月","五月","六月","七月","八月","九月","十月","冬月","腊月"];
  var LUNAR_DAY = ["初一","初二","初三","初四","初五","初六","初七","初八","初九","初十",
    "十一","十二","十三","十四","十五","十六","十七","十八","十九","二十",
    "廿一","廿二","廿三","廿四","廿五","廿六","廿七","廿八","廿九","三十"];
  var LUNAR_FEST = {"1-1":"春节","1-15":"元宵节","5-5":"端午节","7-7":"七夕","8-15":"中秋节","9-9":"重阳节","12-8":"腊八节"};
  var SOLAR_FEST = {"1-1":"元旦","2-14":"情人节","5-1":"劳动节","10-1":"国庆节","10-31":"万圣夜","12-24":"平安夜","12-25":"圣诞节"};
  var HOLIDAY = {
    2026: {
      "1-1":"休","1-2":"休","1-3":"休",
      "2-15":"休","2-16":"休","2-17":"休","2-18":"休","2-19":"休","2-20":"休","2-21":"休","2-22":"休","2-23":"休",
      "4-4":"休","4-5":"休","4-6":"休",
      "5-1":"休","5-2":"休","5-3":"休","5-4":"休","5-5":"休",
      "6-19":"休","6-20":"休","6-21":"休",
      "9-25":"休","9-26":"休","9-27":"休",
      "10-1":"休","10-2":"休","10-3":"休","10-4":"休","10-5":"休","10-6":"休","10-7":"休",
      "1-4":"班","2-14":"班","2-28":"班","5-9":"班","9-20":"班","10-10":"班"
    }
  };

  function lYearDays(y){
    var i, sum = 348;
    for (i = 0x8000; i > 0x8; i >>= 1) sum += (LUNAR_INFO[y-1900] & i) ? 1 : 0;
    return sum + leapDays(y);
  }
  function leapMonth(y){ return LUNAR_INFO[y-1900] & 0xf; }
  function leapDays(y){ if (leapMonth(y)) return (LUNAR_INFO[y-1900] & 0x10000) ? 30 : 29; return 0; }
  function monthDays(y, m){ return (LUNAR_INFO[y-1900] & (0x10000 >> m)) ? 30 : 29; }
  function solar2lunar(y, m, d){
    var offset = Math.floor((Date.UTC(y, m-1, d) - Date.UTC(1900, 0, 31)) / 86400000);
    var i, temp = 0, leap;
    for (i = 1900; i < 2101 && offset > 0; i++){ temp = lYearDays(i); offset -= temp; }
    if (offset < 0){ offset += temp; i--; }
    var year = i;
    leap = leapMonth(i);
    var isLeap = false;
    for (i = 1; i < 13 && offset > 0; i++){
      if (leap > 0 && i === (leap+1) && !isLeap){ --i; isLeap = true; temp = leapDays(year); }
      else { temp = monthDays(year, i); }
      if (isLeap && i === (leap+1)) isLeap = false;
      offset -= temp;
    }
    if (offset === 0 && leap > 0 && i === leap+1){ if (isLeap){ isLeap = false; } else { isLeap = true; --i; } }
    if (offset < 0){ offset += temp; --i; }
    return { lm: i, ld: offset + 1, leap: isLeap };
  }
  function lunarLabel(lm, ld, leap){
    if (ld === 1) return (leap ? '闰' : '') + LUNAR_MONTHS[lm];
    return LUNAR_DAY[ld-1];
  }
  function getTermName(y, m, d){
    var arr = TERMS_DATA[y-1900];
    if (!arr) return null;
    for (var n = 0; n < 24; n++){
      if (Math.floor(n/2) + 1 === m && arr[n] === d) return TERM_NAMES[n];
    }
    return null;
  }
  function getFestival(y, m, d, l){
    var key = l.lm + '-' + l.ld;
    if (LUNAR_FEST[key]) return LUNAR_FEST[key];
    if (l.lm === 12 && l.ld === monthDays(y, 12)) return '除夕';
    var skey = m + '-' + d;
    if (SOLAR_FEST[skey]) return SOLAR_FEST[skey];
    return null;
  }
  function getHoliday(y, m, d){
    var yt = HOLIDAY[y];
    if (!yt) return null;
    return yt[m + '-' + d] || null;
  }
  function cellSub(y, m, d, l){
    var fest = getFestival(y, m, d, l);
    if (fest){
      var red = (fest === '春节' || fest === '国庆节' || fest === '元旦');
      return { text: fest, cls: 'lunar ' + (red ? 'fest-red' : 'fest') };
    }
    var term = getTermName(y, m, d);
    if (term) return { text: term, cls: 'term-pill' };
    return { text: lunarLabel(l.lm, l.ld, l.leap), cls: 'lunar' };
  }

  function pad(n){ return n<10?'0'+n:''+n; }
  function todayMd(){ var t=new Date(); return pad(t.getMonth()+1)+'-'+pad(t.getDate()); }
  function fullToday(){ var t=new Date(); return t.getFullYear()+'年'+(t.getMonth()+1)+'月'+t.getDate()+'日'; }

  function init(){
    var t = new Date();
    curMonth = t.getMonth();
    document.getElementById('todayDate').textContent = fullToday();
    buildWeekHead();
    var md = todayMd();
    var c = INDEX[md] ? INDEX[md].count : 0;
    document.getElementById('todayMeta').textContent =
      c>0 ? ('历年今日共 '+c+' 张 · '+INDEX[md].years.length+' 个年份') : '这一天暂无图集';
    document.getElementById('todayRead').onclick = function(e){ e.preventDefault(); showCollection(md); };

    // 底部数据区间：统计 INDEX 中覆盖的最小/最大日期（年月日完整）
    var minD='', maxD='';
    for (var k in INDEX) {
      var ys = INDEX[k].years || [];
      for (var i=0;i<ys.length;i++) {
        var full = ys[i] + '-' + k;          // k 为 MM-DD
        if (!minD || full < minD) minD = full;
        if (!maxD || full > maxD) maxD = full;
      }
    }
    if (maxD) {
      document.getElementById('footRange').textContent = minD + ' ~ ' + maxD;
    }

    buildMonthNav(); renderGrid(); showCollection(md);
  }

  function buildMonthNav(){
    var nav = document.getElementById('navMonth'); nav.innerHTML='';
    var names=['1月','2月','3月','4月','5月','6月','7月','8月','9月','10月','11月','12月'];
    for(var i=0;i<12;i++){
      (function(m){ var b=document.createElement('button'); b.textContent=names[m];
        if(m===curMonth) b.className='active';
        b.onclick=function(){ curMonth=m; buildMonthNav(); renderGrid(); };
        nav.appendChild(b); })(i);
    }
    // 将当前月按钮滚动到可视区域中间
    var active = nav.querySelector('button.active');
    if (active) {
      var target = active.offsetLeft - (nav.clientWidth - active.offsetWidth) / 2;
      nav.scrollLeft = Math.max(0, target);
    }
  }

  function buildWeekHead(){
    var wh = document.getElementById('weekHead'); wh.innerHTML='';
    var days = ['一','二','三','四','五','六','日'];
    for (var i=0;i<7;i++){ var s=document.createElement('span'); s.textContent=days[i]; wh.appendChild(s); }
  }

  function renderGrid(){
    var grid=document.getElementById('dayGrid'); grid.innerHTML='';
    var t=new Date();
    var year = t.getFullYear();
    var firstDay=(new Date(year,curMonth,1).getDay()+6)%7;
    var days=new Date(year,curMonth+1,0).getDate();
    document.getElementById('navHint').textContent = (curMonth+1)+'月 · 共 '+days+' 天';
    for(var i=0;i<firstDay;i++){ var e=document.createElement('div'); e.className='day-cell empty'; grid.appendChild(e); }
    for(var d=1;d<=days;d++){
      (function(day){
        var md=pad(curMonth+1)+'-'+pad(day);
        var cell=document.createElement('div'); cell.className='day-cell';
        var has=INDEX[md];
        if(!has) cell.classList.add('no-data');
        var dn=document.createElement('span'); dn.className='d'; dn.textContent=day; cell.appendChild(dn);
        var l = solar2lunar(year, curMonth+1, day);
        var sub = cellSub(year, curMonth+1, day, l);
        var sp=document.createElement('span'); sp.className=sub.cls; sp.textContent=sub.text; cell.appendChild(sp);
        if(has){ var dot=document.createElement('span'); dot.className='dot-ind'; cell.appendChild(dot); }
        var h = getHoliday(year, curMonth+1, day);
        if(h){ var tag=document.createElement('span'); tag.className='holiday-tag '+(h==='休'?'rest':'work'); tag.textContent=h; cell.appendChild(tag); }
        if(curMonth===t.getMonth() && day===t.getDate()) cell.classList.add('today');
        cell.setAttribute('data-md', md);
        if(md===curSelected) cell.classList.add('selected');
        if(has) cell.onclick=function(){ showCollection(md); };
        grid.appendChild(cell);
      })(d);
    }
  }

  function syncSelection(){
    var cells = document.getElementById('dayGrid').children;
    for (var i=0;i<cells.length;i++){
      var md = cells[i].getAttribute('data-md');
      cells[i].classList.toggle('selected', !!md && md===curSelected);
    }
  }

  function showCollection(md){
    curSelected = md;
    syncSelection();
    var coll=document.getElementById('collection'); coll.classList.add('show');
    document.getElementById('collTitle').textContent = md.replace('-','月')+'日 · 历年图集';
    document.getElementById('collBack').onclick=function(){ curSelected=null; syncSelection(); coll.classList.remove('show'); window.scrollTo({top:0,behavior:'smooth'}); };
    var body=document.getElementById('collBody');
    body.innerHTML='<div class="loading">加载中…</div>';
    // 不再强制 window.scrollTo(top:0)：点日期时页面停在原处，交给金圈做反馈
    var info=INDEX[md];
    if(!info){ body.innerHTML='<div class="loading">这一天暂无图集</div>'; return; }
    var html='';
    var years=info.years;
    years.forEach(function(y){
      html+='<div class="year-group"><span class="year-tag">'+y+' 年</span>';
      // 每年独立编号，最多 30 张（够用），加载失败自动隐藏
      for(var i=1;i<=30;i++){
        var seq=(i<10?'00'+i:(i<100?'0'+i:''+i));
        var name=md+'-'+y+'-'+seq+'.jpg';
        html+='<div class="item"><img loading="lazy" src="./history/'+md+'/'+name+'" onerror="this.parentNode.style.display=\'none\'"></div>';
      }
      html+='</div>';
    });
    body.innerHTML=html;
  }

  init();
})();
</script>
</body>
</html>
"""


# ===================== PushDeer 通知 =====================
def create_notify(month, day, images, years):
    today = get_beijing_time()
    md = f"{month:02d}-{day:02d}"
    cover = f"{SITE_URL}/history/{md}/{images[0]}" if images else ""
    home = SITE_URL
    now = today.strftime("%Y-%m-%d %H:%M:%S")
    notify = (
        f"## 🏔 山师图集 {month}月{day}日\n"
        f"历年今日共 {len(images)} 张图集，覆盖 {len(years)} 个年份。\n\n"
        f"![封面]({cover})\n\n"
        f"📖 [查看今日图集]({home})\n"
        f"⏰ 生成时间 {now}"
    )
    (RESULT_DIR / "notify.txt").write_text(notify, encoding="utf-8")
    (RESULT_DIR / "cover.txt").write_text(cover, encoding="utf-8")


# ===================== 主程序 =====================
def main():
    print("=" * 20)
    print("山师图集「历史上的今天」")
    print("=" * 20)

    init_dirs()

    if not PDF_PATH.exists():
        raise FileNotFoundError(f"找不到 PDF: {PDF_PATH}")

    arg = sys.argv[1] if len(sys.argv) > 1 else ""
    full = (arg == "--all")

    md_map = analyze_pdf()
    print(f"PDF 解析完成：{len(md_map)} 个月-日组合")

    doc = pymupdf.open(PDF_PATH)

    if full:
        targets = sorted(md_map.keys())
        print("全量生成模式")
    elif arg and re.match(r"^\d{2}-\d{2}$", arg):
        m, d = arg.split("-")
        targets = [(int(m), int(d))]
        print(f"指定月日: {arg}")
    else:
        t = get_beijing_time()
        targets = [(t.month, t.day)]
        print(f"增量模式: 今天 {t.month:02d}-{t.day:02d}")

    for md_key in targets:
        if md_key not in md_map:
            print(f"[跳过] {md_key[0]:02d}-{md_key[1]:02d} 无内容")
            continue
        images, years = build_monthday(md_key, md_map, doc)
        month, day = md_key
        print(f"[{month:02d}-{day:02d}] {len(images)} 张图, 年份 {years}")

    doc.close()

    index = build_index_json(md_map)
    build_calendar_html(index)

    # 生成通知（今天）
    t = get_beijing_time()
    if (t.month, t.day) in md_map:
        images, years = build_monthday((t.month, t.day), md_map, None)
        create_notify(t.month, t.day, images, years)
        (RESULT_DIR / "status.txt").write_text("FOUND", encoding="utf-8")
    else:
        print("今天无图集")
        (RESULT_DIR / "status.txt").write_text("", encoding="utf-8")

    print("=" * 20)
    print("完成")
    print("=" * 20)


if __name__ == "__main__":
    main()
