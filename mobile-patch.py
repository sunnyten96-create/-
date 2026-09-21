from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else "mobile-app")
js = root / "app/src/main/assets/mobile/app.js"
css = root / "app/src/main/assets/mobile/app.css"

s = js.read_text(encoding="utf-8")

old = """  function showManuscript(anchor='') {
    state.sheet={type:'manuscript',anchor}; render();
    if(anchor) setTimeout(()=>document.getElementById(`para-${anchor}`)?.scrollIntoView({block:'center',behavior:'smooth'}),120);
  }
"""
new = """  function normalizeEvidenceId(value='') {
    const m=String(value||'').match(/P\\s*0*(\\d+)/i);
    return m ? `P${String(Number(m[1])).padStart(4,'0')}` : String(value||'').replace(/[\\[\\]\\s]/g,'');
  }

  function evidenceForClaim(claimType, claimText, subject='') {
    const target=String(claimText||'').trim();
    const sub=String(subject||'').trim().toLocaleLowerCase('ko-KR');
    const hit=arr(state.analysis?.claimEvidence).find(c=>
      c?.claimType===claimType && String(c?.claimText||'').trim()===target && String(c?.subject||'').trim().toLocaleLowerCase('ko-KR')===sub
    );
    return arr(hit?.evidence);
  }

  function evidenceButtons(evidence, claim='') {
    return arr(evidence).map(raw=>{
      const id=normalizeEvidenceId(raw);
      return `<button class="evidence" data-action="evidence" data-id="${esc(id)}" data-claim="${esc(claim)}">${esc(raw)}</button>`;
    }).join('');
  }

  function showManuscript(anchor='', claim='') {
    const normalized=normalizeEvidenceId(anchor);
    state.sheet={type:'manuscript',anchor:normalized,claim:String(claim||'')}; render();
    if(normalized) setTimeout(()=>document.getElementById(`para-${normalized}`)?.scrollIntoView({block:'center',behavior:'smooth'}),160);
  }
"""
if old not in s:
    raise SystemExit("showManuscript block not found")
s = s.replace(old, new)

s = s.replace(
    "${arr(a.positives).length?detail('강점','＋',listHtml(a.positives,'good'),true):''}",
    "${arr(a.positives).length?detail('강점','＋',claimListHtml(a.positives,'positive','good'),true):''}"
)
s = s.replace(
    "${arr(a.negatives).length?detail('우려 지점','−',listHtml(a.negatives,'risk'),false):''}",
    "${arr(a.negatives).length?detail('우려 지점','−',claimListHtml(a.negatives,'negative','risk'),true):''}"
)

old = """  function listHtml(items,type='good'){return `<ul class="bullet-list ${type==='risk'?'risk':''}">${arr(items).map(x=>`<li class="bullet-item">${esc(typeof x==='string'?x:(x?.text||x?.detail||''))}</li>`).join('')}</ul>`}
  function suggestionsHtml(items){return arr(items).map(s=>`<div class="suggestion">${arr(s.location||s.evidence).length?`<div class="suggestion-loc">${arr(s.location||s.evidence).map(e=>`<button class="evidence" data-action="evidence" data-id="${esc(e)}">${esc(e)}</button>`).join('')}</div>`:''}<div class="suggestion-title">${esc(s.issue||s.title||'수정 제안')}</div><div class="suggestion-copy">${esc(s.suggestion||s.action||s.detail||'')}</div></div>`).join('')}
"""
new = """  function listHtml(items,type='good'){return `<ul class="bullet-list ${type==='risk'?'risk':''}">${arr(items).map(x=>`<li class="bullet-item">${esc(typeof x==='string'?x:(x?.text||x?.detail||''))}</li>`).join('')}</ul>`}
  function claimListHtml(items,claimType,type='good'){return `<ul class="bullet-list ${type==='risk'?'risk':''}">${arr(items).map(x=>{const text=typeof x==='string'?x:(x?.text||x?.detail||'');const ev=arr(x?.evidence).length?arr(x.evidence):evidenceForClaim(claimType,text);return `<li class="bullet-item claim-item"><div>${esc(text)}</div>${ev.length?`<div class="claim-evidence">${evidenceButtons(ev,text)}</div>`:''}</li>`}).join('')}</ul>`}
  function suggestionsHtml(items){return arr(items).map(s=>{const claim=s.issue||s.title||s.suggestion||s.detail||'수정 제안';const ev=arr(s.location||s.evidence);return `<div class="suggestion">${ev.length?`<div class="suggestion-loc">${evidenceButtons(ev,claim)}</div>`:''}<div class="suggestion-title">${esc(s.issue||s.title||'수정 제안')}</div><div class="suggestion-copy">${esc(s.suggestion||s.action||s.detail||'')}</div></div>`}).join('')}
"""
if old not in s:
    raise SystemExit("list/suggestions block not found")
s = s.replace(old, new)

old = """      const text=state.selectedChapter?.content||'';
      const paragraphs=text.split(/\\n\\s*\\n/).filter((p,i,a)=>p.trim()||a.length===1);
      const html=paragraphs.map((p,i)=>{const id=`P${String(i+1).padStart(3,'0')}`;const focus=state.sheet.anchor===id?' focus':'';return `<div class="paragraph${focus}" id="para-${id}"><span class="paragraph-id">${id}</span>${esc(p).replaceAll('\\n','<br>')}</div>`}).join('');
"""
new = """      const text=state.selectedChapter?.content||'';
      const paragraphs=text.split('\\n').map(p=>p.trim()).filter(Boolean);
      const focusId=normalizeEvidenceId(state.sheet.anchor||'');
      const claim=String(state.sheet.claim||'').trim();
      const html=paragraphs.map((p,i)=>{
        const id=`P${String(i+1).padStart(4,'0')}`;
        const focus=focusId===id?' focus':'';
        let body=esc(p);
        if(focus && claim){
          const sentences=p.match(/[^.!?。！？\\n]+[.!?。！？]?/g)?.map(x=>x.trim()).filter(Boolean)||[p];
          const tokens=[...new Set(claim.replace(/[^0-9A-Za-z가-힣\\s]/g,' ').split(/\\s+/).filter(x=>x.length>=2))];
          let best='',bestScore=0;
          for(const sentence of sentences){
            const overlap=tokens.reduce((n,t)=>n+(sentence.includes(t)?1:0),0);
            if(overlap>bestScore){bestScore=overlap;best=sentence;}
          }
          if(best && bestScore>0){
            const idx=p.indexOf(best);
            if(idx>=0) body=`${esc(p.slice(0,idx))}<mark class="sentence-focus">${esc(best)}</mark>${esc(p.slice(idx+best.length))}`;
          }
        }
        return `<div class="paragraph${focus}" id="para-${id}"><span class="paragraph-id">[${id}]</span>${body}</div>`
      }).join('');
"""
if old not in s:
    raise SystemExit("manuscript rendering block not found")
s = s.replace(old, new)

s = s.replace(
    "if(action==='evidence'){showManuscript(id);return;}",
    "if(action==='evidence'){showManuscript(id,el.dataset.claim||'');return;}"
)

js.write_text(s, encoding="utf-8")

c = css.read_text(encoding="utf-8")
c += """
.claim-item{display:block}
.claim-evidence{display:flex;flex-wrap:wrap;gap:5px;margin-top:7px}
.sentence-focus{background:#fff0a8;color:inherit;border-radius:3px;padding:1px 2px;box-shadow:0 0 0 2px #fff0a8}
.paragraph.focus{background:#f0ecff;box-shadow:inset 3px 0 0 var(--primary);animation:evidencePulse .7s ease-out}
@keyframes evidencePulse{0%{background:#ddd4ff}100%{background:#f0ecff}}
"""
css.write_text(c, encoding="utf-8")
print("mobile patch applied")
