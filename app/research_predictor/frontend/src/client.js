import {createHistory,exportJSON,exportCSV,reportHTML} from './private-history.js';
let metadata;
const history=()=>createHistory(window.localStorage);
export async function request(url,options){
 if(url==='/runs')return history().list();
 if(/^\/runs\/[a-f0-9]{32}$/.test(url))return history().get(url.split('/')[2]);
 const response=await fetch(url,options);let data;try{data=await response.json();}catch{throw Error('Unable to read the prediction service response.');}
 if(!response.ok)throw Error(data.detail||data.error||'Unable to complete the request.');
 if(url==='/model-info')metadata=data;
 if(url==='/predict'){data={...data,record_storage:'browser_only',model_metadata:metadata};history().save(data);}
 return data;
}
export function downloadResult(record,lang,info,format){
 const metadata=record.model_metadata||info;
 const contents=format==='report'?reportHTML(record,lang,metadata):format==='csv'?exportCSV(record,lang,metadata):exportJSON(record,lang,metadata);
 const url=URL.createObjectURL(new Blob([contents],{type:format==='report'?'text/html;charset=utf-8':format==='csv'?'text/csv;charset=utf-8':'application/json;charset=utf-8'}));
 if(format==='report')window.open(url,'_blank','noopener,noreferrer');
 else{const a=document.createElement('a');a.href=url;a.download='oncopredict-'+record.run_id+'.'+format;document.body.appendChild(a);a.click();a.remove();}
 window.setTimeout(()=>URL.revokeObjectURL(url),60000);
}
