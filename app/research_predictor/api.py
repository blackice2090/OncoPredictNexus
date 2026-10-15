"""Local FastAPI service; predictions use a frozen artifact, never train here."""
from pathlib import Path
from datetime import datetime,timezone
from typing import Literal
from html import escape
import csv,io,json,os,re,uuid
import numpy as np
from fastapi import FastAPI,HTTPException,Request
from fastapi.responses import HTMLResponse,JSONResponse,Response,FileResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel,ConfigDict,StrictBool
from starlette.middleware.trustedhost import TrustedHostMiddleware
from .engine import PredictionEngine,profile_vector,LIMITATIONS
from .localization import localized_result,render_report

class GenomicProfile(BaseModel):
    model_config=ConfigDict(extra='forbid')
    egfr_mutated:StrictBool
    egfr_variants:list[str]
    tp53_mutated:StrictBool
    kras_mutated:StrictBool

class PredictionRequest(BaseModel):
    model_config=ConfigDict(extra='forbid')
    profile:GenomicProfile
    case_source:Literal['manual_research_profile','original_training_cell','synthetic_demo','tcga_demo_proxy']
    cell_id:str|None=None
    proxy_id:str|None=None

def create_app(root:Path,record_dir:Path|None=None,*,public_demo:bool=False,allowed_hosts:list[str]|None=None):
    engine=PredictionEngine(root)
    records=record_dir or Path(root)/'outputs/prediction_mvp/runs'
    if not public_demo:records.mkdir(parents=True,exist_ok=True)
    app=FastAPI(title='OncoPredict Nexus research prediction API',version='1.1.0',description='Frozen exploratory Ridge. Bilingual presentation. Not for clinical use. No sensitive/resistant thresholds.')
    app.state.engine=engine;app.state.records=records
    app.add_middleware(TrustedHostMiddleware,allowed_hosts=allowed_hosts or ['127.0.0.1','localhost','testserver'])
    @app.middleware('http')
    async def local_origin(request:Request,call_next):
        if public_demo and (request.url.path=='/runs' or request.url.path.startswith('/runs/')):
            return JSONResponse({'error':'Experiments are stored only in your browser.'},status_code=404)
        origin=request.headers.get('origin')
        if request.method=='POST' and origin and origin.rstrip('/')!=str(request.base_url).rstrip('/'):
            return JSONResponse({'error':'هذا المسار يقبل الطلبات من واجهة الجهاز المحلي فقط.'},status_code=403)
        response=await call_next(request)
        response.headers['Cache-Control']='no-store';response.headers['X-Content-Type-Options']='nosniff'
        response.headers['Referrer-Policy']='no-referrer'
        return response
    @app.exception_handler(RequestValidationError)
    async def validation_error(request,exc):
        return JSONResponse({'error':'المدخلات غير مكتملة أو غير صالحة. اختر حالة كل جين؛ لا ترسل بيانات سريرية أو حقولًا إضافية.'},status_code=422)

    def verify():
        try:engine.verify_sources()
        except ValueError as exc:raise HTTPException(503,str(exc))
    def saved(rid):
        if not re.fullmatch(r'[a-f0-9]{32}',rid):raise HTTPException(404,'النتيجة غير موجودة.')
        path=records/(rid+'.json')
        if not path.is_file():raise HTTPException(404,'النتيجة غير موجودة.')
        try:return json.loads(path.read_text(encoding='utf-8'))
        except (OSError,json.JSONDecodeError):raise HTTPException(409,'تعذر قراءة سجل النتيجة.')

    @app.get('/health')
    def health():verify();return {'status':'ready','model_version':engine.version,'scope':'research_only','training_performed':False}
    @app.get('/model-info')
    def model_info():verify();return engine.model_info
    @app.get('/cells')
    def cells():verify();return engine.list_cells()
    @app.get('/demo/tcga')
    def tcga_demo():verify();return engine.tcga_demo
    @app.get('/explain/global')
    def global_explanation():verify();return engine.global_explanation()
    @app.post('/predict')
    def predict(body:PredictionRequest):
        verify();profile=body.profile.model_dump()
        try:
            if body.case_source=='tcga_demo_proxy':
                if body.cell_id is not None or body.proxy_id!=engine.tcga_demo['id'] or not np.array_equal(profile_vector(profile),profile_vector(engine.tcga_demo['profile'])):raise ValueError('بيانات الحالة لا تطابق مثال TCGA الموثق. أي تعديل يصبح إدخالًا بحثيًا يدويًا.')
            elif body.proxy_id is not None:raise ValueError('معرف TCGA مسموح فقط لحالة العرض الموثقة.')
            if body.case_source=='original_training_cell':
                selected=next((c for c in engine.list_cells() if c['id']==body.cell_id),None)
                if not selected or not np.array_equal(profile_vector(selected['profile']),profile_vector(profile)):raise ValueError('المدخلات لا تطابق الخلية الأصلية المختارة. استخدم إدخالًا بحثيًا مستقلًا عند تعديلها.')
            elif body.cell_id is not None:raise ValueError('معرف الخلية مسموح فقط عند اختيار خلية أصلية.')
            result=engine.predict(profile)
        except ValueError as exc:raise HTTPException(422,str(exc))
        result.update({'run_id':uuid.uuid4().hex,'created_at_utc':datetime.now(timezone.utc).isoformat(),'case_source':body.case_source,'cell_id':body.cell_id,'model_sha256':engine.manifest['exploratory_model.joblib']['sha256'],'input_features':dict(zip(engine.artifact['features'],profile_vector(profile).astype(int).tolist()))})
        if body.case_source=='tcga_demo_proxy':
            result['proxy_id']=body.proxy_id
            result['provenance']=engine.tcga_demo
            result['warnings'].append('حالة TCGA للعرض فقط: طفرات مسجلة في المصدر لم نؤكدها سريريًا. لا توجد قياسات دوائية مطابقة للتحقق، ونقل النموذج من الخلايا إلى نسيج المريض غير مثبت. KRAS مسجلة بعمق 17 قراءة؛ لا نُقر جودة التسلسل لهذه الحالة.')
        if public_demo:
            result['record_storage']='browser_only'
            return result
        name=result['run_id'];tmp=records/(name+'.tmp');final=records/(name+'.json')
        try:
            with tmp.open('x',encoding='utf-8') as stream:
                json.dump(result,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.flush();os.fsync(stream.fileno())
            os.replace(tmp,final)
        except OSError:raise HTTPException(503,'تعذر حفظ سجل التجربة؛ لم تُعد النتيجة كمخرَج مكتمل.')
        return result
    @app.get('/runs')
    def runs():
        rows=[]
        for path in sorted(records.glob('*.json'),key=lambda p:p.stat().st_mtime,reverse=True)[:30]:
            try:
                r=json.loads(path.read_text(encoding='utf-8'));row={k:r[k] for k in ['run_id','created_at_utc','case_source','cell_id','model_version','profile']};row['proxy_id']=r.get('proxy_id');rows.append(row)
            except (OSError,json.JSONDecodeError,KeyError):continue
        return rows
    @app.get('/runs/{rid}')
    def get_run(rid:str):return saved(rid)
    @app.get('/runs/{rid}/json')
    def get_json(rid:str,lang:Literal['ar','en']='ar'):
        return Response(json.dumps(localized_result(saved(rid),lang,engine.model_info),ensure_ascii=False,indent=2),media_type='application/json',headers={'Content-Disposition':f'attachment; filename="oncopredict-{rid}.json"'})
    @app.get('/runs/{rid}/csv')
    def get_csv(rid:str,lang:Literal['ar','en']='ar'):
        r=localized_result(saved(rid),lang,engine.model_info);out=io.StringIO();fields=['run_id','created_at_utc','case_source','cell_id','proxy_id','provenance_json','model_version','model_sha256','drug','rank','predicted_LN_IC50','predicted_IC50_uM','sensitivity_status','prediction_role','threshold_policy','shap_method','pattern_training_count','genomic_input_json','warnings_json']
        writer=csv.DictWriter(out,fields);writer.writeheader()
        for d in r['drugs']:
            row={k:r.get(k) for k in fields if k in r};row.update({k:d[k] for k in ['drug','rank','predicted_LN_IC50','predicted_IC50_uM','sensitivity_status']});row['genomic_input_json']=json.dumps(r['profile']);row['warnings_json']=json.dumps(r['warnings'],ensure_ascii=False);row['provenance_json']=json.dumps(r.get('provenance'),ensure_ascii=False);writer.writerow(row)
        return Response('\ufeff'+out.getvalue(),media_type='text/csv; charset=utf-8',headers={'Content-Disposition':f'attachment; filename="oncopredict-{rid}.csv"'})
    @app.get('/runs/{rid}/report',response_class=HTMLResponse)
    def report(rid:str,lang:Literal['ar','en']='ar'):
        return render_report(saved(rid),lang,engine.model_info)
    web=Path(__file__).resolve().parent/'frontend/dist'
    if web.is_dir():
        app.mount('/assets',StaticFiles(directory=web/'assets'),name='assets')
        if (web/'fonts').is_dir():app.mount('/fonts',StaticFiles(directory=web/'fonts'),name='fonts')
        @app.get('/',response_class=HTMLResponse)
        def index():return FileResponse(web/'index.html')
    return app

ROOT=Path(__file__).resolve().parents[2]

def main():
    import argparse,uvicorn
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8766);args=parser.parse_args()
    uvicorn.run(create_app(ROOT),host='127.0.0.1',port=args.port)

if __name__=='__main__':main()
