const input = document.querySelector("#textInput");
const convertBtn = document.querySelector("#convertBtn");
const clearBtn = document.querySelector("#clearBtn");
const fullOutput = document.querySelector("#fullPinyin");
const splitOutput = document.querySelector("#splitPinyin");
const copyFullBtn = document.querySelector("#copyFullBtn");
const copySplitBtn = document.querySelector("#copySplitBtn");
const message = document.querySelector("#message");
const counter = document.querySelector("#counter");
const definitionDialog = document.querySelector("#definitionDialog");
const definitionTitle = document.querySelector("#definitionTitle");
const definitionContent = document.querySelector("#definitionContent");
const closeDefinitionBtn = document.querySelector("#closeDefinitionBtn");
const currentTime = document.querySelector("#currentTime");
let currentResult = [];
const definitionCache = new Map();

input.addEventListener("input", () => counter.textContent = `${input.value.length} / 5000`);
input.addEventListener("keydown", event => { if ((event.ctrlKey || event.metaKey) && event.key === "Enter") convert(); });
convertBtn.addEventListener("click", convert);
clearBtn.addEventListener("click", clearAll);
copyFullBtn.addEventListener("click", () => copyText(currentResult.map(item => item.pinyin).join(" "), copyFullBtn));
copySplitBtn.addEventListener("click", () => copyText(currentResult.map(item => `${item.char}\t${item.pinyin}`).join("\n"), copySplitBtn));
closeDefinitionBtn.addEventListener("click", () => definitionDialog.close());
definitionDialog.addEventListener("click", event => {
  if (event.target === definitionDialog) definitionDialog.close();
});

function updateCurrentTime() {
  const now=new Date();
  currentTime.dateTime=now.toISOString();
  currentTime.textContent=new Intl.DateTimeFormat("zh-CN", {
    year:"numeric",month:"2-digit",day:"2-digit",
    hour:"2-digit",minute:"2-digit",second:"2-digit",
    hour12:false
  }).format(now);
}

updateCurrentTime();
setInterval(updateCurrentTime,1000);

async function convert() {
  if (!input.value.trim()) return showMessage("请先输入汉字。", true);
  setLoading(true); showMessage("正在转换…");
  try {
    const response = await fetch("/pinyin", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({text:input.value})});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "转换失败，请稍后重试。");
    renderResult(data.result);
    const isSingleHanzi=/^[\u3400-\u9fff\uf900-\ufaff]$/.test(input.value);
    if (isSingleHanzi && data.result.length > 1) {
      showMessage(`该字为多音字，找到 ${data.result.length} 个读音`);
    } else {
      showMessage(`转换完成，共 ${data.result.length} 个字符。`);
    }
  } catch (error) { showMessage(error.message || "无法连接后端服务。", true); }
  finally { setLoading(false); }
}

function renderResult(result) {
  currentResult = result;
  fullOutput.textContent = result.map(item => item.pinyin).join(" "); fullOutput.classList.remove("placeholder");
  splitOutput.replaceChildren(); splitOutput.classList.remove("empty-state");
  result.forEach(item => {
    const row=document.createElement("div"); row.className="char-row";
    const char=document.createElement("span"); char.className="char"; char.textContent=item.char === " " ? "␠" : item.char;
    const py=document.createElement("span"); py.className="pinyin"; py.textContent=item.pinyin === " " ? "空格" : item.pinyin;
    const copyGroup=document.createElement("div"); copyGroup.className="row-copy-group";
    const formats=[
      {label:"字(音)", value:`${item.char}(${item.pinyin})`},
      {label:"拼音", value:item.pinyin},
      {label:"字+音", value:`${item.char}${item.pinyin}`}
    ];
    formats.forEach(format => {
      const button=document.createElement("button");
      button.className="row-copy"; button.type="button"; button.textContent=format.label;
      button.title=`即将复制：${format.value}`;
      button.setAttribute("aria-label",`复制 ${format.value}`);
      button.addEventListener("click",()=>copyText(format.value,button));
      copyGroup.appendChild(button);
    });
    if (/^[\u3400-\u9fff\uf900-\ufaff]$/.test(item.char)) {
      const definitionButton=document.createElement("button");
      definitionButton.className="row-copy definition-button";
      definitionButton.type="button";
      definitionButton.textContent="释义";
      definitionButton.title=`查看 ${item.char}（${item.pinyin}）的释义`;
      definitionButton.addEventListener("click",()=>showDefinition(item,definitionButton));
      copyGroup.appendChild(definitionButton);
    }
    row.append(char,py,copyGroup); splitOutput.appendChild(row);
  });
  copyFullBtn.disabled=copySplitBtn.disabled=result.length === 0;
}

function normalizePinyin(value) {
  return value.toLowerCase().replace(/[\s()[\]（）]/g, "");
}

function selectDefinition(definitions, pinyin) {
  const target=normalizePinyin(pinyin);
  return Object.entries(definitions).filter(([key]) => normalizePinyin(key).includes(target));
}

function selectLayout(layouts, pinyin) {
  const target=normalizePinyin(pinyin);
  const matched=Object.entries(layouts || {}).filter(([key]) => normalizePinyin(key).includes(target));
  return matched.map(([,value]) => value).join("");
}

async function showDefinition(item, button) {
  definitionTitle.textContent=`${item.char}（${item.pinyin}）释义`;
  definitionContent.textContent="正在获取释义…";
  if (!definitionDialog.open) definitionDialog.showModal();
  button.disabled=true;
  try {
    let definitionData=definitionCache.get(item.char);
    if (!definitionData) {
      const response=await fetch("/definition", {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({text:item.char})});
      const data=await response.json();
      if (!response.ok) throw new Error(data.error || "获取释义失败。");
      definitionData={definitions:data.definitions,layouts:data.layouts || {}};
      definitionCache.set(item.char,definitionData);
    }
    definitionContent.replaceChildren();
    const layout=selectLayout(definitionData.layouts,item.pinyin);
    if (layout) {
      definitionContent.innerHTML=layout;
    } else {
      const matchedDefinitions=selectDefinition(definitionData.definitions,item.pinyin);
      if (!matchedDefinitions.length) {
        definitionContent.textContent="未找到该读音释义";
        return;
      }
      matchedDefinitions.forEach(([reading,value]) => {
        const block=document.createElement("section"); block.className="definition-item";
        const heading=document.createElement("h3"); heading.textContent=reading;
        const body=document.createElement("div"); body.className="definition-text"; body.textContent=value;
        block.append(heading,body); definitionContent.appendChild(block);
      });
    }
  } catch (error) {
    definitionContent.textContent=error.message || "暂时无法获取释义，请稍后重试。";
  } finally { button.disabled=false; }
}

async function copyText(text, button) { try { await navigator.clipboard.writeText(text); flash(button); } catch { showMessage("复制失败，请检查剪贴板权限。",true); } }
function flash(button) { const old=button.textContent; button.textContent="已复制"; setTimeout(()=>button.textContent=old,1200); }
function showMessage(text,isError=false) { message.textContent=text; message.classList.toggle("error",isError); }
function setLoading(value) { convertBtn.disabled=value; convertBtn.textContent=value ? "转换中…" : "转换拼音"; }
function clearAll() { input.value=""; currentResult=[]; counter.textContent="0 / 5000"; fullOutput.textContent="转换结果会显示在这里"; fullOutput.classList.add("placeholder"); splitOutput.textContent="每个字符均提供“字(音)”“拼音”“字+音”三种复制格式。"; splitOutput.classList.add("empty-state"); copyFullBtn.disabled=copySplitBtn.disabled=true; if(definitionDialog.open)definitionDialog.close(); showMessage(""); input.focus(); }
