#!/usr/bin/env python3
# node_converter.py
# Reads input_nodes.txt and writes nodes.yaml (overwrite each time)
import re, base64, json, yaml

def decode_base64(data):
    data = data.strip().replace('\n','').replace(' ','')
    pad = len(data) % 4
    if pad: data += '=' * (4 - pad)
    return base64.b64decode(data)

def parse_vmess(uri):
    payload = uri.split('://',1)[1]
    try:
        data = json.loads(decode_base64(payload).decode('utf-8'))
        return {
            'name': data.get('ps') or data.get('id','vmess'),
            'server': data.get('add') or '',
            'port': int(data.get('port',0)),
            'uuid': data.get('id',''),
            'type': 'vmess'
        }
    except Exception:
        return None

def parse_vless(uri):
    m = re.match(r'vless://([^@]+)@([^:]+):(\d+)', uri)
    if not m: return None
    uuid, host, port = m.groups()
    return {'name': host, 'server': host, 'port': int(port), 'uuid': uuid, 'type': 'vless'}

def parse_trojan(uri):
    m = re.match(r'trojan://([^@]+)@([^:]+):(\d+)', uri)
    if not m: return None
    pwd, host, port = m.groups()
    return {'name': host, 'server': host, 'port': int(port), 'password': pwd, 'type': 'trojan'}

def main():
    txt = open('input_nodes.txt','r',encoding='utf-8',errors='ignore').read()
    uris = re.findall(r'(vmess://[^\s]+|vless://[^\s]+|trojan://[^\s]+)', txt)
    nodes = []
    for u in uris:
        p = None
        if u.startswith('vmess://'): p = parse_vmess(u)
        elif u.startswith('vless://'): p = parse_vless(u)
        elif u.startswith('trojan://'): p = parse_trojan(u)
        if p: nodes.append(p)
    yaml.safe_dump({'proxies': nodes}, open('nodes.yaml','w',encoding='utf-8'), allow_unicode=True)
    print('Wrote nodes.yaml with', len(nodes), 'nodes')

if __name__ == '__main__':
    main()