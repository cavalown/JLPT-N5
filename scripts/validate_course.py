"""Validate course structure and local links without third-party dependencies."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
HEADINGS = ['本課目標', '日文正文', '繁體中文翻譯', '重點單字與搭配', '核心語塊', '新文法解析', '舊知識回顧', '理解題', '造句／改寫練習', '學習後問題與訂正']
errors = []
total = 0

def require(ok, message):
    if not ok:
        errors.append(message)

def section(text, name):
    return text.split('## ' + name + '\n', 1)[1].split('\n## ', 1)[0]

lessons = sorted((ROOT / 'lessons/n5').glob('day-*.md'))
require(len(lessons) == 30, 'Expected 30 lessons')
for day in range(1, 31):
    path = ROOT / f'lessons/n5/day-{day:02d}.md'
    answer = ROOT / f'lessons/n5/answers/day-{day:02d}.md'
    require(path.exists() and answer.exists(), f'Day {day}: missing lesson or answer')
    if not path.exists() or not answer.exists():
        continue
    text = path.read_text()
    headers = re.findall(r'^## (.+)$', text, re.M)
    require(headers == HEADINGS, f'Day {day}: section structure differs')
    if headers != HEADINGS:
        continue
    body = section(text, '日文正文')
    translation = section(text, '繁體中文翻譯')
    body_nums = re.findall(r'^(\d+)\. ', body, re.M)
    translation_nums = re.findall(r'^(\d+)\. ', translation, re.M)
    require(10 <= len(body_nums) <= 12, f'Day {day}: sentence count {len(body_nums)}')
    require(body_nums == [str(n) for n in range(1, len(body_nums) + 1)], f'Day {day}: numbering')
    require(translation_nums == body_nums, f'Day {day}: translation alignment')
    require(body.count('。') == len(body_nums), f'Day {day}: one complete sentence per body item')
    total += len(body_nums)
    exercises = section(text, '理解題') + section(text, '造句／改寫練習')
    require(re.findall(r'^(\d+)\. ', exercises, re.M) == list(map(str, range(1, 9))), f'Day {day}: expected questions 1–8')
    require(re.findall(r'^## 第(\d+)題$', answer.read_text(), re.M) == list(map(str, range(1, 9))), f'Day {day}: expected answers 1–8')
    require('<details' not in text and '參考答案：' not in exercises, f'Day {day}: answer content in lesson')
    require(f'(answers/day-{day:02d}.md)' in text, f'Day {day}: missing answer link')
    # Student-owned section may later contain real entries; creation-time QA checks it separately.
    groups = len(re.findall(r'^### ', section(text, '新文法解析'), re.M))
    require(1 <= groups <= 3, f'Day {day}: grammar group count {groups}')
require(330 <= total <= 360, f'Total sentence count {total}')

# Check local Markdown links and our explicit sentence / grammar anchors.
for path in ROOT.rglob('*.md'):
    if any(part in {'.git', '.codex', '.agents', 'node_modules'} for part in path.parts):
        continue
    text = path.read_text()
    explicit_ids = re.findall(r'<a id="([^"]+)"', text)
    require(len(explicit_ids) == len(set(explicit_ids)), f'{path.relative_to(ROOT)}: duplicate anchor')
    for link in re.findall(r'\]\(([^)]+)\)', text):
        if re.match(r'^[a-z]+://', link):
            continue
        dest, _, anchor = link.partition('#')
        target = path.parent / dest if dest else path
        require(target.exists(), f'{path.relative_to(ROOT)}: missing target {link}')
        if target.exists() and anchor and (anchor.startswith('s') or anchor.startswith('g-')):
            require(f'id="{anchor}"' in target.read_text(), f'{path.relative_to(ROOT)}: missing anchor {link}')

# Current skill metadata is intentionally simple: only name and plain-text description.
for path in (ROOT / 'skills').glob('*/SKILL.md'):
    text = path.read_text()
    front = re.match(r'^---\nname: ([a-z0-9-]+)\ndescription: ([^\n]+)\n---\n', text)
    require(bool(front), f'{path}: invalid simple skill frontmatter')
    if front:
        require(front.group(1) == path.parent.name, f'{path}: name differs from directory')
    require('[TODO:' not in text, f'{path}: unfinished scaffold')

if errors:
    raise SystemExit('\n'.join(errors))
print(f'PASS: {len(lessons)} lessons, {total} body sentences, 240 questions, 30 answer files; local links and skill metadata valid.')
