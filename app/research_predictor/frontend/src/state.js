export const EMPTY={egfr:'',tp53:'',kras:'',variants:[]};
export function profileFromForm(form){
  for(const key of ['egfr','tp53','kras'])if(!['yes','no'].includes(form[key]))throw Error('اختر حالة كل جين؛ البيانات المجهولة لا تعني عدم وجود طفرة.');
  if(form.egfr==='yes'&&!form.variants.length)throw Error('حدد نوع طفرة EGFR لإكمال المدخلات.');
  return {egfr_mutated:form.egfr==='yes',tp53_mutated:form.tp53==='yes',kras_mutated:form.kras==='yes',egfr_variants:form.egfr==='yes'?[...form.variants]:[]};
}
export function formFromProfile(p){return {egfr:p.egfr_mutated?'yes':'no',tp53:p.tp53_mutated?'yes':'no',kras:p.kras_mutated?'yes':'no',variants:[...p.egfr_variants]};}
export function revisionAfterEdit(state){return {...state,result:null,source:'manual_research_profile',cellId:null,proxyId:null,provenance:null};}
export const SOURCE_LABELS={manual_research_profile:'مدخلات بحثية يدوية',original_training_cell:'خلية أصلية من التدريب',synthetic_demo:'حالة افتراضية للعرض، ليست من TCGA'};
