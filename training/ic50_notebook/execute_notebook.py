"""Execute the notebook with a project-local kernel, validate and export HTML."""
from pathlib import Path
import json,sys,time,os
HERE=Path(__file__).resolve().parent
import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager
from jupyter_client.kernelspec import KernelSpecManager
from nbconvert import HTMLExporter
kernel_dir=HERE/'kernels'/'oncotraining';kernel_dir.mkdir(parents=True,exist_ok=True)
(kernel_dir/'kernel.json').write_text(json.dumps({'argv':[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}'],'display_name':'OncoPredict local training','language':'python'}),encoding='utf-8')
path=HERE/'OncoPredict_IC50_EDA_Training.ipynb'
nb=nbformat.read(path,as_version=4);nbformat.validate(nb)
for cell in nb.cells:
    if cell.cell_type=='code':compile(cell.source,'notebook_cell','exec')
manager=KernelManager(kernel_name='oncotraining',kernel_spec_manager=KernelSpecManager(kernel_dirs=[str(HERE/'kernels')]))
def before_cell(cell,cell_index,**kwargs):
    if cell.cell_type=='code':print(f'Executing cell {cell_index+1}/{len(nb.cells)}',flush=True)
client=NotebookClient(nb,km=manager,kernel_name='oncotraining',timeout=1800,allow_errors=False,resources={'metadata':{'path':str(HERE)}},on_cell_start=before_cell)
started=time.perf_counter()
try:
    client.execute()
except Exception:
    nbformat.write(nb,HERE/'FAILED_execution.ipynb')
    raise
nbformat.validate(nb);nbformat.write(nb,path)
template_root=str(HERE/'notebook_runtime/share/jupyter/nbconvert/templates')
exporter=HTMLExporter(extra_template_basedirs=[template_root],extra_template_paths=[template_root]);exporter.exclude_input=False
html,_=exporter.from_notebook_node(nb)
(HERE/'OncoPredict_IC50_EDA_Training.html').write_text(html,encoding='utf-8')
execution={'status':'all_cells_executed_without_errors','elapsed_seconds':time.perf_counter()-started,'code_cells':sum(c.cell_type=='code' for c in nb.cells),'output_images':sum('image/png' in o.get('data',{}) for c in nb.cells if c.cell_type=='code' for o in c.outputs)}
(HERE/'execution_verification.json').write_text(json.dumps(execution,indent=2),encoding='utf-8')
print(json.dumps(execution),flush=True)
