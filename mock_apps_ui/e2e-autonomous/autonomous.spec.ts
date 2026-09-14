import {test, expect, type APIRequestContext, type Page} from "@playwright/test";
import {mkdir} from "node:fs/promises";
import {fileURLToPath} from "node:url";
const shots=fileURLToPath(new URL("../../docs/screenshots/phase10-minute-opening/", import.meta.url));
const headers={Origin:"http://127.0.0.1:5231","X-Stratos-Action":"1","X-Stratos-Demo-Profile":"automation","X-Stratos-Demo-Maintainer":"local-demo-reset"};
const workspace=(page:Page)=>page.locator('.aw-workspace');

test.beforeEach(async({context})=>{
  await context.addInitScript(()=>{
    class NoSpeech {start(){throw Error("No real speech in tests");} stop(){} abort(){}}
    Object.assign(window,{SpeechRecognition:NoSpeech,webkitSpeechRecognition:NoSpeech});
  });
  await mkdir(shots,{recursive:true});
});
async function login(page:Page, path='/control/overview') {
  await page.goto(path);
  await page.getByRole('button',{name:'Log in',exact:true}).click();
  await page.getByRole('dialog',{name:'Demo access'}).getByRole('button',{name:/^Program operator/}).click();
  if (path === '/control/overview') await expect(page.locator('.cp-connection')).toContainText('Current read');
  else await controls(page); // Reader entry redirects until a permitted persona is selected.
}
async function fullReset(request:APIRequestContext) {
  const state=await (await request.get('/control-api/demo')).json();
  const r=await request.post('/control-api/demo/reset',{headers,data:{scope:'full',confirmation:'RESET',expected_epoch:state.epoch}});
  expect(r.ok(),await r.text()).toBeTruthy();
}
async function controls(page:Page) {
  await page.getByRole('navigation',{name:'Control plane navigation'}).getByRole('link',{name:'Operations',exact:true}).click();
  await page.getByRole('link',{name:'Demo controls',exact:true}).click();
}
async function prepare(page:Page) {
  await controls(page);
  await page.getByRole('button',{name:'Replay autonomous opening',exact:true}).click();
  await expect(page.locator('.cp-autonomous-opening')).toContainText('QE-011 starts automatically');
  await page.getByRole('link',{name:'Open Overview →',exact:true}).click();
}

test('app entry starts QE-011 automatically with a full roster and concurrent isolated work',async({page,request})=>{
  const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
  await fullReset(request);
  const indexed=await request.post('/control-api/knowledge/reindex',{headers,data:{rebuild:false,confirm:'REINDEX KNOWLEDGE'}});
  expect(indexed.ok(),await indexed.text()).toBeTruthy();
  await login(page);
  await expect(workspace(page)).toContainText('QE-011 starts automatically');
  await expect(workspace(page).locator('[data-agent-id="coordinator"]')).toHaveAttribute('data-display-state','processing',{timeout:15000});
  await expect(workspace(page)).toContainText('Scoping work');
  await expect(workspace(page)).not.toContainText('Demo pacing');
  await expect(workspace(page)).not.toContainText('Scripted demo');
  await expect(workspace(page)).not.toContainText('Selected task');
  await expect(workspace(page)).not.toContainText('active investigation');
  await page.screenshot({path:shots+'/coordinator-triage-1440.png',fullPage:true});
  await expect(workspace(page).locator('.aw-flowing')).toHaveCount(4,{timeout:20000});
  await expect(workspace(page).locator('.aw-agent')).toHaveCount(5);
  await expect(workspace(page).locator('[data-agent-id="change_impact"]')).toHaveAttribute('data-display-state','processing');
  await expect(workspace(page).locator('[data-agent-id="coordinator"]')).toContainText('With specialists');
  const qe=(await (await request.get('/control-api/demo/autonomous',{headers})).json()).run_id;
  const dot=workspace(page).locator('.aw-flowing circle').first();
  const before=await dot.evaluate(el=>getComputedStyle(el).offsetDistance);
  await page.waitForTimeout(150);
  expect(await dot.evaluate(el=>getComputedStyle(el).offsetDistance)).not.toBe(before);
  await page.getByRole('link',{name:'Inspect case CR-017',exact:true}).click();
  await page.getByRole('button',{name:'Run investigation',exact:true}).click();
  await page.getByRole('navigation',{name:'Control plane navigation'}).getByRole('link',{name:'Overview',exact:true}).click();
  await expect(workspace(page)).toContainText('2 Active runs');
  const runs=await (await request.get('/control-api/runs',{headers})).json();
  const cr=runs.find((r:any)=>r.change_id==='CR-017').run_id;
  await expect(workspace(page)).toHaveAttribute('data-selection',cr);
  await workspace(page).getByRole('combobox').selectOption(qe);
  await expect(workspace(page).locator('.aw-agent')).toHaveCount(5);
  await expect(workspace(page).getByRole('combobox')).toContainText('Source event');
  await page.screenshot({path:shots+'/concurrent-1440.png',fullPage:true});
  await expect(workspace(page).locator('[data-agent-id="coordinator"]')).toContainText('Reconciling findings',{timeout:95000});
  await expect(workspace(page).locator('.aw-flowing')).toHaveCount(0);
  await page.screenshot({path:shots+'/coordinator-review-1440.png',fullPage:true});
  await expect(workspace(page)).toContainText('Preparing assessment',{timeout:15000});
  await expect(workspace(page)).toContainText('Quality investigation handoff verified',{timeout:20000});
  const completed=(await (await request.get('/control-api/runs',{headers})).json()).find((r:any)=>r.run_id===qe);
  expect(Date.parse(completed.completed_at)-Date.parse(completed.started_at)).toBeGreaterThanOrEqual(120000);
  await expect(workspace(page).locator('.aw-flowing')).toHaveCount(0);
  await expect(workspace(page)).toHaveAttribute('data-selection',qe);
  await expect(page.locator('.cp-attention-section')).not.toContainText('QE-011');
  await workspace(page).getByRole('combobox').selectOption(cr);
  await expect(workspace(page)).toContainText('Awaiting Engineering review',{timeout:30000});
  await workspace(page).getByRole('combobox').selectOption(qe);
  for(const [width,height] of [[1440,900],[1920,1080],[1280,800],[390,844]]) {
    await page.setViewportSize({width,height});
    await page.screenshot({path:shots+'/handoff-'+width+'.png',fullPage:true});
    expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBeTruthy();
  }
  await page.setViewportSize({width:1440,height:900});
  await page.getByRole('link',{name:'Inspect QE-011',exact:true}).click();
  await page.locator('a[href="/control/runs/'+qe+'"]').first().click();
  await expect(page.getByText('Manufacturing source event',{exact:true})).toBeVisible();
  await expect(page.getByText('Touchless / standard quality investigation',{exact:true})).toBeVisible();
  await expect(page.getByText('Handoff verified · Lab authorization pending',{exact:true})).toHaveCount(0);
  await expect(page.getByText('Not required for executed actions',{exact:true})).toBeVisible();
  await expect(page.locator('.kn-run-event')).toHaveCount(3);
  await page.screenshot({path:shots+'/operations-1440.png',fullPage:true});
  await page.locator('a[href="/control/programs/PRG-A17/cases/QE-011"]').first().click();
  await expect(page.getByRole('heading',{name:'Recovery decision',exact:true})).toHaveCount(0);
  await expect(page.getByText(/No human approval required for executed actions/)).toBeVisible();
  await page.screenshot({path:shots+'/case-1440.png',fullPage:true});
  await controls(page);
  await page.getByRole('button',{name:'Reset autonomous opening'}).click();
  await expect(page.locator('.cp-autonomous-opening')).toContainText('Autonomous opening idle');
  const remaining=await (await request.get('/control-api/runs',{headers})).json();
  expect(remaining.map((r:any)=>r.change_id)).toEqual(['CR-017']);
  expect(errors).toEqual([]);
});

test('reset cancels automatic entry, stays at baseline, and reload starts one new opening',async({page,request,context})=>{
  await fullReset(request);await login(page);
  await expect(workspace(page)).toContainText('QE-011 starts automatically');
  await controls(page);
  await page.getByRole('button',{name:'Reset autonomous opening'}).click();
  await expect(page.locator('.cp-autonomous-opening')).toContainText('Autonomous opening idle');
  await page.waitForTimeout(8500);
  expect(await (await request.get('/control-api/runs',{headers})).json()).toEqual([]);
  await page.getByRole('link',{name:'Open Overview →',exact:true}).click();
  await expect(workspace(page).locator('.aw-agent')).toHaveCount(5);
  await expect(workspace(page).locator('[data-display-state="idle"]')).toHaveCount(5);
  expect((await (await request.get('/control-api/demo/autonomous',{headers})).json()).status).toBe('idle');
  await page.reload();
  await expect(workspace(page)).toContainText('QE-011 starts automatically');
  const generation=(await (await request.get('/control-api/demo/autonomous',{headers})).json()).generation;
  const second=await context.newPage();await second.goto('/control/overview');
  await expect(workspace(second)).toContainText('QE-011 starts automatically');
  expect((await (await request.get('/control-api/demo/autonomous',{headers})).json()).generation).toBe(generation);
  await expect(workspace(page)).toContainText('Quality investigation handoff verified',{timeout:150000});
  expect((await (await request.get('/control-api/runs',{headers})).json())).toHaveLength(1);
  await page.reload();
  await expect(workspace(page)).toContainText('Quality investigation handoff verified');
  expect((await (await request.get('/control-api/demo/autonomous',{headers})).json()).generation).toBe(generation);
  await second.close();
});

test('full reset controls restore the initial state without immediately rearming',async({page,request})=>{
  await fullReset(request);
  await login(page,'/control/operations/demo');
  expect((await (await request.get('/control-api/demo/autonomous',{headers})).json()).status).toBe('idle');
  await page.getByRole('combobox',{name:'Reset scope'}).selectOption('full');
  await page.getByRole('button',{name:'Review reset…',exact:true}).click();
  await page.getByRole('dialog').getByLabel('Type RESET to confirm').fill('RESET');
  await page.getByRole('dialog').getByRole('button',{name:'Confirm demo reset',exact:true}).click();
  await expect(page.getByRole('dialog')).toHaveCount(0);
  const verify=await request.get('/control-api/demo/verify?scope=full');
  expect((await verify.json()).baseline_valid).toBe(true);
  expect((await (await request.get('/control-api/demo/autonomous',{headers})).json()).status).toBe('idle');
  expect((await (await request.get('/control-api/runs',{headers})).json())).toEqual([]);
  await page.getByRole('navigation',{name:'Control plane navigation'}).getByRole('link',{name:'Overview',exact:true}).click();
  await expect(workspace(page).locator('[data-display-state="idle"]')).toHaveCount(5);
  await page.waitForTimeout(8500);
  expect((await (await request.get('/control-api/demo/autonomous',{headers})).json()).status).toBe('idle');
});
