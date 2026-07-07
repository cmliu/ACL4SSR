import os
import sys
import requests

# 需要拉取的 ASN 列表
included_asns = ['209242', '13335', '149648', '132892', '139242', '202623', '203898', '394536']

asn_data_list = []

print("开始获取 ASN 数据...")
for asn in included_asns:
    url = f"https://raw.githubusercontent.com/ipverse/as-ip-blocks/refs/heads/master/as/{asn}/aggregated.json"
    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        data = response.json()
        asn_data_list.append(data)
        print(f"ASN {asn} 下载成功")
    except Exception as e:
        print(f"错误: 下载 ASN {asn} 数据失败: {e}")
        sys.exit(1)

# 确保 Clash 目录存在
os.makedirs('Clash', exist_ok=True)

# 写入输出文件
print("开始整理并写入本地文件...")
with open('Clash/CloudflareCIDR.list', 'w', encoding='utf-8') as clash_file, \
     open('CloudflareCIDR.txt', 'w', encoding='utf-8') as cidr_file:
     
    for data in asn_data_list:
        asn = data.get("asn", "")
        metadata = data.get("metadata", {})
        handle = metadata.get("handle", "") or ""
        description = metadata.get("description", "") or ""
        
        # 写入 Clash 格式的注释头部
        clash_file.write(f"# AS{asn} ({handle.strip()})\n")
        clash_file.write(f"# {description.strip()}\n")
        clash_file.write("#\n")
        
        # 写入 IPv4 列表
        ipv4_prefixes = data.get("prefixes", {}).get("ipv4", [])
        for ip in ipv4_prefixes:
            clash_file.write(f"IP-CIDR,{ip},no-resolve\n")
            cidr_file.write(f"{ip}\n")

print("所有 ASN 数据下载并整理完成！")

