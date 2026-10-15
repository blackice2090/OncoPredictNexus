import numpy as np
def audit_cells(ids,x,y):
    if len(set(ids))!=len(ids):raise ValueError('Duplicate cell identity')
    if x.shape!=(len(ids),8) or y.shape!=(len(ids),3):raise ValueError('Invalid input/target shape')
    if not np.isfinite(x).all() or not np.isin(x,[0,1]).all() or not np.isfinite(y).all():raise ValueError('Missing or invalid data')
def ranking_labels(values):
    minimum=values.min(axis=1,keepdims=True)
    ties=np.isclose(values,minimum,rtol=0,atol=1e-10).sum(axis=1)>1
    return np.where(ties,3,values.argmin(axis=1))
def bootstrap_gain(y,reference,candidate,n_bootstrap=2000):
    if reference.shape!=candidate.shape or reference.shape[1:]!=y.shape:raise ValueError('Prediction shape mismatch')
    base_loss=((reference-y[None,:,:])**2).mean(axis=(0,2))
    new_loss=((candidate-y[None,:,:])**2).mean(axis=(0,2))
    indices=np.random.default_rng(810).integers(0,len(y),(n_bootstrap,len(y)))
    delta=np.sqrt(base_loss[indices].mean(axis=1))-np.sqrt(new_loss[indices].mean(axis=1))
    rmse_base=float(np.sqrt(base_loss.mean()));rmse_new=float(np.sqrt(new_loss.mean()))
    return {'reference_RMSE':rmse_base,'candidate_RMSE':rmse_new,'delta_RMSE':rmse_base-rmse_new,'relative_gain':(rmse_base-rmse_new)/rmse_base if rmse_base else None,'conditional_95_interval':np.quantile(delta,[.025,.975]).tolist(),'method':'paired cell bootstrap, repeats and drugs retained; no retraining'}
