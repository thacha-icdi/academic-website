# ICDI Career Hub

เว็บไซต์หางานในประเทศไทยสำหรับนักศึกษาและศิษย์เก่า International College of Digital Innovation, Chiang Mai University

**เว็บไซต์:** https://thacha-icdi.github.io/academic-website/icdi-career/

Created by Assoc. Prof. Dr. Thacha Lawanna

## สถานะการเปิดใช้งาน

หน้าเว็บและตัวสร้างเรซูเม่เปิดดูได้ทันทีบน GitHub Pages ระบบสมาชิก การบันทึกเข้าบัญชี หลักฐาน และการอัปโหลด **จะเปิดเมื่อผู้ดูแลติดตั้ง schema.sql และใส่ค่าของ Supabase ใน config.js แล้วเท่านั้น** ไม่มีการจำลองว่าบันทึกสำเร็จ และไม่มีรหัสผ่าน Admin เริ่มต้น

การดึงงาน: GitHub Actions อ่าน Public Posting API ของ SmartRecruiters แล้วบันทึกข้อมูลสาธารณะใน data/jobs.json ทุกวันประมาณ 07:17 น. เวลาไทย (อาจล่าช้าตามคิวของ GitHub) และเมื่อแก้สคริปต์หรือสั่ง Run workflow ผู้ใช้กด “อัปเดตจากบริษัท” เพื่อดึงตรงจาก API ได้ด้วย หากแหล่งข้อมูลไม่พร้อมหรือ CORS ไม่อนุญาต ระบบใช้ snapshot ล่าสุดและแสดงสถานะแหล่งข้อมูล งานไม่รับประกันว่ายังเปิดรับจนกว่าจะตรวจที่ต้นทาง

## ผู้ใช้และสิทธิ์

| บทบาท | สิทธิ์ |
| --- | --- |
| นักศึกษา | สมัคร ยืนยันอีเมล ส่งหลักฐานสถานภาพ ICDI และเมื่ออนุมัติแล้วบันทึก/แก้ไขเรซูเม่ อัปโหลดผลงาน บันทึกงาน |
| ศิษย์เก่า | เช่นเดียวกับนักศึกษา พร้อมระบุปีสำเร็จการศึกษาและส่งหลักฐาน |
| Manager | ตรวจหลักฐาน อนุมัติ/ขอหลักฐานใหม่ เพิ่ม/แก้ไข/ปิด/ลบประกาศงานที่ ICDI ตรวจสอบ |
| Admin | สิทธิ์ Manager พร้อมแต่งตั้ง/ถอนสิทธิ์เจ้าหน้าที่ ระงับ/เปิดบัญชี และอ่าน Audit log |

ผู้สมัครเลือก Manager หรือ Admin ไม่ได้ การอนุมัติสมาชิกและเปลี่ยนสิทธิ์ตรวจที่ฐานข้อมูล เจ้าหน้าที่อนุมัติหลักฐานตนเองไม่ได้ Admin เปลี่ยนสิทธิ์หรือระงับบัญชีตนเองไม่ได้

เรซูเม่ พอร์ตโฟลิโอ และงานที่บันทึกอ่านได้เฉพาะเจ้าของ แม้ Manager ก็ไม่ได้สิทธิ์อ่านเรซูเม่ของคนอื่น หลักฐานอ่านได้เฉพาะเจ้าของและเจ้าหน้าที่ ไม่เปิด bucket เป็นสาธารณะ

## เปิดระบบสมาชิก: ทำครั้งเดียว

1. สร้างโปรเจกต์ของอาจารย์ที่ https://supabase.com/dashboard เลือกพื้นที่จัดเก็บที่เหมาะกับนโยบายของหน่วยงาน
2. เปิด **SQL Editor → New query** วางเนื้อหาจาก [schema.sql](schema.sql) ทั้งหมด แล้ว Run หนึ่งครั้ง สคริปต์สร้างตาราง, RLS, ฟังก์ชันสิทธิ์ และ private storage buckets
3. ไปที่ **Authentication → URL Configuration** ตั้ง Site URL และ Redirect URLs เป็น `https://thacha-icdi.github.io/academic-website/icdi-career/` พร้อมอนุญาต URL เดียวกันที่ลงท้าย `#account` สำหรับการยืนยันอีเมล/กู้รหัสผ่าน
4. เปิด Email provider และการยืนยันอีเมล ตั้งขั้นต่ำรหัสผ่านอย่างน้อย 12 ตัวอักษร หากเปิดรับนักศึกษาจำนวนมากให้ตั้ง SMTP ของหน่วยงานตามข้อจำกัดของผู้ให้บริการ แนะนำเปิด CAPTCHA ใน Supabase ก่อนรับสมัครสาธารณะ (ต้องเพิ่ม widget ให้ตรงกับการตั้งค่าด้วย)
5. คัดลอก **Project URL** และ **publishable key หรือ legacy anon key** จาก Settings / API แล้วแก้ [config.js](config.js):

```javascript
window.CAREER_CONFIG = {
  supabaseUrl: 'https://YOUR_PROJECT.supabase.co',
  supabaseAnonKey: 'YOUR_PUBLISHABLE_OR_ANON_KEY'
};
```

**ใช้เฉพาะ publishable/anon key เท่านั้น ห้ามใส่ service_role, secret key หรือ database password ใน GitHub** Public key ใช้กับ RLS เพื่อจำกัดข้อมูลของแต่ละบัญชี

6. เปิดเว็บ สมัครบัญชีของอาจารย์ และยืนยันอีเมล จากนั้นตั้ง Admin คนแรกผ่าน SQL Editor โดยเปลี่ยนอีเมลให้ตรงกับบัญชีที่ยืนยันแล้ว:

```sql
insert into public.career_staff(user_id, role)
select id, 'admin' from auth.users
where email = 'YOUR_CONFIRMED_ADMIN_EMAIL'
  and email_confirmed_at is not null
on conflict (user_id) do update set role = 'admin';
```

7. ออกจากระบบและเข้าใหม่ จะเห็นเมนู **จัดการระบบ** เลือกบัญชีที่สมัครแล้วเพื่อแต่งตั้ง Manager ได้

## การทดสอบก่อนเปิดรับนักศึกษา

- ใช้บัญชีทดสอบสองบัญชี ตรวจว่าบัญชี A อ่าน/แก้เรซูเม่และไฟล์ของ B ไม่ได้ แม้เรียก REST API โดยตรง
- บัญชีรอตรวจสอบต้องบันทึกเรซูเม่และอัปโหลด portfolio ไม่ได้ หลัง Manager อนุมัติจึงทำได้
- นักศึกษาเรียก RPC แต่งตั้ง Admin หรืออนุมัติสมาชิกเองต้องถูกปฏิเสธ
- ตรวจส่งหลักฐาน, ขอหลักฐานใหม่, ส่งซ้ำ, อนุมัติ และดู Audit log
- ตรวจสมัคร/ยืนยันอีเมล, เข้าสู่ระบบ, ออกจากระบบ, กู้รหัสผ่าน และโหลดเรซูเม่เดิมหลังเข้าใหม่
- ตรวจอัปโหลด PDF / JPG / PNG ขนาดไม่เกิน 10 MB, เปิดลิงก์ชั่วคราวและลบผลงาน
- ตรวจนโยบายข้อมูลส่วนบุคคล ระยะเก็บหลักฐาน และช่องทางติดต่อของหน่วยงานก่อนรับข้อมูลจริง

สคริปต์ทดสอบการจัดกลุ่มงานและระดับประสบการณ์:

```bash
node --check icdi-career/app.js
python -m unittest discover -s icdi-career/scripts -p 'test_*.py'
```

ไม่สามารถยืนยันการทดสอบ Auth/SQL/Storage จริงได้จนกว่าจะมีโปรเจกต์ Supabase ที่ติดตั้ง schema แล้ว

## ข้อมูลประกาศงาน

- แหล่งดึงอัตโนมัติ: Bosch Group, Western Digital, Minor International, Dentsu และ Accor ผ่าน Public Posting API และ Agoda ผ่าน Greenhouse Job Board API เท่าที่บริษัทนั้นเผยแพร่ในระบบ
- กรอง `location.country == th` ทั้งฝั่งดึงข้อมูลและแสดงผล; ใช้คำสำคัญจับคู่ 30 กลุ่มตำแหน่ง ไม่รับประกันว่าทุกกลุ่มมีงานในทุกวัน
- งานที่ระบุ Senior/Manager/Lead ไม่ติดป้ายเป็นงานเริ่มต้น งานที่ไม่ได้ระบุระดับแสดงให้ตรวจคุณสมบัติที่ต้นทาง
- หน้าแสดงงานมีชื่อบริษัท เมือง แหล่งที่มา เวลาตรวจ และลิงก์ประกาศจริง การสมัครเกิดที่เว็บนายจ้าง ระบบไม่ส่งเรซูเม่อัตโนมัติ
- JobsDB / JobThai / JobBKK / LinkedIn / Indeed เป็น **ลิงก์ค้นหาภายนอก** ไม่อ้างว่าดึงข้อมูลของบริการเหล่านี้มาแล้ว ไม่ใช้การข้าม login หรือมาตรการจำกัดการเข้าถึง
- Manager เพิ่ม/แก้ไขประกาศของบริษัทในไทยที่ตรวจสอบแล้วได้ผ่านหน้าเว็บหลังเชื่อมฐานข้อมูล
- สามารถเพิ่มบริษัทอื่นที่มี public API ใน `COMPANIES` ของ app.js และ scripts/refresh_jobs.py ได้

เอกสาร API: https://developers.smartrecruiters.com/docs/posting-api
เอกสาร RLS: https://supabase.com/docs/guides/database/postgres/row-level-security

## การลบข้อมูลและบัญชี

ผู้ใช้ลบผลงานและไฟล์ผ่านหน้าเว็บได้ หากขอลบบัญชีทั้งหมด Admin ต้องยืนยันคำขอจากเจ้าของก่อน แล้วลบไฟล์ใน private buckets ของ user ID นั้นผ่าน Supabase Dashboard ตามด้วยลบบัญชีใน Authentication ตารางที่เกี่ยวข้องลบตาม foreign key; Audit log เก็บรายการโดยเปลี่ยน actor/target เป็น null เมื่อบัญชีถูกลบ อย่าใช้ service-role key ในเบราว์เซอร์

## โครงสร้างไฟล์

- index.html / style.css / app.js — เว็บ responsive ไม่ต้อง build
- config.js — ค่าสาธารณะสำหรับ Supabase
- schema.sql — ตาราง, RLS, RPC และ private storage
- data/roles.json — 30 กลุ่มงานและคำสำคัญ ไทย–อังกฤษ
- data/jobs.json — snapshot ประกาศงานสาธารณะ ไม่มีข้อมูลนักศึกษา
- scripts/refresh_jobs.py — ดึงงานในไทยและเก็บ snapshot
- .github/workflows/icdi-career-jobs.yml — workflow อยู่ที่ root ของ repository

ไม่เก็บเรซูเม่ รหัสผ่าน หลักฐาน หรือไฟล์ส่วนตัวของนักศึกษาใน GitHub

ค่าเริ่มต้นซ่อนงานฝึกงานและระดับอาวุโส ผู้ใช้เลือกให้รวมได้จากตัวกรอง ระบบระบุระดับจากชื่อตำแหน่งและ metadata ที่มี จึงต้องตรวจคุณสมบัติที่ต้นทางเสมอ
