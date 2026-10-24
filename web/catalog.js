"use strict";
(() => {
  const REPO_URL="https://lg.darc.dev/";
  const ROOT_ICON="/assets/app-fallback.png";
  const $=(q,root=document)=>root.querySelector(q);
  const state={tab:"homebrew", category:"All",query:"",sort:"featured",visible:24, homebrew:[], dstore:[],loading:true};
  const labels={All:"Wszystkie",Video:"Filmy i wideo",IPTV:"IPTV",Games:"Gry",Utilities:"Narzędzia",Music:"Muzyka",Personalization:"Personalizacja",Education:"Edukacja",External:"Inne",Other:"Pozostałe"};
  let toastTimer=0;

  function text(node,value){node.textContent=value==null?"":String(value);return node;}
  function el(tag,cls,value) {
    const node=document.createElement(tag);
    if(cls) node.className=cls;
    if(value!=null) text(node,value);
    return node;
  }
  function safeUrl(value,fallback) {
    try { const u=new URL(value,location.origin); return ["https:","http:"].includes(u.protocol)?u.href:fallback; }
    catch { return fallback; }
  }
  function showToast(message) {
    const t=$("#toast");t.textContent=message;t.classList.add("visible");
    clearTimeout(toastTimer);toastTimer=setTimeout(()=>t.classList.remove("visible"),2700);
  }
  async function copyRepo() {
    try {
      if(navigator.clipboard&&navigator.clipboard.writeText) await navigator.clipboard.writeText(REPO_URL);
      else {
        const input=document.createElement("textarea");input.value=REPO_URL;input.style.position="fixed";input.style.opacity="0";
        document.body.append(input);input.select();const ok=document.execCommand("copy");input.remove();
        if(!ok)throw Error("copy blocked");
      }
      showToast("Skopiowano adres repozytorium");
    } catch { showToast("Adres repozytorium: "+REPO_URL); }
  }
  function dateValue(value) {
    const m=String(value||"").match(/^(\d{1,2})\.(\d{1,2})\.(\d{2,4})$/);
    if(!m)return 0;
    const year=Number(m[3])<100?2000+Number(m[3]):Number(m[3]);
    return year*10000+Number(m[2])*100+Number(m[1]);
  }
  function prettyCategory(cat){return labels[cat]||cat||"Pozostałe";}
  function homebrewMapping(packageList,dstoreRows) {
    const dstoreIds=new Map(dstoreRows.filter(r=>r.verified&&r.id).map(r=>[r.id,r]));
    return packageList.map((item,i)=>{
      const m=item.manifest||{},src=dstoreIds.get(item.id);
      const isDStore=Boolean(src)||String(m.ipkUrl||"").includes("/source/ipk/");
      return {id:item.id,title:item.title||m.title||item.id,iconUri:item.iconUri||m.iconUri,
        description:!isDStore?(item.shortDescription||m.appDescription||"Aplikacja dla LG webOS"):
          "Pakiet z katalogu DStore. Format IPK i suma SHA-256 sprawdzone, ale aplikacja nie przeszła audytu bezpieczeństwa.",
        originalDescription:src?src.description:null,
        category:src?src.category:(/(vod|boring|video|tv)/i.test(item.title||"")?"Video":"Other"),
        source:isDStore?"DStore":"DC4I",verified:true,rootRequired:!!m.rootRequired,
        ipkUrl:m.ipkUrl||"",sourceUrl:m.sourceUrl||"",version:m.version||"",sha256:m.ipkHash&&m.ipkHash.sha256||"",
        size:m.ipkSize||0,date:src?src.date:"24.10.2026",index:i};
    });
  }
  function dstoreMapping(dstoreRows,packages) {
    const byId=new Map(packages.map(p=>[p.id,p]));
    return dstoreRows.map((r,i)=>{
      const pkg=r.id?byId.get(r.id):null,m=pkg&&pkg.manifest||{};
      return {id:r.id||"",filename:r.filename,title:r.title||r.filename,iconUri:r.iconUri||ROOT_ICON,
        description:r.description||"Aplikacja z katalogu DStore.",category:r.category||"External",
        source:"DStore",verified:!!pkg&&!!r.verified,rootRequired:!!m.rootRequired,
        ipkUrl:pkg?m.ipkUrl:r.sourceUrl,sourceUrl:r.sourceUrl,version:m.version||"",sha256:m.ipkHash&&m.ipkHash.sha256||"",
        size:m.ipkSize||0,date:r.date||"",index:i};
    });
  }
  function chooseCategory(value) {
    state.category=value;state.visible=24;
    document.querySelectorAll("#filters .filter").forEach(b=>{
      const yes=b.dataset.category===value;b.classList.toggle("active",yes);b.setAttribute("aria-pressed",String(yes));
    });
    render();
  }
  function updateFilters() {
    const list=state.tab==="homebrew"?state.homebrew:state.dstore;
    const counts={All:list.length};
    for(const app of list)counts[app.category]=(counts[app.category]||0)+1;
    if(!counts[state.category])state.category="All";
    const holder=$("#filters");holder.replaceChildren();
    const order=["All","Video","IPTV","Games","Utilities","Music","Personalization","Education","Other","External"];
    const categories=Object.keys(counts).sort((a,b)=>{
      const ai=order.indexOf(a),bi=order.indexOf(b);
      return (ai===-1?99:ai)-(bi===-1?99:bi);
    });
    for(const cat of categories){
      const b=el("button","filter"+(cat===state.category?" active":""),prettyCategory(cat)+" "+counts[cat]);
      b.type="button";b.dataset.category=cat;b.setAttribute("aria-pressed",String(cat===state.category));
      b.addEventListener("click",()=>chooseCategory(cat));holder.append(b);
    }
  }
  function chooseTab(value) {
    state.tab=value;state.category="All";state.visible=24;
    for(const button of document.querySelectorAll(".tab")){
      const selected=button.dataset.tab===value;button.classList.toggle("active",selected);button.setAttribute("aria-selected",String(selected));
    }
    $("#source-note").textContent=value==="homebrew"?"Gotowe do dodania przez Homebrew Channel":"Dodatkowe pliki wymagają samodzielnej weryfikacji";
    updateFilters();render();
  }
  function card(app) {
    const article=el("article","app-card");
    const head=el("div","card-head");
    const img=el("img","app-icon"+(app.verified?"":" dstore-generic"));
    img.src=safeUrl(app.iconUri,ROOT_ICON);img.alt="";img.loading="lazy";img.onerror=()=>{img.onerror=null;img.src=ROOT_ICON;};
    const label=el("div","card-label");
    const title=el("strong","",app.title);title.title=app.title;
    const sub=el("small","",app.source==="DC4I"?"DC4I Labs":prettyCategory(app.category));
    label.append(title,sub);head.append(img,label);article.append(head);
    const desc=el("p","card-desc",app.description);article.append(desc);
    const badges=el("div","card-badges");
    badges.append(el("span","chip"+(app.verified?" good":" warning"),app.verified?"Sprawdzony IPK":"Zewnętrzny"));
    if(app.version)badges.append(el("span","chip","v"+app.version));
    if(app.rootRequired)badges.append(el("span","chip warning","ROOT"));
    article.append(badges);
    const actions=el("div","card-actions");
    const a=el("a","card-action",app.verified?"Pobierz IPK ↗":"Otwórz źródło ↗");
    a.href=safeUrl(app.ipkUrl,"#");a.target="_blank";a.rel="noopener noreferrer";a.title=app.verified?"Pobierz pakiet IPK":"Otwórz oryginalny plik w DStore";
    a.addEventListener("click",event=>{if(a.href.endsWith("#")){event.preventDefault();showToast("Brak dostępnego linku");}});
    actions.append(a);
    const details=el("button","card-action muted","ⓘ");details.type="button";details.title="Szczegóły pakietu";
    details.setAttribute("aria-label","Szczegóły: "+app.title);details.addEventListener("click",()=>showDetails(app));
    actions.append(details);article.append(actions);
    return article;
  }
  function pair(dl,name,value) {
    if(value==null||value==="")return;
    dl.append(el("dt","",name),el("dd","",value));
  }
  function showDetails(app) {
    const box=$("#details"),content=$("#details-content");content.replaceChildren();
    const head=el("div","detail-heading");
    const img=el("img");img.src=safeUrl(app.iconUri,ROOT_ICON);img.alt="";
    img.onerror=()=>{img.onerror=null;img.src=ROOT_ICON;};
    const header=el("div");header.append(el("h2","",app.title),el("span","chip "+(app.verified?"good":"warning"),app.verified?"IPK: format i SHA-256 sprawdzone":"Plik niezweryfikowany"));
    head.append(img,header);content.append(head);
    content.append(el("p","",app.description));
    if(app.originalDescription)content.append(el("p","", "Opis źródłowy DStore: "+app.originalDescription));
    const dl=el("dl");pair(dl,"Źródło",app.source);pair(dl,"Kategoria",prettyCategory(app.category));
    pair(dl,"ID aplikacji",app.id);pair(dl,"Wersja",app.version);pair(dl,"Plik",app.filename);
    pair(dl,"Data z listy",app.date);pair(dl,"Wymaga roota",app.rootRequired?"Tak":"Nie podano / nie wykryto");
    pair(dl,"Rozmiar",app.size?(app.size/1024/1024).toFixed(2)+" MB":"");
    pair(dl,"SHA-256",app.sha256);content.append(dl);
    const btns=el("div","detail-buttons");
    const open=el("a","btn primary",app.verified?"Pobierz IPK ↗":"Otwórz źródłowy pakiet ↗");
    open.href=safeUrl(app.ipkUrl,REPO_URL);open.target="_blank";open.rel="noopener noreferrer";btns.append(open);
    if(app.verified){
      const repobtn=el("button","btn secondary","Kopiuj repo TV");repobtn.type="button";repobtn.addEventListener("click",copyRepo);btns.append(repobtn);
    }
    content.append(btns);
    if(typeof box.showModal==="function")box.showModal();else box.setAttribute("open","");
  }
  function render() {
    if(state.loading)return;
    const list=state.tab==="homebrew"?state.homebrew:state.dstore;
    const query=state.query.toLocaleLowerCase("pl");
    const filtered=list.filter(app=>{
      if(state.category!=="All"&&app.category!==state.category)return false;
      if(!query)return true;
      return [app.title,app.id,app.filename,app.description,app.originalDescription,app.category].some(v=>String(v||"").toLocaleLowerCase("pl").includes(query));
    }).sort((a,b)=>{
      if(state.sort==="name")return a.title.localeCompare(b.title,"pl");
      if(state.sort==="newest")return dateValue(b.date)-dateValue(a.date)||a.title.localeCompare(b.title,"pl");
      if(a.source!==b.source&&state.tab==="homebrew")return a.source==="DC4I"?-1:1;
      if(a.verified!==b.verified)return Number(b.verified)-Number(a.verified);
      return a.title.localeCompare(b.title,"pl");
    });
    const container=$("#cards");
    const frag=document.createDocumentFragment();
    for(const app of filtered.slice(0,state.visible))frag.append(card(app));
    container.replaceChildren(frag);
    const number=filtered.length;
    $("#section-count").textContent=String(number);
    $("#result-text").textContent="Znaleziono "+number+" "+(number===1?"aplikację":"aplikacji")+". "+(state.tab==="dstore"?"Pozycje bez zielonej etykiety pochodzą z niezweryfikowanego źródła.":"");
    $("#empty").hidden=number!==0;
    const more=$("#show-more");more.hidden=number<=state.visible;
    if(!more.hidden)more.textContent="Pokaż kolejne "+Math.min(24,number-state.visible)+" ↓";
  }
  async function load() {
    try {
      const responses=await Promise.all([fetch("/api/apps.json",{cache:"no-store"}),fetch("/catalog/dstore.json",{cache:"no-store"})]);
      if(responses.some(r=>!r.ok))throw Error("HTTP "+responses.map(r=>r.status).join(","));
      const [catalog,dstore]=await Promise.all(responses.map(r=>r.json()));
      if(!Array.isArray(catalog.packages)||!Array.isArray(dstore.entries))throw Error("Nieprawidłowe dane katalogu");
      state.homebrew=homebrewMapping(catalog.packages,dstore.entries);
      state.dstore=dstoreMapping(dstore.entries,catalog.packages);
      $("#stat-homebrew").textContent=state.homebrew.length;
      $("#stat-dstore").textContent=state.dstore.length;
      $("#stat-verified").textContent=state.dstore.filter(r=>r.verified).length;
      $("#tab-homebrew-count").textContent=state.homebrew.length;
      $("#tab-dstore-count").textContent=state.dstore.length;
      state.loading=false;updateFilters();render();
      const target=new URL(location.href).searchParams.get("q");
      if(target){$("#search").value=target;state.query=target;render();}
    } catch(error) {
      state.loading=false;$("#result-text").textContent="Nie udało się wczytać katalogu. Spróbuj odświeżyć stronę.";
      $("#source-note").textContent=String(error.message||error);
      console.error("DC4I webOS catalogue:",error);
    }
  }
  document.querySelectorAll(".js-copy").forEach(button=>button.addEventListener("click",copyRepo));
  document.querySelectorAll(".tab").forEach(button=>button.addEventListener("click",()=>chooseTab(button.dataset.tab)));
  $("#search").addEventListener("input",e=>{state.query=e.target.value.trim();state.visible=24;render();});
  $("#sort").addEventListener("change",e=>{state.sort=e.target.value;render();});
  $("#show-more").addEventListener("click",()=>{state.visible+=24;render();});
  document.addEventListener("keydown",event=>{
    if(event.key==="/"&&!/input|textarea/i.test(document.activeElement.tagName)){event.preventDefault();$("#search").focus();}
  });
  load();
})();
