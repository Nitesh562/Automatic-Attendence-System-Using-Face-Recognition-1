import os, sqlite3, csv, io
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file
import cv2, numpy as np
from openpyxl import Workbook

BASE=os.path.dirname(os.path.abspath(__file__))
DB=os.path.join(BASE,"data","attendance.db")
FACES=os.path.join(BASE,"data","faces")
REPORTS=os.path.join(BASE,"data","reports")
MODEL=os.path.join(BASE,"data","trainer.yml")
os.makedirs(FACES,exist_ok=True); os.makedirs(REPORTS,exist_ok=True)

app=Flask(__name__)

def con():
    c=sqlite3.connect(DB)
    c.execute("CREATE TABLE IF NOT EXISTS students(id INTEGER PRIMARY KEY,name TEXT NOT NULL)")
    c.execute("""CREATE TABLE IF NOT EXISTS attendance(
        id INTEGER,name TEXT,date TEXT,time TEXT, UNIQUE(id,date))""")
    c.commit(); return c

def detector():
    return cv2.CascadeClassifier(cv2.data.haarcascades+"haarcascade_frontalface_default.xml")

def train_model():
    faces=[]; ids=[]; det=detector()
    for fn in os.listdir(FACES):
        if not fn.endswith(".jpg"): continue
        try: sid=int(fn.split(".")[1])
        except: continue
        img=cv2.imread(os.path.join(FACES,fn),cv2.IMREAD_GRAYSCALE)
        if img is None: continue
        found=det.detectMultiScale(img,1.2,5)
        for x,y,w,h in found:
            faces.append(img[y:y+h,x:x+w]); ids.append(sid)
    if not faces: return False,0
    rec=cv2.face.LBPHFaceRecognizer_create()
    rec.train(faces,np.array(ids)); rec.write(MODEL)
    return True,len(faces)

@app.route("/")
def index(): return render_template("index.html")

@app.route("/api/students",methods=["GET"])
def students():
    c=con(); rows=c.execute("SELECT id,name FROM students ORDER BY id").fetchall(); c.close()
    return jsonify([{"id":r[0],"name":r[1]} for r in rows])

@app.route("/api/register",methods=["POST"])
def register():
    sid=request.form.get("id","").strip(); name=request.form.get("name","").strip()
    if not sid.isdigit() or not name: return jsonify(ok=False,error="Enter a numeric ID and name."),400
    sid=int(sid); c=con(); c.execute("INSERT OR REPLACE INTO students VALUES(?,?)",(sid,name)); c.commit(); c.close()
    files=request.files.getlist("images")
    saved=0
    for i,f in enumerate(files,1):
        data=f.read(); arr=np.frombuffer(data,np.uint8); img=cv2.imdecode(arr,cv2.IMREAD_GRAYSCALE)
        if img is None: continue
        cv2.imwrite(os.path.join(FACES,f"User.{sid}.{i}.jpg"),img); saved+=1
    return jsonify(ok=True,saved=saved)

@app.route("/api/train",methods=["POST"])
def train():
    ok,n=train_model()
    return jsonify(ok=ok,samples=n,error=None if ok else "Register at least one student with face images.")

@app.route("/api/recognize",methods=["POST"])
def recognize():
    if not os.path.exists(MODEL): return jsonify(ok=False,error="Train faces first.")
    f=request.files.get("image")
    if not f: return jsonify(ok=False,error="No camera image received.")
    arr=np.frombuffer(f.read(),np.uint8); img=cv2.imdecode(arr,cv2.IMREAD_COLOR)
    if img is None: return jsonify(ok=False,error="Invalid image.")
    gray=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY); det=detector()
    rec=cv2.face.LBPHFaceRecognizer_create(); rec.read(MODEL)
    c=con(); results=[]
    for x,y,w,h in det.detectMultiScale(gray,1.2,5):
        sid,conf=rec.predict(gray[y:y+h,x:x+w])
        name=None
        if conf < 70:
            row=c.execute("SELECT name FROM students WHERE id=?",(sid,)).fetchone()
            if row:
                name=row[0]; now=datetime.now()
                try:
                    c.execute("INSERT INTO attendance VALUES(?,?,?,?)",
                              (sid,name,now.strftime("%Y-%m-%d"),now.strftime("%H:%M:%S")))
                    c.commit(); marked=True
                except sqlite3.IntegrityError: marked=False
                results.append({"id":sid,"name":name,"confidence":round(conf,1),"marked":marked})
    c.close()
    return jsonify(ok=True,results=results)

@app.route("/api/attendance")
def attendance():
    c=con(); rows=c.execute("SELECT id,name,date,time FROM attendance ORDER BY date DESC,time DESC").fetchall(); c.close()
    return jsonify([{"id":r[0],"name":r[1],"date":r[2],"time":r[3]} for r in rows])

@app.route("/api/export/<fmt>")
def export(fmt):
    c=con(); rows=c.execute("SELECT id,name,date,time FROM attendance ORDER BY date,time").fetchall(); c.close()
    if fmt=="csv":
        out=io.StringIO(); w=csv.writer(out); w.writerow(["Student ID","Name","Date","Time"]); w.writerows(rows)
        return send_file(io.BytesIO(out.getvalue().encode()),as_attachment=True,download_name="attendance_report.csv",mimetype="text/csv")
    wb=Workbook(); ws=wb.active; ws.title="Attendance"; ws.append(["Student ID","Name","Date","Time"])
    for r in rows: ws.append(r)
    bio=io.BytesIO(); wb.save(bio); bio.seek(0)
    return send_file(bio,as_attachment=True,download_name="attendance_report.xlsx",
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@app.route("/manifest.webmanifest")
def manifest():
    return jsonify({"name":"Face Attendance","short_name":"Attendance","start_url":"/",
                    "display":"standalone","background_color":"#0f172a","theme_color":"#0f172a",
                    "icons":[]})

if __name__=="__main__":
    app.run(host="0.0.0.0",port=5000,debug=False)
