import json

raw_text = """```json
{
  "05-06-2026": "{{rd}}",
  "Jh eukst dqekj": "{{ss[0].n}}",
  "Jh fHkok jke": "{{ss[0].rn}}",
  "36": "{{ss[0].a}}",
  "Hkknok] tkscusj] t;iqjjkt-": "{{ss[0].adr}}",
  "eksuw dqekjh": "{{bs[0].n}}",
  "Jh jkeorkj eh.kk": "{{bs[0].rn}}",
  "28": "{{bs[0].a}}",
  "eh.kk": "{{bs[0].c}}",
  "okMZ u- 3] Hkkfroj] >qU>quw jkt-": "{{bs[0].adr}}",
  "vkoklh; iwohZ Hkkx IykV uEcj&15": "{{ps[0].plot_no}}",
  "ckykth uxj": "{{ps[0].scheme}}",
  "gkFkkst": "{{ps[0].village}}",
  "dkyokM jksM] >ksVokMk] t;iqj] jktLFkku": "{{ps[0].adr}}",
  "iwoZ ls if'pe 13 fQV 6 bZap rFkk mRrj ls nf{k.k 50 fQV": "{{ps[0].land_area_dimensions}}",
  "75 oxZxt": "{{ps[0].land_area}}",
  "IykV u- 14": "{{ps[0].e}}",
  "IykV u- 15 dk 'ks"k ifpe Hkkx": "{{ps[0].w}}",
  "jksM 20 fQV pkSMh vkenjQr ljdkjh": "{{ps[0].n}}",
  "vU; Hkwfe": "{{ps[0].s}}",
  "675 oxZfQV": "{{ps[0].const_area}}",
  "Jherh tfeyk [kkrwu iRuh Jh vkye 'ksj [kkrwu": "{{title_chain[0].owner}}",
  "vkoaVu i=": "{{title_chain[0].deed_type}}",
  "11-06-1996": "{{title_chain[0].date}}",
  "Jh vuqy dqekj iq= Jh guqeku lgk;": "{{title_chain[1].owner}}",
  "10-10-2016": "{{title_chain[1].date}}",
  "Jh Jo.k dqekj dksBkjh iq= Jh panxh jke": "{{title_chain[2].owner}}",
  "25-10-2022": "{{title_chain[2].date}}",
  "iathd`r fo; i=": "{{title_chain[3].deed_type}}",
  "06-011-2025": "{{title_chain[3].date}}",
  "iath;u dk;kZy;] mi iath;d t;iqj&r`rh; ds ;gka": "{{title_chain[3].reg_office}}",
  "12-11-2025": "{{title_chain[3].reg_date}}",
  "1": "{{title_chain[3].book}}",
  "1243": "{{title_chain[3].vol}}",
  "108": "{{title_chain[3].page}}",
  "202503017117125": "{{title_chain[3].reg_no}}",
  "vfrfjDr iqLrd la[khk 1": "{{title_chain[3].add_book}}",
  "4996": "{{title_chain[3].add_vol}}",
  "497 ls 512": "{{title_chain[3].add_page}}",
  "Canfin Homes Ltd.": "{{hypothecation}}",
  "26]50,000": "{{amount}}",
  "Nchl yk[k ipkl gtkj :i;s ek=": "{{amount_words}}",
  "jke fuokl dqekor": "{{ws[0].n}}",
  "Jh dUgS;k yky dqekor": "{{ws[0].rn}}",
  "ts&539] vktkn uxj] jkdMh lksMkyk] t;iqj": "{{ws[0].adr}}",
  "vt; xqtZj": "{{ws[1].n}}",
  "Jh ccyw xqtZj": "{{ws[1].rn}}",
  "97&,] izrki uxj] t;iqj": "{{ws[1].adr}}"
}
```"""

import re
m = re.search(r'```json\s*(.*?)\s*```', raw_text, re.DOTALL | re.IGNORECASE)
if m:
    try:
        data = json.loads(m.group(1))
        print("Success! Parsed", len(data), "items.")
    except Exception as e:
        print("Failed to parse inside code block:", e)
else:
    print("Could not match markdown block.")
