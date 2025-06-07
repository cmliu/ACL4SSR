import os
import shutil
import zipfile
import requests
import re  # 导入正则表达式库

# 下载zip文件
url = "https://github.com/ipverse/asn-ip/archive/refs/heads/master.zip"
r = requests.get(url)
with open("master.zip", "wb") as code:
  code.write(r.content)

# 解压zip文件
with zipfile.ZipFile("master.zip", 'r') as zip_ref:
  zip_ref.extractall(".")

# 将结果存储在这个列表中
ip_addresses = []
included_asns = ['209242', '13335', '149648', '132892', '139242', '202623', '203898', '394536']

# 遍历as文件夹
for root, dirs, files in os.walk("asn-ip-master/as"):
  if 'ipv4-aggregated.txt' in files:
    asn = root.split('/')[-1]
    if asn in included_asns:
      with open(os.path.join(root, 'ipv4-aggregated.txt'), 'r') as file:
        ips = file.read().splitlines()
        ip_addresses.extend(ips)

# 正则表达式用于匹配IPv4地址和子网掩码
ipv4_regex = re.compile(r'^(\d{1,3}\.){3}\d{1,3}(/\d{1,2})$')

# 将结果写入两个文件
with open('Clash/CloudflareCIDR.list', 'w') as clash_file, \
     open('CloudflareCIDR.txt', 'w') as cidr_file:
  for ip in ip_addresses:
    # 检查IP是否符合IPv4/子网掩码格式
    if ipv4_regex.match(ip):
      clash_file.write(f"IP-CIDR,{ip},no-resolve\n")
      cidr_file.write(f"{ip}\n")
    else:
      clash_file.write(f"{ip}\n")

# 清理下载的zip文件和解压的文件夹
os.remove("master.zip")
shutil.rmtree("asn-ip-master")
