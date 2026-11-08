import http from 'node:http';
import path from 'node:path';
import {readFile,stat} from 'node:fs/promises';
const root=path.resolve('dist');
const arg=process.argv.indexOf('--port');
const port=Number(arg>=0?process.argv[arg+1]:process.env.PORT||4173);
const types={'.html':'text/html; charset=utf-8','.css':'text/css; charset=utf-8','.js':'text/javascript; charset=utf-8','.svg':'image/svg+xml','.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg','.webp':'image/webp','.json':'application/json','.xml':'application/xml; charset=utf-8','.txt':'text/plain; charset=utf-8'};
async function responseHeaders(pathname){
 const headers={};let pattern='';
 for(const line of (await readFile(path.join(root,'_headers'),'utf8')).split('\n')){
  if(!line.trim()||line.startsWith('#'))continue;
  if(!/^\s/.test(line)){pattern=line.trim();continue;}
  const at=line.indexOf(':');
  const matches=pattern==='/*'||pattern==='/assets/*'&&pathname.startsWith('/assets/')||pattern==='/'&&pathname==='/'||pattern==='/*/'&&pathname.endsWith('/')&&pathname!=='/'||pattern==='/*.html'&&pathname.endsWith('.html')||pattern===pathname;
  if(at>0 && matches)headers[line.slice(0,at).trim()]=line.slice(at+1).trim();
 }
 return headers;
}
http.createServer(async(req,res)=>{
 try{
  if(!['GET','HEAD'].includes(req.method)){res.writeHead(405,{'Allow':'GET, HEAD'});return res.end();}
  const url=new URL(req.url,'http://local');const pathname=decodeURIComponent(url.pathname);
  const headers=await responseHeaders(pathname);
  if(pathname==='/_qa/http-audit/'){
   // Developer-only checks run next to the supervised preview server.
   // This route is never copied into dist or deployed to the public site.
   const inventory=JSON.parse(await readFile('page-inventory.json','utf8'));
   const redirects=(await readFile(path.join(root,'_redirects'),'utf8')).trim().split('\n').map(line=>line.split(/\s+/));
   const failures=[];
   const local='http://127.0.0.1:'+port;
   const pages=inventory.filter(item=>item.url!='/404/');
   for(const item of pages){
    const response=await fetch(local+item.url,{redirect:'manual'});
    if(response.status!==200)failures.push([item.url,'Expected 200',response.status]);
    for(const name of ['content-security-policy','x-content-type-options','referrer-policy','permissions-policy','strict-transport-security']){
     if(!response.headers.get(name))failures.push([item.url,'Missing header',name]);
    }
    await response.arrayBuffer();
   }
   for(const [from,to,code] of redirects){
    const response=await fetch(local+from,{redirect:'manual'});
    if(response.status!==Number(code)||response.headers.get('location')!==to)failures.push([from,response.status,response.headers.get('location')]);
    await response.arrayBuffer();
   }
   for(const target of ['/missing-page-for-release-audit/','/.git/config','/content.py','/_headers']){
    const response=await fetch(local+target,{redirect:'manual'});
    if(response.status!==404)failures.push([target,'Expected 404',response.status]);
    await response.arrayBuffer();
   }
   for(const [target,expected] of [['/ceni','/ceni/'],['/bg/info/ceni/?audit=1','/ceni/?audit=1']]){
    const response=await fetch(local+target,{redirect:'manual'});
    if(response.status!==301||response.headers.get('location')!==expected)failures.push([target,'Incorrect normalisation/query redirect']);
    await response.arrayBuffer();
   }
   const post=await fetch(local+'/',{method:'POST'});
   if(post.status!==405)failures.push(['POST /','Expected 405',post.status]);
   await post.arrayBuffer();
   const result={content_pages_checked:pages.length,legacy_redirects_checked:redirects.length,errors:failures,scope:'Supervised preview HTTP responses; final public host still requires verification.'};
   res.writeHead(200,{'Content-Type':'text/html; charset=utf-8','Cache-Control':'no-store','X-Robots-Tag':'noindex'});
   return res.end('<!doctype html><html lang="en"><head><title>EGO HTTP audit</title></head><body><h1>EGO HTTP audit</h1><pre>'+JSON.stringify(result,null,2).replaceAll('&','&amp;').replaceAll('<','&lt;')+'</pre></body></html>');
  }
  if(pathname==='/_qa/shell.css'){res.writeHead(200,{'Content-Type':'text/css'});return res.end('body{margin:0;background:#ddd;display:flex;justify-content:center}iframe{border:0;background:white;display:block}');}
  if(pathname==='/_qa/mobile/'){
   const width=Math.max(320,Math.min(800,Number(url.searchParams.get('width'))||390));
   const target=url.searchParams.get('path')||'/';
   if(!/^\/[a-z0-9/\-]*$/.test(target)){res.writeHead(400);return res.end();}
   res.writeHead(200,{'Content-Type':'text/html; charset=utf-8','Cache-Control':'no-store','X-Robots-Tag':'noindex'});
   return res.end('<!doctype html><html lang="bg"><head><title>EGO mobile QA</title><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="stylesheet" href="/_qa/shell.css"></head><body><iframe title="EGO — mobile view" src="'+target+'" width="'+width+'" height="900"></iframe></body></html>');
  }
  // Serve the same direct 301 rules as the static host; preserve query parameters.
  for(const line of (await readFile(path.join(root,'_redirects'),'utf8')).split('\n')){
   const [from,to,status]=line.trim().split(/\s+/);
   if(from===pathname){res.writeHead(Number(status),{...headers,Location:to+url.search});return res.end();}
  }
  if(pathname.split('/').some(part=>part.startsWith('.'))||['/_headers','/_redirects'].includes(pathname)){res.writeHead(404,headers);return res.end();}
  const local=path.resolve(root,'.'+pathname);
  if(local!==root&&!local.startsWith(root+path.sep)){res.writeHead(403,headers);return res.end();}
  try{
   if(!pathname.endsWith('/')&&(await stat(local)).isDirectory()){
    res.writeHead(301,{...headers,Location:pathname+'/'+url.search});return res.end();
   }
  }catch{}
  const file=pathname.endsWith('/')?path.join(local,'index.html'):local;
  try{
   const body=await readFile(file);
   res.writeHead(200,{...headers,'Content-Type':types[path.extname(file)]||'application/octet-stream'});
   return res.end(req.method==='HEAD'?undefined:body);
  }catch{
   res.writeHead(404,{...headers,'Content-Type':'text/html; charset=utf-8'});
   return res.end(req.method==='HEAD'?undefined:await readFile(path.join(root,'404.html')));
  }
 }catch{res.writeHead(400,{'Content-Type':'text/plain'});res.end('Bad request');}
}).listen(port,'0.0.0.0',()=>console.log('EGO preview listening on '+port));
