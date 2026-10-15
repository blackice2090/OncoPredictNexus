"""Build and genuinely execute the comparison notebook with a local kernel."""
from pathlib import Path
import sys,json
import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager
from jupyter_client.kernelspec import KernelSpecManager
from nbconvert import HTMLExporter
HERE=Path(__file__).resolve().parent
source=(HERE/'compare.py').read_text(encoding='utf-8').split("if __name__=='__main__':")[0]
source=source.replace('HERE=Path(__file__).resolve().parent','HERE=Path.cwd()\nsys.path.insert(0,str(HERE))')
nb=nbformat.v4.new_notebook(cells=[
    nbformat.v4.new_markdown_cell('<section dir="rtl"><h1>OncoPredict — مقارنة XGBoost المحدودة</h1><p>تجربة داخلية لتوثيق المقارنة الواردة بالخطة الأصلية. لا تستبدل النموذج تلقائيًا، ولا تثبت اعتمادًا سريريًا. اقرأ البروتوكول قبل تعديل الإعدادات.</p></section>'),
    nbformat.v4.new_code_cell("from pathlib import Path\nfrom IPython.display import display,Markdown,Image\ndisplay(Markdown(Path('PROTOCOL_AR.md').read_text(encoding='utf-8')))"),
    nbformat.v4.new_markdown_cell('<section dir="rtl"><h2>الكود الكامل: البيانات والتقسيم والضبط والمقارنة</h2><p>خمس طيات خارجية ×ثلاث إعادات، أربع طيات داخلية، وثمانية إعدادات XGBoost فقط. إعادة إنتاج Ridge التاريخي شرط للتحقق.</p></section>'),
    nbformat.v4.new_code_cell(source),
    nbformat.v4.new_code_cell('summary=run()'),
    nbformat.v4.new_code_cell("out=Path('runs')/summary['run_id']\ndisplay(pd.read_csv(out/'metrics.csv'))\ndisplay(pd.read_csv(out/'per_drug_metrics.csv'))\nfor name in ['01_model_comparison','02_per_drug_errors','03_ranking_confusion_matrices']:\n    display(Image(filename=str(out/'figures'/f'{name}.png')))\ndisplay(Markdown((out/'RESULTS_AR.md').read_text(encoding='utf-8')))"),
    nbformat.v4.new_markdown_cell('<section dir="rtl"><h2>القرار والحدود</h2><p>التوقعات محجوبة داخل التطوير، والخلايا نفسها استُخدمت سابقًا. الفاصل الشرطي لا يشمل إعادة التدريب. مصفوفات الترتيب ليست حساسية/مقاومة، ومحدودية218/249 قياسًا فوق نطاق الجرعات باقية. تُحفظ كل النتائج ولا توسع الشبكة بعد رؤيتها.</p></section>')
],metadata={'kernelspec':{'name':'python3','display_name':'Python 3 — bounded XGBoost','language':'python'},'language_info':{'name':'python'}})
kernel=HERE/'kernels'/'oncopredict_xgb';kernel.mkdir(parents=True,exist_ok=True)
(kernel/'kernel.json').write_text(json.dumps({'argv':[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}'],'display_name':'OncoPredict XGBoost','language':'python'}))
manager=KernelManager(kernel_name='oncopredict_xgb',kernel_spec_manager=KernelSpecManager(kernel_dirs=[str(HERE/'kernels')]))
client=NotebookClient(nb,km=manager,timeout=1800,allow_errors=False,resources={'metadata':{'path':str(HERE)}})
try:client.execute()
except Exception:nbformat.write(nb,HERE/'FAILED_comparison.ipynb');raise
nbformat.validate(nb);path=HERE/'OncoPredict_XGBoost_Comparison.ipynb';nbformat.write(nb,path)
templates=str(HERE.parent/'ic50_notebook/notebook_runtime/share/jupyter/nbconvert/templates')
html,_=HTMLExporter(extra_template_basedirs=[templates],extra_template_paths=[templates]).from_notebook_node(nb)
(HERE/'OncoPredict_XGBoost_Comparison.html').write_text(html,encoding='utf-8')
verification={'all_code_cells_executed':all(c.execution_count is not None for c in nb.cells if c.cell_type=='code'),'no_errors':not any(o.output_type=='error' for c in nb.cells if c.cell_type=='code' for o in c.outputs),'figures':sum('image/png' in o.get('data',{}) for c in nb.cells if c.cell_type=='code' for o in c.outputs)}
(HERE/'execution_verification.json').write_text(json.dumps(verification,indent=2))
print(json.dumps(verification))
