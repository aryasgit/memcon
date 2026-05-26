# This adds the write panel to the existing ui.html
# Find the line: <div class="results" id="results"></div>
# and replace with the version below

python3 << 'PYEOF'
with open('api/ui.html', 'r') as f:
    content = f.read()

write_panel = '''
<div id="write-panel" style="display:none;margin-top:2rem">
  <div style="color:#00ff88;font-size:.7rem;letter-spacing:.1em;margin-bottom:1rem">// WRITE MEMORY</div>

  <div style="display:flex;gap:.5rem;margin-bottom:1rem;flex-wrap:wrap">
    <button class="mode-btn active" id="wt-debug" onclick="setWriteType('debug')">DEBUG SESSION</button>
    <button class="mode-btn" id="wt-decision" onclick="setWriteType('decision')">DECISION</button>
    <button class="mode-btn" id="wt-experiment" onclick="setWriteType('experiment')">EXPERIMENT</button>
    <button class="mode-btn" id="wt-session" onclick="setWriteType('session')">SESSION SUMMARY</button>
  </div>

  <div id="write-form"></div>
  <div id="write-result" style="margin-top:1rem;font-size:.8rem;color:#00ff88;display:none"></div>
</div>
'''

new_results = '<div class="results" id="results"></div>' + write_panel

content = content.replace('<div class="results" id="results"></div>', new_results)

# Add write mode toggle to the mode buttons
content = content.replace(
  '<button class="mode-btn" id="btn-search" onclick="setMode(\'search\')">SEARCH</button>',
  '<button class="mode-btn" id="btn-search" onclick="setMode(\'search\')">SEARCH</button>\n  <button class="mode-btn" id="btn-write" onclick="setMode(\'write\')">WRITE</button>'
)

# Add write JS before </script>
write_js = '''
let writeType = 'debug';

function setWriteType(t){
  writeType = t;
  ['debug','decision','experiment','session'].forEach(function(x){
    document.getElementById('wt-'+x).classList.toggle('active', x===t);
  });
  renderWriteForm();
}

function renderWriteForm(){
  const f = document.getElementById('write-form');
  const inp = 'style="width:100%;background:#111;border:1px solid #222;color:#e0e0e0;padding:.6rem;font-family:inherit;font-size:.83rem;margin-bottom:.5rem;outline:none" ';
  const ta = 'style="width:100%;background:#111;border:1px solid #222;color:#e0e0e0;padding:.6rem;font-family:inherit;font-size:.83rem;margin-bottom:.5rem;outline:none;resize:vertical;min-height:60px" ';

  const subsystemOpts = subsystems.map(function(s){
    return '<option value="'+s+'">'+s+'</option>';
  }).join('');

  const subSel = '<select id="w-subsystem" '+inp+'><option value="unknown">subsystem...</option>'+subsystemOpts+'</select>';

  if(writeType==='debug'){
    f.innerHTML =
      '<input id="w-title" '+inp+' placeholder="Title (e.g. RR Wrist Overheating)"/>' +
      '<textarea id="w-symptom" '+ta+' placeholder="Symptom — what happened?"></textarea>' +
      '<textarea id="w-cause" '+ta+' placeholder="Cause (optional)"></textarea>' +
      '<textarea id="w-fix" '+ta+' placeholder="Fix applied (optional)"></textarea>' +
      subSel +
      '<button class="go" onclick="submitWrite()" style="margin-top:.5rem">SAVE TO MEMORY →</button>';
  } else if(writeType==='decision'){
    f.innerHTML =
      '<input id="w-title" '+inp+' placeholder="Decision title"/>' +
      '<textarea id="w-decision" '+ta+' placeholder="What was decided?"></textarea>' +
      '<textarea id="w-reasoning" '+ta+' placeholder="Why? What trade-offs?"></textarea>' +
      subSel +
      '<button class="go" onclick="submitWrite()" style="margin-top:.5rem">SAVE TO MEMORY →</button>';
  } else if(writeType==='experiment'){
    f.innerHTML =
      '<input id="w-title" '+inp+' placeholder="Experiment title"/>' +
      '<textarea id="w-hypothesis" '+ta+' placeholder="Hypothesis"></textarea>' +
      '<textarea id="w-result" '+ta+' placeholder="Result"></textarea>' +
      '<textarea id="w-conclusion" '+ta+' placeholder="Conclusion"></textarea>' +
      subSel +
      '<button class="go" onclick="submitWrite()" style="margin-top:.5rem">SAVE TO MEMORY →</button>';
  } else if(writeType==='session'){
    f.innerHTML =
      '<textarea id="w-summary" '+ta+' style="min-height:120px" placeholder="What did you work on today? What did you learn? What broke? What was fixed?"></textarea>' +
      subSel +
      '<button class="go" onclick="submitWrite()" style="margin-top:.5rem">SAVE TO MEMORY →</button>';
  }
}

async function submitWrite(){
  const sub = document.getElementById('w-subsystem')?.value || 'unknown';
  const resEl = document.getElementById('write-result');
  let endpoint, body;

  if(writeType==='debug'){
    endpoint='/memory/debug';
    body={
      title: document.getElementById('w-title').value,
      symptom: document.getElementById('w-symptom').value,
      cause: document.getElementById('w-cause').value,
      fix: document.getElementById('w-fix').value,
      subsystem: sub, tags:[]
    };
  } else if(writeType==='decision'){
    endpoint='/memory/decision';
    body={
      title: document.getElementById('w-title').value,
      decision: document.getElementById('w-decision').value,
      reasoning: document.getElementById('w-reasoning').value,
      subsystem: sub, tags:[]
    };
  } else if(writeType==='experiment'){
    endpoint='/memory/experiment';
    body={
      title: document.getElementById('w-title').value,
      hypothesis: document.getElementById('w-hypothesis').value,
      result: document.getElementById('w-result').value,
      conclusion: document.getElementById('w-conclusion').value,
      subsystem: sub, tags:[]
    };
  } else if(writeType==='session'){
    endpoint='/memory/session';
    body={
      summary: document.getElementById('w-summary').value,
      subsystem: sub
    };
  }

  try{
    const r = await fetch(endpoint,{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify(body)
    });
    const d = await r.json();
    resEl.style.display='block';
    resEl.textContent = '✅ Saved to memory: ' + d.path;
    fetch('/stats').then(r=>r.json()).then(function(d){
      document.getElementById('s-chunks').textContent = d.total_chunks;
    });
  }catch(e){
    resEl.style.display='block';
    resEl.style.color='#ff4444';
    resEl.textContent = 'Error: ' + e.message;
  }
}

let subsystems = [];
'''

content = content.replace('let mode=\'ask\', activeSub=null;', write_js + "let mode='ask', activeSub=null;")

# Store subsystems globally when loaded
content = content.replace(
  "(conf.subsystems || []).forEach(function(s){",
  "subsystems = conf.subsystems || [];\n    (conf.subsystems || []).forEach(function(s){"
)

# Add write mode to setMode
content = content.replace(
  "function setMode(m){",
  """function setMode(m){
  document.getElementById('write-panel').style.display = m==='write' ? 'block' : 'none';
  document.getElementById('answer-box').style.display = 'none';
  document.getElementById('results').innerHTML = '';
  document.getElementById('btn-write').classList.toggle('active', m==='write');
  if(m==='write'){ renderWriteForm(); return; }"""
)

with open('api/ui.html', 'w') as f:
    f.write(content)

print("ui.html updated with write panel")
PYEOF