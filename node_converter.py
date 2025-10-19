import re
import yaml
import json
import base64
from urllib.parse import urlparse, parse_qs
from collections import defaultdict
import os
import sys

# 国家代码到中文名的映射
COUNTRY_MAP = {
    'US': '美国', 'JP': '日本', 'KR': '韩国', 'SG': '新加坡', 'HK': '香港', 'TW': '台湾', 'IN': '印度',
    'GB': '英国', 'DE': '德国', 'FR': '法国', 'CA': '加拿大', 'AU': '澳大利亚', 'NL': '荷兰', 'CH': '瑞士',
    'SE': '瑞典', 'NO': '挪威', 'DK': '丹麦', 'FI': '芬兰', 'IE': '爱尔兰', 'IT': '意大利', 'ES': '西班牙',
    'PT': '葡萄牙', 'BE': '比利时', 'AT': '奥地利', 'PL': '波兰', 'CZ': '捷克', 'HU': '匈牙利', 'RO': '罗马尼亚',
    'BG': '保加利亚', 'GR': '希腊', 'TR': '土耳其', 'RU': '俄罗斯', 'BR': '巴西', 'MX': '墨西哥', 'AR': '阿根廷',
    'CL': '智利', 'CO': '哥伦比亚', 'PE': '秘鲁', 'VE': '委内瑞拉', 'ZA': '南非', 'EG': '埃及', 'NG': '尼日利亚',
    'KE': '肯尼亚', 'GH': '加纳', 'ET': '埃塞俄比亚', 'MA': '摩洛哥', 'TN': '突尼斯', 'IL': '以色列', 'SA': '沙特',
    'AE': '阿联酋', 'QA': '卡塔尔', 'KW': '科威特', 'OM': '阿曼', 'PK': '巴基斯坦', 'BD': '孟加拉国', 'LK': '斯里兰卡',
    'NP': '尼泊尔', 'BT': '不丹', 'MV': '马尔代夫', 'MM': '缅甸', 'TH': '泰国', 'VN': '越南', 'KH': '柬埔寨',
    'LA': '老挝', 'MY': '马来西亚', 'ID': '印尼', 'PH': '菲律宾', 'TL': '东帝汶', 'BN': '文莱',
    'AD': '安道尔', 'AF': '阿富汗', 'AG': '安提瓜和巴布达', 'AI': '安圭拉', 'AL': '阿尔巴尼亚', 'AM': '亚美尼亚', 'AO': '安哥拉',
    'AQ': '南极洲', 'AS': '美属萨摩亚', 'AW': '阿鲁巴', 'AX': '奥兰', 'AZ': '阿塞拜疆', 'BA': '波黑', 'BB': '巴巴多斯',
    'BF': '布基纳法索', 'BH': '巴林', 'BI': '布隆迪', 'BJ': '贝宁', 'BL': '圣巴泰勒米', 'BM': '百慕大', 'BO': '玻利维亚',
    'BQ': '荷兰加勒比区', 'BS': '巴哈马', 'BV': '布韦岛', 'BW': '波札那', 'BY': '白俄罗斯', 'BZ': '伯利兹', 'CC': '科科斯群岛',
    'CD': '刚果金', 'CF': '中非', 'CG': '刚果', 'CI': '科特迪瓦', 'CK': '库克群岛', 'CM': '喀麦隆', 'CN': '中国',
    'CR': '哥斯达黎加', 'CU': '古巴', 'CV': '佛得角', 'CW': '库拉索', 'CX': '圣诞岛', 'CY': '塞浦路斯', 'DJ': '吉布提',
    'DM': '多米尼克', 'DO': '多米尼加', 'DZ': '阿尔及利亚', 'EC': '厄瓜多尔', 'EE': '爱沙尼亚', 'EH': '西撒哈拉', 'ER': '厄立特里亚',
    'FJ': '斐济', 'FK': '福克兰群岛', 'FM': '密克罗尼西亚', 'FO': '法罗群岛', 'GA': '加蓬', 'GD': '格林纳达', 'GE': '格鲁吉亚',
    'GF': '法属圭亚那', 'GG': '根西', 'GI': '直布罗陀', 'GL': '格陵兰', 'GM': '冈比亚', 'GN': '几内亚', 'GP': '瓜德罗普',
    'GQ': '赤道几内亚', 'GS': '南乔治亚岛', 'GT': '危地马拉', 'GU': '关岛', 'GW': '几内亚比绍', 'GY': '圭亚那', 'HM': '赫德岛',
    'HN': '洪都拉斯', 'HR': '克罗地亚', 'HT': '海地', 'IM': '曼岛', 'IO': '英属印度洋领地', 'IQ': '伊拉克', 'IR': '伊朗',
    'IS': '冰岛', 'JE': '泽西', 'JM': '牙买加', 'JO': '约旦', 'KG': '吉尔吉斯', 'KI': '基里巴斯', 'KM': '葛摩',
    'KN': '圣基茨和尼维斯', 'KP': '朝鲜', 'KY': '开曼群岛', 'KZ': '哈萨克斯坦', 'LB': '黎巴嫩', 'LC': '圣卢西亚', 'LI': '列支敦士登',
    'LR': '利比里亚', 'LS': '莱索托', 'LT': '立陶宛', 'LU': '卢森堡', 'LV': '拉脱亚', 'LY': '利比亚', 'MC': '摩纳哥',
    'MD': '摩尔多瓦', 'ME': '黑山', 'MF': '法属圣马丁', 'MG': '马达加斯加', 'MH': '马绍尔群岛', 'MK': '北马其顿', 'ML': '马里',
    'MN': '蒙古', 'MO': '澳门', 'MP': '北马里亚纳群岛', 'MQ': '马提尼克', 'MR': '毛里塔尼亚', 'MS': '蒙特塞拉特', 'MT': '马耳他',
    'MU': '毛里求斯', 'MW': '马拉维', 'MZ': '莫桑比克', 'NA': '纳米比亚', 'NC': '新喀里多尼亚', 'NE': '尼日尔', 'NF': '诺福克岛',
    'NI': '尼加拉瓜', 'NR': '诺鲁', 'NU': '纽埃', 'NZ': '新西兰', 'PA': '巴拿马', 'PF': '法属波利尼西亚', 'PG': '巴布亚新几内亚',
    'PM': '圣皮埃尔和密克隆', 'PN': '皮特凯恩群岛', 'PR': '波多黎各', 'PS': '巴勒斯坦', 'PW': '帛琉', 'PY': '巴拉圭', 'RE': '留尼汪',
    'RS': '塞尔维亚', 'RW': '卢旺达', 'SB': '所罗门群岛', 'SC': '塞舌尔', 'SD': '苏丹', 'SI': '斯洛文尼亚', 'SJ': '斯瓦尔巴',
    'SK': '斯洛伐克', 'SL': '塞拉利昂', 'SM': '圣马力诺', 'SN': '塞内加尔', 'SO': '索马里', 'SR': '苏里南', 'SS': '南苏丹',
    'ST': '圣多美和普林西比', 'SV': '萨尔瓦多', 'SX': '荷属圣马丁', 'SY': '叙利亚', 'SZ': '斯威士兰', 'TC': '特克斯和凯科斯群岛',
    'TD': '乍得', 'TF': '法属南部领地', 'TG': '多哥', 'TJ': '塔吉克斯坦', 'TK': '托克劳', 'TM': '土库曼斯坦', 'TN': '突尼斯',
    'TO': '汤加', 'TT': '特立尼达和多巴哥', 'TV': '图瓦卢', 'TZ': '坦桑尼亚', 'UA': '乌克兰', 'UG': '乌干达', 'UM': '美国本土外小岛屿',
    'UY': '乌拉圭', 'UZ': '乌兹别克斯坦', 'VA': '梵蒂冈', 'VC': '圣文森特和格林纳丁斯', 'VG': '英属维尔京群岛', 'VI': '美属维尔京群岛',
    'VU': '瓦努阿图', 'WF': '瓦利斯和富图纳', 'WS': '萨摩亚', 'YE': '也门', 'YT': '马约特', 'ZM': '赞比亚', 'ZW': '津巴布韦'
}

# 国家代码到国旗表情的映射
COUNTRY_EMOJI_MAP = {
    'US': '🇺🇸', 'JP': '🇯🇵', 'KR': '🇰🇷', 'SG': '🇸🇬', 'HK': '🇭🇰', 'TW': '🇹🇼', 'IN': '🇮🇳',
    'GB': '🇬🇧', 'DE': '🇩🇪', 'FR': '🇫🇷', 'CA': '🇨🇦', 'AU': '🇦🇺', 'NL': '🇳🇱', 'CH': '🇨🇭',
    'SE': '🇸🇪', 'NO': '🇳🇴', 'DK': '🇩🇰', 'FI': '🇫🇮', 'IE': '🇮🇪', 'IT': '🇮🇹', 'ES': '🇪🇸',
    'PT': '🇵🇹', 'BE': '🇧🇪', 'AT': '🇦🇹', 'PL': '🇵🇱', 'CZ': '🇨🇿', 'HU': '🇭🇺', 'RO': '🇷🇴',
    'BG': '🇧🇬', 'GR': '🇬🇷', 'TR': '🇹🇷', 'RU': '🇷🇺', 'BR': '🇧🇷', 'MX': '🇲🇽', 'AR': '🇦🇷',
    'CL': '🇨🇱', 'CO': '🇨🇴', 'PE': '🇵🇪', 'VE': '🇻🇪', 'ZA': '🇿🇦', 'EG': '🇪🇬', 'NG': '🇳🇬',
    'KE': '🇰🇪', 'GH': '🇬🇭', 'ET': '🇪🇹', 'MA': '🇲🇦', 'TN': '🇹🇳', 'IL': '🇮🇱', 'SA': '🇸🇦',
    'AE': '🇦🇪', 'QA': '🇶🇦', 'KW': '🇰🇼', 'OM': '🇴🇲', 'PK': '🇵🇰', 'BD': '🇧🇩', 'LK': '🇱🇰',
    'NP': '🇳🇵', 'BT': '🇧🇹', 'MV': '🇲🇻', 'MM': '🇲🇲', 'TH': '🇹🇭', 'VN': '🇻🇳', 'KH': '🇰🇭',
    'LA': '🇱🇦', 'MY': '🇲🇾', 'ID': '🇮🇩', 'PH': '🇵🇭', 'TL': '🇹🇱', 'BN': '🇧🇳',
    'AD': '🇦🇩', 'AF': '🇦🇫', 'AG': '🇦🇬', 'AI': '🇦🇮', 'AL': '🇦🇱', 'AM': '🇦🇲', 'AO': '🇦🇴',
    'AQ': '🇦🇶', 'AS': '🇦🇸', 'AW': '🇦🇼', 'AX': '🇦🇽', 'AZ': '🇦🇿', 'BA': '🇧🇦', 'BB': '🇧🇧',
    'BF': '🇧🇫', 'BH': '🇧🇭', 'BI': '🇧🇮', 'BJ': '🇧🇯', 'BL': '🇧🇱', 'BM': '🇧🇲', 'BO': '🇧🇴',
    'BQ': '🇧🇶', 'BS': '🇧🇸', 'BV': '🇧🇻', 'BW': '🇧🇼', 'BY': '🇧🇾', 'BZ': '🇧🇿', 'CC': '🇨🇨',
    'CD': '🇨🇩', 'CF': '🇨🇫', 'CG': '🇨🇬', 'CI': '🇨🇮', 'CK': '🇨🇰', 'CM': '🇨🇲', 'CN': '🇨🇳',
    'CR': '🇨🇷', 'CU': '🇨🇺', 'CV': '🇨🇻', 'CW': '🇨🇼', 'CX': '🇨🇽', 'CY': '🇨🇾', 'DJ': '🇩🇯',
    'DM': '🇩🇲', 'DO': '🇩🇴', 'DZ': '🇩🇿', 'EC': '🇪🇨', 'EE': '🇪🇪', 'EH': '🇪🇭', 'ER': '🇪🇷',
    'FJ': '🇫🇯', 'FK': '🇫🇰', 'FM': '🇫🇲', 'FO': '🇫🇴', 'GA': '🇬🇦', 'GD': '🇬🇩', 'GE': '🇬🇪',
    'GF': '🇬🇫', 'GG': '🇬🇬', 'GI': '🇬🇮', 'GL': '🇬🇱', 'GM': '🇬🇲', 'GN': '🇬🇳', 'GP': '🇬🇵',
    'GQ': '🇬🇶', 'GS': '🇬🇸', 'GT': '🇬🇹', 'GU': '🇬🇺', 'GW': '🇬🇼', 'GY': '🇬🇾', 'HM': '🇭🇲',
    'HN': '🇭🇳', 'HR': '🇭🇷', 'HT': '🇭🇹', 'IM': '🇮🇲', 'IO': '🇮🇴', 'IQ': '🇮🇶', 'IR': '🇮🇷',
    'IS': '🇮🇸', 'JE': '🇯🇪', 'JM': '🇯🇲', 'JO': '🇯🇴', 'KG': '🇰🇬', 'KI': '🇰🇮', 'KM': '🇰🇲',
    'KN': '🇰🇳', 'KP': '🇰🇵', 'KY': '🇰🇾', 'KZ': '🇰🇿', 'LB': '🇱🇧', 'LC': '🇱🇨', 'LI': '🇱🇮',
    'LR': '🇱🇷', 'LS': '🇱🇸', 'LT': '立陶宛', 'LU': '卢森堡', 'LV': '拉脱亚', 'LY': '利比亚', 'MC': '摩纳哥',
    'MD': '摩尔多瓦', 'ME': '黑山', 'MF': '法属圣马丁', 'MG': '马达加斯加', 'MH': '马绍尔群岛', 'MK': '北马其顿', 'ML': '马里',
    'MN': '蒙古', 'MO': '澳门', 'MP': '北马里亚纳群岛', 'MQ': '马提尼克', 'MR': '毛里塔尼亚', 'MS': '蒙特塞拉特', 'MT': '马耳他',
    'MU': '毛里求斯', 'MW': '马拉维', 'MZ': '莫桑比克', 'NA': '纳米比亚', 'NC': '新喀里多尼亚', 'NE': '尼日尔', 'NF': '诺福克岛',
    'NI': '尼加拉瓜', 'NR': '诺鲁', 'NU': '纽埃', 'NZ': '新西兰', 'PA': '巴拿马', 'PF': '法属波利尼西亚', 'PG': '巴布亚新几内亚',
    'PM': '圣皮埃尔和密克隆', 'PN': '皮特凯恩群岛', 'PR': '波多黎各', 'PS': '巴勒斯坦', 'PW': '帛琉', 'PY': '巴拉圭', 'RE': '留尼汪',
    'RS': '塞尔维亚', 'RW': '卢旺达', 'SB': '所罗门群岛', 'SC': '塞舌尔', 'SD': '苏丹', 'SI': '斯洛文尼亚', 'SJ': '斯瓦尔巴',
    'SK': '斯洛伐克', 'SL': '塞拉利昂', 'SM': '圣马力诺', 'SN': '塞内加尔', 'SO': '索马里', 'SR': '苏里南', 'SS': '南苏丹',
    'ST': '圣多美和普林西比', 'SV': '萨尔瓦多', 'SX': '荷属圣马丁', 'SY': '叙利亚', 'SZ': '斯威士兰', 'TC': '特克斯和凯科斯群岛',
    'TD': '乍得', 'TF': '法属南部领地', 'TG': '多哥', 'TJ': '塔吉克斯坦', 'TK': '托克劳', 'TM': '土库曼斯坦', 'TN': '突尼斯',
    'TO': '汤加', 'TT': '特立尼达和多巴哥', 'TV': '图瓦卢', 'TZ': '坦桑尼亚', 'UA': '乌克兰', 'UG': '乌干达', 'UM': '美国本土外小岛屿',
    'UY': '乌拉圭', 'UZ': '乌兹别克斯坦', 'VA': '梵蒂冈', 'VC': '圣文森特和格林纳丁斯', 'VG': '英属维尔京群岛', 'VI': '美属维尔京群岛',
    'VU': '瓦努阿图', 'WF': '瓦利斯和富图纳', 'WS': '萨摩亚', 'YE': '也门', 'YT': '马约特', 'ZM': '赞ambia', 'ZW': '津巴布韦'
}

def parse_vless_uri(uri):
    """Parse VLESS URI to extract proxy parameters."""
    parsed = urlparse(uri)
    if not parsed.scheme == 'vless':
        raise ValueError("Invalid VLESS URI")
    username = parsed.username
    hostname = parsed.hostname
    port = parsed.port
    query = parse_qs(parsed.query)
    params = {
        'type': 'vless',
        'server': hostname,
        'port': port,
        'uuid': username,
        'network': query.get('type', ['tcp'])[0],
        'tls': query.get('security', ['none'])[0] == 'tls',
        'flow': query.get('flow', [None])[0],
        'sni': query.get('sni', [None])[0],
        'path': query.get('path', [None])[0]
    }
    return {k: v for k, v in params.items() if v is not None}

def parse_trojan_uri(uri):
    """Parse Trojan URI to extract proxy parameters."""
    parsed = urlparse(uri)
    if not parsed.scheme == 'trojan':
        raise ValueError("Invalid Trojan URI")
    username = parsed.username
    hostname = parsed.hostname
    port = parsed.port
    query = parse_qs(parsed.query)
    params = {
        'type': 'trojan',
        'server': hostname,
        'port': port,
        'password': username,
        'sni': query.get('sni', [None])[0],
        'network': query.get('type', ['tcp'])[0],
        'path': query.get('path', [None])[0]
    }
    return {k: v for k, v in params.items() if v is not None}

def parse_vmess_uri(uri):
    """Parse VMess URI to extract proxy parameters."""
    parsed = urlparse(uri)
    if not parsed.scheme == 'vmess':
        raise ValueError("Invalid VMess URI")
    # VMess URI 的 base64 编码部分
    encoded = parsed.netloc.split('@')[0]
    try:
        decoded = json.loads(base64.b64decode(encoded).decode('utf-8'))
    except Exception as e:
        raise ValueError(f"Invalid VMess URI encoding: {e}")
    params = {
        'type': 'vmess',
        'server': parsed.hostname,
        'port': parsed.port or decoded.get('port'),
        'uuid': decoded.get('id'),
        'alterId': decoded.get('aid', 0),
        'network': decoded.get('net', 'tcp'),
        'path': decoded.get('path'),
        'tls': decoded.get('tls') == 'tls',
        'sni': decoded.get('sni')
    }
    return {k: v for k, v in params.items() if v is not None}

def extract_country_from_name(name):
    """Extract country code from node name (e.g., '🇹🇷 TR 土耳其 1' -> 'TR')."""
    match = re.search(r'\b([A-Z]{2})\b', name)
    return match.group(1) if match else None

def is_known_country(country):
    """Check if country code is in COUNTRY_MAP."""
    return country in COUNTRY_MAP

def generate_node_name(country, seq):
    """Generate node name with country, emoji, and sequence."""
    emoji = COUNTRY_EMOJI_MAP.get(country, '🇺🇳')
    chinese = COUNTRY_MAP.get(country, '未知')
    return f"{emoji} {country} {chinese} {seq}"

def print_country_stats(country_counts):
    """Print country stats in a formatted grid (5 columns, aligned with spacing, sorted by count descending)."""
    if not country_counts:
        print("未找到任何国家统计。")
        return
    
    country_list = sorted(country_counts.items(), key=lambda x: x[1], reverse=True)
    
    # Print title
    title = f"按国家统计的有效节点数 ({len(country_list)} 个)"
    print(f"\n[{title}]")
    
    # Calculate max width for each item
    max_width = 0
    for country, count in country_list:
        chinese = COUNTRY_MAP.get(country, '未知')
        emoji = COUNTRY_EMOJI_MAP.get(country, '🇺🇳')
        item = f"{emoji} {country} {chinese}: {count}"
        max_width = max(max_width, len(item))
    
    # Column width = max_width + 2 (for spacing)
    col_width = max_width + 2
    
    # Print in rows of 5 columns
    for i in range(0, len(country_list), 5):
        row_items = country_list[i:i+5]
        row = []
        for country, count in row_items:
            chinese = COUNTRY_MAP.get(country, '未知')
            emoji = COUNTRY_EMOJI_MAP.get(country, '🇺🇳')
            item = f"{emoji} {country} {chinese}: {count}"
            row.append(item.ljust(col_width))  # Left-align and pad
        print(''.join(row))  # Join without extra separators; padding provides spacing

def main(input_file, output_file):
    """Main function to process input_nodes.txt and generate YAML."""
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"读取输入文件失败: {e}")
        return

    nodes_by_country = defaultdict(list)
    country_counts = defaultdict(int)
    total_skipped_format = 0
    total_remaining = 0
    
    for line in lines:
        try:
            base_uri, name = line.split('#', 1) if '#' in line else (line, '')
            base_uri = base_uri.strip()
            name = name.strip() if name else base_uri
        except:
            total_skipped_format += 1
            continue
    
        country = extract_country_from_name(name)
        if country and is_known_country(country):
            nodes_by_country[country].append((base_uri, name))
            country_counts[country] += 1
            total_remaining += 1
    
    proxies = []
    for country, node_list in nodes_by_country.items():
        for seq, (base_uri, orig_name) in enumerate(node_list, 1):
            scheme = base_uri.split('://', 1)[0] if '://' in base_uri else ''
            params = None
            try:
                if scheme == 'vless':
                    params = parse_vless_uri(base_uri)
                elif scheme == 'trojan':
                    params = parse_trojan_uri(base_uri)
                elif scheme == 'vmess':
                    params = parse_vmess_uri(base_uri)
            except ValueError as e:
                total_skipped_format += 1
                continue
            except Exception:
                total_skipped_format += 1
                continue
    
            if params:
                node_name = generate_node_name(country, seq)
                params['name'] = node_name
                proxies.append(params)
            else:
                total_skipped_format += 1
    
    config = {'proxies': proxies}
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    except Exception as e:
        print(f"写入 YAML 文件失败: {e}")
        return
    
    print("---------------------------------------")
    print("节点转换完成")
    print("---------------------------------------")
    print(f"总节点 URI 数量 (过滤前): {len(lines)}")
    print(f"成功转换节点数: {len(proxies)}")
    print(f"因格式错误或不支持协议跳过数: {total_skipped_format}")
    
    print_country_stats(country_counts)
    
    print("\n---------------------------------------")
    print(f"已生成 Stash 纯节点源 YAML 文件: {output_file}")
    print("提示: 此文件可上传到 GitHub/Gist 作为远程订阅链接。")
    print("---------------------------------------")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python node_converter.py <input_file> <output_file>")
        print("示例: python node_converter.py input_nodes.txt nodes.yaml")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    main(input_file, output_file)