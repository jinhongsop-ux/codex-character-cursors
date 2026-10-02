const $ = selector => document.querySelector(selector);
const roles = ['Arrow','Help','AppStarting','Wait','Crosshair','IBeam','NWPen','No','SizeAll','SizeWE','SizeNESW','UpArrow','SizeNS','SizeNWSE','Hand','Extra'];
const labels = ['普通选择','帮助选择','后台工作','忙碌等待','精确选择','文本选择','手写','不可用','移动','水平调整','斜向 ↗↙','候选选择','垂直调整','斜向 ↖↘','链接选择','额外状态'];
const characterImages = { reze: 'reze', rem: 'rem', deepseek: 'deepseek', pochita: 'pochita', pinkhorn: 'zero-two' };
let themes = [], downloads = {}, theme = 'reze', role = 'Arrow', size = 32, revision = 0;
const sources = new Map(), previews = new Map();

function message(text, error = false) {
  $('#message').textContent = text;
  $('#message').className = error ? 'error' : '';
}

function original(id, state) {
  const key = `${id}/${state}`;
  if (!sources.has(key)) sources.set(key, new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => resolve(image);
    image.onerror = () => reject(new Error('图片加载失败，请刷新后重试。'));
    image.src = `/themes/${id}/${state}.png`;
  }));
  return sources.get(key);
}

async function preview(id, state, pixels) {
  const key = `${id}/${state}/${pixels}`;
  if (previews.has(key)) return previews.get(key);
  const image = await original(id, state);
  const canvas = document.createElement('canvas');
  canvas.width = canvas.height = pixels;
  const context = canvas.getContext('2d');
  context.imageSmoothingEnabled = true;
  context.imageSmoothingQuality = 'high';
  // Resize directly from the original transparent canvas, never from a thumbnail.
  context.drawImage(image, 0, 0, pixels, pixels);
  const url = canvas.toDataURL('image/png');
  if (previews.size >= 192) previews.delete(previews.keys().next().value);
  previews.set(key, url);
  return url;
}

function resetFollower() {
  $('#follower').hidden = true;
  $('#hero').style.visibility = 'visible';
  $('#stage').style.cursor = '';
}

async function refresh() {
  const current = ++revision;
  resetFollower();
  $('#size').value = $('#range').value = size;
  $('#stateLabel').textContent = labels[roles.indexOf(role)];
  $('#canvasSize').textContent = `${size} × ${size} px`;
  document.querySelectorAll('[data-size]').forEach(button => button.classList.toggle('active', +button.dataset.size === size));
  document.querySelectorAll('[data-role]').forEach(button => {
    const selected = button.dataset.role === role;
    button.classList.toggle('active', selected);
    button.setAttribute('aria-pressed', selected);
  });
  const width = size / window.devicePixelRatio;
  for (const id of ['hero', 'follower']) {
    $('#' + id).style.width = $('#' + id).style.height = `${width}px`;
  }
  try {
    const url = await preview(theme, role, size);
    if (current !== revision) return;
    $('#hero').src = $('#follower').src = url;
    message(`${downloads[theme].version} · ${(downloads[theme].bytes / 1048576).toFixed(1)} MB · 含安装脚本和使用说明`);
  } catch (error) { if (current === revision) message(error.message, true); }
}

function chooseTheme(id) {
  theme = id;
  document.querySelectorAll('[data-theme]').forEach(button => {
    const selected = button.dataset.theme === id;
    button.classList.toggle('active', selected);
    button.setAttribute('aria-pressed', selected);
  });
  const download = downloads[id];
  $('#download').href = download.url;
  $('#download').download = download.filename;
  const chosen = id;
  document.querySelectorAll('[data-role] img').forEach(async image => {
    try {
      const url = await preview(chosen, image.dataset.imageRole, 108);
      if (theme === chosen) image.src = url;
    } catch (error) { message(error.message, true); }
  });
  refresh();
}

function setSize(value) {
  const next = Number(value);
  if (!Number.isInteger(next) || next < 16 || next > 256) {
    $('#size').value = size;
    message('请输入 16–256 之间的整数像素。', true);
    return;
  }
  size = next;
  refresh();
}

$('#range').oninput = event => setSize(event.target.value);
$('#size').onchange = event => setSize(event.target.value);
$('#themes').onclick = event => {
  const button = event.target.closest('[data-theme]');
  if (button) chooseTheme(button.dataset.theme);
};
$('#states').onclick = event => {
  const button = event.target.closest('[data-role]');
  if (button) { role = button.dataset.role; refresh(); }
};
$('.presets').onclick = event => {
  const button = event.target.closest('[data-size]');
  if (button) setSize(button.dataset.size);
};
$('.backgrounds').onclick = event => {
  const button = event.target.closest('[data-bg]');
  if (!button) return;
  $('#stage').className = 'stage ' + button.dataset.bg;
  document.querySelectorAll('[data-bg]').forEach(item => item.classList.toggle('active', item === button));
};
$('#stage').onpointermove = event => {
  if (event.pointerType !== 'mouse' || !themes.length) return;
  const bounds = $('#stage').getBoundingClientRect();
  const hotspot = themes.find(item => item.id === theme).roles.find(item => item.role === role);
  const width = size / window.devicePixelRatio;
  const x = event.clientX - bounds.left - hotspot.hx * width;
  const y = event.clientY - bounds.top - hotspot.hy * width;
  if (x < 0 || y < 0 || x + width > bounds.width || y + width > bounds.height) { resetFollower(); return; }
  $('#follower').hidden = false;
  $('#follower').style.left = `${x}px`;
  $('#follower').style.top = `${y}px`;
  $('#hero').style.visibility = 'hidden';
  $('#stage').style.cursor = 'none';
};
$('#stage').onpointerleave = resetFollower;
window.addEventListener('resize', () => { if (themes.length) refresh(); });

(async () => {
  try {
    const response = await fetch('/catalog.json');
    if (!response.ok) throw new Error('无法加载角色列表，请刷新后重试。');
    const catalog = await response.json();
    ({ themes, downloads } = catalog);
    $('#fullDownload').href = catalog.fullRelease.url;
    $('#fullDownload').textContent = `下载完整合集 V${catalog.fullRelease.version} ↓`;
    $('#fullDownload').setAttribute('download', catalog.fullRelease.filename);
    $('#themes').innerHTML = themes.map(item => `<button class="theme" data-theme="${item.id}" aria-pressed="false"><img src="/characters/${characterImages[item.id]}.png" alt=""><span><strong>${item.name}</strong><small>${downloads[item.id].version} · 16 项状态</small></span></button>`).join('');
    $('#states').innerHTML = roles.map((state, index) => `<button class="state" data-role="${state}" aria-pressed="false"><img data-image-role="${state}" alt=""><span>${labels[index]}</span></button>`).join('');
    $('#downloadsGrid').innerHTML = themes.map(item => `<article class="download-card"><img src="/characters/${characterImages[item.id]}.png" alt="${item.name}基础形象"><h3>${item.name}</h3><p>${downloads[item.id].version} · ${(downloads[item.id].bytes / 1048576).toFixed(1)} MB</p><a href="${downloads[item.id].url}" download="${downloads[item.id].filename}">下载完整安装包 ↓</a></article>`).join('');
    $('#studioDownload').href = catalog.fullRelease.url;
    $('#studioDownload').textContent = '下载五款合集工作台与制作 Skills ↗';
    chooseTheme(theme);
  } catch (error) { message(error.message, true); }
})();
