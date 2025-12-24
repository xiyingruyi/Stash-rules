function operator(proxies) {
  return proxies.map((proxy) => {
    // Hy2：Hysteria2 类型
    if (proxy.type === 'hysteria2') {
      proxy.server = 'hy2.xinote.site';
      proxy.ports = "30000-50000";
      proxy.port = null;  // 显式设为 null，阻止内核自动生成随机 port
      if (proxy.port === undefined) delete proxy.port;  // 保险起见，双重删除
      if (proxy.auth) {
        proxy.password = proxy.auth;  // 把 auth 值复制到 password
        delete proxy.auth;  // 删除原 auth，避免冲突
      }
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
