import os
import logging
from dotenv import dotenv_values
import psutil
import time, requests
import sys
import subprocess
import pandas as pd
import shutil

global_logger = None


def setup_logging():
    """配置全局日志记录器，输出到控制台和日志文件"""
    global global_logger
    global_logger = logging.getLogger("global_logger")
    global_logger.setLevel(logging.INFO)
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    # 创建文件处理器
    file_handler = logging.FileHandler("running.log")
    file_handler.setLevel(logging.DEBUG)  # 文件日志级别
    # 创建格式化器
    formatter = logging.Formatter("%(asctime)s - %(name)s - [%(filename)s:%(lineno)d] - %(levelname)s - %(message)s")
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # 将处理器添加到日志记录器
    if not global_logger.hasHandlers():
        global_logger.addHandler(console_handler)
        global_logger.addHandler(file_handler)
    return global_logger


# 配置全局日志记录器
global_logger = setup_logging()


def wait_for_health_check(url, headers=None, timeout=60):
    """等待服务器健康检查通过."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(5)
    return False


def get_process_pid(command_keywords_list):
    for proc in psutil.process_iter(["pid", "cmdline"]):
        cmdline = proc.info["cmdline"]
        if cmdline:  # 检查 cmdline 是否非空
            cmdline_str = " ".join(cmdline)  # 将命令行参数列表连接成字符串
            # 检查命令行是否包含所有的关键字
            if all(keyword in cmdline_str for keyword in command_keywords_list):
                # 检查是否直接运行 python，而不是通过 /bin/sh -c 调用
                if "/bin/sh" not in cmdline_str:
                    return proc.info["pid"]
    return None  # 如果没有匹配的进程，返回 None


def get_container_pid(container_name_or_id):
    """根据容器名或容器ID获取容器的主进程PID"""
    try:
        # 通过 docker inspect 获取容器的主进程 PID
        pid = subprocess.check_output(["docker", "inspect", "--format", "'{{.State.Pid}}'", container_name_or_id])
        # 清理输出并转换为整数
        return int(pid.strip().decode("utf-8").replace("'", ""))
    except subprocess.CalledProcessError as e:
        print(f"Error getting PID for container {container_name_or_id}: {e}")
        return None


def write_dict_to_csv(data, filename):
    # 追加字典数据为pd
    df = pd.DataFrame(data)
    if os.path.exists(filename):
        existing_df = pd.read_csv(filename)
        existing_columns = existing_df.columns.tolist()
        for col in existing_columns:
            if col not in df.columns:
                df[col] = None
        for col in df.columns:
            if col not in existing_columns:
                existing_df[col] = None
        # 按照新数据的列顺序，合并并写入数据
        combined_df = pd.concat([existing_df, df], ignore_index=True)
        # 覆盖模式写入数据，确保表头和数据的一致性
        combined_df.to_csv(filename, mode="w", header=True, index=False)
    else:
        # 如果文件不存在，直接写入数据
        df.to_csv(filename, mode="w", header=True, index=False)


def clear_folders(directory_path):
    # 清除文件夹下面所有的文件夹，文件除外
    for item in os.listdir(directory_path):
        item_path = os.path.join(directory_path, item)
        if os.path.isdir(item_path):
            shutil.rmtree(item_path)
        else:
            pass
