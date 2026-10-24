# -*- coding: utf-8 -*-
"""
看板成果截图脚本（Chrome DevTools Protocol 直连，无需 chromedriver）

用途：自动化抓取看板在不同状态下的成品截图，供实验报告与 README 使用。
     需先启动看板服务：streamlit run app.py --server.port 8501

运行：
    python tools/capture_screenshots.py
"""

import base64
import json
import os
import shutil
import subprocess
import tempfile
import time
import urllib.request

import websockets.sync.client as ws_client

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not os.path.exists(CHROME):
    CHROME = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"

BASE_URL = os.environ.get("DASH_URL", "http://localhost:8501")
DEBUG_PORT = int(os.environ.get("DEBUG_PORT", "9222"))
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT_DIR = os.path.join(BASE_DIR, "screenshots")
os.makedirs(SHOT_DIR, exist_ok=True)


# ------------------------------------------------------------------ CDP 封装
class Chrome:
    def __init__(self):
        self.proc = None
        self.profile = tempfile.mkdtemp(prefix="cdp-shot-")
        self.ws = None
        self._id = 0

    def start(self):
        self.proc = subprocess.Popen([
            CHROME, "--headless=new",
            f"--remote-debugging-port={DEBUG_PORT}",
            f"--user-data-dir={self.profile}",
            "--no-first-run", "--no-default-browser-check",
            "--disable-gpu", "--hide-scrollbars",
            "--force-device-scale-factor=1",
            "--window-size=1920,1080",
            "about:blank",
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        for _ in range(60):
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{DEBUG_PORT}/json/version",
                                            timeout=2) as r:
                    json.load(r)
                break
            except Exception:
                time.sleep(0.5)
        else:
            raise RuntimeError("Chrome 调试端口未就绪")

        with urllib.request.urlopen(f"http://127.0.0.1:{DEBUG_PORT}/json/list",
                                    timeout=5) as r:
            targets = json.load(r)
        page = next(t for t in targets if t["type"] == "page")
        self.ws = ws_client.connect(page["webSocketDebuggerUrl"], max_size=None)
        self.send("Page.enable")
        self.send("Runtime.enable")
        return self

    def send(self, method, **params):
        self._id += 1
        self.ws.send(json.dumps({"id": self._id, "method": method, "params": params}))
        while True:
            msg = json.loads(self.ws.recv(timeout=120))
            if msg.get("id") == self._id:
                if "error" in msg:
                    raise RuntimeError(f"CDP {method} 失败: {msg['error']}")
                return msg.get("result", {})

    def js(self, expr: str):
        res = self.send("Runtime.evaluate", expression=expr,
                        returnByValue=True, awaitPromise=False)
        v = res.get("result", {}).get("value")
        return v

    def goto(self, url: str):
        self.send("Page.navigate", url=url)
        time.sleep(1.0)

    def set_viewport(self, width: int, height: int, mobile: bool = False):
        self.send("Emulation.setDeviceMetricsOverride",
                  width=width, height=height, deviceScaleFactor=1,
                  mobile=mobile)

    def wait_plots(self, minimum: int = 8, timeout: float = 60):
        """等待 Streamlit 与 Plotly 渲染完成。"""
        t0 = time.time()
        while time.time() - t0 < timeout:
            n = self.js(
                "document.querySelectorAll('.js-plotly-plot .main-svg').length || 0")
            if (n or 0) >= minimum:
                break
            time.sleep(0.8)
        # 滚动一遍触发懒加载（明细表格等）
        self.js("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1.5)
        self.js("window.scrollTo(0, 0);")
        time.sleep(1.2)

    def content_height(self) -> int:
        h = self.js("Math.max(document.body.scrollHeight,"
                    "document.documentElement.scrollHeight, 800)")
        return int(h or 800)

    def shot(self, name: str, full_page: bool = True, width: int = 1920):
        if full_page:
            for _ in range(3):
                h = self.content_height()
                h = min(h + 40, 16000)
                self.set_viewport(width, h)
                time.sleep(1.0)
        res = self.send("Page.captureScreenshot", format="png",
                        captureBeyondViewport=full_page, fromSurface=True)
        data = base64.b64decode(res["data"])
        path = os.path.join(SHOT_DIR, name)
        with open(path, "wb") as f:
            f.write(data)
        size = os.path.getsize(path) // 1024
        print(f"  ✔ {name}  ({width}x{'整页' if full_page else '首屏'}, {size} KB)")
        return path

    def click_text(self, text: str) -> str:
        """点击包含指定文本的开关/按钮。"""
        expr = f"""
        (() => {{
          const boxes = Array.from(document.querySelectorAll(
              '[data-testid="stToggle"],[data-testid="stCheckbox"],button'));
          const box = boxes.find(e => e.textContent && e.textContent.includes({json.dumps(text)}));
          if (!box) return 'notfound';
          const inp = box.querySelector('input');
          if (inp) {{ inp.click(); return 'clicked-input'; }}
          box.click();
          return 'clicked-box';
        }})()
        """
        return self.js(expr)

    def slider_to_min(self, label_text: str) -> str:
        """把指定滑块拉到最小值（用于演示预警）。"""
        rect_expr = f"""
        (() => {{
          const boxes = Array.from(document.querySelectorAll('[data-testid="stSlider"]'));
          const box = boxes.find(e => e.textContent && e.textContent.includes({json.dumps(label_text)}));
          if (!box) return null;
          const th = box.querySelector("[role='slider']");
          if (!th) return null;
          th.scrollIntoView({{block:'center'}});
          const r = th.getBoundingClientRect();
          return [Math.round(r.x + r.width/2), Math.round(r.y + r.height/2)];
        }})()
        """
        pos = self.js(rect_expr)
        if not pos:
            return "notfound"
        x, y = int(pos[0]), int(pos[1])
        self.send("Input.dispatchMouseEvent", type="mousePressed",
                  x=x, y=y, button="left", clickCount=1)
        self.send("Input.dispatchMouseEvent", type="mouseReleased",
                  x=x, y=y, button="left", clickCount=1)
        time.sleep(0.4)
        for key, code, vk in (("Home", "Home", 36), ("ArrowLeft", "ArrowLeft", 37)):
            self.send("Input.dispatchKeyEvent", type="rawKeyDown", key=key,
                      code=code, windowsVirtualKeyCode=vk, nativeVirtualKeyCode=vk)
            self.send("Input.dispatchKeyEvent", type="keyUp", key=key,
                      code=code, windowsVirtualKeyCode=vk, nativeVirtualKeyCode=vk)
            time.sleep(0.3)
        time.sleep(1.0)
        return "ok"

    def click_plotly_bar(self, index: int = 0) -> str:
        """点击学院柱状图的第 index 根柱子（演示图表联动）。"""
        expr = f"""
        (() => new Promise(res => {{
          const plots = document.querySelectorAll('.js-plotly-plot');
          if (!plots.length) return res(null);
          const bars = plots[0].querySelectorAll('.point path, g.points path, .bars path, path.point');
          if (!bars.length) return res(null);
          const el = bars[{index}] || bars[0];
          el.scrollIntoView({{block:'center'}});
          setTimeout(() => {{
            const r = el.getBoundingClientRect();
            res([Math.round(r.x + r.width/2), Math.round(r.y + Math.min(r.height/2, 30))]);
          }}, 600);
        }}))()
        """
        pos = self.send("Runtime.evaluate", expression=expr,
                        awaitPromise=True, returnByValue=True)["result"]["value"]
        if not pos:
            return "notfound"
        x, y = int(pos[0]), int(pos[1])
        self.send("Input.dispatchMouseEvent", type="mouseMoved", x=x, y=y, buttons=0)
        self.send("Input.dispatchMouseEvent", type="mousePressed",
                  x=x, y=y, button="left", clickCount=1, buttons=1)
        self.send("Input.dispatchMouseEvent", type="mouseReleased",
                  x=x, y=y, button="left", clickCount=1, buttons=0)
        time.sleep(3.0)
        return "ok"

    def has_text(self, text: str) -> bool:
        return bool(self.js(
            f"document.body.innerText.includes({json.dumps(text)})"))

    def close(self):
        try:
            if self.ws:
                self.ws.close()
        except Exception:
            pass
        try:
            if self.proc:
                self.proc.terminate()
                self.proc.wait(timeout=10)
        except Exception:
            pass
        shutil.rmtree(self.profile, ignore_errors=True)


# ------------------------------------------------------------------ 主流程
def main():
    print("开始抓看板截图（Chrome CDP）…")
    br = Chrome().start()
    try:
        # 1) 暗色科技风 · 首屏 + 整页
        br.goto(BASE_URL)
        br.wait_plots()
        br.set_viewport(1920, 1080)
        br.shot("01-overview-dark-fold.png", full_page=False, width=1920)
        br.shot("02-overview-dark-full.png", full_page=True, width=1920)

        # 2) 亮色简约风（主题切换）
        br.goto(f"{BASE_URL}/?theme=亮色简约风")
        br.wait_plots()
        br.shot("03-light-theme.png", full_page=True, width=1920)

        # 3) 图表联动下钻：先尝试真实点击柱体，失败则回退 URL 参数
        br.goto(BASE_URL)
        br.wait_plots()
        state = br.click_plotly_bar(0)
        if br.has_text("已联动下钻至"):
            print("  · 柱体点击联动生效")
        else:
            print("  · 柱体点击未生效，回退 URL 参数下钻")
            br.goto(f"{BASE_URL}/?college=计算机学院")
            br.wait_plots()
        br.shot("04-drilldown-college.png", full_page=True, width=1920)

        # 4) 预警触发：先尝试真实拖动滑块，失败则用 URL 参数把阈值压到最低
        br.goto(BASE_URL)
        br.wait_plots()
        br.slider_to_min("日均消费额预警上限")
        br.slider_to_min("占比预警上限")
        br.wait_plots(timeout=30)
        if br.has_text("预警触发"):
            print("  · 预警状态已触发")
        else:
            print("  · 预警未触发，改用 URL 参数强制演示")
            br.goto(f"{BASE_URL}/?thr_daily=300&thr_big=0.5")
            br.wait_plots()
        br.shot("05-alert-warning.png", full_page=True, width=1920)

        # 5) 实时数据源模式
        br.goto(BASE_URL)
        br.wait_plots()
        r = br.click_text("开启实时刷新")
        time.sleep(3.5)
        if br.has_text("实时数据流已接入"):
            print("  · 实时模式已开启")
        else:
            print(f"  · 实时开关点击结果：{r}")
        br.shot("06-realtime-mode.png", full_page=True, width=1920)

        # 6) 移动端适配 430×932
        br.goto(BASE_URL)
        br.set_viewport(430, 932, mobile=True)
        br.wait_plots()
        br.shot("07-mobile.png", full_page=True, width=430)

        # 7) 超宽大屏 2560×1440 首屏
        br.goto(BASE_URL)
        br.set_viewport(2560, 1440)
        br.wait_plots()
        br.shot("08-bigscreen-2560.png", full_page=False, width=2560)
    finally:
        br.close()

    print(f"\n全部截图已保存至：{SHOT_DIR}")


if __name__ == "__main__":
    main()
