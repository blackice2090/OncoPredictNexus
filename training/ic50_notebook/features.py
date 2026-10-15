"""Target-free genomic interactions, persisted by name for reloadable pipelines."""
import numpy as np
FEATURES=['EGFR_mutation_present','TP53_mutation_present','KRAS_mutation_present','L858R','Exon19_deletion','T790M','C797S','Other_EGFR']
ENGINEERED_NAMES=FEATURES+['EGFR_x_TP53','EGFR_x_KRAS','TP53_x_KRAS']
def add_genomic_interactions(x):
    x=np.asarray(x,dtype=float)
    if x.ndim!=2 or x.shape[1]!=8 or not np.isfinite(x).all() or not np.isin(x,[0,1]).all():
        raise ValueError('Expected eight complete binary genomic inputs; missing values are not zeros.')
    return np.column_stack([x,x[:,0]*x[:,1],x[:,0]*x[:,2],x[:,1]*x[:,2]])
