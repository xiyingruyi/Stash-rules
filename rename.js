// Sub-Store 全球节点终极美化脚本（2025永久维护版）
// 功能：纯中文名 + 同地区自动聚合 + 自动编号01 02 03 + 固定洲际顺序

const REGIONS = [
  // 亚洲
  { cn: '香港',     keywords: '香港|Hong Kong|HK|HKT|港|🇭🇰',       order: 10 },
  { cn: '台湾',     keywords: '台湾|Taiwan|TW|台北|Taipei|台|🇹🇼',   order: 20 },
  { cn: '日本',     keywords: '日本|Japan|JP|东京|Tokyo|大阪|Osaka|🇯🇵', order: 30 },
  { cn: '韩国',     keywords: '韩国|Korea|KR|首尔|Seoul|韩|🇰🇷',     order: 40 },
  { cn: '新加坡',   keywords: '新加坡|Singapore|SG|狮城|新|🇸🇬',     order: 50 },
  { cn: '马来西亚', keywords: '马来西亚|Malaysia|MY|马来|🇲🇾',      order: 60 },
  { cn: '泰国',     keywords: '泰国|Thailand|TH|曼谷|泰|🇹🇭',       order: 70 },
  { cn: '越南',     keywords: '越南|Vietnam|VN|河内|胡志明|越|🇻🇳', order: 80 },
  { cn: '菲律宾',   keywords: '菲律宾|Philippines|PH|菲|🇵🇭',       order: 90 },
  { cn: '印尼',     keywords: '印尼|Indonesia|ID|雅加达|🇮🇩',       order: 100 },

  // 北美
  { cn: '美国',     keywords: '美国|US|United States|America|洛杉矶|圣何塞|芝加哥|纽约|西雅图|达拉斯|美|🇺🇸', order: 200 },
  { cn: '加拿大',   keywords: '加拿大|Canada|CA|蒙特利尔|多伦多|温哥华|加|🇨🇦', order: 210 },

  // 欧洲
  { cn: '英国',     keywords: '英国|UK|United Kingdom|London|伦敦|英|🇬🇧', order: 300 },
  { cn: '德国',     keywords: '德国|Germany|DE|法兰克福|德|🇩🇪',         order: 310 },
  { cn: '法国',     keywords: '法国|France|FR|巴黎|法|🇫🇷',             order: 320 },
  { cn: '荷兰',     keywords: '荷兰|Netherlands|NL|阿姆斯特丹|荷|🇳🇱',    order: 330 },
  { cn: '瑞士',     keywords: '瑞士|Switzerland|CH|苏黎世|瑞|🇨🇭',       order: 340 },
  { cn: '瑞典',     keywords: '瑞典|Sweden|SE|斯德哥尔摩|瑞典|🇸🇪',       order: 350 },
  { cn: '芬兰',     keywords: '芬兰|Finland|FI|赫尔辛基|芬|🇫🇮',        order: 360 },
  { cn: '意大利',   keywords: '意大利|Italy|IT|米兰|罗马|意|🇮🇹',        order: 370 },
  { cn: '西班牙',   keywords: '西班牙|Spain|ES|马德里|巴塞罗那|西|🇪🇸',   order: 380 },
  { cn: '俄罗斯',   keywords: '俄罗斯|Russia|RU|莫斯科|圣彼得堡|俄|🇷🇺',  order: 390 },

  // 大洋洲
  { cn: '澳大利亚', keywords: '澳大利亚|Australia|AU|悉尼|墨尔本|澳|🇦🇺', order: 500 },
  { cn: '新西兰',   keywords: '新西兰|New Zealand|NZ|奥克兰|🇳🇿',        order: 510 },

  // 南美
  { cn: '巴西',     keywords: '巴西|Brazil|BR|圣保罗|里约|巴|🇧🇷',       order: 600 },
  { cn: '阿根廷',   keywords: '阿根廷|Argentina|AR|布宜诺斯艾利斯|阿根廷|🇦🇷', order: 610 },

  // 其他常见
  { cn: '土耳其',   keywords: '土耳其|Turkey|TR|伊斯坦布尔|土|🇹🇷',      order: 700 },
  { cn: '阿联酋',   keywords: '阿联酋|UAE|Dubai|迪拜|阿联|🇦🇪',          order: 710 },
  { cn: '南非',     keywords: '南非|South Africa|ZA|开普敦|约翰内斯堡|南非|🇿🇦', order: 800 },
];

const counter = {};

function operator(proxies) {
  // 第一步：识别并打标 + 编号
  proxies.forEach(proxy => {
    proxy._regionOrder = 9999;
    proxy._regionName = '其他';

    for (const region of REGIONS) {
      if (new RegExp(region.keywords, 'i').test(proxy.name)) {
        counter[region.cn] = (counter[region.cn] || 0) + 1;
        const num = String(counter[region.cn]).padStart(2, '0');

        proxy.name = `${region.cn} ${num}`;
        proxy._regionOrder = region.order;
        proxy._regionName = region.cn;

        break;
      }
    }
  });

  // 第二步：排序（先按洲际顺序，再按国家内部编号）
  proxies.sort((a, b) => {
    if (a._regionOrder !== b._regionOrder) {
      return a._regionOrder - b._regionOrder;
    }
    return a.name.localeCompare(b.name, 'zh-CN');
  });

  return proxies;
}
