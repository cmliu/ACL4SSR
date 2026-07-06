import os
import shutil
import zipfile
import requests
import re

url = "https://github.com/ipverse/asn-ip/archive/refs/heads/master.zip"
zip_name = "master.zip"

# 输出目录与文件
os.makedirs("Clash", exist_ok=True)  # 确保 Clash 目录存在
clash_path = os.path.join("Clash", "CloudflareCIDR.list")
cidr_path = "CloudflareCIDR.txt"

included_asns = ['209242', '13335', '149648', '132892', '139242', '202623', '203898', '394536']
ip_addresses = []

try:
    # 下载 zip 文件
    r = requests.get(url, timeout=30)
    r.raise_for_status()  # 如果状态不是 200-299，会抛异常
    with open(zip_name, "wb") as f:
        f.write(r.content)

    # 解压 zip 到当前目录
    with zipfile.ZipFile(zip_name, 'r') as zip_ref:
        zip_ref.extractall(".")

        # 尝试从 zip 列表推断根目录（通常是 asn-ip-master 或 asn-ip-<sha>）
        names = zip_ref.namelist()
        root_dirs = [n.split('/')[0] for n in names if n and '/' in n]
        root_dirs = list(dict.fromkeys(root_dirs))  # 去重且保留顺序
        root = root_dirs[0] if root_dirs else "asn-ip-master"

    # 遍历 as 目录（注意使用 os.path.join）
    as_dir = os.path.join(root, "as")
    for root_dir, dirs, files in os.walk(as_dir):
        if 'ipv4-aggregated.txt' in files:
            asn = os.path.basename(root_dir)
            if asn in included_asns:
                with open(os.path.join(root_dir, 'ipv4-aggregated.txt'), 'r') as file:
                    ips = file.read().splitlines()
                    ip_addresses.extend(ips)

    # 匹配 IPv4/CIDR 的简单正则
    ipv4_regex = re.compile(r'^(\d{1,3}\.){3}\d{1,3}(/\d{1,2})$')

    # 写入结果文件
    with open(clash_path, 'w') as clash_file, open(cidr_path, 'w') as cidr_file:
        for ip in ip_addresses:
            if ipv4_regex.match(ip):
                clash_file.write(f"IP-CIDR,{ip},no-resolve\n")
                cidr_file.write(f"{ip}\n")
            else:
                # 如果不是标准 CIDR，按原脚本保留一行（或可以改为跳过）
                clash_file.write(f"{ip}\n")

finally:
    # 清理下载和解压的文件夹，先检查是否存在（避免抛 FileNotFoundError）
    try:
        if os.path.isfile(zip_name):
            os.remove(zip_name)
    except Exception as e:
        print(f"Warning: 删除 {zip_name} 时出错: {e}")

    try:
        # 如果我们推断出的 root 存在则删除
        if 'root' in locals() and os.path.isdir(root):
            shutil.rmtree(root)
        else:
            # 兜底判断常见目录名
            if os.path.isdir("asn-ip-master"):
                shutil.rmtree("asn-ip-master")
    except FileNotFoundError:
        # 已被删除或不存在，忽略
        pass
    except Exception as e:
        print(f"Warning: 删除解压目录时出错: {e}")
