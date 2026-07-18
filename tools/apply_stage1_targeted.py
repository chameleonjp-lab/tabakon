from pathlib import Path
import re
import subprocess

BASE_SHA = "88bfc09cd756f2920e4b642ebbbdef205c552baa"
INDEX = Path("index.html")
WORKFLOW = Path(".github/workflows/apply-stage1-targeted.yml")
SELF = Path("tools/apply_stage1_targeted.py")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, got {count}")
    return text.replace(old, new, 1)


def regex_once(text: str, pattern: str, replacement: str, label: str) -> str:
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.S)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, got {count}")
    return updated


html = subprocess.check_output(["git", "show", f"{BASE_SHA}:index.html"], text=True)

html = replace_once(
    html,
    "<li>60秒以内に高スコアを狙います。</li><li>ステージは10種類から開始ごとにランダムで選ばれます。</li>",
    "<li>60秒以内に高スコアを狙います。</li><li>ステージ1では3つの室から最低2室を開放し、中層で左右へ振ってから中央へ戻します。</li><li>ステージは10種類から開始ごとにランダムで選ばれます。</li>",
    "rule text",
)

plans = """  const DEFAULT_TYPE_PLAN = ['normal','normal','normal','normal','normal','normal','normal','normal','normal','normal','red','blue','normal','red','blue','normal','red','blue','normal','black','normal','red','blue','normal','red','blue','normal','black','normal','black'];
  const STAGE1_TYPE_PLAN = ['normal','normal','normal','normal','normal','normal','normal','normal','normal','normal','red','blue','red','blue','red','blue','red','blue','red','blue','black','red','black','red','blue','black','red','black','red','blue'];
"""
html = replace_once(html, "  };\n  const BAD_COMMENT", "  };\n" + plans + "  const BAD_COMMENT", "type plans")

stage_block = r"""  // 4. ステージ定義（P0-C: ステージ1のみ個別再設計）
  const COMMON_WALLS = [
    { kind: 'wall', x: 0, y: 0, w: 2, h: 144 },
    { kind: 'wall', x: 46, y: 0, w: 2, h: 144 },
    { kind: 'wall', x: 0, y: 142, w: 48, h: 2 }
  ];
  function makeStageOne() {
    return {
      id: 'stage1-strategy', strategy: true,
      name: 'ステージ1：三室の選択', shortName: '三室の選択',
      strategyHint: '2室以上を開けよう　左=安全 / 中央=速攻 / 右=高得点',
      spawnClusters: [{ x: 64, y: 48 }, { x: 166, y: 48 }, { x: 264, y: 48 }],
      spawnSpacing: 16,
      typePlan: [...STAGE1_TYPE_PLAN],
      rects: [
        ...COMMON_WALLS,
        { kind: 'wall', x: 17, y: 0, w: 2, h: 36 },
        { kind: 'wall', x: 31, y: 0, w: 2, h: 36 },
        { kind: 'sand', x: 2, y: 12, w: 15, h: 22 },
        { kind: 'sand', x: 19, y: 12, w: 12, h: 22 },
        { kind: 'sand', x: 33, y: 12, w: 13, h: 22 },
        { kind: 'wall', x: 2, y: 34, w: 4, h: 2 },
        { kind: 'wall', x: 11, y: 34, w: 14, h: 2 },
        { kind: 'wall', x: 30, y: 34, w: 8, h: 2 },
        { kind: 'wall', x: 43, y: 34, w: 3, h: 2 },
        { kind: 'sand', x: 2, y: 36, w: 44, h: 30 },
        { kind: 'wall', x: 2, y: 66, w: 6, h: 2 },
        { kind: 'wall', x: 14, y: 66, w: 20, h: 2 },
        { kind: 'wall', x: 40, y: 66, w: 6, h: 2 },
        { kind: 'sand', x: 2, y: 68, w: 44, h: 34 },
        { kind: 'wall', x: 2, y: 102, w: 19, h: 2 },
        { kind: 'wall', x: 27, y: 102, w: 19, h: 2 },
        { kind: 'sand', x: 2, y: 104, w: 44, h: 28 }
      ],
      carves: [
        { x: 8, y: 27, rx: 28, ry: 48 },
        { x: 27, y: 27, rx: 18, ry: 48 },
        { x: 40, y: 27, rx: 28, ry: 48 },
        { x: 9, y: 51, rx: 32, ry: 72 },
        { x: 26, y: 51, rx: 22, ry: 66 },
        { x: 39, y: 51, rx: 30, ry: 72 },
        { x: 11, y: 85, rx: 38, ry: 82 },
        { x: 37, y: 85, rx: 38, ry: 82 },
        { x: 24, y: 119, rx: 50, ry: 86 }
      ],
      traps: [
        { x: 260, y: 305, w: 38, h: 30, type: 'danger' },
        { x: 268, y: 548, w: 34, h: 34, type: 'swamp' }
      ],
      mechanisms: [
        { kind: 'gate', x: 152, y: 300, w: 15, h: 72, t: 0, open: false },
        { kind: 'bar', x: 44, y: 505, w: 86, h: 10, min: 36, max: 146, speed: 30, dir: 1 },
        { kind: 'rotor', x: 252, y: 610, len: 66, angle: 0.3, speed: 1.65 }
      ],
      goal: { x: 104, y: 840, w: 116, h: 68 },
      routeHints: [
        { x: 22, y: 10, w: 84, text: '安全　白', tone: 'safe' },
        { x: 124, y: 10, w: 84, text: '速攻　赤青', tone: 'fast' },
        { x: 218, y: 10, w: 88, text: '高得点　黒', tone: 'score' },
        { x: 96, y: 420, w: 128, text: '← 左か右へ →', tone: 'decision' },
        { x: 100, y: 676, w: 120, text: '中央へ戻す', tone: 'decision' }
      ]
    };
  }
  function makeStage(name, shortName, variant) {
    const leftGoal = variant % 3 === 0;
    const rightRisk = variant % 2 === 0;
    const goalX = leftGoal ? 92 : variant % 3 === 1 ? 104 : 124;
    const rects = [
      ...COMMON_WALLS,
      { kind: 'sand', x: 2, y: 12, w: 44, h: 20 },
      { kind: 'sand', x: 3, y: 38, w: 15, h: 34 },
      { kind: 'sand', x: 18, y: 36, w: 12, h: 36 },
      { kind: 'sand', x: 31, y: 38, w: 13, h: 34 },
      { kind: 'sand', x: 4, y: 76, w: 16, h: 34 },
      { kind: 'sand', x: 20, y: 74, w: 9, h: 38 },
      { kind: 'sand', x: 30, y: 76, w: 14, h: 34 },
      { kind: 'sand', x: 8, y: 116, w: 32, h: 18 },
      { kind: 'wall', x: 2, y: 34 + (variant % 3), w: 10, h: 2 },
      { kind: 'wall', x: 34, y: 34 + (variant % 4), w: 12, h: 2 },
      { kind: 'wall', x: 12, y: 68, w: 7, h: 2 },
      { kind: 'wall', x: 30, y: 68, w: 8, h: 2 },
      { kind: 'wall', x: 4, y: 112, w: 10, h: 2 },
      { kind: 'wall', x: 34, y: 112, w: 10, h: 2 }
    ];
    if (variant === 7) rects.push({ kind: 'wall', x: 22, y: 94, w: 4, h: 28 });
    const carves = [
      { x: 11, y: 14, rx: 30, ry: 14 }, { x: 24, y: 14, rx: 32, ry: 14 }, { x: 37, y: 14, rx: 30, ry: 14 },
      { x: 10, y: 50, rx: 28, ry: 84 }, { x: 24, y: 51, rx: 22, ry: 82 }, { x: 38, y: 50, rx: 28, ry: 84 },
      { x: rightRisk ? 37 : 11, y: 88, rx: 26, ry: 90 }, { x: 24, y: 96, rx: variant === 7 ? 16 : 34, ry: 94 },
      { x: Math.round((goalX + 64) / CELL_W), y: 124, rx: 58, ry: 36 }
    ];
    const traps = [
      { x: rightRisk ? 236 : 24, y: 330 + variant * 6, w: 62, h: 30, type: 'danger' },
      { x: rightRisk ? 220 : 36, y: 560 + (variant % 4) * 16, w: 64, h: 34, type: variant % 2 ? 'swamp' : 'danger' },
      { x: variant % 2 ? 244 : 28, y: 725, w: 52, h: 26, type: 'pit' }
    ];
    const mechanisms = [
      { kind: 'bar', x: 62 + (variant % 5) * 10, y: 285 + variant * 4, w: 90, h: 10, min: 46, max: 214, speed: 32 + variant * 2, dir: 1 },
      { kind: 'gate', x: 150 + (variant % 3) * 4, y: 545 + (variant % 4) * 12, w: 15, h: 76, t: 0, open: false }
    ];
    if (variant === 4 || variant === 9 || variant === 10) mechanisms.push({ kind: 'rotor', x: 236, y: 610, len: 76, angle: 0.2, speed: 1.8 });
    if (variant === 5 || variant === 10) mechanisms.push({ kind: 'bar', x: 150, y: 678, w: 92, h: 10, min: 108, max: 270, speed: 40, dir: -1 });
    if (variant === 9) mechanisms.push({ kind: 'rotor', x: 150, y: 700, len: 86, angle: -0.3, speed: -1.9 });
    return { id: 'legacy-' + variant, name, shortName, rects, carves, traps, mechanisms, goal: { x: goalX, y: 840, w: leftGoal ? 128 : 116, h: 68 } };
  }
  const STAGES = [
    makeStageOne(),
    makeStage('ステージ2：左安全路', '左安全路', 2),
    makeStage('ステージ3：中央ゲート', '中央ゲート', 3),
    makeStage('ステージ4：右高得点路', '右高得点路', 4),
    makeStage('ステージ5：二段バー', '二段バー', 5),
    makeStage('ステージ6：広い受け皿', '広い受け皿', 6),
    makeStage('ステージ7：細い通路', '細い通路', 7),
    makeStage('ステージ8：危険サンド', '危険サンド', 8),
    makeStage('ステージ9：回転障害物', '回転障害物', 9),
    makeStage('ステージ10：総合', '総合', 10)
  ];

  function rectToWorld"""
html = regex_once(
    html,
    r"  // 4\. ステージ定義.*?\n  function rectToWorld",
    stage_block,
    "stage block",
)

validation_block = r"""  function stageHasWallAt(stage, x, y) {
    return stage.rects.some(r => r.kind === 'wall' && x >= r.x && x < r.x + r.w && y >= r.y && y < r.y + r.h);
  }
  function countTypes(list) {
    return list.reduce((acc, type) => { acc[type] = (acc[type] || 0) + 1; return acc; }, {});
  }
  function validateStageOneStrategy(stage) {
    if (!stage.strategy) return [];
    const warnings = [];
    if (!Array.isArray(stage.typePlan) || stage.typePlan.length !== 30) warnings.push('ステージ1のtypePlanは30件必要');
    const left = countTypes((stage.typePlan || []).slice(0, 10));
    const middle = countTypes((stage.typePlan || []).slice(10, 20));
    const right = countTypes((stage.typePlan || []).slice(20, 30));
    if (left.normal !== 10) warnings.push('左室は白10個である必要');
    if (middle.red !== 5 || middle.blue !== 5) warnings.push('中央室は赤5・青5である必要');
    if (right.black !== 4 || right.red !== 4 || right.blue !== 2) warnings.push('右室は黒4・赤4・青2である必要');
    if (!stageHasWallAt(stage, 17, 10) || !stageHasWallAt(stage, 31, 10)) warnings.push('上層の室仕切りが不足');
    if (!stageHasWallAt(stage, 24, 66)) warnings.push('第2障壁の中央が開いている');
    if (stageHasWallAt(stage, 24, 102)) warnings.push('第3障壁の中央開口が塞がっている');
    for (const x of [8, 27, 40]) if (stageHasWallAt(stage, x, 34)) warnings.push('第1障壁の室別出口が塞がっている: ' + x);
    for (const x of [10, 36]) if (stageHasWallAt(stage, x, 66)) warnings.push('第2障壁の左右開口が塞がっている: ' + x);
    return warnings;
  }
  function validateAllStages() {
    const warnings = STAGES.flatMap(stage => [...validateStageGoalAccess(stage), ...validateStageOneStrategy(stage)]);
    if (warnings.length) console.warn('[tabakon] stage warnings', warnings);
    return warnings;
  }
  validateAllStages();
  function selectStage() {
    const requested = new URLSearchParams(location.search).get('stage');
    if (requested === '1') return STAGES[0];
    return STAGES[Math.floor(Math.random() * STAGES.length)];
  }
"""
html = regex_once(
    html,
    r"  function validateAllStages\(\) \{.*?\n  validateAllStages\(\);\n",
    validation_block,
    "stage validation",
)

html = replace_once(html, "    currentStage = STAGES[Math.floor(Math.random() * STAGES.length)];", "    currentStage = selectStage();", "stage selection")
html = regex_once(
    html,
    r"  function spawnPosition\(i\) \{.*?\n  \}",
    """  function spawnPosition(i) {
    const clusters = currentStage.spawnClusters || SPAWN_CLUSTERS;
    const spacing = currentStage.spawnSpacing || 17;
    const cluster = clusters[Math.floor(i / 10)];
    return { x: cluster.x + ((i % 5) - 2) * spacing, y: cluster.y + Math.floor((i % 10) / 5) * spacing };
  }""",
    "stage spawn positions",
)
html = regex_once(
    html,
    r"    const typePlan = \['normal'.*?\];",
    "    const typePlan = currentStage.typePlan || DEFAULT_TYPE_PLAN;",
    "stage type plan",
)
html = replace_once(html, "        id: i, x: p.x,", "        id: i, room: Math.floor(i / 10), x: p.x,", "room metadata")
html = replace_once(html, "    drawGrid(); drawBrightMarks();", "    drawGrid(); drawRouteHints(); drawBrightMarks();", "route hint draw order")

route_hints = r"""  function drawRouteHints() {
    const palette = {
      safe: ['#237b64', '#fff'],
      fast: ['#21537a', '#fff'],
      score: ['#6b255f', '#fff'],
      decision: ['#fff7a8', '#4d321d']
    };
    for (const hint of currentStage.routeHints || []) {
      if (!isNearView(hint.y, 22)) continue;
      const colors = palette[hint.tone] || palette.decision;
      ctx.save();
      ctx.globalAlpha = 0.94;
      ctx.fillStyle = colors[0];
      roundRect(hint.x, hint.y, hint.w, 20, 7, true);
      ctx.strokeStyle = 'rgba(255,255,255,.8)';
      ctx.lineWidth = 1.5;
      roundRect(hint.x + 1, hint.y + 1, hint.w - 2, 18, 6, false, true);
      ctx.fillStyle = colors[1];
      ctx.font = 'bold 11px sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(hint.text, hint.x + hint.w / 2, hint.y + 10);
      ctx.restore();
    }
    ctx.textAlign = 'start';
    ctx.textBaseline = 'alphabetic';
  }
"""
html = replace_once(html, "  function drawBrightMarks() {", route_hints + "  function drawBrightMarks() {", "route hint function")

html = replace_once(
    html,
    "    $('stageHud').textContent = 'ステージ：' + currentStage.shortName + '　左バーで上下を見る / 砂を削って🚬を🦊へ届けよう';\n    $('statusHud').textContent = '失った ' + lost + '個　危険ゾーンと最下部に注意';",
    "    $('stageHud').textContent = 'ステージ：' + currentStage.shortName + '　左バーで上下を見る';\n    $('statusHud').textContent = currentStage.strategyHint || ('失った ' + lost + '個　危険ゾーンと最下部に注意');",
    "stage strategy HUD",
)

html = replace_once(
    html,
    "    getState: () => state,\n    getPhysics:",
    "    getState: () => state,\n    getStage: () => currentStage.id || currentStage.name,\n    getPhysics:",
    "debug stage getter",
)
html = replace_once(
    html,
    "    finishGame, resetGame, showError, validateAllStages, validateStageGoalAccess",
    "    finishGame, resetGame, showError, validateAllStages, validateStageGoalAccess, validateStageOneStrategy",
    "debug strategy validator",
)

required = [
    "makeStageOne()",
    "stageHasWallAt(stage, 24, 66)",
    "stageHasWallAt(stage, 24, 102)",
    "currentStage = selectStage();",
    "currentStage.typePlan || DEFAULT_TYPE_PLAN",
    "drawRouteHints();",
    "new URLSearchParams(location.search).get('stage')",
    "/rest/v1/rpc/submit_score",
    "/rest/v1/rpc/get_best_score_ranking",
]
for token in required:
    if token not in html:
        raise RuntimeError(f"required token missing: {token}")

script_match = re.search(r"<script>([\s\S]*?)</script>", html)
if not script_match:
    raise RuntimeError("script tag not found")
Path("/tmp/tabakon-stage1.js").write_text(script_match.group(1), encoding="utf-8")
subprocess.run(["node", "--check", "/tmp/tabakon-stage1.js"], check=True)

INDEX.write_text(html, encoding="utf-8")
for path in (WORKFLOW, SELF):
    if path.exists():
        path.unlink()
print("targeted stage1 patch applied and syntax checked")
