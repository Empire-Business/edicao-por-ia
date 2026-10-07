const test=require('node:test');const assert=require('node:assert/strict');
const M=require('../studio/lib/motion.js');
const near=(a,b,tol=1e-5)=>assert.ok(Math.abs(a-b)<tol,`${a} != ${b}`);
test('spring rest before event',()=>{near(M.spring(-1),0);near(M.spring(0),0)});
test('spring finite parameters only',()=>{for(const t of [NaN,Infinity,'1'])assert.throws(()=>M.spring(t));});
test('spring invalid physical parameters',()=>{for(const c of [{stiffness:0},{damping:-1},{mass:0}])assert.throws(()=>M.spring(.1,c));});
test('critical analytic value',()=>near(M.spring(1,{stiffness:4,damping:4}),1-3*Math.exp(-2)));
test('overdamping not silently critical',()=>assert.ok(Math.abs(M.spring(.3,{stiffness:4,damping:12})-M.spring(.3,{stiffness:4,damping:4}))>.02));
for(const [name,damping] of [['under',8],['critical',20],['over',35]]){
 test(name+' step satisfies differential equation',()=>{const dt=1e-5,t=.2,k=100,x=M.spring(t,{stiffness:k,damping}),l=M.spring(t-dt,{stiffness:k,damping}),r=M.spring(t+dt,{stiffness:k,damping});near((r-2*x+l)/(dt*dt)+damping*(r-l)/(2*dt)+k*x,k,.005)});
 test(name+' converges',()=>near(M.spring(30,{stiffness:100,damping}),1));
}
test('mass equivalence',()=>near(M.spring(.3,{stiffness:200,damping:40,mass:2}),M.spring(.3,{stiffness:100,damping:20})));
test('track superposition identity',()=>near(M.track(2,[[0,2],[1,5],[1.5,1]]),2+3*M.spring(1)-4*M.spring(.5)));
test('track continuity across target change',()=>near(M.track(1-1e-7,[[0,0],[1,10],[2,0]]),M.track(1+1e-7,[[0,0],[1,10],[2,0]])));
test('track out of order seeks identical',()=>{const k=[[0,2],[1,5],[2,0]];const expected=M.track(2.3,k);M.track(100,k);M.track(.1,k);near(M.track(2.3,k),expected)});
test('track rejects repeated/invalid keys',()=>{assert.throws(()=>M.track(1,[]));assert.throws(()=>M.track(1,[[0,1],[0,2]]));assert.throws(()=>M.track(1,[[0,NaN]]));});
test('indicator width nonnegative and bounded',()=>{const x=M.indicator(.3,[[0,0],[.1,40]]);assert.ok(x.right-x.left>=120)});
test('seed reproducible after reset',()=>{const a=M.rng(21),b=M.rng(21);for(let i=0;i<50;i++)near(a(),b())});
test('seeded sequence advances and must be reset',()=>{const a=M.rng(21);assert.notEqual(a(),a())});
test('loop modulo handles negative time, not seam proof',()=>{near(M.loopT(-1,4),3);assert.throws(()=>M.loopT(1,0));});
test('alpha only within window',()=>{near(M.swapAlpha(0,1,2),0);near(M.swapAlpha(1.5,1,2),1);near(M.swapAlpha(3,1,2),0)});
test('layout reflows by aspect',()=>{assert.equal(M.layout(360,640).columns,1);assert.equal(M.layout(640,360).columns,2);assert.equal(M.layout(360,360).columns,2)});
