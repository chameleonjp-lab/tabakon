from pathlib import Path
import re
import subprocess

INDEX = Path('index.html')
WORKFLOW = Path('.github/workflows/apply-offset-goals.yml')
SELF = Path('tools/apply_offset_goals.py')


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f'{label}: expected exactly one match, got {count}')
    return text.replace(old, new, 1)


html = INDEX.read_text(encoding='utf-8')

html = replace_once(
    html,
    '<li>60秒以内に高スコアを狙います。</li><li>ステージ1では3つの室から最低2室を開放し、中層で左右へ振ってから中央へ戻します。</li><li>ステージは10種類から開始ごとにランダムで選ばれます。</li>',
    '<li>60秒以内に高スコアを狙います。</li><li>狐はステージごとに左端または右端へ現れます。中段の開口とは反対側へ誘導して届けます。</li><li>ステージ1では3つの室から最低2室を開放します。</li><li>ステージは10種類から開始ごとにランダムで選ばれます。</li>',
    'rule text',
)

common = """  const COMMON_WALLS = [
    { kind: 'wall', x: 0, y: 0, w: 2, h: 144 },
    { kind: 'wall', x: 46, y: 0, w: 2, h: 144 },
    { kind: 'wall', x: 0, y: 142, w: 48, h: 2 }
  ];
"""
helpers = common + """  function barrierWithOpening(y, openX, openWidth = 8) {
    const leftWidth = openX - 2;
    const rightX = openX + openWidth;
    const rightWidth = 46 - rightX;
    return [
      leftWidth > 0 ? { kind: 'wall', x: 2, y, w: leftWidth, h: 2 } : null,
      rightWidth > 0 ? { kind: 'wall', x: rightX, y, w: rightWidth, h: 2 } : null
    ].filter(Boolean);
  }
  function routeOpenings(goalSide) {
    return goalSide === 'left'
      ? { goalSide: 'left', goalX: 28, midOpenX: 34, finalOpenX: 6, openWidth: 8, midY: 68, finalY: 112 }
      : { goalSide: 'right', goalX: 176, midOpenX: 6, finalOpenX: 34, openWidth: 8, midY: 68, finalY: 112 };
  }
  function legacyGoalSide(variant) {
    return [2, 5, 7, 9].includes(variant) ? 'left' : 'right';
  }
"""
html = replace_once(html, common, helpers, 'route helpers')

html = replace_once(
    html,
    "  function makeStageOne() {\n    return {",
    "  function makeStageOne() {\n    const route = { ...routeOpenings('right'), midY: 66, finalY: 102 };\n    return {",
    'stage1 route declaration',
)
html = replace_once(
    html,
    "      strategyHint: '2室以上を開けよう　左=安全 / 中央=速攻 / 右=高得点',",
    "      strategyHint: '2室以上を開け、左へ振ってから右の狐へ',",
    'stage1 hint',
)
html = replace_once(
    html,
    "      spawnSpacing: 16,\n      typePlan: [...STAGE1_TYPE_PLAN],",
    "      spawnSpacing: 16,\n      routePattern: route,\n      typePlan: [...STAGE1_TYPE_PLAN],",
    'stage1 route metadata',
)
html = replace_once(
    html,
    "        { kind: 'wall', x: 2, y: 66, w: 6, h: 2 },\n        { kind: 'wall', x: 14, y: 66, w: 20, h: 2 },\n        { kind: 'wall', x: 40, y: 66, w: 6, h: 2 },",
    "        ...barrierWithOpening(route.midY, route.midOpenX, route.openWidth),",
    'stage1 mid barrier',
)
html = replace_once(
    html,
    "        { kind: 'wall', x: 2, y: 102, w: 19, h: 2 },\n        { kind: 'wall', x: 27, y: 102, w: 19, h: 2 },",
    "        ...barrierWithOpening(route.finalY, route.finalOpenX, route.openWidth),",
    'stage1 final barrier',
)
html = replace_once(
    html,
    "        { x: 24, y: 119, rx: 50, ry: 86 }",
    "        { x: route.finalOpenX + route.openWidth / 2, y: 119, rx: 42, ry: 86 }",
    'stage1 final carve',
)
html = replace_once(
    html,
    "      goal: { x: 104, y: 840, w: 116, h: 68 },",
    "      goal: { x: route.goalX, y: 840, w: 116, h: 68 },",
    'stage1 goal',
)
html = replace_once(
    html,
    "        { x: 96, y: 420, w: 128, text: '← 左か右へ →', tone: 'decision' },\n        { x: 100, y: 676, w: 120, text: '中央へ戻す', tone: 'decision' }",
    "        { x: 20, y: 420, w: 110, text: '← まず左へ', tone: 'decision' },\n        { x: 188, y: 676, w: 112, text: '右の狐へ →', tone: 'decision' }",
    'stage1 route hints',
)

html = replace_once(
    html,
    "  function makeStage(name, shortName, variant) {\n    const leftGoal = variant % 3 === 0;\n    const rightRisk = variant % 2 === 0;\n    const goalX = leftGoal ? 92 : variant % 3 === 1 ? 104 : 124;",
    "  function makeStage(name, shortName, variant) {\n    const route = routeOpenings(legacyGoalSide(variant));\n    const rightRisk = variant % 2 === 0;\n    const goalX = route.goalX;",
    'legacy route declaration',
)
html = replace_once(
    html,
    "      { kind: 'wall', x: 12, y: 68, w: 7, h: 2 },\n      { kind: 'wall', x: 30, y: 68, w: 8, h: 2 },\n      { kind: 'wall', x: 4, y: 112, w: 10, h: 2 },\n      { kind: 'wall', x: 34, y: 112, w: 10, h: 2 }",
    "      ...barrierWithOpening(route.midY, route.midOpenX, route.openWidth),\n      ...barrierWithOpening(route.finalY, route.finalOpenX, route.openWidth)",
    'legacy zigzag barriers',
)
html = replace_once(
    html,
    "      { x: rightRisk ? 37 : 11, y: 88, rx: 26, ry: 90 }, { x: 24, y: 96, rx: variant === 7 ? 16 : 34, ry: 94 },\n      { x: Math.round((goalX + 64) / CELL_W), y: 124, rx: 58, ry: 36 }",
    "      { x: route.midOpenX + route.openWidth / 2, y: 86, rx: 28, ry: 58 },\n      { x: 24, y: 94, rx: variant === 7 ? 16 : 24, ry: 34 },\n      { x: route.finalOpenX + route.openWidth / 2, y: 122, rx: 42, ry: 62 }",
    'legacy route carves',
)
html = replace_once(
    html,
    "    return { id: 'legacy-' + variant, name, shortName, rects, carves, traps, mechanisms, goal: { x: goalX, y: 840, w: leftGoal ? 128 : 116, h: 68 } };",
    "    const leftGoal = route.goalSide === 'left';\n    const routeHints = leftGoal\n      ? [\n          { x: 190, y: 430, w: 110, text: 'まず右へ →', tone: 'decision' },\n          { x: 18, y: 690, w: 112, text: '← 左の狐へ', tone: 'decision' }\n        ]\n      : [\n          { x: 18, y: 430, w: 112, text: '← まず左へ', tone: 'decision' },\n          { x: 188, y: 690, w: 112, text: '右の狐へ →', tone: 'decision' }\n        ];\n    return {\n      id: 'legacy-' + variant, name, shortName, rects, carves, traps, mechanisms,\n      routePattern: route,\n      strategyHint: leftGoal ? '中段で右へ振り、最後は左の狐へ' : '中段で左へ振り、最後は右の狐へ',\n      routeHints,\n      goal: { x: goalX, y: 840, w: 116, h: 68 }\n    };",
    'legacy return metadata',
)

stage_wall = """  function stageHasWallAt(stage, x, y) {
    return stage.rects.some(r => r.kind === 'wall' && x >= r.x && x < r.x + r.w && y >= r.y && y < r.y + r.h);
  }
"""
validators = stage_wall + """  function barrierMatchesOpening(stage, y, openX, openWidth) {
    for (let x = 2; x < 46; x++) {
      const shouldBeWall = x < openX || x >= openX + openWidth;
      if (stageHasWallAt(stage, x, y) !== shouldBeWall) return false;
    }
    return true;
  }
  function validateOffsetGoal(stage) {
    const warnings = [];
    const route = stage.routePattern;
    if (!route) return ['左右ゴール用routePatternがない: ' + stage.name];
    const goalCenter = stage.goal.x + stage.goal.w / 2;
    if (goalCenter >= 120 && goalCenter <= 200) warnings.push('狐が中央帯に残っている: ' + stage.name);
    const actualSide = goalCenter < VIEW_W / 2 ? 'left' : 'right';
    if (route.goalSide !== actualSide) warnings.push('routePatternと狐の左右が一致しない: ' + stage.name);
    if (route.midOpenX === route.finalOpenX) warnings.push('中段と最終開口が同じ側: ' + stage.name);
    if (!barrierMatchesOpening(stage, route.midY, route.midOpenX, route.openWidth)) warnings.push('中段障壁が指定開口と一致しない: ' + stage.name);
    if (!barrierMatchesOpening(stage, route.finalY, route.finalOpenX, route.openWidth)) warnings.push('最終障壁が指定開口と一致しない: ' + stage.name);
    const finalCenter = route.finalOpenX + route.openWidth / 2;
    if ((actualSide === 'left' && finalCenter >= 24) || (actualSide === 'right' && finalCenter <= 24)) warnings.push('最終開口が狐と反対側: ' + stage.name);
    return warnings;
  }
"""
html = replace_once(html, stage_wall, validators, 'offset validators')

html = replace_once(
    html,
    "    if (!stageHasWallAt(stage, 24, 66)) warnings.push('第2障壁の中央が開いている');\n    if (stageHasWallAt(stage, 24, 102)) warnings.push('第3障壁の中央開口が塞がっている');\n    for (const x of [8, 27, 40]) if (stageHasWallAt(stage, x, 34)) warnings.push('第1障壁の室別出口が塞がっている: ' + x);\n    for (const x of [10, 36]) if (stageHasWallAt(stage, x, 66)) warnings.push('第2障壁の左右開口が塞がっている: ' + x);",
    "    for (const x of [8, 27, 40]) if (stageHasWallAt(stage, x, 34)) warnings.push('第1障壁の室別出口が塞がっている: ' + x);",
    'stage1 old barrier checks',
)
html = replace_once(
    html,
    "    const warnings = STAGES.flatMap(stage => [...validateStageGoalAccess(stage), ...validateStageOneStrategy(stage)]);",
    "    const warnings = STAGES.flatMap(stage => [...validateStageGoalAccess(stage), ...validateStageOneStrategy(stage), ...validateOffsetGoal(stage)]);",
    'validate all stages',
)

html = replace_once(
    html,
    "  function drawGoal() {\n    ctx.fillStyle = 'rgba(73,158,95,.26)'; roundRect(goal.x, goal.y, goal.w, goal.h, 12, true);\n    ctx.strokeStyle = '#2f8f68'; ctx.lineWidth = 3; roundRect(goal.x + 2, goal.y + 2, goal.w - 4, goal.h - 4, 10, false, true);\n    ctx.font = '36px serif'; ctx.fillText('🦊', goal.x + 29, goal.y + 38);\n  }",
    "  function drawGoal() {\n    ctx.fillStyle = 'rgba(73,158,95,.26)'; roundRect(goal.x, goal.y, goal.w, goal.h, 12, true);\n    ctx.strokeStyle = '#2f8f68'; ctx.lineWidth = 3; roundRect(goal.x + 2, goal.y + 2, goal.w - 4, goal.h - 4, 10, false, true);\n    ctx.save();\n    ctx.font = '36px serif';\n    ctx.textAlign = 'center';\n    ctx.textBaseline = 'middle';\n    ctx.fillText('🦊', goal.x + goal.w / 2, goal.y + goal.h / 2 + 2);\n    ctx.restore();\n  }",
    'center fox in goal',
)

script = re.search(r'<script>([\s\S]*?)</script>', html)
if not script:
    raise RuntimeError('script tag not found')
Path('/tmp/tabakon-offset-goals.js').write_text(script.group(1), encoding='utf-8')
subprocess.run(['node', '--check', '/tmp/tabakon-offset-goals.js'], check=True)

INDEX.write_text(html, encoding='utf-8')
for path in (WORKFLOW, SELF):
    if path.exists():
        path.unlink()

print('offset goals and zigzag barriers applied')
