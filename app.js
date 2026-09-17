let stream=null, timer=null, images=[];
const video=document.getElementById("video"), canvas=document.getElementById("canvas");
async function capture(){
  if(!stream) await startCamera();
  images=[];
  for(let i=0;i<20;i++){await new Promise(r=>setTimeout(r,100));canvas.width=video.videoWidth;canvas.height=video.videoHeight;canvas.getContext("2d").drawImage(video,0,0);let b=await new Promise(r=>canvas.toBlob(r,"image/jpeg",.8));images.push(new File([b],`face${i}.jpg`,{type:"image/jpeg"}));}
  document.getElementById("preview").innerHTML=`<b>${images.length} face samples captured.</b>`;
}
async function startCamera(){
  try{stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:"user"},audio:false});video.srcObject=stream;document.getElementById("status").textContent="Camera running";}catch(e){alert("Camera permission is required. Use HTTPS or localhost.");}
}
async function start(){await startCamera();if(timer)return;timer=setInterval(scan,1200)}
function stop(){if(timer){clearInterval(timer);timer=null}if(stream){stream.getTracks().forEach(t=>t.stop());stream=null}video.srcObject=null;document.getElementById("status").textContent="Camera stopped"}
async function scan(){if(!stream)return;canvas.width=video.videoWidth;canvas.height=video.videoHeight;canvas.getContext("2d").drawImage(video,0,0);let b=await new Promise(r=>canvas.toBlob(r,"image/jpeg",.75));let fd=new FormData();fd.append("image",b,"camera.jpg");let r=await fetch("/api/recognize",{method:"POST",body:fd});let d=await r.json();if(d.results?.length){document.getElementById("status").textContent=d.results.map(x=>`${x.name}: ${x.marked?"Attendance marked":"Already marked"}`).join(" | ");loadAttendance()}}
async function register(){let id=document.getElementById("sid").value,name=document.getElementById("name").value;if(!id||!name||!images.length){alert("Enter ID/name and capture face first.");return}let fd=new FormData();fd.append("id",id);fd.append("name",name);images.forEach(x=>fd.append("images",x));let r=await fetch("/api/register",{method:"POST",body:fd});let d=await r.json();if(d.ok){alert("Student registered.");images=[];document.getElementById("preview").textContent=""}else alert(d.error)}
async function train(){let r=await fetch("/api/train",{method:"POST"}),d=await r.json();document.getElementById("trainmsg").textContent=d.ok?`Training complete: ${d.samples} samples.`:d.error}
async function loadAttendance(){let d=await (await fetch("/api/attendance")).json();document.getElementById("rows").innerHTML=d.map(x=>`<tr><td>${x.id}</td><td>${x.name}</td><td>${x.date}</td><td>${x.time}</td></tr>`).join("")}
loadAttendance();
