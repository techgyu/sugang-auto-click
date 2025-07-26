import asyncio
import aiohttp
import time
import pyautogui
from datetime import datetime, timezone, timedelta
import threading

URL = "https://sugang.anyang.ac.kr"
TARGET_TIME = "2025-02-14 11:54:00"  # 수강신청 목표 시간

# 🔹 비동기 방식으로 서버 시간 가져오기
async def get_server_time():
    async with aiohttp.ClientSession() as session:
        start_time = time.time()  # 요청 전 로컬 시간 기록
        async with session.head(URL) as response:
            end_time = time.time()  # 응답 후 로컬 시간 기록

            if "Date" in response.headers:
                gmt_time = response.headers["Date"]  # 서버 GMT 시간
                gmt_datetime = datetime.strptime(gmt_time, "%a, %d %b %Y %H:%M:%S %Z")
                kst_datetime = gmt_datetime.replace(tzinfo=timezone.utc) + timedelta(hours=9)

                # RTT (네트워크 왕복 시간) 계산
                rtt = (end_time - start_time) / 2  # 왕복 지연 시간 반으로 나누기
                corrected_time = kst_datetime + timedelta(seconds=rtt)  # 보정된 시간

                return corrected_time, rtt
    return None, None

# 🔹 10번 반복해서 평균 RTT 계산
async def measure_average_rtt():
    rtt_list = []
    for _ in range(10):
        server_time, rtt = await get_server_time()
        if rtt:
            rtt_list.append(rtt)
        await asyncio.sleep(0.05)  # 너무 빠른 요청 방지

    average_rtt = sum(rtt_list) / len(rtt_list) if rtt_list else 0
    return server_time, average_rtt

# 🔹 자동 클릭 실행 (현재 마우스 위치 사용)
def auto_click():
    # 현재 마우스 위치 파악
    mouse_x, mouse_y = pyautogui.position()
    print(f"✅ 클릭 명령 전송! 현재 마우스 위치: ({mouse_x}, {mouse_y})")
    
    # 마우스 위치에서 클릭 실행
    pyautogui.click(mouse_x, mouse_y)

# 🔹 정확한 시간에 실행하는 스레드
def wait_until_target(target_datetime):
    while True:
        now = datetime.now()
        if now >= target_datetime:
            auto_click()
            break
        time.sleep(0.001)  # 1ms 간격으로 체크 (CPU 부하 최소화)

# 🔹 실행 함수
async def main():
    print("⏳ 서버 시간 동기화 중...")
    server_time, average_rtt = await measure_average_rtt()
    
    if not server_time:
        print("❌ 서버 시간 동기화 실패!")
        return
    
    print(f"🌍 예상 서버 시간 (KST): {server_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⚡ 평균 네트워크 지연 시간 (RTT): {average_rtt:.3f} 초")

    # 🔹 보정된 목표 시간 계산 (RTT 보정)
    target_datetime = datetime.strptime(TARGET_TIME, "%Y-%m-%d %H:%M:%S") - timedelta(seconds=average_rtt)
    print(f"🎯 최적 클릭 예상 시간: {target_datetime.strftime('%Y-%m-%d %H:%M:%S.%f')}")
      
    # 🔹 클릭 실행 스레드 시작
    thread = threading.Thread(target=wait_until_target, args=(target_datetime,))
    thread.start()

# 🔹 실행
asyncio.run(main())
