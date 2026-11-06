# -*- coding: utf-8 -*-
"""TC-0008 修订：仅女性素体、健壮素体、群众、六种几何模型。
异常群众输入只验证输入/预览，不点击添加；合法输入才添加核对人数。
产品缺陷逐项记录，执行完全部用例后统一断言失败，不把已知缺陷标为通过。
运行：python test_tc0008_add_character.py，或 pytest -v -s 本文件。
准备：pip install playwright pytest；应用启用9222调试，已登录并进入3D导演台。
所有输入操作均通过实测元素定位；模型检查为当前版本只读适配器。
每次合法添加后校验并撤销本次操作；执行期间请勿人工操作场景。
"""
import os
import json
import re
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright, expect

READ_SCENE = r"""() => {
 const canvas = document.querySelector('.director-desk-root .director-canvas canvas');
 if (!canvas) throw Error('未找到导演台主画布');
 const key = Object.keys(canvas).find(k => k.startsWith('__reactFiber'));
 if (!key) throw Error('当前版本未暴露场景检查入口，需要更新适配器');
 let doc = null, store = null;
 for (let f = canvas[key], depth = 0; f && depth < 100; f = f.return, depth++) {
   for (let h = f.memoizedState, i = 0; h && i < 180; h = h.next, i++) {
     const v = h.memoizedState;
     if (v && Array.isArray(v.objects) && Array.isArray(v.cameras)
         && v.scene && v.version !== undefined) doc = v;
     const c = v?.current;
     if (c?.object?.isCamera && c.__r3f?.root?.getState) store = c.__r3f.root;
   }
 }
 if (!doc || !store) throw Error('场景适配器不兼容，无法验证真实添加结果');
 const s = store.getState(), root = s.scene.getObjectByName('director-scene-root');
 if (!root) throw Error('3D 场景根对象不存在');
 const groups = root.children.filter(o => o.isGroup &&
   o.__r3f?.props?.onPointerDown && !o.userData?.hideFromViewportCapture);
 const rendered = groups.map(g => {
   let meshCount = 0, visibleMeshCount = 0, inFrustumMeshCount = 0;
   const m = s.camera.projectionMatrix.clone().multiply(s.camera.matrixWorldInverse).elements;
   const planes = [[m[3]+m[0],m[7]+m[4],m[11]+m[8],m[15]+m[12]],
     [m[3]-m[0],m[7]-m[4],m[11]-m[8],m[15]-m[12]],
     [m[3]+m[1],m[7]+m[5],m[11]+m[9],m[15]+m[13]],
     [m[3]-m[1],m[7]-m[5],m[11]-m[9],m[15]-m[13]],
     [m[3]+m[2],m[7]+m[6],m[11]+m[10],m[15]+m[14]],
     [m[3]-m[2],m[7]-m[6],m[11]-m[10],m[15]-m[14]]];
   const modelNames = [];
   g.traverse(o => {
     if (o.name.startsWith('ue-retopology-mannequin-') || o.name.startsWith('geometry-')) modelNames.push(o.name);
     if (!o.isMesh || !o.geometry?.attributes?.position?.count) return;
     meshCount++;
     let visible = true;
     for (let a = o; a; a = a.parent) if (!a.visible) visible = false;
     const mats = Array.isArray(o.material) ? o.material : [o.material];
     if (visible && mats.some(m => m && m.visible && m.opacity > 0)) {
       visibleMeshCount++;
       // 使用渲染器已计算的包围球，只读判断模型是否与相机视锥相交。
       const bound = o.boundingSphere || o.geometry.boundingSphere;
       if (bound) {
         const ball = bound.clone().applyMatrix4(o.matrixWorld), c = ball.center;
         if (planes.every(p => p[0]*c.x+p[1]*c.y+p[2]*c.z+p[3] >=
             -ball.radius*Math.hypot(p[0],p[1],p[2]))) inFrustumMeshCount++;
       }
     }
   });
   return {uuid:g.uuid, meshCount, visibleMeshCount, inFrustumMeshCount, modelNames};
 });
 return {objects:doc.objects.map(o => ({id:o.id, name:o.name, kind:o.kind,
   bodyType:o.bodyType??null, visible:o.visible,crowdId:o.crowdId??null,crowdLabel:o.crowdLabel??null,transform:o.transform,geometryType:o.geometryType??null})), rendered,
   renderFrame:s.gl.info.render.frame, contextLost:s.gl.getContext().isContextLost()};
}"""

CHARACTERS=[('女性素体','female'),('健壮素体','muscular')]
GEOMETRIES=[('立方体','box'),('球体','sphere'),('圆柱体','cylinder'),('环状体','torus'),('圆锥','cone'),('棱锥','pyramid')]
INPUT_CASES=[]
for axis in ['行','列']:
    for value in ['-1','0','1','2','11','12','13','999999','','1.5']:
        INPUT_CASES.append((axis+'输入'+(value or '空值'),value if axis=='行' else '3',value if axis=='列' else '3'))
INPUT_CASES += [('行列同时越上限','13','13'),('行列同时输入大整数','999999','999999')]
LEGAL_CROWDS=[(1,1),(3,3),(12,12)]


def require(ok,message):
    if not ok:raise AssertionError(message)


def test_tc0008_add_character():
    output=Path(os.getenv('FJ_TEST_OUTPUT',str(Path(__file__).parent/'screenshots'/'tc0008_revised')))/datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    output.mkdir(parents=True)
    report=dict(case='TC-0008',revision='女性+健壮+群众+几何；按输入约束判定缺陷',status='RUNNING',cases=[],errors=[])
    page=None
    def save():
        (output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    with sync_playwright() as pw:
        try:
            browser=pw.chromium.connect_over_cdp('http://{}:{}'.format(os.getenv('FJ_CDP_HOST','127.0.0.1'),os.getenv('FJ_CDP_PORT','9222')),timeout=60000)
            pages=[p for c in browser.contexts for p in c.pages]
            hint=os.getenv('FJ_PAGE_URL')
            pages=[p for p in pages if hint in p.url] if hint else [p for p in pages if '帧境' in p.title()]
            require(len(pages)==1,'无法唯一确定帧境页面，请设置FJ_PAGE_URL')
            page=pages[0];page.set_default_timeout(15000)
            page.on('pageerror',lambda e:report['errors'].append(dict(type='pageerror',message=str(e))))
            page.on('console',lambda m:report['errors'].append(dict(type='console',message=m.text)) if m.type=='error' else None)
            page.on('requestfailed',lambda r:report['errors'].append(dict(type='requestfailed',message=r.url.split('?')[0],failure=r.failure)))
            root=page.locator('.director-desk-root');expect(root).to_have_count(1);expect(root).to_be_visible()
            add=root.get_by_role('button',name='添加角色',exact=True)
            menu=root.get_by_role('menu',name='选择角色体型',exact=True)
            dialog=root.get_by_role('dialog',name='添加群众阵列',exact=True)
            def state():return page.evaluate(READ_SCENE)
            report['baseline']=state()
            def open_main():
                if menu.is_visible():add.click();expect(menu).to_be_hidden()
                add.click();expect(menu).to_be_visible()
            def open_crowd():
                open_main();menu.get_by_role('menuitem',name='群众 (3x3)',exact=True).hover();expect(dialog).to_be_visible()
            def undo(before,after):
                require(state()['objects']==after['objects'],'场景有其他修改，停止撤销')
                root.get_by_role('button',name='撤销 ⌘Z',exact=True).click()
                page.wait_for_function('v=>JSON.stringify(('+READ_SCENE+')().objects)===JSON.stringify(v)',arg=before['objects'],timeout=60000)
            def wait_models(before,n):
                ids=[g['uuid'] for g in before['rendered']]
                page.wait_for_function('a=>{const s=('+READ_SCENE+')();const gs=s.rendered.filter(g=>!a.ids.includes(g.uuid));return !s.contextLost && gs.length===a.n && gs.every(g=>g.visibleMeshCount>0) && s.renderFrame>a.frame;}',arg=dict(ids=ids,n=n,frame=before['renderFrame']),timeout=60000)
                return [g for g in state()['rendered'] if g['uuid'] not in ids]
            def complete(case):
                case['status']='FAIL' if case.get('issues') else 'PASS'
                save();print(case['status'],case['id'],case['name'],case.get('display',''),'; '.join(case.get('issues',[])),flush=True)
            # 只选择女性及健壮，不遍历其余六种体型。
            for i,(name,kind) in enumerate(CHARACTERS,1):
                case=dict(id=f'A{i:02d}',name='添加'+name,status='RUNNING');report['cases'].append(case)
                open_main();before=state();old={o['id'] for o in before['objects']}
                menu.get_by_role('menuitem',name=name,exact=True).click();expect(menu).to_be_hidden()
                page.wait_for_function('n=>('+READ_SCENE+')().objects.length===n',arg=len(old)+1)
                after=state();new=[o for o in after['objects'] if o['id'] not in old]
                require(len(new)==1 and new[0]['kind']=='character' and new[0]['bodyType']==kind,'实际添加体型不符')
                row=root.get_by_role('group',name='角色分组',exact=True).get_by_role('treeitem',name=new[0]['name'],exact=True)
                expect(row).to_have_count(1);expect(row).to_have_attribute('aria-selected','true')
                expect(root.get_by_role('region',name='角色右侧属性面板',exact=True)).to_be_visible()
                models=wait_models(before,1);require('ue-retopology-mannequin-'+kind in models[0]['modelNames'],'真实模型体型不符')
                page.screenshot(path=str(output/f'A{i:02d}_{kind}.png'))
                case.update(actual_added=1,object=new[0],models=models)
                undo(before,after);case['restored']=True;complete(case)
            # 输入矩阵：无论预览如何，绝不点击添加群众；逐项记录问题后继续执行。
            for i,(name,raw_r,raw_c) in enumerate(INPUT_CASES,1):
                case=dict(id=f'I{i:02d}',name=name,requested_rows=raw_r,requested_columns=raw_c,mode='INPUT_ONLY',status='RUNNING',issues=[]);report['cases'].append(case)
                before=state();open_crowd()
                r=dialog.get_by_role('spinbutton',name='群众行数',exact=True)
                c=dialog.get_by_role('spinbutton',name='群众列数',exact=True)
                r.fill(raw_r);case['row_immediate']=r.input_value()
                c.fill(raw_c);case['column_immediate']=c.input_value()
                c.press('Tab')
                case['fields']=dialog.locator('input').evaluate_all('(es)=>es.map(e=>({label:e.getAttribute("aria-label"),value:e.value,min:e.min,max:e.max,valid:e.validity.valid,underflow:e.validity.rangeUnderflow,overflow:e.validity.rangeOverflow,stepMismatch:e.validity.stepMismatch}))')
                actual_r=r.input_value();actual_c=c.input_value()
                case.update(actual_rows=actual_r,actual_columns=actual_c,display=dialog.locator('.viewport-toolbar-crowd-panel-count').inner_text(),add_enabled=dialog.get_by_role('button',name='添加群众',exact=True).is_enabled())
                values=[]
                for label,text in [('行数',actual_r),('列数',actual_c)]:
                    if text=='':
                        values.append(None)
                        if case['add_enabled']:case['issues'].append(label+'为空时添加按钮仍可用')
                    else:
                        number=float(text);values.append(number)
                        if number<=0:case['issues'].append(f'{label}成功保留非法值{text}，应拒绝小于等于0')
                        elif not number.is_integer():case['issues'].append(f'{label}成功保留小数{text}，人数行列应为正整数')
                if all(v is not None for v in values):
                    product=values[0]*values[1]
                    case['input_product']=int(product) if product.is_integer() else product
                    match=re.fullmatch(r'共\s*(\d+)\s*人',case['display'])
                    actual_count=int(match.group(1)) if match else None
                    case['preview_count']=actual_count
                    if actual_count!=product:case['issues'].append(f'人数预览{actual_count}不等于输入行×列={case["input_product"]}')
                page.screenshot(path=str(output/f'I{i:02d}_input_only.png'))
                dialog.get_by_role('button',name='取消',exact=True).click();expect(dialog).to_be_hidden()
                require(state()['objects']==before['objects'],'只检查输入时不应新增或修改场景对象')
                case['actual_added']=0;complete(case)
            # 仅对合法行列点击添加，比较输入乘积、预览、对象、成员、模型及实际布局。
            for i,(rows,cols) in enumerate(LEGAL_CROWDS,1):
                n=rows*cols;case=dict(id=f'C{i:02d}',name=f'合法群众{rows}×{cols}',rows=rows,columns=cols,expected_count=n,status='RUNNING');report['cases'].append(case)
                open_crowd();r=dialog.get_by_role('spinbutton',name='群众行数',exact=True);c=dialog.get_by_role('spinbutton',name='群众列数',exact=True)
                r.fill(str(rows));c.fill(str(cols));c.press('Tab')
                expect(r).to_have_value(str(rows));expect(c).to_have_value(str(cols))
                expect(dialog.locator('.viewport-toolbar-crowd-panel-count')).to_have_text(f'共{n}人')
                before=state();old={o['id'] for o in before['objects']}
                dialog.get_by_role('button',name='添加群众',exact=True).click();expect(dialog).to_be_hidden()
                page.wait_for_function('n=>('+READ_SCENE+')().objects.length===n',arg=len(old)+n,timeout=60000)
                after=state();new=[o for o in after['objects'] if o['id'] not in old]
                require(len(new)==n and all(o['kind']=='character' and o['visible'] for o in new),'实际新增群众人数不等于输入乘积')
                require(len({o['crowdId'] for o in new})==1 and new[0]['crowdId'],'群众ID错误')
                label=new[0]['crowdLabel'];require(label==f'群众（{rows}x{cols}）','群众分组名称错误')
                # 按实际观测到的data-crowd-id确定本次分组，兼容已有同名群众。
                crowd=root.get_by_role('group',name='群众分组',exact=True)
                matches=[e for e in crowd.locator('[data-crowd-id]').all() if e.get_attribute('data-crowd-id')==new[0]['crowdId']]
                require(len(matches)==1,'新增群众分组不唯一');row=matches[0]
                expect(row).to_have_attribute('aria-selected','true')
                row.get_by_role('button',name='展开 '+label,exact=True).click()
                members=row.locator('..').get_by_role('list',name=label+' 成员预览',exact=True).get_by_role('button')
                expect(members).to_have_count(n);require(set(members.all_text_contents())=={o['name'] for o in new},'成员列表名称不符')
                pos=[o['transform']['position'] for o in new]
                require(len({round(v[0],5) for v in pos})==cols and len({round(v[2],5) for v in pos})==rows,'实际群众布局行列不符')
                require(len({tuple(v) for v in pos})==n,'群众位置重复')
                models=wait_models(before,n)
                page.screenshot(path=str(output/f'C{i:02d}_{rows}x{cols}_added.png'))
                case.update(display=f'共{n}人',actual_added=len(new),member_count=members.count(),model_count=len(models),objects=new)
                undo(before,after);case['restored']=True;complete(case)
            for i,(name,kind) in enumerate(GEOMETRIES,1):
                case=dict(id=f'G{i:02d}',name='添加'+name,status='RUNNING');report['cases'].append(case)
                open_main();menu.get_by_role('menuitem',name='几何模型',exact=True).hover()
                submenu=root.get_by_role('menu',name='选择几何模型',exact=True);expect(submenu).to_be_visible()
                before=state();old={o['id'] for o in before['objects']}
                submenu.get_by_role('menuitem',name=name,exact=True).click();expect(submenu).to_be_hidden()
                page.wait_for_function('n=>('+READ_SCENE+')().objects.length===n',arg=len(old)+1)
                after=state();new=[o for o in after['objects'] if o['id'] not in old]
                require(len(new)==1 and new[0]['kind']=='prop' and new[0]['geometryType']==kind,'几何模型对象不符')
                expect(root.get_by_role('treeitem',name=new[0]['name'],exact=True)).to_have_attribute('aria-selected','true')
                models=wait_models(before,1);require('geometry-'+kind in models[0]['modelNames'],'真实几何网格不符')
                page.screenshot(path=str(output/f'G{i:02d}_{kind}.png'))
                case.update(actual_added=1,object=new[0],models=models)
                undo(before,after);case['restored']=True;complete(case)
            require(state()['objects']==report['baseline']['objects'],'最终对象基线未恢复')
            report['passed']=sum(c['status']=='PASS' for c in report['cases'])
            report['failed']=sum(c['status']=='FAIL' for c in report['cases'])
            report['execution_complete']=True
            report['status']='FAIL' if report['failed'] or report['errors'] else 'PASS'
        except Exception as error:
            report.update(status='ERROR',execution_error=str(error),execution_complete=False)
            if report['cases'] and report['cases'][-1]['status']=='RUNNING':report['cases'][-1].update(status='ERROR',error=str(error))
            if page:
                try:page.screenshot(path=str(output/'execution_error.png'),timeout=5000)
                except Exception:pass
            raise
        finally:
            save();print(report['status'],'report:',output/'report.json',flush=True)
    # 实际缺陷导致非零退出；已执行全部检查并保留逐项结果。
    require(report['status']=='PASS',f"TC-0008发现{report.get('failed',0)}项失败，运行异常{len(report['errors'])}条；详见{output/'report.json'}")


if __name__=='__main__':
    test_tc0008_add_character()
