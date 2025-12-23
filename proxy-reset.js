// 统一替换服务器地址 + 名称直接改为协议类型

function operator(proxies) {
  return proxies.map(p => {
    if (p.type === "hysteria2") {
      p.server = "hy2.xinote.site";
      p.name = "hysteria2";
    } else if (p.type === "trojan") {
      p.server = "trojan.xinote.site";
      p.name = "trojan";
    } else if (p.type === "vless" && p.tls && p.flow === "xtls-rprx-vision" && p["reality-opts"]) {
      p.server = "reality.xinote.site";
      p.name = "reality";
    } else if (p.type === "vless" && p.network === "ws" && p["ws-opts"] && p["ws-opts"].headers && p["ws-opts"].headers["v2ray-http-upgrade"] === "true") {
      p.server = "vless.xinote.site";
      p.name = "vless-upgrade";
    } else if (p.type === "vless" && p.network === "ws") {
      p.server = "ws.xinote.site";
      p.name = "vless-ws";
    }
    return p;
  });
}
