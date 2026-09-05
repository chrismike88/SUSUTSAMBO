import { chromium } from "playwright";
const S=process.env.SCR;
const b=await chromium.launch({executablePath:"/opt/pw-browsers/chromium"});
const ctx=await b.newContext({viewport:{width:1340,height:1000}});
const p=await ctx.newPage();
const err=[]; p.on("pageerror",e=>err.push(e.message));
p.on("console",m=>{if(m.type()==="error")err.push(m.text())});
await p.goto("file://"+S+"/susutsambo.html",{waitUntil:"networkidle"});
await p.waitForTimeout(1200);
await p.screenshot({path:S+"/shots/art-ringkas.png",fullPage:true});
for (const t of ["teknis","simulasi"]) {
  await p.click(`button[data-t="${t}"]`); await p.waitForTimeout(500);
  await p.screenshot({path:`${S}/shots/art-${t}.png`,fullPage:true});
}
const ow=await p.evaluate(()=>document.documentElement.scrollWidth-document.documentElement.clientWidth);
console.log("overflow-x:",ow,"| galat:",err.length?err:"tidak ada");
await b.close();
