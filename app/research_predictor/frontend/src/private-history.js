/** Browser-private research records. Never synchronizes visitor history to a server. */
import {translate,featureLabel,profileWarnings,sourceLabel,direction} from './i18n.js';

const KEY='oncopredict-private-experiments-v1';
const valid=r=>r&&/^[a-f0-9]{32}$/.test(r.run_id)&&typeof r.created_at_utc==='string'&&r.profile&&Array.isArray(r.drugs)&&r.drugs.every(d=>Number.isFinite(d.predicted_LN_IC50)&&Number.isFinite(d.predicted_IC50_uM));
export function createHistory(storage){
 const list=()=>{try{const data=JSON.parse(storage.getItem(KEY)||'[]');return Array.isArray(data)?data.filter(valid):[];}catch{return [];}};
 return {list,save(record){if(!valid(record))throw Error('Cannot save an invalid experiment.');try{storage.setItem(KEY,JSON.stringify([record,...list().filter(r=>r.run_id!==record.run_id)].slice(0,30)));}catch{throw Error('Unable to save this experiment in browser storage. Enable local storage or free space and try again.');}return record;},get(id){const r=list().find(r=>r.run_id===id);if(!r)throw Error('Experiment not found in this browser.');return r;},clear(){storage.removeItem(KEY);}};
}

function localized(record,lang,info){
 const r=JSON.parse(JSON.stringify(record));r.display_language=lang;r.warnings=profileWarnings(r,lang,info);r.limitations=Array.from({length:5},(_,i)=>translate(lang,'limit'+i));
 for(const d of r.drugs)for(const f of d.shap_values)f.label=featureLabel(lang,f.feature);
 return r;
}
export const exportJSON=(r,lang,info)=>JSON.stringify(localized(r,lang,info),null,2);
const csvCell=v=>{let s=typeof v==='object'?JSON.stringify(v):String(v??'');if(typeof v==='string'&&/^[=+\-@\t\r]/.test(s))s="'"+s;return '"'+s.replaceAll('"','""')+'"';};
export function exportCSV(record,lang,info){
 const r=localized(record,lang,info),headers=['run_id','created_at_utc','case_source','cell_id','proxy_id','model_version','model_sha256','drug','rank','predicted_LN_IC50','predicted_IC50_uM','sensitivity_status','prediction_role','threshold_policy','shap_method','genomic_input_json','warnings_json','provenance_json'];
 return '\uFEFF'+[headers,...r.drugs.map(d=>headers.map(k=>k==='genomic_input_json'?r.profile:k==='warnings_json'?r.warnings:k==='provenance_json'?r.provenance??null:d[k]??r[k]??null))].map(row=>row.map(csvCell).join(',')).join('\r\n');
}
const safe=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export function reportHTML(record,lang,info){
 const r=localized(record,lang,info),t=k=>safe(translate(lang,k)),num=v=>Number(v).toFixed(6);
 const table=(heads,rows)=>'<table><thead><tr>'+heads.map(h=>'<th>'+safe(h)+'</th>').join('')+'</tr></thead><tbody>'+rows.map(row=>'<tr>'+row.map(v=>'<td><bdi>'+safe(v)+'</bdi></td>').join('')+'</tr>').join('')+'</tbody></table>';
 const output=table([translate(lang,'drug'),translate(lang,'rank'),'LN_IC50','IC50 µM',translate(lang,'sensitivity')],[...r.drugs].sort((a,b)=>a.rank-b.rank).map(d=>[d.drug,d.rank,num(d.predicted_LN_IC50),num(d.predicted_IC50_uM),translate(lang,'unavailable')]));
 const inputs=table([translate(lang,'gene'),translate(lang,'input')],[['EGFR',r.profile.egfr_mutated],['TP53',r.profile.tp53_mutated],['KRAS',r.profile.kras_mutated],['EGFR variants',r.profile.egfr_variants.join(', ')||translate(lang,'noVariant')]]);
 const explanations=r.drugs.map(d=>'<section><h3>'+safe(d.drug)+'</h3><p>'+t('baseValue')+': <bdi>'+num(d.shap_base_value)+'</bdi></p>'+table([translate(lang,'feature'),translate(lang,'input'),translate(lang,'contribution')],d.shap_values.map(f=>[f.label,f.input,num(f.value)]))+'</section>').join('');
 const provenance=r.provenance?'<h2>TCGA provenance</h2><pre>'+safe(JSON.stringify(r.provenance,null,2))+'</pre>':'';
 return '<!doctype html><html lang="'+safe(lang)+'" dir="'+direction(lang)+'"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>OncoPredict Nexus — '+t('reportTitle')+'</title><style>body{font:16px Arial,sans-serif;line-height:1.55;color:#22232b;max-width:1000px;margin:36px auto;padding:0 24px}h1,h2{color:#6754dd}table{width:100%;border-collapse:collapse;margin:20px 0}th,td{padding:10px;border:1px solid #ded9ed;text-align:start}th{background:#eeebfc}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f7f5fc;padding:16px}section{break-inside:avoid}footer{border-top:1px solid #ddd;margin-top:32px}@media print{body{margin:0}a{color:inherit}}</style></head><body><h1>OncoPredict Nexus</h1><h2>'+t('reportTitle')+'</h2><p>'+t('researchBanner')+'</p><p>'+t('source')+': '+safe(sourceLabel(lang,r.case_source))+'</p><h2>'+t('genomicInputs')+'</h2>'+inputs+'<h2>'+t('results')+'</h2>'+output+'<p>'+t('rankNote')+'</p><p>'+t('thresholdNote')+'</p><ul>'+r.warnings.map(w=>'<li>'+safe(w)+'</li>').join('')+'</ul><h2>'+t('localTitle')+'</h2><p>'+t('localText')+'</p>'+explanations+provenance+'<h2>'+t('fingerprints')+'</h2><pre>'+safe(JSON.stringify({run_id:r.run_id,created_at_utc:r.created_at_utc,model_version:r.model_version,model_sha256:r.model_sha256,source_sha256:r.model_metadata?.source_sha256??info.source_sha256},null,2))+'</pre><footer>'+t('heroFoot')+'</footer></body></html>';
}
