function operator(proxies) {
  return proxies.map(p => {

    // Trojan + WS
    if (p.type === 'trojan') {
      p.server = 'trojan.xinote.site';
      p.port = 443;
      p.tls = true;
      p.sni = 'trojan.xinote.site';
    }

    // VLESS + TLS + WS（排除 reality）
    if (p.type === 'vless' && p.network === 'ws' && p.name !== 'reality-direct') {
      p.server = 'vless.xinote.site';
      p.port = 443;
      p.tls = true;
      p.sni = 'vless.xinote.site';
    }

    // TUIC
    if (p.type === 'tuic') {
      p.server = 'direct.xinote.site';
      p.version = 5;
    }

    // HY2
    if (p.type === 'hysteria2') {
      p.server = 'direct.xinote.site';
    }

    // Reality 节点直接用节点名匹配
    if (p.name === 'reality-direct') {
      p.server = 'direct.xinote.site';
      // 其他字段保持不变
    }

    return p;
  });
}
 
