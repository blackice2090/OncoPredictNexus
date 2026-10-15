"""Public deployment must calculate predictions without sharing or saving visitor runs."""
from pathlib import Path
import inspect,tempfile,unittest
from fastapi.testclient import TestClient
from app.research_predictor.api import create_app

ROOT=Path(__file__).resolve().parents[3]
PROFILE={'egfr_mutated':True,'egfr_variants':['L858R'],'tp53_mutated':True,'kras_mutated':False}

class PublicModeTests(unittest.TestCase):
    def test_public_storage_mode_is_supported_explicitly(self):
        self.assertIn('public_demo',inspect.signature(create_app).parameters)

    def test_public_predictions_never_write_or_expose_server_records(self):
        self.assertIn('public_demo',inspect.signature(create_app).parameters)
        with tempfile.TemporaryDirectory() as tmp:
            records=Path(tmp)/'not-created'
            with TestClient(create_app(ROOT,record_dir=records,public_demo=True,allowed_hosts=['testserver','oncopredictnexus.vercel.app'])) as client:
                result=client.post('/predict',json={'profile':PROFILE,'case_source':'synthetic_demo'}).json()
                self.assertEqual(result['record_storage'],'browser_only')
                self.assertEqual(len(result['drugs']),3)
                self.assertFalse(records.exists())
                for endpoint in ['/runs','/runs/'+result['run_id'],'/runs/'+result['run_id']+'/json']:
                    self.assertEqual(client.get(endpoint).status_code,404)
                self.assertEqual(client.get('/health',headers={'Host':'oncopredictnexus.vercel.app'}).status_code,200)
                self.assertEqual(client.post('/predict',json={'profile':PROFILE,'case_source':'synthetic_demo'},headers={'Origin':'https://other.example'}).status_code,403)

if __name__=='__main__':unittest.main()
