# เปิดระบบค้นหาฝึกงานจากเว็บจริง

สถานะ: เตรียมโค้ดและเชื่อมหน้าเว็บแล้ว ยังไม่ได้ deploy เข้า Supabase และยังไม่ได้ทดสอบด้วย Search API จริง

## 1. ขอ Search API key
เปิด https://api-dashboard.search.brave.com/
สมัครบัญชี เลือกบริการ Web Search ตรวจสอบราคาและโควตาก่อนเปิดบริการ
สร้าง API key อย่านำ key ไปใส่ GitHub หรือ HTML

## 2. ตั้งค่า Supabase secret
เปิด https://supabase.com/dashboard/project/eqfblcwcwsvfbjipehke/functions
ไป Secrets เพิ่มชื่อ BRAVE_SEARCH_API_KEY และใส่ key จากขั้นตอน 1

## 3. Deploy function
ใน Edge Functions เลือก Deploy a new function > Via Editor
ตั้งชื่อ internship-search
แทนโค้ดทั้งหมดด้วยไฟล์ supabase/functions/internship-search/index.ts ในโฟลเดอร์นี้
กด Deploy function คงการตรวจ JWT ไว้ เพราะระบบต้องเข้าสู่ระบบด้วย Supabase Auth
ไม่ต้องใช้ service_role key

## 4. ทดสอบ
เปิด https://thacha-icdi.github.io/academic-website/icdi-internship/?v=21
Login ด้วยบัญชีที่ยืนยันอีเมลแล้ว
ไปค้นหาฝึกงาน กรอกตำแหน่งและจังหวัด กดค้นหาประกาศฝึกงานจริง
หากขึ้นข้อความยังไม่พร้อม ให้ตรวจชื่อ function, secret, logs และโควตาบริการ
ทดสอบหลายตำแหน่ง รวมคำค้นที่ไม่มีผล เปลี่ยนตัวกรองระหว่างรอ และ Clear
ทดสอบเลือกประกาศแล้วส่งรายงานด้วยบัญชีนักศึกษา
การส่งรายงานยังต้องใช้ migration 005-letter-requests.sql ที่มีอยู่เดิม

## ขอบเขต
- รับคำค้นอิสระ ไม่ได้จำกัดเฉพาะตัวอย่าง
- ผลมาจากดัชนี Brave Search สูงสุด 20 ผลต่อคำค้น ก่อนกรอง
- ตรวจหลักฐาน internship และคำตำแหน่งในชื่อผลค้นหา จังหวัดในข้อความ พร้อมตัดผลที่ระบุปิดรับ
- ไม่รับประกันความครบถ้วน ความถูกต้องของข้อความจากดัชนี หรือสถานะรับสมัครปัจจุบัน ต้องตรวจประกาศต้นทาง
- ไม่ได้เปิดตรวจเนื้อหาทุกหน้าหรือยืนยันวันเริ่ม–สิ้นสุดฝึกงาน
- คำจังหวัดภาษาอังกฤษรองรับ Bangkok และ Chiang Mai โดยตรง จังหวัดอื่นอาจตกหล่นหากประกาศใช้ภาษาอังกฤษ
- throttle 10 วินาทีต่อบัญชีเป็นแบบต่อ instance ไม่ใช่ global rate limit
- ตั้งเพดานงบ/โควตาที่ผู้ให้บริการ ก่อนเปิดให้นักศึกษาใช้งานวงกว้าง
- คำค้นและจังหวัดส่งไป Brave Search ไม่ส่งประวัตินักศึกษาหรือข้อมูลขอจดหมาย
