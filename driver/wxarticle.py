from .wx import WX_API
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from typing import Dict
import time

class WXArticleFetcher:
    """微信公众号文章获取器
    
    基于WX_API登录状态获取文章内容
    
    Attributes:
        wait_timeout: 显式等待超时时间(秒)
    """
    
    def __init__(self, wait_timeout: int = 10):
        """初始化文章获取器"""
        self.wait_timeout = wait_timeout
        
    def get_article_content(self, url: str) -> Dict:
        """获取单篇文章详细内容
        
        Args:
            url: 文章URL (如: https://mp.weixin.qq.com/s/qfe2F6Dcw-uPXW_XW7UAIg)
            
        Returns:
            文章内容数据字典，包含:
            - title: 文章标题
            - author: 作者
            - publish_time: 发布时间
            - content: 正文HTML
            - images: 图片URL列表
            
        Raises:
            Exception: 如果未登录或获取内容失败
        """
            
        driver = WX_API.driver
        wait = WebDriverWait(driver, self.wait_timeout)
        
        try:
            driver.get(url)
            
            # 等待关键元素加载
            wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#activity-detail"))
            )
            
            # 获取文章元数据
            title = driver.find_element(
                By.CSS_SELECTOR, "#activity-name"
            ).text.strip()
            
            author = driver.find_element(
                By.CSS_SELECTOR, "#meta_content .rich_media_meta_text"
            ).text.strip()
            
            publish_time = driver.find_element(
                By.CSS_SELECTOR, "#publish_time"
            ).text.strip()
            
            # 获取正文内容和图片
            content_element = driver.find_element(
                By.CSS_SELECTOR, "#js_content"
            )
            content = content_element.get_attribute("innerHTML")
            
            images = [
                img.get_attribute("data-src") or img.get_attribute("src")
                for img in content_element.find_elements(By.TAG_NAME, "img")
                if img.get_attribute("data-src") or img.get_attribute("src")
            ]
            
            return {
                "title": title,
                "author": author,
                "publish_time": publish_time,
                "content": content,
                "images": images
            }
            
        except Exception as e:
            raise Exception(f"文章内容获取失败: {str(e)}")