from pathlib import Path
import re
import subprocess

index = Path('index.html')
workflow = Path('.github/workflows/apply-stage1-spawn-clearance.yml')
self_path = Path('tools/apply_stage1_spawn_clearance.py')
html = index.read_text(encoding='utf-8')

old = "spawnClusters: [{ x: 64, y: 48 }, { x: 166, y: 48 }, { x: 264, y: 48 }],"
new = "spawnClusters: [{ x: 64, y: 48 }, { x: 166.67, y: 48 }, { x: 264, y: 48 }],"
if html.count(old) != 1:
    raise SystemExit(f'spawn cluster match count: {html.count(old)}')
html = html.replace(old, new, 1)

needle = """  function countTypes(list) {
    return list.reduce((acc, type) => { acc[type] = (acc[type] || 0) + 1; return acc; }, {});
  }
"""
addition = needle + """  function stageSpawnPosition(stage, i) {
    const clusters = stage.spawnClusters || SPAWN_CLUSTERS;
    const spacing = stage.spawnSpacing || 17;
    const cluster = clusters[Math.floor(i / 10)];
    return { x: cluster.x + ((i % 5) - 2) * spacing, y: cluster.y + Math.floor((i % 10) / 5) * spacing };
  }
  function spawnIntersectsStageWall(stage, point, radius = BALL_RADIUS) {
    return stage.rects.some(rect => {
      if (rect.kind !== 'wall') return false;
      const world = rectToWorld(rect);
      const nearestX = clamp(point.x, world.x, world.x + world.w);
      const nearestY = clamp(point.y, world.y, world.y + world.h);
      return (point.x - nearestX) ** 2 + (point.y - nearestY) ** 2 < (radius - 0.01) ** 2;
    });
  }
"""
if html.count(needle) != 1:
    raise SystemExit(f'countTypes match count: {html.count(needle)}')
html = html.replace(needle, addition, 1)

needle2 = """    for (const x of [8, 27, 40]) if (stageHasWallAt(stage, x, 34)) warnings.push('第1障壁の室別出口が塞がっている: ' + x);
    for (const x of [10, 36]) if (stageHasWallAt(stage, x, 66)) warnings.push('第2障壁の左右開口が塞がっている: ' + x);
    return warnings;
"""
replacement2 = """    for (const x of [8, 27, 40]) if (stageHasWallAt(stage, x, 34)) warnings.push('第1障壁の室別出口が塞がっている: ' + x);
    for (const x of [10, 36]) if (stageHasWallAt(stage, x, 66)) warnings.push('第2障壁の左右開口が塞がっている: ' + x);
    const spawnPoints = Array.from({ length: TOTAL }, (_, i) => stageSpawnPosition(stage, i));
    for (let i = 0; i < spawnPoints.length; i++) {
      if (spawnIntersectsStageWall(stage, spawnPoints[i])) warnings.push('初期配置が固定壁へ接触している: ' + i);
      for (let j = i + 1; j < spawnPoints.length; j++) {
        if (Math.hypot(spawnPoints[i].x - spawnPoints[j].x, spawnPoints[i].y - spawnPoints[j].y) < BALL_RADIUS * 2 - 0.01) {
          warnings.push('初期配置が重なっている: ' + i + '/' + j);
        }
      }
    }
    return warnings;
"""
if html.count(needle2) != 1:
    raise SystemExit(f'validator tail match count: {html.count(needle2)}')
html = html.replace(needle2, replacement2, 1)

needle3 = """  function spawnPosition(i) {
    const clusters = currentStage.spawnClusters || SPAWN_CLUSTERS;
    const spacing = currentStage.spawnSpacing || 17;
    const cluster = clusters[Math.floor(i / 10)];
    return { x: cluster.x + ((i % 5) - 2) * spacing, y: cluster.y + Math.floor((i % 10) / 5) * spacing };
  }
"""
replacement3 = """  function spawnPosition(i) {
    return stageSpawnPosition(currentStage, i);
  }
"""
if html.count(needle3) != 1:
    raise SystemExit(f'spawnPosition match count: {html.count(needle3)}')
html = html.replace(needle3, replacement3, 1)

script = re.search(r'<script>([\s\S]*?)</script>', html)
if not script:
    raise SystemExit('script tag not found')
Path('/tmp/tabakon-stage1-clearance.js').write_text(script.group(1), encoding='utf-8')
subprocess.run(['node', '--check', '/tmp/tabakon-stage1-clearance.js'], check=True)

index.write_text(html, encoding='utf-8')
for path in (workflow, self_path):
    if path.exists():
        path.unlink()
print('stage1 spawn clearance applied and syntax checked')
