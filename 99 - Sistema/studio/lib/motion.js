/* Video Factory: analytic, random-access motion. No runtime dependencies.
 * Unit mass by default; step response of m*x''+d*x'+k*x=k, x(0)=x'(0)=0.
 * This is original implementation, not a copy of a social-post renderer.
 */
(function(root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.CVFStudioMotion = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function() {
  'use strict';
  function finite(x, name) {
    if (typeof x !== 'number' || !Number.isFinite(x)) throw Error(name+' must be finite');
    return x;
  }
  const clamp = (v, lo=0, hi=1) => Math.min(hi, Math.max(lo,v));
  function spring(t, {stiffness=170, damping=26, mass=1}={}) {
    [t,stiffness,damping,mass].forEach((x,i)=>finite(x,['t','stiffness','damping','mass'][i]));
    if(stiffness<=0 || damping<0 || mass<=0) throw Error('Invalid spring parameters');
    if(t<=0) return 0;
    const w = Math.sqrt(stiffness/mass), z=damping/(2*Math.sqrt(stiffness*mass));
    if(Math.abs(z-1)<1e-7) return 1-(1+w*t)*Math.exp(-w*t);
    if(z<1) {
      const wd=w*Math.sqrt(1-z*z);
      return 1-Math.exp(-z*w*t)*(Math.cos(wd*t)+(z*w/wd)*Math.sin(wd*t));
    }
    // Actual overdamped solution: do not silently substitute critical damping.
    const a=Math.sqrt(z*z-1), r1=-w/(z+a), r2=-w*(z+a);
    return 1+(r2*Math.exp(r1*t)-r1*Math.exp(r2*t))/(r1-r2);
  }
  function track(t, keys, options={}) {
    finite(t,'t');
    if(!Array.isArray(keys)||!keys.length) throw Error('Track requires keys');
    let prev=-Infinity;
    for(const pair of keys) {
      if(!Array.isArray(pair)||pair.length!==2) throw Error('Invalid key');
      const [at,v]=pair; finite(at,'time'); finite(v,'value');
      if(at<=prev) throw Error('Key times must increase strictly'); prev=at;
    }
    let v=keys[0][1];
    for(let i=1;i<keys.length;i++) v+=(keys[i][1]-keys[i-1][1])*spring(t-keys[i][0],options);
    return v;
  }
  function indicator(t, stops, width=120) {
    finite(width,'width'); if(width<=0)throw Error('Positive width required');
    const lead=track(t,stops,{stiffness:320,damping:30});
    const trail=track(t,stops,{stiffness:140,damping:22});
    return {left:Math.min(lead,trail),right:Math.max(lead,trail)+width};
  }
  function rng(seed) {
    if(!Number.isInteger(seed)) throw Error('Integer seed required');
    let state=seed>>>0;
    return function() {
      state=(Math.imul(1664525,state)+1013904223)>>>0;
      return state/4294967296;
    };
  }
  // Reset a generator inside seek, or precompute static noise at initialization.
  // A seeded generator whose state advances between seeks is NOT deterministic.
  function loopT(t,duration) {
    finite(t,'t'); finite(duration,'duration'); if(duration<=0)throw Error('Positive duration required');
    return ((t%duration)+duration)%duration;
  }
  function swapAlpha(t,start,end,enter=.16,exit=.14) {
    [t,start,end,enter,exit].forEach(x=>finite(x,'alpha input'));
    if(end<=start||enter<=0||exit<=0)throw Error('Invalid alpha interval');
    return Math.min(clamp((t-start)/enter),clamp((end-t)/exit));
  }
  function layout(w,h) {
    if(!Number.isInteger(w)||!Number.isInteger(h)||w<=0||h<=0)throw Error('Invalid layout');
    const m=Math.min(w,h)*.07, vertical=h>w*1.12;
    return {w,h,margin:m,vertical,content:{x:m,y:m,w:w-2*m,h:h-2*m},
      // Reflow is an authoring choice. This is not a platform-certified safe area.
      columns:vertical?1:2};
  }
  return {clamp,spring,track,indicator,rng,loopT,swapAlpha,layout};
});
