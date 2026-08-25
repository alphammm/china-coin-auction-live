"""
Playwright 抓取通道。

多数拍行的检索结果是前端渲染的（首轮探测里 Auctionet 103KB、Sotheby's 109KB、
Lyon & Turnbull 152KB 的 HTML 里一条拍品都没有），另有一批直接对 requests 返回
403 / 202 挑战页。真浏览器能同时解决这两类问题。

只在 sources.yml 里标了 browser: true 的源上启用，避免整轮跑太慢。
"""
from __future__ import annotations

import time


class FakeResp:
    """把浏览器结果包装成 requests.Response 的最小子集，供 core 统一处理。"""
    def __init__(self, status: int, text: str, url: str):
        self.status_code = status
        self.text = text
        self.content = text.encode("utf-8", "ignore")
        self.headers = {"content-type": "text/html; charset=utf-8"}
        self.url = url


class Browser:
    def __init__(self, headless: bool = True):
        self._pw = None
        self._browser = None
        self._ctx = None
        self.headless = headless
        self.available = False

    def start(self):
        if self._browser:
            return True
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            print("  ⚠ 未安装 playwright，浏览器通道不可用", flush=True)
            return False
        try:
            self._pw = sync_playwright().start()
            self._browser = self._pw.chromium.launch(
                headless=self.headless,
                args=["--disable-blink-features=AutomationControlled",
                      "--no-sandbox", "--disable-dev-shm-usage"])
            self._ctx = self._browser.new_context(
                viewport={"width": 1440, "height": 1000},
                locale="en-GB",
                user_agent=("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/127.0.0.0 Safari/537.36"),
                extra_http_headers={"Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8"},
            )
            # 抹掉最容易被检测的 webdriver 痕迹
            self._ctx.add_init_script(
                "Object.defineProperty(navigator,'webdriver',{get:()=>undefined});")
            self.available = True
            return True
        except Exception as e:                                   # noqa: BLE001
            print(f"  ⚠ 浏览器启动失败：{type(e).__name__}: {e}", flush=True)
            return False

    def get(self, url: str, wait_selector: str = "", timeout: int = 45000,
            scroll: bool = True) -> FakeResp:
        if not self.start():
            return FakeResp(0, "", url)
        page = self._ctx.new_page()
        status = 0
        try:
            resp = page.goto(url, wait_until="domcontentloaded", timeout=timeout)
            status = resp.status if resp else 0
            if wait_selector:
                try:
                    page.wait_for_selector(wait_selector, timeout=15000)
                except Exception:                                # noqa: BLE001
                    pass
            else:
                try:
                    page.wait_for_load_state("networkidle", timeout=12000)
                except Exception:                                # noqa: BLE001
                    pass
            if scroll:                       # 触发懒加载：滚到底再回顶
                for frac in (0.35, 0.7, 1.0):
                    page.evaluate(f"window.scrollTo(0, document.body.scrollHeight*{frac})")
                    time.sleep(0.7)
            html = page.content()
            return FakeResp(status or 200, html, url)
        except Exception as e:                                   # noqa: BLE001
            return FakeResp(status, f"<!-- browser error: {type(e).__name__}: {e} -->", url)
        finally:
            try:
                page.close()
            except Exception:                                    # noqa: BLE001
                pass

    def close(self):
        for obj in (self._ctx, self._browser):
            try:
                obj and obj.close()
            except Exception:                                    # noqa: BLE001
                pass
        try:
            self._pw and self._pw.stop()
        except Exception:                                        # noqa: BLE001
            pass
