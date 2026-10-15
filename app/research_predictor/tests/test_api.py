import json,tempfile,unittest
from pathlib import Path
from fastapi.testclient import TestClient
from app.research_predictor.api import create_app
from .test_engine import ROOT,VALID

class APITests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.client=TestClient(create_app(ROOT,Path(self.tmp.name)))
    def tearDown(self):self.client.close();self.tmp.cleanup()
    def payload(self,profile=None,**extras):return {'profile':profile or VALID,'case_source':'manual_research_profile',**extras}
    def test_prediction_persisted_and_exported(self):
        response=self.client.post('/predict',json=self.payload());self.assertEqual(response.status_code,200,response.text)
        data=response.json();rid=data['run_id'];self.assertEqual(len(data['drugs']),3)
        self.assertEqual(self.client.get('/runs/'+rid).json(),data)
        self.assertEqual(self.client.get('/runs').json()[0]['run_id'],rid)
        self.assertEqual(self.client.get('/runs/'+rid+'/json').json(),data)
        csv=self.client.get('/runs/'+rid+'/csv');self.assertIn('predicted_LN_IC50',csv.text);self.assertIn('not_validation',csv.text)
        report=self.client.get('/runs/'+rid+'/report');self.assertEqual(report.status_code,200);self.assertIn(rid,report.text);self.assertIn('LN_IC50',report.text)
    def test_invalid_inputs_never_saved(self):
        for bad in [{**VALID,'tp53_mutated':None},{**VALID,'kras_mutated':0},{**VALID,'egfr_variants':['C797S']},{**VALID,'age':40}]:
            self.assertEqual(self.client.post('/predict',json=self.payload(bad)).status_code,422)
        self.assertEqual(self.client.get('/runs').json(),[])
    def test_training_cell_identity_checked(self):
        cell=self.client.get('/cells').json()[0]
        good={'profile':cell['profile'],'case_source':'original_training_cell','cell_id':cell['id']}
        self.assertEqual(self.client.post('/predict',json=good).status_code,200)
        good['profile']={**cell['profile'],'tp53_mutated':not cell['profile']['tp53_mutated']}
        self.assertEqual(self.client.post('/predict',json=good).status_code,422)
    def test_no_patient_or_tcga_claims(self):
        self.assertEqual(self.client.post('/predict',json=self.payload(case_source='TCGA')).status_code,422)
        self.assertEqual(self.client.get('/health').json()['status'],'ready')
        self.assertEqual(self.client.get('/model-info').json()['threshold_policy'],'deferred_no_validated_thresholds')
        self.assertEqual(len(self.client.get('/explain/global').json()['drugs']),3)

    def test_documented_proxy_identity_provenance_and_exports(self):
        proxy=self.client.get('/demo/tcga').json()
        body={'profile':proxy['profile'],'case_source':'tcga_demo_proxy','proxy_id':proxy['id']}
        response=self.client.post('/predict',json=body)
        self.assertEqual(response.status_code,200,response.text)
        result=response.json();rid=result['run_id']
        self.assertFalse(result['provenance']['independent_model_validation'])
        self.assertFalse(result['provenance']['drug_response_available'])
        self.assertEqual(result['provenance']['id'],proxy['id'])
        self.assertEqual(self.client.get('/runs').json()[0]['proxy_id'],proxy['id'])
        self.assertIn(proxy['commit'],self.client.get('/runs/'+rid+'/report?lang=en').text)
        self.assertIn(proxy['id'],self.client.get('/runs/'+rid+'/csv?lang=en').text)
        for altered in [{**body,'proxy_id':'invented'},{**body,'profile':{**proxy['profile'],'kras_mutated':False}},{**body,'cell_id':'SIDM00759'},self.payload(proxy_id=proxy['id'])]:
            self.assertEqual(self.client.post('/predict',json=altered).status_code,422)
        self.assertEqual(len(self.client.get('/runs').json()),1)

    def test_original_cell_variant_order_is_not_identity(self):
        cell=next(c for c in self.client.get('/cells').json() if c['id']=='SIDM00759')
        profile={**cell['profile'],'egfr_variants':list(reversed(cell['profile']['egfr_variants']))}
        self.assertEqual(self.client.post('/predict',json={'profile':profile,'case_source':'original_training_cell','cell_id':cell['id']}).status_code,200)
    def test_rejects_unknown_run_and_remote_origin(self):
        self.assertEqual(self.client.get('/runs/../../source').status_code,404)
        self.assertEqual(self.client.get('/runs/'+'0'*32).status_code,404)
        self.assertEqual(self.client.post('/predict',json=self.payload(),headers={'Origin':'https://example.com'}).status_code,403)
    def test_schema_documents_profile_and_version(self):
        spec=self.client.get('/openapi.json').json();self.assertIn('/predict',spec['paths']);self.assertIn('GenomicProfile',spec['components']['schemas'])

    def test_xgboost_evidence_is_completed_without_model_replacement(self):
        info=self.client.get('/model-info').json()
        comparison=info['xgboost_comparison']
        self.assertEqual(comparison['status'],'bounded_xgboost_comparison_completed')
        self.assertFalse(comparison['model_replaced_in_platform']);self.assertFalse(comparison['independent_validation'])
        self.assertEqual(info['family'],'Ridge')

    def test_english_exports_preserve_scientific_values_and_saved_record(self):
        original=self.client.post('/predict',json=self.payload()).json();rid=original['run_id']
        html=self.client.get('/runs/'+rid+'/report?lang=en').text
        self.assertIn('lang="en"',html);self.assertIn('dir="ltr"',html);self.assertIn('Research prediction report',html)
        translated=self.client.get('/runs/'+rid+'/json?lang=en').json()
        self.assertEqual(translated['drugs'][0]['predicted_LN_IC50'],original['drugs'][0]['predicted_LN_IC50'])
        self.assertIn('not an independent',translated['warnings'][0])
        self.assertEqual(self.client.get('/runs/'+rid).json(),original)
        self.assertIn('not an independent',self.client.get('/runs/'+rid+'/csv?lang=en').text)

if __name__=='__main__':unittest.main()
