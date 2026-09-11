import http from 'node:http';
import path from 'node:path';
import {readFile} from 'node:fs/promises';
const root=path.resolve('dist');
const arg=process.argv.indexOf('--port');
const port=Number(arg>=0?process.argv[arg+1]:process.env.PORT||4173);
const types={'.html':'text/html; charset=utf-8','.css':'text/css','.js':'text/javascript','.mjs':'text/javascript','.svg':'image/svg+xml','.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg','.webp':'image/webp','.json':'application/json','.xml':'application/xml','.txt':'text/plain'};
http.createServer(async(req,res)=>{
 try{
  let url=new URL(req.url,'http://local');let pathname=decodeURIComponent(url.pathname);
  if(pathname==='/_qa/mobile/'){
   res.writeHead(200,{'Content-Type':'text/html; charset=utf-8'});
   return res.end('<!doctype html><html><head><title>EGO mobile QA</title><meta name=viewport content="width=device-width,initial-scale=1"></head><body style="margin:0;background:#ddd;display:flex;justify-content:center"><iframe title="EGO — mobile view" src="/" style="width:390px;height:844px;border:0;background:white"></iframe></body></html>');
  }
  const local=path.resolve(root,'.'+pathname);if(local!==root&&!local.startsWith(root+path.sep)){res.writeHead(403);return res.end();}
  const file=pathname.endsWith('/')?path.join(local,'index.html'):local;
  try{let body=await readFile(file);res.writeHead(200,{'Content-Type':types[path.extname(file)]||'application/octet-stream','Cache-Control':'no-store'});res.end(body);}catch{if(!path.extname(local)){try{let body=await readFile(path.join(local,'index.html'));res.writeHead(200,{'Content-Type':'text/html; charset=utf-8'});return res.end(body);}catch{}}
  res.writeHead(404,{'Content-Type':'text/html; charset=utf-8'});res.end(await readFile(path.join(root,'404.html')));}
 }catch{res.writeHead(400);res.end('Bad request');}
}).listen(port,'0.0.0.0',()=>console.log(`EGO preview listening on ${port}`));
