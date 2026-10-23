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
def analyze_pdf():
    """
    扫描整个 PDF，返回 md_map: {(month, day): [(year, page_index), ...]}
    每页第一个日期决定该页归属（年、月、日），按页面顺序排列。
    """
    doc = pymupdf.open(PDF_PATH)
    md_map = {}
    for i, page in enumerate(doc):
        text = page.get_text()
        dates = DATE_PATTERN.findall(text)
        if not dates:
            continue
        y, m, d = dates[0]
        year = int(y)
        month = int(m)
        day = int(d)
        key = (month, day)
        if key not in md_map:
            md_map[key] = []
        md_map[key].append((year, i))
    doc.close()
    return md_map


def cut_page_to_jpg(doc, page_index, out_path, dpi=180):
    page = doc[page_index]
    pix = page.get_pixmap(dpi=dpi)
    pix.save(str(out_path))
    return out_path


def build_monthday(md_key, md_map, doc):
    """
    切某个月日的图，返回 (图片文件名列表, 年份列表)。
    doc 为 None 时只统计（用于通知）。
    """
    month, day = md_key
    entries = md_map[md_key]  # [(year, page_index), ...]
    folder = HISTORY_DIR / f"{month:02d}-{day:02d}"
    folder.mkdir(exist_ok=True)

    year_counter = {}
    images = []
    years_seen = []
    for year, page_idx in entries:
        year_counter[year] = year_counter.get(year, 0) + 1
        seq = year_counter[year]
        name = f"{month:02d}-{day:02d}-{year}-{seq:03d}.jpg"
        out = folder / name
        if doc is not None:
            if not out.exists():
                cut_page_to_jpg(doc, page_idx, out)
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
  .day-grid { display:grid; grid-template-columns:repeat(7,1fr); gap:6px; }
  .day-cell { aspect-ratio:1; display:flex; flex-direction:column; align-items:center; justify-content:center;
    border-radius:10px; background:var(--card); border:1px solid var(--border); cursor:pointer; transition:all .12s; }
  .day-cell:hover { background:var(--card-hover); }
  .day-cell .d { font-size:15px; font-weight:600; }
  .day-cell .dot-ind { width:5px; height:5px; border-radius:50%; background:var(--accent); margin-top:3px; }
  .day-cell.empty { background:transparent; border-color:transparent; cursor:default; }
  .day-cell.no-data { opacity:.35; cursor:default; }
  .day-cell.today { border-color:var(--accent); box-shadow:0 0 0 1px var(--accent); }
  .day-cell.today .d { color:var(--accent); }
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
  <div class="section-title">选择日期<span class="hint">带金点 = 有图集</span></div>
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

  function pad(n){ return n<10?'0'+n:''+n; }
  function todayMd(){ var t=new Date(); return pad(t.getMonth()+1)+'-'+pad(t.getDate()); }
  function fullToday(){ var t=new Date(); return t.getFullYear()+'年'+(t.getMonth()+1)+'月'+t.getDate()+'日'; }

  function init(){
    var t = new Date();
    curMonth = t.getMonth();
    document.getElementById('todayDate').textContent = fullToday();
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

    buildMonthNav(); renderGrid();
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

  function renderGrid(){
    var grid=document.getElementById('dayGrid'); grid.innerHTML='';
    var t=new Date();
    var firstDay=new Date(t.getFullYear(),curMonth,1).getDay();
    var days=new Date(t.getFullYear(),curMonth+1,0).getDate();
    document.getElementById('navHint').textContent = (curMonth+1)+'月 · 共 '+days+' 天';
    for(var i=0;i<firstDay;i++){ var e=document.createElement('div'); e.className='day-cell empty'; grid.appendChild(e); }
    for(var d=1;d<=days;d++){
      (function(day){
        var md=pad(curMonth+1)+'-'+pad(day);
        var cell=document.createElement('div'); cell.className='day-cell';
        var has=INDEX[md];
        if(!has) cell.classList.add('no-data');
        var dn=document.createElement('span'); dn.className='d'; dn.textContent=day; cell.appendChild(dn);
        if(has){ var dot=document.createElement('span'); dot.className='dot-ind'; cell.appendChild(dot); }
        if(curMonth===t.getMonth() && day===t.getDate()) cell.classList.add('today');
        if(has) cell.onclick=function(){ showCollection(md); };
        grid.appendChild(cell);
      })(d);
    }
  }

  function showCollection(md){
    var coll=document.getElementById('collection'); coll.classList.add('show');
    document.getElementById('collTitle').textContent = md.replace('-','月')+'日 · 历年图集';
    var body=document.getElementById('collBody');
    body.innerHTML='<div class="loading">加载中…</div>';
    window.scrollTo({top:0,behavior:'smooth'});
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
    document.getElementById('collBack').onclick=function(){ coll.classList.remove('show'); window.scrollTo({top:0,behavior:'smooth'}); };
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
