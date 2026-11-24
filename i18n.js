let L={},LANG="ru";
async function setLang(l){LANG=l;localStorage.setItem("lang",l);L=await (await fetch("/"+l+".json?v=10")).json()}
const t=k=>L[k]||k;
