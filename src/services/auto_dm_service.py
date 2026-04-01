"""
自动私聊服务
用于自动向闲鱼卖家发送私聊消息
风险提示：此功能仅用于学习交流，使用需承担相应风险
"""
import asyncio
import random
from typing import Optional
from playwright.async_api import Page, Response


class AutoDmService:
    """自动私聊服务类"""

    def __init__(self):
        self.sent_items: set[str] = set()

    async def send_dm(
        self,
        page: Page,
        item_id: str,
        seller_id: Optional[str],
        message: str,
        item_url: Optional[str] = None
    ) -> bool:
        """
        向卖家发送私聊消息

        Args:
            page: Playwright Page 对象
            item_id: 商品ID
            seller_id: 卖家ID
            message: 要发送的消息
            item_url: 商品链接（可选）

        Returns:
            是否发送成功
        """
        if item_id in self.sent_items:
            print(f"   [私聊] 商品 {item_id} 已发送过私聊，跳过")
            return False

        if not message.strip():
            print(f"   [私聊] 消息内容为空，跳过")
            return False

        try:
            print(f"   [私聊] 开始向商品 {item_id} 卖家发送私聊...")

            # 导航到商品详情页
            if item_url:
                await page.goto(item_url, wait_until="domcontentloaded", timeout=30000)
            else:
                await page.goto(
                    f"https://www.goofish.com/item?id={item_id}",
                    wait_until="domcontentloaded",
                    timeout=30000
                )

            await asyncio.sleep(random.uniform(2, 4))

            # 查找并点击"聊一聊"链接
            chat_button_found = False
            try:
                # 优先查找带 "want--" 类名的链接（从用户提供的HTML）
                want_link = page.locator("a[class*='want--']")
                count = await want_link.count()
                if count > 0:
                    # 获取 href 属性
                    href = await want_link.first.get_attribute("href")
                    if href:
                        print(f"   [私聊] 找到聊天链接: {href}")
                        await page.goto(href, wait_until="domcontentloaded", timeout=30000)
                        chat_button_found = True
            except Exception as e:
                print(f"   [私聊] 尝试 want-- 链接失败: {e}")

            if not chat_button_found:
                # 备选方案：查找包含"聊一聊"的元素
                chat_button_selectors = [
                    "//*[contains(text(), '聊一聊')]",
                    "a:has-text('聊一聊')",
                    "//*[contains(text(), '我想要')]",
                    "//button[contains(., '我想要')]",
                    "//button[contains(., '聊聊')]",
                    "//*[contains(text(), '私信')]",
                ]

                for selector in chat_button_selectors:
                    try:
                        elements = page.locator(selector)
                        count = await elements.count()
                        if count > 0:
                            await elements.first.click()
                            chat_button_found = True
                            print(f"   [私聊] 找到并点击聊天按钮")
                            break
                    except Exception:
                        continue

            if not chat_button_found:
                print(f"   [私聊] 未找到聊天按钮，尝试直接访问聊天页面")
                if seller_id:
                    await page.goto(
                        f"https://www.goofish.com/chat?userId={seller_id}",
                        wait_until="domcontentloaded",
                        timeout=30000
                    )

            await asyncio.sleep(random.uniform(3, 5))

            # 打印当前 URL 以便调试
            current_url = page.url
            print(f"   [私聊] 当前聊天页面 URL: {current_url}")

            # 查找输入框并输入消息
            input_selectors = [
                "[class*='textarea-no-border']",
                "[class*='ant-input']",
                "//textarea[contains(@placeholder, '请输入消息')]",
                "//textarea[contains(@placeholder, '说点什么')]",
                "//textarea[contains(@placeholder, '输入消息')]",
                "//input[@type='text' and contains(@placeholder, '消息')]",
                "//div[contains(@class, 'editor')]//textarea",
                "//div[@contenteditable='true']",
                "textarea",
                "input[type='text']",
                "[class*='input']",
                "[class*='editor']",
            ]

            message_sent = False
            for selector in input_selectors:
                try:
                    input_element = page.locator(selector)
                    count = await input_element.count()
                    if count > 0:
                        print(f"   [私聊] 找到输入框 (选择器: {selector})")
                        
                        # 尝试不同的输入方式
                        try:
                            await input_element.first.fill(message)
                        except:
                            try:
                                await input_element.first.click()
                                await input_element.first.type(message)
                            except:
                                pass
                        
                        await asyncio.sleep(random.uniform(1, 2))

                        # 查找发送按钮
                        send_selectors = [
                            "[class*='ant-btn']",
                            "//button[contains(., '发送')]",
                            "//*[contains(text(), '发送')]",
                            "//*[contains(text(), '发送')]/ancestor::button",
                            "//button[@type='submit']",
                            "button",
                            "[class*='send']",
                            "[class*='submit']",
                        ]

                        for send_selector in send_selectors:
                            try:
                                send_btn = page.locator(send_selector)
                                send_count = await send_btn.count()
                                if send_count > 0:
                                    print(f"   [私聊] 找到发送按钮 (选择器: {send_selector})")
                                    await send_btn.first.click()
                                    message_sent = True
                                    print(f"   [私聊] 消息发送成功: {item_id}")
                                    self.sent_items.add(item_id)
                                    break
                            except Exception as e:
                                print(f"   [私聊] 尝试发送按钮失败 ({send_selector}): {e}")
                                continue

                        if message_sent:
                            break
                except Exception as e:
                    print(f"   [私聊] 尝试输入框失败 ({selector}): {e}")
                    continue

            if not message_sent:
                print(f"   [私聊] 消息发送失败，未找到输入框或发送按钮")

            await asyncio.sleep(random.uniform(1, 2))
            return message_sent

        except Exception as e:
            print(f"   [私聊] 发送私聊时发生错误: {e}")
            return False

    def clear_sent_items(self) -> None:
        """清空已发送商品记录"""
        self.sent_items.clear()

    def has_sent(self, item_id: str) -> bool:
        """检查是否已向该商品发送过私聊"""
        return item_id in self.sent_items
