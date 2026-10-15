import test from 'node:test';
import assert from 'node:assert/strict';
const feature=await import('./private-history.js').catch(()=>null);
function module(){assert.ok(feature,'Browser-private history module is not implemented');return feature;}
const memory=()=>{const values=new Map();return {getItem:k=>values.get(k)??null,setItem:(k,v)=>values.set(k,String(v)),removeItem:k=>values.delete(k)};};
const record={run_id:'a'.repeat(32),created_at_utc:'2026-10-15T00:00:00+00:00',case_source:'synthetic_demo',cell_id:null,model_version:'frozen-test',model_sha256:'b'.repeat(64),profile:{egfr_mutated:true,egfr_variants:['L858R'],tp53_mutated:false,kras_mutated:false},pattern_training_count:0,drugs:[{drug:'Osimertinib',rank:1,predicted_LN_IC50:-1.25,predicted_IC50_uM:0.2865047968601901,shap_base_value:0,shap_values:[{feature:'L858R',label:'L858R',value:-1.25,input:1}],sensitivity_status:null}]};
const info={feature_counts:[13,71,30,2,3,1,0,8]};

test('saving in one browser store is invisible to another and survives reopening',()=>{
 const {createHistory}=module(),a=memory(),b=memory();createHistory(a).save(record);
 assert.equal(createHistory(a).get(record.run_id).drugs[0].predicted_LN_IC50,-1.25);
 assert.equal(createHistory(b).list().length,0);
 assert.throws(()=>createHistory(b).get(record.run_id),/not found/i);
});
test('unavailable storage prevents a misleading saved result',()=>{
 const {createHistory}=module();assert.throws(()=>createHistory({getItem:()=>null,setItem:()=>{throw Error('quota');}}).save(record),/save|storage/i);
});
test('corrupt browser content never becomes a visible experiment',()=>{
 const {createHistory}=module();assert.deepEqual(createHistory({getItem:()=>'{bad',setItem(){}}).list(),[]);
});
test('CSV and report preserve numerical values and escape unsafe text',()=>{
 const {exportJSON,exportCSV,reportHTML}=module(),original=JSON.stringify(record);
 const parsed=JSON.parse(exportJSON(record,'en',info));assert.equal(parsed.drugs[0].predicted_LN_IC50,-1.25);
 assert.match(exportCSV(record,'en',info),/-1.25/);
 const html=reportHTML({...record,model_version:'<script>alert(1)</script>'},'en',info);
 assert.ok(!html.includes('<script>'));assert.match(html,/&lt;script&gt;/);assert.match(html,/-1.250000/);assert.match(html,/not an independent/i);
 assert.equal(JSON.stringify(record),original);
});
