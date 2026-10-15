"""Frozen Ridge inference and exact interventional linear SHAP in LN_IC50."""
from pathlib import Path
import hashlib,json,math
import joblib,numpy as np,pandas as pd

FEATURES=['EGFR_mutation_present','TP53_mutation_present','KRAS_mutation_present','L858R','Exon19_deletion','T790M','C797S','Other_EGFR']
DRUGS=['Osimertinib','Erlotinib','Gefitinib']
VARIANTS=['L858R','Exon19_deletion','T790M','Other_EGFR']
FEATURE_LABELS=['وجود طفرة EGFR','وجود طفرة TP53','وجود طفرة KRAS','L858R','حذف Exon 19','T790M','C797S','طفرات EGFR أخرى']
LIMITATIONS=['النموذج استكشافي، والنتائج ليست توصية علاج لمريض.','218 من 249 قيمة IC50 منشورة فوق أعلى جرعة مختبرة.','التفسير يشرح حساب النموذج، ولا يثبت تأثيرًا سببيًا للطفرات.','المساهمات على LN_IC50 وتفترض تفسيرًا تدخليًا؛ ترابط رايات EGFR يحدّ من تفسير كل راية وحدها.','لا تتوفر عتبات حساسية ومقاومة معتمدة لهذه النسخة، ولا درجة ثقة فردية.']

def profile_vector(profile):
    keys={'egfr_mutated','egfr_variants','tp53_mutated','kras_mutated'}
    if not isinstance(profile,dict) or set(profile)!=keys:raise ValueError('أدخل الحقول الجينية الأربعة كاملة، دون حقول إضافية.')
    if any(type(profile[k]) is not bool for k in ['egfr_mutated','tp53_mutated','kras_mutated']):raise ValueError('اختر وجود أو عدم وجود الطفرة لكل جين؛ المعلومة المجهولة ليست صفرًا.')
    variants=profile['egfr_variants']
    if not isinstance(variants,list) or any(not isinstance(v,str) for v in variants) or len(set(variants))!=len(variants):raise ValueError('قائمة أنواع EGFR غير صالحة أو مكررة.')
    if any(v not in VARIANTS for v in variants):raise ValueError('نوع الطفرة غير مدعوم؛ C797S لم تظهر في التدريب ولا يمكن توقعها بهذه النسخة.')
    if not profile['egfr_mutated'] and variants:raise ValueError('لا يمكن اختيار نوع طفرة EGFR مع عدم وجود طفرة EGFR.')
    if profile['egfr_mutated'] and not variants:raise ValueError('حدد نوع طفرة EGFR؛ لا نحول النوع المجهول إلى طفرة أخرى.')
    if 'Other_EGFR' in variants and len(variants)>1:raise ValueError('هذه النسخة تفصل طفرات EGFR الأخرى عن الأنواع المحددة؛ لا يدعم مخطط التدريب هذا الجمع.')
    return np.array([profile['egfr_mutated'],profile['tp53_mutated'],profile['kras_mutated'],'L858R' in variants,'Exon19_deletion' in variants,'T790M' in variants,0,'Other_EGFR' in variants],dtype=float)

def vector_profile(x):
    return {'egfr_mutated':bool(x[0]),'tp53_mutated':bool(x[1]),'kras_mutated':bool(x[2]),'egfr_variants':[v for v,i in [('L858R',3),('Exon19_deletion',4),('T790M',5),('Other_EGFR',7)] if x[i]]}

def rank_predictions(values):
    return [int(1+sum(v<value and not math.isclose(v,value,rel_tol=0,abs_tol=1e-10) for v in values)) for value in values]

class PredictionEngine:
    def __init__(self,root):
        self.root=Path(root);self.assets=self.root/'app/research_predictor/assets'
        try:
            self.manifest=json.loads((self.assets/'manifest.json').read_text())
            self.verify_sources()
        except (OSError,KeyError,json.JSONDecodeError) as exc:raise ValueError('مصادر النموذج غير متاحة أو غير موثقة.') from exc
        artifact=joblib.load(self.assets/'exploratory_model.joblib') # Only frozen own artifact, verified before deserialization.
        if artifact['features']!=FEATURES or artifact['drugs']!=DRUGS or artifact['target']!='LN_IC50':raise ValueError('مخطط النموذج لا يطابق النسخة البحثية.')
        self.model=artifact['model'];self.artifact=artifact
        self.cells=pd.read_csv(self.assets/'cell_features_83.csv')
        self.x=self.cells[FEATURES].to_numpy(dtype=float)
        if self.x.shape!=(83,8) or not np.isfinite(self.x).all() or not np.isin(self.x,[0,1]).all():raise ValueError('ميزات التدريب غير مكتملة.')
        self.mean=self.x.mean(axis=0);self.counts=self.x.sum(axis=0).astype(int)
        if list(self.model.named_steps)!=['variance','model']:raise ValueError('SHAP الخطي لهذه النسخة يتطلب خط المعالجة الأصلي.')
        ridge=self.model.named_steps['model'];mask=self.model.named_steps['variance'].get_support()
        self.coef=np.zeros((3,8));self.coef[:,mask]=ridge.coef_
        self.base=self.model.predict(self.mean.reshape(1,-1))[0]
        self.version='ridge-ic50-20261002-'+self.manifest['exploratory_model.joblib']['sha256'][:12]
        self.study=json.loads((self.assets/'run_summary.json').read_text())
        self.model_info={'model_version':self.version,'family':'Ridge','alpha':float(ridge.alpha),'status':'exploratory_not_clinically_validated','target':'LN_IC50','unit':'µM after exp(LN_IC50)','n_training_cells':83,'n_targets':249,'features':FEATURES,'feature_labels':FEATURE_LABELS,'feature_counts':self.counts.tolist(),'drugs':DRUGS,'sensitivity_status':None,'threshold_policy':'deferred_no_validated_thresholds','shap_method':'exact_interventional_linear_SHAP','shap_background':'83 original training cells; descriptive full-refit explanations','limitations':LIMITATIONS,'metrics':self.study['metrics'],'validation':self.study['validation'],'source_sha256':{k:v['sha256'] for k,v in self.manifest.items()}}

        if 'xgboost_comparison.json' in self.manifest:
            comparison=json.loads((self.assets/'xgboost_comparison.json').read_text(encoding='utf-8'))
            if comparison['status']!='bounded_xgboost_comparison_completed' or comparison['independent_validation'] or comparison['model_replaced_in_platform']:raise ValueError('سجل المقارنة لا يطابق نطاق النموذج المجمد.')
            self.model_info['xgboost_comparison']=comparison

    def verify_sources(self):
        for name,entry in self.manifest.items():
            if Path(name).name!=name:raise ValueError('اسم مصدر غير صالح.')
            p=self.assets/name
            if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=entry['sha256']:raise ValueError('تغير مصدر محفوظ؛ التنبؤ متوقف لحين مراجعة المصدر.')

    def predict(self,profile):
        self.verify_sources()
        result=self.predict_vector(profile_vector(profile));result['profile']=profile
        return result

    @property
    def tcga_demo(self):
        self.verify_sources()
        case=json.loads((self.assets/'tcga_demo_proxy.json').read_text(encoding='utf-8'))
        if case['independent_model_validation'] or case['drug_response_available'] or case['role']!='public_reported_mutation_demo_only':raise ValueError('مصدر حالة العرض لا يطابق النطاق المحدد.')
        return case

    def predict_vector(self,x):
        x=np.asarray(x,dtype=float)
        if x.shape!=(8,) or not np.isfinite(x).all() or not np.isin(x,[0,1]).all() or x[6]!=0:raise ValueError('ملف جيني غير صالح أو غير مدعوم.')
        predicted=self.model.predict(x.reshape(1,-1))[0]
        shap=self.coef*(x-self.mean)[None,:]
        if not np.allclose(self.base+shap.sum(axis=1),predicted,atol=1e-10,rtol=0):raise ValueError('فشل تحقق جمع مساهمات التفسير.')
        ranks=rank_predictions(predicted);matches=np.all(self.x==x,axis=1);n_matches=int(matches.sum())
        codes=['not_independent_validation'];warnings=['هذه تجربة للنموذج المحفوظ وليست اختبارًا مستقلًا جديدًا.']
        if n_matches:warnings.append(f'هذا النمط الجيني ظهر في {n_matches} خلية تدريب؛ تطابق النمط لا يعني تطابق الاستجابة.');codes.append('training_pattern')
        else:warnings.append('هذا النمط الجيني لم يظهر في بيانات التدريب؛ التوقع استقراء بحثي غير متحقق.');codes.append('unseen_pattern')
        for i in [3,4,5]:
            if x[i]:warnings.append(f'الميزة {FEATURE_LABELS[i]} ظهرت في {self.counts[i]} خلية فقط؛ لا تكفي لإثبات أداء مستقل لهذا النوع.');codes.append('rare_variant')
        drugs=[{'drug':d,'rank':ranks[j],'predicted_LN_IC50':float(predicted[j]),'predicted_IC50_uM':float(np.exp(predicted[j])),'sensitivity_status':None,'shap_base_value':float(self.base[j]),'shap_unit':'LN_IC50','shap_values':[{'feature':f,'label':FEATURE_LABELS[i],'input':int(x[i]),'value':float(shap[j,i]),'supported':i!=6} for i,f in enumerate(FEATURES)]} for j,d in enumerate(DRUGS)]
        return {'model_version':self.version,'prediction_role':'new_input_full_refit_inference_not_validation','drugs':drugs,'pattern_training_count':n_matches,'warnings':warnings,'warnings_codes':codes,'limitations':LIMITATIONS,'ranking_definition':'ascending predicted IC50 within this assay; not clinical treatment preference','threshold_policy':'deferred_no_validated_thresholds','shap_method':'exact_interventional_linear_SHAP'}

    def global_explanation(self):
        values=(self.x-self.mean)[None,:,:]*self.coef[:,None,:]
        return {'method':'exact_interventional_linear_SHAP','scope':'descriptive full-refit model, all 83 training cells; not validation','unit':'LN_IC50','drugs':[{'drug':d,'features':[{'feature':f,'label':FEATURE_LABELS[i],'mean_abs_shap':float(np.abs(values[j,:,i]).mean()),'count':int(self.counts[i])} for i,f in enumerate(FEATURES)]} for j,d in enumerate(DRUGS)]}

    def list_cells(self):
        return [{'id':r.SangerModelID,'name':r.CellLineName,'role':'original_training_cell_not_external_validation','profile':vector_profile(r[FEATURES].to_numpy(dtype=float))} for _,r in self.cells.iterrows()]
