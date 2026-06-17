import os, json

cases_dir = 'cases'
for case_id in os.listdir(cases_dir):
    sess_file = os.path.join(cases_dir, case_id, 'session.json')
    if not os.path.exists(sess_file):
        continue
    with open(sess_file, encoding='utf-8') as f:
        sess = json.load(f)
    if sess.get('doc_type') != 'SD':
        continue
    data = sess.get('data', {})
    ps = data.get('ps', [])
    tc = data.get('title_chain', [])
    print(f'Case: {case_id}')
    if ps:
        p = ps[0]
        print(f'  plot_no: {p.get("plot_no","")}')
        print(f'  const_area: {p.get("const_area","")}')
        print(f'  land_area: {p.get("land_area","")}')
        print(f'  length_ew: {p.get("length_ew","")}')
        print(f'  length_ns: {p.get("length_ns","")}')
        print(f'  n: {p.get("n","")}')
        print(f'  s: {p.get("s","")}')
        print(f'  e: {p.get("e","")}')
        print(f'  w: {p.get("w","")}')
        print(f'  scheme: {p.get("scheme","")}')
        print(f'  village: {p.get("village","")}')
        print(f'  full_address: {p.get("full_address","")}')
        print(f'  dimension_text: {p.get("dimension_text","")}')
        print(f'  boundary_text: {p.get("boundary_text","")}')
    print(f'  title_chain count: {len(tc)}')
    for i, evt in enumerate(tc):
        et = evt.get('event_type','')
        dt = evt.get('date','')
        ex = evt.get('executant_name','')[:40]
        rv = evt.get('reg_vol','')
        rav = evt.get('reg_add_vol','')
        rap = evt.get('reg_add_page','')
        print(f'  [{i}] {et} | {dt} | exec={ex} | vol={rv} | add_vol={rav} | add_page={rap}')
    print()
