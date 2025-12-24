function operator(proxies) {
  return proxies.map((proxy) => {
    // Hy2：Hysteria2 类型
    if (proxy.type === 'hysteria2') {
      proxy.server = 'hy2.xinote.site';
      proxy.ports = "30000-50000";
      delete proxy.port;  // 删除原有的 port 字段，避免冲突
    }
   
    // Reality：VLESS + Reality 类型（有 reality-opts）
    else if (proxy.type === 'vless' && proxy['reality-opts']) {
      proxy.server = 'reality.xinote.site';
    }
   
    // Trojan 类型
    else if (proxy.type === 'trojan') {
      proxy.server = 'trojan.xinote.site';
    }
   
    // vless-upgrade：VLESS + WS + v2ray-http-upgrade
    else if (
      proxy.type === 'vless' &&
      proxy.network === 'ws' &&
      proxy['ws-opts'] &&
      proxy['ws-opts']['v2ray-http-upgrade'] === true
    ) {
      proxy.server = 'vless.xinote.site';
    }
   
    // vless-ws：普通 VLESS + WS（无 upgrade）
    else if (
      proxy.type === 'vless' &&
      proxy.network === 'ws' &&
      (!proxy['ws-opts'] || proxy['ws-opts']['v2ray-http-upgrade'] !== true)
    ) {
      proxy.server = 'ws.xinote.site';
    }
   
    return proxy;
  });
}
