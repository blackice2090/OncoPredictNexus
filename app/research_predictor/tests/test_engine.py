import itertools,math,tempfile,unittest,shutil
from pathlib import Path
import numpy as np
from app.research_predictor.engine import PredictionEngine,profile_vector,rank_predictions

ROOT=Path(__file__).resolve().parents[3]
VALID={'egfr_mutated':True,'egfr_variants':['L858R'],'tp53_mutated':False,'kras_mutated':False}

class EngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.engine=PredictionEngine(ROOT)

    def test_complete_consistent_inputs_only(self):
        np.testing.assert_array_equal(profile_vector(VALID),[1,0,0,1,0,0,0,0])
        for bad in [{**VALID,'tp53_mutated':None},{**VALID,'kras_mutated':0},{**VALID,'egfr_mutated':False},{**VALID,'egfr_variants':['C797S']},{**VALID,'egfr_variants':['unknown']},{**VALID,'egfr_variants':['Other_EGFR','L858R']},{**VALID,'extra':1}]:
            with self.subTest(bad=bad),self.assertRaises(ValueError):profile_vector(bad)

    def test_every_training_cell_matches_original_artifact(self):
        e=self.engine
        expected=e.model.predict(e.x)
        for i,x in enumerate(e.x):
            result=e.predict_vector(x)
            np.testing.assert_allclose([r['predicted_LN_IC50'] for r in result['drugs']],expected[i],rtol=1e-12)
            for r in result['drugs']:
                self.assertAlmostEqual(r['shap_base_value']+sum(c['value'] for c in r['shap_values']),r['predicted_LN_IC50'],places=11)
                self.assertAlmostEqual(math.exp(r['predicted_LN_IC50']),r['predicted_IC50_uM'],places=11)
                self.assertIsNone(r['sensitivity_status'])

    def test_shap_matches_coalition_definition(self):
        e=self.engine;x=profile_vector(VALID);m=len(x)
        actual=e.predict_vector(x)['drugs']
        def coalition(S):
            background=e.x.copy()
            for i in S:background[:,i]=x[i]
            return e.model.predict(background).mean(axis=0)
        for i in range(m):
            others=[k for k in range(m) if k!=i];value=np.zeros(3)
            for n in range(m):
                for S in itertools.combinations(others,n):
                    weight=math.factorial(n)*math.factorial(m-n-1)/math.factorial(m)
                    value+=weight*(coalition((*S,i))-coalition(S))
            for j in range(3):self.assertAlmostEqual(actual[j]['shap_values'][i]['value'],value[j],places=10)

    def test_ranking_keeps_ties(self):self.assertEqual(rank_predictions([1,1,2]),[1,1,3])

    def test_known_cells_warn_training_not_validation(self):
        result=self.engine.predict(VALID)
        self.assertIn('not_independent_validation',result['warnings_codes'])
        self.assertNotIn('confidence',result)

    def test_source_hash_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):PredictionEngine(Path(tmp))

    def test_changed_verified_bytes_block_inference(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/'app/research_predictor/assets'
            shutil.copytree(self.engine.assets,target)
            isolated=PredictionEngine(Path(tmp))
            with (target/'cell_features_83.csv').open('ab') as stream:stream.write(b'changed')
            with self.assertRaises(ValueError):isolated.predict(VALID)

if __name__=='__main__':unittest.main()
