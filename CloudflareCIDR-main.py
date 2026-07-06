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

def safe_remove_file(path):
    try:
        if os.path.isfile(path):
            os.remove(path)
    except Exception as e:
        print(f"Warning: 删除文件 {path} 时出错: {e}")

def safe_rmtree(path):
    """
    更稳健地删除目录：
    - 如果目录不存在则静默返回
    - 对可能的 OSError/FileNotFoundError 做捕获
    - 尝试使用 ignore_errors=True 作为兜底（在某些场景下更稳妥）
    """
    try:
        if not path:
            return
        # 只在路径存在且为目录时调用 rmtree
        if os.path.isdir(path):
            # 优先直接调用 rmtree，捕获常见异常
            try:
                shutil.rmtree(path)
            except FileNotFoundError:
                # 竞态导致已被删除，忽略
                pass
            except PermissionError as e:
                # 权限问题时打印警告并尝试 ignore_errors 作为兜底
                print(f"Warning: 删除目录 {path} 时权限错误: {e}, 尝试 ignore_errors=True")
                try:
                    shutil.rmtree(path, ignore_errors=True)
                except Exception:
                    pass
            except OSError as e:
                # 其他 OS 级错误，尝试 ignore_errors
                print(f"Warning: 删除目录 {path} 时出错: {e}, 尝试 ignore_errors=True")
                try:
                    shutil.rmtree(path, ignore_errors=True)
                except Exception:
                    pass
    except Exception as e:
        # 最外层兜底，确保不会把异常抛到 workflow 里导致失败
        print(f"Warning: safe_rmtree 异常: {e}")

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
    # 清理下载和解压的文件夹，使用安全删除函数，避免抛出未捕获异常导致 job 失败
    safe_remove_file(zip_name)

    # 删除推断出的 root 目录或常见目录名（都使用 safe_rmtree）
    if 'root' in locals():
        safe_rmtree(root)
    # 兜底：常见目录名
    safe_rmtree("asn-ip-master")
