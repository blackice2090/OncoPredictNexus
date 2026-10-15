"""Predeclared, bounded nested XGBoost comparison; no deployment or refit."""
from pathlib import Path
import sys,json,hashlib,time,uuid,platform
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'runtime'))
import numpy as np,pandas as pd,matplotlib.pyplot as plt,sklearn,xgboost
from scipy.stats import spearmanr
from sklearn.pipeline import Pipeline
from sklearn.feature_selection import VarianceThreshold
from sklearn.linear_model import Ridge
from sklearn.dummy import DummyRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.model_selection import KFold,GridSearchCV
from sklearn.metrics import mean_squared_error,mean_absolute_error,r2_score,confusion_matrix
from xgboost import XGBRegressor
from notebook_checks import bootstrap_gain,ranking_labels,audit_cells
FEATURES=['EGFR_mutation_present','TP53_mutation_present','KRAS_mutation_present','L858R','Exon19_deletion','T790M','C797S','Other_EGFR']
DRUGS=['Osimertinib','Erlotinib','Gefitinib'];SEEDS=[42,137,2026]

def partition_indices(assignment,fold):
    if set(assignment)!={1,2,3,4,5} or fold not in range(1,6):raise ValueError('Frozen assignment must contain exactly five folds')
    return np.flatnonzero(assignment!=fold),np.flatnonzero(assignment==fold)

def searches(inner,seed):
    defs={'baseline':(DummyRegressor(),{}),'ridge':(Ridge(),{'model__alpha':[.1,1.,10.,100.]}),
      'xgboost':(MultiOutputRegressor(XGBRegressor(objective='reg:squarederror',tree_method='hist',device='cpu',n_jobs=1,random_state=seed,learning_rate=.05,min_child_weight=5,subsample=1.,colsample_bytree=1.),n_jobs=1),{'model__estimator__n_estimators':[100,250],'model__estimator__max_depth':[1,2],'model__estimator__reg_lambda':[10.,100.]})}
    return {name:GridSearchCV(Pipeline([('variance',VarianceThreshold()),('model',model)]),grid,cv=inner,scoring='neg_mean_squared_error',n_jobs=1,error_score='raise') for name,(model,grid) in defs.items()}

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def run():
    root=HERE.parents[1];source=HERE/'data'
    expected=json.loads((HERE/'data_manifest.json').read_text())['sha256']
    assert all(sha(source/name)==digest for name,digest in expected.items())
    catalog_path=root/'outputs/research_explorer/source_manifest.json'
    protected=json.loads(catalog_path.read_text(encoding='utf-8')) if catalog_path.exists() else []
    assert all(sha(root/e['path'])==e['sha256'] for e in protected)
    cells=pd.read_csv(source/'cell_features_83.csv').sort_values('SangerModelID').reset_index(drop=True)
    ids=cells.SangerModelID.to_numpy();x=cells[FEATURES].to_numpy(dtype=float)
    y=pd.read_csv(source/'targets_wide_83.csv').set_index('SangerModelID').loc[ids,DRUGS].to_numpy()
    audit_cells(ids,x,y);folds=pd.read_csv(source/'fold_assignments.csv')
    run_id='xgb_'+time.strftime('%Y%m%dT%H%M%S',time.gmtime())+'_'+uuid.uuid4().hex[:6]
    out=HERE/'runs'/run_id;out.mkdir(parents=True);(out/'figures').mkdir()
    def save(name,value):(out/name).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    config={'target':'LN_IC50','features':FEATURES,'drugs':DRUGS,'seeds':SEEDS,'n_cells':83,'n_targets':249,'inner_folds':4,'outer_folds':5,'protocol_sha256':sha(HERE/'PROTOCOL_AR.md'),'code_sha256':sha(HERE/'compare.py'),'versions':{'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,'sklearn':sklearn.__version__,'xgboost':xgboost.__version__},'xgb_grid':searches(4,43)['xgboost'].param_grid,'status':'development_internal_not_independent','early_stopping':False}
    save('config.json',config);save('source_manifest.json',expected)
    predictions={name:np.full((3,83,3),np.nan) for name in ['baseline','ridge','xgboost','nested_selected']}
    grid_rows=[];selection_rows=[];partitions=[];started=time.perf_counter()
    for repeat,seed in enumerate(SEEDS,1):
        assignment=folds[folds['repeat']==repeat].set_index('SangerModelID').loc[ids]
        assert assignment.seed.eq(seed).all()
        for fold in range(1,6):
            train,test=partition_indices(assignment.outer_fold.to_numpy(),fold)
            inner=list(KFold(4,shuffle=True,random_state=seed+fold).split(x[train]))
            assert not set(ids[train])&set(ids[test])
            for a,b in inner:assert not set(ids[train[a]])&set(ids[train[b]])
            fits=searches(inner,seed+fold)
            for name,search in fits.items():
                search.fit(x[train],y[train]);predictions[name][repeat-1,test]=search.predict(x[test])
                selection_rows.append({'repeat':repeat,'fold':fold,'candidate':name,'inner_MSE':-float(search.best_score_),'params':json.dumps(search.best_params_)})
                for params,score in zip(search.cv_results_['params'],search.cv_results_['mean_test_score']):grid_rows.append({'repeat':repeat,'fold':fold,'candidate':name,'params':json.dumps(params),'inner_MSE':-float(score)})
            chosen=max(fits,key=lambda name:fits[name].best_score_)
            predictions['nested_selected'][repeat-1,test]=fits[chosen].predict(x[test])
            selection_rows.append({'repeat':repeat,'fold':fold,'candidate':'nested_selected','selected_family':chosen,'inner_MSE':-float(fits[chosen].best_score_),'params':json.dumps(fits[chosen].best_params_)})
            partitions.append({'repeat':repeat,'fold':fold,'training':ids[train].tolist(),'held_out':ids[test].tolist(),'inner':[{'training':ids[train[a]].tolist(),'validation':ids[train[b]].tolist()} for a,b in inner]})
            pd.DataFrame(selection_rows).to_csv(out/'selections.csv',index=False)
            print(f'Repeat {repeat}/3 fold {fold}/5: inner-selected {chosen}',flush=True)
    assert all(np.isfinite(p).all() for p in predictions.values())
    old=pd.read_csv(source/'held_out_predictions.csv');old_ridge=np.stack([old[(old.model=='ridge')&(old['repeat']==k)].pivot(index='SangerModelID',columns='drug',values='predicted_LN_IC50').loc[ids,DRUGS].to_numpy() for k in range(1,4)])
    reproduction=float(np.max(np.abs(predictions['ridge']-old_ridge)));assert reproduction<1e-9
    metrics=[];per_drug=[];prediction_rows=[]
    truth=ranking_labels(y)
    for name,p in predictions.items():
        top1=[float((ranking_labels(q)[truth!=3]==truth[truth!=3]).mean()) for q in p]
        metrics.append({'candidate':name,'RMSE':float(np.sqrt(((p-y[None])**2).mean())),'MAE':float(np.abs(p-y[None]).mean()),'mean_top1_no_tie':float(np.mean(top1))})
        for j,drug in enumerate(DRUGS):
            rho=[spearmanr(y[:,j],p[k,:,j]).statistic for k in range(3)]
            per_drug.append({'candidate':name,'drug':drug,'RMSE':float(np.sqrt(((p[:,:,j]-y[None,:,j])**2).mean())),'MAE':float(np.abs(p[:,:,j]-y[None,:,j]).mean()),'mean_R2':float(np.mean([r2_score(y[:,j],p[k,:,j]) for k in range(3)])),'mean_Spearman':float(np.mean(rho)) if np.isfinite(rho).all() else None})
        for k in range(3):
            for i in range(83):
                for j,drug in enumerate(DRUGS):prediction_rows.append({'repeat':k+1,'SangerModelID':ids[i],'candidate':name,'drug':drug,'observed_LN_IC50':float(y[i,j]),'predicted_LN_IC50':float(p[k,i,j]),'prediction_role':'held_out_internal_development_not_external_validation'})
    metric=pd.DataFrame(metrics).set_index('candidate')
    comparison=bootstrap_gain(y,predictions['ridge'],predictions['xgboost'])
    comparison['MAE_not_increased']=bool(metric.loc['xgboost','MAE']<=metric.loc['ridge','MAE'])
    comparison['development_signal']=bool(comparison['relative_gain']>=.05 and comparison['conditional_95_interval'][0]>0 and comparison['MAE_not_increased'])
    pd.DataFrame(grid_rows).to_csv(out/'inner_grid_scores.csv',index=False);pd.DataFrame(selection_rows).to_csv(out/'selections.csv',index=False)
    metric.to_csv(out/'metrics.csv');pd.DataFrame(per_drug).to_csv(out/'per_drug_metrics.csv',index=False);pd.DataFrame(prediction_rows).to_csv(out/'held_out_predictions.csv',index=False)
    save('partition_audit.json',partitions);save('comparison_vs_ridge.json',comparison)
    np.savez_compressed(out/'oof_predictions.npz',**predictions)
    plt.rcParams.update({'font.family':'DejaVu Sans','axes.spines.top':False,'axes.spines.right':False})
    def figure(fig,name):
        fig.tight_layout();fig.savefig(out/'figures'/f'{name}.png',dpi=180,bbox_inches='tight');fig.savefig(out/'figures'/f'{name}.svg',bbox_inches='tight');plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(11,4))
    labels=metric.index.tolist();colors=['#bec4d2','#7363eb','#55a58d','#9a82c8']
    for ax,key in zip(axes,['RMSE','MAE']):
        ax.barh(labels,metric[key],color=colors);ax.invert_yaxis();ax.set_xlabel(key+' on LN_IC50 (lower is better)')
        for i,value in enumerate(metric[key]):ax.text(value+.025,i,f'{value:.3f}',va='center')
        ax.set_xlim(0,max(metric[key])*1.2)
    figure(fig,'01_model_comparison')
    fig,axes=plt.subplots(1,3,figsize=(12,3.8));pdg=pd.DataFrame(per_drug)
    for j,drug in enumerate(DRUGS):
        q=pdg[(pdg.drug==drug)&(pdg.candidate!='nested_selected')];axes[j].bar(q.candidate,q.RMSE,color=colors[:3]);axes[j].set_title(drug);axes[j].set_ylabel('Held-out RMSE on LN_IC50')
    figure(fig,'02_per_drug_errors')
    matrices=[confusion_matrix(truth,ranking_labels(p),labels=[0,1,2,3]) for p in predictions['xgboost']]
    save('xgb_ranking_confusion_matrices.json',{'classes':DRUGS+['Tie'],'matrices':[m.tolist() for m in matrices],'n_cells_each':83,'not_sensitive_resistant':True})
    fig,axes=plt.subplots(1,3,figsize=(12,4))
    for k,(ax,m) in enumerate(zip(axes,matrices)):
        assert m.sum()==83;ax.imshow(m,cmap='Purples');ax.set_title(f'XGBoost repeat {k+1}: 83 cells');ax.set_xticks(range(4),DRUGS+['Tie'],rotation=45,ha='right');ax.set_yticks(range(4),DRUGS+['Tie']);ax.set_xlabel('Predicted lowest IC50 drug');ax.set_ylabel('Published lowest IC50 drug')
        for i in range(4):
            for j in range(4):ax.text(j,i,str(m[i,j]),ha='center',va='center',color='white' if m[i,j]>m.max()/2 else 'black')
    figure(fig,'03_ranking_confusion_matrices')
    assert all(sha(source/name)==digest for name,digest in expected.items())
    assert all(sha(root/e['path'])==e['sha256'] for e in protected)
    decision='ظهرت إشارة تطوير داخلية وفق القاعدة المسبقة؛ لا اعتماد أو استبدال تلقائي.' if comparison['development_signal'] else 'لم تتحقق إشارة تطوير XGBoost المحددة؛ يبقى Ridge نسخة المنصة، ونحفظ المقارنة كاملة.'
    summary={'status':'bounded_xgboost_comparison_completed','run_id':run_id,'runtime_seconds':time.perf_counter()-started,'versions':config['versions'],'ridge_reproduction_max_abs':reproduction,'metrics':metrics,'comparison':comparison,'decision_ar':decision,'original_assets_verified_unchanged':len(protected),'training_snapshots_unchanged':True,'model_replaced_in_platform':False,'independent_validation':False,'no_final_refit_artifact':True,'figures':3}
    save('summary.json',summary);(HERE/'latest_run.txt').write_text(run_id)
    table='\n'.join(f"| {m['candidate']} | {m['RMSE']:.4f} | {m['MAE']:.4f} | {m['mean_top1_no_tie']:.1%} |" for m in metrics)
    report=f'''# نتيجة مقارنة XGBoost المحدودة

{decision}

83 خلية، ثلاث إعادات من التقييم المتداخل بتقسيمات الدراسة نفسها. الهدف LN_IC50؛ الأصغر أفضل.

| المسار | RMSE | MAE | تطابق الدواء الأدنى |
|---|---:|---:|---:|
{table}

فرق RMSE لصالح XGBoost مقارنة بـRidge: {comparison['delta_RMSE']:.6f}؛ التحسن النسبي {comparison['relative_gain']*100:.2f}%. القيمة السالبة تعني تراجعًا. الفاصل الشرطي95%: {comparison['conditional_95_interval']}. لا يشمل إعادة التدريب أو التحقق المستقل.

قاعدة5% عملية لهذه التجربة، وليست شرط قبول MVP أو معيارًا طبيًا. نسبة تطابق الترتيب ليست درجة ثقة. مصفوفة الارتباك لترتيب IC50 فقط، وليست حساسية/مقاومة. بيانات القياس ذات محدودية218/249 قيمة فوق نطاق الجرعات ما زالت نفسها.

أُعيد إنتاج Ridge التاريخي بفارق أقصى {reproduction:.3g}. مصادر الدراسة المحمية {len(protected)} بقيت مطابقة. لا تغيير في المنصة أو نموذجها، ولا توسيع تلقائي للبحث.
'''
    (out/'RESULTS_AR.md').write_text(report,encoding='utf-8');(HERE/'RESULTS_AR.md').write_text(report,encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2),flush=True)
    return summary

if __name__=='__main__':run()
