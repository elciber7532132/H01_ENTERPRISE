#!/usr/bin/env python3
"""HT-01 Enterprise - backend de demostración funcional (Python stdlib)."""
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import sqlite3, json, csv, io, os, re, uuid, hashlib, hmac, secrets, time, math, mimetypes, threading, tempfile
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse, parse_qs

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.environ.get('HT01_DATA_DIR', str(ROOT / 'data')))
STORE_JSON = DATA_DIR / 'ht01_store.json'
UPLOADS = DATA_DIR / 'private_uploads'
_STORE_LOCK = threading.RLock()
_STORE_CONN = None
_STORE_READY = False
STATIC = ROOT / 'static'
UPLOADS.mkdir(parents=True, exist_ok=True)
MAX_UPLOAD = 5 * 1024 * 1024
SESSION_HOURS = 8
SECRET = os.environ.get('HT01_SECRET', 'CAMBIAR-ESTA-CLAVE-EN-PRODUCCION-' + str(uuid.uuid4()))

SCHEMA = '''
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('admin','instructor','student')), active INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS sessions(token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id), expires_at TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS datasets(id TEXT PRIMARY KEY, name TEXT NOT NULL, source_type TEXT NOT NULL, filename TEXT, file_key TEXT, rows_json TEXT NOT NULL, profile_json TEXT NOT NULL, row_count INTEGER NOT NULL, column_count INTEGER NOT NULL, status TEXT NOT NULL, owner_id TEXT REFERENCES users(id), created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS practices(id TEXT PRIMARY KEY, title TEXT NOT NULL, dataset_id TEXT NOT NULL REFERENCES datasets(id), approach TEXT NOT NULL, problem_type TEXT NOT NULL, target_column TEXT, feature_columns TEXT NOT NULL, objective TEXT NOT NULL, created_by TEXT NOT NULL REFERENCES users(id), created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS executions(id TEXT PRIMARY KEY, practice_id TEXT NOT NULL REFERENCES practices(id), status TEXT NOT NULL, engine_type TEXT NOT NULL, engine_version TEXT NOT NULL, started_at TEXT NOT NULL, finished_at TEXT, result_json TEXT, error_code TEXT, error_message TEXT);
CREATE TABLE IF NOT EXISTS audit_events(id TEXT PRIMARY KEY, actor_id TEXT, action TEXT NOT NULL, entity_type TEXT, entity_id TEXT, outcome TEXT NOT NULL, metadata_json TEXT, occurred_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS learning_progress(user_id TEXT NOT NULL REFERENCES users(id), unit_id TEXT NOT NULL, completed_at TEXT NOT NULL, PRIMARY KEY(user_id,unit_id));
'''

def now(): return datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds')
class JsonBackedConnection:
    """SQL workspace in memory; durable application records are serialized to JSON."""
    def __init__(self, conn):
        self._conn=conn
    def __getattr__(self, name):
        return getattr(self._conn, name)
    def close(self):
        # The shared in-memory workspace remains available for subsequent requests.
        return None
    def commit(self):
        with _STORE_LOCK:
            self._conn.commit()
            _save_json_store(self._conn)

def _save_json_store(conn):
    tables=['users','sessions','datasets','practices','executions','audit_events','learning_progress']
    snapshot={'format':'HT01_JSON_STORE_V1','updated_at':now(),'tables':{}}
    for table in tables:
        cur=conn.execute(f'SELECT * FROM {table}')
        cols=[d[0] for d in cur.description]
        snapshot['tables'][table]=[{cols[i]:row[i] for i in range(len(cols))} for row in cur.fetchall()]
    DATA_DIR.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='ht01_',suffix='.tmp',dir=str(DATA_DIR))
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            json.dump(snapshot,f,ensure_ascii=False,separators=(',',':'))
            f.flush(); os.fsync(f.fileno())
        os.replace(tmp,STORE_JSON)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

def db():
    global _STORE_CONN, _STORE_READY
    with _STORE_LOCK:
        if _STORE_CONN is None:
            DATA_DIR.mkdir(parents=True,exist_ok=True)
            raw=sqlite3.connect(':memory:',check_same_thread=False)
            raw.row_factory=sqlite3.Row
            raw.execute('PRAGMA foreign_keys=ON')
            raw.executescript(SCHEMA)
            if STORE_JSON.exists():
                try:
                    snapshot=json.loads(STORE_JSON.read_text(encoding='utf-8'))
                    tables=snapshot.get('tables',{})
                    for table in ['users','datasets','practices','executions','audit_events','learning_progress','sessions']:
                        records=tables.get(table,[])
                        if not records: continue
                        cols=list(records[0].keys())
                        marks=','.join('?' for _ in cols)
                        names=','.join('"'+c+'"' for c in cols)
                        raw.executemany(f'INSERT OR REPLACE INTO {table} ({names}) VALUES ({marks})',
                                        [[r.get(c) for c in cols] for r in records])
                    raw.commit()
                except Exception as exc:
                    raise RuntimeError('No se pudo leer ht01_store.json: '+str(exc))
            _STORE_CONN=raw
            _STORE_READY=True
        return JsonBackedConnection(_STORE_CONN)
def pw_hash(pw, salt=None):
    salt=salt or secrets.token_bytes(16); return salt.hex()+hashlib.pbkdf2_hmac('sha256',pw.encode(),salt,240000).hex()
def pw_ok(pw, stored):
    try:
        salt=bytes.fromhex(stored[:32]); expected=stored[32:]; got=hashlib.pbkdf2_hmac('sha256',pw.encode(),salt,240000).hex(); return hmac.compare_digest(got,expected)
    except Exception: return False

def seed():
    c=db(); c.executescript(SCHEMA)
    users=[('admin','Administración HT-01','admin@ht01.local','AdminHT01!2026','admin'),('instructor','Instructor HT-01','instructor@ht01.local','DocenteHT01!2026','instructor'),('student','Estudiante HT-01','estudiante@ht01.local','AlumnoHT01!2026','student')]
    for uid,name,email,pw,role in users:
        if not c.execute('SELECT 1 FROM users WHERE email=?',(email,)).fetchone(): c.execute('INSERT INTO users VALUES(?,?,?,?,?,?,?)',(uid,name,email,pw_hash(pw),role,1,now()))
    demo=[
      ('Solicitudes de crédito (sintético)','classification',[{'edad':22+i%35,'ingreso_mensual':1200+(i*317)%6500,'antiguedad_laboral':i%12,'aprobada':'Sí' if (i*7+i//3)%5<3 else 'No'} for i in range(80)]),
      ('Ventas mensuales (sintético)','regression',[{'inversion_publicitaria':200+(i*73)%900,'visitas_web':500+(i*193)%4000,'descuento_pct':i%25,'ventas':round(1200+(200+(i*73)%900)*2.7+(500+(i*193)%4000)*.42-(i%25)*11+((i*17)%75),2)} for i in range(80)]),
      ('Comportamiento de clientes (sintético)','clustering',[{'frecuencia_mensual':1+(i*7)%18,'gasto_promedio':round(25+(i*31)%280,2),'meses_antiguedad':1+(i*11)%48} for i in range(90)])]
    for name,kind,rows in demo:
        if not c.execute('SELECT 1 FROM datasets WHERE name=?',(name,)).fetchone():
            profile=profile_rows(rows)
            c.execute('INSERT INTO datasets VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(str(uuid.uuid4()),name,'DEMO SINTÉTICO',None,None,json.dumps(rows),json.dumps(profile),len(rows),len(rows[0]),'Válido','admin',now()))
    c.commit(); c.close()

def infer_type(vals):
    non=[v for v in vals if v not in (None,'')]
    if not non:return 'vacío'
    try:
        for v in non: float(str(v).replace(',','.'))
        return 'numérico'
    except: pass
    return 'categórico'
def profile_rows(rows):
    if not rows: raise ValueError('El CSV no contiene filas de datos.')
    cols=list(rows[0].keys())
    if not cols or any(not str(x).strip() for x in cols): raise ValueError('Hay encabezados vacíos.')
    if len(set(cols))!=len(cols): raise ValueError('Hay encabezados duplicados.')
    columns=[]; warnings=[]
    for col in cols:
        vals=[r.get(col) for r in rows]; non=[v for v in vals if v not in (None,'')]; typ=infer_type(vals)
        nulls=len(vals)-len(non); distinct=len(set(str(v) for v in non))
        item={'name':col,'type':typ,'null_count':nulls,'null_pct':round(nulls/len(rows)*100,1),'distinct_count':distinct}
        if typ=='numérico' and non:
            nums=sorted(float(str(v).replace(',','.')) for v in non)
            q1=nums[len(nums)//4]; q3=nums[(3*len(nums))//4]; iqr=q3-q1
            outliers=sum(v<q1-1.5*iqr or v>q3+1.5*iqr for v in nums)
            item.update({'min':round(min(nums),3),'max':round(max(nums),3),'mean':round(sum(nums)/len(nums),3),'outlier_count':outliers})
        elif typ=='categórico':
            freq={}
            for value in non: freq[str(value)]=freq.get(str(value),0)+1
            item.update({'top_values':sorted(freq.items(),key=lambda kv:(-kv[1],kv[0]))[:5]})
        columns.append(item)
        if nulls: warnings.append(f'{col}: {nulls} valores faltantes ({item["null_pct"]}%).')
        if distinct<=1: warnings.append(f'{col}: columna constante o con un único valor.')
    seen=set(); dup=0
    for r in rows:
        key=json.dumps(r,sort_keys=True,ensure_ascii=False)
        if key in seen: dup+=1
        seen.add(key)
    if dup: warnings.append(f'Se detectaron {dup} filas duplicadas exactas.')
    return {'row_count':len(rows),'column_count':len(cols),'columns':columns,'duplicate_rows':dup,'warnings':warnings,'preview':rows[:8], 'quality_status':'Válido con advertencias' if warnings else 'Válido'}

def audit(c,actor,action,etype=None,eid=None,outcome='Éxito',meta=None):
    c.execute('INSERT INTO audit_events VALUES(?,?,?,?,?,?,?,?)',(str(uuid.uuid4()),actor,action,etype,eid,outcome,json.dumps(meta or {},ensure_ascii=False),now()))
def user_public(u): return {'id':u['id'],'name':u['name'],'email':u['email'],'role':u['role'],'active':bool(u['active'])}
def parse_body(handler):
    n=int(handler.headers.get('Content-Length','0'))
    if n>MAX_UPLOAD+1024*100: raise ValueError('La solicitud supera el límite permitido.')
    raw=handler.rfile.read(n) if n else b''
    ct=handler.headers.get('Content-Type','')
    if 'application/json' in ct: return json.loads(raw or b'{}'),None
    if 'multipart/form-data' in ct:
        # Minimal multipart parser using email package
        from email.parser import BytesParser
        from email.policy import default
        msg=BytesParser(policy=default).parsebytes(b'Content-Type: '+ct.encode()+b'\r\nMIME-Version: 1.0\r\n\r\n'+raw)
        fields={}; filedata=None; filename=None
        for part in msg.iter_parts():
            name=part.get_param('name',header='content-disposition')
            fn=part.get_filename()
            payload=part.get_payload(decode=True) or b''
            if fn: filename=Path(fn).name; filedata=payload
            elif name: fields[name]=payload.decode('utf-8','replace')
        return fields,(filename,filedata) if filename else None
    return {},None

class Handler(BaseHTTPRequestHandler):
    server_version='HT01Enterprise/1.0'
    def log_message(self,fmt,*args): print('[%s] %s'%(now(),fmt%args))
    def cors(self):
        origin=self.headers.get('Origin','')
        allowed=[x.strip() for x in os.environ.get('HT01_CORS_ORIGINS','').split(',') if x.strip()]
        if origin and origin in allowed:
            self.send_header('Access-Control-Allow-Origin',origin); self.send_header('Vary','Origin'); self.send_header('Access-Control-Allow-Credentials','true')
        self.send_header('Access-Control-Allow-Headers','Content-Type'); self.send_header('Access-Control-Allow-Methods','GET,POST,PATCH,DELETE,OPTIONS')
    def do_OPTIONS(self):
        self.send_response(204); self.cors(); self.send_header('Content-Length','0'); self.end_headers()
    def send_json(self,status,obj):
        data=json.dumps(obj,ensure_ascii=False).encode(); self.send_response(status); self.cors(); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Content-Length',str(len(data))); self.send_header('Cache-Control','no-store'); self.end_headers(); self.wfile.write(data)
    def send_file(self,path,ctype=None,download=None):
        data=Path(path).read_bytes(); self.send_response(200); self.cors(); self.send_header('Content-Type',ctype or mimetypes.guess_type(str(path))[0] or 'application/octet-stream'); self.send_header('Content-Length',str(len(data))); self.send_header('X-Content-Type-Options','nosniff')
        if download:self.send_header('Content-Disposition',f'attachment; filename="{download}"')
        self.end_headers(); self.wfile.write(data)
    def token_user(self):
        cookie=self.headers.get('Cookie',''); m=re.search(r'ht01_session=([A-Za-z0-9_-]+)',cookie)
        if not m:return None
        th=hashlib.sha256(m.group(1).encode()).hexdigest(); c=db(); row=c.execute('SELECT u.* FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.token_hash=? AND s.expires_at>?',(th,now())).fetchone(); c.close()
        return row
    def require(self,roles=None):
        u=self.token_user()
        if not u or not u['active']: raise PermissionError('Sesión no válida o expirada.')
        if roles and u['role'] not in roles: raise PermissionError('No tiene permisos para realizar esta operación.')
        return u
    def do_GET(self):
        path=urlparse(self.path).path
        try:
            if path=='/api/health': return self.send_json(200,{'status':'ok','service':'HT-01 Enterprise'})
            if path.startswith('/api/'):
                u=self.require()
                if path=='/api/me': return self.send_json(200,{'user':user_public(u)})
                if path=='/api/dashboard':
                    c=db(); scope='' if u['role']!='student' else ' AND p.created_by=?'; args=() if not scope else (u['id'],)
                    practices=c.execute('SELECT COUNT(*) n FROM practices p WHERE 1=1'+scope,args).fetchone()['n']
                    datasets=c.execute('SELECT COUNT(*) n FROM datasets').fetchone()['n']
                    runs=c.execute('SELECT COUNT(*) n FROM executions e JOIN practices p ON p.id=e.practice_id WHERE 1=1'+scope,args).fetchone()['n']
                    recent=c.execute('SELECT e.id,e.status,e.started_at,e.engine_type,p.title,d.name dataset_name FROM executions e JOIN practices p ON p.id=e.practice_id JOIN datasets d ON d.id=p.dataset_id WHERE 1=1'+scope+' ORDER BY e.started_at DESC LIMIT 6',args).fetchall()
                    progress=c.execute('SELECT COUNT(*) n FROM learning_progress WHERE user_id=?',(u['id'],)).fetchone()['n']; c.close()
                    return self.send_json(200,{'stats':{'practices':practices,'datasets':datasets,'executions':runs,'learning_units':progress},'recent':[dict(x) for x in recent],'engine':'Motor ML real integrado (Python puro) para esta versión'})
                if path=='/api/learning':
                    c=db(); done={x['unit_id'] for x in c.execute('SELECT unit_id FROM learning_progress WHERE user_id=?',(u['id'],))}; c.close()
                    units=learning_units();
                    for x in units:x['completed']=x['id'] in done
                    return self.send_json(200,{'units':units})
                if path=='/api/datasets':
                    c=db(); rows=c.execute('SELECT id,name,source_type,filename,row_count,column_count,status,owner_id,created_at,profile_json FROM datasets ORDER BY created_at DESC').fetchall(); c.close()
                    return self.send_json(200,{'datasets':[dataset_public(x) for x in rows]})
                if path.startswith('/api/datasets/'):
                    did=path.split('/')[-1]; c=db(); x=c.execute('SELECT * FROM datasets WHERE id=?',(did,)).fetchone(); c.close()
                    if not x: return self.send_json(404,{'error':'Dataset no encontrado.'})
                    return self.send_json(200,dataset_detail(x))
                if path=='/api/practices':
                    c=db(); sql='SELECT p.*,d.name dataset_name FROM practices p JOIN datasets d ON d.id=p.dataset_id'; args=()
                    if u['role']=='student':sql+=' WHERE p.created_by=?';args=(u['id'],)
                    sql+=' ORDER BY p.created_at DESC'; rows=c.execute(sql,args).fetchall(); c.close(); return self.send_json(200,{'practices':[practice_public(x) for x in rows]})
                if path=='/api/executions':
                    q=parse_qs(urlparse(self.path).query); c=db(); sql='SELECT e.*,p.title,p.created_by,d.name dataset_name,p.approach FROM executions e JOIN practices p ON p.id=e.practice_id JOIN datasets d ON d.id=p.dataset_id WHERE 1=1'; args=[]
                    if u['role']=='student':sql+=' AND p.created_by=?';args.append(u['id'])
                    for key,col in [('status','e.status'),('approach','p.approach'),('dataset','d.name')]:
                        if q.get(key):sql+=f' AND {col} LIKE ?';args.append('%'+q[key][0]+'%')
                    if q.get('from'):sql+=' AND date(e.started_at)>=date(?)';args.append(q['from'][0])
                    if q.get('to'):sql+=' AND date(e.started_at)<=date(?)';args.append(q['to'][0])
                    sql+=' ORDER BY e.started_at DESC'; rows=c.execute(sql,args).fetchall(); c.close(); return self.send_json(200,{'executions':[execution_public(x) for x in rows]})
                if path.startswith('/api/executions/'):
                    eid=path.split('/')[-1]; c=db(); x=c.execute('SELECT e.*,p.title,p.created_by,p.objective,p.approach,p.problem_type,p.target_column,p.feature_columns,d.name dataset_name FROM executions e JOIN practices p ON p.id=e.practice_id JOIN datasets d ON d.id=p.dataset_id WHERE e.id=?',(eid,)).fetchone(); c.close()
                    if not x:return self.send_json(404,{'error':'Ejecución no encontrada.'})
                    if u['role']=='student' and x['created_by']!=u['id']:raise PermissionError('No tiene acceso a esta ejecución.')
                    return self.send_json(200,execution_detail(x))
                if path=='/api/users':
                    if u['role']!='admin':raise PermissionError('Solo administración puede gestionar usuarios.')
                    c=db(); rows=c.execute('SELECT * FROM users ORDER BY created_at DESC').fetchall(); c.close(); return self.send_json(200,{'users':[user_public(x) for x in rows]})
                if path=='/api/audit':
                    if u['role'] not in ('admin','instructor'):raise PermissionError('No tiene permisos para consultar auditoría.')
                    c=db(); rows=c.execute('SELECT a.*,u.name actor_name FROM audit_events a LEFT JOIN users u ON u.id=a.actor_id ORDER BY occurred_at DESC LIMIT 250').fetchall(); c.close(); return self.send_json(200,{'events':[dict(x) for x in rows]})
                return self.send_json(404,{'error':'Endpoint no encontrado.'})
            if path=='/' or path=='/index.html':return self.send_file(STATIC/'index.html','text/html; charset=utf-8')
            p=(STATIC/path.lstrip('/')).resolve()
            if STATIC.resolve() not in p.parents: return self.send_json(403,{'error':'Ruta no permitida.'})
            if p.is_file():return self.send_file(p)
            return self.send_json(404,{'error':'Recurso no encontrado.'})
        except PermissionError as e:self.send_json(403,{'error':str(e)})
        except Exception as e:self.send_json(400,{'error':str(e)})
    def do_POST(self):
        path=urlparse(self.path).path
        try:
            data,file=parse_body(self)
            if path=='/api/login':
                email=str(data.get('email','')).lower().strip(); pw=str(data.get('password','')); c=db(); u=c.execute('SELECT * FROM users WHERE email=?',(email,)).fetchone()
                if not u or not pw_ok(pw,u['password_hash']) or not u['active']:
                    audit(c,None,'LOGIN','session',None,'Denegado',{'email_provided':bool(email)});c.commit();c.close();return self.send_json(401,{'error':'No se pudo iniciar sesión. Verifique sus credenciales o contacte al administrador.'})
                token=secrets.token_urlsafe(36); c.execute('INSERT INTO sessions VALUES(?,?,?,?)',(hashlib.sha256(token.encode()).hexdigest(),u['id'],(datetime.now(timezone.utc)+timedelta(hours=SESSION_HOURS)).isoformat(),now())); audit(c,u['id'],'LOGIN','session',None,'Éxito'); c.commit(); c.close()
                self.send_response(200); self.cors(); self.send_header('Content-Type','application/json; charset=utf-8'); cookie_mode='SameSite=None; Secure' if os.environ.get('HT01_CROSS_SITE_COOKIE','0')=='1' else 'SameSite=Lax'
                self.send_header('Set-Cookie',f'ht01_session={token}; HttpOnly; {cookie_mode}; Path=/; Max-Age={SESSION_HOURS*3600}'); self.send_header('Cache-Control','no-store'); body=json.dumps({'user':user_public(u)},ensure_ascii=False).encode();self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body);return
            u=self.require()
            if path=='/api/logout':
                cookie=self.headers.get('Cookie','');m=re.search(r'ht01_session=([A-Za-z0-9_-]+)',cookie);c=db()
                if m:c.execute('DELETE FROM sessions WHERE token_hash=?',(hashlib.sha256(m.group(1).encode()).hexdigest(),))
                audit(c,u['id'],'LOGOUT','session',None);c.commit();c.close();self.send_response(200);self.cors();self.send_header('Set-Cookie','ht01_session=; HttpOnly; SameSite=None; Secure; Path=/; Max-Age=0');self.send_header('Content-Length','2');self.end_headers();self.wfile.write(b'{}');return
            if path=='/api/datasets':
                if file:
                    filename,raw=file
                    if not filename.lower().endswith('.csv'):raise ValueError('Formato no permitido. Solo se acepta CSV.')
                    if not raw or len(raw)>MAX_UPLOAD:raise ValueError('El archivo está vacío o supera el límite de 5 MB.')
                    try: txt=raw.decode('utf-8-sig')
                    except UnicodeDecodeError: txt=raw.decode('latin-1')
                    reader=csv.DictReader(io.StringIO(txt))
                    if not reader.fieldnames:raise ValueError('El CSV no contiene encabezados válidos.')
                    headers=[h.strip() if h else '' for h in reader.fieldnames]
                    if len(set(headers))!=len(headers) or any(not h for h in headers):raise ValueError('Los encabezados deben ser únicos y no pueden estar vacíos.')
                    rows=[]
                    for row in reader:
                        rows.append({headers[i]: (row.get(reader.fieldnames[i]) or '').strip() for i in range(len(headers))})
                        if len(rows)>10000:raise ValueError('El dataset supera el máximo de 10 000 filas.')
                    if not rows:raise ValueError('El CSV debe contener al menos una fila de datos.')
                    name=str(data.get('name') or Path(filename).stem)[:100]
                    key=secrets.token_hex(20); (UPLOADS/key).write_bytes(raw); source='CSV importado'; stored_file=filename
                else:
                    raise ValueError('Seleccione un archivo CSV para importar.')
                prof=profile_rows(rows); did=str(uuid.uuid4()); c=db(); c.execute('INSERT INTO datasets VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(did,name,source,stored_file,key,json.dumps(rows,ensure_ascii=False),json.dumps(prof,ensure_ascii=False),len(rows),len(rows[0]),prof['quality_status'],u['id'],now())); audit(c,u['id'],'DATASET_IMPORT','dataset',did,'Éxito',{'filename':stored_file,'rows':len(rows)});c.commit();c.close();return self.send_json(201,{'dataset_id':did,'dataset':{'id':did,'name':name,'profile':prof}})
            if path.startswith('/api/learning/'):
                unit=path.split('/')[-1]
                if unit not in {x['id'] for x in learning_units()}:raise ValueError('Unidad de aprendizaje no válida.')
                c=db();c.execute('INSERT OR IGNORE INTO learning_progress VALUES(?,?,?)',(u['id'],unit,now()));audit(c,u['id'],'LEARNING_COMPLETE','learning_unit',unit);c.commit();c.close();return self.send_json(200,{'ok':True})
            if path=='/api/practices':
                did=str(data.get('dataset_id','')); approach=data.get('approach'); problem=data.get('problem_type'); target=data.get('target_column') or None; features=data.get('feature_columns') or []; title=str(data.get('title') or 'Práctica HT-01').strip()[:120]; objective=str(data.get('objective') or '').strip()[:500]
                c=db();ds=c.execute('SELECT * FROM datasets WHERE id=?',(did,)).fetchone();c.close()
                if not ds:raise ValueError('Seleccione un dataset válido.')
                rows=json.loads(ds['rows_json']); cols=list(rows[0].keys()); prof=json.loads(ds['profile_json']); types={x['name']:x['type'] for x in prof['columns']}
                if approach=='supervised':
                    if problem not in ('classification','regression'):raise ValueError('Seleccione clasificación o regresión.')
                    if target not in cols:raise ValueError('La variable objetivo es obligatoria y debe existir.')
                    if problem=='classification' and types[target] not in ('categórico','numérico'):raise ValueError('Clasificación requiere una variable objetivo categórica o discreta.')
                    if problem=='regression' and types[target]!='numérico':raise ValueError('Regresión requiere una variable objetivo numérica.')
                elif approach=='unsupervised':
                    problem='clustering';target=None
                else:raise ValueError('Enfoque de aprendizaje no válido.')
                features=[x for x in features if x in cols and x!=target]
                if not features: features=[x['name'] for x in prof['columns'] if x['type']=='numérico' and x['name']!=target]
                if not features:raise ValueError('Seleccione al menos una variable numérica de entrada.')
                if any(types[f]!='numérico' for f in features):raise ValueError('La primera versión del motor requiere variables de entrada numéricas. Excluya o transforme las columnas categóricas.')
                pid=str(uuid.uuid4());c=db();c.execute('INSERT INTO practices VALUES(?,?,?,?,?,?,?,?,?,?)',(pid,title,did,approach,problem,target,json.dumps(features),objective,u['id'],now()));audit(c,u['id'],'PRACTICE_CREATE','practice',pid,'Éxito',{'approach':approach,'problem_type':problem});c.commit();c.close();return self.send_json(201,{'practice_id':pid})
            if path.startswith('/api/practices/') and path.endswith('/execute'):
                pid=path.split('/')[-2];c=db();p=c.execute('SELECT p.*,d.rows_json,d.profile_json,d.name dataset_name FROM practices p JOIN datasets d ON d.id=p.dataset_id WHERE p.id=?',(pid,)).fetchone()
                if not p: c.close();return self.send_json(404,{'error':'Práctica no encontrada.'})
                if u['role']=='student' and p['created_by']!=u['id']:c.close();raise PermissionError('No puede ejecutar prácticas de otro usuario.')
                eid=str(uuid.uuid4());started=now();c.execute('INSERT INTO executions VALUES(?,?,?,?,?,?,?,?,?,?)',(eid,pid,'En proceso','ML_REAL','HT01-PureML-1.0',started,None,None,None,None));c.commit()
                try:
                    result=run_model(p,json.loads(p['rows_json']))
                    status='Completada' if not result['warnings'] else 'Con advertencias'
                    c.execute('UPDATE executions SET status=?,finished_at=?,result_json=? WHERE id=?',(status,now(),json.dumps(result,ensure_ascii=False),eid));audit(c,u['id'],'EXECUTION','execution',eid,status,{'engine':'ML_REAL','version':'HT01-PureML-1.0'});c.commit();c.close();return self.send_json(201,{'execution_id':eid,'status':status,'result':result})
                except Exception as e:
                    c.execute('UPDATE executions SET status=?,finished_at=?,error_code=?,error_message=? WHERE id=?',('Fallida',now(),'ML_EXECUTION_ERROR',str(e)[:300],eid));audit(c,u['id'],'EXECUTION','execution',eid,'Fallida',{'code':'ML_EXECUTION_ERROR'});c.commit();c.close();return self.send_json(422,{'error':str(e),'execution_id':eid})
            if path.startswith('/api/executions/') and path.endswith('/report'):
                eid=path.split('/')[-2]; c=db(); row=c.execute('SELECT e.id,p.created_by FROM executions e JOIN practices p ON p.id=e.practice_id WHERE e.id=?',(eid,)).fetchone()
                if not row: c.close(); return self.send_json(404,{'error':'Ejecución no encontrada.'})
                if u['role']=='student' and row['created_by']!=u['id']: c.close(); raise PermissionError('No tiene acceso a esta ejecución.')
                audit(c,u['id'],'REPORT_EXPORT','execution',eid,'Éxito',{'format':'HTML'}); c.commit(); c.close(); return self.send_json(200,{'ok':True})
            if path=='/api/users':
                if u['role']!='admin':raise PermissionError('Solo administración puede crear usuarios.')
                name=str(data.get('name','')).strip();email=str(data.get('email','')).lower().strip();pw=str(data.get('password',''));role=data.get('role')
                if not name or not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$',email) or len(pw)<10 or role not in ('admin','instructor','student'):raise ValueError('Complete nombre, correo válido, contraseña de 10 caracteres y rol.')
                c=db();uid=str(uuid.uuid4())
                try:c.execute('INSERT INTO users VALUES(?,?,?,?,?,?,?)',(uid,name,email,pw_hash(pw),role,1,now()))
                except sqlite3.IntegrityError:c.close();raise ValueError('Ya existe un usuario con ese correo.')
                audit(c,u['id'],'USER_CREATE','user',uid,'Éxito',{'role':role});c.commit();c.close();return self.send_json(201,{'user_id':uid})
            return self.send_json(404,{'error':'Endpoint no encontrado.'})
        except PermissionError as e:self.send_json(403,{'error':str(e)})
        except Exception as e:self.send_json(400,{'error':str(e)})
    def do_PATCH(self):
        try:
            u=self.require(['admin']); path=urlparse(self.path).path
            if not path.startswith('/api/users/'):return self.send_json(404,{'error':'Endpoint no encontrado.'})
            data,_=parse_body(self);uid=path.split('/')[-1];active=1 if data.get('active') else 0
            if uid==u['id'] and not active:raise ValueError('No puede desactivar su propia cuenta.')
            c=db();c.execute('UPDATE users SET active=? WHERE id=?',(active,uid));audit(c,u['id'],'USER_STATUS','user',uid,'Éxito',{'active':bool(active)});c.commit();c.close();return self.send_json(200,{'ok':True})
        except PermissionError as e:self.send_json(403,{'error':str(e)})
        except Exception as e:self.send_json(400,{'error':str(e)})
    def do_DELETE(self):
        try:
            u=self.require(['admin']); path=urlparse(self.path).path
            if path.startswith('/api/datasets/'):
                did=path.split('/')[-1]; c=db(); row=c.execute('SELECT file_key FROM datasets WHERE id=?',(did,)).fetchone()
                if not row: c.close(); return self.send_json(404,{'error':'Dataset no encontrado.'})
                used=c.execute('SELECT COUNT(*) n FROM practices WHERE dataset_id=?',(did,)).fetchone()['n']
                if used: c.close(); return self.send_json(409,{'error':'No se puede eliminar: el dataset está asociado a prácticas. Conserve la trazabilidad histórica.'})
                c.execute('DELETE FROM datasets WHERE id=?',(did,)); audit(c,u['id'],'DATASET_DELETE','dataset',did,'Éxito'); c.commit(); c.close()
                if row['file_key'] and (UPLOADS/row['file_key']).exists(): (UPLOADS/row['file_key']).unlink()
                return self.send_json(200,{'ok':True})
            return self.send_json(405,{'error':'Operación no permitida.'})
        except PermissionError as e:self.send_json(403,{'error':str(e)})
        except Exception as e:self.send_json(400,{'error':str(e)})

def dataset_public(x):return {'id':x['id'],'name':x['name'],'source_type':x['source_type'],'filename':x['filename'],'row_count':x['row_count'],'column_count':x['column_count'],'status':x['status'],'created_at':x['created_at'],'profile':json.loads(x['profile_json'])}
def dataset_detail(x):return {'dataset':dataset_public(x),'rows':json.loads(x['rows_json'])[:8]}
def practice_public(x):return {'id':x['id'],'title':x['title'],'dataset_id':x['dataset_id'],'dataset_name':x['dataset_name'],'approach':x['approach'],'problem_type':x['problem_type'],'target_column':x['target_column'],'feature_columns':json.loads(x['feature_columns']),'objective':x['objective'],'created_at':x['created_at']}
def execution_public(x):return {'id':x['id'],'practice_id':x['practice_id'],'title':x['title'],'dataset_name':x['dataset_name'],'status':x['status'],'engine_type':x['engine_type'],'engine_version':x['engine_version'],'started_at':x['started_at'],'finished_at':x['finished_at'],'approach':x['approach']}
def execution_detail(x):return {'execution':execution_public(x),'configuration':{'objective':x['objective'],'approach':x['approach'],'problem_type':x['problem_type'],'target_column':x['target_column'],'feature_columns':json.loads(x['feature_columns'])},'result':json.loads(x['result_json']) if x['result_json'] else None,'error':x['error_message']}

def learning_units():
 return [
 {'id':'ia','title':'Inteligencia Artificial','category':'Fundamentos','body':'Campo que desarrolla sistemas capaces de realizar tareas asociadas con capacidades inteligentes.','example':'Un sistema que reconoce patrones en documentos o recomienda contenidos.','takeaway':'La IA no implica que un sistema comprenda como una persona; depende de datos, objetivos y límites.'},
 {'id':'ml','title':'Machine Learning','category':'Fundamentos','body':'Enfoque de IA que permite aprender patrones a partir de datos para producir predicciones o apoyar decisiones.','example':'Un modelo aprende de ejemplos históricos y estima la categoría de una nueva solicitud.','takeaway':'Los datos, el entrenamiento y la evaluación determinan la utilidad del modelo.'},
 {'id':'data','title':'Datos e información','category':'Datos','body':'Los datos son registros o valores. La información surge al organizarlos e interpretarlos dentro de un contexto.','example':'Datos: 120, 135 y 150 ventas. Información: las ventas muestran una tendencia creciente en el periodo.','takeaway':'El contexto convierte registros aislados en información útil.'},
 {'id':'supervised','title':'Aprendizaje supervisado','category':'Enfoques ML','body':'Utiliza ejemplos que incluyen una salida o etiqueta conocida para aprender a predecirla.','example':'Registros de solicitudes con resultado aprobado o rechazado.','takeaway':'Requiere una variable objetivo conocida.'},
 {'id':'unsupervised','title':'Aprendizaje no supervisado','category':'Enfoques ML','body':'Busca estructura, similitudes o agrupaciones sin recibir una etiqueta objetivo.','example':'Agrupar clientes por frecuencia y gasto sin segmentos preasignados.','takeaway':'Explora patrones; los grupos no equivalen automáticamente a categorías verdaderas.'},
 {'id':'classification','title':'Clasificación','category':'Tipos de problema','body':'Predice una categoría o clase discreta.','example':'Estimar si una solicitud pertenece a la clase aprobada o rechazada.','takeaway':'La salida es una categoría.'},
 {'id':'regression','title':'Regresión','category':'Tipos de problema','body':'Estima un valor numérico continuo.','example':'Estimar ventas o demanda de un periodo.','takeaway':'La salida es un valor numérico.'},
 {'id':'workflow','title':'Flujo de trabajo ML','category':'Proceso','body':'Definir el problema, revisar datos, preparar variables, dividir datos, entrenar, evaluar e interpretar.','example':'Un pipeline reproducible registra cada etapa y las transformaciones realizadas.','takeaway':'La evaluación debe corresponder al objetivo y no solo a una cifra aislada.'},
 {'id':'why-now','title':'¿Por qué ahora?','category':'Contexto','body':'La disponibilidad de datos, capacidad de cómputo y herramientas facilita aplicar ML a tareas concretas.','example':'Automatizar análisis repetitivos con revisión humana y controles de calidad.','takeaway':'Adoptar IA requiere propósito, gobernanza y evaluación de riesgos.'}]

def run_model(p,rows):
    features=json.loads(p['feature_columns']); target=p['target_column']; approach=p['approach']; problem=p['problem_type']; warnings=[]
    def num(v):
        try:return float(str(v).replace(',','.'))
        except:return None
    valid=[]
    for r in rows:
        vals=[num(r.get(f)) for f in features]
        if any(v is None for v in vals):continue
        y=r.get(target) if target else None
        if target and (y is None or str(y).strip()==''):continue
        valid.append((vals,str(y) if y is not None else None))
    if len(valid)<12:raise ValueError('Se requieren al menos 12 filas completas para separar entrenamiento y prueba.')
    if len(valid)<len(rows):warnings.append(f'Se excluyeron {len(rows)-len(valid)} filas con datos incompletos o no numéricos en las variables seleccionadas.')
    # deterministic 80/20 holdout
    split=max(8,int(len(valid)*.8)); train=valid[:split]; test=valid[split:]
    if not test:raise ValueError('No hay suficientes filas para el conjunto de prueba.')
    if approach=='unsupervised':
        xs=[x for x,y in valid]; k=3 if len(xs)>=18 else 2
        mins=[min(row[j] for row in xs) for j in range(len(features))]; maxs=[max(row[j] for row in xs) for j in range(len(features))]
        norm=[[(r[j]-mins[j])/(maxs[j]-mins[j] or 1) for j in range(len(features))] for r in xs]
        centers=[norm[int(i*len(norm)/k)][:] for i in range(k)]; labels=[]
        for _ in range(30):
            labels=[min(range(k),key=lambda z:sum((v-centers[z][j])**2 for j,v in enumerate(row))) for row in norm]
            for z in range(k):
                members=[row for row,l in zip(norm,labels) if l==z]
                if members:centers[z]=[sum(r[j] for r in members)/len(members) for j in range(len(features))]
        counts=[labels.count(z) for z in range(k)]; inertia=sum(sum((v-centers[l][j])**2 for j,v in enumerate(row)) for row,l in zip(norm,labels))
        return {'engine_label':'MODELO ML REAL · K-MEANS','engine_type':'ML_REAL','algorithm':'K-Means','algorithm_version':'1.0','rows_used':len(xs),'train_rows':len(xs),'test_rows':0,'features':features,'metrics':[{'name':'Número de grupos (k)','value':k,'unit':'grupos'},{'name':'Inercia (SSE)','value':round(inertia,4),'unit':'menor es mejor'}],'clusters':[{'cluster':i+1,'records':counts[i]} for i in range(k)],'explanation':f'K-Means agrupó {len(xs)} registros usando {len(features)} variables numéricas. Los grupos se forman por cercanía; requieren interpretación del contexto.','warnings':warnings+['Aprendizaje no supervisado: no existe etiqueta verdadera para calcular accuracy.','La inercia depende de la escala de las variables; se normalizaron valores para agrupar.'],'pipeline':['Dataset validado','Variables numéricas seleccionadas','Normalización min-max','K-Means (k='+str(k)+')','Resumen de agrupamientos']}
    if problem=='classification':
        labels=sorted(set(y for x,y in valid));
        if len(labels)<2:raise ValueError('La variable objetivo necesita al menos dos clases distintas.')
        if len(labels)>12:raise ValueError('El motor de demostración admite hasta 12 clases distintas.')
        means={}; vars_={}; priors={}
        for lab in labels:
            group=[x for x,y in train if y==lab]
            if not group:continue
            priors[lab]=len(group)/len(train); means[lab]=[sum(r[j] for r in group)/len(group) for j in range(len(features))]; vars_[lab]=[sum((r[j]-means[lab][j])**2 for r in group)/max(1,len(group)-1) or 1e-6 for j in range(len(features))]
        preds=[]
        for x,y in test:
            scores={}
            for lab in means:
                s=math.log(priors[lab])
                for j,v in enumerate(x):s-=.5*math.log(2*math.pi*vars_[lab][j])+(v-means[lab][j])**2/(2*vars_[lab][j])
                scores[lab]=s
            preds.append((y,max(scores,key=scores.get)))
        acc=sum(a==b for a,b in preds)/len(preds); per=[]
        for lab in labels:
            tp=sum(a==lab and b==lab for a,b in preds); fp=sum(a!=lab and b==lab for a,b in preds); fn=sum(a==lab and b!=lab for a,b in preds)
            prec=tp/(tp+fp) if tp+fp else 0; rec=tp/(tp+fn) if tp+fn else 0; f1=2*prec*rec/(prec+rec) if prec+rec else 0
            per.append({'class':lab,'precision':round(prec,4),'recall':round(rec,4),'f1':round(f1,4),'support':sum(a==lab for a,b in preds)})
        return {'engine_label':'MODELO ML REAL · GAUSSIAN NAIVE BAYES','engine_type':'ML_REAL','algorithm':'Gaussian Naive Bayes','algorithm_version':'1.0','rows_used':len(valid),'train_rows':len(train),'test_rows':len(test),'features':features,'target':target,'metrics':[{'name':'Accuracy','value':round(acc,4),'unit':'0–1'},{'name':'Macro F1','value':round(sum(x['f1'] for x in per)/len(per),4),'unit':'0–1'}],'class_metrics':per,'explanation':f'El modelo aprendió distribuciones numéricas por clase con {len(train)} registros y se evaluó sobre {len(test)} registros no usados durante el ajuste. Accuracy mide aciertos globales; Macro F1 resume precisión y recall por clase.','warnings':warnings+['Gaussian Naive Bayes supone independencia condicional entre variables; el resultado depende de la representatividad del dataset.'],'pipeline':['Validación de variable objetivo categórica','Eliminación de filas incompletas','Separación entrenamiento/prueba 80/20','Ajuste Gaussian Naive Bayes','Evaluación con Accuracy y Macro F1']}
    if problem=='regression':
        # standardize features, fit multiple linear regression via gradient descent
        xs=[x for x,y in train]; ys=[float(y) for x,y in train]
        means=[sum(r[j] for r in xs)/len(xs) for j in range(len(features))]; stds=[(sum((r[j]-means[j])**2 for r in xs)/len(xs))**.5 or 1 for j in range(len(features))]
        X=[[(r[j]-means[j])/stds[j] for j in range(len(features))] for r in xs]; xt=[[(r[j]-means[j])/stds[j] for j in range(len(features))] for r,y in test]
        ym=sum(ys)/len(ys); weights=[0.0]*len(features); bias=ym; lr=.03
        for _ in range(1800):
            gb=0; gw=[0.0]*len(features)
            for row,y in zip(X,ys):
                pred=bias+sum(a*b for a,b in zip(weights,row)); err=pred-y; gb+=err
                for j,v in enumerate(row):gw[j]+=err*v
            bias-=lr*gb/len(X)
            weights=[w-lr*g/len(X) for w,g in zip(weights,gw)]
        actual=[float(y) for x,y in test]; pred=[bias+sum(a*b for a,b in zip(weights,row)) for row in xt]
        mae=sum(abs(a-b) for a,b in zip(actual,pred))/len(actual); mse=sum((a-b)**2 for a,b in zip(actual,pred))/len(actual); rmse=mse**.5; ss=sum((a-sum(actual)/len(actual))**2 for a in actual); r2=1-sum((a-b)**2 for a,b in zip(actual,pred))/(ss or 1)
        return {'engine_label':'MODELO ML REAL · REGRESIÓN LINEAL','engine_type':'ML_REAL','algorithm':'Regresión lineal multivariable (descenso de gradiente)','algorithm_version':'1.0','rows_used':len(valid),'train_rows':len(train),'test_rows':len(test),'features':features,'target':target,'metrics':[{'name':'MAE','value':round(mae,4),'unit':'unidades de la variable objetivo'},{'name':'RMSE','value':round(rmse,4),'unit':'unidades de la variable objetivo'},{'name':'R²','value':round(r2,4),'unit':'0–1 (puede ser negativo)'}],'predictions':[{'actual':round(a,3),'predicted':round(b,3)} for a,b in list(zip(actual,pred))[:30]],'explanation':'MAE y RMSE expresan el error de predicción; menor suele ser mejor. R² compara el ajuste con predecir la media y puede ser negativo. Las variables se estandarizaron usando solo entrenamiento.','warnings':warnings+['La regresión lineal modela relaciones lineales; no demuestra causalidad y puede ser sensible a valores atípicos.'],'pipeline':['Validación de objetivo numérico','Eliminación de filas incompletas','Separación entrenamiento/prueba 80/20','Estandarización ajustada con entrenamiento','Entrenamiento por descenso de gradiente','Evaluación MAE, RMSE y R²']}
    raise ValueError('Tipo de práctica no soportado.')

if __name__=='__main__':
    DATA_DIR.mkdir(parents=True,exist_ok=True); UPLOADS.mkdir(parents=True,exist_ok=True)
    seed(); host=os.environ.get('HT01_HOST','0.0.0.0'); port=int(os.environ.get('PORT',os.environ.get('HT01_PORT','8000')))
    print(f'HT-01 Enterprise disponible en http://{host}:{port}'); print('Persistencia: archivo JSON ht01_store.json; archivos CSV en private_uploads.')
    HTTPServer((host,port),Handler).serve_forever()
