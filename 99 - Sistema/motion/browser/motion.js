/* CVF Motion 1.0.0. Frame-driven, offline SVG animation; no model calls.
 * Exposed as CVFMotion in the browser and module.exports for Node tests.
 * Untrusted strings are text, never executable markup.
 */
(function(root) {
  'use strict';
  const VERSION = '1.0.0';
  const esc = v => String(v).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&apos;'}[c]));
  const clamp = n => Math.min(1, Math.max(0, n));
  const ease = n => 1 - Math.pow(1 - clamp(n), 3);
  const integer = (v, lo, hi) => Number.isInteger(v) && v >= lo && v <= hi;
  const finite = (v, lo, hi) => typeof v === 'number' && Number.isFinite(v) && v >= lo && v <= hi;
  const textOK = (v, n) => typeof v === 'string' && v.trim().length > 0 && v.length <= n;
  function validate(s) {
    if (!s || typeof s !== 'object' || Array.isArray(s)) throw Error('Expected motion spec object');
    if (!textOK(s.id, 100) || !textOK(s.child_id, 100)) throw Error('id and child_id are required');
    if (!['keyphrase','steps','proof-frame','lower-third'].includes(s.template)) throw Error('Unknown template');
    if (!integer(s.width, 160, 4096) || !integer(s.height, 160, 4096)) throw Error('Invalid dimensions');
    if (!finite(s.fps, 1, 120) || !integer(s.duration_frames, 4, 3600)) throw Error('Invalid timing');
    if (!['overlay','fullframe'].includes(s.mode)) throw Error('mode must be overlay or fullframe');
    for (const k of ['foreground','background','accent']) if (!/^#[a-fA-F0-9]{6}$/.test(s.colors?.[k] || '')) throw Error('Invalid color '+k);
    if (!Array.isArray(s.lines) || s.lines.length > 3 || s.lines.some(t => !textOK(t, 65))) throw Error('Use at most 3 short lines');
    if (s.template !== 'proof-frame' && s.lines.length === 0) throw Error('Text required');
    if (s.template === 'steps' && (!Array.isArray(s.steps) || s.steps.length < 2 || s.steps.length > 4 || s.steps.some(t => !textOK(t, 45)))) throw Error('Use 2 to 4 short steps');
    if (s.label !== undefined && (typeof s.label !== 'string' || s.label.length > 60)) throw Error('Invalid label');
    const b=s.box;
    if (!b || !finite(b.x,0,1) || !finite(b.y,0,1) || !finite(b.w,0.1,1) || !finite(b.h,0.1,1) || b.x+b.w>1.000001 || b.y+b.h>1.000001) throw Error('box must fit within the frame');
    if (s.asset_data_uri !== undefined && !/^data:image\/(png|jpeg|webp);base64,[A-Za-z0-9+/=]+$/.test(s.asset_data_uri)) throw Error('Only embedded raster images are allowed');
    if (s.font_family !== undefined && !/^[A-Za-z0-9 ,\-]+$/.test(s.font_family)) throw Error('Invalid font family');
    return s;
  }
  function state(frame,s) {
    validate(s);
    if (!Number.isInteger(frame)) throw Error('frame must be integer');
    const n=s.duration_frames, edge=Math.min(Math.max(2,Math.round(s.fps*.22)),Math.floor((n-1)/2));
    return {opacity: frame<0 || frame>=n ? 0 : Math.min(ease(frame/edge),ease((n-1-frame)/edge)), progress:clamp(frame/Math.max(1,n-1))};
  }
  function renderFrame(frame,s) {
    const st=state(frame,s), w=s.width,h=s.height;
    const b={x:s.box.x*w,y:s.box.y*h,w:s.box.w*w,h:s.box.h*h};
    const c=s.colors, pad=Math.min(b.w,b.h)*.1;
    const font=esc(s.font_family || 'Arial, sans-serif');
    let body='';
    if(s.mode==='fullframe') body+=`<rect width="${w}" height="${h}" fill="${c.background}"/>`;
    const text=(t,x,y,size,weight=600,color=c.foreground)=>`<text x="${x}" y="${y}" font-family="${font}" font-size="${size}" font-weight="${weight}" fill="${color}">${esc(t)}</text>`;
    let inner=`<rect x="${b.x}" y="${b.y}" width="${b.w}" height="${b.h}" rx="${pad*.7}" fill="${c.background}" fill-opacity=".96"/>`;
    inner+=`<rect x="${b.x}" y="${b.y+pad}" width="${Math.max(2,w*.005)}" height="${b.h-2*pad}" fill="${c.accent}"/>`;
    if(s.template==='proof-frame') {
      if(!s.asset_data_uri) throw Error('proof-frame needs asset_data_uri; prepare the local image first');
      inner+=`<image href="${s.asset_data_uri}" x="${b.x+pad}" y="${b.y+pad}" width="${b.w-2*pad}" height="${b.h-2.8*pad}" preserveAspectRatio="xMidYMid meet"/>`;
      if(s.label) inner+=text(s.label,b.x+pad,b.y+b.h-pad*.55,Math.min(pad*.65,b.w/(s.label.length*.7)),500);
    } else if(s.template==='steps') {
      const fs=Math.min(b.w*.06,b.h*.09), row=(b.h-pad*2)/(s.steps.length+1);
      inner+=text(s.lines[0],b.x+pad,b.y+pad+fs,Math.min(fs,b.w*.82/(s.lines[0].length*.64)),700);
      s.steps.forEach((t,i)=>{
        const reveal=ease((frame-i*Math.round(s.fps*.18))/Math.max(2,Math.round(s.fps*.22)));
        const y=b.y+pad+row*(i+1)+fs;
        inner+=`<g opacity="${reveal}" transform="translate(${(1-reveal)*w*.02} 0)">`;
        inner+=text(String(i+1).padStart(2,'0'),b.x+pad,y,fs,700,c.accent);
        inner+=text(t,b.x+pad+fs*2.2,y,Math.min(fs,(b.w-2*pad-fs*2.2)/(t.length*.64)),500)+'</g>';
      });
    } else {
      const maxLength=Math.max(...s.lines.map(t=>t.length));
      const fs=Math.min((b.w-pad*2)/Math.max(1,maxLength*.64),b.h/(s.lines.length*1.35+1.7));
      const center=b.y+b.h/2;
      s.lines.forEach((t,i)=>{inner+=text(t,b.x+pad,center+(i-(s.lines.length-1)/2)*fs*1.22+fs*.32,fs,700);});
    }
    body+=`<g opacity="${st.opacity}" transform="translate(0 ${(1-st.opacity)*h*.012})">${inner}</g>`;
    return `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">${body}</svg>`;
  }
  const api={VERSION,validate,state,renderFrame};
  root.CVFMotion=api;
  if(typeof module!=='undefined' && module.exports) module.exports=api;
})(globalThis);
