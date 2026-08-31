import requests
import time
import schedule
import os
from urllib.parse import quote
from datetime import date

# 将成功状态持久化写入本地文件，防止重启后失忆
STATUS_FILE = "last_success.txt"

def send_bark(title, content):
    bark_url = os.environ.get("BARK_URL")
    if not bark_url or "请在这里填入" in bark_url:
        return
        
    if not bark_url.endswith('/'):
        bark_url += '/'
        
    try:
        url = f"{bark_url}{quote(title)}/{quote(content)}"
        requests.get(url, timeout=10)
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Bark 推送成功")
    except Exception as e:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Bark 推送失败: {e}")

def do_checkin():
    today_str = str(date.today())
    
    # 检查本地文件记录的成功日期
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "r") as f:
            last_success = f.read().strip()
        if last_success == today_str:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 今日已签到成功，跳过本次执行。")
            return

    url = os.environ.get("CHECKIN_URL")
    if not url or "请在这里填入" in url or "xxx" in url:
        error_msg = "错误: 未配置有效的 CHECKIN_URL 环境变量。"
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {error_msg}")
        send_bark("灵犀签到失败", error_msg)
        return

    cookie = os.environ.get("LINGXI_COOKIE")
    if not cookie or "请在这里填入" in cookie:
        error_msg = "错误: 未配置有效的 LINGXI_COOKIE 环境变量。"
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {error_msg}")
        send_bark("灵犀签到失败", error_msg)
        return

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36",
        "Cookie": cookie
    }

    try:
        response = requests.post(url, headers=headers, timeout=10)
        res_text = response.text
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 签到响应: {res_text}")
        
        if "未登录" in res_text or "error" in res_text.lower():
            send_bark("灵犀签到异常(Cookie可能已失效)", res_text)
        else:
            send_bark("灵犀签到结果", res_text)
            # 签到成功后，将今天的日期写入文件持久保存
            with open(STATUS_FILE, "w") as f:
                f.write(today_str)
            
    except Exception as e:
        error_msg = f"签到请求网络异常: {e}"
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {error_msg}")
        send_bark("灵犀签到运行异常", error_msg)

if __name__ == "__main__":
    print("启动金山灵犀自动签到服务...")
    
    times_str = os.environ.get("CHECKIN_TIMES", "08:30,16:30")
    times_list = [t.strip() for t in times_str.split(",") if t.strip()]
    
    if not times_list:
        times_list = ["08:30"]
        
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 设定的每日签到时间: {', '.join(times_list)}")
    
    for t in times_list:
        schedule.every().day.at(t).do(do_checkin)
        
    do_checkin() 
    
    while True:
        schedule.run_pending()
        time.sleep(60)
