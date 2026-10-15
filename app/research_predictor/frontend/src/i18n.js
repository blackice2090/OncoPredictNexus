import catalog from '../../translation_catalog.json' with {type:'json'};
export const messages={ar:Object.fromEntries(catalog.map(([k,ar])=>[k,ar])),en:Object.fromEntries(catalog.map(([k,,en])=>[k,en]))};
export function direction(lang){return lang==='en'?'ltr':'rtl';}
export function translate(lang,key,params={}){let s=messages[lang]?.[key]||messages.ar[key]||key;for(const [name,value] of Object.entries(params))s=s.replaceAll('{'+name+'}',String(value));return s;}
export const featureKeys=['EGFR_mutation_present','TP53_mutation_present','KRAS_mutation_present','L858R','Exon19_deletion','T790M','C797S','Other_EGFR'];
export const featureLabel=(lang,feature)=>translate(lang,'feature'+featureKeys.indexOf(feature));
export const sourceLabel=(lang,source)=>translate(lang,({original_training_cell:'trainingSource',synthetic_demo:'syntheticSource',manual_research_profile:'manual',tcga_demo_proxy:'tcgaSource'})[source]||'manual');
export function profileWarnings(result,lang,info){
  const t=(key,p)=>translate(lang,key,p);const lines=[t('notValidation')];if(result.case_source==='tcga_demo_proxy')lines.push(t('tcgaWarning'));
  lines.push(result.pattern_training_count?t('trainingPattern',{count:result.pattern_training_count,cellWord:result.pattern_training_count===1?'cell':'cells'}):t('unseenPattern'));
  for(const [v,index] of [['L858R',3],['Exon19_deletion',4],['T790M',5]])if(result.profile?.egfr_variants?.includes(v))lines.push(t('rareVariant',{variant:featureLabel(lang,v),count:info.feature_counts[index],cellWord:info.feature_counts[index]===1?'cell':'cells'}));
  return lines;
}
export function initialLanguage(){try{return localStorage.getItem('oncopredict-language')==='en'?'en':'ar';}catch{return 'ar';}}
export function localizeError(error,lang){
  const message=error instanceof Error?error.message:String(error);
  if(/Failed to fetch|Load failed|NetworkError/i.test(message))return translate(lang,'fetchError');
  if(lang==='ar')return message;
  const map={
    'اختر حالة كل جين؛ البيانات المجهولة لا تعني عدم وجود طفرة.':'missingStatus',
    'حدد نوع طفرة EGFR لإكمال المدخلات.':'missingVariant',
    'تعذر قراءة استجابة الخدمة. تحقق من تشغيل البرنامج.':'fetchError'
  };
  if(map[message])return translate(lang,map[message]);
  return /[\u0600-\u06ff]/.test(message)?translate(lang,'requestError'):message;
}
