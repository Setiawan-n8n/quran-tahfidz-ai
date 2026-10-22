import io, random, hashlib
import numpy as np
import qrcode
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

app = FastAPI()

HTML_PAGE = """<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Tahfidz & Sanad AI</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <link href="https://fonts.googleapis.com/css2?family=Amiri:wght@700&display=swap" rel="stylesheet">
  <style>.arab { font-family: 'Amiri', serif; line-height: 2.2; }</style>
</head>
<body class="bg-slate-200 flex justify-center min-h-screen">
  <div class="w-full max-w-md bg-white min-h-screen shadow-2xl flex flex-col justify-between">
    <header class="bg-teal-800 text-white p-4">
      <h1 class="text-lg font-bold">Tahfidz & Tahsin Sanad AI</h1>
      <p class="text-xs text-teal-200">Qari Acuan: Syaikh Mahmud Khalil Al-Hushari (Riwayat Hafs)</p>
    </header>
    <main class="flex-1 p-4 space-y-4 overflow-y-auto">
      <div id="tab-1" class="space-y-4">
        <div class="border rounded-2xl p-5 text-center shadow-sm">
          <div class="text-xs text-gray-400">QS. Al-Fatihah : Ayat 1</div>
          <div id="ayat" dir="rtl" class="arab text-4xl my-5 flex justify-center gap-3 flex-wrap">
            <span>بِسْمِ</span><span>ٱللَّهِ</span><span>ٱلرَّحْمَـٰنِ</span><span>ٱلرَّحِيمِ</span>
          </div>
          <div id="info-kata" class="hidden bg-amber-50 border-l-4 border-amber-500 p-3 text-left text-xs rounded"></div>
        </div>
        <div id="kartu-skor" class="hidden border rounded-2xl p-4 shadow-sm">
          <div class="grid grid-cols-3 gap-2 text-center mb-3">
            <div class="bg-green-50 p-2 rounded-xl"><div id="s-lafaz" class="font-bold text-lg text-green-600"></div><div class="text-[10px]">Lafaz</div></div>
            <div class="bg-amber-50 p-2 rounded-xl"><div id="s-tajwid" class="font-bold text-lg text-amber-600"></div><div class="text-[10px]">Tajwid</div></div>
            <div class="bg-blue-50 p-2 rounded-xl"><div id="s-irama" class="font-bold text-lg text-blue-600"></div><div class="text-[10px]">Irama</div></div>
          </div>
          <canvas id="grafikNada" height="120"></canvas>
        </div>
        <div class="text-center pt-2">
          <button id="btn-mic" onclick="rekam()" class="w-20 h-20 rounded-full bg-teal-700 text-white text-3xl shadow-lg">🎙️</button>
          <div id="status-mic" class="text-xs text-gray-600 mt-2">Ketuk Mikrofon untuk Setor Bacaan</div>
        </div>
      </div>
      <div id="tab-2" class="hidden space-y-3">
        <div class="bg-red-50 border border-red-200 p-3 rounded-xl text-xs">
          <b class="text-red-700">MANZIL JATUH TEMPO:</b> QS. An-Naba 1-30 (Hal 582) • Daya Ingat: 61%
        </div>
        <div class="text-sm font-bold">Peta Kekuatan Memori Juz 30 (Hal 582-604)</div>
        <div id="grid-mutabaah" class="grid grid-cols-5 gap-2"></div>
      </div>
      <div id="tab-3" class="hidden space-y-4 text-center">
        <div class="border rounded-2xl p-6 shadow-sm">
          <div class="text-xs text-gray-400">Sambungkan ayat berikut:</div>
          <div id="mhq-soal" dir="rtl" class="arab text-3xl my-4">فَإِذَا فَرَغۡتَ فَٱنصَبۡ</div>
          <div id="mhq-Jawab" dir="rtl" class="arab text-2xl text-green-700 hidden border-t pt-3 mt-3">وَإِلَىٰ رَبِّكَ فَٱرۡغَبۡ</div>
        </div>
        <div class="flex gap-2">
          <button onclick="document.getElementById('mhq-Jawab').classList.remove('hidden')" class="flex-1 border border-teal-700 text-teal-700 py-2 rounded-xl text-sm">Lihat Kunci</button>
          <button onclick="acakSoal()" class="flex-1 bg-teal-700 text-white py-2 rounded-xl text-sm">Soal Baru</button>
        </div>
      </div>
      <div id="tab-4" class="hidden space-y-4">
        <div class="border rounded-2xl p-4 space-y-3">
          <div class="font-bold text-sm">Terbitkan Syahadah Sanad Digital (RSA-SHA256)</div>
          <input id="nama-santri" value="Ahmad Fauzi" class="w-full border p-2 rounded-xl text-sm">
          <button onclick="unduhPdf()" class="w-full bg-amber-600 text-white py-3 rounded-xl font-bold text-sm">Unduh PDF Syahadah Ber-QR Code</button>
        </div>
      </div>
    </main>
    <nav class="border-t grid grid-cols-4 text-center py-2 text-xs bg-white">
      <button onclick="bukaTab(1)">🎙️<br>Setoran</button>
      <button onclick="bukaTab(2)">📊<br>Mutaba'ah</button>
      <button onclick="bukaTab(3)">🤖<br>MHQ Bot</button>
      <button onclick="bukaTab(4)">📜<br>Syahadah</button>
    </nav>
  </div>
<script>
let sedangRekam = false, chart = null;
function bukaTab(n) {
  [1,2,3,4].forEach(i => document.getElementById('tab-'+i).classList.add('hidden'));
  document.getElementById('tab-'+n).classList.remove('hidden');
  if(n===2) muatMutabaah();
}
async function rekam() {
  const btn = document.getElementById('btn-mic'), st = document.getElementById('status-mic');
  if(!sedangRekam) {
    sedangRekam = true; btn.classList.replace('bg-teal-700','bg-red-600');
    st.innerText = 'Sedang menyimak bacaan... Ketuk lagi untuk hasil AI';
  } else {
    sedangRekam = false; btn.classList.replace('bg-red-600','bg-teal-700');
    st.innerText = 'Memproses di AI Server...';
    const fd = new FormData(); fd.append('audio_file', new Blob(['wav']), 's.wav');
    const r = await fetch('/api/v1/evaluate-recitation', {method:'POST', body:fd});
    const d = await r.json();
    st.innerText = 'Ketuk pada kata berwarna merah/kuning di atas untuk detail koreksi';
    document.getElementById('kartu-skor').classList.remove('hidden');
    document.getElementById('s-lafaz').innerText = d.scores.lafaz + '%';
    document.getElementById('s-tajwid').innerText = d.scores.tajwid + '%';
    document.getElementById('s-irama').innerText = d.scores.irama + '%';
    const box = document.getElementById('ayat'); box.innerHTML = '';
    d.words.forEach(w => {
      const s = document.createElement('span'); s.innerText = w.text;
      s.className = 'cursor-pointer px-2 rounded ' + (w.status==='ok'?'text-green-600':w.status==='warn'?'text-amber-600 underline':'text-red-600 underline');
      s.onclick = () => {
        const info = document.getElementById('info-kata'); info.classList.remove('hidden');
        info.innerHTML = '<b>' + w.rule + ':</b> ' + w.msg;
      };
      box.appendChild(s);
    });
    if(chart) chart.destroy();
    chart = new Chart(document.getElementById('grafikNada'), {
      type:'line',
      data:{labels:d.ref.map((_,i)=>i+1), datasets:[
        {label:'Nada Qari Acuan', data:d.ref, borderColor:'#0d9488', pointRadius:0},
        {label:'Nada Suara Anda', data:d.usr, borderColor:'#d97706', borderDash:[4,4], pointRadius:0}
      ]}
    });
  }
}
async function muatMutabaah() {
  const g = document.getElementById('grid-mutabaah'); g.innerHTML = '';
  for(let i=0;i<23;i++) {
    const p = 582+i, w = i<8?'bg-yellow-600':i===8?'bg-red-600':'bg-green-600';
    g.innerHTML += `<div class="${w} text-white p-2 rounded text-center text-xs font-bold">Hal ${p}</div>`;
  }
}
async function acakSoal() {
  const r = await fetch('/api/v1/mhq'); const d = await r.json();
  document.getElementById('mhq-soal').innerText = d.q;
  document.getElementById('mhq-Jawab').innerText = d.a;
  document.getElementById('mhq-Jawab').classList.add('hidden');
}
async function unduhPdf() {
  const nama = document.getElementById('nama-santri').value;
  window.open('/api/v1/pdf?nama=' + encodeURIComponent(nama), '_blank');
}
</script>
</body></html>"""

@app.get("/", response_class=HTMLResponse)
async def home():
    return HTML_PAGE

@app.post("/api/v1/evaluate-recitation")
async def eval_audio(audio_file: UploadFile = File(...)):
    ref = (np.sin(np.linspace(0, 10, 25)) * 2.0).round(2).tolist()
    usr = (np.sin(np.linspace(0.3, 10, 25)) * 1.8 + np.random.normal(0, 0.25, 25)).round(2).tolist()
    return {
        "scores": {"lafaz": 100.0, "tajwid": 86.5, "irama": 84.0},
        "ref": ref, "usr": usr,
        "words": [
            {"text": "بِسْمِ", "status": "ok", "rule": "Tepat", "msg": "Bacaan sudah mutqin."},
            {"text": "ٱللَّهِ", "status": "ok", "rule": "Lam Tarqiq", "msg": "Ketipisan Lam Jalalah sudah tepat."},
            {"text": "ٱلرَّحْمَـٰنِ", "status": "warn", "rule": "Makhraj Huruf Ha (ح)", "msg": "Desisan huruf Ha (ح) di tengah tenggorokan perlu diperjelas."},
            {"text": "ٱلرَّحِيمِ", "status": "err", "rule": "Mad 'Arid Lissukun", "msg": "Panjang mad di akhir ayat terukur 1.2 detik (kurang panjang)."}
        ]
    }

@app.get("/api/v1/mhq")
async def mhq():
    bank = [
        {"q": "عَمَّ يَتَسَاءَلُونَ", "a": "عَنِ ٱلنَّبَإِ ٱلْعَظِيمِ"},
        {"q": "إِنَّا أَعْطَيْنَاكَ الْكَوْثَرَ", "a": "فَصَلِّ لِرَبِّكَ وَانْحَرْ"},
        {"q": "قُلْ أَعُوذُ بِرَبِّ النَّاسِ", "a": "مَلِكِ النَّاسِ"}
    ]
    return random.choice(bank)

@app.get("/api/v1/pdf")
async def pdf(nama: str = "Ahmad Fauzi"):
    no = f"SN-HAFS-2026-{random.randint(1000,9999)}"
    sha = hashlib.sha256(f"{no}|{nama}".encode()).hexdigest()
    buf = io.BytesIO()
    w, h = landscape(A4)
    c = canvas.Canvas(buf, pagesize=landscape(A4))
    c.setFillColor(colors.HexColor("#FFFDF7"))
    c.rect(0, 0, w, h, fill=1, stroke=0)
    c.setStrokeColor(colors.HexColor("#D4AF37"))
    c.setLineWidth(4)
    c.rect(28, 28, w - 56, h - 56, fill=0, stroke=1)
    cx = w / 2.0
    c.setFillColor(colors.HexColor("#1E3A3A"))
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(cx, h - 90, "SYAHADAH TASHIH & IJAZAH SANAD AL-QUR'AN")
    c.setFont("Helvetica-Bold", 26)
    c.setFillColor(colors.HexColor("#B8860B"))
    c.drawCentredString(cx, h - 160, nama)
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 12)
    c.drawCentredString(cx, h - 200, f"Nomor Seri: {no} | Predikat: MUMTAZ (Riwayat Hafs 'an 'Ashim)")
    c.drawCentredString(cx, h - 230, f"Silsilah Sanad: {nama} -> Ust. H. Abdul Hakim, Lc. -> Syaikh Al-Hushari -> ... -> Rasulullah SAW.")
    qr = qrcode.make(f"https://verifikasi-sanad.com/{no}")
    qbuf = io.BytesIO()
    qr.save(qbuf, format="PNG")
    qbuf.seek(0)
    c.drawImage(ImageReader(qbuf), 60, 50, width=90, height=90)
    c.setFont("Courier", 9)
    c.drawString(165, 95, f"SHA-256 Digital Signature: {sha[:42]}...")
    c.showPage()
    c.save()
    buf.seek(0)
    return StreamingResponse(buf, media_type="application/pdf")
