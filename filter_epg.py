#!/usr/bin/env python3
"""
EPG频道筛选工具
根据channel_groups.yml配置文件筛选EPG节目单
"""

import yaml
import xml.etree.ElementTree as ET
import requests
import argparse


def load_channel_groups(config_file):
    """加载频道组配置"""
    with open(config_file, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def get_enabled_channels(channel_groups):
    """获取所有启用的频道列表"""
    enabled_channels = set()
    for group_name in channel_groups.get('enabled_groups', []):
        if group_name in channel_groups:
            enabled_channels.update(channel_groups[group_name])
    return enabled_channels


def download_epg(url):
    """下载EPG文件"""
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.content


def filter_epg(epg_content, enabled_channels):
    """根据启用的频道筛选EPG"""
    root = ET.fromstring(epg_content)
    
    # 创建新的根元素
    new_root = ET.Element(root.tag, root.attrib)
    
    # 存储需要保留的频道ID映射
    channel_id_map = {}
    
    # 筛选频道
    for channel in root.findall('./channel'):
        display_name = channel.find('./display-name').text
        if display_name in enabled_channels:
            # 添加到新的根元素
            new_root.append(channel)
            # 记录频道ID
            channel_id = channel.get('id')
            channel_id_map[channel_id] = True
    
    # 筛选节目
    for programme in root.findall('./programme'):
        channel_id = programme.get('channel')
        if channel_id in channel_id_map:
            new_root.append(programme)
    
    # 生成新的XML内容
    return ET.tostring(new_root, encoding='utf-8', xml_declaration=True)


def main():
    parser = argparse.ArgumentParser(description='EPG频道筛选工具')
    parser.add_argument('--config', default='channel_groups.yml', help='频道组配置文件路径')
    parser.add_argument('--input', default='e.xml', help='输入EPG文件URL或路径')
    parser.add_argument('--output', default='e.xml', help='输出EPG文件路径')
    
    args = parser.parse_args()
    
    print(f"加载频道组配置: {args.config}")
    channel_groups = load_channel_groups(args.config)
    
    enabled_channels = get_enabled_channels(channel_groups)
    print(f"启用的频道数量: {len(enabled_channels)}")
    
    print(f"下载/读取EPG文件: {args.input}")
    if args.input.startswith(('http://', 'https://')):
        epg_content = download_epg(args.input)
    else:
        with open(args.input, 'rb') as f:
            epg_content = f.read()
    
    print("筛选EPG频道...")
    filtered_epg = filter_epg(epg_content, enabled_channels)
    
    print(f"保存筛选后的EPG到: {args.output}")
    with open(args.output, 'wb') as f:
        f.write(filtered_epg)
    
    print("操作完成!")


if __name__ == '__main__':
    main()
