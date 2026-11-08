import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {readFile} from 'node:fs/promises';
const directory=process.argv[2]||'dist';
const worker=(await import(pathToFileURL(path.resolve(directory,'server/index.js')).href)).default;
const info=JSON.parse(await readFile(path.join(directory,'build-info.json'),'utf8'));
const inventory=JSON.parse(await readFile('page-inventory.json','utf8'));
const mapping=JSON.parse(await readFile('redirect-map.json','utf8'));
const errors=[];
const ask=(pathname,init)=>worker.fetch(new Request(info.origin+pathname,init));
for(const page of inventory){
  const response=await ask(page.url);
  if(response.status!==200)errors.push([page.url,'status',response.status]);
  for(const header of ['content-security-policy','x-content-type-options','referrer-policy','x-frame-options','strict-transport-security'])
    if(!response.headers.get(header))errors.push([page.url,'missing header',header]);
  if(info.mode==='preview'&&!response.headers.get('x-robots-tag')?.includes('noindex'))errors.push([page.url,'preview indexing']);
}
for(const [from,to] of Object.entries(mapping)){
  const response=await ask(from);
  if(response.status!==301||response.headers.get('location')!==to)errors.push([from,'redirect']);
}
for(const p of ['/.git/config','/build.py','/server/index.js','/_headers','/not-found-release-check/'])
  if((await ask(p)).status!==404)errors.push([p,'source/404 protection']);
const home=await ask('/');
const tag=home.headers.get('etag');
if((await ask('/',{headers:{'If-None-Match':tag}})).status!==304)errors.push(['ETag']);
if(await (await ask('/',{method:'HEAD'})).text()!=='')errors.push(['HEAD body']);
if((await ask('/',{method:'POST'})).status!==405)errors.push(['Method restriction']);
if((await ask('/bg/info/ceni/?test=1')).headers.get('location')!=='/ceni/?test=1')errors.push(['Redirect query']);
if((await ask('/ceni')).headers.get('location')!=='/ceni/')errors.push(['Slash normalization']);
if((await ask('/ceni/index.html')).headers.get('location')!=='/ceni/')errors.push(['HTML normalization']);
if((await ask('/assets/site.js')).headers.get('content-type')!=='text/javascript; charset=utf-8')errors.push(['Asset MIME']);
if((await ask('/%E0%A4%A')).status!==400)errors.push(['Malformed path']);
const result={mode:info.mode,content_routes:inventory.length,redirects:Object.keys(mapping).length,errors};
console.log(JSON.stringify(result,null,2));
if(errors.length)process.exitCode=1;
