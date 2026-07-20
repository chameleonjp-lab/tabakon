from pathlib import Path
import re
import subprocess

INDEX = Path('index.html')
WORKFLOW = Path('.github/workflows/enable-stage-review-selection.yml')
SELF = Path('tools/enable_stage_review_selection.py')


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f'{label}: expected one match, got {count}')
    return text.replace(old, new, 1)

html = INDEX.read_text(encoding='utf-8')
html = replace_once(
    html,
    """  function selectStage() {
    const requested = new URLSearchParams(location.search).get('stage');
    if (requested === '1') return STAGES[0];
    return STAGES[Math.floor(Math.random() * STAGES.length)];
  }
""",
    """  function selectStage() {
    const requested = new URLSearchParams(location.search).get('stage');
    const stageNumber = Number.parseInt(requested || '', 10);
    if (Number.isInteger(stageNumber) && stageNumber >= 1 && stageNumber <= STAGES.length) return STAGES[stageNumber - 1];
    return STAGES[Math.floor(Math.random() * STAGES.length)];
  }
""",
    'selectStage',
)
script = re.search(r'<script>([\s\S]*?)</script>', html)
if not script:
    raise RuntimeError('script tag not found')
Path('/tmp/tabakon-stage-review-selector.js').write_text(script.group(1), encoding='utf-8')
subprocess.run(['node', '--check', '/tmp/tabakon-stage-review-selector.js'], check=True)
INDEX.write_text(html, encoding='utf-8')

for doc_name in ('docs/OFFSET_GOAL_ZIGZAG_SPEC.md', 'docs/STAGE1_CORE_GAMEPLAY_SPEC.md', 'docs/REVIEW_CHECKLIST.md'):
    path = Path(doc_name)
    text = path.read_text(encoding='utf-8')
    if doc_name.endswith('OFFSET_GOAL_ZIGZAG_SPEC.md'):
        marker = '## 10. 実機合格条件\n'
        addition = """## 10. レビュー用ステージ固定

`?stage=1`から`?stage=10`までを指定すると、その番号のステージを固定選択できる。

例:

- `?stage=1`: 三室の選択
- `?stage=2`: 左安全路
- `?stage=9`: 回転障害物
- `?stage=10`: 総合

指定なし、範囲外、数値以外の場合は通常どおりランダム選択する。

## 11. 実機合格条件
"""
        text = replace_once(text, marker, addition, 'offset spec review selector')
        text = text.replace('## 11. 未解決', '## 12. 未解決', 1)
    elif doc_name.endswith('STAGE1_CORE_GAMEPLAY_SPEC.md'):
        text = replace_once(
            text,
            '`?stage=1`を付けた場合だけステージ1を固定選択できる。通常URLでは10種類からランダム選択する。',
            '`?stage=1`でステージ1を固定選択できる。レビュー用途では`?stage=1`〜`?stage=10`で各ステージを固定でき、指定なし・不正値では通常どおりランダム選択する。',
            'stage1 review selector docs',
        )
    else:
        marker = '- [ ] `validateOffsetGoal()`の警告が0\n'
        text = replace_once(text, marker, marker + '- [ ] `?stage=1`〜`?stage=10`で各ステージを固定選択できる\n- [ ] 範囲外・不正値ではランダム選択へ戻る\n', 'review selector checklist')
    path.write_text(text, encoding='utf-8')

for path in (WORKFLOW, SELF):
    if path.exists():
        path.unlink()
print('stage review selection enabled and syntax checked')
