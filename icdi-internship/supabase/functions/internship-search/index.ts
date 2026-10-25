// Supabase Edge Function: internship-search
// Keep BRAVE_SEARCH_API_KEY in Supabase secrets, never in this repository.
const origin = "https://thacha-icdi.github.io";
const cors = {
  "Access-Control-Allow-Origin": origin,
  "Access-Control-Allow-Headers": "authorization, apikey, content-type, x-client-info",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Vary": "Origin",
};
const reply = (data, status=200) => new Response(JSON.stringify(data), {
  status, headers: {...cors, "Content-Type":"application/json; charset=utf-8", "Cache-Control":"no-store"}
});
const clean = v => String(v||"").replace(/<[^>]*>/g," ").replace(/\s+/g," ").trim();
const normalize = v => clean(v).normalize("NFKC").toLowerCase();
const aliases = {
  "ba":"business analyst", "นักวิเคราะห์ธุรกิจ":"business analyst",
  "นักวิเคราะห์ข้อมูล":"data analyst", "โปรแกรมเมอร์":"programmer",
  "ออกแบบเว็บไซต์":"web designer", "การตลาด":"marketing",
};
export function filterResults(rows, keyword, province) {
  const q = normalize(keyword), role = aliases[q] || q;
  const tokens = role.split(/\s+/).filter(t=>!["intern","internship","ฝึกงาน"].includes(t));
  const place = normalize(province);
  const locations = place==="กรุงเทพมหานคร" ? ["กรุงเทพ","bangkok"] :
    place==="เชียงใหม่" ? ["เชียงใหม่","chiang mai"] : [place];
  const seen = new Set();
  return rows.flatMap(r=>{
    const title=clean(r.title), description=clean(r.description);
    const text=normalize([title, description, ...(r.extra_snippets||[])].join(" "));
    const titleText=normalize(title);
    // Require internship evidence in the result title, not merely the search query.
    if(!/\b(intern|internship|trainee)\b|ฝึกงาน|สหกิจ/.test(titleText))return [];
    if(!tokens.every(t=>titleText.includes(t)))return [];
    if(!/ประเทศไทย|thailand|bangkok|กรุงเทพ|เชียงใหม่|chiang mai/.test(text)&&!text.includes(place||"ประเทศไทย"))return [];
    if(place&&!locations.some(p=>text.includes(p)))return [];
    if(/หมดเขต|ปิดรับสมัคร|position filled|no longer accepting|job expired|closed position/i.test(text))return [];
    let url;try{url=new URL(r.url)}catch{return []}
    if(url.protocol!=="https:"||seen.has(url.href))return [];
    // Exclude search/category pages and listicles rather than present them as vacancies.
    if(/\/search(?:\/|$)|[?&](keyword|search|q)=|\/(?:tag|category)\//i.test(url.href))return [];
    if(/^\d+\s|top \d|jobs in |ตำแหน่งงานทั้งหมด/i.test(title))return [];
    seen.add(url.href);
    return [{title,company:url.hostname.replace(/^www\./,""),province:province||"ประเทศไทย — ตรวจสอบที่ประกาศ",
      url:url.href,description,source:url.hostname,checked_at:new Date().toISOString(),
      availability:"ต้องตรวจสอบวันปิดรับและช่วงฝึกงานกับบริษัท"}];
  });
}
const recent = new Map(); // Best-effort per-instance throttle; set provider spending limits too.
Deno.serve(async req=>{
  if(req.method==="OPTIONS")return new Response(null,{headers:cors});
  if(req.method!=="POST")return reply({error:"Method not allowed"},405);
  if(req.headers.get("origin") && req.headers.get("origin")!==origin)return reply({error:"Origin not allowed"},403);
  try {
    const authorization=req.headers.get("authorization")||"";
    if(!authorization.startsWith("Bearer "))return reply({error:"กรุณาเข้าสู่ระบบก่อนค้นหาประกาศสด"},401);
    const auth=await fetch(Deno.env.get("SUPABASE_URL")+"/auth/v1/user",{
      headers:{Authorization:authorization,apikey:Deno.env.get("SUPABASE_ANON_KEY")||""},
      signal:AbortSignal.timeout(8000)
    });
    if(!auth.ok)return reply({error:"กรุณาเข้าสู่ระบบใหม่"},401);
    const account=await auth.json();
    if(!account.id||!account.email_confirmed_at)return reply({error:"กรุณายืนยันอีเมลก่อนค้นหา"},403);
    const now=Date.now();
    for(const [id,until] of recent)if(until<now)recent.delete(id);
    if((recent.get(account.id)||0)>now)return reply({error:"กรุณารอ 10 วินาทีก่อนค้นหาครั้งต่อไป"},429);
    if(Number(req.headers.get("content-length")||0)>4096)return reply({error:"Request too large"},413);
    const body=await req.json();
    const keyword=clean(body.keyword),province=clean(body.province);
    if(!keyword||keyword.length>100||province.length>80)return reply({error:"กรอกตำแหน่งฝึกงานไม่เกิน 100 ตัวอักษร"},400);
    const key=Deno.env.get("BRAVE_SEARCH_API_KEY");
    if(!key)return reply({error:"ผู้ดูแลยังไม่ได้ตั้งค่า BRAVE_SEARCH_API_KEY"},503);
    recent.set(account.id,now+10000);
    const role=aliases[normalize(keyword)]||keyword;
    const query=[role.replace(/[^\p{L}\p{N}\s/+-]/gu," "),province,"Thailand (intern OR internship OR ฝึกงาน)"].join(" ");
    const url=new URL("https://api.search.brave.com/res/v1/web/search");
    url.search=new URLSearchParams({q:query,count:"20",country:"TH",extra_snippets:"true"}).toString();
    const response=await fetch(url,{headers:{"X-Subscription-Token":key,Accept:"application/json"},signal:AbortSignal.timeout(15000)});
    if(!response.ok)return reply({error:"บริการค้นหาขัดข้องหรือโควตาเต็ม กรุณาให้ผู้ดูแลตรวจสอบ"},502);
    const data=await response.json();
    const results=filterResults(data.web?.results||[],keyword,province);
    return reply({results, searched_at:new Date().toISOString(),
      note:"ผลจากดัชนีค้นหา กรองจากชื่อและข้อความประกาศ ไม่ยืนยันว่าบริษัทยังรับสมัครหรือรับในช่วงวันที่เลือก"});
  } catch {
    return reply({error:"ค้นหาไม่สำเร็จ กรุณาลองใหม่"},502);
  }
});
