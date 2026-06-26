#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import ssl
from datetime import date
from html import unescape
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
RAW_MD = ROOT / "鬼谷子文稿.md"
ANNOTATION_DIR = ROOT / "鬼谷子白话注释"
BOOK_DIR = ROOT / "library" / "books" / "guiguzi"
NOTES_PATH = ROOT / "library" / "notes" / "guiguzi.json"

CHAPTERS = [
    ("捭阖", "bai-he"),
    ("反应", "fan-ying"),
    ("内揵", "nei-qian"),
    ("抵巇", "di-xi"),
    ("飞箝", "fei-qian"),
    ("忤合", "wu-he"),
    ("揣篇", "chuai-pian"),
    ("摩篇", "mo-pian"),
    ("权篇", "quan-pian"),
    ("谋篇", "mou-pian"),
    ("决篇", "jue-pian"),
    ("符言", "fu-yan"),
    ("盛神法五龙", "sheng-shen-fa-wu-long"),
    ("养志法灵龟", "yang-zhi-fa-ling-gui"),
    ("实意法螣蛇", "shi-yi-fa-teng-she"),
    ("分威法伏熊", "fen-wei-fa-fu-xiong"),
    ("散势法鸷鸟", "san-shi-fa-zhi-niao"),
    ("转圆法猛兽", "zhuan-yuan-fa-meng-shou"),
    ("损兑法灵蓍", "sun-dui-fa-ling-shi"),
    ("持枢", "chi-shu"),
    ("中经", "zhong-jing"),
]

THEMES = {
    "捭阖": "讲开合之道：先观察阴阳、言默、进退，再决定打开话题还是收住话头",
    "反应": "讲反复观察和回应：通过回看过去、验证将来，探知对方真实情势",
    "内揵": "讲向内建立信任和进言之术：让意见能进入君主心中而不被拒斥",
    "抵巇": "讲发现裂隙并处理裂隙：小缝未成大患时就要补救或利用",
    "飞箝": "讲先扬后制、以言语钳制对方：通过称引、试探、牵引来掌握人心",
    "忤合": "讲相合与相背的选择：顺逆、离合都要因时因势而定",
    "揣篇": "讲揣度天下与诸侯之情：先量权势，再推测真实意向",
    "摩篇": "讲摩切试探之术：在隐微处接触对方，观察内心是否相符",
    "权篇": "讲游说权衡：根据对象、形势和利害调整言辞轻重",
    "谋篇": "讲谋划的原则：谋事要得其所因，合乎时势、人情和机变",
    "决篇": "讲决断疑难：在利害未明处判断祸福，作出取舍",
    "符言": "讲主位与治国言行：君主要安静、正定、虚心，以言行合符于道",
    "盛神法五龙": "讲养神：使心神充盛，五气归位，作为谋虑和行动的根本",
    "养志法灵龟": "讲养志：让心志专一、欲望有主，像灵龟一样能静而知机",
    "实意法螣蛇": "讲实意：使意念真实深远，心静则谋略自然生发",
    "分威法伏熊": "讲分威：内在神气稳固后，威势才能向外覆盖",
    "散势法鸷鸟": "讲散势：像猛禽乘隙而动，把内在威势推出去",
    "转圆法猛兽": "讲转圆：用圆转无穷的计谋应对不可测的变化",
    "损兑法灵蓍": "讲损兑：在机危成败处减少泄露、谨慎决断",
    "持枢": "讲把握四时运行的枢纽：顺应生长收藏之时，掌握变化中心",
    "中经": "讲救急、振穷、摄心和用人：在困厄中收摄人心、成就事功",
}

GLOSSARY = {
    "捭阖": "开合。捭是打开、展开，阖是闭合、收住。",
    "阴阳": "这里常指事物相反相成的两面，如开合、进退、动静、强弱。",
    "名命物": "用名称分别事物，使事物在言说中各有定位。",
    "反覆": "反复观察、来回验证，不只看一面。",
    "反应": "由对方的回应反观其情，也指以回应来试探对方。",
    "内揵": "把意见、谋略向内扣合到君主或对方心中。",
    "抵巇": "抵，是抵住、处理；巇，是裂隙、漏洞、危机。",
    "飞箝": "用言辞称扬、牵引、钳制对方，使其情意显露并受控制。",
    "忤合": "忤是相逆，合是相合；指顺逆离合的权衡。",
    "揣": "揣度、估量，推测对方实情。",
    "摩": "摩切、接触、试探，在细微处探知对方。",
    "权": "权衡轻重、审度利害，也指因势调整的方法。",
    "谋": "谋划。重点不是空想计策，而是顺着实际原因和人情立策。",
    "决": "决断疑难，在犹豫和风险中作取舍。",
    "符言": "言语与事理相合，如符契相合。",
    "五龙": "本经阴符七术中的象征，用来指养神时五气运行有序。",
    "灵龟": "象征静定、蓄养和知机。",
    "螣蛇": "象征意念深藏、变化灵动。",
    "伏熊": "象征威势内蓄、沉稳有力。",
    "鸷鸟": "猛禽，象征抓住间隙、迅疾出击。",
    "猛兽": "象征圆转变化中的强大行动力。",
    "灵蓍": "蓍草，象征占决机微、审慎判断。",
    "持枢": "把持枢纽，掌握事物运转的中心。",
    "中经": "可理解为内在经法，重在收摄人心、济急扶困。",
    "圣人": "在《鬼谷子》中多指洞察阴阳、人情、时势并能运用其术的人。",
    "君臣": "既指政治中的君臣，也常用来说明上下、主从、内外关系。",
    "机": "关键时机、细微发动处。",
    "势": "形势、力量展开的方向。",
    "情": "真实情况、内心意向或事物实情。",
    "道": "运行原则和方法，不只是道德意义的道。",
}

MODERN_REPLACEMENTS = [
    ("圣人之在天地间也", "通达事理的人处在天地之间"),
    ("故圣人之在天下也", "所以通达事理的人处在天下"),
    ("筹策万类", "谋划各种事物"),
    ("其道一也", "其根本方法是一贯的"),
    ("粤若稽古", "考察古代"),
    ("圣人", "通达事理的人"),
    ("众生", "众人和万物"),
    ("阴阳", "阴阳变化"),
    ("开阖", "打开和闭合"),
    ("名命物", "给事物命名分类"),
    ("存亡", "存续和灭亡"),
    ("门户", "关键关口"),
    ("筹策", "谋划"),
    ("万类", "各种事物"),
    ("终始", "开始和终结"),
    ("达人心之理", "通达人心的规律"),
    ("变化之朕", "变化初现的征兆"),
    ("守司", "守住并掌握"),
    ("无穷", "没有穷尽"),
    ("有所归", "各有归向"),
    ("是故", "所以"),
    ("审察", "仔细考察"),
    ("度权量能", "衡量权势和能力"),
    ("伎巧短长", "技巧的长处和短处"),
    ("贤不肖", "贤能和不贤"),
    ("智愚", "聪明和愚笨"),
    ("勇怯", "勇敢和怯懦"),
    ("捭", "打开"),
    ("阖", "闭合"),
    ("无为以牧之", "以不强行干预的方式统摄他们"),
    ("其实虚", "真实和虚假"),
    ("嗜欲", "喜好和欲望"),
    ("志意", "心志意向"),
    ("微", "暗中、细微地"),
    ("贵", "关键在于"),
    ("指", "意旨"),
    ("计谋", "谋划"),
    ("同异", "相同和不同之处"),
    ("周密", "周全而严密"),
    ("反覆", "反复验证"),
    ("反以观往", "回头观察过去"),
    ("覆以验来", "翻转验证将来"),
    ("动静虚实", "行动、静止、虚假、真实"),
    ("内揵", "向内扣合、取得信任"),
    ("抵巇", "处理裂隙和漏洞"),
    ("飞箝", "用言辞牵引并控制"),
    ("忤合", "相逆和相合"),
    ("揣", "揣度"),
    ("摩", "试探"),
    ("权", "权衡"),
    ("谋", "谋划"),
    ("决", "决断"),
    ("君", "君主"),
    ("臣", "臣下"),
    ("主", "主上"),
    ("天下", "天下局势"),
    ("诸侯", "各国诸侯"),
    ("心", "内心"),
    ("神", "精神"),
    ("志", "志向"),
    ("意", "意念"),
    ("气", "气势"),
    ("威", "威势"),
    ("机", "关键时机"),
    ("势", "形势"),
    ("情", "真实情形"),
    ("道", "方法和原则"),
]


def fetch(url: str) -> str:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    context = ssl._create_unverified_context()
    with urlopen(request, timeout=40, context=context) as response:
        return response.read().decode("utf-8", errors="replace")


def strip_html(fragment: str) -> str:
    fragment = re.sub(r"<sup\b[^>]*>.*?</sup>", "", fragment, flags=re.S | re.I)
    fragment = re.sub(r"<script\b[^>]*>.*?</script>", "", fragment, flags=re.S | re.I)
    fragment = re.sub(r"<style\b[^>]*>.*?</style>", "", fragment, flags=re.S | re.I)
    fragment = re.sub(r'<div\s+id="comm\d+"\s*>\s*</div>', "", fragment, flags=re.S | re.I)
    fragment = re.sub(r"<br\s*/?>", "\n", fragment, flags=re.I)
    text = re.sub(r"<[^>]+>", "", fragment)
    text = unescape(text).replace("\xa0", " ")
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n\s*", "\n", text)
    return text.strip()


def extract_rows(page: str) -> list[str]:
    rows = []
    for match in re.finditer(
        r'<tr\s+id="n\d+".*?<td\s+class="ctext"\s*>\s*(.*?)</td>\s*</tr>',
        page,
        flags=re.S | re.I,
    ):
        text = strip_html(match.group(1))
        if text:
            rows.append(text)
    return merge_continuations(rows)


def merge_continuations(rows: list[str]) -> list[str]:
    merged: list[str] = []
    for row in rows:
        if merged and not merged[-1].endswith(("。", "！", "？", "；", "”", "’")):
            merged[-1] = merged[-1] + row
        else:
            merged.append(row)
    return merged


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[。！？；])", text)
    return [part.strip() for part in parts if part.strip()]


def key_terms(text: str) -> list[str]:
    terms = []
    for term, explanation in GLOSSARY.items():
        if term in text and len(terms) < 5:
            terms.append(f"{term}：{explanation}")
    return terms


def plain_text(title: str, paragraph: str, index: int) -> str:
    theme = THEMES[title]
    modern = modernize(paragraph)
    return (
        f"白话试读：{modern}\n\n"
        f"本段主旨：这一段围绕“{title}”展开，{theme}。阅读时重点看它怎样说明观察人情、"
        "把握时机、判断利害，或由内在修养转入外在行动。"
    )


def modernize(paragraph: str) -> str:
    text = paragraph
    for old, new in MODERN_REPLACEMENTS:
        if len(old) >= 2:
            text = text.replace(old, new)
    text = re.sub(r"夫", "大凡", text, count=1)
    text = re.sub(r"曰：", "说：", text)
    text = re.sub(r"不可不", "不能不", text)
    return text


def reading_hint(title: str, paragraph: str, index: int) -> str:
    theme = THEMES[title]
    if index == 1:
        return f"本段通常是《{title}》的开端，要先抓住本篇主题：{theme}。"
    if any(word in paragraph for word in ["故", "是故", "由此", "乃"]):
        return "这一段多是在承接前文作推论，阅读时注意它怎样从观察、试探推进到行动原则。"
    if any(word in paragraph for word in ["君", "主", "臣", "天下", "诸侯"]):
        return "这一段把方法放到政治和用人场景中，重点看上下关系、权势和人情如何配合。"
    if any(word in paragraph for word in ["心", "神", "志", "意", "气"]):
        return "这一段偏重内在修养，说明谋略并不只靠口才，也靠心神、志意和气势的稳定。"
    return "这一段可先抓关键词，再看它是在讲观察、试探、取舍还是行动。"


def notes_for(title: str, paragraph: str, index: int) -> list[str]:
    notes = key_terms(paragraph)
    if not notes:
        notes.append(f"{title}：{THEMES[title]}")
    if "曰" in paragraph:
        notes.append("曰：古文中常作“说”或提示论断。")
    if any(word in paragraph for word in ["故", "是故"]):
        notes.append("故/是故：表示由前面的判断推出后面的原则。")
    if len(notes) < 3:
        notes.append("本段注释为初版理解提示，适合先读通大意，后续可在个人笔记中继续细化。")
    return notes[:6]


def write_raw(chapter_data: list[dict]) -> None:
    lines = [
        "# 鬼谷子",
        "",
        "整理：据中国哲学书电子化计划简体字版整理。",
        "来源：https://ctext.org/gui-gu-zi/zhs",
        "底本信息：网页列出底本为《四部丛刊初编》本《鬼谷子》，并列有《正统道藏》本《鬼谷子》。",
        "说明：CText 目录中“转丸”“胠乱”仅显示篇名，未提供可点击正文页；本次收入可抓取正文的篇章。",
        f"整理日期：{date.today().isoformat()}",
        "",
        "## 目录",
        "",
    ]
    for i, item in enumerate(chapter_data, 1):
        lines.append(f"{i}. {item['title']}")
    lines.append("")
    for i, item in enumerate(chapter_data, 1):
        lines.extend([f"## {i}. {item['title']}", "", f"来源：{item['source']}", ""])
        for paragraph in item["paragraphs"]:
            lines.extend([paragraph, ""])
    RAW_MD.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def write_annotation_markdown(chapter_data: list[dict]) -> None:
    ANNOTATION_DIR.mkdir(exist_ok=True)
    for c_index, item in enumerate(chapter_data, 1):
        lines = [
            f"# {item['title']}",
            "",
            f"来源：{item['source']}",
            "底稿：../鬼谷子文稿.md",
            "",
            "## 阅读说明",
            "",
            "本文按原文自然段逐段整理。每段包含原文、白话文、注释、理解提示和“我的理解”空位。",
            "段落编号仅用于本项目内部阅读和做笔记，不代表古籍原有编号。",
            "白话文和注释为初版读解，适合先建立理解框架；精读时可继续在“我的理解”中补充。",
            "",
        ]
        for p_index, paragraph in enumerate(item["paragraphs"], 1):
            lines.extend([f"### 第 {p_index} 段", "", "**原文**", ""])
            for line in paragraph.splitlines():
                lines.append(f"> {line}")
            lines.extend(
                [
                    "",
                    "**白话文**",
                    "",
                    plain_text(item["title"], paragraph, p_index),
                    "",
                    "**注释**",
                    "",
                ]
            )
            for note in notes_for(item["title"], paragraph, p_index):
                lines.append(f"- {note}")
            lines.extend(
                [
                    "",
                    "**理解提示**",
                    "",
                    reading_hint(item["title"], paragraph, p_index),
                    "",
                    "**我的理解**",
                    "",
                    "> 在这里写你的理解、疑问或联想。",
                    "",
                ]
            )
        filename = ANNOTATION_DIR / f"{c_index:02d}-{item['title']}.md"
        filename.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def write_book_json(chapter_data: list[dict]) -> None:
    chapters = []
    paragraphs = []
    for c_index, item in enumerate(chapter_data, 1):
        chapter_id = f"ch{c_index:02d}"
        chapters.append({"id": chapter_id, "title": item["title"]})
        for p_index, paragraph in enumerate(item["paragraphs"], 1):
            paragraphs.append(
                {
                    "id": f"guiguzi-{chapter_id}-p{p_index:03d}",
                    "chapter_id": chapter_id,
                    "index": p_index,
                    "original": paragraph,
                    "plain_text": plain_text(item["title"], paragraph, p_index),
                    "notes": notes_for(item["title"], paragraph, p_index),
                    "reading_hint": reading_hint(item["title"], paragraph, p_index),
                }
            )
    book = {
        "book_id": "guiguzi",
        "title": "鬼谷子",
        "source": "https://ctext.org/gui-gu-zi/zhs",
        "chapters": chapters,
        "paragraphs": paragraphs,
    }
    BOOK_DIR.mkdir(parents=True, exist_ok=True)
    (BOOK_DIR / "book.json").write_text(
        json.dumps(book, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if not NOTES_PATH.exists():
        NOTES_PATH.parent.mkdir(parents=True, exist_ok=True)
        NOTES_PATH.write_text(
            json.dumps({"book_id": "guiguzi", "notes": {}}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


def main() -> None:
    chapter_data = []
    for title, slug in CHAPTERS:
        source = f"https://ctext.org/gui-gu-zi/{slug}/zhs"
        rows = extract_rows(fetch(source))
        if not rows:
            raise RuntimeError(f"未抓取到正文：{title}")
        chapter_data.append({"title": title, "slug": slug, "source": source, "paragraphs": rows})
        print(f"{title}: {len(rows)} 段")
    write_raw(chapter_data)
    write_annotation_markdown(chapter_data)
    write_book_json(chapter_data)
    print(f"已整理《鬼谷子》：{len(chapter_data)} 篇，{sum(len(c['paragraphs']) for c in chapter_data)} 段")


if __name__ == "__main__":
    main()
