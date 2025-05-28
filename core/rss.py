import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

def serialize_datetime(obj):
    if isinstance(obj, datetime):
        return obj.isoformat
    return obj
def generate_rss(rss_list: dict, rss_file: str = None, title: str = "Mp-Rss", 
                author: str = "Mp-Rss", link: str = "https://github.com/rachelos/we-mp-rss",
                description: str = "RSS频道", language: str = "zh-CN"):
    # 创建根元素(RSS标准)
    rss = ET.Element("feed", version="2.0")
    rss.attrib["xmlns"] = "http://www.w3.org/2005/Atom"
    # 设置渠道信息
    ET.SubElement(rss, "title").text = title
    ET.SubElement(rss, "link").text = link
    ET.SubElement(rss, "description").text = description
    ET.SubElement(rss, "language").text = language
    ET.SubElement(rss, "lastBuildDate").text = serialize_datetime(datetime.now().isoformat())
    author_elem = ET.SubElement(rss, "author")
    ET.SubElement(author_elem, "name").text = author

    # 添加项目条目(取消注释并修改为RSS标准)
    for rss_item in rss_list:
        item = ET.SubElement(rss, "entity")
        ET.SubElement(item, "id").text = rss_item["id"]
        ET.SubElement(item, "title").text = rss_item["title"]
        link=ET.SubElement(item, "link")
        link.text = rss_item["link"]
        link.attrib["href"] = rss_item["link"]

        ET.SubElement(item, "pubDate").text = rss_item["updated"]

    # 生成XML字符串(添加声明和美化输出)
    tree_str = '<?xml version="1.0" encoding="utf-8"?>\r\n' + \
               ET.tostring(rss, encoding="utf-8", method="xml", short_empty_elements=False).decode("utf-8")
    
    if rss_file is not None:
        with open(rss_file, "w", encoding="utf-8") as f:
            f.write(tree_str)
            
    return tree_str
