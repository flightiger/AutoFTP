#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
   @File : 1.py
   @Time : 2024/5/13 10:17
   @Author : Kevin Zhou
   @Version : Python 3.11
   @Contact : market@visiondatum.com
   @License : (C)Copyright 2008-2023, Vision Datum Technology Co.,Ltd.
   @Desc : None
"""
import os
import time
import ftplib
import socket
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import configparser


class FileEventHandler(FileSystemEventHandler):
    def __init__(self, ftp):
        super().__init__()
        self.ftp = ftp
        self.max_retry_attempts = 7

    def on_created(self, event):
        filepath = event.src_path
        filename = os.path.basename(filepath)
        print(f"发现新文件: {filename}")
        retry_count = 0
        success = False
        while retry_count < self.max_retry_attempts and not success:
            try:
                with open(filepath, "rb") as file:
                    self.ftp.storbinary(f"STOR {filename}", file)
                success = True
                print(f"文件 {filename} 传输成功")
            except Exception as e:
                retry_count += 1
                print(f"传输失败 ({retry_count}/{self.max_retry_attempts}): {e}")
                time.sleep(5)
        if not success:
            print(f"文件 {filename} 传输失败，放弃当前传输")


def connect_ftp(ftp_server, ftp_port, username, password, max_retries=2, timeout=10):
    retry_count = 0
    ftp = None
    while retry_count < max_retries:
        try:
            ftp = ftplib.FTP()
            ftp.connect(ftp_server, ftp_port, timeout=timeout)
            ftp.login(username, password)
            print(f"FTP 连接成功: {ftp_server}")
            print('请不要关闭本窗口，关闭将中断FTP连接......')
            return ftp
        except (socket.timeout, ftplib.error_temp):
            retry_count += 1
            print(f"FTP 连接超时，正在再次尝试 ({retry_count}/{max_retries})")
            time.sleep(5)
        except Exception as e:
            retry_count += 1
            print(f"FTP 连接失败 ({retry_count}/{max_retries}): {e}")
            time.sleep(3)
    return None


# 从外部 ini 文件中读取配置信息
print('微图视觉FTP自动监听文件传输系统1.3.0')
print('请勿关闭本窗口，正在检查配置及尝试连接远程FTP服务器......')
config_file = "config.ini"
config = configparser.ConfigParser()
if os.path.exists(config_file):
    config.read(config_file)
    ftp_server = config.get("FTP", "ip")
    ftp_port = config.getint("FTP", "port")
    username = config.get("FTP", "username")
    password = config.get("FTP", "password")
    monitored_folder_path = config.get("FTP", "monitored_folder_path")

    # FTP 连接
    ftp = connect_ftp(ftp_server, ftp_port, username, password)
    if ftp is None:
        print("FTP连接失败，请检查文件config.ini中FTP配置参数以及远程FTP服务器是否正常！")
        input()
        exit()

    if not os.path.isdir(monitored_folder_path):
        print(f"监控文件夹路径无效: {monitored_folder_path}")
        print("请检查配置文件路径设置，并确保 FTP 监听文件夹路径存在。")
        input()
        exit()

    # 监听文件夹
    event_handler = FileEventHandler(ftp)
    observer = Observer()
    observer.schedule(event_handler, monitored_folder_path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        observer.join()

else:
    print("配置文件不存在。请在程序目录创建配置文件 config.ini 并包含 FTP 服务器地址、用户名、密码和监听文件夹路径。")
    print('请参考以下示例配置文件：\n'
          '[FTP]\n'
          'ip = 192.168.1.1\n'
          'port = 21\n'
          'username = username\n'
          'password = password\n'
          'monitored_folder_path = X:\\path\\to\\files\\Name')
    input()
