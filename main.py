from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from utils import global_logger

submit_button_XPATH = "//button[@aria-label='发送提示' and @data-testid='send-button']"
stop_button_XPATH = "//button[@aria-label='停止流式传输' and @data-testid='stop-button']"
prompt_textarea_ID = "prompt-textarea"
conversation_XPATH = "//article[starts-with(@data-testid, 'conversation-turn-')]"
time_to_sleep = 0.5


def wait_for_button_to_change(driver, button_xpath, timeout=30):
    """等待按钮的状态变化"""
    try:
        WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.XPATH, button_xpath)))
        global_logger.info(f"按钮状态变化，当前按钮为：{button_xpath}")
    except TimeoutException:
        global_logger.error(f"等待按钮状态变化时超时：{button_xpath}")


def query_to_answer(driver, query):
    """清空发送框，发送query，等待按钮变化，读取最新的conversation结果"""
    try:
        prompt_textarea = driver.find_element(By.ID, prompt_textarea_ID)
        prompt_textarea.clear()
        prompt_textarea.send_keys(query)
        # 找到发送按钮并点击
        submit_button = driver.find_element(By.XPATH, submit_button_XPATH)
        submit_button.click()
        # 等待按钮变成“停止流式传输”
        wait_for_button_to_change(driver, stop_button_XPATH)
        # 等待按钮变回“发送提示”，表示对话生成完成
        wait_for_button_to_change(driver, submit_button_XPATH)
        time.sleep(time_to_sleep)
        conversation_turns = driver.find_elements(By.XPATH, conversation_XPATH)
        max_turn = 0
        max_element = None
        for turn in conversation_turns:
            data_testid = turn.get_attribute("data-testid")
            turn_number = int(data_testid.split("-")[-1])
            if turn_number > max_turn:
                max_turn = turn_number
                max_element = turn
        # 返回对话结果
        conversation_text = max_element.text if max_element else "没有找到最新对话"
        return conversation_text
    except Exception as e:
        global_logger.error(f"查询对话时发生错误: {e}")


if __name__ == "__main__":
    conversation_id = "6711d5a7-2938-8011-b55f-1465e2538c0f"
    chatgpt_url = "https://chatgpt.com"
    conversation_url = f"{chatgpt_url}/c/{conversation_id}"

    options = Options()
    options.debugger_address = "127.0.0.1:9222"
    driver = webdriver.Chrome(options=options)
    # driver.get(conversation_url)
    query = "介绍周瑜和小乔的故事，200字"
    answer = query_to_answer(driver=driver, query=query)
    print(answer)
