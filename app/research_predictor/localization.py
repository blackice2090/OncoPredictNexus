"""Presentation-only translations; frozen predictions and stored records are unchanged."""
from pathlib import Path
from html import escape
import copy,json
CATALOG=json.loads((Path(__file__).parent/'translation_catalog.json').read_text(encoding='utf-8'))
MESSAGES={'ar':{k:ar for k,ar,_ in CATALOG},'en':{k:en for k,_,en in CATALOG}}
FEATURES=['EGFR_mutation_present','TP53_mutation_present','KRAS_mutation_present','L858R','Exon19_deletion','T790M','C797S','Other_EGFR']

def text(lang,key,**params):
    result=MESSAGES[lang][key]
    for name,value in params.items():result=result.replace('{'+name+'}',str(value))
    return result

def translated_warnings(r,lang,info):
    lines=[text(lang,'notValidation')]
    if r['case_source']=='tcga_demo_proxy':lines.append(text(lang,'tcgaWarning'))
    lines.append(text(lang,'trainingPattern',count=r['pattern_training_count'],cellWord='cell' if r['pattern_training_count']==1 else 'cells') if r['pattern_training_count'] else text(lang,'unseenPattern'))
    for variant,index in [('L858R',3),('Exon19_deletion',4),('T790M',5)]:
        if variant in r['profile']['egfr_variants']:lines.append(text(lang,'rareVariant',variant=text(lang,'feature'+str(index)),count=info['feature_counts'][index],cellWord='cell' if info['feature_counts'][index]==1 else 'cells'))
    return lines

def localized_result(original,lang,info):
    result=copy.deepcopy(original)
    if lang=='en':
        result['display_language']='en'
        result['warnings']=translated_warnings(result,lang,info)
        result['limitations']=[text(lang,'limit'+str(i)) for i in range(5)]
        for drug in result['drugs']:
            for feature in drug['shap_values']:feature['label']=text(lang,'feature'+str(FEATURES.index(feature['feature'])))
    return result

def render_report(original,lang,info):
    r=localized_result(original,lang,info);t=lambda key,**params:escape(text(lang,key,**params));safe=lambda value:escape(str(value))
    direction='rtl' if lang=='ar' else 'ltr'
    source_key={'manual_research_profile':'manual','original_training_cell':'trainingSource','synthetic_demo':'syntheticSource','tcga_demo_proxy':'tcgaSource'}[r['case_source']]
    rows=''.join(f"<tr><td><bdi>{safe(d['drug'])}</bdi></td><td>{d['rank']}</td><td><bdi>{d['predicted_LN_IC50']:.6f}</bdi></td><td><bdi>{d['predicted_IC50_uM']:.6f}</bdi></td><td>{t('unavailable')}</td></tr>" for d in sorted(r['drugs'],key=lambda d:d['rank']))
    profile_rows=''.join(f"<tr><td>{gene}</td><td>{t('mutated') if r['profile'][key] else t('notMutated')}</td></tr>" for gene,key in [('EGFR','egfr_mutated'),('TP53','tp53_mutated'),('KRAS','kras_mutated')])
    variant_key={'L858R':'feature3','Exon19_deletion':'feature4','T790M':'feature5','Other_EGFR':'feature7'}
    variants=(', ' if lang=='en' else '، ').join(t(variant_key[v]) for v in r['profile']['egfr_variants']) or t('noVariant')
    explanations=''
    for drug in r['drugs']:
        explanations+=f"<section><h3><bdi>{safe(drug['drug'])}</bdi></h3><p>{t('baseValue')}: <bdi>{drug['shap_base_value']:.6f}</bdi></p><table><tr><th>{t('feature')}</th><th>{t('input')}</th><th>{t('contribution')}</th></tr>"
        for f in drug['shap_values']:explanations+=f"<tr><td>{safe(f['label'])}</td><td>{f['input']}</td><td><bdi>{f['value']:+.6f}</bdi></td></tr>"
        explanations+='</table></section>'
    provenance=''
    if r.get('provenance'):
        c=r['provenance']
        call_rows=''.join(f"<tr><td>{safe(x['Hugo_Symbol'])}</td><td><bdi>{safe(x['HGVSp_Short'])}</bdi></td><td>{safe(x['Variant_Classification'])}</td><td>{safe(x['t_ref_count'])} / {safe(x['t_alt_count'])}</td></tr>" for x in c['calls'])
        provenance=f"<h2>{t('tcgaTitle')}</h2><p><bdi>{safe(c['id'])}</bdi> · {safe(c['study_name'])}<br>{t('dataRevision')}: <code>{safe(c['commit'])}</code><br>WXS · {safe(c['retrieved_at_utc'])}</p><table><tr><th>{t('gene')}</th><th>{t('proteinCall')}</th><th>{t('callClassification')}</th><th>{t('readCounts')}</th></tr>{call_rows}</table><p>{t('tcgaWarning')}</p><a href='{safe(c['source_url'])}'>{t('tcgaReadSource')}</a>"
    notes=''.join('<li>'+safe(line)+'</li>' for line in r['warnings']+r['limitations'])
    return f'''<!doctype html><html lang="{lang}" dir="{direction}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>OncoPredict — {t('reportTitle')}</title><link rel="stylesheet" href="/fonts/fonts.css"><style>body{{font:15px/1.8 'Manrope','IBM Plex Sans Arabic',Tahoma,sans-serif;color:#202124;max-width:1000px;margin:30px auto;padding:20px}}html[lang=ar] body{{font-family:'IBM Plex Sans Arabic','Manrope',Tahoma,sans-serif}}header{{padding:25px;background:#eeeaff;border-radius:14px}}h1{{font-size:30px}}h2{{margin-top:32px}}table{{width:100%;border-collapse:collapse;table-layout:fixed;margin:18px 0 25px}}th,td{{text-align:start;border-bottom:1px solid #dce0e7;padding:9px;overflow-wrap:anywhere}}th{{background:#f2efff}}code{{overflow-wrap:anywhere}}button{{background:#a1edce;border:0;border-radius:30px;padding:12px 20px;font:inherit;cursor:pointer}}section{{break-inside:avoid}}@media print{{button{{display:none}}body{{margin:0;padding:0}}}}@media(max-width:600px){{body{{padding:12px}}th,td{{font-size:11px;padding:6px}}}}</style></head><body><button onclick="window.print()">{t('print')}</button><header><p>OncoPredict Nexus</p><h1>{t('reportTitle')}</h1><p>{t('heroFoot')}</p></header><p>{t('runId')}: <code>{safe(r['run_id'])}</code><br>{t('savedTime')}: <bdi>{safe(r['created_at_utc'])}</bdi><br>{t('version')}: <bdi>{safe(r['model_version'])}</bdi><br>{t('source')}: {t(source_key)}<br>{t('cell')}: {safe(r['cell_id']) if r['cell_id'] else t('noCell')}</p>{provenance}<h2>{t('profile')}</h2><table><tr><th>{t('gene')}</th><th>{t('status')}</th></tr>{profile_rows}<tr><td>{t('egfrType')}</td><td>{variants}</td></tr></table><h2>{t('results')}</h2><p>{t('rankNote')}</p><table><tr><th>{t('drug')}</th><th>{t('rank')}</th><th>LN_IC50</th><th>IC50 µM</th><th>{t('sensitivity')}</th></tr>{rows}</table><p>{t('thresholdNote')}</p><h2>{t('localTitle')}</h2><p>{t('localText')}</p>{explanations}<h2>{t('limitations')}</h2><ul>{notes}</ul><p>{t('modelHash')}: <code>{safe(r['model_sha256'])}</code><br>{t('predictionRole')}</p></body></html>'''
