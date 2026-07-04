"""
Stock Intelligence Report Generator
Produces a self-contained HTML report from assembled stock data.
All charts drawn on Canvas; zero external dependencies.
"""
import html as _html
import json

# ── Helpers ───────────────────────────────────────────────────────────────────

LABEL_META = {
    'STRONG_CANDIDATE': {'color': '#00D87C', 'bg': '#002914', 'label': 'STRONG BUY'},
    'EMERGING':         {'color': '#06B6A4', 'bg': '#003028', 'label': 'EMERGING'},
    'WATCHLIST':        {'color': '#3DA0FF', 'bg': '#001E3A', 'label': 'WATCHLIST'},
    'NEUTRAL':          {'color': '#F5A024', 'bg': '#2A1800', 'label': 'NEUTRAL'},
    'AVOID':            {'color': '#F04A4A', 'bg': '#2A0808', 'label': 'AVOID'},
}

def _sc(v) -> str:
    n = float(v or 0)
    if n >= 75: return '#00D87C'
    if n >= 60: return '#3DA0FF'
    if n >= 40: return '#F5A024'
    return '#F04A4A'

def _rc(v) -> str:
    if v is None: return '#4D6A90'
    n = float(v)
    if n > 0: return '#00D87C'
    if n < 0: return '#F04A4A'
    return '#4D6A90'

def _v(val, dec=1, fallback='--') -> str:
    if val is None: return fallback
    try:
        n = float(val)
        return f'{n:.{dec}f}'
    except: return fallback

def _pct(val, sign=False, fallback='--') -> str:
    if val is None: return fallback
    try:
        n = float(val)
        s = '+' if n >= 0 and sign else ''
        return f'{s}{n:.1f}%'
    except: return fallback

def _cr(val, fallback='--') -> str:
    if val is None: return fallback
    try:
        n = float(val)
        if abs(n) >= 100_000: return f'&#x20B9;{n/100_000:.1f}L Cr'
        if abs(n) >= 1_000:   return f'&#x20B9;{n/1_000:.1f}K Cr'
        return f'&#x20B9;{n:.0f} Cr'
    except: return fallback

def _h(val) -> str:
    if val is None: return ''
    return _html.escape(str(val))


# ── Main generator ────────────────────────────────────────────────────────────

def generate_report_html(symbol: str, data: dict) -> str:
    sym    = symbol.upper()
    label  = str(data.get('label') or 'NEUTRAL')
    close  = data.get('close_now') or (data.get('technical') or {}).get('close_now')
    sector = str(data.get('sector') or '')
    regime = str(data.get('market_regime') or '')
    score  = float(data.get('bull_run_score') or 0)
    as_of  = str(data.get('as_of_date') or '')[:10]

    lm = LABEL_META.get(label, LABEL_META['NEUTRAL'])
    lcolor, lbg, llabel = lm['color'], lm['bg'], lm['label']

    ml      = data.get('ml_scores') or {}
    ml_bull = float(ml.get('ml_bull_run_score') or 0)
    accum   = float(ml.get('accumulation_score') or 0)
    fwd_r   = float(ml.get('forward_return_score') or 0)
    fwd_p   = ml.get('forward_return_prob')

    comps    = data.get('components') or {}
    c_price  = float(comps.get('price_score')       or 0)
    c_sector = float(comps.get('sector_flow_score')  or 0)
    c_deal   = float(comps.get('deal_score')         or 0)
    c_corp   = float(comps.get('corporate_score')    or 0)

    pr      = data.get('price') or {}
    ret30   = pr.get('ret_30d')
    ret90   = pr.get('ret_90d')
    ret365  = pr.get('ret_365d')
    volr    = pr.get('vol_ratio')
    ret7    = pr.get('ret_7d')
    ret15   = pr.get('ret_15d')
    chg1d   = pr.get('change_1d_pct')
    chg1dA  = pr.get('change_1d_abs')

    t       = data.get('technical') or {}
    h52     = t.get('high_52w')
    l52     = t.get('low_52w')
    dma20   = t.get('dma_20')
    dma50   = t.get('dma_50')
    dma200  = t.get('dma_200')
    vs20    = t.get('vs_dma_20')
    vs50    = t.get('vs_dma_50')
    vs200   = t.get('vs_dma_200')
    prox52h = t.get('prox_52w_high')
    trend   = str(t.get('trend_signal') or '')
    vol_avg = t.get('vol_20d_avg')

    f       = data.get('fundamentals') or {}
    pe      = f.get('pe_ratio')
    roe     = f.get('roe_pct')
    roce    = f.get('roce_pct')
    opm     = f.get('opm_pct')
    bvps    = f.get('book_value_per_share')
    rev_ttm = f.get('revenue_ttm_cr')
    pft_ttm = f.get('profit_ttm_cr')
    mcap    = f.get('market_cap_cr')
    val_lbl = str(f.get('valuation_label') or '')
    yoy_rev = f.get('yoy_revenue_pct')
    yoy_pft = f.get('yoy_profit_pct')
    sg_3y   = f.get('sales_growth_3y_pct')

    shp      = data.get('shareholding') or {}
    promo    = shp.get('promoter_pct')
    fii_pct  = shp.get('fii_pct')
    dii_pct  = shp.get('dii_pct')
    pub_pct  = shp.get('public_pct')
    shp_date = str(shp.get('quarter_end_date') or '')

    ht_list = data.get('holding_trends') or []
    fii_d = dii_d = pro_d = None
    if ht_list:
        ht = ht_list[-1]
        fii_d = ht.get('fii_delta')
        dii_d = ht.get('dii_delta')
        pro_d = ht.get('promoter_delta')

    mgmt       = data.get('management') or {}
    mgmt_label = str(mgmt.get('management_label') or '')
    mgmt_score = mgmt.get('management_score')

    fno_d  = data.get('fno') or {}
    oi_sig = str(fno_d.get('oi_signal') or '')
    fut_oi = fno_d.get('futures_oi')
    oi_1d  = fno_d.get('oi_1d')
    oi_5d  = fno_d.get('oi_5d')

    agm      = data.get('agm') or {}
    gov_risk = str(agm.get('governance_risk') or '')
    gov_sc   = agm.get('governance_score') or 50
    key_dec  = str(agm.get('key_decision') or '')

    news   = data.get('news') or {}
    n_cnt  = news.get('news_count_7d')
    n_sent = str(news.get('sentiment_label') or '')

    cc_d    = data.get('concall') or {}
    cc_sent = str(cc_d.get('sentiment') or '')
    cc_guid = str(cc_d.get('guidance_direction') or '')
    cc_stmt = str(cc_d.get('key_statement') or '')

    insights = data.get('analyst_insights') or []

    deal_d   = data.get('deal_signals') or {}
    inst_net = deal_d.get('inst_net_value_cr')
    deal_sig = str(deal_d.get('deal_signal') or '')

    cc_corp  = data.get('corporate_confidence') or {}
    corp_conf = cc_corp.get('confidence_score')

    con_d  = data.get('consensus') or {}
    con_sc = con_d.get('consensus_score')
    con_lb = str(con_d.get('consensus_label') or '')

    qr_list = data.get('quarterly_results') or []

    # ── Display helpers ───────────────────────────────────────────────────────
    TREND_COLORS = {
        'STRONG_UPTREND':   ('#00D87C', 'STRONG UPTREND'),
        'UPTREND':          ('#3DA0FF', 'UPTREND'),
        'SIDEWAYS':         ('#F5A024', 'SIDEWAYS'),
        'DOWNTREND':        ('#F04A4A', 'DOWNTREND'),
        'STRONG_DOWNTREND': ('#F04A4A', 'STRONG DOWNTREND'),
    }
    trend_color, trend_disp = TREND_COLORS.get(trend, ('#4D6A90', _h(trend) or 'N/A'))

    OI_COLORS = {
        'LONG_BUILDUP':   '#00D87C',
        'SHORT_COVERING': '#3DA0FF',
        'SHORT_BUILDUP':  '#F04A4A',
        'LONG_UNWINDING': '#F5A024',
    }
    oi_color = OI_COLORS.get(oi_sig, '#4D6A90')

    VAL_COLORS = {'FAIR_VALUE': '#3DA0FF', 'UNDERVALUED': '#00D87C', 'CHEAP': '#00D87C', 'EXPENSIVE': '#F04A4A'}
    val_color = VAL_COLORS.get(val_lbl, '#4D6A90')

    MGMT_COLORS = {'STRONG_BULLISH': '#00D87C', 'BULLISH': '#3DA0FF', 'NEUTRAL': '#F5A024', 'BEARISH': '#F04A4A', 'STRONG_BEARISH': '#F04A4A'}
    mgmt_color = MGMT_COLORS.get(mgmt_label, '#4D6A90')

    NEWS_COLORS = {'BULLISH': '#00D87C', 'POSITIVE': '#00D87C', 'BEARISH': '#F04A4A', 'NEUTRAL': '#F5A024'}
    news_color = NEWS_COLORS.get(n_sent, '#4D6A90')

    GOV_COLORS = {'LOW': '#00D87C', 'MEDIUM': '#F5A024', 'HIGH': '#F04A4A'}
    gov_color = GOV_COLORS.get(gov_risk, '#4D6A90')

    # JS data for canvas drawing
    pub_computed = max(0.0, 100.0 - float(promo or 0) - float(fii_pct or 0) - float(dii_pct or 0))
    js_data = json.dumps({
        'scores': {
            'bull': round(score, 1), 'ml_bull': round(ml_bull, 1),
            'accum': round(accum, 1), 'fwd': round(fwd_r, 1),
        },
        'components': {
            'price': round(c_price, 1), 'sector': round(c_sector, 1),
            'deal': round(c_deal, 1), 'corp': round(c_corp, 1),
        },
        'shareholding': {
            'promoter': float(promo or 0), 'fii': float(fii_pct or 0),
            'dii': float(dii_pct or 0), 'public': pub_computed,
        },
        'momentum': {
            '7d': float(ret7 or 0), '15d': float(ret15 or 0),
            '30d': float(ret30 or 0), '90d': float(ret90 or 0), '365d': float(ret365 or 0),
        },
        'vs_dma': {
            '20': float(vs20 or 0), '50': float(vs50 or 0), '200': float(vs200 or 0),
        },
        'label_color': lcolor,
    }, ensure_ascii=True)

    # ── Quarterly results table rows ──────────────────────────────────────────
    qr_rows_html = ''
    for q in qr_list[:4]:
        period = str(q.get('period') or q.get('period_end_date') or q.get('quarter_end_date') or '')[:10]
        rev    = _cr(q.get('revenue_cr') or q.get('revenue'))
        pft    = q.get('net_profit_cr') or q.get('net_profit')
        pft_v  = _cr(pft)
        eps    = _v(q.get('eps'), dec=2)
        p_col  = _rc(pft)
        yoy_p  = q.get('yoy_profit_pct')
        yoy_v  = _pct(yoy_p, sign=True)
        yoy_c  = _rc(yoy_p)
        qr_rows_html += f'''
        <tr>
          <td style="color:#8AAED0">{_h(period)}</td>
          <td style="font-family:'Courier New',monospace">{rev}</td>
          <td style="font-family:'Courier New',monospace;color:{p_col}">{pft_v}</td>
          <td style="font-family:'Courier New',monospace">{eps}</td>
          <td style="font-family:'Courier New',monospace;color:{yoy_c}">{yoy_v}</td>
        </tr>'''

    # ── Insights HTML ─────────────────────────────────────────────────────────
    insight_cards = ''
    for i, ins in enumerate(insights[:6]):
        insight_cards += f'<div class="insight-card"><div class="insight-num">{i+1:02d}</div><p>{_h(ins)}</p></div>'

    # ── Shareholding delta row ────────────────────────────────────────────────
    def _delta_badge(v, label):
        if v is None: return ''
        n = float(v)
        c = '#00D87C' if n > 0 else '#F04A4A' if n < 0 else '#4D6A90'
        s = f'+{n:.2f}%' if n > 0 else f'{n:.2f}%'
        return f'<span style="font-size:10px;color:{c};font-family:\'Courier New\',monospace">{label} {s} QoQ</span>'

    shp_deltas = ' &nbsp; '.join(filter(None, [
        _delta_badge(pro_d, 'PRO'),
        _delta_badge(fii_d, 'FII'),
        _delta_badge(dii_d, 'DII'),
    ]))

    # ── ML interpretation text ────────────────────────────────────────────────
    def _ml_interp():
        lines = []
        if ml_bull >= 75:
            lines.append(f'ML Bull Run Score of <b>{ml_bull:.0f}</b> signals high-conviction bullish setup — model sees alignment across price momentum, institutional flow, and fundamentals.')
        elif ml_bull >= 60:
            lines.append(f'ML Bull Run Score of <b>{ml_bull:.0f}</b> indicates a building opportunity — multiple positive signals without full confirmation yet.')
        elif ml_bull >= 40:
            lines.append(f'ML Bull Run Score of <b>{ml_bull:.0f}</b> reflects a mixed picture — some bullish signals present but offset by weaker areas.')
        else:
            lines.append(f'ML Bull Run Score of <b>{ml_bull:.0f}</b> suggests caution — the model does not yet see a compelling setup in this stock.')

        if accum >= 65:
            lines.append(f'Accumulation Score of <b>{accum:.0f}</b> indicates active institutional buying or volume-price patterns consistent with accumulation.')
        elif accum <= 35:
            lines.append(f'Accumulation Score of <b>{accum:.0f}</b> suggests distribution may be occurring — volume patterns do not confirm institutional buying.')

        if fwd_r >= 70:
            lines.append(f'Forward Return Model predicts <b>above-average</b> returns over the next 45 days based on historical analogs with similar feature profiles.')
        elif fwd_r <= 35:
            lines.append(f'Forward Return Model sees <b>limited near-term upside</b> relative to the broader universe — current setup resembles low-return historical analogs.')

        dominant = max([('Price Momentum', c_price), ('Sector Flow', c_sector), ('Deal Signals', c_deal), ('Corp Actions', c_corp)], key=lambda x: x[1])
        if dominant[1] > 60:
            lines.append(f'Primary driver of the composite score: <b>{dominant[0]}</b> ({dominant[1]:.0f}/100) — this signal carried the most weight in the model\'s assessment.')

        return ' '.join(lines) if lines else 'Model assessment based on 24 features across 5 signal categories.'

    ml_interp = _ml_interp()

    # ── Phase status note for sector ──────────────────────────────────────────
    sector_note = f.get('_sector_note', '')

    # ── Price display ─────────────────────────────────────────────────────────
    close_disp = f'&#x20B9;{float(close):.2f}' if close else 'N/A'

    # Pre-compute any HTML with font-family single-quotes (Python 3.11 f-string restriction)
    _ret30_hero = ''
    if ret30 is not None:
        _col = _rc(ret30)
        _val = _pct(ret30, sign=True)
        _ret30_hero = ('<div style="font-family:\'Courier New\',monospace;'
                       'font-size:12px;color:' + _col + ';margin-top:4px">'
                       + _val + ' 30D</div>')

    _chg1d_hero = ''
    if chg1d is not None:
        _c   = _rc(chg1d)
        _arr = '&#9650;' if float(chg1d) >= 0 else '&#9660;'
        _s   = ('+' if float(chg1d) >= 0 else '') + f'{float(chg1d):.2f}%'
        _abs_part = ''
        if chg1dA is not None:
            _abs_sign = '+' if float(chg1dA) >= 0 else ''
            _abs_part = (' <span style="font-size:11px;opacity:0.8">('
                         + _abs_sign + '&#x20B9;' + f'{abs(float(chg1dA)):.2f}' + ')</span>')
        _chg1d_hero = ('<div style="font-family:\'Courier New\',monospace;'
                       'font-size:15px;font-weight:800;color:' + _c + ';margin-top:6px;line-height:1.2">'
                       + _arr + ' ' + _s + _abs_part + '</div>'
                       '<div style="font-size:9px;color:#4D6A90;letter-spacing:1px">1 DAY CHANGE</div>')

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{_h(sym)} Intelligence Report — Capital Flow Platform</title>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html {{ font-size: 14px; }}
  body {{
    background: #060A14;
    color: #C8D8EC;
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    line-height: 1.5;
    min-height: 100vh;
  }}
  .verdict-band {{
    height: 6px;
    background: {lcolor};
    width: 100%;
  }}
  .page {{ max-width: 1200px; margin: 0 auto; padding: 0 24px 48px; }}
  /* ── Hero ── */
  .hero {{
    padding: 28px 0 20px;
    border-bottom: 1px solid #1A2E48;
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 24px;
    align-items: start;
  }}
  .hero-sym {{
    font-family: 'Courier New', monospace;
    font-size: 48px;
    font-weight: 800;
    color: #E8F0FC;
    letter-spacing: -1px;
    line-height: 1;
  }}
  .hero-sector {{
    font-size: 12px;
    color: #4D6A90;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-top: 6px;
  }}
  .hero-meta {{
    display: flex;
    gap: 10px;
    margin-top: 12px;
    flex-wrap: wrap;
    align-items: center;
  }}
  .hero-right {{ text-align: right; }}
  .hero-price {{
    font-family: 'Courier New', monospace;
    font-size: 36px;
    font-weight: 700;
    color: #E8F0FC;
  }}
  .hero-date {{ font-size: 11px; color: #4D6A90; margin-top: 6px; }}
  .pill {{
    display: inline-flex;
    align-items: center;
    padding: 3px 10px;
    border-radius: 3px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    font-family: 'Courier New', monospace;
  }}
  .regime-pill {{
    border: 1px solid #1A2E48;
    color: #4D6A90;
    background: transparent;
    font-size: 11px;
    padding: 3px 8px;
    border-radius: 3px;
    font-family: 'Courier New', monospace;
  }}
  /* ── Sections ── */
  section {{ margin-top: 28px; }}
  .section-title {{
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    color: #4D6A90;
    border-bottom: 1px solid #1A2E48;
    padding-bottom: 8px;
    margin-bottom: 16px;
  }}
  /* ── Score gauges ── */
  .gauges {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }}
  .gauge-box {{
    background: #0D1525;
    border: 1px solid #1A2E48;
    border-radius: 6px;
    padding: 12px 8px 8px;
    text-align: center;
  }}
  .gauge-canvas {{ display: block; margin: 0 auto; }}
  .gauge-label {{
    font-size: 10px;
    color: #4D6A90;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-top: 6px;
  }}
  .gauge-sub {{
    font-size: 9px;
    color: #2D4060;
    margin-top: 2px;
  }}
  /* ── 2-column grid ── */
  .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
  .card {{
    background: #0D1525;
    border: 1px solid #1A2E48;
    border-radius: 6px;
    padding: 18px;
  }}
  .card-title {{
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #4D6A90;
    margin-bottom: 14px;
  }}
  /* ── Stat grid ── */
  .stat-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }}
  .stat-grid-3 {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }}
  .stat {{
    background: #111D35;
    border: 1px solid #1A2E48;
    border-radius: 4px;
    padding: 10px 12px;
  }}
  .stat-label {{
    font-size: 9px;
    color: #4D6A90;
    text-transform: uppercase;
    letter-spacing: 1.5px;
  }}
  .stat-value {{
    font-family: 'Courier New', monospace;
    font-size: 18px;
    font-weight: 700;
    line-height: 1.2;
    margin-top: 3px;
  }}
  .stat-sub {{
    font-size: 10px;
    color: #4D6A90;
    margin-top: 2px;
  }}
  /* ── Bar chart ── */
  .bar-row {{
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 10px;
  }}
  .bar-label {{
    font-size: 11px;
    color: #8AAED0;
    width: 52px;
    flex-shrink: 0;
  }}
  .bar-track {{
    flex: 1;
    height: 6px;
    background: #1A2E48;
    border-radius: 3px;
    position: relative;
    overflow: visible;
  }}
  .bar-fill {{
    height: 100%;
    border-radius: 3px;
    position: absolute;
    top: 0;
    transition: width 0.5s ease;
  }}
  .bar-zero {{
    position: absolute;
    top: -4px;
    width: 1px;
    height: 14px;
    background: #2D4060;
  }}
  .bar-val {{
    font-family: 'Courier New', monospace;
    font-size: 11px;
    width: 52px;
    text-align: right;
    flex-shrink: 0;
  }}
  /* ── DMA table ── */
  .dma-row {{
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 8px;
  }}
  .dma-label {{ font-size: 11px; color: #4D6A90; width: 50px; }}
  .dma-val   {{ font-family: 'Courier New', monospace; font-size: 12px; width: 70px; }}
  .dma-pct   {{ font-family: 'Courier New', monospace; font-size: 11px; width: 58px; }}
  /* ── ML section ── */
  .ml-section {{
    background: #0A1422;
    border: 1px solid {lcolor}30;
    border-left: 3px solid {lcolor};
    border-radius: 6px;
    padding: 20px 24px;
  }}
  .ml-header {{
    display: flex;
    align-items: baseline;
    gap: 12px;
    margin-bottom: 16px;
  }}
  .ml-title {{
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    color: #4D6A90;
  }}
  .ml-model-tag {{
    font-size: 10px;
    padding: 2px 8px;
    border-radius: 2px;
    background: #111D35;
    border: 1px solid #1A2E48;
    color: #4D6A90;
    font-family: 'Courier New', monospace;
  }}
  .ml-scores-row {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin-bottom: 18px;
  }}
  .ml-score-box {{
    background: #0D1525;
    border: 1px solid #1A2E48;
    border-radius: 4px;
    padding: 12px;
    text-align: center;
  }}
  .ml-score-num {{
    font-family: 'Courier New', monospace;
    font-size: 28px;
    font-weight: 800;
    line-height: 1;
  }}
  .ml-score-name {{ font-size: 9px; color: #4D6A90; text-transform: uppercase; letter-spacing: 1.5px; margin-top: 4px; }}
  .ml-score-desc {{ font-size: 9px; color: #2D4060; margin-top: 2px; }}
  .ml-components {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
    margin-bottom: 16px;
  }}
  .ml-comp {{
    background: #111D35;
    border: 1px solid #1A2E48;
    border-radius: 4px;
    padding: 10px 12px;
  }}
  .ml-comp-label {{ font-size: 9px; color: #4D6A90; text-transform: uppercase; letter-spacing: 1px; }}
  .ml-comp-bar {{
    margin-top: 6px;
    height: 4px;
    background: #1A2E48;
    border-radius: 2px;
    overflow: hidden;
  }}
  .ml-comp-fill {{ height: 100%; border-radius: 2px; }}
  .ml-comp-val {{
    font-family: 'Courier New', monospace;
    font-size: 13px;
    font-weight: 700;
    margin-top: 4px;
  }}
  .ml-interp {{
    font-size: 12px;
    color: #8AAED0;
    line-height: 1.7;
    border-top: 1px solid #1A2E48;
    padding-top: 14px;
  }}
  .ml-feature-grid {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 6px;
    margin-top: 14px;
  }}
  .ml-feature {{
    background: #111D35;
    border: 1px solid #1A2E48;
    border-radius: 3px;
    padding: 6px 10px;
    font-size: 10px;
    color: #4D6A90;
  }}
  .ml-feature span {{
    display: block;
    font-family: 'Courier New', monospace;
    color: #8AAED0;
    font-size: 9px;
    margin-top: 2px;
  }}
  /* ── Insights ── */
  .insights-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }}
  .insight-card {{
    background: #0D1525;
    border: 1px solid #1A2E48;
    border-radius: 6px;
    padding: 14px 16px;
    display: grid;
    grid-template-columns: 28px 1fr;
    gap: 10px;
    align-items: start;
  }}
  .insight-num {{
    font-family: 'Courier New', monospace;
    font-size: 20px;
    font-weight: 800;
    color: #1A2E48;
    line-height: 1;
    padding-top: 2px;
  }}
  .insight-card p {{ font-size: 12px; color: #8AAED0; line-height: 1.65; }}
  /* ── Quarterly table ── */
  .qr-table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
  .qr-table th {{
    font-size: 9px;
    font-weight: 700;
    color: #4D6A90;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    padding: 0 8px 8px 0;
    text-align: left;
    border-bottom: 1px solid #1A2E48;
  }}
  .qr-table td {{
    padding: 7px 8px 7px 0;
    border-bottom: 1px solid #111D35;
    vertical-align: middle;
  }}
  /* ── Signal rows ── */
  .sig-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 7px 0;
    border-bottom: 1px solid #111D35;
    font-size: 12px;
  }}
  .sig-row:last-child {{ border-bottom: none; }}
  .sig-key {{ color: #4D6A90; }}
  .sig-val {{ font-family: 'Courier New', monospace; }}
  /* ── Footer ── */
  footer {{
    margin-top: 40px;
    padding-top: 16px;
    border-top: 1px solid #1A2E48;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 10px;
    color: #2D4060;
  }}
  .canvas-wrapper {{ position: relative; }}
  @media print {{
    body {{ background: #fff; color: #000; }}
    .verdict-band {{ print-color-adjust: exact; -webkit-print-color-adjust: exact; }}
    .page {{ padding: 0; }}
    section {{ page-break-inside: avoid; }}
  }}
  @media (max-width: 800px) {{
    .gauges {{ grid-template-columns: repeat(2, 1fr); }}
    .grid-2 {{ grid-template-columns: 1fr; }}
    .ml-scores-row {{ grid-template-columns: repeat(2, 1fr); }}
    .ml-components {{ grid-template-columns: repeat(2, 1fr); }}
    .insights-grid {{ grid-template-columns: 1fr; }}
  }}
</style>
</head>
<body>
<div class="verdict-band"></div>
<div class="page">

  <!-- ── HERO ─────────────────────────────────────────────────────────────── -->
  <div class="hero">
    <div>
      <div class="hero-sym">{_h(sym)}</div>
      <div class="hero-sector">{_h(sector)}</div>
      <div class="hero-meta">
        <span class="pill" style="background:{lbg};color:{lcolor};border:1px solid {lcolor}40">{_h(llabel)}</span>
        {f'<span class="pill" style="background:#111D35;color:{val_color};border:1px solid {val_color}40">{_h(val_lbl.replace("_"," "))}</span>' if val_lbl else ''}
        {f'<span class="pill" style="background:#111D35;color:{trend_color};border:1px solid {trend_color}40">{trend_disp}</span>' if trend else ''}
        {f'<span class="regime-pill">{_h(regime)}</span>' if regime else ''}
        {f'<span class="pill" style="background:#111D35;color:{oi_color};border:1px solid {oi_color}40">{_h(oi_sig.replace("_"," "))}</span>' if oi_sig else ''}
      </div>
    </div>
    <div class="hero-right">
      <div class="hero-price">{close_disp}</div>
      {_chg1d_hero}
      {_ret30_hero}
      <div class="hero-date">Report as of {_h(as_of)} &nbsp;&bull;&nbsp; Capital Flow Intelligence Platform</div>
    </div>
  </div>

  <!-- ── INTELLIGENCE SCORES ───────────────────────────────────────────────── -->
  <section>
    <div class="section-title">Intelligence Scores</div>
    <div class="gauges">
      <div class="gauge-box">
        <canvas id="g-bull" class="gauge-canvas" width="160" height="100"></canvas>
        <div class="gauge-label">Bull Run Score</div>
        <div class="gauge-sub">4-factor composite</div>
      </div>
      <div class="gauge-box">
        <canvas id="g-ml" class="gauge-canvas" width="160" height="100"></canvas>
        <div class="gauge-label">ML Bull Run</div>
        <div class="gauge-sub">LightGBM + XGBoost</div>
      </div>
      <div class="gauge-box">
        <canvas id="g-acc" class="gauge-canvas" width="160" height="100"></canvas>
        <div class="gauge-label">Accumulation</div>
        <div class="gauge-sub">XGBoost binary model</div>
      </div>
      <div class="gauge-box">
        <canvas id="g-fwd" class="gauge-canvas" width="160" height="100"></canvas>
        <div class="gauge-label">Forward Return</div>
        <div class="gauge-sub">45-day prediction</div>
      </div>
    </div>
  </section>

  <!-- ── MOMENTUM + FUNDAMENTALS ──────────────────────────────────────────── -->
  <section>
    <div class="grid-2">
      <!-- Price Momentum -->
      <div class="card">
        <div class="card-title">Price Momentum</div>
        <div class="bar-row">
          <div class="bar-label">7 Day</div>
          <div class="bar-track" id="bt-7">
            <div class="bar-zero" id="bz-7"></div>
            <div class="bar-fill" id="bf-7"></div>
          </div>
          <div class="bar-val" id="bv-7" style="color:{_rc(ret7)}">{_pct(ret7,sign=True)}</div>
        </div>
        <div class="bar-row">
          <div class="bar-label">15 Day</div>
          <div class="bar-track" id="bt-15">
            <div class="bar-zero" id="bz-15"></div>
            <div class="bar-fill" id="bf-15"></div>
          </div>
          <div class="bar-val" id="bv-15" style="color:{_rc(ret15)}">{_pct(ret15,sign=True)}</div>
        </div>
        <div class="bar-row">
          <div class="bar-label">30 Day</div>
          <div class="bar-track" id="bt-30">
            <div class="bar-zero" id="bz-30"></div>
            <div class="bar-fill" id="bf-30"></div>
          </div>
          <div class="bar-val" id="bv-30" style="color:{_rc(ret30)}">{_pct(ret30,sign=True)}</div>
        </div>
        <div class="bar-row">
          <div class="bar-label">90 Day</div>
          <div class="bar-track" id="bt-90">
            <div class="bar-zero" id="bz-90"></div>
            <div class="bar-fill" id="bf-90"></div>
          </div>
          <div class="bar-val" id="bv-90" style="color:{_rc(ret90)}">{_pct(ret90,sign=True)}</div>
        </div>
        <div class="bar-row">
          <div class="bar-label">1 Year</div>
          <div class="bar-track" id="bt-365">
            <div class="bar-zero" id="bz-365"></div>
            <div class="bar-fill" id="bf-365"></div>
          </div>
          <div class="bar-val" id="bv-365" style="color:{_rc(ret365)}">{_pct(ret365,sign=True)}</div>
        </div>
        <div class="bar-row" style="margin-top:6px">
          <div class="bar-label" style="color:#4D6A90">Vol Ratio</div>
          <div class="bar-track">
            <div class="bar-fill" style="width:{min(100,float(volr or 0)*50):.0f}%;background:#3DA0FF;"></div>
          </div>
          <div class="bar-val" style="color:#3DA0FF">{_v(volr,'1')}x</div>
        </div>

        {f'<div style="margin-top:14px"><div style="font-size:9px;color:#4D6A90;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:8px">52-Week Range</div>' if h52 and l52 else ''}
        {_52w_range_html(close, l52, h52) if h52 and l52 else ''}
        {'</div>' if h52 and l52 else ''}
      </div>

      <!-- Fundamentals -->
      <div class="card">
        <div class="card-title">Fundamentals</div>
        {'<div style="font-size:10px;color:#F5A024;margin-bottom:10px;padding:6px 8px;background:#2A180020;border-radius:3px">Banking/NBFC XBRL taxonomy pending — financials may be incomplete</div>' if sector_note == 'BANKING_XBRL_PENDING' else ''}
        <div class="stat-grid">
          <div class="stat">
            <div class="stat-label">P/E Ratio</div>
            <div class="stat-value" style="color:{_pe_color(pe)}">{_v(pe,'1')}</div>
          </div>
          <div class="stat">
            <div class="stat-label">ROE</div>
            <div class="stat-value" style="color:{_sc(roe) if roe and float(roe)>0 else '#F04A4A'}">{_pct(roe)}</div>
          </div>
          <div class="stat">
            <div class="stat-label">ROCE</div>
            <div class="stat-value" style="color:{_sc(roce) if roce and float(roce)>0 else '#4D6A90'}">{_pct(roce)}</div>
          </div>
          <div class="stat">
            <div class="stat-label">OPM</div>
            <div class="stat-value" style="color:{_sc(opm) if opm else '#4D6A90'}">{_pct(opm)}</div>
          </div>
          <div class="stat">
            <div class="stat-label">Revenue TTM</div>
            <div class="stat-value" style="font-size:14px;color:#8AAED0">{_cr(rev_ttm)}</div>
            {f'<div class="stat-sub" style="color:{_rc(yoy_rev)}">YoY {_pct(yoy_rev,sign=True)}</div>' if yoy_rev is not None else ''}
          </div>
          <div class="stat">
            <div class="stat-label">Net Profit TTM</div>
            <div class="stat-value" style="font-size:14px;color:{_rc(pft_ttm)}">{_cr(pft_ttm)}</div>
            {f'<div class="stat-sub" style="color:{_rc(yoy_pft)}">YoY {_pct(yoy_pft,sign=True)}</div>' if yoy_pft is not None else ''}
          </div>
          <div class="stat">
            <div class="stat-label">Market Cap</div>
            <div class="stat-value" style="font-size:14px;color:#8AAED0">{_cr(mcap)}</div>
          </div>
          <div class="stat">
            <div class="stat-label">Book Value / Share</div>
            <div class="stat-value" style="font-size:14px;color:#8AAED0">&#x20B9;{_v(bvps,'1')}</div>
            {f'<div class="stat-sub">Sales CAGR {_pct(sg_3y)}</div>' if sg_3y is not None else ''}
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- ── SHAREHOLDING + TECHNICAL ─────────────────────────────────────────── -->
  <section>
    <div class="grid-2">
      <!-- Shareholding -->
      <div class="card">
        <div class="card-title">Shareholding Pattern {f'&mdash; {_h(shp_date)}' if shp_date else ''}</div>
        <div style="display:grid;grid-template-columns:auto 1fr;gap:16px;align-items:center">
          <canvas id="g-shp" width="140" height="140"></canvas>
          <div>
            {_shp_legend('Promoter', promo, pro_d, '#9B6DFF')}
            {_shp_legend('FII / FPI', fii_pct, fii_d, '#3DA0FF')}
            {_shp_legend('DII', dii_pct, dii_d, '#06B6A4')}
            {_shp_legend('Public', pub_pct if pub_pct is not None else (100 - float(promo or 0) - float(fii_pct or 0) - float(dii_pct or 0)), None, '#F5A024')}
          </div>
        </div>
        {f'<div style="margin-top:10px;font-size:10px;color:#4D6A90">{shp_deltas}</div>' if shp_deltas else ''}
      </div>

      <!-- Technical Signals -->
      <div class="card">
        <div class="card-title">Technical Signals</div>
        <div style="margin-bottom:12px">
          <div class="dma-row">
            <div class="dma-label" style="color:#4D6A90">DMA</div>
            <div class="dma-val" style="color:#4D6A90;font-size:10px">Price</div>
            <div class="dma-pct" style="color:#4D6A90;font-size:10px">vs DMA</div>
            <div style="font-size:10px;color:#4D6A90">Signal</div>
          </div>
          {_dma_row('20 DMA', dma20, vs20)}
          {_dma_row('50 DMA', dma50, vs50)}
          {_dma_row('200 DMA', dma200, vs200)}
        </div>
        <div class="stat-grid-3" style="margin-top:8px">
          <div class="stat">
            <div class="stat-label">52W High</div>
            <div class="stat-value" style="font-size:14px;color:#8AAED0">&#x20B9;{_v(h52,'0')}</div>
            {f'<div class="stat-sub" style="color:{_rc((float(prox52h or 0)-100) if prox52h else None)}">{_pct(prox52h and float(prox52h)-100,sign=True)} off high</div>' if prox52h else ''}
          </div>
          <div class="stat">
            <div class="stat-label">52W Low</div>
            <div class="stat-value" style="font-size:14px;color:#8AAED0">&#x20B9;{_v(l52,'0')}</div>
          </div>
          <div class="stat">
            <div class="stat-label">Avg Volume 20D</div>
            <div class="stat-value" style="font-size:13px;color:#8AAED0">{_vol_disp(vol_avg)}</div>
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- ── ML INTELLIGENCE ──────────────────────────────────────────────────── -->
  <section>
    <div class="section-title">ML Intelligence — What the Models Have Learned</div>
    <div class="ml-section">
      <div class="ml-header">
        <span class="ml-title">Ensemble AI Analysis</span>
        <span class="ml-model-tag">XGBoost v3.2</span>
        <span class="ml-model-tag">LightGBM v4.6</span>
        <span class="ml-model-tag">24 Features</span>
        <span class="ml-model-tag">Phase 12C</span>
      </div>

      <!-- 4 ML score boxes -->
      <div class="ml-scores-row">
        <div class="ml-score-box">
          <div class="ml-score-num" style="color:{_sc(score)}">{score:.0f}</div>
          <div style="font-size:8px;color:#4D6A90;margin-top:2px">/ 100</div>
          <div class="ml-score-name">Bull Run Score</div>
          <div class="ml-score-desc">4-factor composite</div>
        </div>
        <div class="ml-score-box">
          <div class="ml-score-num" style="color:{_sc(ml_bull)}">{ml_bull:.0f}</div>
          <div style="font-size:8px;color:#4D6A90;margin-top:2px">/ 100</div>
          <div class="ml-score-name">ML Bull Run</div>
          <div class="ml-score-desc">LGB + XGB ensemble</div>
        </div>
        <div class="ml-score-box">
          <div class="ml-score-num" style="color:{_sc(accum)}">{accum:.0f}</div>
          <div style="font-size:8px;color:#4D6A90;margin-top:2px">/ 100</div>
          <div class="ml-score-name">Accumulation</div>
          <div class="ml-score-desc">Binary classifier</div>
        </div>
        <div class="ml-score-box">
          <div class="ml-score-num" style="color:{_sc(fwd_r)}">{fwd_r:.0f}</div>
          <div style="font-size:8px;color:#4D6A90;margin-top:2px">/ 100</div>
          <div class="ml-score-name">Fwd Return</div>
          <div class="ml-score-desc">45-day horizon {f'({float(fwd_p)*100:.0f}% prob)' if fwd_p else ''}</div>
        </div>
      </div>

      <!-- Component scores — what fed the ML -->
      <div style="font-size:10px;color:#4D6A90;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:8px">
        Signal Components (inputs to ML models)
      </div>
      <div class="ml-components">
        {_ml_comp('Price Momentum', c_price, 'ret_30/60/90/365d, vol_ratio, vol_score')}
        {_ml_comp('Sector Flow', c_sector, 'FII/DII/PRO sector attribution score')}
        {_ml_comp('Deal Signals', c_deal, 'Block/bulk deal net flow, inst. conviction')}
        {_ml_comp('Corp Actions', c_corp, 'Dividend, buyback, corporate confidence')}
      </div>

      <!-- Feature taxonomy -->
      <div style="font-size:10px;color:#4D6A90;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:8px">
        Feature Categories (24 total across 5 groups)
      </div>
      <div class="ml-feature-grid">
        <div class="ml-feature">Price &amp; Momentum<span>ret_30d/60d/90d/365d, vol_ratio, price_score, RSI, MACD</span></div>
        <div class="ml-feature">Technical Patterns<span>Bollinger bands, ADX, 20/50/200 DMA position, trend signal</span></div>
        <div class="ml-feature">Sector Intelligence<span>Sector flow z-score, rotation signal, FII/DII attribution</span></div>
        <div class="ml-feature">Institutional Flows<span>Block/bulk deal net, deal signal, institutional conviction</span></div>
        <div class="ml-feature">Fundamentals<span>P/E, ROE, OPM, revenue growth, book value per share</span></div>
        <div class="ml-feature">F&amp;O Signals<span>Futures OI delta, OI signal (long/short buildup)</span></div>
      </div>

      <!-- Interpretation -->
      <div class="ml-interp">{ml_interp}</div>
    </div>
  </section>

  <!-- ── QUARTERLY RESULTS ─────────────────────────────────────────────────── -->
  {_qr_section(qr_rows_html) if qr_rows_html else ''}

  <!-- ── INSTITUTIONAL + F&O ──────────────────────────────────────────────── -->
  <section>
    <div class="grid-2">
      <!-- Institutional -->
      <div class="card">
        <div class="card-title">Institutional &amp; Concall Signals</div>
        <div class="sig-row">
          <div class="sig-key">Inst. Net Flow (30D)</div>
          <div class="sig-val" style="color:{_rc(inst_net)}">{_cr(inst_net)}</div>
        </div>
        <div class="sig-row">
          <div class="sig-key">Deal Signal</div>
          <div class="sig-val" style="color:{_deal_color(deal_sig)}">{_h(deal_sig.replace('_',' '))}</div>
        </div>
        <div class="sig-row">
          <div class="sig-key">Corp. Confidence</div>
          <div class="sig-val" style="color:{_sc(corp_conf)}">{_v(corp_conf,'1')}/100</div>
        </div>
        <div class="sig-row">
          <div class="sig-key">Management</div>
          <div class="sig-val" style="color:{mgmt_color}">{_h(mgmt_label.replace('_',' '))}</div>
        </div>
        {f'<div class="sig-row"><div class="sig-key">Concall Sentiment</div><div class="sig-val" style="color:{NEWS_COLORS.get(cc_sent, "#4D6A90")}">{_h(cc_sent.replace("_"," "))}</div></div>' if cc_sent else ''}
        {f'<div class="sig-row"><div class="sig-key">Guidance</div><div class="sig-val" style="color:{_rc_dir(cc_guid)}">{_h(cc_guid.replace("_"," "))}</div></div>' if cc_guid else ''}
        {f'<div style="margin-top:10px;font-size:11px;color:#4D6A90;font-style:italic;line-height:1.6">&ldquo;{_h(cc_stmt[:200])}&rdquo;</div>' if cc_stmt and cc_stmt not in ('None','nan','') else ''}
      </div>

      <!-- F&O -->
      <div class="card">
        <div class="card-title">F&amp;O Intelligence</div>
        <div class="sig-row">
          <div class="sig-key">OI Signal</div>
          <div class="sig-val" style="color:{oi_color}">{_h(oi_sig.replace('_',' '))}</div>
        </div>
        <div class="sig-row">
          <div class="sig-key">Futures OI</div>
          <div class="sig-val" style="color:#8AAED0">{_cr(fut_oi)}</div>
        </div>
        <div class="sig-row">
          <div class="sig-key">OI Change 1D</div>
          <div class="sig-val" style="color:{_rc(oi_1d)}">{_pct(oi_1d,sign=True)}</div>
        </div>
        <div class="sig-row">
          <div class="sig-key">OI Change 5D</div>
          <div class="sig-val" style="color:{_rc(oi_5d)}">{_pct(oi_5d,sign=True)}</div>
        </div>
        <div style="margin-top:14px">
          <div class="card-title">Governance &amp; News</div>
          <div class="sig-row">
            <div class="sig-key">Governance Risk</div>
            <div class="sig-val" style="color:{gov_color}">{_h(gov_risk)}</div>
          </div>
          {f'<div class="sig-row"><div class="sig-key">Key Decision</div><div class="sig-val" style="font-size:10px;color:#8AAED0;max-width:200px;text-align:right;line-height:1.4">{_h(key_dec[:100])}</div></div>' if key_dec and key_dec not in ('None','nan','') else ''}
          <div class="sig-row">
            <div class="sig-key">News Sentiment</div>
            <div class="sig-val" style="color:{news_color}">{_h(n_sent.replace('_',' '))}</div>
          </div>
          {f'<div class="sig-row"><div class="sig-key">News 7D Count</div><div class="sig-val" style="color:#8AAED0">{int(n_cnt)}</div></div>' if n_cnt is not None else ''}
        </div>
      </div>
    </div>
  </section>

  <!-- ── ANALYST INSIGHTS ──────────────────────────────────────────────────── -->
  {_insights_section(insight_cards) if insight_cards else ''}

  <!-- ── FOOTER ─────────────────────────────────────────────────────────────── -->
  <footer>
    <span>{_h(sym)} &bull; Generated {_h(as_of)} &bull; Capital Flow Intelligence Platform</span>
    <span>All data from NSE via nselib. Not investment advice.</span>
  </footer>

</div>

<script>
const D = {js_data};

// ── Gauge drawing ─────────────────────────────────────────────────────────────
function drawGauge(id, score, color) {{
  const canvas = document.getElementById(id);
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const W = canvas.width, H = canvas.height;
  const cx = W / 2, cy = H * 0.82;
  const r  = Math.min(W * 0.38, cy * 0.78);
  const lw = 12;
  ctx.lineCap = 'round';
  // Track
  ctx.beginPath();
  ctx.arc(cx, cy, r, Math.PI, 0, false);
  ctx.strokeStyle = '#1A2E48'; ctx.lineWidth = lw; ctx.stroke();
  // Fill
  const pct = Math.max(0, Math.min(100, score)) / 100;
  ctx.beginPath();
  ctx.arc(cx, cy, r, Math.PI, Math.PI + Math.PI * pct, false);
  ctx.strokeStyle = color; ctx.lineWidth = lw; ctx.stroke();
  // Score
  ctx.fillStyle = '#E8F0FC';
  ctx.font = 'bold 20px \\'Courier New\\', monospace';
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  ctx.fillText(score.toFixed(0), cx, cy - r * 0.28);
}}

// ── Donut chart ───────────────────────────────────────────────────────────────
function drawDonut(id, segments) {{
  const canvas = document.getElementById(id);
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const W = canvas.width, H = canvas.height;
  const cx = W / 2, cy = H / 2;
  const r  = Math.min(W, H) * 0.42;
  const total = segments.reduce((s, d) => s + d.v, 0);
  if (total <= 0) return;
  let a = -Math.PI / 2;
  for (const seg of segments) {{
    const sweep = (seg.v / total) * 2 * Math.PI;
    ctx.beginPath(); ctx.moveTo(cx, cy);
    ctx.arc(cx, cy, r, a, a + sweep); ctx.closePath();
    ctx.fillStyle = seg.c; ctx.fill();
    a += sweep;
  }}
  // Donut hole
  ctx.beginPath(); ctx.arc(cx, cy, r * 0.52, 0, 2 * Math.PI);
  ctx.fillStyle = '#0D1525'; ctx.fill();
}}

// ── Momentum bars ─────────────────────────────────────────────────────────────
function drawBars() {{
  const range = 60; // +/- 60% max
  [['7',  'bt-7',  'bz-7',  'bf-7',   D.momentum['7d']],
   ['15', 'bt-15', 'bz-15', 'bf-15',  D.momentum['15d']],
   ['30', 'bt-30', 'bz-30', 'bf-30',  D.momentum['30d']],
   ['90', 'bt-90', 'bz-90', 'bf-90',  D.momentum['90d']],
   ['365','bt-365','bz-365','bf-365', D.momentum['365d']]].forEach(([k,tid,zid,fid,val]) => {{
    const track = document.getElementById(tid);
    const zero  = document.getElementById(zid);
    const fill  = document.getElementById(fid);
    if (!track || !zero || !fill) return;
    const zeroPos = (0 + range) / (range * 2) * 100;
    zero.style.left = zeroPos + '%';
    const clamped = Math.max(-range, Math.min(range, val));
    if (clamped >= 0) {{
      fill.style.left   = zeroPos + '%';
      fill.style.width  = (clamped / (range * 2) * 100) + '%';
      fill.style.background = '#00D87C';
    }} else {{
      const w = Math.abs(clamped) / (range * 2) * 100;
      fill.style.left  = (zeroPos - w) + '%';
      fill.style.width = w + '%';
      fill.style.background = '#F04A4A';
    }}
  }});
}}

// ── Run on load ───────────────────────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', () => {{
  const s = D.scores, c = D.label_color;
  function sc(v) {{ return v >= 75 ? '#00D87C' : v >= 60 ? '#3DA0FF' : v >= 40 ? '#F5A024' : '#F04A4A'; }}
  drawGauge('g-bull', s.bull,    sc(s.bull));
  drawGauge('g-ml',   s.ml_bull, sc(s.ml_bull));
  drawGauge('g-acc',  s.accum,   sc(s.accum));
  drawGauge('g-fwd',  s.fwd,     sc(s.fwd));
  const sh = D.shareholding;
  drawDonut('g-shp', [
    {{ v: sh.promoter, c: '#9B6DFF' }},
    {{ v: sh.fii,      c: '#3DA0FF' }},
    {{ v: sh.dii,      c: '#06B6A4' }},
    {{ v: sh.public,   c: '#F5A024' }},
  ]);
  drawBars();
}});
</script>
</body>
</html>'''


# ── HTML sub-builders ─────────────────────────────────────────────────────────

def _pe_color(pe) -> str:
    if pe is None: return '#4D6A90'
    try:
        n = float(pe)
        if n <= 0: return '#F04A4A'
        if n <= 15: return '#00D87C'
        if n <= 30: return '#3DA0FF'
        if n <= 50: return '#F5A024'
        return '#F04A4A'
    except: return '#4D6A90'

def _52w_range_html(close, low, high) -> str:
    if not (close and low and high): return ''
    try:
        c, l, h = float(close), float(low), float(high)
        pct = max(0.0, min(1.0, (c - l) / (h - l))) if h > l else 0.5
        return f'''<div style="position:relative;height:16px;background:#1A2E48;border-radius:8px;overflow:visible;margin-top:4px">
  <div style="position:absolute;height:100%;width:{pct*100:.1f}%;background:linear-gradient(90deg,#1A2E48,#3DA0FF);border-radius:8px"></div>
  <div style="position:absolute;top:-3px;width:10px;height:22px;background:#E8F0FC;border-radius:2px;left:calc({pct*100:.1f}% - 5px)"></div>
  <div style="display:flex;justify-content:space-between;margin-top:4px;font-family:'Courier New',monospace;font-size:10px;color:#4D6A90;position:relative;top:20px">
    <span>&#x20B9;{l:.0f}</span><span>&#x20B9;{h:.0f}</span>
  </div></div><div style="height:16px"></div>'''
    except: return ''

def _shp_legend(name: str, pct, delta, color: str) -> str:
    pct_v = f'{float(pct):.1f}%' if pct is not None else '--'
    delta_html = ''
    if delta is not None:
        n = float(delta)
        dc = '#00D87C' if n > 0 else '#F04A4A' if n < 0 else '#4D6A90'
        delta_html = f'<span style="color:{dc};font-size:10px;font-family:\'Courier New\',monospace">&nbsp;{"+" if n>0 else ""}{n:.2f}%</span>'
    return f'''<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
  <div style="width:10px;height:10px;border-radius:50%;background:{color};flex-shrink:0"></div>
  <div style="font-size:11px;color:#8AAED0;flex:1">{_h(name)}</div>
  <div style="font-family:'Courier New',monospace;font-size:13px;font-weight:700;color:#C8D8EC">{pct_v}{delta_html}</div>
</div>'''

def _dma_row(label: str, dma_price, vs_dma) -> str:
    price_s = f'&#x20B9;{float(dma_price):.0f}' if dma_price else '--'
    vs_s = _pct_signed(vs_dma)
    vs_c = '#00D87C' if vs_dma and float(vs_dma) > 0 else '#F04A4A' if vs_dma and float(vs_dma) < 0 else '#4D6A90'
    sig = 'ABOVE' if vs_dma and float(vs_dma) > 0 else 'BELOW' if vs_dma and float(vs_dma) < 0 else '--'
    sig_c = '#00D87C' if sig == 'ABOVE' else '#F04A4A'
    return f'''<div class="dma-row">
  <div class="dma-label">{_h(label)}</div>
  <div class="dma-val" style="font-family:'Courier New',monospace">{price_s}</div>
  <div class="dma-pct" style="font-family:'Courier New',monospace;color:{vs_c}">{vs_s}</div>
  <div style="font-size:10px;font-family:'Courier New',monospace;color:{sig_c}">{sig}</div>
</div>'''

def _pct_signed(v) -> str:
    if v is None: return '--'
    try:
        n = float(v)
        s = '+' if n >= 0 else ''
        return f'{s}{n:.1f}%'
    except: return '--'

def _vol_disp(v) -> str:
    if v is None: return '--'
    try:
        n = float(v)
        if n >= 1e7: return f'{n/1e7:.1f}Cr'
        if n >= 1e5: return f'{n/1e5:.1f}L'
        if n >= 1e3: return f'{n/1e3:.0f}K'
        return f'{n:.0f}'
    except: return '--'

def _ml_comp(name: str, score: float, desc: str) -> str:
    c = _sc(score)
    pct = min(100, max(0, score))
    return f'''<div class="ml-comp">
  <div class="ml-comp-label">{_h(name)}</div>
  <div class="ml-comp-bar"><div class="ml-comp-fill" style="width:{pct:.0f}%;background:{c}"></div></div>
  <div class="ml-comp-val" style="color:{c}">{score:.0f}</div>
  <div style="font-size:9px;color:#2D4060;margin-top:2px">{_h(desc)}</div>
</div>'''

def _deal_color(sig: str) -> str:
    DEAL_COLORS = {'BUY': '#00D87C', 'ACCUMULATE': '#3DA0FF', 'SELL': '#F04A4A', 'NEUTRAL': '#F5A024'}
    for k, v in DEAL_COLORS.items():
        if k in sig.upper(): return v
    return '#4D6A90'

def _rc_dir(direction: str) -> str:
    UP = {'POSITIVE', 'UPWARD', 'UP', 'BULLISH', 'GROWTH', 'UPGRADE'}
    DOWN = {'NEGATIVE', 'DOWNWARD', 'DOWN', 'BEARISH', 'DECLINE', 'DOWNGRADE'}
    d = direction.upper()
    if any(w in d for w in UP): return '#00D87C'
    if any(w in d for w in DOWN): return '#F04A4A'
    return '#F5A024'

def _qr_section(rows_html: str) -> str:
    if not rows_html: return ''
    return f'''<section>
  <div class="section-title">Quarterly Results</div>
  <div class="card">
    <table class="qr-table">
      <thead><tr>
        <th>Period</th><th>Revenue</th><th>Net Profit</th><th>EPS</th><th>YoY</th>
      </tr></thead>
      <tbody>{rows_html}</tbody>
    </table>
  </div>
</section>'''

def _insights_section(cards_html: str) -> str:
    if not cards_html: return ''
    return f'''<section>
  <div class="section-title">Analyst Insights</div>
  <div class="insights-grid">{cards_html}</div>
</section>'''
